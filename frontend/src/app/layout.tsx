import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { QueryProvider } from "@/contexts/QueryProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "InterviewMe | AI-Powered Mock Interviews",
  description: "Practice your interview skills with our AI-powered mock interview simulator. Get real-time feedback, improve your communication, and land your dream job.",
  keywords: [
    "interview practice", 
    "mock interview", 
    "AI interview", 
    "job preparation", 
    "career development",
    "interview simulator",
    "job interview practice",
    "AI feedback",
    "interview coaching"
  ],
  authors: [{ name: "InterviewMe Team" }],
  creator: "InterviewMe",
  publisher: "InterviewMe",
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://interviewme.ai",
    title: "InterviewMe | AI-Powered Mock Interviews",
    description: "Practice your interview skills with our AI-powered mock interview simulator. Get real-time feedback and improve your performance.",
    siteName: "InterviewMe",
  },
  twitter: {
    card: "summary_large_image",
    title: "InterviewMe | AI-Powered Mock Interviews",
    description: "Practice your interview skills with our AI-powered mock interview simulator.",
    creator: "@interviewme_ai",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/manifest.json" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen`}
        style={{ background: 'var(--background)', color: 'var(--text-primary)' }}
      >
        <QueryProvider>
          <AuthProvider>
            <div id="root" className="min-h-screen">
              {children}
            </div>
            
            {/* Portal containers for modals and overlays */}
            <div id="modal-root" />
            <div id="tooltip-root" />
            <div id="notification-root" />
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}