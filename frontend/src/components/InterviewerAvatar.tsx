'use client';

import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';
import { cn } from '@/lib/utils';

interface InterviewerAvatarProps {
    isThinking?: boolean;
    isSpeaking?: boolean;
    size?: 'sm' | 'md' | 'lg';
}

export function InterviewerAvatar({
    isThinking = false,
    isSpeaking = false,
    size = 'md'
}: InterviewerAvatarProps) {
    const sizes = {
        sm: 'w-9 h-9',
        md: 'w-12 h-12',
        lg: 'w-16 h-16',
    };

    const iconSizes = {
        sm: 18,
        md: 24,
        lg: 32,
    };

    return (
        <div className="relative">
            {/* Glow effect when thinking */}
            {isThinking && (
                <motion.div
                    className={cn(
                        'absolute inset-0 rounded-full bg-[#0D9488]/20 blur-lg',
                        sizes[size]
                    )}
                    animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.3, 0.5, 0.3],
                    }}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: 'easeInOut',
                    }}
                />
            )}

            {/* Avatar */}
            <motion.div
                className={cn(
                    'relative rounded-full bg-[#0F172A]',
                    'flex items-center justify-center shadow-md',
                    sizes[size]
                )}
                animate={
                    isSpeaking
                        ? { scale: [1, 1.05, 1] }
                        : isThinking
                            ? { rotate: [0, 3, -3, 0] }
                            : { y: [0, -1, 0] }
                }
                transition={{
                    duration: isSpeaking ? 0.3 : 2,
                    repeat: Infinity,
                    ease: 'easeInOut',
                }}
            >
                <Bot size={iconSizes[size]} className="text-white" />
            </motion.div>

            {/* Status indicator */}
            <div
                className={cn(
                    'absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-white',
                    isThinking ? 'bg-[#F59E0B]' : 'bg-[#10B981]'
                )}
            />
        </div>
    );
}
