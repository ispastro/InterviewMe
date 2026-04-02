'use client';

import { motion } from 'framer-motion';
import { 
  Terminal, 
  ChevronRight, 
  Shield, 
  Activity, 
  Zap,
  Globe,
  Clock,
  Command
} from 'lucide-react';
import { useState, useEffect } from 'react';

export function InteractiveMockup() {
  const [step, setStep] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      setStep((prev) => (prev + 1) % 4);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (step === 0) {
      setLogs(['> Initializing session...', '> Loading neural weights...', '> Mode: Simulation_Alpha']);
    } else if (step === 1) {
      setLogs(prev => [...prev, '> Calibrating to Senior_Fullstack_JD.md', '> Analyzing candidate_trajectory.pdf']);
    } else if (step === 2) {
      setLogs(prev => [...prev, '> Detected signal: High Integrity', '> Recommended session: HARD_MODE']);
    } else {
      setLogs([]);
    }
  }, [step]);

  return (
    <div className="relative w-full max-w-5xl mx-auto group">
      {/* Vercel-style subtle top gradient */}
      <div className="absolute -top-[1px] left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent z-10" />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-black border border-white/10 rounded-sm shadow-2xl overflow-hidden"
      >
        {/* Header / Project Navbar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-black">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-sm bg-white flex items-center justify-center">
                <Shield size={18} className="text-black" />
              </div>
              <div className="flex flex-col">
                <span className="text-[11px] font-black text-white leading-none tracking-tight">interview-me-ai / session-001</span>
                <span className="geist-label !tracking-widest !text-[9px] mt-1 opacity-50">Interview_Mode (Active)</span>
              </div>
            </div>
            
            <div className="hidden md:flex items-center gap-4 border-l border-white/5 pl-6">
              <div className="geist-label">
                <Globe size={12} className="inline mr-2" />
                Global-Edge
              </div>
              <div className="geist-label border-l border-white/5 pl-4">
                <Clock size={12} className="inline mr-2" />
                24ms
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
             <div className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest">Live</span>
             </div>
             <button className="w-8 h-8 flex items-center justify-center border border-white/5 rounded-sm hover:bg-white/5 transition-colors">
                <Command size={14} className="text-slate-400" />
             </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex h-[400px]">
          {/* Main Monitor */}
          <div className="flex-1 flex flex-col bg-black">
            <div className="flex-1 p-8 space-y-6 overflow-hidden">
                <div className="space-y-4">
                    <div className="geist-label">Session Intelligence</div>
                    <div className="text-2xl font-bold text-white tracking-tight leading-tight max-w-xl uppercase">
                      {step === 0 && <span className="opacity-30">Awaiting session start...</span>}
                      {step === 1 && "Analyzing 'Resume' and 'JD' for alignment..."}
                      {step === 2 && "Synthesizing custom questions for 'Stripe / Tech Lead'."}
                      {step === 3 && "Interview session instantiated. Initializing voice engine."}
                    </div>
                </div>

                {/* Technical Meter */}
                <div className="grid grid-cols-3 gap-6 pt-8">
                   {[
                    { label: 'CALIBRATION', val: '98%', color: 'text-indigo-400' },
                    { label: 'INTENT_SIGNAL', val: 'HIGH', color: 'text-emerald-400' },
                    { label: 'SYSTEM_LOAD', val: '1.2ms', color: 'text-blue-400' }
                   ].map(item => (
                    <div key={item.label} className="space-y-2">
                        <div className="geist-label">{item.label}</div>
                        <div className={`text-xl font-bold font-mono ${item.color}`}>{item.val}</div>
                    </div>
                   ))}
                </div>
            </div>

            <div className="h-40 bg-black border-t border-white/5 p-6 space-y-4">
              <div className="geist-label !text-slate-600 flex items-center gap-2 border-b border-white/5 pb-2">
                <Terminal size={12} />
                Session_Intelligence
              </div>
              <div className="space-y-1.5 geist-mono h-full overflow-y-auto custom-scrollbar !text-[10px]">
                {logs.map((log, i) => (
                  <motion.div 
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    key={i} 
                    className="flex gap-4"
                  >
                    <span className="text-slate-800 select-none">[{new Date().toLocaleTimeString([], { hour12: false })}]</span>
                    <span>{log}</span>
                  </motion.div>
                ))}
                {logs.length > 0 && (
                   <motion.div 
                    animate={{ opacity: [1, 0] }}
                    transition={{ repeat: Infinity, duration: 0.8 }}
                    className="w-2 h-4 bg-white/20 inline-block ml-16" 
                   />
                )}
              </div>
            </div>
          </div>

          {/* Right Sidebar - Analytics Overlay */}
          <div className="w-64 border-l border-white/5 bg-[#050505] p-6 space-y-8 hidden md:block">
            <div className="space-y-12">
                <div className="space-y-4">
                    <div className="text-[9px] font-black text-slate-600 uppercase tracking-widest">Mastery_Score</div>
                    <div className="flex items-end gap-2">
                        <span className="text-4xl font-light text-white tracking-tighter">89</span>
                        <span className="text-sm font-bold text-slate-600 mb-1">/ 100</span>
                    </div>
                    <div className="h-1 bg-white/5 w-full">
                        <div className="h-full bg-white shimmer w-3/4" />
                    </div>
                </div>

                <div className="space-y-6 pt-4 border-t border-white/5">
                    <div className="text-[9px] font-black text-slate-600 uppercase tracking-widest">Active_Filters</div>
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-[10px] font-bold text-white/50">
                            <Activity size={10} className="text-indigo-400" /> RESUME_PARSER_ACTIVE
                        </div>
                        <div className="flex items-center gap-2 text-[10px] font-bold text-white/50">
                            <Zap size={10} className="text-blue-400" /> ANALYTICS_REALTIME
                        </div>
                    </div>
                </div>
            </div>

            <div className="mt-auto pt-8 border-t border-white/5">
                <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                    v2.4.0-stable
                </div>
            </div>
          </div>
        </div>
      </motion.div>
      
      {/* Visual background element */}
      <div className="absolute -bottom-10 -right-10 w-64 h-64 bg-indigo-500/5 blur-[100px] -z-10" />
    </div>
  );
}
