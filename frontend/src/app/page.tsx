'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowRight, Bot, BarChart3, MessageSquare, Mic, Target, Sparkles, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui';

const features = [
  {
    icon: MessageSquare,
    title: 'Real-time Conversations',
    description: 'Practice with AI that responds naturally and adapts to your answers.',
  },
  {
    icon: BarChart3,
    title: 'Instant Feedback',
    description: 'Get detailed analysis on communication, structure, and technical depth.',
  },
  {
    icon: Mic,
    title: 'Voice & Text Modes',
    description: 'Choose your preferred interview style — type or speak your answers.',
  },
  {
    icon: Target,
    title: 'Role-Specific Questions',
    description: 'Tailored questions for Software Engineers, Product Managers, and more.',
  },
];

const benefits = [
  'Unlimited practice sessions',
  'Personalized feedback',
  'Track your progress',
  'No credit card required',
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4 bg-white border-b border-[#E5E7EB]">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-[12px] bg-[#0F172A] flex items-center justify-center">
              <Bot size={22} className="text-white" />
            </div>
            <span className="text-xl font-semibold text-[#0F172A] font-[Lora]">InterviewAI</span>
          </Link>

          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">Log In</Button>
            </Link>
            <Link href="/register">
              <Button size="sm">Sign Up</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section - Centered */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#F0FDFA] border border-[#99F6E4] mb-6">
              <Sparkles size={16} className="text-[#0D9488]" />
              <span className="text-sm text-[#0D9488] font-[Lexend]">AI-Powered Interview Practice</span>
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-[#0F172A] leading-tight mb-6 font-[Lora]">
              Master Your Interviews<br />
              <span className="text-[#0D9488]">With AI Coaching</span>
            </h1>

            <p className="text-lg md:text-xl text-[#475569] mb-8 max-w-2xl mx-auto font-[Lexend]">
              Practice real interview scenarios, receive instant feedback, and build the confidence you need to land your dream job.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-10">
              <Link href="/interview/setup">
                <Button size="lg" className="w-full sm:w-auto">
                  Start Free Practice
                  <ArrowRight size={18} className="ml-2" />
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button variant="secondary" size="lg" className="w-full sm:w-auto">
                  View Dashboard
                </Button>
              </Link>
            </div>

            {/* Benefits */}
            <div className="flex flex-wrap justify-center gap-x-6 gap-y-2">
              {benefits.map((benefit) => (
                <div key={benefit} className="flex items-center gap-2">
                  <CheckCircle size={16} className="text-[#0D9488]" />
                  <span className="text-sm text-[#475569] font-[Lexend]">{benefit}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="grid grid-cols-3 gap-8 mt-16 pt-8 border-t border-[#E5E7EB] max-w-lg mx-auto"
          >
            <div>
              <p className="text-3xl font-bold text-[#0F172A] font-[Lora]">10K+</p>
              <p className="text-sm text-[#94A3B8] font-[Lexend]">Sessions</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-[#0F172A] font-[Lora]">95%</p>
              <p className="text-sm text-[#94A3B8] font-[Lexend]">Success Rate</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-[#0F172A] font-[Lora]">4.9★</p>
              <p className="text-sm text-[#94A3B8] font-[Lexend]">User Rating</p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-[#F8FAFC]">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold text-[#0F172A] mb-4 font-[Lora]">
              Everything You Need to Succeed
            </h2>
            <p className="text-[#475569] max-w-2xl mx-auto font-[Lexend]">
              Our AI-powered platform provides comprehensive interview preparation with real-time feedback and personalized coaching.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="group p-6 rounded-[20px] bg-white border border-[#E5E7EB] shadow-[0px_4px_16px_rgba(0,0,0,0.06)] hover:shadow-[0px_8px_24px_rgba(0,0,0,0.08)] transition-all duration-200"
              >
                <div className="w-12 h-12 rounded-[12px] bg-[#F0FDFA] flex items-center justify-center mb-4 group-hover:bg-[#0D9488] transition-colors">
                  <feature.icon size={24} className="text-[#0D9488] group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-lg font-semibold text-[#0F172A] mb-2 font-[Lora]">{feature.title}</h3>
                <p className="text-[#475569] text-sm font-[Lexend]">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative rounded-[20px] overflow-hidden bg-[#0F172A] p-12 text-center"
          >
            <h2 className="text-3xl font-bold text-white mb-4 font-[Lora]">
              Ready to Ace Your Next Interview?
            </h2>
            <p className="text-[#94A3B8] max-w-xl mx-auto mb-8 font-[Lexend]">
              Join thousands of professionals who have improved their interview skills and landed their dream jobs.
            </p>
            <Link href="/interview/setup">
              <Button size="lg">
                Start Free Practice
                <ArrowRight size={18} className="ml-2" />
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-[#E5E7EB]">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#0F172A] flex items-center justify-center">
              <Bot size={16} className="text-white" />
            </div>
            <span className="text-sm text-[#94A3B8] font-[Lexend]">© {new Date().getFullYear()} InterviewAI. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-[#94A3B8] font-[Lexend]">
            <Link href="#" className="hover:text-[#0F172A] transition-colors">Privacy</Link>
            <Link href="#" className="hover:text-[#0F172A] transition-colors">Terms</Link>
            <Link href="#" className="hover:text-[#0F172A] transition-colors">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
