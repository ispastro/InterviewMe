'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ScoreCardProps {
    label: string;
    score: number; // 1-5
    maxScore?: number;
    color?: 'blue' | 'green' | 'amber' | 'purple' | 'rose';
}

export function ScoreCard({ label, score, maxScore = 5, color = 'blue' }: ScoreCardProps) {
    const percentage = (score / maxScore) * 100;

    const colors = {
        blue: 'bg-[#0D9488]',
        green: 'bg-[#10B981]',
        amber: 'bg-[#F59E0B]',
        purple: 'bg-[#8B5CF6]',
        rose: 'bg-[#F43F5E]',
    };

    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between">
                <span className="text-sm text-[#475569] font-[Lexend]">{label}</span>
                <span className="text-sm font-semibold text-[#0F172A] font-[Lexend]">
                    {score}/{maxScore}
                </span>
            </div>
            <div className="h-2 bg-[#E5E7EB] rounded-full overflow-hidden">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                    className={cn('h-full rounded-full', colors[color])}
                />
            </div>
        </div>
    );
}
