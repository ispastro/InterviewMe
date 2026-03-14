'use client';

import { motion } from 'framer-motion';
import { Mic, MicOff } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MicButtonProps {
    isRecording: boolean;
    onClick: () => void;
    disabled?: boolean;
}

export function MicButton({ isRecording, onClick, disabled = false }: MicButtonProps) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={cn(
                'relative w-14 h-14 rounded-full flex items-center justify-center',
                'transition-all duration-200',
                'focus:outline-none focus:ring-4',
                isRecording
                    ? 'bg-[#EF4444] text-white focus:ring-[#EF4444]/30'
                    : 'bg-[#F1F5F9] text-[#475569] hover:bg-[#E2E8F0] focus:ring-[#94A3B8]/30 border border-[#E5E7EB]',
                disabled && 'opacity-50 cursor-not-allowed'
            )}
        >
            {/* Pulse animation when recording */}
            {isRecording && (
                <>
                    <motion.div
                        className="absolute inset-0 rounded-full bg-[#EF4444]"
                        animate={{
                            scale: [1, 1.3, 1],
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
                            scale: [1, 1.2, 1],
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
                {isRecording ? <MicOff size={22} /> : <Mic size={22} />}
            </div>
        </button>
    );
}
