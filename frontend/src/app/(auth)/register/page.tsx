'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mail, Lock, User, Bot, ArrowRight, Check } from 'lucide-react';
import { Button, Input, Card, CardContent } from '@/components/ui';
import { useUserStore } from '@/stores';
import { authService } from '@/services/auth.service';

export default function RegisterPage() {
    const router = useRouter();
    const { login } = useUserStore();
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [acceptTerms, setAcceptTerms] = useState(false);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!name || !email || !password) {
            setError('Please fill in all fields');
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (!acceptTerms) {
            setError('Please accept the terms and conditions');
            return;
        }

        setIsLoading(true);
        try {
            const user = await authService.register(name, email, password);
            login(user);
            router.push('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Registration failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center px-6 py-12 bg-[#F8FAFC]">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md"
            >
                {/* Logo */}
                <Link href="/" className="flex items-center justify-center gap-2 mb-8">
                    <div className="w-12 h-12 rounded-[12px] bg-[#0F172A] flex items-center justify-center">
                        <Bot size={26} className="text-white" />
                    </div>
                    <span className="text-2xl font-semibold text-[#0F172A] font-[Lora]">InterviewAI</span>
                </Link>

                <Card>
                    <CardContent>
                        <div className="text-center mb-8">
                            <h1 className="text-2xl font-semibold text-[#0F172A] mb-2 font-[Lora]">Create Account</h1>
                            <p className="text-[#475569] font-[Lexend]">Start your interview practice journey</p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <Input
                                label="Full Name"
                                type="text"
                                placeholder="John Doe"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                icon={<User size={18} />}
                            />

                            <Input
                                label="Email"
                                type="email"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                icon={<Mail size={18} />}
                            />

                            <Input
                                label="Password"
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                icon={<Lock size={18} />}
                            />

                            <Input
                                label="Confirm Password"
                                type="password"
                                placeholder="••••••••"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                icon={<Lock size={18} />}
                            />

                            {/* Terms checkbox */}
                            <label className="flex items-start gap-3 cursor-pointer group">
                                <div
                                    className={`w-5 h-5 rounded border flex-shrink-0 flex items-center justify-center transition-colors ${acceptTerms
                                            ? 'bg-[#0D9488] border-[#0D9488]'
                                            : 'border-[#E5E7EB] group-hover:border-[#94A3B8]'
                                        }`}
                                    onClick={() => setAcceptTerms(!acceptTerms)}
                                >
                                    {acceptTerms && <Check size={14} className="text-white" />}
                                </div>
                                <span className="text-sm text-[#475569] font-[Lexend]">
                                    I agree to the{' '}
                                    <Link href="#" className="text-[#0D9488] hover:underline">
                                        Terms of Service
                                    </Link>{' '}
                                    and{' '}
                                    <Link href="#" className="text-[#0D9488] hover:underline">
                                        Privacy Policy
                                    </Link>
                                </span>
                            </label>

                            {error && (
                                <p className="text-sm text-[#EF4444] font-[Lexend]">{error}</p>
                            )}

                            <Button
                                type="submit"
                                className="w-full"
                                isLoading={isLoading}
                            >
                                Create Account
                                <ArrowRight size={18} className="ml-2" />
                            </Button>
                        </form>

                        <p className="mt-8 text-center text-sm text-[#475569] font-[Lexend]">
                            Already have an account?{' '}
                            <Link href="/login" className="text-[#0D9488] hover:underline font-medium">
                                Sign in
                            </Link>
                        </p>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    );
}
