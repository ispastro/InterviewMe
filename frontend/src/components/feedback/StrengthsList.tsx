'use client';

import { motion } from 'framer-motion';
import { CheckCircle } from 'lucide-react';

interface StrengthsListProps {
    items: string[];
}

export function StrengthsList({ items }: StrengthsListProps) {
    // Handle undefined, null, or empty arrays
    if (!items || !Array.isArray(items) || items.length === 0) {
        return null;
    }

    return (
        <div>
            <h4 className="text-sm font-semibold text-[#059669] mb-3 flex items-center gap-2 font-[Lora]">
                <CheckCircle size={16} />
                What You Did Well
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
                        <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] mt-2 flex-shrink-0" />
                        {item}
                    </motion.li>
                ))}
            </ul>
        </div>
    );
}
