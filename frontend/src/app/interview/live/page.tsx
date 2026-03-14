'use client';

import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter, useSearchParams } from 'next/navigation';
import { Bot, X, Wifi, WifiOff, Pause, Play, AlertCircle, Volume2, VolumeX } from 'lucide-react';
import { Button, ConfirmModal } from '@/components/ui';
import { ChatMessage, TypingIndicator, ChatInput, VoiceInput } from '@/components/chat';
import { FeedbackPanel } from '@/components/feedback';
import { Timer } from '@/components/Timer';
import { InterviewerAvatar } from '@/components/InterviewerAvatar';
import { useAuth } from '@/contexts/AuthContext';
import { useWebSocket, useSpeech } from '@/hooks';
import { useInterviewStore, useInterviewSelectors, useSettingsSelectors } from '@/stores';
import { withAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';
import type { ChatMessage as ChatMessageType } from '@/types';

function LiveInterviewContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { user } = useAuth();
    
    // Get URL parameters
    const interviewId = searchParams.get('interview_id');
    const userId = searchParams.get('user_id') || user?.id || null;
    
    // Store selectors
    const interview = useInterviewStore();
    const setInterviewId = useInterviewStore((state) => state.setInterviewId);
    const setUserId = useInterviewStore((state) => state.setUserId);
    const setTimer = useInterviewStore((state) => state.setTimer);
    const { isConnected, isActive, formattedTimer } = useInterviewSelectors();
    const { mode, durationInSeconds } = useSettingsSelectors();
    
    // Local state
    const [showEndModal, setShowEndModal] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [connectionError, setConnectionError] = useState<string | null>(null);
    const [autoSpeakEnabled, setAutoSpeakEnabled] = useState(true);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const lastSpokenMessageRef = useRef<string | null>(null);
    
    // WebSocket connection
    const {
        isConnected: wsConnected,
        isConnecting,
        connectionError: wsError,
        sessionId,
        startInterview,
        sendAnswer,
        pauseInterview,
        resumeInterview,
        endSession,
    } = useWebSocket(interviewId, userId, {
        onConnect: (sessionId) => {
            console.log('✅ Connected to interview session:', sessionId);
            interview.setSessionId(sessionId);
            // Auto-start interview after connection
            setTimeout(() => {
                startInterview();
            }, 1000);
        },
        onDisconnect: () => {
            console.log('❌ Disconnected from interview session');
            setConnectionError('Connection lost. Attempting to reconnect...');
        },
        onError: (error) => {
            console.error('❌ WebSocket error:', error);
            setConnectionError(error.message);
        },
    });

    // Speech synthesis for AI responses (TTS)
    const {
        speak,
        stopSpeech,
        isSpeaking,
        isSynthesisSupported,
    } = useSpeech({
        lang: 'en-US',
        autoSpeak: false, // Manual control
    });

    // Redirect if missing required parameters
    useEffect(() => {
        if (!interviewId || !userId) {
            router.push('/interview/setup');
            return;
        }
        
        // Set initial state
        setInterviewId(interviewId);
        setUserId(userId);
        setTimer(durationInSeconds);
    }, [interviewId, userId, setInterviewId, setUserId, setTimer, router, durationInSeconds]);

    // Auto-scroll chat to bottom
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [interview.messages]);

    // Auto-speak AI messages (TTS)
    useEffect(() => {
        if (!autoSpeakEnabled || !isSynthesisSupported || mode !== 'voice') return;

        // Get the last message
        const lastMessage = interview.messages[interview.messages.length - 1];
        
        // Only speak AI messages that haven't been spoken yet
        if (
            lastMessage && 
            lastMessage.sender === 'interviewer' && 
            lastMessage.id !== lastSpokenMessageRef.current &&
            !interview.isEvaluating
        ) {
            // Stop any ongoing speech
            stopSpeech();
            
            // Speak the new message
            speak(lastMessage.message, {
                rate: 1.0,
                pitch: 1.0,
                volume: 1.0,
            });
            
            // Mark as spoken
            lastSpokenMessageRef.current = lastMessage.id;
            
            console.log('🔊 Speaking AI message:', lastMessage.message.substring(0, 50) + '...');
        }
    }, [interview.messages, autoSpeakEnabled, isSynthesisSupported, mode, interview.isEvaluating, speak, stopSpeech]);

    // Stop speech when interview is paused or ended
    useEffect(() => {
        if (isPaused || !wsConnected) {
            stopSpeech();
        }
    }, [isPaused, wsConnected, stopSpeech]);

    // Timer countdown
    const handleTimerTick = useCallback(() => {
        if (interview.timer > 0 && isActive && !isPaused) {
            interview.decrementTimer();
        }
        
        if (interview.timer <= 1) {
            handleEndInterview();
        }
    }, [interview.timer, isActive, isPaused]);

    // Handle sending messages (both text and voice)
    const handleSendMessage = useCallback(async (message: string) => {
        if (!message.trim() || !wsConnected) return;
        
        // Stop any ongoing speech before sending
        stopSpeech();
        
        sendAnswer(message);
    }, [wsConnected, sendAnswer, stopSpeech]);

    // Handle auto-speak toggle
    const handleAutoSpeakToggle = useCallback(() => {
        const newValue = !autoSpeakEnabled;
        setAutoSpeakEnabled(newValue);
        
        // Stop speech if disabling
        if (!newValue) {
            stopSpeech();
        }
        
        console.log('🔊 Auto-speak:', newValue ? 'enabled' : 'disabled');
    }, [autoSpeakEnabled, stopSpeech]);

    // Handle pause/resume
    const handlePauseResume = useCallback(() => {
        if (isPaused) {
            resumeInterview();
            setIsPaused(false);
        } else {
            pauseInterview();
            setIsPaused(true);
        }
    }, [isPaused, pauseInterview, resumeInterview]);

    // Handle ending interview
    const handleEndInterview = useCallback(() => {
        setShowEndModal(false);
        
        // Stop any ongoing speech
        stopSpeech();
        
        endSession();
        
        // Navigate to summary page
        setTimeout(() => {
            router.push(`/interview/summary?interview_id=${interviewId}&session_id=${sessionId}`);
        }, 1000);
    }, [endSession, router, interviewId, sessionId, stopSpeech]);

    // Show loading state while connecting
    if (isConnecting) {
        return (
            <div className="h-screen flex items-center justify-center bg-white">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-[#E5E7EB] border-t-[#0D9488] rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-[#475569] font-[Lexend]">Connecting to interview session...</p>
                </div>
            </div>
        );
    }

    // Show error state if connection failed
    if (wsError && !wsConnected) {
        return (
            <div className="h-screen flex items-center justify-center bg-white">
                <div className="text-center max-w-md">
                    <AlertCircle size={48} className="text-[#EF4444] mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-[#0F172A] mb-2 font-[Lora]">Connection Failed</h2>
                    <p className="text-[#475569] mb-6 font-[Lexend]">{wsError}</p>
                    <div className="flex gap-4 justify-center">
                        <Button onClick={() => window.location.reload()}>
                            Try Again
                        </Button>
                        <Button variant="secondary" onClick={() => router.push('/dashboard')}>
                            Back to Dashboard
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen flex flex-col bg-white">
            {/* Top Bar */}
            <header className="flex-shrink-0 px-6 py-4 bg-white border-b border-[#E5E7EB]">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <InterviewerAvatar isThinking={interview.isEvaluating} />
                        <div>
                            <p className="font-semibold text-[#0F172A] font-[Lora]">AI Interviewer</p>
                            <div className="flex items-center gap-2 text-sm font-[Lexend]">
                                {wsConnected ? (
                                    <span className="flex items-center gap-1 text-[#10B981]">
                                        <Wifi size={14} />
                                        Connected
                                    </span>
                                ) : (
                                    <span className="flex items-center gap-1 text-[#EF4444]">
                                        <WifiOff size={14} />
                                        {connectionError || 'Disconnected'}
                                    </span>
                                )}
                                {isPaused && (
                                    <span className="text-[#F59E0B]">• Paused</span>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Auto-speak toggle (voice mode only) */}
                        {mode === 'voice' && isSynthesisSupported && (
                            <button
                                onClick={handleAutoSpeakToggle}
                                disabled={!wsConnected}
                                className={cn(
                                    'flex items-center gap-2 px-3 py-1.5 rounded-[8px] transition-all text-sm font-[Lexend]',
                                    autoSpeakEnabled
                                        ? 'bg-[#DBEAFE] text-[#1E40AF] hover:bg-[#BFDBFE]'
                                        : 'bg-[#F1F5F9] text-[#64748B] hover:bg-[#E2E8F0]',
                                    !wsConnected && 'opacity-50 cursor-not-allowed'
                                )}
                                title={autoSpeakEnabled ? 'Auto-speak enabled' : 'Auto-speak disabled'}
                            >
                                {autoSpeakEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
                                <span className="hidden lg:inline">
                                    {autoSpeakEnabled ? 'TTS On' : 'TTS Off'}
                                </span>
                            </button>
                        )}

                        <Timer
                            seconds={interview.timer}
                            totalSeconds={durationInSeconds}
                            onTick={handleTimerTick}
                        />
                        
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={handlePauseResume}
                            disabled={!wsConnected}
                        >
                            {isPaused ? <Play size={16} /> : <Pause size={16} />}
                            {isPaused ? 'Resume' : 'Pause'}
                        </Button>
                    </div>

                    <Button variant="destructive" size="sm" onClick={() => setShowEndModal(true)}>
                        <X size={18} className="mr-2" />
                        End Interview
                    </Button>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Chat Panel */}
                <div className="flex-1 flex flex-col border-r border-[#E5E7EB] lg:w-[70%]">
                    <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-6 space-y-6 bg-white">
                        {interview.messages.length === 0 && !interview.isEvaluating && (
                            <div className="text-center py-12">
                                <Bot size={48} className="text-[#94A3B8] mx-auto mb-4" />
                                <p className="text-[#475569] font-[Lexend]">
                                    {wsConnected ? 'Interview starting soon...' : 'Connecting to interview session...'}
                                </p>
                            </div>
                        )}
                        
                        <AnimatePresence mode="popLayout">
                            {interview.messages.map((message) => (
                                <ChatMessage key={message.id} message={message} />
                            ))}
                        </AnimatePresence>
                        
                        {interview.isEvaluating && <TypingIndicator />}
                    </div>

                    <div className="flex-shrink-0 p-6 border-t border-[#E5E7EB] bg-[#F8FAFC]">
                        {mode === 'text' ? (
                            <ChatInput
                                onSend={handleSendMessage}
                                disabled={!wsConnected || interview.isEvaluating || isPaused}
                                placeholder={
                                    !wsConnected ? "Connecting..." :
                                    isPaused ? "Interview paused..." :
                                    interview.isEvaluating ? "AI is evaluating your response..." :
                                    "Type your answer..."
                                }
                            />
                        ) : (
                            <VoiceInput
                                onSend={handleSendMessage}
                                disabled={!wsConnected || interview.isEvaluating || isPaused}
                                autoSpeak={autoSpeakEnabled}
                                onAutoSpeakChange={setAutoSpeakEnabled}
                            />
                        )}
                    </div>
                </div>

                {/* Feedback Panel */}
                <div className="hidden lg:block w-[30%] p-6 overflow-y-auto bg-[#F8FAFC]">
                    <h2 className="text-lg font-semibold text-[#0F172A] mb-6 font-[Lora]">Real-time Feedback</h2>
                    <FeedbackPanel
                        feedback={interview.feedback as any}
                        isEvaluating={interview.isEvaluating}
                    />
                    
                    {/* Interview Progress */}
                    <div className="mt-6 p-4 bg-white rounded-[12px] border border-[#E5E7EB]">
                        <h3 className="font-medium text-[#0F172A] mb-3 font-[Lora]">Progress</h3>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-[#475569] font-[Lexend]">Mode</span>
                                <span className="text-[#0F172A] font-[Lexend] capitalize">{mode}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-[#475569] font-[Lexend]">Questions</span>
                                <span className="text-[#0F172A] font-[Lexend]">{interview.currentTurn}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-[#475569] font-[Lexend]">Feedback</span>
                                <span className="text-[#0F172A] font-[Lexend]">{interview.allFeedbacks.length}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-[#475569] font-[Lexend]">Time Left</span>
                                <span className="text-[#0F172A] font-[Lexend]">{formattedTimer()}</span>
                            </div>
                            {mode === 'voice' && (
                                <div className="flex justify-between text-sm">
                                    <span className="text-[#475569] font-[Lexend]">TTS</span>
                                    <span className={cn(
                                        "font-[Lexend] font-medium",
                                        autoSpeakEnabled ? "text-[#10B981]" : "text-[#94A3B8]"
                                    )}>
                                        {autoSpeakEnabled ? 'Active' : 'Inactive'}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <ConfirmModal
                isOpen={showEndModal}
                onClose={() => setShowEndModal(false)}
                onConfirm={handleEndInterview}
                title="End Interview?"
                message="Are you sure you want to end this interview session? Your progress will be saved and you'll receive a detailed summary."
                confirmText="End Interview"
                cancelText="Continue"
                variant="destructive"
            />
        </div>
    );
}

function LiveInterviewPage() {
    return (
        <Suspense fallback={
            <div className="h-screen flex items-center justify-center bg-white">
                <div className="w-10 h-10 border-4 border-[#E5E7EB] border-t-[#0D9488] rounded-full animate-spin" />
            </div>
        }>
            <LiveInterviewContent />
        </Suspense>
    );
}

export default withAuth(LiveInterviewPage);