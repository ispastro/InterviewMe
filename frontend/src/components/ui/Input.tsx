'use client';

import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    icon?: React.ReactNode;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ className, label, error, icon, type = 'text', ...props }, ref) => {
        return (
            <div className="w-full">
                {label && (
                    <label className="block text-sm font-medium text-[#0F172A] mb-2 font-[Lexend]">
                        {label}
                    </label>
                )}
                <div className="relative">
                    {icon && (
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#94A3B8]">
                            {icon}
                        </div>
                    )}
                    <input
                        ref={ref}
                        type={type}
                        className={cn(
                            'w-full h-10 px-3 py-2 rounded-[12px] font-[Lexend] text-sm',
                            'bg-white border border-[#E5E7EB]',
                            'text-[#0F172A] placeholder:text-[#94A3B8]',
                            'focus:outline-none focus:ring-2 focus:ring-[#0D9488] focus:border-transparent',
                            'transition-all duration-200',
                            icon && 'pl-10',
                            error && 'border-[#EF4444] focus:ring-[#EF4444]',
                            className
                        )}
                        {...props}
                    />
                </div>
                {error && (
                    <p className="mt-2 text-sm text-[#EF4444] font-[Lexend]">{error}</p>
                )}
            </div>
        );
    }
);

Input.displayName = 'Input';

export { Input };
