'use client';

import { useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { formatTime } from '@/lib/utils';

interface TimerProps {
    seconds: number;
    totalSeconds: number;
    onTick?: () => void;
}

export function Timer({ seconds, totalSeconds, onTick }: TimerProps) {
    const percentage = (seconds / totalSeconds) * 100;
    const circumference = 2 * Math.PI * 45;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    const colorClass = useMemo(() => {
        if (percentage > 50) return '#10B981';
        if (percentage > 25) return '#F59E0B';
        return '#EF4444';
    }, [percentage]);

    useEffect(() => {
        if (seconds > 0 && onTick) {
            const interval = setInterval(onTick, 1000);
            return () => clearInterval(interval);
        }
    }, [seconds, onTick]);

    return (
        <div className="relative w-20 h-20">
            {/* Background circle */}
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="#E5E7EB"
                    strokeWidth="6"
                />
                <motion.circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke={colorClass}
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    initial={{ strokeDashoffset: 0 }}
                    animate={{ strokeDashoffset }}
                    transition={{ duration: 0.5 }}
                />
            </svg>

            {/* Time display */}
            <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-semibold text-[#0F172A] font-[Lexend]">
                    {formatTime(seconds)}
                </span>
            </div>
        </div>
    );
}
