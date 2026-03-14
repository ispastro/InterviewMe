'use client';

import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
        const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed font-[Lexend]';

        const variants = {
            primary: 'bg-[#0D9488] text-white hover:bg-[#0F766E] focus:ring-[#0D9488] shadow-sm',
            secondary: 'bg-[#F1F5F9] text-[#0F172A] hover:bg-[#E2E8F0] focus:ring-[#94A3B8] border border-[#E5E7EB]',
            outline: 'border border-[#E5E7EB] text-[#0F172A] hover:bg-[#F8FAFC] focus:ring-[#94A3B8]',
            ghost: 'text-[#475569] hover:text-[#0F172A] hover:bg-[#F8FAFC] focus:ring-[#94A3B8]',
            destructive: 'bg-[#EF4444] text-white hover:bg-[#DC2626] focus:ring-[#EF4444]',
        };

        const sizes = {
            sm: 'text-sm px-3 py-1.5 rounded-[10px]',
            md: 'text-sm px-4 py-2.5 rounded-[12px]',
            lg: 'text-base px-6 py-3 rounded-[12px]',
        };

        return (
            <button
                ref={ref}
                className={cn(baseStyles, variants[variant], sizes[size], className)}
                disabled={disabled || isLoading}
                {...props}
            >
                {isLoading ? (
                    <>
                        <svg
                            className="animate-spin -ml-1 mr-2 h-4 w-4"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                        >
                            <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                strokeWidth="4"
                            />
                            <path
                                className="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                        </svg>
                        Loading...
                    </>
                ) : (
                    children
                )}
            </button>
        );
    }
);

Button.displayName = 'Button';
