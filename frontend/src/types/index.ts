// Re-export backend types for consistency
export type {
  User,
  Interview,
  CVAnalysis,
  JDAnalysis,
  Turn,
  TurnEvaluation,
  Feedback,
  InterviewConfig,
  InterviewPhase,
  MessageType,
  WebSocketMessage,
  CreateInterviewResponse,
  UploadResponse,
  InterviewListResponse,
  InterviewStatsResponse,
  ApiError
} from './backend';

import type { CVAnalysis, JDAnalysis, Interview, Feedback } from './backend';

// Frontend-specific types
export interface ChatMessage {
  id: string;
  sender: 'user' | 'interviewer';
  message: string;
  timestamp: Date;
  streaming?: boolean;
  type?: 'question' | 'answer' | 'feedback' | 'system';
}

// Simplified feedback for UI components
export interface UIFeedback {
  id: string;
  questionId: string;
  overall_score: number;
  criteria_scores: Record<string, number>;
  strengths: string[];  // Array of strings
  weaknesses: string[];  // Array of strings (renamed from areas_for_improvement)
  improvements: string[];  // Alias for areas_for_improvement
  feedback: string;
  modelAnswer?: string;  // Optional model answer
}

// Score breakdown for charts and displays
export interface ScoreBreakdown {
  communication: number; // 1-10
  confidence: number;
  structure: number;
  technicalDepth: number;
  relevance: number;
  overall: number;
}

// Interview session state for frontend
export interface InterviewSessionState {
  sessionId: string | null;
  interviewId: string | null;
  userId: string | null;
  status: 'waiting' | 'active' | 'paused' | 'completed' | 'disconnected';
  messages: ChatMessage[];
  currentQuestion: string;
  feedback: UIFeedback | null;
  allFeedbacks: UIFeedback[];
  recording: boolean;
  websocketConnected: boolean;
  timer: number;
  isEvaluating: boolean;
  currentTurn: number;
  totalTurns: number;
}

// User settings for interview preferences
export interface InterviewSettings {
  selectedRole: string;
  difficulty: 'easy' | 'medium' | 'hard';
  interviewStyle: 'friendly' | 'neutral' | 'strict';
  mode: 'text' | 'voice';
  duration: 5 | 10 | 20 | 30 | 45 | 60; // minutes
  focusAreas: string[];
  enableRealTimeFeedback: boolean;
  autoAdvance: boolean;
}

// Session summary for dashboard
export interface SessionSummary {
  id: string;
  role: string;
  company: string | null;
  date: Date;
  duration: number; // minutes
  overallScore: number;
  scores: ScoreBreakdown;
  questionsAnswered: number;
  status: 'completed' | 'incomplete';
  feedback?: {
    strengths: string[];
    improvements: string[];
    recommendation: string;
  };
}

// File upload types
export interface FileUploadState {
  file: File | null;
  uploading: boolean;
  progress: number;
  error: string | null;
  preview: string | null;
}

export interface CVUploadState extends FileUploadState {
  analysis: CVAnalysis | null;
}

export interface JDUploadState extends FileUploadState {
  analysis: JDAnalysis | null;
}

// WebSocket connection state
export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  sessionId: string | null;
  lastPing: Date | null;
  reconnectAttempts: number;
}

// Navigation and routing types
export interface RouteParams {
  interviewId?: string;
  sessionId?: string;
  userId?: string;
}

// Form validation types
export interface ValidationError {
  field: string;
  message: string;
}

export interface FormState<T> {
  data: T;
  errors: ValidationError[];
  isValid: boolean;
  isSubmitting: boolean;
}

// API loading states
export interface LoadingState {
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

// Notification types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

// Theme and UI preferences
export interface UIPreferences {
  theme: 'light' | 'dark' | 'system';
  fontSize: 'small' | 'medium' | 'large';
  reducedMotion: boolean;
  highContrast: boolean;
}

// Analytics and tracking
export interface AnalyticsEvent {
  event: string;
  properties: Record<string, any>;
  timestamp: Date;
  userId?: string;
  sessionId?: string;
}

// Performance monitoring
export interface PerformanceMetrics {
  pageLoadTime: number;
  apiResponseTime: number;
  websocketLatency: number;
  renderTime: number;
  memoryUsage?: number;
}

// Error boundary types
export interface ErrorInfo {
  componentStack: string;
  errorBoundary?: string;
}

export interface ErrorState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

// Utility types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// API response wrapper
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
  meta?: {
    page?: number;
    per_page?: number;
    total?: number;
    total_pages?: number;
  };
}

// Pagination
export interface PaginationState {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// Search and filtering
export interface SearchFilters {
  query?: string;
  status?: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  scoreRange?: {
    min: number;
    max: number;
  };
  roles?: string[];
  companies?: string[];
}

// Export commonly used type unions
export type InterviewStatus = Interview['status'];
export type SeniorityLevel = CVAnalysis['seniority_level'];
export type EmploymentType = JDAnalysis['employment_type'];
export type CompanySize = JDAnalysis['company_culture']['size'];
export type WorkStyle = JDAnalysis['company_culture']['work_style'];
export type Recommendation = Feedback['recommendation'];