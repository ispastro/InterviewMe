'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Lightbulb } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ModelAnswerProps {
    answer: string;
}

export function ModelAnswer({ answer }: ModelAnswerProps) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="border border-[#E5E7EB] rounded-[16px] overflow-hidden">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between p-4 bg-[#F8FAFC] hover:bg-[#F1F5F9] transition-colors"
            >
                <span className="flex items-center gap-2 text-sm font-semibold text-[#0D9488] font-[Lora]">
                    <Lightbulb size={16} />
                    Suggested Model Answer
                </span>
                <motion.div
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                >
                    <ChevronDown size={18} className="text-[#94A3B8]" />
                </motion.div>
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="p-4 border-t border-[#E5E7EB] bg-white">
                            <p className="text-sm text-[#475569] leading-relaxed whitespace-pre-wrap font-[Lexend]">
                                {answer}
                            </p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
