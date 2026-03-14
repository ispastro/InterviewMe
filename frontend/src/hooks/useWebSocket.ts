'use client';

import { useEffect, useCallback, useRef, useState } from 'react';
import { websocketService, type ChatMessage, type Feedback } from '@/lib/websocket';
import { useInterviewStore } from '@/stores';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  onConnect?: (sessionId: string) => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

export function useWebSocket(
  interviewId: string | null,
  userId: string | null,
  options: UseWebSocketOptions = {}
) {
  const { autoConnect = true, onConnect, onDisconnect, onError } = options;
  const websocketConnected = useInterviewStore((state) => state.websocketConnected);
  const sessionId = useInterviewStore((state) => state.sessionId);
  const setSessionId = useInterviewStore((state) => state.setSessionId);
  const setWebsocketConnected = useInterviewStore((state) => state.setWebsocketConnected);
  const addMessage = useInterviewStore((state) => state.addMessage);
  const setCurrentQuestion = useInterviewStore((state) => state.setCurrentQuestion);
  const setFeedback = useInterviewStore((state) => state.setFeedback);
  const setIsEvaluating = useInterviewStore((state) => state.setIsEvaluating);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const isConnectingRef = useRef(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(async () => {
    if (!interviewId || !userId) {
      console.warn('Cannot connect: missing interviewId or userId');
      return;
    }

    if (isConnectingRef.current) {
      console.warn('Connection already in progress');
      return;
    }

    // If already connected, don't reconnect
    if (websocketService.isConnected()) {
      console.log('Already connected');
      return;
    }

    isConnectingRef.current = true;
    setIsConnecting(true);
    setConnectionError(null);

    try {
      const sessionId = await websocketService.connect(interviewId, userId);
      setSessionId(sessionId);
      setWebsocketConnected(true);
      onConnect?.(sessionId);
      console.log('✅ WebSocket connected with session:', sessionId);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Connection failed';
      console.error('❌ Failed to connect WebSocket:', errorMessage);
      setConnectionError(errorMessage);
      setWebsocketConnected(false);
      onError?.(error instanceof Error ? error : new Error(errorMessage));
    } finally {
      setIsConnecting(false);
      isConnectingRef.current = false;
    }
  }, [interviewId, userId, onConnect, onError, setSessionId, setWebsocketConnected]);

  const disconnect = useCallback(() => {
    console.log('🔌 Disconnecting from useWebSocket hook');
    websocketService.disconnect();
    setWebsocketConnected(false);
    setSessionId(null);
    onDisconnect?.();
    
    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    // Reset connecting state
    isConnectingRef.current = false;
    setIsConnecting(false);
  }, [onDisconnect, setSessionId, setWebsocketConnected]);

  const startInterview = useCallback(() => {
    websocketService.startInterview();
  }, []);

  const sendAnswer = useCallback((text: string) => {
    if (!text.trim()) return;
    
    setIsEvaluating(true);
    websocketService.sendAnswer(text);
  }, [setIsEvaluating]);

  const sendTranscript = useCallback((transcript: string) => {
    if (!transcript.trim()) return;
    
    setIsEvaluating(true);
    websocketService.sendTranscript(transcript);
  }, [setIsEvaluating]);

  const pauseInterview = useCallback(() => {
    websocketService.pauseInterview();
  }, []);

  const resumeInterview = useCallback(() => {
    websocketService.resumeInterview();
  }, []);

  const endSession = useCallback(() => {
    websocketService.endSession();
  }, []);

  const ping = useCallback(() => {
    websocketService.ping();
  }, []);

  // Set up event handlers
  useEffect(() => {
    if (!interviewId || !userId) return;

    const unsubscribeMessage = websocketService.onMessage((message: ChatMessage) => {
      addMessage(message);
      
      // If it's an AI question, update current question
      if (message.sender === 'interviewer') {
        setCurrentQuestion(message.message);
      }
    });

    const unsubscribeFeedback = websocketService.onFeedback((feedback: Feedback) => {
      // Convert backend feedback to UI feedback format
      const uiFeedback = {
        id: feedback.id,
        questionId: feedback.questionId,
        overall_score: feedback.overall_score,
        criteria_scores: feedback.criteria_scores || {},
        strengths: feedback.strengths || [],
        weaknesses: feedback.areas_for_improvement || [],
        improvements: feedback.areas_for_improvement || [],
        feedback: feedback.feedback || '',
        modelAnswer: feedback.feedback || '',
      };
      
      setFeedback(uiFeedback as any);
      setIsEvaluating(false);
    });

    const unsubscribeStatus = websocketService.onStatus((status) => {
      setWebsocketConnected(status === 'connected');
      
      if (status === 'disconnected') {
        // Don't auto-reconnect here - let the WebSocket service handle it
        console.log('WebSocket disconnected - service will handle reconnection if needed');
      }
    });

    return () => {
      unsubscribeMessage();
      unsubscribeFeedback();
      unsubscribeStatus();
    };
  }, [interviewId, userId, addMessage, setCurrentQuestion, setFeedback, setIsEvaluating, setWebsocketConnected]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && interviewId && userId && !websocketService.isConnected()) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [autoConnect, interviewId, userId, connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      console.log('useWebSocket unmounting - cleaning up');
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      // Don't disconnect here - let the component decide
    };
  }, []);

  // Health check ping every 30 seconds
  useEffect(() => {
    if (!websocketConnected) return;

    const pingInterval = setInterval(() => {
      if (websocketService.isConnected()) {
        ping();
      }
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [ping, websocketConnected]);

  return {
    // Connection state
    isConnected: websocketConnected,
    isConnecting,
    connectionError,
    sessionId,
    
    // Connection methods
    connect,
    disconnect,
    
    // Interview methods
    startInterview,
    sendAnswer,
    sendTranscript,
    pauseInterview,
    resumeInterview,
    endSession,
    
    // Utility methods
    ping,
    
    // WebSocket service instance (for advanced usage)
    websocketService,
  };
}