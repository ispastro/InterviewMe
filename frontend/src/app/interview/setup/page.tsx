'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
    Bot,
    ArrowRight,
    ArrowLeft,
    MessageSquare,
    Mic,
    Sparkles,
    FileText,
    Loader2
} from 'lucide-react';
import { Button, Card, CardContent } from '@/components/ui';
import { FileUpload } from '@/components/upload';
import { useSettingsStore, useSettingsSelectors } from '@/stores';
import { interviewService } from '@/services/interview.service';
import { cn } from '@/lib/utils';

export default function InterviewSetupPage() {
    const router = useRouter();
    const settingsStore = useSettingsStore();
    const settings = useSettingsSelectors();

    const [cvFile, setCvFile] = useState<File | null>(null);
    const [jdFile, setJdFile] = useState<File | null>(null);
    const [jdText, setJdText] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const [processingStatus, setProcessingStatus] = useState<string>('');

    const handlePasteJobDescription = async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text?.trim()) {
                setJdText(text.trim());
                setJdFile(null);
                setUploadError(null);
            }
        } catch {
            setUploadError('Could not access clipboard. Please paste manually into the text box.');
        }
    };

    const handleStartInterview = async () => {
        if (!cvFile) {
            setUploadError('Please upload your CV to continue');
            return;
        }

        const trimmedJdText = jdText.trim();
        if (!jdFile && trimmedJdText.length < 100) {
            setUploadError('Pasted job description is too short. Please provide at least 100 characters.');
            return;
        }

        if (!jdFile && !trimmedJdText) {
            setUploadError('Please upload a Job Description file or paste the text to continue.');
            return;
        }

        setIsUploading(true);
        setUploadError(null);
        setProcessingStatus('Uploading files...');

        try {
            // Show processing steps
            setTimeout(() => setProcessingStatus('Analyzing your CV with AI...'), 1000);
            setTimeout(() => setProcessingStatus('Processing job description...'), 3000);
            setTimeout(() => setProcessingStatus('Generating interview strategy...'), 5000);

            const interview = await interviewService.createInterview({
                cvFile,
                jdFile: jdFile || undefined,
                jdText: jdFile ? undefined : trimmedJdText,
            });

            setProcessingStatus('Interview ready! Redirecting...');

            // Navigate to live interview
            setTimeout(() => {
                router.push(`/interview/live?interview_id=${interview.id}`);
            }, 500);
        } catch (error: any) {
            setUploadError(error.message || 'Upload failed');
            setProcessingStatus('');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#F8FAFC]">
            <header className="sticky top-0 z-40 px-6 py-4 bg-white border-b border-[#E5E7EB]">
                <div className="max-w-4xl mx-auto flex items-center justify-between">
                    <Link
                        href="/dashboard"
                        className="flex items-center gap-2 text-[#475569] hover:text-[#0F172A] transition-colors font-[Lexend]"
                    >
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

            <main className="px-6 py-12 max-w-4xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-12"
                >
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#F0FDFA] border border-[#99F6E4] mb-6">
                        <Sparkles size={16} className="text-[#0D9488]" />
                        <span className="text-sm text-[#0D9488] font-[Lexend]">Context-Aware AI Interview</span>
                    </div>
                    <h1 className="text-3xl font-bold text-[#0F172A] mb-4 font-[Lora]">
                        Prepare for Your Specific Role
                    </h1>
                    <p className="text-[#475569] max-w-lg mx-auto font-[Lexend]">
                        Upload your profile and the job requirements. Our AI will craft an interview perfectly tailored to this position.
                    </p>
                </motion.div>

                <div className="space-y-8">
                    {/* Communication Mode Selection */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                        <Card className="border-none shadow-sm overflow-hidden">
                            <div className="bg-[#0F172A] px-6 py-4">
                                <h3 className="text-white font-[Lora] font-semibold flex items-center gap-2">
                                    <MessageSquare size={18} />
                                    Choose Your Interview Mode
                                </h3>
                            </div>
                            <CardContent className="p-6">
                                <div className="grid grid-cols-2 gap-4">
                                    {[
                                        { id: 'text', label: 'Text Session', icon: MessageSquare, description: 'Practice with real-time text chat' },
                                        { id: 'voice', label: 'Voice Session', icon: Mic, description: 'Simulate a real call with voice' },
                                    ].map((type) => (
                                        <button
                                            key={type.id}
                                            onClick={() => settingsStore.updateInterviewSettings({ mode: type.id as 'text' | 'voice' })}
                                            className={cn(
                                                'p-5 rounded-[16px] border transition-all duration-300 text-left relative group',
                                                settings.mode === type.id
                                                    ? 'bg-[#F0FDFA] border-[#0D9488] ring-2 ring-[#0D9488]/10'
                                                    : 'bg-white border-[#E5E7EB] hover:border-[#94A3B8] hover:bg-slate-50'
                                            )}
                                        >
                                            <div className={cn(
                                                "w-10 h-10 rounded-full flex items-center justify-center mb-3 transition-colors",
                                                settings.mode === type.id ? "bg-[#0D9488] text-white" : "bg-slate-100 text-slate-500 group-hover:bg-slate-200"
                                            )}>
                                                <type.icon size={20} />
                                            </div>
                                            <p className="font-semibold text-[#0F172A] font-[Lora]">{type.label}</p>
                                            <p className="text-sm text-[#475569] font-[Lexend] mt-1 pr-4">{type.description}</p>
                                            {settings.mode === type.id && (
                                                <div className="absolute top-4 right-4">
                                                    <div className="w-2 h-2 rounded-full bg-[#0D9488]" />
                                                </div>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* CV Upload */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                        <Card>
                            <CardContent className="p-6">
                                <FileUpload
                                    label="Your CV/Resume (Required)"
                                    description="PDF, DOC, or DOCX up to 10MB. This gives the AI context on your background."
                                    accept=".pdf,.doc,.docx"
                                    maxSize={10}
                                    file={cvFile}
                                    onFileSelect={setCvFile}
                                    onFileRemove={() => setCvFile(null)}
                                    isUploading={isUploading}
                                    error={uploadError}
                                />
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* JD Upload/Paste */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                        <Card>
                            <CardContent className="p-6">
                                <FileUpload
                                    label="Target Job Description (Required)"
                                    description="File or text. The interview strategy will be perfectly tailored to these requirements."
                                    accept=".pdf,.doc,.docx,.txt"
                                    maxSize={5}
                                    file={jdFile}
                                    onFileSelect={setJdFile}
                                    onFileRemove={() => setJdFile(null)}
                                    isUploading={isUploading}
                                />

                                <div className="mt-6 pt-6 border-t border-slate-100">
                                    <div className="flex items-center justify-between mb-3">
                                        <label className="text-sm font-semibold text-[#0F172A] font-[Lexend]">
                                            Or Paste Job Description Directly
                                        </label>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={handlePasteJobDescription}
                                            disabled={isUploading}
                                            className="text-[#0D9488] hover:text-[#0D9488] hover:bg-[#F0FDFA]"
                                        >
                                            <FileText size={16} className="mr-2" />
                                            Paste Skills & Duties
                                        </Button>
                                    </div>
                                    <textarea
                                        value={jdText}
                                        onChange={(e) => {
                                            setJdText(e.target.value);
                                            if (e.target.value.trim().length > 0) {
                                                setJdFile(null);
                                            }
                                        }}
                                        placeholder="Paste the requirements, responsibilities, and seniority details here..."
                                        className="w-full min-h-[160px] rounded-[12px] border border-[#E5E7EB] p-4 text-sm text-[#0F172A] font-[Lexend] focus:outline-none focus:ring-2 focus:ring-[#0D9488]/20 focus:border-[#0D9488] transition-all resize-none"
                                        disabled={isUploading}
                                    />
                                    <div className="mt-3 flex items-start gap-2">
                                        <div className="w-1.5 h-1.5 rounded-full bg-[#0D9488] mt-1.5 flex-shrink-0" />
                                        <p className="text-xs text-[#64748B] font-[Lexend] leading-relaxed">
                                            The more detail you provide, the more specific and challenging the AI's questions will be. Minimum 100 characters recommended.
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Processing Status */}
                    {isUploading && processingStatus && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="p-4 bg-[#F0FDFA] border border-[#0D9488] rounded-[12px] text-[#0D9488] text-sm font-[Lexend] flex items-center gap-3"
                        >
                            <Loader2 size={16} className="animate-spin" />
                            {processingStatus}
                        </motion.div>
                    )}

                    {uploadError && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="p-4 bg-red-50 border border-red-100 rounded-[12px] text-red-600 text-sm font-[Lexend] flex items-center gap-3"
                        >
                            <div className="w-2 h-2 rounded-full bg-red-600 animate-pulse" />
                            {uploadError}
                        </motion.div>
                    )}

                    <div className="pt-6">
                        <Button
                            onClick={handleStartInterview}
                            className="w-full shadow-lg shadow-[#0F172A]/10 h-14 text-base"
                            size="lg"
                            isLoading={isUploading}
                            disabled={!cvFile || (!jdFile && jdText.trim().length < 100)}
                        >
                            {isUploading ? 'Processing...' : 'Analyze & Start Practice Session'}
                            {!isUploading && <ArrowRight size={20} className="ml-2" />}
                        </Button>
                        <p className="text-center text-xs text-slate-400 mt-4 font-[Lexend]">
                            Our agentic engine will analyze your profile and the JD to create a custom session in ~5-10 seconds.
                        </p>
                    </div>
                </div>
            </main>
        </div>
    );
}
