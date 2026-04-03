'use client';

import { useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Bot, Upload, FileText, Loader2, ArrowLeft, CheckCircle } from 'lucide-react';
import { Button, Card } from '@/components/ui';
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
            setUploadError(error.message || 'Upload failed');
            setProcessingStatus('');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-white">
            {/* Header */}
            <header className="border-b border-gray-200">
                <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/dashboard" className="flex items-center gap-2 text-gray-600 hover:text-gray-900">
                        <ArrowLeft size={20} />
                        <span className="text-sm">Back</span>
                    </Link>
                    <Link href="/" className="flex items-center gap-1">
                        <img src="/logo.png" alt="InterviewMe" className="h-8 w-auto object-contain" />
                        <span className="text-xl font-bold text-gray-900">InterviewMe</span>
                    </Link>
                    <div className="w-16"></div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-2xl mx-auto px-6 py-16">
                <div className="mb-12">
                    <h1 className="text-4xl font-bold text-gray-900 mb-3">Setup Your Interview</h1>
                    <p className="text-gray-600 text-lg">Upload your documents to begin</p>
                </div>

                {/* CV Upload */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-8 h-8 bg-[#0D9488] text-white flex items-center justify-center font-bold text-sm">
                            1
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900">Upload Your CV</h3>
                            <p className="text-sm text-gray-600">PDF, DOCX, TXT (Max 5MB)</p>
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
                        className="w-full border-2 border-dashed border-gray-300 p-12 hover:border-gray-400 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {cvFile ? (
                            <div className="flex flex-col items-center gap-2 text-[#0D9488]">
                                <CheckCircle size={28} />
                                <span className="font-medium">{cvFile.name}</span>
                            </div>
                        ) : (
                            <div className="text-center">
                                <Upload size={36} className="mx-auto mb-3 text-gray-400" />
                                <p className="text-gray-600 font-medium mb-1">Click to upload your CV</p>
                                <p className="text-sm text-gray-500">or drag and drop</p>
                            </div>
                        )}
                    </button>
                </div>

                {/* JD Upload */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-8 h-8 bg-[#0D9488] text-white flex items-center justify-center font-bold text-sm">
                            2
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900">Job Description</h3>
                            <p className="text-sm text-gray-600">Upload file or paste text below</p>
                        </div>
                    </div>

                    <textarea
                        value={jdText}
                        onChange={(e) => {
                            setJdText(e.target.value);
                            if (e.target.value.trim()) setJdFile(null);
                        }}
                        className="w-full h-48 px-4 py-3 border border-gray-300 rounded-none resize-none focus:outline-none focus:ring-1 focus:ring-[#0D9488] focus:border-[#0D9488] mb-3"
                        placeholder="Paste the job description here...&#x0A;&#x0A;Include role requirements, responsibilities, and qualifications."
                        disabled={isUploading}
                    />

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
                            className="rounded-none"
                        >
                            <Upload size={16} className="mr-2" />
                            Upload File Instead
                        </Button>
                        {jdFile && (
                            <div className="flex items-center gap-2 text-[#0D9488]">
                                <CheckCircle size={16} />
                                <span className="text-sm font-medium truncate">
                                    {jdFile.name}
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Error Message */}
                {uploadError && (
                    <div className="mb-6 p-4 border border-red-300 bg-red-50 text-red-700 text-sm">
                        {uploadError}
                    </div>
                )}

                {/* Processing Status */}
                {isUploading && processingStatus && (
                    <div className="mb-6 p-4 border border-blue-300 bg-blue-50 text-blue-700 text-sm flex items-center gap-3">
                        <Loader2 size={16} className="animate-spin" />
                        {processingStatus}
                    </div>
                )}

                {/* Start Button */}
                <div className="text-center">
                    <Button
                        size="lg"
                        onClick={handleStartInterview}
                        disabled={isUploading || !cvFile || (!jdFile && jdText.trim().length < 100)}
                        className="px-12 rounded-none group overflow-hidden relative"
                    >
                        {isUploading ? (
                            <>
                                <Loader2 size={18} className="mr-2 animate-spin" />
                                Processing...
                            </>
                        ) : (
                            <>
                                <span className="invisible">Start Interview</span>
                                <span className="absolute inset-0 flex items-center justify-center transition-transform duration-300 group-hover:-translate-y-full">
                                    Start Interview
                                </span>
                                <span className="absolute inset-0 flex items-center justify-center translate-y-full transition-transform duration-300 group-hover:translate-y-0">
                                    Start Interview
                                </span>
                            </>
                        )}
                    </Button>
                    <p className="mt-4 text-sm text-gray-500">
                        Your data is encrypted and secure
                    </p>
                </div>
            </main>
        </div>
    );
}
