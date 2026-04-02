'use client';

import { motion } from 'framer-motion';
import { 
  FileText, 
  Search, 
  Zap, 
  Terminal, 
  ArrowRight, 
  Layout, 
  Cpu, 
  Layers, 
  CheckCircle2, 
  Activity 
} from 'lucide-react';
import { Spotlight } from '@/components/ui/Spotlight';

export function SynthesisNexus() {
  const steps = [
    {
      id: '01',
      title: 'Source Ingestion',
      description: 'The engine processes your professional trajectory and the target role specification.',
      details: ['resume_v2.pdf', 'stripe_tech_lead.md'],
      icon: FileText,
      color: 'text-indigo-400'
    },
    {
      id: '02',
      title: 'Neural Calibration',
      description: 'Mapping your experience against industry standards and company-specific culture.',
      details: ['Technical_Delta_Analysis', 'Culture_Fit_Mapping'],
      icon: Search,
      color: 'text-emerald-400'
    },
    {
      id: '03',
      title: 'Session Activation',
      description: 'A bespoke, live interview session is instantiated and optimized for session start.',
      details: ['Activating_Voice_Engine', 'Mock_Session_Ready'],
      icon: Zap,
      color: 'text-blue-400'
    }
  ];

  return (
    <div className="py-32 px-6 relative overflow-hidden bg-black grid-bg">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row items-end justify-between gap-12 mb-32">
          <div className="max-w-2xl space-y-6">
              <div className="geist-label !text-white/40">
                <Cpu size={12} className="inline mr-2" />
                Intelligence_Engine_v4
              </div>
            <h2 className="text-5xl md:text-7xl geist-tight text-white uppercase">
              Preparation <br />
              <span className="text-white/20">Pipeline.</span>
            </h2>
          </div>
          <div className="max-w-sm">
            <p className="geist-body">
              We treat your interview prep like a mission-critical session. Precision, speed, and real-time calibration.
            </p>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-px bg-white/10 border border-white/10 rounded-sm overflow-hidden">
          {steps.map((step, i) => (
            <Spotlight key={step.id} fillColor="rgba(255, 255, 255, 0.02)" className="border-none">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="bg-black p-16 group relative hover:bg-white/[0.01] transition-colors overflow-hidden h-full"
              >
                {/* Background Offset Number */}
                <div className="absolute -top-4 -right-4 text-[12rem] font-black text-white/[0.02] leading-none select-none group-hover:text-white/[0.04] transition-colors pointer-events-none">
                  {step.id}
                </div>

                <div className="space-y-12 relative z-10">
                  <div className="flex justify-between items-start">
                    <div className={`p-4 bg-black border border-white/5 rounded-sm ${step.color} group-hover:border-white/20 transition-colors shadow-xl`}>
                      <step.icon size={28} />
                    </div>
                    <span className="geist-label !text-[12px] opacity-20 !tracking-widest group-hover:opacity-100 transition-colors">STAGE_{step.id}</span>
                  </div>

                  <div className="space-y-6">
                    <h3 className="text-2xl geist-heading text-white">{step.title}</h3>
                    <p className="text-slate-500 text-sm leading-relaxed font-medium">{step.description}</p>
                  </div>

                  <div className="flex flex-col border-t border-white/5 pt-8">
                    <span className="text-[11px] font-black text-white leading-none tracking-tight">interview-me-ai / session-001</span>
                    <span className="geist-label !tracking-[0.4em] !text-[9px] mt-2 opacity-50">Interview_Mode (Active)</span>
                  </div>

                  <div className="pt-8 space-y-3">
                    <div className="geist-label !text-slate-800 flex items-center gap-2 border-b border-white/5 pb-2">
                      <Activity size={10} />
                      Processing_Signals
                    </div>
                    {step.details.map((detail, idx) => (
                      <div key={idx} className="geist-label !text-slate-500 flex items-center gap-3">
                        <div className="w-1.5 h-1.5 rounded-full bg-slate-900" />
                        {detail}
                      </div>
                    ))}
                  </div>

                  <div className="mt-auto pt-8 flex items-center justify-between geist-label !text-slate-700">
                    <span className="group-hover:text-white transition-colors">READY_FOR_SESSION</span>
                    <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform group-hover:text-white" />
                  </div>
                </div>

                {/* Hover highlight line */}
                <div className="absolute bottom-0 left-0 right-0 h-px bg-white/0 group-hover:bg-white/20 transition-all" />
              </motion.div>
            </Spotlight>
          ))}
        </div>

        {/* Live Status Board below */}
        <div className="mt-20 glass-card p-6 border-white/5 rounded-sm flex flex-wrap items-center justify-between gap-10">
           <div className="flex items-center gap-10">
              <div className="flex items-center gap-4">
                 <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
               <div className="flex flex-col">
                    <span className="geist-label !text-slate-600 !tracking-[0.2em] mb-1">Latency_Optimized</span>
                    <span className="text-[11px] font-bold text-white font-mono uppercase tracking-tight">GLOBAL_EDGE</span>
                 </div>
              </div>
              <div className="flex items-center gap-4">
                 <Activity size={16} className="text-indigo-400" />
                 <div className="flex flex-col">
                    <span className="geist-label !text-slate-600 !tracking-[0.2em] mb-1">Analysis_Precision</span>
                    <span className="text-[11px] font-bold text-white font-mono uppercase tracking-tight">99.2%</span>
                 </div>
              </div>
           </div>
           
           <div className="flex items-center gap-3 px-4 py-2 bg-white/5 border border-white/10 rounded-sm">
             <Terminal size={14} className="text-slate-500" />
             <span className="geist-label !text-slate-400">system_status --HEALTHY</span>
           </div>
        </div>
      </div>
    </div>
  );
}
