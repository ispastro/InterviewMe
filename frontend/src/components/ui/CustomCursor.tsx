'use client';

import React, { useEffect, useState } from 'react';
import { motion, useSpring, useMotionValue } from 'framer-motion';

export function CustomCursor() {
  const [isHovering, setIsHovering] = useState(false);
  const mouseX = useMotionValue(-100);
  const mouseY = useMotionValue(-100);

  const springConfig = { damping: 25, stiffness: 250 };
  const cursorX = useSpring(mouseX, springConfig);
  const cursorY = useSpring(mouseY, springConfig);

  useEffect(() => {
    const moveMouse = (e: MouseEvent) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
    };

    const handleHover = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'BUTTON' || 
        target.tagName === 'A' || 
        target.closest('button') || 
        target.closest('a') ||
        target.classList.contains('cursor-pointer')
      ) {
        setIsHovering(true);
      } else {
        setIsHovering(false);
      }
    };

    window.addEventListener('mousemove', moveMouse);
    window.addEventListener('mouseover', handleHover);

    return () => {
      window.removeEventListener('mousemove', moveMouse);
      window.removeEventListener('mouseover', handleHover);
    };
  }, [mouseX, mouseY]);

  return (
    <div className="fixed inset-0 pointer-events-none z-[9999] hidden lg:block">
      {/* Main Reticle */}
      <motion.div
        style={{
          x: cursorX,
          y: cursorY,
          translateX: '-50%',
          translateY: '-50%',
        }}
        className="relative"
      >
        {/* Core Dot */}
        <div className={`w-1 h-1 rounded-full bg-white transition-transform duration-300 ${isHovering ? 'scale-[3]' : 'scale-100'}`} />
        
        {/* Revolving Ring */}
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
          className={`absolute inset-0 -m-3 w-6 h-6 border rounded-full border-white/20 border-t-white/80 transition-all duration-300 ${isHovering ? 'scale-[1.5] opacity-100' : 'scale-100 opacity-40'}`} 
        />

        {/* Orbiting Elements */}
        <motion.div 
          animate={{ rotate: -360 }}
          transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
          className="absolute inset-0 -m-6 w-12 h-12 border-[0.5px] border-dashed border-white/10 rounded-full" 
        />

        {/* Status Label */}
        <div className="absolute top-8 left-8 flex flex-col gap-1 whitespace-nowrap">
            <span className="text-[8px] font-black tracking-[0.3em] text-white/40 uppercase">Mode: Session_Scan</span>
            <div className="flex items-center gap-2">
                <div className="w-1 h-1 rounded-full bg-blue-500 animate-pulse" />
                <span className="text-[7px] font-bold text-blue-500/80 uppercase tracking-widest">Calibration_Active</span>
            </div>
        </div>
      </motion.div>

      {/* Global Cursor Hide Override */}
      <style jsx global>{`
        body {
          cursor: none !important;
        }
        a, button, [role="button"] {
          cursor: none !important;
        }
      `}</style>
    </div>
  );
}
