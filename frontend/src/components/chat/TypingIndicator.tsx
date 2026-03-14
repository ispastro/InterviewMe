'use client';

import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';

export function TypingIndicator() {
    return (
        <div className="flex gap-3">
            {/* Avatar */}
            <div className="flex-shrink-0 w-9 h-9 rounded-full bg-[#0F172A] flex items-center justify-center">
                <Bot size={18} className="text-white" />
            </div>

            {/* Typing Bubble */}
            <div className="bg-[#F1F5F9] rounded-[16px] rounded-tl-[4px] px-4 py-3">
                <div className="flex gap-1.5">
                    {[0, 1, 2].map((i) => (
                        <motion.div
                            key={i}
                            className="w-2 h-2 rounded-full bg-[#94A3B8]"
                            animate={{
                                y: [0, -6, 0],
                                opacity: [0.5, 1, 0.5],
                            }}
                            transition={{
                                duration: 0.8,
                                repeat: Infinity,
                                delay: i * 0.15,
                            }}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
