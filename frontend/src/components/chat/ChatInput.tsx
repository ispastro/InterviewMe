'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Send } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
    onSend: (message: string) => void;
    disabled?: boolean;
    placeholder?: string;
}

export function ChatInput({ onSend, disabled = false, placeholder = 'Type your answer...' }: ChatInputProps) {
    const [message, setMessage] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
        }
    }, [message]);

    const handleSubmit = useCallback((e: React.FormEvent) => {
        e.preventDefault();
        if (message.trim() && !disabled) {
            onSend(message.trim());
            setMessage('');
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        }
    }, [message, onSend, disabled]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e as any);
        }
    }, [handleSubmit]);

    return (
        <form onSubmit={handleSubmit} className="relative">
            <div className="flex items-end gap-3 p-4 bg-slate-900/85 border border-slate-700 rounded-[16px] shadow-[0px_8px_24px_rgba(2,6,23,0.35)]">
                <textarea
                    ref={textareaRef}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    disabled={disabled}
                    rows={1}
                    className={cn(
                        'flex-1 bg-transparent text-slate-100 placeholder:text-slate-500 resize-none font-[Lexend] text-sm',
                        'focus:outline-none',
                        'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                />
                <button
                    type="submit"
                    disabled={disabled || !message.trim()}
                    className={cn(
                        'flex-shrink-0 w-10 h-10 rounded-[12px] flex items-center justify-center',
                        'bg-[#0D9488] hover:bg-[#0F766E]',
                        'text-white transition-all duration-200',
                        'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                >
                    <Send size={18} />
                </button>
            </div>
        </form>
    );
}
