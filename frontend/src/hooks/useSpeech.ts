'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  speechRecognition,
  speechSynthesis,
  isSpeechRecognitionSupported,
  isSpeechSynthesisSupported,
  requestMicrophonePermission,
  checkMicrophonePermission,
  type SpeechRecognitionResult,
  type SpeechRecognitionError,
  type SpeechSynthesisConfig,
} from '@/lib/speech';

export interface UseSpeechOptions {
  autoSpeak?: boolean; // Auto-speak AI responses
  lang?: string;
  continuous?: boolean;
  interimResults?: boolean;
  silenceTimeout?: number; // Auto-submit after X ms of silence
  autoSubmit?: boolean; // Enable auto-submit on silence
  onTranscriptChange?: (transcript: string, isFinal: boolean) => void;
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
  onError?: (error: SpeechRecognitionError) => void;
  onSilenceDetected?: (transcript: string) => void; // Called when silence detected
}

export interface UseSpeechReturn {
  // Recognition state
  isListening: boolean;
  transcript: string;
  interimTranscript: string;
  recognitionError: string | null;
  
  // Synthesis state
  isSpeaking: boolean;
  isPaused: boolean;
  
  // Permissions
  hasPermission: boolean;
  permissionState: PermissionState | null;
  
  // Support
  isRecognitionSupported: boolean;
  isSynthesisSupported: boolean;
  
  // Recognition methods
  startListening: () => Promise<void>;
  stopListening: () => void;
  resetTranscript: () => void;
  
  // Synthesis methods
  speak: (text: string, config?: SpeechSynthesisConfig) => void;
  pauseSpeech: () => void;
  resumeSpeech: () => void;
  stopSpeech: () => void;
  
  // Permission methods
  requestPermission: () => Promise<boolean>;
  
  // Utility
  getAvailableVoices: () => SpeechSynthesisVoice[];
}

