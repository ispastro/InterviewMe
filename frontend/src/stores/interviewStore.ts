import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { shallow } from 'zustand/shallow';
import type { 
  ChatMessage, 
  UIFeedback, 
  InterviewSessionState,
  Interview,
  CVAnalysis,
  JDAnalysis 
} from '@/types';

interface InterviewState extends InterviewSessionState {
  // Interview data
  interview: Interview | null;
  cvAnalysis: CVAnalysis | null;
  jdAnalysis: JDAnalysis | null;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setInterview: (interview: Interview) => void;
  setCVAnalysis: (analysis: CVAnalysis) => void;
  setJDAnalysis: (analysis: JDAnalysis) => void;
  setSessionId: (id: string | null) => void;
  setInterviewId: (id: string | null) => void;
  setUserId: (id: string | null) => void;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  setCurrentQuestion: (question: string) => void;
  setFeedback: (feedback: UIFeedback) => void;
  setRecording: (recording: boolean) => void;
  setWebsocketConnected: (connected: boolean) => void;
  setTimer: (seconds: number) => void;
  decrementTimer: () => void;
  setIsEvaluating: (evaluating: boolean) => void;
  setCurrentTurn: (turn: number) => void;
  incrementTurn: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
  resetSession: () => void;
}

const initialSessionState: InterviewSessionState = {
  sessionId: null,
  interviewId: null,
  userId: null,
  status: 'waiting',
  messages: [],
  currentQuestion: '',
  feedback: null,
  allFeedbacks: [],
  recording: false,
  websocketConnected: false,
  timer: 0,
  isEvaluating: false,
  currentTurn: 0,
  totalTurns: 0,
};

const initialState = {
  ...initialSessionState,
  interview: null,
  cvAnalysis: null,
  jdAnalysis: null,
  isLoading: false,
  error: null,
};

export const useInterviewStore = create<InterviewState>()(
  subscribeWithSelector(
    devtools(
      (set, get) => ({
        ...initialState,

        // Interview data setters
        setInterview: (interview) => 
          set({ interview }, false, 'setInterview'),

        setCVAnalysis: (analysis) => 
          set({ cvAnalysis: analysis }, false, 'setCVAnalysis'),

        setJDAnalysis: (analysis) => 
          set({ jdAnalysis: analysis }, false, 'setJDAnalysis'),

        // Session management
        setSessionId: (id) => 
          set({ sessionId: id }, false, 'setSessionId'),

        setInterviewId: (id) => 
          set({ interviewId: id }, false, 'setInterviewId'),

        setUserId: (id) => 
          set({ userId: id }, false, 'setUserId'),

        // Message management
        addMessage: (message) =>
          set((state) => ({
            messages: [...state.messages, message],
            currentTurn: message.sender === 'interviewer' 
              ? state.currentTurn + 1 
              : state.currentTurn
          }), false, 'addMessage'),

        updateMessage: (id, updates) =>
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === id ? { ...msg, ...updates } : msg
            ),
          }), false, 'updateMessage'),

        setCurrentQuestion: (question) => 
          set({ currentQuestion: question }, false, 'setCurrentQuestion'),

        // Feedback management
        setFeedback: (feedback) =>
          set((state) => ({
            feedback,
            allFeedbacks: [...state.allFeedbacks, feedback],
            isEvaluating: false,
          }), false, 'setFeedback'),

        // Recording state
        setRecording: (recording) => 
          set({ recording }, false, 'setRecording'),

        // WebSocket connection
        setWebsocketConnected: (connected) => 
          set({ 
            websocketConnected: connected,
            status: connected ? 'active' : 'disconnected'
          }, false, 'setWebsocketConnected'),

        // Timer management
        setTimer: (seconds) => 
          set({ timer: seconds }, false, 'setTimer'),

        decrementTimer: () =>
          set((state) => ({ 
            timer: Math.max(0, state.timer - 1) 
          }), false, 'decrementTimer'),

        // Evaluation state
        setIsEvaluating: (evaluating) => 
          set({ isEvaluating: evaluating }, false, 'setIsEvaluating'),

        // Turn management
        setCurrentTurn: (turn) => 
          set({ currentTurn: turn }, false, 'setCurrentTurn'),

        incrementTurn: () =>
          set((state) => ({ 
            currentTurn: state.currentTurn + 1 
          }), false, 'incrementTurn'),

        // Loading and error states
        setLoading: (loading) => 
          set({ isLoading: loading }, false, 'setLoading'),

        setError: (error) => 
          set({ error }, false, 'setError'),

        // Reset functions
        reset: () => 
          set(initialState, false, 'reset'),

        resetSession: () => 
          set((state) => ({
            ...initialSessionState,
            interview: state.interview,
            cvAnalysis: state.cvAnalysis,
            jdAnalysis: state.jdAnalysis,
            isLoading: state.isLoading,
            error: state.error,
          }), false, 'resetSession'),
      }),
      {
        name: 'interview-store',
        partialize: (state: any) => ({
          interviewId: state.interviewId,
          userId: state.userId,
          interview: state.interview,
          cvAnalysis: state.cvAnalysis,
          jdAnalysis: state.jdAnalysis,
        }),
      }
    )
  )
);

// ============================================================
// OPTIMIZED GRANULAR SELECTORS
// ============================================================

