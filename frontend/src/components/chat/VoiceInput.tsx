'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Send, AlertCircle, Volume2, VolumeX } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSpeech } from '@/hooks';
import { Button } from '@/components/ui';

interface VoiceInputProps {
  onSend: (transcript: string) => void;
  disabled?: boolean;
  autoSpeak?: boolean;
  onAutoSpeakChange?: (enabled: boolean) => void;
}

export function VoiceInput({ 
  onSend, 
  disabled = false,
  autoSpeak = true,
  onAutoSpeakChange,
}: VoiceInputProps) {
  const [localTranscript, setLocalTranscript] = useState('');
  const [showTranscript, setShowTranscript] = useState(false);
  const [autoSpeakEnabled, setAutoSpeakEnabled] = useState(autoSpeak);
  const [isOnline, setIsOnline] = useState(true);

  // Check network status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    setIsOnline(navigator.onLine);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const {
    isListening,
    transcript,
    interimTranscript,
    recognitionError,
    hasPermission,
    isRecognitionSupported,
    startListening,
    stopListening,
    resetTranscript,
    requestPermission,
  } = useSpeech({
    continuous: true,
    interimResults: true,
    lang: 'en-US',
    silenceTimeout: 2000, // 2 seconds of silence
    autoSubmit: true, // Enable auto-submit
    onTranscriptChange: (text, isFinal) => {
      if (isFinal) {
        setLocalTranscript(text);
        setShowTranscript(true);
      }
    },
    onSilenceDetected: (finalTranscript) => {
      // Auto-submit when silence detected
      if (finalTranscript.trim()) {
        onSend(finalTranscript.trim());
        setLocalTranscript('');
        setShowTranscript(false);
      }
    },
  });

  // Update local transcript when speech recognition provides final result
  useEffect(() => {
    if (transcript) {
      setLocalTranscript(transcript);
      setShowTranscript(true);
    }
  }, [transcript]);

  // Handle microphone toggle
  const handleMicToggle = async () => {
    if (disabled) return;

    if (isListening) {
      // Stop listening
      stopListening();
    } else {
      // Check permission first
      if (!hasPermission) {
        const granted = await requestPermission();
        if (!granted) {
          return;
        }
      }

      // Reset previous transcript
      resetTranscript();
      setLocalTranscript('');
      setShowTranscript(false);

      // Start listening
      await startListening();
    }
  };

  // Handle send
  const handleSend = () => {
    if (!localTranscript.trim() || disabled) return;

    onSend(localTranscript.trim());
    
    // Reset
    setLocalTranscript('');
    setShowTranscript(false);
    resetTranscript();
  };

  // Handle auto-speak toggle
  const handleAutoSpeakToggle = () => {
    const newValue = !autoSpeakEnabled;
    setAutoSpeakEnabled(newValue);
    onAutoSpeakChange?.(newValue);
  };

  // Show error if not supported
  if (!isRecognitionSupported) {
    return (
      <div className="p-6 bg-[#FEF2F2] border border-[#FCA5A5] rounded-[16px]">
        <div className="flex items-start gap-3">
          <AlertCircle size={20} className="text-[#DC2626] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-[#DC2626] mb-1 font-[Lora]">
              Voice Mode Not Supported
            </p>
            <p className="text-sm text-[#991B1B] font-[Lexend]">
              Your browser doesn't support speech recognition. Please use text mode or try a different browser (Chrome, Edge, or Safari recommended).
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Show warning if offline
  if (!isOnline) {
    return (
      <div className="p-6 bg-[#FEF3C7] border border-[#FCD34D] rounded-[16px]">
        <div className="flex items-start gap-3">
          <AlertCircle size={20} className="text-[#D97706] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-[#D97706] mb-1 font-[Lora]">
              No Internet Connection
            </p>
            <p className="text-sm text-[#92400E] font-[Lexend]">
              Speech recognition requires an internet connection. Please check your connection and try again.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Transcript Display */}
      <AnimatePresence>
        {(showTranscript || isListening) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4 bg-white border border-[#E5E7EB] rounded-[12px] shadow-sm">
              <div className="flex items-start justify-between mb-2">
                <p className="text-xs font-medium text-[#64748B] uppercase tracking-wide font-[Lexend]">
                  {isListening ? 'Listening...' : 'Your Response'}
                </p>
                {isListening && (
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        className="w-1 h-3 bg-[#EF4444] rounded-full"
                        animate={{
                          scaleY: [1, 1.5, 1],
                        }}
                        transition={{
                          duration: 0.6,
                          repeat: Infinity,
                          delay: i * 0.15,
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>
              <p className="text-sm text-[#0F172A] leading-relaxed font-[Lexend] min-h-[60px]">
                {isListening ? (
                  <>
                    {localTranscript && <span>{localTranscript} </span>}
                    <span className="text-[#94A3B8]">{interimTranscript}</span>
                    {!localTranscript && !interimTranscript && (
                      <span className="text-[#94A3B8] italic">Start speaking...</span>
                    )}
                  </>
                ) : (
                  localTranscript || <span className="text-[#94A3B8] italic">No transcript yet</span>
                )}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Display */}
      <AnimatePresence>
        {recognitionError && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-3 bg-[#FEF2F2] border border-[#FCA5A5] rounded-[12px]"
          >
            <div className="flex items-start gap-2">
              <AlertCircle size={16} className="text-[#DC2626] flex-shrink-0 mt-0.5" />
              <p className="text-sm text-[#DC2626] font-[Lexend]">{recognitionError}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        {/* Auto-speak toggle */}
        <button
          onClick={handleAutoSpeakToggle}
          disabled={disabled}
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-[10px] transition-all',
            'text-sm font-[Lexend]',
            autoSpeakEnabled
              ? 'bg-[#DBEAFE] text-[#1E40AF] hover:bg-[#BFDBFE]'
              : 'bg-[#F1F5F9] text-[#64748B] hover:bg-[#E2E8F0]',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          title={autoSpeakEnabled ? 'Auto-speak enabled' : 'Auto-speak disabled'}
        >
          {autoSpeakEnabled ? (
            <Volume2 size={16} />
          ) : (
            <VolumeX size={16} />
          )}
          <span className="hidden sm:inline">
            {autoSpeakEnabled ? 'Auto-speak On' : 'Auto-speak Off'}
          </span>
        </button>

        {/* Microphone Button */}
        <button
          onClick={handleMicToggle}
          disabled={disabled}
          className={cn(
            'relative w-16 h-16 rounded-full flex items-center justify-center',
            'transition-all duration-200 shadow-lg',
            'focus:outline-none focus:ring-4',
            isListening
              ? 'bg-[#EF4444] text-white focus:ring-[#EF4444]/30 scale-110'
              : 'bg-[#0D9488] text-white hover:bg-[#0F766E] focus:ring-[#0D9488]/30',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          {/* Pulse animation when listening */}
          {isListening && (
            <>
              <motion.div
                className="absolute inset-0 rounded-full bg-[#EF4444]"
                animate={{
                  scale: [1, 1.4, 1],
                  opacity: [0.5, 0, 0.5],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              />
              <motion.div
                className="absolute inset-0 rounded-full bg-[#EF4444]"
                animate={{
                  scale: [1, 1.3, 1],
                  opacity: [0.3, 0, 0.3],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: 0.5,
                }}
              />
            </>
          )}

          {/* Icon */}
          <div className="relative z-10">
            {isListening ? <MicOff size={24} /> : <Mic size={24} />}
          </div>
        </button>

        {/* Send Button */}
        <Button
          onClick={handleSend}
          disabled={disabled || !localTranscript.trim() || isListening}
          size="lg"
          className="min-w-[100px]"
        >
          <Send size={18} className="mr-2" />
          Send
        </Button>
      </div>

      {/* Instructions */}
      <div className="text-center">
        <p className="text-sm text-[#64748B] font-[Lexend]">
          {!isOnline ? (
            <span className="text-[#D97706] font-medium">No internet connection</span>
          ) : isListening ? (
            <span className="text-[#EF4444] font-medium">Speak your answer... (auto-submits after 2s silence)</span>
          ) : disabled ? (
            'Interview paused'
          ) : localTranscript ? (
            'Click Send or start speaking again'
          ) : (
            'Click the microphone and start speaking'
          )}
        </p>
      </div>
    </div>
  );
}
