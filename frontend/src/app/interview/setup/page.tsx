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
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200">
                <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/dashboard" className="flex items-center gap-2 text-gray-600 hover:text-gray-900">
                        <ArrowLeft size={20} />
                        <span>Back</span>
                    </Link>
                    <Link href="/" className="flex items-center gap-2">
                        <Bot size={24} className="text-[#0D9488]" />
                        <span className="text-xl font-semibold text-gray-900">InterviewMe</span>
                    </Link>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-4xl mx-auto px-6 py-12">
                <div className="text-center mb-12">
                    <h1 className="text-3xl font-bold text-gray-900 mb-3">Setup Your Interview</h1>
                    <p className="text-gray-600">Upload your CV and job description to get started</p>
                </div>

                <div className="grid md:grid-cols-2 gap-6 mb-8">
                    {/* CV Upload */}
                    <Card className="p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-lg bg-[#F0FDFA] flex items-center justify-center">
                                <Upload size={20} className="text-[#0D9488]" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-gray-900">Your CV</h3>
                                <p className="text-sm text-gray-600">PDF, DOCX (Max 5MB)</p>
                            </div>
                        </div>

                        <input
                            ref={cvInputRef}
                            type="file"
                            accept=".pdf,.doc,.docx"
                            className="hidden"
                            onChange={handleCVPick}
                            disabled={isUploading}
                        />

                        <button
                            onClick={() => cvInputRef.current?.click()}
                            disabled={isUploading}
                            className="w-full border-2 border-dashed border-gray-300 rounded-lg p-8 hover:border-[#0D9488] hover:bg-[#F0FDFA] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {cvFile ? (
                                <div className="flex items-center justify-center gap-2 text-[#0D9488]">
                                    <CheckCircle size={20} />
                                    <span className="font-medium">{cvFile.name}</span>
                                </div>
                            ) : (
                                <div className="text-center">
                                    <Upload size={32} className="mx-auto mb-2 text-gray-400" />
                                    <p className="text-sm text-gray-600">Click to upload CV</p>
                                </div>
                            )}
                        </button>
                    </Card>

                    {/* JD Upload */}
                    <Card className="p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-lg bg-[#F0FDFA] flex items-center justify-center">
                                <FileText size={20} className="text-[#0D9488]" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-gray-900">Job Description</h3>
                                <p className="text-sm text-gray-600">Upload or paste text</p>
                            </div>
                        </div>

                        <textarea
                            value={jdText}
                            onChange={(e) => {
                                setJdText(e.target.value);
                                if (e.target.value.trim()) setJdFile(null);
                            }}
                            className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-[#0D9488] focus:border-transparent"
                            placeholder="Paste job description here..."
                            disabled={isUploading}
                        />

                        <div className="mt-3 flex items-center gap-3">
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
                                className="flex-1"
                            >
                                Upload File
                            </Button>
                            {jdFile && (
                                <span className="text-sm text-[#0D9488] font-medium truncate flex-1">
                                    {jdFile.name}
                                </span>
                            )}
                        </div>
                    </Card>
                </div>

                {/* Error Message */}
                {uploadError && (
                    <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                        {uploadError}
                    </div>
                )}

                {/* Processing Status */}
                {isUploading && processingStatus && (
                    <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 text-sm flex items-center gap-3">
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
                        className="px-12"
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
                    <p className="mt-4 text-sm text-gray-500">
                        Your data is encrypted and secure
                    </p>
                </div>
            </main>
        </div>
    );
}
