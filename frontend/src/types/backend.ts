// Backend-aligned type definitions matching the Python models

export interface User {
  id: string; // UUID
  email: string;
  name: string | null;
  display_name: string;
  oauth_provider: string | null;
  oauth_subject: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Interview {
  id: string; // UUID
  user_id: string;
  status: 'pending' | 'processing_cv' | 'ready' | 'in_progress' | 'completed' | 'failed';
  cv_raw_text: string | null;
  cv_analysis: CVAnalysis | null;
  jd_raw_text: string | null;
  jd_analysis: JDAnalysis | null;
  interview_config: InterviewConfig | null;
  target_role: string | null;
  target_company: string | null;
  session_state: SessionState | null;
  current_phase: InterviewPhase | null;
  current_turn: number;
  completed_at: string | null;
  total_duration_seconds: number | null;
  created_at: string;
  updated_at: string;
  turn_count?: number;
  has_feedback?: boolean;
}

export interface CVAnalysis {
  candidate_name: string;
  years_of_experience: number;
  current_role: string;
  seniority_level: 'junior' | 'mid' | 'senior' | 'lead' | 'principal';
  skills: {
    technical: string[];
    soft: string[];
  };
  experience: Array<{
    role: string;
    company: string;
    duration: string;
    key_achievements: string[];
    technologies_used: string[];
  }>;
  education: Array<{
    degree: string;
    institution: string;
    year: string;
    relevant_coursework: string[];
  }>;
  projects: Array<{
    name: string;
    description: string;
    technologies: string[];
    achievements: string[];
  }>;
  certifications: string[];
  notable_points: string[];
  potential_gaps: string[];
  interview_focus_areas: string[];
  _metadata?: {
    processed_at: string;
    ai_model: string;
    text_length: number;
    word_count: number;
  };
}

export interface JDAnalysis {
  role_title: string;
  company: string | null;
  department: string | null;
  seniority_level: 'junior' | 'mid' | 'senior' | 'lead' | 'principal' | 'executive';
  employment_type: 'full-time' | 'part-time' | 'contract' | 'internship';
  location: string | null;
  salary_range: string | null;
  required_skills: string[];
  preferred_skills: string[];
  required_experience: {
    years_minimum: number;
    years_preferred: number;
    specific_domains: string[];
  };
  key_responsibilities: string[];
  technical_requirements: string[];
  soft_skills: string[];
  education_requirements: string[];
  company_culture: {
    values: string[];
    work_style: 'collaborative' | 'independent' | 'hybrid';
    pace: 'fast-paced' | 'steady' | 'flexible';
    size: 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
  };
  benefits: string[];
  growth_opportunities: string[];
  interview_focus_areas: string[];
  question_categories: {
    technical: string[];
    behavioral: string[];
    system_design: string[];
    coding: string[];
  };
  red_flags_to_watch: string[];
  success_metrics: string[];
  _metadata?: {
    processed_at: string;
    ai_model: string;
    text_length: number;
    word_count: number;
  };
}

export interface InterviewConfig {
  difficulty_level: number; // 0.0 to 1.0
  total_duration_minutes: number;
  question_counts: {
    intro: number;
    behavioral: number;
    technical: number;
    deep_dive: number;
    closing: number;
  };
  focus_areas: string[];
  critical_skills: string[];
  behavioral_context: {
    company_culture: any;
    key_responsibilities: string[];
  };
  technical_depth: {
    system_design_required: boolean;
    coding_required: boolean;
    architecture_focus: boolean;
  };
}

export interface SessionState {
  current_question?: any;
  conversation_history?: Turn[];
  phase_progress?: Record<string, number>;
  evaluation_context?: any;
}

export type InterviewPhase = 'intro' | 'behavioral' | 'technical' | 'deep_dive' | 'closing';

export interface Turn {
  id: string; // UUID
  interview_id: string;
  turn_number: number;
  phase: InterviewPhase;
  ai_question: string;
  user_answer: string | null;
  evaluation: TurnEvaluation | null;
  duration_seconds: number | null;
  difficulty_level: number | null;
  created_at: string;
  updated_at: string;
  has_answer: boolean;
  has_evaluation: boolean;
  overall_score?: number;
}

export interface TurnEvaluation {
  overall_score: number;
  criteria_scores: {
    relevance?: number;
    depth?: number;
    clarity?: number;
    technical_knowledge?: number;
    communication_skills?: number;
    problem_solving?: number;
  };
  strengths: string[];
  areas_for_improvement: string[];
  feedback: string;
  follow_up_suggestions: string[];
}

export interface Feedback {
  id: string; // UUID
  interview_id: string;
  overall_score: number;
  strengths: Array<{
    area: string;
    score: number;
    description?: string;
  }>;
  weaknesses: Array<{
    area: string;
    score: number;
    description?: string;
  }>;
  suggestions: Array<{
    action: string;
    priority: 'low' | 'medium' | 'high';
    description?: string;
  }>;
  phase_scores: Record<InterviewPhase, number>;
  summary: string;
  recommendation: 'hire' | 'maybe' | 'no_hire';
  recommendation_reason: string;
  next_steps: string[];
  created_at: string;
  updated_at: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: MessageType;
  data: any;
}

export type MessageType = 
  | 'connect'
  | 'start_interview'
  | 'user_response'
  | 'ai_question'
  | 'ai_feedback'
  | 'session_status'
  | 'pause_interview'
  | 'resume_interview'
  | 'end_interview'
  | 'error'
  | 'ping'
  | 'pong';

// API Response types
export interface CreateInterviewResponse {
  id: string;
  user_id: string;
  status: string;
  created_at: string;
  message: string;
}

export interface UploadResponse {
  message: string;
  analysis: CVAnalysis | JDAnalysis;
  processing_time: number;
}

export interface InterviewListResponse {
  interviews: Interview[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface InterviewStatsResponse {
  total_interviews: number;
  completed_interviews: number;
  in_progress_interviews: number;
  failed_interviews: number;
  completion_rate: number;
  average_score: number;
  total_time_minutes: number;
  most_recent_interview: Record<string, any> | null;
  role_distribution: Record<string, number>;
  top_skills: Record<string, number>;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy';
  service: string;
  version: string;
  environment: string;
}

export interface ReadinessCheckResponse {
  status: 'ready' | 'not_ready';
  checks: {
    database: boolean;
    configuration: boolean;
  };
  service: string;
  version: string;
}

// Error response type
export interface ApiError {
  detail: string;
  error_code?: string;
  timestamp?: string;
}