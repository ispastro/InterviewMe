'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
    ArrowRight,
    Play,
    Clock,
    TrendingUp,
    Calendar,
    ChevronRight,
    RotateCcw,
    LogOut,
    BarChart3
} from 'lucide-react';
import { Button, Badge, PageTransition, InterviewCardSkeleton } from '@/components/ui';
import { RadarChart } from '@/components/charts';
import { useUserStore } from '@/stores';
import { useUserInterviews, useUserStats } from '@/hooks/api/useInterview';
import { formatDate } from '@/lib/utils';
import type { ScoreBreakdown } from '@/types';

export default function DashboardPage() {
    const router = useRouter();
    const user = useUserStore((state) => state.user);
    const logout = useUserStore((state) => state.logout);
    const userName = user?.name || 'Guest';
    const userEmail = user?.email || 'No email provided';
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const { data: interviewList, isLoading: interviewsLoading } = useUserInterviews(1, 10);
    const { data: stats, isLoading: statsLoading } = useUserStats();

    const handleLogout = () => {
        logout();
        router.push('/login');
    };

    const averageScore = stats?.average_score || 0;
    const mappedScore = Math.max(0, Math.min(5, averageScore / 20));
    const averageScores: ScoreBreakdown = {
        overall: averageScore,
        communication: mappedScore,
        confidence: mappedScore,
        structure: mappedScore,
        technicalDepth: mappedScore,
        relevance: mappedScore,
    };

    const sessions = (interviewList?.interviews || []).map((interview) => ({
        id: interview.id,
        role: interview.target_role || 'Interview Session',
        company: interview.target_company,
        date: new Date(interview.created_at),
        questionsAnswered: interview.current_turn || 0,
        status: interview.status,
    }));

    const inProgressInterview = sessions.find((s) => s.status === 'in_progress');

    const statusLabel = (status: string) => {
        if (status === 'completed') return 'Completed';
        if (status === 'in_progress') return 'In Progress';
        return 'Pending';
    };

    return (
        <PageTransition>
            <div className="relative min-h-screen overflow-x-hidden bg-slate-950 text-slate-100">
                <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(45,212,191,0.08),transparent_45%),radial-gradient(ellipse_at_bottom,rgba(2,6,23,0.96),rgba(2,6,23,1))]" />
                <div className="pointer-events-none absolute left-1/2 top-[-16rem] h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-teal-400/10 blur-[140px]" />

                <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/75 px-6 py-4 backdrop-blur-xl">
                    <div className="mx-auto flex w-full max-w-6xl items-center justify-between">
                    <Link href="/" className="flex items-center gap-1">
                        <img src="/logo.png" alt="InterviewMe" className="h-8 w-auto rounded-xl border border-slate-600/80 object-contain shadow-sm" />
                        <span className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-b from-white via-slate-100 to-slate-300 drop-shadow-[0_0_12px_rgba(255,255,255,0.18)]">
                            InterviewMe
                        </span>
                    </Link>

                    <div className="relative">
                        <button 
                            onClick={() => setIsProfileOpen(!isProfileOpen)}
                            className="flex items-center gap-3 transition-opacity hover:opacity-90"
                        >
                            <div className="w-10 h-10 rounded-full bg-[#0D9488] flex items-center justify-center">
                                <span className="text-white font-semibold">{userName.charAt(0)}</span>
                            </div>
                            <span className="hidden font-medium text-slate-100 sm:block">{userName}</span>
                        </button>

                        {/* Dropdown Menu */}
                        {isProfileOpen && (
                            <>
                                <div 
                                    className="fixed inset-0 z-10" 
                                    onClick={() => setIsProfileOpen(false)}
                                />
                                <div className="absolute right-0 top-full z-20 mt-2 w-64 rounded-xl border border-slate-700 bg-slate-900 shadow-[0_16px_32px_rgba(2,6,23,0.5)]">
                                    <div className="border-b border-slate-800 p-4">
                                        <div className="flex items-center gap-3 mb-2">
                                            <div className="w-12 h-12 rounded-full bg-[#0D9488] flex items-center justify-center">
                                                <span className="text-white font-semibold text-lg">{userName.charAt(0)}</span>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="truncate font-semibold text-slate-100">{userName}</p>
                                                <p className="truncate text-sm text-slate-400">{userEmail}</p>
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleLogout}
                                        className="flex w-full items-center gap-3 rounded-b-xl px-4 py-3 text-left text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
                                    >
                                        <LogOut size={18} />
                                        <span className="font-medium">Logout</span>
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                    </div>
                </header>

                <main className="relative z-10 mx-auto w-full max-w-6xl px-6 py-12">
                    {/* Welcome Section */}
                    <section className="mb-10 flex flex-col justify-between gap-6 md:flex-row md:items-center">
                        <div>
                            <h1 className="mb-2 text-4xl font-bold text-white">Hi {userName}</h1>
                            <p className="text-slate-400">
                                You have completed {stats?.completed_interviews || 0} sessions. Keep the streak alive.
                            </p>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="rounded-full border border-slate-700 bg-slate-900/60 px-4 py-2 text-sm text-slate-300">
                                Total: {stats?.total_interviews || 0}
                            </div>
                            <Link href="/analytics">
                                <Button variant="outline" size="md" className="border-slate-700 text-slate-100 hover:bg-slate-800 hover:text-white">
                                    <BarChart3 size={18} className="mr-2" />
                                    View Analytics
                                </Button>
                            </Link>
                        </div>
                    </section>

                    {/* Quick Actions */}
                    <section className="mb-10 grid gap-6 md:grid-cols-2">
                        <Link href="/interview/setup">
                            <div className="group rounded-2xl border border-slate-700 bg-slate-900/45 p-6 transition-colors hover:border-slate-500">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800">
                                            <Play size={22} className="text-white" />
                                        </div>
                                        <div>
                                            <h3 className="mb-1 font-semibold text-white">Start New Interview</h3>
                                            <p className="text-sm text-slate-400">Practice with a fresh session</p>
                                        </div>
                                    </div>
                                    <ChevronRight size={20} className="text-slate-500 transition-colors group-hover:text-slate-200" />
                                </div>
                            </div>
                        </Link>

                        <Link href={inProgressInterview ? `/interview/live?interview_id=${inProgressInterview.id}` : '/interview/setup'}>
                            <div className="group rounded-2xl border border-slate-700 bg-slate-900/45 p-6 transition-colors hover:border-slate-500">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800">
                                            <RotateCcw size={22} className="text-white" />
                                        </div>
                                        <div>
                                            <h3 className="mb-1 font-semibold text-white">Continue Last Session</h3>
                                            <p className="text-sm text-slate-400">
                                                {inProgressInterview ? 'Pick up where you left off' : 'No active session'}
                                            </p>
                                        </div>
                                    </div>
                                    <ChevronRight size={20} className="text-slate-500 transition-colors group-hover:text-slate-200" />
                                </div>
                            </div>
                        </Link>
                    </section>

                    {/* Main Content Grid */}
                    <section className="grid gap-8 lg:grid-cols-3">
                        <div className="lg:col-span-1">
                            <div className="rounded-2xl border border-slate-700 bg-slate-900/45 p-6">
                                <div className="mb-6 flex items-center justify-between">
                                    <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
                                    <TrendingUp size={20} className="text-[#0D9488]" />
                                    Performance
                                    </h2>
                                    <Link href="/analytics">
                                        <button className="flex items-center gap-1 text-sm text-slate-400 hover:text-white">
                                            Details
                                            <ChevronRight size={16} />
                                        </button>
                                    </Link>
                                </div>
                                <RadarChart scores={averageScores} />
                                <div className="mt-6 text-center">
                                    <p className="text-3xl font-bold text-white">
                                        {averageScore ? `${Math.round(averageScore)}%` : 'N/A'}
                                    </p>
                                    <p className="mt-1 text-sm text-slate-400">
                                        {statsLoading ? 'Loading...' : 'Average Score'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="lg:col-span-2">
                            <div className="rounded-2xl border border-slate-700 bg-slate-900/45 p-6">
                                <div className="mb-6 flex items-center justify-between">
                                    <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
                                    <Clock size={20} className="text-[#0D9488]" />
                                    Previous Sessions
                                    </h2>
                                    <Link href="/sessions">
                                        <button className="flex items-center gap-1 text-sm text-slate-400 hover:text-white">
                                            View All
                                            <ArrowRight size={16} />
                                        </button>
                                    </Link>
                                </div>
                                <div className="space-y-4">
                                    {interviewsLoading && (
                                        <>
                                            <InterviewCardSkeleton />
                                            <InterviewCardSkeleton />
                                            <InterviewCardSkeleton />
                                        </>
                                    )}
                                    {!interviewsLoading && sessions.length === 0 && (
                                        <div className="rounded-xl border border-slate-700 p-4 text-slate-400">
                                            No interviews yet. Start your first session.
                                        </div>
                                    )}
                                    {sessions.map((session) => (
                                        <div
                                            key={session.id}
                                            className="rounded-xl border border-slate-700 p-4 transition-colors hover:border-slate-500"
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#0D9488]">
                                                        <span className="font-bold text-white">{session.questionsAnswered}</span>
                                                    </div>
                                                    <div>
                                                        <h4 className="font-semibold text-white">{session.role}</h4>
                                                        <div className="flex items-center gap-3 text-sm text-slate-400">
                                                            <span className="flex items-center gap-1">
                                                                <Calendar size={14} />
                                                                {formatDate(session.date)}
                                                            </span>
                                                            <span>{session.questionsAnswered} turns</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <Badge variant={session.status === 'completed' ? 'success' : session.status === 'in_progress' ? 'warning' : 'error'}>
                                                        {statusLabel(session.status)}
                                                    </Badge>
                                                    <Link href={session.status === 'completed' ? `/interview/summary?interview_id=${session.id}` : `/interview/live?interview_id=${session.id}`}>
                                                        <button className="flex items-center gap-1 text-sm text-slate-400 hover:text-white">
                                                            {session.status === 'completed' ? 'View' : 'Open'}
                                                            <ChevronRight size={16} />
                                                        </button>
                                                    </Link>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </section>
                </main>
            </div>
        </PageTransition>
    );
}
