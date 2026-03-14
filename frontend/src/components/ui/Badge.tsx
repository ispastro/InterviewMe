'use client';

import { cn } from '@/lib/utils';

interface BadgeProps {
    children: React.ReactNode;
    variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
    className?: string;
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
    const variants = {
        default: 'bg-[#F1F5F9] text-[#475569] border-[#E5E7EB]',
        success: 'bg-[#ECFDF5] text-[#059669] border-[#A7F3D0]',
        warning: 'bg-[#FFFBEB] text-[#D97706] border-[#FDE68A]',
        error: 'bg-[#FEF2F2] text-[#DC2626] border-[#FECACA]',
        info: 'bg-[#F0FDFA] text-[#0D9488] border-[#99F6E4]',
    };

    return (
        <span
            className={cn(
                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border font-[Lexend]',
                variants[variant],
                className
            )}
        >
            {children}
        </span>
    );
}
