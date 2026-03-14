import { apiClient } from '@/lib/api-client';
import type { Interview, CVAnalysis, JDAnalysis, Turn, Feedback } from '@/types/backend';

export interface CreateInterviewRequest {
  cvFile: File;
  jdFile?: File;
  jdText?: string;
  targetCompany?: string;
}

export interface CreateInterviewResponse {
  id: string;
  user_id: string;
  status: string;
  created_at: string;
  target_role?: string | null;
  target_company?: string | null;
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
  average_score: number | null;
  total_time_minutes: number;
  most_recent_interview: Record<string, any> | null;
  role_distribution: Record<string, number>;
  top_skills: Record<string, number>;
}

class InterviewService {
  // Create a new interview with polling for ready status
  async createInterview(data: CreateInterviewRequest): Promise<Interview> {
    const formData = new FormData();
    formData.append('cv_file', data.cvFile);

    if (data.jdFile) {
      formData.append('jd_file', data.jdFile);
    } else if (data.jdText) {
      formData.append('jd_text', data.jdText);
    } else {
      // Fallback JD for testing
      const fallbackJd = 'Software Engineer role requiring problem solving, communication, and technical depth. The candidate should explain past projects, architectural decisions, collaboration style, and delivery impact in a structured interview conversation.';
      formData.append('jd_text', fallbackJd);
    }

    if (data.targetCompany) {
      formData.append('target_company', data.targetCompany);
    }

    // Create interview
    const response = await apiClient.postForm<Interview>('/api/interviews', formData);
    
    // Poll until ready or failed
    return this.pollInterviewStatus(response.id);
  }

  // Poll interview status until ready
  private async pollInterviewStatus(interviewId: string, maxAttempts = 30): Promise<Interview> {
    for (let i = 0; i < maxAttempts; i++) {
      const interview = await this.getInterview(interviewId);
      
      if (interview.status === 'ready') {
        return interview;
      }
      
      if (interview.status === 'failed') {
        throw new Error('Interview processing failed. Please try again.');
      }
      
      // Wait 1 second before next poll
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error('Interview processing timeout. Please try again.');
  }

  // Get interview by ID with optional includes
  async getInterview(interviewId: string, includeAnalysis = false, includeTurns = false): Promise<Interview> {
    const params = new URLSearchParams();
    if (includeAnalysis) params.append('include_analysis', 'true');
    if (includeTurns) params.append('include_turns', 'true');
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get<Interview>(`/api/interviews/${interviewId}${query}`);
  }

  // Start interview (transition to IN_PROGRESS)
  async startInterview(interviewId: string): Promise<Interview> {
    return apiClient.post<Interview>(`/api/interviews/${interviewId}/start`);
  }

  // Complete interview (transition to COMPLETED)
  async completeInterview(interviewId: string, totalDurationSeconds?: number): Promise<Interview> {
    const params = totalDurationSeconds 
      ? `?total_duration_seconds=${totalDurationSeconds}` 
      : '';
    return apiClient.post<Interview>(`/api/interviews/${interviewId}/complete${params}`);
  }

  // Get user's interviews with pagination
  async getUserInterviews(page: number = 1, perPage: number = 10, statusFilter?: string): Promise<InterviewListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: perPage.toString(),
    });
    
    if (statusFilter) {
      params.append('status_filter', statusFilter);
    }
    
    return apiClient.get<InterviewListResponse>(`/api/interviews?${params.toString()}`);
  }

  // Get user interview statistics
  async getUserStats(): Promise<InterviewStatsResponse> {
    return apiClient.get<InterviewStatsResponse>('/api/interviews/stats/summary');
  }

  // Delete interview
  async deleteInterview(interviewId: string): Promise<void> {
    await apiClient.delete(`/api/interviews/${interviewId}`);
  }

  // Get interview turns (Q&A history)
  async getInterviewTurns(interviewId: string, includeEvaluation = true): Promise<Turn[]> {
    const params = includeEvaluation ? '?include_evaluation=true' : '';
    return apiClient.get<Turn[]>(`/api/interviews/${interviewId}/turns${params}`);
  }

  // Get interview feedback/summary
  async getInterviewFeedback(interviewId: string): Promise<Feedback> {
    return apiClient.get<Feedback>(`/api/interviews/${interviewId}/feedback`);
  }

  // Get interview analysis (CV + JD combined insights)
  async getInterviewAnalysis(interviewId: string): Promise<{
    cv_analysis: CVAnalysis;
    jd_analysis: JDAnalysis;
    skill_gap_analysis: {
      matching_skills: string[];
      missing_skills: string[];
      additional_skills: string[];
    };
  }> {
    return apiClient.get(`/api/interviews/${interviewId}/analysis`);
  }

  // Utility methods for file validation
  validateCVFile(file: File): { valid: boolean; error?: string } {
    const maxSize = 5 * 1024 * 1024; // 5MB
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];

    if (file.size > maxSize) {
      return { valid: false, error: 'File size must be less than 5MB' };
    }

    if (!allowedTypes.includes(file.type)) {
      return { valid: false, error: 'File must be PDF, DOCX, or TXT format' };
    }

    return { valid: true };
  }

  validateJDFile(file: File): { valid: boolean; error?: string } {
    return this.validateCVFile(file); // Same validation rules
  }

  // Helper to extract text from file for preview
  async extractTextPreview(file: File): Promise<string> {
    if (file.type === 'text/plain') {
      return file.text();
    }
    
    // For PDF and DOCX, we'll rely on backend processing
    // This is just for basic preview
    return `File: ${file.name} (${file.type}) - ${(file.size / 1024).toFixed(1)} KB`;
  }
}

export const interviewService = new InterviewService();