// Connection state
export const useIsConnected = () => 
  useInterviewStore(state => state.websocketConnected);

export const useSessionId = () => 
  useInterviewStore(state => state.sessionId);

// Messages
export const useMessages = () => 
  useInterviewStore(state => state.messages);

export const useLastMessage = () => 
  useInterviewStore(state => state.messages[state.messages.length - 1]);

export const useMessageCount = () => 
  useInterviewStore(state => state.messages.length);

// Feedback
export const useFeedback = () => 
  useInterviewStore(state => state.feedback);

export const useAllFeedbacks = () => 
  useInterviewStore(state => state.allFeedbacks);

export const useLatestFeedback = () => 
  useInterviewStore(state => state.allFeedbacks[state.allFeedbacks.length - 1]);

// Timer
export const useTimer = () => 
  useInterviewStore(state => state.timer);

export const useFormattedTimer = () => 
  useInterviewStore(state => {
    const minutes = Math.floor(state.timer / 60);
    const seconds = state.timer % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  });

// Status
export const useIsEvaluating = () => 
  useInterviewStore(state => state.isEvaluating);

export const useIsRecording = () => 
  useInterviewStore(state => state.recording);

export const useCurrentTurn = () => 
  useInterviewStore(state => state.currentTurn);

// Interview data
export const useInterview = () => 
  useInterviewStore(state => state.interview);

export const useCVAnalysis = () => 
  useInterviewStore(state => state.cvAnalysis);

export const useJDAnalysis = () => 
  useInterviewStore(state => state.jdAnalysis);

// Loading states
export const useIsLoading = () => 
  useInterviewStore(state => state.isLoading);

export const useError = () => 
  useInterviewStore(state => state.error);

// ============================================================
// COMPUTED SELECTORS (with shallow comparison)
// ============================================================

// Individual computed selectors (stable, no infinite loops)
export const useHasInterview = () => 
  useInterviewStore(state => !!state.interview);

export const useHasCVAnalysis = () => 
  useInterviewStore(state => !!state.cvAnalysis);

export const useHasJDAnalysis = () => 
  useInterviewStore(state => !!state.jdAnalysis);

export const useIsReady = () => 
  useInterviewStore(state => !!state.interview && !!state.cvAnalysis && !!state.jdAnalysis);

export const useFeedbackCount = () => 
  useInterviewStore(state => state.allFeedbacks.length);

export const useAverageScore = () => 
  useInterviewStore(state => 
    state.allFeedbacks.length > 0 
      ? state.allFeedbacks.reduce((sum, f) => sum + f.overall_score, 0) / state.allFeedbacks.length 
      : 0
  );

export const useIsActive = () => 
  useInterviewStore(state => state.status === 'active');

export const useIsPaused = () => 
  useInterviewStore(state => state.status === 'paused');

export const useIsCompleted = () => 
  useInterviewStore(state => state.status === 'completed');

export const useProgressPercentage = () => 
  useInterviewStore(state => 
    state.totalTurns > 0 ? (state.currentTurn / state.totalTurns) * 100 : 0
  );

export const useUserMessages = () => 
  useInterviewStore(state => state.messages.filter(m => m.sender === 'user'), shallow);

export const useInterviewerMessages = () => 
  useInterviewStore(state => state.messages.filter(m => m.sender === 'interviewer'), shallow);

export const useCVSkills = () => 
  useInterviewStore(state => state.cvAnalysis?.skills.technical || [], shallow);

export const useJDRequiredSkills = () => 
  useInterviewStore(state => state.jdAnalysis?.required_skills || [], shallow);

// Skills matching selector (memoized)
export const useSkillsMatch = () => {
  return useInterviewStore(
    state => {
      const cvSkills = state.cvAnalysis?.skills.technical || [];
      const jdSkills = state.jdAnalysis?.required_skills || [];
      const cvSkillsLower = cvSkills.map(s => s.toLowerCase());
      const jdSkillsLower = jdSkills.map(s => s.toLowerCase());
      
      return {
        matching: jdSkillsLower.filter(skill => 
          cvSkillsLower.some(cvSkill => cvSkill.includes(skill) || skill.includes(cvSkill))
        ),
        missing: jdSkillsLower.filter(skill => 
          !cvSkillsLower.some(cvSkill => cvSkill.includes(skill) || skill.includes(cvSkill))
        ),
        additional: cvSkillsLower.filter(skill => 
          !jdSkillsLower.some(jdSkill => jdSkill.includes(skill) || skill.includes(jdSkill))
        ),
      };
    },
    shallow
  );
};

// ============================================================
// PERFORMANCE MONITORING (Development only)
// ============================================================

if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  // Only log significant changes, not timer updates
  let lastLogTime = 0;
  const LOG_THROTTLE = 1000; // Log at most once per second
  
  useInterviewStore.subscribe(
    (state) => state,
    (state, prevState) => {
      const now = Date.now();
      if (now - lastLogTime < LOG_THROTTLE) return;
      
      const changedKeys = Object.keys(state).filter(
        key => state[key as keyof typeof state] !== prevState[key as keyof typeof prevState]
      );
      
      // Filter out timer updates for cleaner logs
      const significantChanges = changedKeys.filter(key => key !== 'timer');
      
      if (significantChanges.length > 0) {
        console.log('🔄 Store updated:', significantChanges);
        lastLogTime = now;
      }
    }
  );
}
