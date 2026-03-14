'use client';

import { motion } from 'framer-motion';
import type { Feedback } from '@/types';
import { ScoreCard } from './ScoreCard';
import { StrengthsList } from './StrengthsList';
import { ImprovementsList } from './ImprovementsList';
import { ModelAnswer } from './ModelAnswer';

interface FeedbackPanelProps {
    feedback: Feedback | null;
    isEvaluating?: boolean;
}

export function FeedbackPanel({ feedback, isEvaluating = false }: FeedbackPanelProps) {
    if (isEvaluating) {
        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full flex items-center justify-center"
            >
                <div className="text-center">
                    <div className="w-10 h-10 mx-auto mb-4 border-4 border-[#E5E7EB] border-t-[#0D9488] rounded-full animate-spin" />
                    <p className="text-[#475569] font-[Lexend]">Evaluating your answer...</p>
                </div>
            </motion.div>
        );
    }

    if (!feedback) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="text-center text-[#94A3B8] font-[Lexend]">
                    <p>Answer a question to see feedback</p>
                </div>
            </div>
        );
    }

    const scoreColors = ['blue', 'green', 'purple', 'amber', 'rose'] as const;
    const scoreLabels = [
        { key: 'communication_skills', label: 'Communication' },
        { key: 'confidence', label: 'Confidence' },
        { key: 'clarity', label: 'Structure (STAR)' },
        { key: 'technical_knowledge', label: 'Technical Depth' },
        { key: 'relevance', label: 'Relevance' },
    ] as const;

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
            className="space-y-6 overflow-y-auto max-h-full pb-4"
        >
            {/* Score Breakdown */}
            <div>
                <h3 className="text-lg font-semibold text-[#0F172A] mb-4 font-[Lora]">Score Breakdown</h3>
                <div className="space-y-4">
                    {scoreLabels.map((item, index) => (
                        <ScoreCard
                            key={item.key}
                            label={item.label}
                            score={feedback?.criteria_scores?.[item.key] || 0}
                            color={scoreColors[index]}
                        />
                    ))}
                </div>
            </div>

            {/* Strengths */}
            <StrengthsList items={feedback?.strengths || []} />

            {/* Improvements */}
            <ImprovementsList items={feedback?.weaknesses || []} />

            {/* Model Answer */}
            {feedback?.modelAnswer && (
                <ModelAnswer answer={feedback.modelAnswer} />
            )}
        </motion.div>
    );
}
