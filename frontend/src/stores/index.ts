// Store exports
export {
  useInterviewStore,
  // Granular selectors
  useIsConnected,
  useSessionId,
  useMessages,
  useLastMessage,
  useMessageCount,
  useFeedback,
  useAllFeedbacks,
  useLatestFeedback,
  useTimer,
  useFormattedTimer,
  useIsEvaluating,
  useIsRecording,
  useCurrentTurn,
  useInterview,
  useCVAnalysis,
  useJDAnalysis,
  useIsLoading,
  useError,
  // Computed selectors
  useHasInterview,
  useHasCVAnalysis,
  useHasJDAnalysis,
  useIsReady,
  useAverageScore,
  useIsActive,
  useIsPaused,
  useIsCompleted,
  useProgressPercentage,
  useUserMessages,
  useInterviewerMessages,
  useCVSkills,
  useJDRequiredSkills,
  useFeedbackCount,
  useSkillsMatch,
} from './interviewStore';
export { useUserStore, useUserSelectors } from './userStore';
export { useSettingsStore, useSettingsSelectors, useTheme } from './settingsStore';

// Re-export types for convenience
export type {
  InterviewSessionState,
  InterviewSettings,
  UIPreferences,
  ChatMessage,
  UIFeedback,
} from '@/types';