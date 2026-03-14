'use client';

import { motion } from 'framer-motion';

interface LoadingOverlayProps {
    message?: string;
}

export function LoadingOverlay({ message = 'Processing...' }: LoadingOverlayProps) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm"
        >
            <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-4 border-4 border-[#E5E7EB] border-t-[#0D9488] rounded-full animate-spin" />
                <p className="text-[#0F172A] font-medium font-[Lexend]">{message}</p>
            </div>
        </motion.div>
    );
}
