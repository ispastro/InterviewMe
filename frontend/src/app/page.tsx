import Link from 'next/link';
import { ArrowRight, Sparkles, Zap, Target, BarChart3, CheckCircle, Star, Users } from 'lucide-react';
import { Button } from '@/components/ui';

const featureItems = [
  {
    title: 'AI-Powered Questions',
    description:
      'Get personalized interview questions generated from your resume and target job description.',
    icon: Zap,
  },
  {
    title: 'Instant Feedback',
    description:
      'Receive real-time scoring and clear guidance on communication, confidence, and technical depth.',
    icon: Target,
  },
  {
    title: 'Performance Analytics',
    description:
      'Track progress over time and focus on the exact areas that improve your interview outcomes.',
    icon: BarChart3,
  },
];

const steps = [
  {
    title: 'Upload Your Resume',
    description:
      'Upload your CV and target job description. InterviewMe analyzes both in seconds.',
  },
  {
    title: 'Practice Interview',
    description:
      'Answer adaptive AI questions in a realistic flow using text or voice.',
  },
  {
    title: 'Get Feedback',
    description:
      'Review score breakdowns, strengths, and clear next actions to improve.',
  },
];

export default function LandingPage() {

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-slate-950 text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(45,212,191,0.1),transparent_45%),radial-gradient(ellipse_at_bottom,rgba(2,6,23,0.95),rgba(2,6,23,1))]" />
      <div className="pointer-events-none absolute left-1/2 top-[-16rem] h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-teal-400/10 blur-[140px]" />
      
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/75 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <img src="/logo.png" alt="InterviewMe" className="h-8 w-auto rounded-xl border border-slate-600/80 object-contain shadow-sm" />
            <span className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-b from-white via-slate-100 to-slate-300 drop-shadow-[0_0_12px_rgba(255,255,255,0.18)]">
              InterviewMe
            </span>
          </Link>
          <div className="flex items-center gap-8">
            <nav className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-slate-400 hover:text-white text-sm transition-colors">Features</a>
              <a href="#how-it-works" className="text-slate-400 hover:text-white text-sm transition-colors">How it Works</a>
              <a 
                href="https://github.com/ispastro/InterviewAI" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-700 rounded-lg hover:bg-slate-800 text-sm text-slate-300 transition-colors"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                <span>GitHub</span>
              </a>
            </nav>
            <div>
              <Link href="/dashboard">
                <Button size="sm" className="bg-white text-slate-900 hover:bg-slate-100">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10">
        <section className="py-28 md:py-36">
          <div className="mx-auto w-full max-w-6xl px-6">
            <div className="mx-auto max-w-4xl text-center">
              <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800/50 px-4 py-2">
              <Sparkles size={16} className="text-teal-400" />
                <span className="text-sm font-medium text-slate-300">Powered by Groq AI • Lightning Fast</span>
              </div>

              <h1 className="mt-8 text-5xl font-bold leading-tight text-white md:text-6xl lg:text-7xl">
                Ace Your Next Interview
                <br />
                <span className="text-slate-400">In Minutes</span>
              </h1>

              <p className="mx-auto mt-8 max-w-2xl text-xl leading-relaxed text-slate-400">
                Practice with an adaptive AI interviewer, get instant feedback, and improve with every session.
              </p>

              <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link href="/interview/setup">
                  <Button size="lg" className="px-8 text-base bg-white text-slate-900 hover:bg-slate-100">
                    <span className="flex items-center gap-2">
                      Start Free Interview
                      <ArrowRight size={20} />
                    </span>
                  </Button>
                </Link>
                <Link href="#how-it-works">
                  <Button variant="outline" size="lg" className="px-8 text-base border-slate-700 text-slate-300 hover:bg-slate-800">
                    See How It Works
                  </Button>
                </Link>
              </div>

              <div className="mt-10 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-slate-400">
                <div className="flex items-center gap-2">
                  <Users size={18} className="text-teal-400" />
                  <span><strong className="text-white">10,000+</strong> users</span>
                </div>
                <div className="flex items-center gap-2">
                  <Star size={18} className="text-teal-400" />
                  <span><strong className="text-white">4.9/5</strong> rating</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle size={18} className="text-teal-400" />
                  <span><strong className="text-white">95%</strong> success rate</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="bg-slate-900/65 py-24">
          <div className="mx-auto w-full max-w-6xl px-6">
            <div className="mb-16 text-center">
              <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl">
                Everything You Need to Succeed
              </h2>
              <p className="mx-auto max-w-2xl text-xl text-slate-400">
                Clean, focused interview practice built for measurable improvement.
              </p>
            </div>

            <div className="grid gap-8 md:grid-cols-3">
              {featureItems.map((feature) => (
                <div key={feature.title} className="rounded-2xl border border-slate-700 bg-slate-800/45 p-8">
                  <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-teal-500/10">
                    <feature.icon size={24} className="text-teal-400" />
                  </div>
                  <h3 className="mb-3 text-xl font-bold text-white">{feature.title}</h3>
                  <p className="leading-relaxed text-slate-400">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="how-it-works" className="py-24">
          <div className="mx-auto w-full max-w-6xl px-6">
            <div className="mb-16 text-center">
              <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl">
              How It Works
              </h2>
              <p className="mx-auto max-w-2xl text-xl text-slate-400">
              Get started in minutes with our simple three-step process
              </p>
            </div>

            <div className="mx-auto grid max-w-5xl gap-10 md:grid-cols-3">
              {steps.map((step, index) => (
                <div key={step.title} className="text-center">
                  <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-full bg-teal-500 text-xl font-bold text-white">
                    {index + 1}
                  </div>
                  <h3 className="mb-3 text-xl font-bold text-white">{step.title}</h3>
                  <p className="text-slate-400">{step.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-slate-900/65 py-24">
          <div className="mx-auto w-full max-w-4xl px-6 text-center">
            <h2 className="mb-6 text-3xl font-bold text-white md:text-4xl">
            Ready to Ace Your Next Interview?
            </h2>
            <p className="mx-auto mb-8 max-w-2xl text-xl text-slate-400">
              Join thousands of candidates improving their confidence and interview performance.
            </p>
            <Link href="/interview/setup">
              <Button size="lg" className="px-12 text-base bg-white text-slate-900 hover:bg-slate-100">
                <span className="flex items-center gap-2">
                  Start Free Interview
                  <ArrowRight size={20} />
                </span>
              </Button>
            </Link>
            <p className="mt-6 text-sm text-slate-500">
              No credit card required • Free forever • Start in 2 minutes
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800 py-12">
        <div className="mx-auto w-full max-w-6xl px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <img src="/logo.png" alt="InterviewMe" className="h-6 w-auto object-contain rounded-xl border border-slate-600/80 shadow-sm" />
              <span className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-b from-white via-slate-100 to-slate-300 drop-shadow-[0_0_10px_rgba(255,255,255,0.14)]">
                InterviewMe
              </span>
            </div>
            <div className="flex gap-8 text-sm text-slate-400">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
            </div>
            <div className="flex flex-col items-center md:items-end gap-2">
              <p className="text-sm text-slate-400">© {new Date().getFullYear()} InterviewMe. All rights reserved.</p>
              <p className="text-sm text-slate-500">
                Designed and built by{' '}
                <a 
                  href="https://github.com/ispastro" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-teal-400 hover:text-teal-300 font-medium transition-colors"
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
