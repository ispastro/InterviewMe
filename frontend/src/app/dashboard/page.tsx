'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import {
    ArrowRight,
    Bot,
    Play,
    Clock,
    TrendingUp,
    Calendar,
    ChevronRight,
    RotateCcw
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui';
import { RadarChart } from '@/components/charts';
import { useUserStore } from '@/stores';
import { useUserInterviews, useUserStats } from '@/hooks/api/useInterview';
import { formatDate } from '@/lib/utils';
import type { ScoreBreakdown } from '@/types';

export default function DashboardPage() {
    const user = useUserStore((state) => state.user);
    const userName = user?.name || 'Guest';
    const { data: interviewList, isLoading: interviewsLoading } = useUserInterviews(1, 10);
    const { data: stats, isLoading: statsLoading } = useUserStats();

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

    return (
        <div className="min-h-screen bg-[#F8FAFC]">
            {/* Header */}
            <header className="sticky top-0 z-40 px-6 py-4 bg-white border-b border-[#E5E7EB]">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2">
                        <div className="w-10 h-10 rounded-[12px] bg-[#0F172A] flex items-center justify-center">
                            <Bot size={22} className="text-white" />
                        </div>
                        <span className="text-xl font-semibold text-[#0F172A] font-[Lora]">InterviewAI</span>
                    </Link>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-[#0D9488] flex items-center justify-center">
                                <span className="text-white font-semibold font-[Lexend]">{userName.charAt(0)}</span>
                            </div>
                            <span className="text-[#0F172A] font-medium hidden sm:block font-[Lexend]">{userName}</span>
                        </div>
                    </div>
                </div>
            </header>

            <main className="px-6 py-8 max-w-7xl mx-auto">
                {/* Welcome Banner */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <Card className="overflow-hidden bg-[#0F172A] border-none">
                        <div className="flex flex-col md:flex-row items-center justify-between gap-6 p-8">
                            <div>
                                <h1 className="text-2xl md:text-3xl font-semibold text-white mb-2 font-[Lora]">
                                    Hi {userName}, ready for today&apos;s practice?
                                </h1>
                                <p className="text-[#94A3B8] font-[Lexend]">
                                    You&apos;ve completed {stats?.completed_interviews || 0} sessions. Keep up the great work!
                                </p>
                            </div>
                            <Link href="/interview/setup">
                                <Button size="lg">
                                    <Play size={18} className="mr-2" />
                                    Start New Interview
                                </Button>
                            </Link>
                        </div>
                    </Card>
                </motion.div>

                {/* Quick Actions */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="grid md:grid-cols-2 gap-6 mb-8"
                >
                    <Card hover className="cursor-pointer group">
                        <Link href="/interview/setup" className="block p-6">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-[12px] bg-[#F0FDFA] flex items-center justify-center group-hover:bg-[#0D9488] transition-colors">
                                        <Play size={22} className="text-[#0D9488] group-hover:text-white transition-colors" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-[#0F172A] font-[Lora]">Start New Interview</h3>
                                        <p className="text-sm text-[#475569] font-[Lexend]">Practice with a fresh session</p>
                                    </div>
                                </div>
                                <ChevronRight size={20} className="text-[#94A3B8] group-hover:text-[#0F172A] transition-colors" />
                            </div>
                        </Link>
                    </Card>

                    <Card hover className="cursor-pointer group">
                        <Link href={inProgressInterview ? `/interview/live?interview_id=${inProgressInterview.id}` : '/interview/setup'} className="block p-6">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-[12px] bg-[#ECFDF5] flex items-center justify-center group-hover:bg-[#10B981] transition-colors">
                                        <RotateCcw size={22} className="text-[#10B981] group-hover:text-white transition-colors" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-[#0F172A] font-[Lora]">Continue Last Session</h3>
                                        <p className="text-sm text-[#475569] font-[Lexend]">
                                            {inProgressInterview ? 'Pick up where you left off' : 'No active session, start a new one'}
                                        </p>
                                    </div>
                                </div>
                                <ChevronRight size={20} className="text-[#94A3B8] group-hover:text-[#0F172A] transition-colors" />
                            </div>
                        </Link>
                    </Card>
                </motion.div>

                {/* Main Content Grid */}
                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Performance Overview */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="lg:col-span-1"
                    >
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <TrendingUp size={20} className="text-[#0D9488]" />
                                    Performance Overview
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <RadarChart scores={averageScores} />
                                <div className="mt-4 text-center">
                                    <p className="text-3xl font-bold text-[#0F172A] font-[Lora]">
                                        {averageScore ? `${Math.round(averageScore)}%` : 'N/A'}
                                    </p>
                                    <p className="text-sm text-[#94A3B8] font-[Lexend]">
                                        {statsLoading ? 'Loading...' : 'Average Score'}
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Previous Sessions */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="lg:col-span-2"
                    >
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between">
                                <CardTitle className="flex items-center gap-2">
                                    <Clock size={20} className="text-[#0D9488]" />
                                    Previous Sessions
                                </CardTitle>
                                <Link href="/sessions">
                                    <Button variant="ghost" size="sm">
                                        View All
                                        <ArrowRight size={16} className="ml-1" />
                                    </Button>
                                </Link>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {interviewsLoading && (
                                        <div className="p-4 rounded-[16px] bg-[#F8FAFC] border border-[#E5E7EB] text-[#475569] font-[Lexend]">
                                            Loading interview history...
                                        </div>
                                    )}
                                    {!interviewsLoading && sessions.length === 0 && (
                                        <div className="p-4 rounded-[16px] bg-[#F8FAFC] border border-[#E5E7EB] text-[#475569] font-[Lexend]">
                                            No interviews yet. Start your first session.
                                        </div>
                                    )}
                                    {sessions.map((session, index) => (
                                        <motion.div
                                            key={session.id}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.1 * index }}
                                            className="p-4 rounded-[16px] bg-[#F8FAFC] border border-[#E5E7EB] hover:bg-[#F1F5F9] transition-colors"
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <div className="w-12 h-12 rounded-[12px] bg-[#0D9488] flex items-center justify-center">
                                                        <span className="text-white font-bold font-[Lexend]">{session.questionsAnswered}</span>
                                                    </div>
                                                    <div>
                                                        <h4 className="font-semibold text-[#0F172A] font-[Lora]">{session.role}</h4>
                                                        <div className="flex items-center gap-3 text-sm text-[#94A3B8] font-[Lexend]">
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
                                                        {session.status === 'completed' ? 'Completed' : session.status === 'in_progress' ? 'In Progress' : 'Pending'}
                                                    </Badge>
                                                    <Link href={session.status === 'completed' ? `/interview/summary?interview_id=${session.id}` : `/interview/live?interview_id=${session.id}`}>
                                                        <Button variant="ghost" size="sm">
                                                            {session.status === 'completed' ? 'View Report' : 'Open Session'}
                                                            <ChevronRight size={16} />
                                                        </Button>
                                                    </Link>
                                                </div>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </div>
            </main>
        </div>
    );
}
