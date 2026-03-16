import { config } from './config';

// WebSocket message types matching backend
export type MessageType = 
  | 'connect'
  | 'start_interview'
  | 'user_response'
  | 'ai_question'
  | 'ai_feedback'
  | 'session_status'
  | 'pause_interview'
  | 'resume_interview'
  | 'end_interview'
  | 'error'
  | 'ping'
  | 'pong';

export interface WebSocketMessage {
  type: MessageType;
  data: any;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'interviewer';
  message: string;
  timestamp: Date;
  streaming?: boolean;
  metadata?: {
    question_type?: string;
    turn_number?: number;
    focus_area?: string;
    expected_duration?: number;
    is_probe?: boolean;
    probe_reason?: string;
  };
}

export interface Feedback {
  id: string;
  questionId: string;
  overall_score: number;
  criteria_scores: Record<string, number>;
  strengths: string[];
  areas_for_improvement: string[];
  feedback: string;
  follow_up_suggestions?: string[];
}

// Connection state machine
enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  FAILED = 'failed',
}

class WebSocketService {
  private socket: WebSocket | null = null;
  private messageHandlers: ((message: ChatMessage) => void)[] = [];
  private feedbackHandlers: ((feedback: Feedback) => void)[] = [];
  private statusHandlers: ((status: 'connected' | 'disconnected') => void)[] = [];
  
  // Message deduplication
  private processedMessageIds: Set<string> = new Set();
  private readonly MAX_PROCESSED_IDS = 1000; // Keep last 1000 message IDs
  
  // Connection state
  private connectionState: ConnectionState = ConnectionState.DISCONNECTED;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5; // Increased from 3
  private baseReconnectDelay = 1000; // Base delay for exponential backoff
  private maxReconnectDelay = 30000; // Max 30 seconds
  private sessionId: string | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private shouldReconnect = true;
  private currentInterviewId: string | null = null;
  private currentUserId: string | null = null;
  
  // Message batching
  private messageQueue: WebSocketMessage[] = [];
  private batchTimeout: NodeJS.Timeout | null = null;
  private readonly BATCH_DELAY = 50; // Batch messages within 50ms
  
  // Health check
  private pingInterval: NodeJS.Timeout | null = null;
  private readonly PING_INTERVAL = 30000; // 30 seconds
  private lastPongTime: number = Date.now();
  private readonly PONG_TIMEOUT = 10000; // 10 seconds

