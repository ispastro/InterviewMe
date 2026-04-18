'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { ChatMessage as ChatMessageType } from '@/types';
import { Bot, User } from 'lucide-react';

interface ChatMessageProps {
    message: ChatMessageType;
}

export const ChatMessage = React.memo(function ChatMessage({ message }: ChatMessageProps) {
    const isUser = message.sender === 'user';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className={cn(
                'flex gap-3',
                isUser ? 'flex-row-reverse' : 'flex-row'
            )}
        >
            {/* Avatar */}
            <div
                className={cn(
                    'flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center',
                    isUser
                        ? 'bg-[#0D9488]'
                        : 'bg-[#0F172A]'
                )}
            >
                {isUser ? (
                    <User size={18} className="text-white" />
                ) : (
                    <Bot size={18} className="text-white" />
                )}
            </div>

            {/* Message Bubble */}
            <div
                className={cn(
                    'max-w-[70%] rounded-[16px] px-4 py-3',
                    isUser
                        ? 'bg-teal-500/18 border border-teal-400/25 text-slate-100 rounded-tr-[4px]'
                        : 'bg-slate-900/85 border border-slate-700 text-slate-100 rounded-tl-[4px]'
                )}
            >
                <p className="text-sm leading-relaxed whitespace-pre-wrap font-[Lexend]">
                    {message.message}
                    {message.streaming && (
                        <span className="inline-block ml-1 animate-pulse text-slate-400">▊</span>
                    )}
                </p>
                <p className="text-xs mt-2 text-slate-400 font-[Lexend]">
                    {new Date(message.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                    })}
                </p>
            </div>
        </motion.div>
    );
});

ChatMessage.displayName = 'ChatMessage';
