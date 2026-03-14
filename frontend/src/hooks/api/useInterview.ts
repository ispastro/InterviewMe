import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { interviewService } from '@/services/interview.service';
import type { 
  Interview, 
  CVAnalysis, 
  JDAnalysis, 
  InterviewListResponse,
  InterviewStatsResponse 
} from '@/types/backend';

// Query keys for consistent caching
export const interviewKeys = {
  all: ['interviews'] as const,
  lists: () => [...interviewKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...interviewKeys.lists(), filters] as const,
  details: () => [...interviewKeys.all, 'detail'] as const,
  detail: (id: string) => [...interviewKeys.details(), id] as const,
  stats: () => [...interviewKeys.all, 'stats'] as const,
  analysis: (id: string) => [...interviewKeys.detail(id), 'analysis'] as const,
  turns: (id: string) => [...interviewKeys.detail(id), 'turns'] as const,
  feedback: (id: string) => [...interviewKeys.detail(id), 'feedback'] as const,
};

// Create interview
export function useCreateInterview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => interviewService.createInterview(data),
    onSuccess: (data) => {
      // Invalidate and refetch interview lists
      queryClient.invalidateQueries({ queryKey: interviewKeys.lists() });
      queryClient.invalidateQueries({ queryKey: interviewKeys.stats() });
      
      // Add the new interview to the cache
      queryClient.setQueryData(interviewKeys.detail(data.id), data);
    },
    onError: (error) => {
      console.error('Failed to create interview:', error);
    },
  });
}

// Get interview by ID
export function useInterview(interviewId: string | null, enabled = true) {
  return useQuery({
    queryKey: interviewKeys.detail(interviewId || ''),
    queryFn: () => interviewService.getInterview(interviewId!),
    enabled: enabled && !!interviewId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// Get user's interviews
export function useUserInterviews(page = 1, perPage = 10) {
  return useQuery({
    queryKey: interviewKeys.list({ page, perPage }),
    queryFn: () => interviewService.getUserInterviews(page, perPage),
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

// Get user interview statistics
export function useUserStats() {
  return useQuery({
    queryKey: interviewKeys.stats(),
    queryFn: () => interviewService.getUserStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Upload CV
export function useUploadCV() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ interviewId, file }: { interviewId: string; file: File }) =>
      interviewService.uploadCV(interviewId, file),
    onSuccess: (data, variables) => {
      // Update the interview cache with new CV analysis
      queryClient.setQueryData(
        interviewKeys.detail(variables.interviewId),
        (oldData: Interview | undefined) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            cv_analysis: data.analysis,
            status: 'cv_uploaded' as const,
          };
        }
      );
      
      // Invalidate related queries
      queryClient.invalidateQueries({ 
        queryKey: interviewKeys.analysis(variables.interviewId) 
      });
    },
    onError: (error) => {
      console.error('Failed to upload CV:', error);
    },
  });
}

// Upload CV as text
export function useUploadCVText() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ interviewId, cvText }: { interviewId: string; cvText: string }) =>
      interviewService.uploadCVText(interviewId, cvText),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(
        interviewKeys.detail(variables.interviewId),
        (oldData: Interview | undefined) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            cv_analysis: data.analysis,
            cv_raw_text: variables.cvText,
            status: 'cv_uploaded' as const,
          };
        }
      );
      
      queryClient.invalidateQueries({ 
        queryKey: interviewKeys.analysis(variables.interviewId) 
      });
    },
  });
}

// Upload JD
export function useUploadJD() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ interviewId, file }: { interviewId: string; file: File }) =>
      interviewService.uploadJD(interviewId, file),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(
        interviewKeys.detail(variables.interviewId),
        (oldData: Interview | undefined) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            jd_analysis: data.analysis,
            status: oldData.cv_analysis ? 'ready' : 'jd_uploaded' as const,
          };
        }
      );
      
      queryClient.invalidateQueries({ 
        queryKey: interviewKeys.analysis(variables.interviewId) 
      });
    },
  });
}

// Upload JD as text
export function useUploadJDText() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ interviewId, jdText }: { interviewId: string; jdText: string }) =>
      interviewService.uploadJDText(interviewId, jdText),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(
        interviewKeys.detail(variables.interviewId),
        (oldData: Interview | undefined) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            jd_analysis: data.analysis,
            jd_raw_text: variables.jdText,
            status: oldData.cv_analysis ? 'ready' : 'jd_uploaded' as const,
          };
        }
      );
      
      queryClient.invalidateQueries({ 
        queryKey: interviewKeys.analysis(variables.interviewId) 
      });
    },
  });
}

// Start interview
export function useStartInterview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (interviewId: string) => interviewService.startInterview(interviewId),
    onSuccess: (data, interviewId) => {
      // Update interview status
      queryClient.setQueryData(interviewKeys.detail(interviewId), data);
      
      // Invalidate lists to reflect status change
      queryClient.invalidateQueries({ queryKey: interviewKeys.lists() });
    },
  });
}

// Complete interview
export function useCompleteInterview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (interviewId: string) => interviewService.completeInterview(interviewId),
    onSuccess: (data, interviewId) => {
      // Update interview status
      queryClient.setQueryData(interviewKeys.detail(interviewId), data);
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: interviewKeys.lists() });
      queryClient.invalidateQueries({ queryKey: interviewKeys.stats() });
    },
  });
}

// Delete interview
export function useDeleteInterview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (interviewId: string) => interviewService.deleteInterview(interviewId),
    onSuccess: (_, interviewId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: interviewKeys.detail(interviewId) });
      
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: interviewKeys.lists() });
      queryClient.invalidateQueries({ queryKey: interviewKeys.stats() });
    },
  });
}

// Get interview turns
export function useInterviewTurns(interviewId: string | null, enabled = true) {
  return useQuery({
    queryKey: interviewKeys.turns(interviewId || ''),
    queryFn: () => interviewService.getInterviewTurns(interviewId!),
    enabled: enabled && !!interviewId,
    staleTime: 30 * 1000, // 30 seconds (turns update frequently during interview)
  });
}

// Get interview feedback
export function useInterviewFeedback(interviewId: string | null, enabled = true) {
  return useQuery({
    queryKey: interviewKeys.feedback(interviewId || ''),
    queryFn: () => interviewService.getInterviewFeedback(interviewId!),
    enabled: enabled && !!interviewId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Get interview analysis (CV + JD combined)
export function useInterviewAnalysis(interviewId: string | null, enabled = true) {
  return useQuery({
    queryKey: interviewKeys.analysis(interviewId || ''),
    queryFn: () => interviewService.getInterviewAnalysis(interviewId!),
    enabled: enabled && !!interviewId,
    staleTime: 10 * 60 * 1000, // 10 minutes (analysis doesn't change often)
  });
}

// Check interview readiness
export function useInterviewReadiness(interviewId: string | null, enabled = true) {
  return useQuery({
    queryKey: [...interviewKeys.detail(interviewId || ''), 'readiness'],
    queryFn: () => interviewService.checkInterviewReadiness(interviewId!),
    enabled: enabled && !!interviewId,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}