  async connect(interviewId: string, userId: string): Promise<string> {
    // Prevent multiple simultaneous connection attempts
    if (this.connectionState === ConnectionState.CONNECTING) {
      console.warn('⚠️ Connection already in progress, skipping...');
      throw new Error('Connection already in progress');
    }

    // If already connected to the same interview, return existing session
    if (this.socket?.readyState === WebSocket.OPEN && 
        this.currentInterviewId === interviewId && 
        this.sessionId) {
      console.log('✅ Already connected to this interview');
      return this.sessionId;
    }

    // Clean up any existing connection first
    if (this.socket) {
      console.log('🧹 Cleaning up existing connection before reconnecting...');
      this.cleanup();
    }

    this.connectionState = ConnectionState.CONNECTING;
    this.shouldReconnect = true;
    this.currentInterviewId = interviewId;
    this.currentUserId = userId;

    return new Promise((resolve, reject) => {
      // Get JWT token for authentication
      const token = localStorage.getItem(config.JWT_STORAGE_KEY);
      if (!token) {
        this.connectionState = ConnectionState.FAILED;
        reject(new Error('No authentication token found'));
        return;
      }

      // Build WebSocket URL
      const wsUrl = config.WS_BASE_URL.replace('http', 'ws');
      const url = `${wsUrl}/ws/interview/${encodeURIComponent(interviewId)}?token=${encodeURIComponent(token)}`;

      console.log('🔌 Connecting to WebSocket:', url.replace(/token=[^&]+/, 'token=***'));

      try {
        this.socket = new WebSocket(url);

        // Connection timeout
        const connectionTimeout = setTimeout(() => {
          if (this.socket?.readyState !== WebSocket.OPEN) {
            console.error('⏱️ WebSocket connection timeout');
            this.socket?.close();
            this.connectionState = ConnectionState.FAILED;
            reject(new Error('Connection timeout'));
          }
        }, 10000);

        this.socket.onopen = () => {
          clearTimeout(connectionTimeout);
          console.log('✅ WebSocket connected successfully');
          this.connectionState = ConnectionState.CONNECTED;
          this.reconnectAttempts = 0;
          this.lastPongTime = Date.now();
          this.startHealthCheck();
          this.notifyStatus('connected');
        };

        this.socket.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message, resolve);
          } catch (error) {
            console.error('❌ Failed to parse WebSocket message:', error);
          }
        };

        this.socket.onclose = (event) => {
          clearTimeout(connectionTimeout);
          this.stopHealthCheck();
          
          const wasConnected = this.connectionState === ConnectionState.CONNECTED;
          this.connectionState = ConnectionState.DISCONNECTED;
          
          console.log(`🔌 WebSocket closed: code=${event.code}, reason=${event.reason || 'none'}, clean=${event.wasClean}`);
          this.notifyStatus('disconnected');
          
          // Determine if we should reconnect
          const shouldAttemptReconnect = 
            event.code !== 1000 && // Not a clean close
            event.code !== 4001 && // Not authentication failure
            this.shouldReconnect && 
            this.reconnectAttempts < this.maxReconnectAttempts &&
            wasConnected; // Only reconnect if we were previously connected

          if (shouldAttemptReconnect) {
            console.log(`🔄 Will attempt reconnection (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
            this.attemptReconnect();
          } else {
            if (event.code === 4001) {
              console.error('🔒 Authentication failed - not reconnecting');
            } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
              console.error('❌ Max reconnection attempts reached');
            }
            this.connectionState = ConnectionState.FAILED;
            this.cleanup();
          }
        };

        this.socket.onerror = (error) => {
          clearTimeout(connectionTimeout);
          console.error('❌ WebSocket error:', error);
          
          // Only reject if we haven't resolved yet (initial connection)
          if (this.connectionState === ConnectionState.CONNECTING) {
            this.connectionState = ConnectionState.FAILED;
            reject(new Error('WebSocket connection failed'));
          }
        };

      } catch (error) {
        this.connectionState = ConnectionState.FAILED;
        console.error('❌ Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  private handleMessage(message: WebSocketMessage, connectResolve?: (sessionId: string) => void) {
    switch (message.type) {
      case 'connect':
        this.sessionId = message.data.session_id;
        if (connectResolve) {
          connectResolve(this.sessionId || '');
        }
        break;

      case 'ai_question':
        const questionId = message.data.question_id || `q-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Deduplicate messages
        if (this.processedMessageIds.has(questionId)) {
          console.warn('⚠️ Duplicate message detected, skipping:', questionId);
          return;
        }
        
        // Add to processed set
        this.processedMessageIds.add(questionId);
        
        // Limit set size to prevent memory leak
        if (this.processedMessageIds.size > this.MAX_PROCESSED_IDS) {
          const firstId = this.processedMessageIds.values().next().value;
          this.processedMessageIds.delete(firstId);
        }
        
        const chatMessage: ChatMessage = {
          id: questionId,
          sender: 'interviewer',
          message: message.data.question,
          timestamp: new Date(),
          metadata: {
            question_type: message.data.question_type,
            turn_number: message.data.turn_number,
            focus_area: message.data.focus_area,
            expected_duration: message.data.expected_duration,
            is_probe: message.data.is_probe,
            probe_reason: message.data.probe_reason,
          }
        };
        this.messageHandlers.forEach(handler => handler(chatMessage));
        break;

      case 'ai_feedback':
        const feedbackId = message.data.feedback_id || Date.now().toString();
        
        // Deduplicate feedback
        if (this.processedMessageIds.has(feedbackId)) {
          console.warn('⚠️ Duplicate feedback detected, skipping:', feedbackId);
          return;
        }
        
        this.processedMessageIds.add(feedbackId);
        
        if (this.processedMessageIds.size > this.MAX_PROCESSED_IDS) {
          const firstId = this.processedMessageIds.values().next().value;
          this.processedMessageIds.delete(firstId);
        }
        
        const feedback: Feedback = {
          id: feedbackId,
          questionId: message.data.question_id,
          overall_score: message.data.overall_score,
          criteria_scores: message.data.criteria_scores || {},
          strengths: message.data.strengths || [],
          areas_for_improvement: message.data.areas_for_improvement || [],
          feedback: message.data.feedback || '',
          follow_up_suggestions: message.data.follow_up_suggestions || [],
        };
        this.feedbackHandlers.forEach(handler => handler(feedback));
        break;

      case 'session_status':
        console.log('📊 Session status:', message.data);
        break;

      case 'error':
        console.error('❌ Server error:', message.data.message);
        break;

      case 'pong':
        this.lastPongTime = Date.now();
        break;

      default:
        console.log('❓ Unhandled message type:', message.type);
    }
  }

  private attemptReconnect() {
    // Clear any existing reconnection timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Don't reconnect if we don't have the necessary info
    if (!this.currentInterviewId || !this.currentUserId) {
      console.error('❌ Cannot reconnect: missing interview or user ID');
      this.connectionState = ConnectionState.FAILED;
      return;
    }

    this.connectionState = ConnectionState.RECONNECTING;
    this.reconnectAttempts++;
    
    // Exponential backoff with jitter
    const exponentialDelay = Math.min(
      this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );
    const jitter = Math.random() * 1000; // Add random jitter to prevent thundering herd
    const delay = exponentialDelay + jitter;
    
    console.log(`⏳ Reconnecting in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      if (!this.shouldReconnect) {
        console.log('🛑 Reconnection cancelled');
        return;
      }

      console.log(`🔄 Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      
      this.connect(this.currentInterviewId!, this.currentUserId!)
        .then(() => {
          console.log('✅ Reconnection successful');
        })
        .catch(error => {
          console.error('❌ Reconnection failed:', error);
          // onclose will handle next reconnection attempt
        });
    }, delay);
  }

  private startHealthCheck() {
    this.stopHealthCheck();
    
    this.pingInterval = setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        // Check if we received a pong recently
        const timeSinceLastPong = Date.now() - this.lastPongTime;
        
        if (timeSinceLastPong > this.PONG_TIMEOUT) {
          console.warn('⚠️ No pong received, connection may be dead');
          this.socket.close(1000, 'Health check failed');
          return;
        }
        
        // Send ping
        this.sendMessage({
          type: 'ping',
          data: { timestamp: Date.now() }
        });
      }
    }, this.PING_INTERVAL);
  }

  private stopHealthCheck() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  startInterview(): void {
    this.sendMessage({
      type: 'start_interview',
      data: {}
    });
  }

  sendAnswer(text: string): void {
    // Add user message to chat immediately
    const userMessage: ChatMessage = {
      id: `u-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      sender: 'user',
      message: text,
      timestamp: new Date(),
    };
    this.messageHandlers.forEach(handler => handler(userMessage));

    // Send to backend
    this.sendMessage({
      type: 'user_response',
      data: { response: text }
    });
  }

  sendTranscript(transcript: string): void {
    this.sendAnswer(transcript);
  }

  pauseInterview(): void {
    this.sendMessage({
      type: 'pause_interview',
      data: {}
    });
  }

  resumeInterview(): void {
    this.sendMessage({
      type: 'resume_interview',
      data: {}
    });
  }

  endSession(): void {
    this.sendMessage({
      type: 'end_interview',
      data: {}
    });
  }

  private sendMessage(message: WebSocketMessage): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      // For critical messages, send immediately
      if (['start_interview', 'end_interview', 'pause_interview', 'resume_interview'].includes(message.type)) {
        this.socket.send(JSON.stringify(message));
      } else {
        // Batch other messages
        this.batchSend(message);
      }
    } else {
      console.warn('⚠️ WebSocket not connected, message not sent:', message.type);
    }
  }

  private batchSend(message: WebSocketMessage): void {
    this.messageQueue.push(message);
    
    if (!this.batchTimeout) {
      this.batchTimeout = setTimeout(() => {
        this.flushQueue();
      }, this.BATCH_DELAY);
    }
  }

  private flushQueue(): void {
    if (this.messageQueue.length > 0 && this.socket?.readyState === WebSocket.OPEN) {
      // If only one message, send it directly
      if (this.messageQueue.length === 1) {
        this.socket.send(JSON.stringify(this.messageQueue[0]));
      } else {
        // Send as batch
        this.messageQueue.forEach(msg => {
          this.socket!.send(JSON.stringify(msg));
        });
      }
      this.messageQueue = [];
    }
    this.batchTimeout = null;
  }

  disconnect(): void {
    console.log('🔌 Disconnecting WebSocket...');
    this.shouldReconnect = false;
    this.cleanup();
  }

  private cleanup(): void {
    // Clear reconnection timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Clear batch timeout
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
      this.batchTimeout = null;
    }

    // Stop health check
    this.stopHealthCheck();

    // Close socket if open
    if (this.socket) {
      try {
        if (this.socket.readyState === WebSocket.OPEN || 
            this.socket.readyState === WebSocket.CONNECTING) {
          this.socket.close(1000, 'Client disconnect');
        }
      } catch (error) {
        console.error('❌ Error closing WebSocket:', error);
      }
      this.socket = null;
    }

    // Reset state
    this.sessionId = null;
    this.connectionState = ConnectionState.DISCONNECTED;
    this.reconnectAttempts = 0;
    this.messageQueue = [];
    this.processedMessageIds.clear(); // Clear deduplication cache
  }

  // Event handlers
  onMessage(handler: (message: ChatMessage) => void): () => void {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    };
  }

  onFeedback(handler: (feedback: Feedback) => void): () => void {
    this.feedbackHandlers.push(handler);
    return () => {
      this.feedbackHandlers = this.feedbackHandlers.filter(h => h !== handler);
    };
  }

  onStatus(handler: (status: 'connected' | 'disconnected') => void): () => void {
    this.statusHandlers.push(handler);
    return () => {
      this.statusHandlers = this.statusHandlers.filter(h => h !== handler);
    };
  }

  private notifyStatus(status: 'connected' | 'disconnected'): void {
    this.statusHandlers.forEach(handler => handler(status));
  }

  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN && 
           this.connectionState === ConnectionState.CONNECTED;
  }

  getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  ping(): void {
    this.sendMessage({
      type: 'ping',
      data: { timestamp: Date.now() }
    });
  }
}

export const websocketService = new WebSocketService();
