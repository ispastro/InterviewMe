'use client';

import { useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Upload, Loader2, ArrowLeft, CheckCircle, Shield, FileText } from 'lucide-react';
import { Button, toast, PageTransition } from '@/components/ui';
import { interviewService } from '@/services/interview.service';

export default function InterviewSetupPage() {
    const router = useRouter();
    const cvInputRef = useRef<HTMLInputElement>(null);
    const jdInputRef = useRef<HTMLInputElement>(null);

    const [cvFile, setCvFile] = useState<File | null>(null);
    const [jdFile, setJdFile] = useState<File | null>(null);
    const [jdText, setJdText] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const [processingStatus, setProcessingStatus] = useState<string>('');

    const jdCharCount = jdText.trim().length;
    const hasValidJd = Boolean(jdFile || jdCharCount >= 100);
    const canStartInterview = Boolean(cvFile && hasValidJd && !isUploading);

    const validateFileSize = (file: File, maxMb: number) => {
        const maxBytes = maxMb * 1024 * 1024;
        return file.size <= maxBytes;
    };

    const handleCVPick = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!validateFileSize(file, 5)) {
            setUploadError('CV file must be 5MB or smaller.');
            return;
        }

        setCvFile(file);
        setUploadError(null);
    };

    const handleJDPick = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!validateFileSize(file, 5)) {
            setUploadError('Job description file must be 5MB or smaller.');
            return;
        }

        setJdFile(file);
        setJdText('');
        setUploadError(null);
    };

    const handleStartInterview = async () => {
        if (!cvFile) {
            setUploadError('Please upload your CV to continue');
            return;
        }

        const trimmedJdText = jdText.trim();
        if (!jdFile && trimmedJdText.length < 100) {
            setUploadError('Job description must be at least 100 characters.');
            return;
        }

        if (!jdFile && !trimmedJdText) {
            setUploadError('Please upload a Job Description or paste the text.');
            return;
        }

        setIsUploading(true);
        setUploadError(null);
        setProcessingStatus('Analyzing your documents...');

        try {
            const interview = await interviewService.createInterview({
                cvFile,
                jdFile: jdFile || undefined,
                jdText: jdFile ? undefined : trimmedJdText,
            });

            setProcessingStatus('Ready! Starting interview...');

            setTimeout(() => {
                router.push(`/interview/live?interview_id=${interview.id}`);
            }, 500);
        } catch (error: any) {
            toast.error(error.message || 'Failed to create interview');
            setUploadError(error.message || 'Upload failed');
            setProcessingStatus('');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <PageTransition>
            <div className="relative min-h-screen overflow-x-hidden bg-slate-950 text-slate-100">
                <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(45,212,191,0.08),transparent_45%),radial-gradient(ellipse_at_bottom,rgba(2,6,23,0.96),rgba(2,6,23,1))]" />
                <div className="pointer-events-none absolute left-1/2 top-[-16rem] h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-teal-400/10 blur-[140px]" />

                {/* Header */}
                <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/75 backdrop-blur-xl">
                    <div className="relative mx-auto flex h-16 w-full max-w-6xl items-center px-6">
                        <Link
                            href="/dashboard"
                            className="inline-flex h-10 items-center gap-2 rounded-lg px-2 text-slate-400 transition-colors hover:text-slate-100"
                        >
                            <ArrowLeft size={18} />
                            <span className="text-sm">Back</span>
                        </Link>

                        <Link
                            href="/"
                            className="absolute left-1/2 top-1/2 inline-flex -translate-x-1/2 -translate-y-1/2 items-center gap-2"
                        >
                            <img src="/logo.png" alt="InterviewMe" className="h-8 w-auto rounded-xl border border-slate-600/80 object-contain shadow-sm" />
                            <span className="text-xl leading-none font-bold text-transparent bg-clip-text bg-gradient-to-b from-white via-slate-100 to-slate-300 drop-shadow-[0_0_12px_rgba(255,255,255,0.18)]">
                                InterviewMe
                            </span>
                        </Link>
                    </div>
                </header>

                {/* Main Content */}
                <main className="relative z-10 mx-auto w-full max-w-6xl px-6 py-12">
                    <div className="mb-10">
                        <h1 className="text-4xl md:text-5xl font-bold text-white mb-3">Set Up Your Interview</h1>
                        <p className="text-slate-400 text-lg max-w-2xl">
                            Upload your CV and add a job description. We will tailor the interview flow to your target role.
                        </p>
                    </div>

                    <div className="grid gap-8 lg:grid-cols-[1fr_340px]">
                        <section className="space-y-6">
                            {/* Step 1 */}
                            <div className="rounded-2xl border border-slate-700 bg-slate-900/45 p-6">
                                <div className="mb-4 flex items-start gap-3">
                                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-teal-500 text-xs font-bold text-white">
                                        1
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold text-white">Upload Your CV</h3>
                                        <p className="text-sm text-slate-400">PDF, DOCX, or TXT. Maximum size 5MB.</p>
                                    </div>
                                </div>

                                <input
                                    ref={cvInputRef}
                                    type="file"
                                    accept=".pdf,.doc,.docx,.txt"
                                    className="hidden"
                                    onChange={handleCVPick}
                                    disabled={isUploading}
                                />

                                <button
                                    onClick={() => cvInputRef.current?.click()}
                                    disabled={isUploading}
                                    className="w-full rounded-xl border-2 border-dashed border-slate-600/80 bg-slate-900/55 p-10 text-left transition-colors hover:border-slate-500 hover:bg-slate-800/70 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {cvFile ? (
                                        <div className="flex items-center justify-between gap-4">
                                            <div className="min-w-0">
                                                <p className="text-sm text-slate-400 mb-1">Selected CV</p>
                                                <p className="truncate font-medium text-white">{cvFile.name}</p>
                                            </div>
                                            <CheckCircle size={22} className="text-emerald-400 flex-shrink-0" />
                                        </div>
                                    ) : (
                                        <div className="text-center">
                                            <Upload size={34} className="mx-auto mb-3 text-slate-400" />
                                            <p className="font-medium text-slate-100 mb-1">Click to upload your CV</p>
                                            <p className="text-sm text-slate-500">Drag and drop also works</p>
                                        </div>
                                    )}
                                </button>
                            </div>

                            {/* Step 2 */}
                            <div className="rounded-2xl border border-slate-700 bg-slate-900/45 p-6">
                                <div className="mb-4 flex items-start gap-3">
                                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-teal-500 text-xs font-bold text-white">
                                        2
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold text-white">Add Job Description</h3>
                                        <p className="text-sm text-slate-400">Paste text or upload a JD file. Minimum 100 characters for pasted text.</p>
                                    </div>
                                </div>

                                <textarea
                                    value={jdText}
                                    onChange={(e) => {
                                        setJdText(e.target.value);
                                        if (e.target.value.trim()) setJdFile(null);
                                    }}
                                    className="mb-3 h-48 w-full resize-none rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-[#0D9488] focus:border-[#0D9488]"
                                    placeholder="Paste the job description here...\n\nInclude role requirements, responsibilities, and qualifications."
                                    disabled={isUploading}
                                />

                                <div className="flex flex-wrap items-center justify-between gap-3">
                                    <div className="text-xs text-slate-500">
                                        {jdFile ? 'Using uploaded JD file' : `${jdCharCount}/100+ characters`}
                                    </div>

                                    <div className="flex items-center gap-3">
                                        <input
                                            ref={jdInputRef}
                                            type="file"
                                            accept=".pdf,.doc,.docx,.txt"
                                            className="hidden"
                                            onChange={handleJDPick}
                                            disabled={isUploading}
                                        />
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => jdInputRef.current?.click()}
                                            disabled={isUploading}
                                            className="border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800"
                                        >
                                            <Upload size={16} className="mr-2" />
                                            Upload JD File
                                        </Button>
                                    </div>
                                </div>

                                {jdFile && (
                                    <div className="mt-3 flex items-center gap-2 text-emerald-400">
                                        <CheckCircle size={16} />
                                        <span className="truncate text-sm font-medium">{jdFile.name}</span>
                                    </div>
                                )}
                            </div>

                            {/* Status Alerts */}
                            {uploadError && (
                                <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
                                    {uploadError}
                                </div>
                            )}

                            {isUploading && processingStatus && (
                                <div className="flex items-center gap-3 rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 text-sm text-blue-300">
                                    <Loader2 size={16} className="animate-spin" />
                                    {processingStatus}
                                </div>
                            )}
                        </section>

                        <aside className="space-y-4">
                            <div className="rounded-2xl border border-slate-700 bg-slate-900/55 p-5">
                                <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide mb-4">Readiness</h3>
                                <div className="space-y-3 text-sm">
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-400">CV uploaded</span>
                                        <span className={cvFile ? 'text-emerald-400' : 'text-slate-500'}>
                                            {cvFile ? 'Yes' : 'No'}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-400">JD provided</span>
                                        <span className={hasValidJd ? 'text-emerald-400' : 'text-slate-500'}>
                                            {hasValidJd ? 'Yes' : 'No'}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-400">Status</span>
                                        <span className={canStartInterview ? 'text-emerald-400' : 'text-amber-400'}>
                                            {canStartInterview ? 'Ready' : 'Incomplete'}
                                        </span>
                                    </div>
                                </div>

                                <Button
                                    size="lg"
                                    onClick={handleStartInterview}
                                    disabled={!canStartInterview}
                                    className="mt-5 w-full bg-white text-slate-900 hover:bg-slate-100"
                                >
                                    {isUploading ? (
                                        <>
                                            <Loader2 size={18} className="mr-2 animate-spin" />
                                            Processing...
                                        </>
                                    ) : (
                                        'Start Interview'
                                    )}
                                </Button>

                                <div className="mt-4 flex items-start gap-2 text-xs text-slate-400">
                                    <Shield size={14} className="mt-0.5 text-emerald-400" />
                                    Your files are processed securely and only used to personalize this interview.
                                </div>
                            </div>

                            <div className="rounded-2xl border border-slate-700 bg-slate-900/55 p-5">
                                <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide mb-3">Tips for best results</h3>
                                <ul className="space-y-2 text-sm text-slate-400">
                                    <li className="flex gap-2">
                                        <FileText size={14} className="mt-0.5 text-slate-500" />
                                        Use a real JD with required skills and responsibilities.
                                    </li>
                                    <li className="flex gap-2">
                                        <FileText size={14} className="mt-0.5 text-slate-500" />
                                        Upload your latest CV version with project details.
                                    </li>
                                    <li className="flex gap-2">
                                        <FileText size={14} className="mt-0.5 text-slate-500" />
                                        Provide at least 100 characters if pasting JD text.
                                    </li>
                                </ul>
                            </div>
                        </aside>
                    </div>
                </main>
            </div>
        </PageTransition>
    );
}