export function useSpeech(options: UseSpeechOptions = {}): UseSpeechReturn {
  const {
    autoSpeak = false,
    lang = 'en-US',
    continuous = true, // Changed to true for auto-submit
    interimResults = true,
    silenceTimeout = 2000,
    autoSubmit = false,
    onTranscriptChange,
    onSpeechStart,
    onSpeechEnd,
    onError,
    onSilenceDetected,
  } = options;

  // Recognition state
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [recognitionError, setRecognitionError] = useState<string | null>(null);

  // Synthesis state
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  // Permission state
  const [hasPermission, setHasPermission] = useState(false);
  const [permissionState, setPermissionState] = useState<PermissionState | null>(null);

  // Support state
  const [isRecognitionSupported] = useState(isSpeechRecognitionSupported());
  const [isSynthesisSupported] = useState(isSpeechSynthesisSupported());

  // Refs to track component mount state
  const isMountedRef = useRef(true);
  const recognitionInitializedRef = useRef(false);

  // ============================================================
  // INITIALIZATION
  // ============================================================

  useEffect(() => {
    isMountedRef.current = true;

    // Initialize speech recognition
    if (isRecognitionSupported && !recognitionInitializedRef.current) {
      try {
        speechRecognition.initialize({
          continuous,
          interimResults,
          lang,
          maxAlternatives: 1,
          silenceTimeout,
          autoSubmit,
        });
        recognitionInitializedRef.current = true;
      } catch (error) {
        console.error('Failed to initialize speech recognition:', error);
      }
    }

    // Check initial permission state
    checkMicrophonePermission().then((state) => {
      if (isMountedRef.current) {
        setPermissionState(state);
        setHasPermission(state === 'granted');
      }
    });

    return () => {
      isMountedRef.current = false;
      // Cleanup on unmount
      if (isListening) {
        speechRecognition.stop();
      }
      if (isSpeaking) {
        speechSynthesis.cancel();
      }
    };
  }, [isRecognitionSupported, continuous, interimResults, lang, silenceTimeout, autoSubmit]);

  // ============================================================
  // PERMISSION METHODS
  // ============================================================

  const requestPermission = useCallback(async (): Promise<boolean> => {
    try {
      const granted = await requestMicrophonePermission();
      if (isMountedRef.current) {
        setHasPermission(granted);
        setPermissionState(granted ? 'granted' : 'denied');
      }
      return granted;
    } catch (error) {
      console.error('Failed to request microphone permission:', error);
      return false;
    }
  }, []);

  // ============================================================
  // RECOGNITION METHODS
  // ============================================================

  const startListening = useCallback(async (): Promise<void> => {
    if (!isRecognitionSupported) {
      const error = 'Speech recognition not supported in this browser';
      setRecognitionError(error);
      onError?.({ error: 'not-supported', message: error });
      return;
    }

    // Check permission
    if (!hasPermission) {
      const granted = await requestPermission();
      if (!granted) {
        const error = 'Microphone permission denied';
        setRecognitionError(error);
        onError?.({ error: 'not-allowed', message: error });
        return;
      }
    }

    // Reset state
    setRecognitionError(null);
    setTranscript('');
    setInterimTranscript('');

    // Start recognition
    speechRecognition.start({
      onStart: () => {
        if (isMountedRef.current) {
          setIsListening(true);
          onSpeechStart?.();
        }
      },
      onEnd: () => {
        if (isMountedRef.current) {
          setIsListening(false);
          onSpeechEnd?.();
        }
      },
      onResult: (result: SpeechRecognitionResult) => {
        if (!isMountedRef.current) return;

        if (result.isFinal) {
          setTranscript(result.transcript);
          setInterimTranscript('');
          onTranscriptChange?.(result.transcript, true);
        } else {
          setInterimTranscript(result.transcript);
          onTranscriptChange?.(result.transcript, false);
        }
      },
      onError: (error: SpeechRecognitionError) => {
        if (!isMountedRef.current) return;
        
        setRecognitionError(error.message);
        setIsListening(false);
        onError?.(error);
      },
      onNoMatch: () => {
        if (!isMountedRef.current) return;
        
        const error = 'No speech was recognized. Please try again.';
        setRecognitionError(error);
        onError?.({ error: 'no-match', message: error });
      },
      onSilenceDetected: (finalTranscript: string) => {
        if (!isMountedRef.current) return;
        
        console.log('🔕 Silence detected - auto-submitting');
        setTranscript(finalTranscript);
        setInterimTranscript('');
        setIsListening(false);
        onSilenceDetected?.(finalTranscript);
      },
    });
  }, [
    isRecognitionSupported,
    hasPermission,
    requestPermission,
    onSpeechStart,
    onSpeechEnd,
    onTranscriptChange,
    onError,
    onSilenceDetected,
  ]);

  const stopListening = useCallback((): void => {
    speechRecognition.stop();
    if (isMountedRef.current) {
      setIsListening(false);
    }
  }, []);

  const resetTranscript = useCallback((): void => {
    speechRecognition.reset();
    if (isMountedRef.current) {
      setTranscript('');
      setInterimTranscript('');
      setRecognitionError(null);
    }
  }, []);

  // ============================================================
  // SYNTHESIS METHODS
  // ============================================================

  const speak = useCallback(
    (text: string, config: SpeechSynthesisConfig = {}): void => {
      if (!isSynthesisSupported) {
        console.warn('Speech synthesis not supported in this browser');
        return;
      }

      if (!text.trim()) {
        console.warn('Cannot speak empty text');
        return;
      }

      // Stop any ongoing speech
      speechSynthesis.cancel();

      // Speak with callbacks
      speechSynthesis.speak(
        text,
        {
          lang: config.lang ?? lang,
          pitch: config.pitch ?? 1.0,
          rate: config.rate ?? 1.0,
          volume: config.volume ?? 1.0,
          voice: config.voice,
        },
        {
          onStart: () => {
            if (isMountedRef.current) {
              setIsSpeaking(true);
              setIsPaused(false);
            }
          },
          onEnd: () => {
            if (isMountedRef.current) {
              setIsSpeaking(false);
              setIsPaused(false);
            }
          },
          onError: (error) => {
            console.error('Speech synthesis error:', error);
            if (isMountedRef.current) {
              setIsSpeaking(false);
              setIsPaused(false);
            }
          },
          onPause: () => {
            if (isMountedRef.current) {
              setIsPaused(true);
            }
          },
          onResume: () => {
            if (isMountedRef.current) {
              setIsPaused(false);
            }
          },
        }
      );
    },
    [isSynthesisSupported, lang]
  );

  const pauseSpeech = useCallback((): void => {
    speechSynthesis.pause();
    if (isMountedRef.current) {
      setIsPaused(true);
    }
  }, []);

  const resumeSpeech = useCallback((): void => {
    speechSynthesis.resume();
    if (isMountedRef.current) {
      setIsPaused(false);
    }
  }, []);

  const stopSpeech = useCallback((): void => {
    speechSynthesis.cancel();
    if (isMountedRef.current) {
      setIsSpeaking(false);
      setIsPaused(false);
    }
  }, []);

  // ============================================================
  // UTILITY METHODS
  // ============================================================

  const getAvailableVoices = useCallback((): SpeechSynthesisVoice[] => {
    return speechSynthesis.getVoices();
  }, []);

  // ============================================================
  // AUTO-SPEAK EFFECT
  // ============================================================

  // This effect can be used to auto-speak AI responses
  // (will be controlled by the component using this hook)

  return {
    // Recognition state
    isListening,
    transcript,
    interimTranscript,
    recognitionError,

    // Synthesis state
    isSpeaking,
    isPaused,

    // Permissions
    hasPermission,
    permissionState,

    // Support
    isRecognitionSupported,
    isSynthesisSupported,

    // Recognition methods
    startListening,
    stopListening,
    resetTranscript,

    // Synthesis methods
    speak,
    pauseSpeech,
    resumeSpeech,
    stopSpeech,

    // Permission methods
    requestPermission,

    // Utility
    getAvailableVoices,
  };
}
