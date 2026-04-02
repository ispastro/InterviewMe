'use client';

import { Suspense, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import { Bot, ArrowLeft, Download, Share2, Home, CheckCircle, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui';
import { RadarChart } from '@/components/charts';
import { formatDate } from '@/lib/utils';
import { interviewService } from '@/services/interview.service';
import type { ScoreBreakdown, ChatMessage, Interview, Feedback, Turn } from '@/types';

function SessionSummaryContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const interviewId = searchParams.get('interview_id');

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [interview, setInterview] = useState<Interview | null>(null);
    const [feedback, setFeedback] = useState<Feedback | null>(null);
    const [turns, setTurns] = useState<Turn[]>([]);

    useEffect(() => {
        const fetchData = async () => {
            if (!interviewId) {
                setError('No interview ID provided');
                setLoading(false);
                return;
            }

            try {
                setLoading(true);
                const [interviewData, feedbackData, turnsData] = await Promise.all([
                    interviewService.getInterview(interviewId),
                    interviewService.getInterviewFeedback(interviewId),
                    interviewService.getInterviewTurns(interviewId)
                ]);

                setInterview(interviewData);
                setFeedback(feedbackData);
                setTurns(turnsData);
            } catch (err: any) {
                console.error('Error fetching interview summary:', err);
                setError(err.message || 'Failed to load interview summary');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [interviewId]);

    if (loading) {
        return (
            <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 text-[#0D9488] animate-spin mx-auto mb-4" />
                    <p className="text-[#475569] font-[Lexend]">Generating your performance report...</p>
                </div>
            </div>
        );
    }

    if (error || !interview || !feedback) {
        return (
            <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-6">
                <Card className="max-w-md w-full">
                    <CardContent className="p-8 text-center">
                        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                        <h2 className="text-xl font-bold text-[#0F172A] mb-2 font-[Lora]">Report Loading Failed</h2>
                        <p className="text-[#475569] mb-6 font-[Lexend]">{error || 'Could not find report data.'}</p>
                        <Button onClick={() => router.push('/dashboard')} className="w-full">
                            Back to Dashboard
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Map backend scores to UI ScoreBreakdown
    const scores: ScoreBreakdown = {
        overall: feedback.overall_score || 0,
        communication: feedback.phase_scores?.behavioral || 0,
        confidence: feedback.phase_scores?.intro || 0,
        structure: feedback.phase_scores?.technical || 0,
        technicalDepth: feedback.phase_scores?.deep_dive || 0,
        relevance: 4, // Default as backend doesn't have 1:1 mapping for all radar points yet
    };

    // Convert Turns to ChatMessages for the transcript
    const transcript: ChatMessage[] = turns.flatMap(turn => [
        {
            id: `q-${turn.turn_number}`,
            sender: 'interviewer' as const,
            message: turn.ai_question,
            timestamp: new Date(interview.created_at) // Approximate
        },
        {
            id: `a-${turn.turn_number}`,
            sender: 'user' as const,
            message: turn.user_answer || '[No response]', // Handle null
            timestamp: new Date(interview.created_at) // Approximate
        }
    ]);

    const scoreLabels = [
        { key: 'communication' as keyof ScoreBreakdown, label: 'Communication' },
        { key: 'confidence' as keyof ScoreBreakdown, label: 'Confidence' },
        { key: 'structure' as keyof ScoreBreakdown, label: 'Structure' },
        { key: 'technicalDepth' as keyof ScoreBreakdown, label: 'Technical Depth' },
        { key: 'relevance' as keyof ScoreBreakdown, label: 'Relevance' },
    ];

    const improvements = (feedback.suggestions || []).map(s =>
        typeof s === 'string' ? s : s.action
    ).slice(0, 4);

    return (
        <div className="min-h-screen bg-[#F8FAFC]">
            <header className="sticky top-0 z-40 px-6 py-4 bg-white border-b border-[#E5E7EB]">
                <div className="max-w-6xl mx-auto flex items-center justify-between">
                    <Link href="/dashboard" className="flex items-center gap-2 text-[#475569] hover:text-[#0F172A] transition-colors font-[Lexend]">
                        <ArrowLeft size={20} />
                        <span>Back to Dashboard</span>
                    </Link>
                    <Link href="/" className="flex items-center gap-2">
                        <div className="w-10 h-10 rounded-[12px] bg-[#0F172A] flex items-center justify-center">
                            <Bot size={22} className="text-white" />
                        </div>
                    </Link>
                </div>
            </header>

            <main className="px-6 py-12 max-w-6xl mx-auto">
                {/* Success Banner */}
                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center mb-12">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#0F172A] mb-6">
                        <CheckCircle size={28} className="text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-[#0F172A] mb-2 font-[Lora]">Interview Complete</h1>
                    <p className="text-[#475569] font-[Lexend]">{interview.target_role || 'Software Engineer'} • {formatDate(new Date(interview.created_at))}</p>
                </motion.div>

                {/* Overall Score */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mb-8">
                    <Card className="text-center py-10">
                        <div className="relative inline-block">
                            <svg className="w-32 h-32 -rotate-90" viewBox="0 0 100 100">
                                <circle cx="50" cy="50" r="45" fill="none" stroke="#E5E7EB" strokeWidth="8" />
                                <motion.circle
                                    cx="50" cy="50" r="45" fill="none" stroke="#0F172A" strokeWidth="8" strokeLinecap="round"
                                    strokeDasharray={2 * Math.PI * 45}
                                    initial={{ strokeDashoffset: 2 * Math.PI * 45 }}
                                    animate={{ strokeDashoffset: 2 * Math.PI * 45 * (1 - scores.overall / 100) }}
                                    transition={{ duration: 1, delay: 0.5 }}
                                />
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div>
                                    <motion.span className="text-3xl font-bold text-[#0F172A] font-[Lora]" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}>
                                        {scores.overall}
                                    </motion.span>
                                    <span className="text-lg text-[#94A3B8]">/100</span>
                                </div>
                            </div>
                        </div>
                        <p className="text-[#475569] mt-4 font-[Lexend]">Overall AI Score</p>
                        <Badge variant={scores.overall >= 80 ? 'success' : scores.overall >= 60 ? 'warning' : 'error'} className="mt-2 text-sm px-4 py-1">
                            {scores.overall >= 80 ? 'Excellent' : scores.overall >= 60 ? 'Good' : 'Needs Work'}
                        </Badge>
                    </Card>
                </motion.div>

                <div className="grid lg:grid-cols-2 gap-8 mb-8">
                    {/* Radar Chart */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                        <Card className="h-full">
                            <CardHeader><CardTitle className="font-[Lora]">Skills Evaluation</CardTitle></CardHeader>
                            <CardContent><RadarChart scores={scores} /></CardContent>
                        </Card>
                    </motion.div>

                    {/* Detailed Analysis */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                        <Card className="h-full">
                            <CardHeader><CardTitle className="font-[Lora]">Feedback Summary</CardTitle></CardHeader>
                            <CardContent className="space-y-4">
                                <div className="p-4 rounded-[12px] bg-[#F8FAFC] border border-[#E5E7EB]">
                                    <p className="text-sm text-[#475569] leading-relaxed font-[Lexend]">
                                        {feedback.summary || "The AI has analyzed your performance across multiple dimensions. You showed strong potential in key areas required for this role."}
                                    </p>
                                </div>
                                <div className="grid grid-cols-2 gap-4 mt-6">
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-[#94A3B8] uppercase tracking-wider font-[Lexend]">STRENGTHS</p>
                                        <div className="flex flex-wrap gap-2">
                                            {(feedback.strengths || []).slice(0, 3).map((s, i) => (
                                                <Badge key={i} variant="success" className="text-[10px]">{typeof s === 'string' ? s : s.area}</Badge>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <p className="text-xs font-semibold text-[#94A3B8] uppercase tracking-wider font-[Lexend]">FOCUS AREAS</p>
                                        <div className="flex flex-wrap gap-2">
                                            {(feedback.weaknesses || []).slice(0, 3).map((w, i) => (
                                                <Badge key={i} variant="warning" className="text-[10px]">{typeof w === 'string' ? w : w.area}</Badge>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </div>

                {/* Score Breakdown Bars */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="mb-8">
                    <Card>
                        <CardHeader><CardTitle className="font-[Lora]">Detailed Performance Indicators</CardTitle></CardHeader>
                        <CardContent className="space-y-6">
                            {scoreLabels.map((item) => (
                                <div key={item.key} className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm font-medium text-[#475569] font-[Lexend]">{item.label}</span>
                                        <span className="text-sm font-bold text-[#0F172A] font-[Lexend]">{scores[item.key]}/5</span>
                                    </div>
                                    <div className="h-2 w-full bg-[#F1F5F9] rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${(scores[item.key] / 5) * 100}%` }}
                                            transition={{ duration: 1, delay: 0.6 }}
                                            className="h-full bg-[#0D9488] rounded-full"
                                        />
                                    </div>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Improvements */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="mb-8">
                    <Card className="border-l-4 border-l-[#0D9488]">
                        <CardHeader><CardTitle className="font-[Lora]">Expert Recommendations</CardTitle></CardHeader>
                        <CardContent>
                            <div className="grid md:grid-cols-2 gap-6">
                                {improvements.map((item, index) => (
                                    <div key={index} className="flex gap-4 p-4 rounded-[12px] bg-[#F0FDFA]">
                                        <div className="w-8 h-8 rounded-full bg-[#0D9488] text-white flex items-center justify-center flex-shrink-0 font-bold text-sm">
                                            {index + 1}
                                        </div>
                                        <p className="text-sm text-[#0F766E] font-[Lexend] leading-relaxed">{item}</p>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Transcript */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} className="mb-12">
                    <Card>
                        <CardHeader className="border-b border-[#F1F5F9]">
                            <CardTitle className="font-[Lora]">Interview Transcript</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="max-h-[500px] overflow-y-auto p-6 space-y-6">
                                {transcript.length > 0 ? transcript.map((message) => (
                                    <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`max-w-[85%] p-4 rounded-[16px] ${message.sender === 'interviewer'
                                                ? 'bg-[#F8FAFC] border border-[#E5E7EB] text-[#0F172A]'
                                                : 'bg-[#0F172A] text-white shadow-lg'
                                            }`}>
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className={`text-[10px] font-bold uppercase tracking-widest ${message.sender === 'interviewer' ? 'text-[#94A3B8]' : 'text-[#94A3B8]'
                                                    }`}>
                                                    {message.sender === 'interviewer' ? 'AI Interviewer' : 'You'}
                                                </span>
                                            </div>
                                            <p className="text-sm leading-relaxed font-[Lexend]">{message.message}</p>
                                        </div>
                                    </div>
                                )) : (
                                    <p className="text-center text-[#94A3B8] py-8">No transcript available for this session.</p>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Actions */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }} className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Button variant="secondary" className="px-8"><Download size={18} className="mr-2" />Save as PDF</Button>
                    <Link href="/interview/setup" className="flex-1 max-w-[200px]">
                        <Button className="w-full">Try Again<ArrowRight size={18} className="ml-2" /></Button>
                    </Link>
                    <Link href="/dashboard" className="flex-1 max-w-[200px]">
                        <Button variant="outline" className="w-full"><Home size={18} className="mr-2" />Dashboard</Button>
                    </Link>
                </motion.div>
            </main>
        </div>
    );
}

export default function SessionSummaryPage() {
    return (
        <Suspense fallback={
            <div className="h-screen flex items-center justify-center bg-white">
                <Loader2 className="w-10 h-10 text-[#0D9488] animate-spin" />
            </div>
        }>
            <SessionSummaryContent />
        </Suspense>
    );
}

