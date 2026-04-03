'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Bot, ArrowRight, Sparkles, Zap, Target, BarChart3, CheckCircle, Star, Users } from 'lucide-react';
import { Button } from '@/components/ui';

export default function LandingPage() {
  const [starCount, setStarCount] = useState<number | null>(null);

  useEffect(() => {
    fetch('https://api.github.com/repos/ispastro/InterviewAI')
      .then(res => res.json())
      .then(data => setStarCount(data.stargazers_count))
      .catch(() => setStarCount(null));
  }, []);

  const formatStarCount = (count: number | null) => {
    if (!count) return '...';
    if (count >= 1000) return `${(count / 1000).toFixed(1)}k`;
    return count.toString();
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 sticky top-0 bg-white/80 backdrop-blur-lg z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-1">
            <img src="/logo.png" alt="InterviewMe" className="h-8 w-auto object-contain" />
            <span className="text-xl font-bold text-gray-900">InterviewMe</span>
          </Link>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-gray-600 hover:text-gray-900 text-sm font-medium">Features</a>
            <a href="#how-it-works" className="text-gray-600 hover:text-gray-900 text-sm font-medium">How it Works</a>
            <a 
              href="https://github.com/ispastro/InterviewAI" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 rounded-none hover:border-gray-400 transition-colors"
            >
              <svg className="w-4 h-4 text-gray-700" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd" />
              </svg>
              <span className="text-sm text-gray-700">Star</span>
              <span className="text-sm text-gray-900">{formatStarCount(starCount)}</span>
            </a>
          </nav>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost" size="sm" className="rounded-none">Log In</Button>
            </Link>
            <Link href="/dashboard">
              <Button size="sm" className="rounded-none group overflow-hidden relative">
                <span className="invisible">Get Started</span>
                <span className="absolute inset-0 flex items-center justify-center transition-transform duration-300 group-hover:-translate-y-full">
                  Get Started
                </span>
                <span className="absolute inset-0 flex items-center justify-center translate-y-full transition-transform duration-300 group-hover:translate-y-0">
                  Get Started
                </span>
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#F0FDFA] via-white to-[#F0F9FF] opacity-70"></div>
        <div className="max-w-7xl mx-auto px-6 py-24 md:py-32 relative">
          <div className="max-w-3xl mx-auto text-center space-y-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-[#99F6E4] shadow-sm">
              <Sparkles size={16} className="text-[#0D9488]" />
              <span className="text-sm font-medium text-gray-700">AI-Powered Interview Practice</span>
            </div>
            
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 leading-tight">
              Ace Your Next Interview with{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#0D9488] to-[#06B6D4]">
                AI Coaching
              </span>
            </h1>
            
            <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
              Practice with our advanced AI interviewer, get instant feedback, and land your dream job. 
              Personalized questions based on your resume and target role.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <Link href="/interview/setup">
                <Button size="lg" className="text-base px-8 rounded-none group overflow-hidden relative">
                  <span className="invisible flex items-center gap-2">
                    Start Free Interview
                    <ArrowRight size={20} />
                  </span>
                  <span className="absolute inset-0 flex items-center justify-center gap-2 transition-transform duration-300 group-hover:-translate-y-full">
                    Start Free Interview
                    <ArrowRight size={20} />
                  </span>
                  <span className="absolute inset-0 flex items-center justify-center gap-2 translate-y-full transition-transform duration-300 group-hover:translate-y-0">
                    Start Free Interview
                    <ArrowRight size={20} />
                  </span>
                </Button>
              </Link>
              <Link href="#how-it-works">
                <Button variant="outline" size="lg" className="text-base px-8 rounded-none group overflow-hidden relative">
                  <span className="invisible">See How It Works</span>
                  <span className="absolute inset-0 flex items-center justify-center transition-transform duration-300 group-hover:-translate-y-full">
                    See How It Works
                  </span>
                  <span className="absolute inset-0 flex items-center justify-center translate-y-full transition-transform duration-300 group-hover:translate-y-0">
                    See How It Works
                  </span>
                </Button>
              </Link>
            </div>

            {/* Social Proof */}
            <div className="flex items-center justify-center gap-8 pt-8 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Users size={18} className="text-[#0D9488]" />
                <span><strong className="text-gray-900">10,000+</strong> users</span>
              </div>
              <div className="flex items-center gap-2">
                <Star size={18} className="text-[#0D9488]" />
                <span><strong className="text-gray-900">4.9/5</strong> rating</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle size={18} className="text-[#0D9488]" />
                <span><strong className="text-gray-900">95%</strong> success rate</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Everything You Need to Succeed
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Our AI-powered platform provides comprehensive interview preparation tailored to your needs
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-[#F0FDFA] flex items-center justify-center mb-6">
                <Zap size={24} className="text-[#0D9488]" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">AI-Powered Questions</h3>
              <p className="text-gray-600 leading-relaxed">
                Get personalized interview questions generated by advanced AI based on your resume and target job description.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-[#F0FDFA] flex items-center justify-center mb-6">
                <Target size={24} className="text-[#0D9488]" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Instant Feedback</h3>
              <p className="text-gray-600 leading-relaxed">
                Receive real-time evaluation on your answers with detailed insights on communication, confidence, and technical depth.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-[#F0FDFA] flex items-center justify-center mb-6">
                <BarChart3 size={24} className="text-[#0D9488]" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Performance Analytics</h3>
              <p className="text-gray-600 leading-relaxed">
                Track your progress over time with detailed analytics and identify areas for improvement with actionable insights.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Get started in minutes with our simple three-step process
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-12 max-w-5xl mx-auto">
            {/* Step 1 */}
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-[#0D9488] text-white flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                1
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Upload Your Resume</h3>
              <p className="text-gray-600">
                Upload your CV and the job description you're targeting. Our AI analyzes both to create personalized questions.
              </p>
            </div>

            {/* Step 2 */}
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-[#0D9488] text-white flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                2
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Practice Interview</h3>
              <p className="text-gray-600">
                Engage in a realistic interview session with our AI. Answer questions via text or voice in real-time.
              </p>
            </div>

            {/* Step 3 */}
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-[#0D9488] text-white flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                3
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Get Feedback</h3>
              <p className="text-gray-600">
                Receive detailed feedback on your performance with scores, strengths, and areas to improve.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
            Ready to Ace Your Next Interview?
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Join thousands of successful candidates who used InterviewMe to land their dream jobs
          </p>
          <Link href="/interview/setup">
            <Button size="lg" className="text-base px-12 rounded-none group overflow-hidden relative">
              <span className="invisible flex items-center gap-2">
                Start Free Interview
                <ArrowRight size={20} />
              </span>
              <span className="absolute inset-0 flex items-center justify-center gap-2 transition-transform duration-300 group-hover:-translate-y-full">
                Start Free Interview
                <ArrowRight size={20} />
              </span>
              <span className="absolute inset-0 flex items-center justify-center gap-2 translate-y-full transition-transform duration-300 group-hover:translate-y-0">
                Start Free Interview
                <ArrowRight size={20} />
              </span>
            </Button>
          </Link>
          <p className="mt-6 text-sm text-gray-500">
            No credit card required • Free forever • Get started in 2 minutes
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-1">
              <img src="/logo.png" alt="InterviewMe" className="h-6 w-auto object-contain" />
              <span className="text-lg font-bold text-gray-900">InterviewMe</span>
            </div>
            <div className="flex gap-8 text-sm text-gray-600">
              <a href="#" className="hover:text-gray-900">Privacy</a>
              <a href="#" className="hover:text-gray-900">Terms</a>
              <a href="#" className="hover:text-gray-900">Contact</a>
            </div>
            <div className="flex flex-col items-center md:items-end gap-2">
              <p className="text-sm text-gray-600">© {new Date().getFullYear()} InterviewMe. All rights reserved.</p>
              <p className="text-sm text-gray-500">
                Designed and built by{' '}
                <a 
                  href="https://github.com/ispastro" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-[#0D9488] hover:text-[#0F766E] font-medium"
                >
                  Haile (ispastro)
                </a>
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
