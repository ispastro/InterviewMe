'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Sparkles, 
  Brain, 
  CheckCircle2, 
  MessageSquare, 
  Bot, 
  Terminal,
  Activity,
  Cpu,
  ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui';

export function InteractiveDemo() {
  const [input, setInput] = useState('');
  const [feedback, setFeedback] = useState<null | { score: number; tip: string; title: string }>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalyze = () => {
    if (!input.trim()) return;
    setIsAnalyzing(true);
    
    // Simulate AI analysis delay
    setTimeout(() => {
      setIsAnalyzing(false);
      setFeedback({
        score: Math.floor(Math.random() * 20) + 75, // 75-95
        title: "Senior Technical Alignment",
        tip: "Your keyword density is optimal. Recommendation: Elaborate on the 'State Synchronization' trade-offs for Next.js 14 server components."
      });
    }, 2000);
  };

  return (
    <div id="demo" className="py-32 px-6 relative overflow-hidden bg-black grid-bg">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-end justify-between gap-12 mb-24">
          <div className="max-w-2xl space-y-6">
            <div className="geist-label !text-white/40">
              <Activity size={12} className="inline mr-2" />
              Live_Calibration_Module
            </div>
            <h2 className="text-5xl md:text-7xl geist-tight text-white uppercase">
              Instant <span className="text-white/30">Calibration.</span>
            </h2>
          </div>
          <p className="text-slate-500 text-lg max-w-sm font-medium leading-relaxed">
            Test our evaluation engine. Type a technical response and see how the AI ranks your depth and clarity.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-px bg-white/10 border border-white/10 rounded-sm overflow-hidden shadow-2xl">
          {/* Question & Input */}
          <div className="bg-black p-12 space-y-10">
            <div className="space-y-8">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-sm bg-white flex items-center justify-center flex-shrink-0">
                  <Cpu size={20} className="text-black" />
                </div>
                <div className="space-y-4">
                  <div className="geist-label">System_Prompt // session_v2</div>
                  <h3 className="text-2xl font-bold text-white tracking-tight leading-tight uppercase">
                    "How do you handle state management across a large-scale React application?"
                  </h3>
                </div>
              </div>

              <div className="relative group">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your response here..."
                  className="w-full h-56 bg-black border border-white/5 rounded-sm p-8 text-white placeholder:text-slate-700 focus:outline-none focus:border-white/20 transition-colors resize-none font-mono text-xs leading-relaxed"
                />
              </div>

              <Button 
                onClick={handleAnalyze} 
                disabled={!input.trim() || isAnalyzing}
                className="w-full h-14 rounded-sm bg-white text-black font-black uppercase tracking-widest text-[10px] hover:bg-slate-200 border-none transition-all"
              >
                {isAnalyzing ? (
                  <div className="flex items-center gap-3">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    >
                      <Terminal size={14} />
                    </motion.div>
                    <span>Extracting_Signals...</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Send size={14} />
                    <span>Run Analysis</span>
                  </div>
                )}
              </Button>
            </div>
          </div>

          {/* Feedback Display */}
          <div className="bg-[#050505] p-12 relative min-h-[400px]">
            <AnimatePresence mode="wait">
              {isAnalyzing ? (
                <motion.div 
                  key="analyzing"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-full flex flex-col items-center justify-center space-y-12"
                >
                  <div className="relative">
                    <div className="w-40 h-40 rounded-full border border-white/5 flex items-center justify-center">
                       <motion.div 
                        animate={{ rotate: 360 }}
                        transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-0 rounded-full border-t border-white/40"
                       />
                       <Bot size={48} className="text-white opacity-20" />
                    </div>
                  </div>
                  <div className="space-y-6 text-center">
                    <h4 className="geist-label !text-white animate-pulse">Processing_Neural_Weights</h4>
                    <div className="w-64 h-px bg-white/5 relative mx-auto overflow-hidden">
                        <motion.div 
                          initial={{ left: '-100%' }}
                          animate={{ left: '100%' }}
                          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                          className="absolute top-0 bottom-0 w-24 bg-gradient-to-r from-transparent via-white/40 to-transparent"
                        />
                    </div>
                  </div>
                </motion.div>
              ) : feedback ? (
                <motion.div 
                  key="feedback"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="h-full flex flex-col"
                >
                  <div className="flex items-center justify-between mb-16">
                    <div className="flex items-center gap-6">
                        <div className="w-12 h-12 rounded-sm bg-white/5 border border-white/10 flex items-center justify-center">
                          <CheckCircle2 size={24} className="text-white" />
                        </div>
                        <div>
                          <div className="geist-label !text-slate-700 mb-2">Signal_Detected</div>
                          <h4 className="text-2xl geist-heading text-white">{feedback.title}</h4>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-6xl font-black text-white tracking-tighter tabular-nums leading-none">{feedback.score}</div>
                        <div className="geist-label !text-slate-800 mt-4">Calibration_Score</div>
                      </div>
                    </div>

                    <div className="flex-1 space-y-12">
                      <div className="space-y-4">
                        <div className="flex justify-between geist-label !text-slate-600">
                          <span>Conceptual_Depth</span>
                          <span className="text-white font-mono tracking-normal">{feedback.score - 5}/100</span>
                        </div>
                        <div className="h-px bg-white/5 w-full">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${feedback.score - 5}%` }}
                            className="h-full bg-white"
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-4 pt-12 border-t border-white/5">
                         <div className="geist-label">AI_Refinement_Note</div>
                         <div className="p-8 bg-white/[0.02] border border-white/5 rounded-sm">
                            <p className="geist-mono !text-base italic">
                              "{feedback.tip}"
                            </p>
                         </div>
                      </div>
                    </div>
                </motion.div>
              ) : (
                <motion.div
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-full flex flex-col items-center justify-center text-center space-y-8"
                >
                  <div className="w-16 h-16 rounded-sm border border-white/5 bg-black flex items-center justify-center opacity-20">
                    <MessageSquare size={24} className="text-white" />
                  </div>
                  <div className="space-y-4">
                    <h4 className="geist-label !text-slate-700">Awaiting_Input</h4>
                    <p className="text-slate-600 text-sm italic font-medium max-w-[200px] mx-auto">Evaluation metrics will appear here after analysis.</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

        </div>
      </div>
    </div>
  );
}
