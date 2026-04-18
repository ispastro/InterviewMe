'use client';

import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter, useSearchParams } from 'next/navigation';
import { Bot, X, Wifi, WifiOff, Pause, Play, AlertCircle, Volume2, VolumeX } from 'lucide-react';
import { Button, ConfirmModal, toast } from '@/components/ui';
import { ChatMessage, TypingIndicator, ChatInput, VoiceInput } from '@/components/chat';
import { FeedbackPanel } from '@/components/feedback';
import { Timer } from '@/components/Timer';
import { InterviewerAvatar } from '@/components/InterviewerAvatar';
import { useAuth } from '@/contexts/AuthContext';
import { useWebSocket, useSpeech } from '@/hooks';
import { useInterviewStore, useIsConnected, useIsActive, useFormattedTimer, useSettingsSelectors } from '@/stores';
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
    const isConnected = useIsConnected();
    const isActive = useIsActive();
    const formattedTimer = useFormattedTimer();
    const { mode, durationInSeconds } = useSettingsSelectors();

    // Local state
    const [showEndModal, setShowEndModal] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [connectionError, setConnectionError] = useState<string | null>(null);
    const [autoSpeakEnabled, setAutoSpeakEnabled] = useState(true);
    const [streamingMessage, setStreamingMessage] = useState<string>('');
    const [isStreaming, setIsStreaming] = useState(false);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const lastSpokenMessageRef = useRef<string | null>(null);
    const hasStartedRef = useRef(false);

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
            toast.success('Connected to interview session');
            interview.setSessionId(sessionId);
            // Only start the interview ONCE — skip on reconnects
            if (!hasStartedRef.current) {
                hasStartedRef.current = true;
                setTimeout(() => {
                    startInterview();
                }, 1000);
            } else {
                console.log('♻️ Reconnected — skipping startInterview (already started)');
            }
        },
        onDisconnect: () => {
            console.log('❌ Disconnected from interview session');
            toast.error('Connection lost. Reconnecting...');
            setConnectionError('Connection lost. Attempting to reconnect...');
        },
        onError: (error) => {
            console.error('❌ WebSocket error:', error);
            toast.error(error.message);
            setConnectionError(error.message);
        },
        onStreaming: (chunk, isComplete) => {
            if (isComplete) {
                // Streaming complete
                setIsStreaming(false);
                setStreamingMessage('');
            } else {
                // Accumulate chunks
                setIsStreaming(true);
                setStreamingMessage(prev => prev + chunk);
            }
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
        if (!message.trim()) return;

        // Guard: Check connection and session state
        if (!wsConnected) {
            console.warn('⚠️ Cannot send message: not connected');
            return;
        }

        // Guard: Check if interview is active
        if (!isActive) {
            console.warn('⚠️ Cannot send message: interview not active');
            return;
        }

        // Guard: Check if currently evaluating
        if (interview.isEvaluating) {
            console.warn('⚠️ Cannot send message: AI is evaluating');
            return;
        }

        // Guard: Check if paused
        if (isPaused) {
            console.warn('⚠️ Cannot send message: interview is paused');
            return;
        }

        // Stop any ongoing speech before sending
        stopSpeech();

        sendAnswer(message);
    }, [wsConnected, isActive, interview.isEvaluating, isPaused, sendAnswer, stopSpeech]);

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
            <div className="h-screen flex items-center justify-center bg-slate-950 text-slate-100">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-slate-700 border-t-[#0D9488] rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-slate-400 font-[Lexend]">Connecting to interview session...</p>
                </div>
            </div>
        );
    }

    // Show error state if connection failed
    if (wsError && !wsConnected) {
        return (
            <div className="h-screen flex items-center justify-center bg-slate-950 text-slate-100">
                <div className="text-center max-w-md">
                    <AlertCircle size={48} className="text-[#EF4444] mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-white mb-2 font-[Lora]">Connection Failed</h2>
                    <p className="text-slate-400 mb-6 font-[Lexend]">{wsError}</p>
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
        <div className="relative h-screen flex flex-col overflow-hidden bg-slate-950 text-slate-100">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(45,212,191,0.08),transparent_45%),radial-gradient(ellipse_at_bottom,rgba(2,6,23,0.96),rgba(2,6,23,1))]" />
            <div className="pointer-events-none absolute left-1/2 top-[-16rem] h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-teal-400/10 blur-[140px]" />

            {/* Top Bar */}
            <header className="relative z-10 flex-shrink-0 px-4 sm:px-6 py-3 sm:py-4 bg-slate-950/75 border-b border-slate-800/80 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 sm:gap-4 min-w-0">
                        <InterviewerAvatar isThinking={interview.isEvaluating} />
                        <div className="min-w-0">
                            <p className="font-semibold text-white font-[Lora] text-sm sm:text-base truncate">AI Interviewer</p>
                            <div className="flex items-center gap-2 text-xs sm:text-sm font-[Lexend]">
                                {wsConnected ? (
                                    <span className="flex items-center gap-1 text-[#10B981]">
                                        <Wifi size={12} className="sm:w-3.5 sm:h-3.5" />
                                        <span className="hidden sm:inline">Connected</span>
                                    </span>
                                ) : (
                                    <span className="flex items-center gap-1 text-[#EF4444]">
                                        <WifiOff size={12} className="sm:w-3.5 sm:h-3.5" />
                                        <span className="hidden sm:inline">{connectionError || 'Disconnected'}</span>
                                    </span>
                                )}
                                {isPaused && (
                                    <span className="text-[#F59E0B] hidden sm:inline">• Paused</span>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 sm:gap-4">
                        {/* Auto-speak toggle (voice mode only) */}
                        {mode === 'voice' && isSynthesisSupported && (
                            <button
                                onClick={handleAutoSpeakToggle}
                                disabled={!wsConnected}
                                className={cn(
                                    'flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 rounded-[8px] transition-all text-xs sm:text-sm font-[Lexend]',
                                    autoSpeakEnabled
                                        ? 'bg-teal-500/15 text-teal-300 hover:bg-teal-500/20 border border-teal-400/20'
                                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700',
                                    !wsConnected && 'opacity-50 cursor-not-allowed'
                                )}
                                title={autoSpeakEnabled ? 'Auto-speak enabled' : 'Auto-speak disabled'}
                            >
                                {autoSpeakEnabled ? <Volume2 size={14} className="sm:w-4 sm:h-4" /> : <VolumeX size={14} className="sm:w-4 sm:h-4" />}
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
                            className="hidden sm:flex border-slate-700 bg-slate-800 text-slate-100 hover:bg-slate-700"
                        >
                            {isPaused ? <Play size={16} /> : <Pause size={16} />}
                            <span className="hidden md:inline ml-2">{isPaused ? 'Resume' : 'Pause'}</span>
                        </Button>
                    </div>

                    <Button variant="destructive" size="sm" onClick={() => setShowEndModal(true)} className="text-xs sm:text-sm">
                        <X size={14} className="sm:w-4 sm:h-4 sm:mr-2" />
                        <span className="hidden sm:inline">End</span>
                    </Button>
                </div>
            </header>

            {/* Main Content */}
            <div className="relative z-10 flex-1 flex overflow-hidden">
                {/* Chat Panel */}
                <div className="flex-1 flex flex-col border-r border-slate-800 lg:w-[70%]">
                    <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-4 sm:space-y-6 bg-slate-950/30">
                        {interview.messages.length === 0 && !interview.isEvaluating && (
                            <div className="text-center py-12">
                                <Bot size={48} className="text-slate-500 mx-auto mb-4" />
                                <p className="text-slate-400 font-[Lexend]">
                                    {wsConnected ? 'Interview starting soon...' : 'Connecting to interview session...'}
                                </p>
                            </div>
                        )}

                        <AnimatePresence mode="popLayout">
                            {interview.messages.map((message) => (
                                <ChatMessage key={message.id} message={message} />
                            ))}
                            
                            {/* Streaming message */}
                            {isStreaming && streamingMessage && (
                                <ChatMessage
                                    key="streaming"
                                    message={{
                                        id: 'streaming',
                                        sender: 'interviewer',
                                        message: streamingMessage,
                                        timestamp: new Date(),
                                        streaming: true,
                                    } as ChatMessageType}
                                />
                            )}
                        </AnimatePresence>

                        {interview.isEvaluating && !isStreaming && <TypingIndicator />}
                    </div>

                    <div className="flex-shrink-0 p-3 sm:p-6 border-t border-slate-800 bg-slate-900/45">
                        {mode === 'text' ? (
                            <ChatInput
                                onSend={handleSendMessage}
                                disabled={!wsConnected || interview.isEvaluating || isPaused || !isActive}
                                placeholder={
                                    !wsConnected ? "Connecting..." :
                                        !isActive ? "Starting interview..." :
                                            isPaused ? "Interview paused..." :
                                                interview.isEvaluating ? "AI is evaluating your response..." :
                                                    "Type your answer..."
                                }
                            />
                        ) : (
                            <VoiceInput
                                onSend={handleSendMessage}
                                disabled={!wsConnected || interview.isEvaluating || isPaused || !isActive}
                                autoSpeak={autoSpeakEnabled}
                                onAutoSpeakChange={setAutoSpeakEnabled}
                            />
                        )}
                    </div>
                </div>

                {/* Feedback Panel */}
                <div className="hidden lg:block w-[30%] p-6 overflow-y-auto bg-slate-900/55">
                    <h2 className="text-lg font-semibold text-white mb-6 font-[Lora]">Real-time Feedback</h2>
                    <FeedbackPanel
                        feedback={interview.feedback as any}
                        isEvaluating={interview.isEvaluating}
                    />

                    {/* Interview Progress */}
                    <div className="mt-6 p-4 rounded-[12px] border border-slate-700 bg-slate-900/80">
                        <h3 className="font-medium text-white mb-3 font-[Lora]">Progress</h3>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400 font-[Lexend]">Mode</span>
                                <span className="text-slate-100 font-[Lexend] capitalize">{mode}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400 font-[Lexend]">Questions</span>
                                <span className="text-slate-100 font-[Lexend]">{interview.currentTurn}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400 font-[Lexend]">Feedback</span>
                                <span className="text-slate-100 font-[Lexend]">{interview.allFeedbacks.length}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400 font-[Lexend]">Time Left</span>
                                <span className="text-slate-100 font-[Lexend]">{formattedTimer}</span>
                            </div>
                            {mode === 'voice' && (
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-400 font-[Lexend]">TTS</span>
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
            <div className="h-screen flex items-center justify-center bg-slate-950">
                <div className="w-10 h-10 border-4 border-slate-700 border-t-[#0D9488] rounded-full animate-spin" />
            </div>
        }>
            <LiveInterviewContent />
        </Suspense>
    );
}

export default withAuth(LiveInterviewPage);