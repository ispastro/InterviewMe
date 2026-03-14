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

class WebSocketService {
  private socket: WebSocket | null = null;
  private messageHandlers: ((message: ChatMessage) => void)[] = [];
  private feedbackHandlers: ((feedback: Feedback) => void)[] = [];
  private statusHandlers: ((status: 'connected' | 'disconnected') => void)[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 2000;
  private sessionId: string | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private shouldReconnect = true;
  private currentInterviewId: string | null = null;
  private currentUserId: string | null = null;

  async connect(interviewId: string, userId: string): Promise<string> {
    // Prevent multiple simultaneous connection attempts
    if (this.isConnecting) {
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

    this.isConnecting = true;
    this.shouldReconnect = true;
    this.currentInterviewId = interviewId;
    this.currentUserId = userId;

    return new Promise((resolve, reject) => {
      // Get JWT token for authentication
      const token = localStorage.getItem(config.JWT_STORAGE_KEY);
      if (!token) {
        this.isConnecting = false;
        reject(new Error('No authentication token found'));
        return;
      }

      // Build WebSocket URL to match backend route: /ws/interview/{interview_id}?token=...
      const wsUrl = config.WS_BASE_URL.replace('http', 'ws');
      const url = `${wsUrl}/ws/interview/${encodeURIComponent(interviewId)}?token=${encodeURIComponent(token)}`;

      console.log('Connecting to WebSocket:', url.replace(/token=[^&]+/, 'token=***'));

      try {
        this.socket = new WebSocket(url);

        // Connection timeout
        const connectionTimeout = setTimeout(() => {
          if (this.socket?.readyState !== WebSocket.OPEN) {
            console.error('WebSocket connection timeout');
            this.socket?.close();
            this.isConnecting = false;
            reject(new Error('Connection timeout'));
          }
        }, 10000); // 10 second timeout

        this.socket.onopen = () => {
          clearTimeout(connectionTimeout);
          console.log('✅ WebSocket connected successfully');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.notifyStatus('connected');
        };

        this.socket.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message, resolve);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.socket.onclose = (event) => {
          clearTimeout(connectionTimeout);
          this.isConnecting = false;
          console.log(`WebSocket closed: code=${event.code}, reason=${event.reason || 'none'}, clean=${event.wasClean}`);
          this.notifyStatus('disconnected');
          
          // Only attempt reconnection if:
          // 1. Not a clean close (code 1000)
          // 2. Not intentionally disconnected (shouldReconnect = true)
          // 3. Haven't exceeded max attempts
          // 4. Not authentication failure (code 4001)
          const shouldAttemptReconnect = 
            event.code !== 1000 && 
            event.code !== 4001 && 
            this.shouldReconnect && 
            this.reconnectAttempts < this.maxReconnectAttempts;

          if (shouldAttemptReconnect) {
            console.log(`Will attempt reconnection (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
            this.attemptReconnect();
          } else {
            if (event.code === 4001) {
              console.error('Authentication failed - not reconnecting');
            } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
              console.error('Max reconnection attempts reached');
            }
            this.cleanup();
          }
        };

        this.socket.onerror = (error) => {
          clearTimeout(connectionTimeout);
          this.isConnecting = false;
          console.error('WebSocket error:', error);
          // Don't reject here - let onclose handle reconnection
          // Only reject if we haven't resolved yet (initial connection)
          if (!this.sessionId) {
            reject(new Error('WebSocket connection failed'));
          }
        };

      } catch (error) {
        this.isConnecting = false;
        console.error('Failed to create WebSocket:', error);
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
        const chatMessage: ChatMessage = {
          id: message.data.question_id || `q-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
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
        const feedback: Feedback = {
          id: message.data.feedback_id || Date.now().toString(),
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
        console.log('Session status:', message.data);
        break;

      case 'error':
        console.error('Server error:', message.data.message);
        break;

      case 'pong':
        // Handle ping/pong for connection health
        break;

      default:
        console.log('Unhandled message type:', message.type);
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
      console.error('Cannot reconnect: missing interview or user ID');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`⏳ Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      if (!this.shouldReconnect) {
        console.log('Reconnection cancelled');
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

  startInterview(): void {
    this.sendMessage({
      type: 'start_interview',
      data: {}
    });
  }

  sendAnswer(text: string): void {
    // Add user message to chat immediately with unique ID
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
      this.socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  disconnect(): void {
    console.log('🔌 Disconnecting WebSocket...');
    this.shouldReconnect = false; // Prevent reconnection
    this.cleanup();
  }

  private cleanup(): void {
    // Clear reconnection timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Close socket if open
    if (this.socket) {
      try {
        if (this.socket.readyState === WebSocket.OPEN || 
            this.socket.readyState === WebSocket.CONNECTING) {
          this.socket.close(1000, 'Client disconnect');
        }
      } catch (error) {
        console.error('Error closing WebSocket:', error);
      }
      this.socket = null;
    }

    // Reset state
    this.sessionId = null;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
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
    return this.socket?.readyState === WebSocket.OPEN;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  // Health check
  ping(): void {
    this.sendMessage({
      type: 'ping',
      data: { timestamp: Date.now() }
    });
  }
}

export const websocketService = new WebSocketService();
