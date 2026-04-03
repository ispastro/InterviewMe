'use client';

import Link from 'next/link';
import { Bot, ArrowRight, Sparkles, Zap, Target, BarChart3, CheckCircle, Star, Users } from 'lucide-react';
import { Button } from '@/components/ui';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 sticky top-0 bg-white/80 backdrop-blur-lg z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Bot size={28} className="text-[#0D9488]" />
            <span className="text-xl font-bold text-gray-900">InterviewMe</span>
          </Link>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-gray-600 hover:text-gray-900 text-sm font-medium">Features</a>
            <a href="#how-it-works" className="text-gray-600 hover:text-gray-900 text-sm font-medium">How it Works</a>
            <a href="#testimonials" className="text-gray-600 hover:text-gray-900 text-sm font-medium">Testimonials</a>
          </nav>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost" size="sm">Log In</Button>
            </Link>
            <Link href="/dashboard">
              <Button size="sm">Get Started</Button>
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
                <Button size="lg" className="text-base px-8">
                  Start Free Interview
                  <ArrowRight size={20} className="ml-2" />
                </Button>
              </Link>
              <Link href="#how-it-works">
                <Button variant="outline" size="lg" className="text-base px-8">
                  See How It Works
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

      {/* Testimonials */}
      <section id="testimonials" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Loved by Job Seekers
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              See what our users have to say about their experience
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Testimonial 1 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm">
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={18} className="fill-[#0D9488] text-[#0D9488]" />
                ))}
              </div>
              <p className="text-gray-700 mb-6 leading-relaxed">
                "InterviewMe helped me land my dream job at Google. The AI feedback was incredibly detailed and helped me improve my answers significantly."
              </p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-bold">
                  S
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Sarah Chen</div>
                  <div className="text-sm text-gray-600">Software Engineer at Google</div>
                </div>
              </div>
            </div>

            {/* Testimonial 2 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm">
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={18} className="fill-[#0D9488] text-[#0D9488]" />
                ))}
              </div>
              <p className="text-gray-700 mb-6 leading-relaxed">
                "The personalized questions based on my resume were spot-on. I felt so much more confident going into my actual interviews."
              </p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-bold">
                  M
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Michael Rodriguez</div>
                  <div className="text-sm text-gray-600">Product Manager at Amazon</div>
                </div>
              </div>
            </div>

            {/* Testimonial 3 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm">
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={18} className="fill-[#0D9488] text-[#0D9488]" />
                ))}
              </div>
              <p className="text-gray-700 mb-6 leading-relaxed">
                "Best interview prep tool I've used. The real-time feedback helped me identify and fix my weaknesses before the actual interview."
              </p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-bold">
                  E
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Emily Watson</div>
                  <div className="text-sm text-gray-600">Data Scientist at Meta</div>
                </div>
              </div>
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
            <Button size="lg" className="text-base px-12">
              Start Free Interview
              <ArrowRight size={20} className="ml-2" />
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
            <div className="flex items-center gap-2">
              <Bot size={24} className="text-[#0D9488]" />
              <span className="text-lg font-bold text-gray-900">InterviewMe</span>
            </div>
            <div className="flex gap-8 text-sm text-gray-600">
              <a href="#" className="hover:text-gray-900">Privacy</a>
              <a href="#" className="hover:text-gray-900">Terms</a>
              <a href="#" className="hover:text-gray-900">Contact</a>
            </div>
            <p className="text-sm text-gray-600">© {new Date().getFullYear()} InterviewMe. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
