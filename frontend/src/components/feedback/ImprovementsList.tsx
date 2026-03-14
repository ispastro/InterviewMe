'use client';

import { motion } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';

interface ImprovementsListProps {
    items: string[];
}

export function ImprovementsList({ items }: ImprovementsListProps) {
    // Handle undefined, null, or empty arrays
    if (!items || !Array.isArray(items) || items.length === 0) {
        return null;
    }

    return (
        <div>
            <h4 className="text-sm font-semibold text-[#D97706] mb-3 flex items-center gap-2 font-[Lora]">
                <AlertTriangle size={16} />
                Areas to Improve
            </h4>
            <ul className="space-y-2">
                {items.map((item, index) => (
                    <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-start gap-2 text-sm text-[#475569] font-[Lexend]"
                    >
                        <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B] mt-2 flex-shrink-0" />
                        {item}
                    </motion.li>
                ))}
            </ul>
        </div>
    );
}
