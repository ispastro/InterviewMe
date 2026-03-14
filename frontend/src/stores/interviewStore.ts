import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
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
          // Update current turn if it's a new question
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
          // Keep interview data
          interview: state.interview,
          cvAnalysis: state.cvAnalysis,
          jdAnalysis: state.jdAnalysis,
          isLoading: state.isLoading,
          error: state.error,
        }), false, 'resetSession'),
    }),
    {
      name: 'interview-store',
      // Only serialize essential data
      partialize: (state: any) => ({
        interviewId: state.interviewId,
        userId: state.userId,
        interview: state.interview,
        cvAnalysis: state.cvAnalysis,
        jdAnalysis: state.jdAnalysis,
      }),
    }
  )
);

// Selectors for computed values
export const useInterviewSelectors = () => {
  const store = useInterviewStore();
  
  return {
    // Computed properties
    hasInterview: !!store.interview,
    hasCVAnalysis: !!store.cvAnalysis,
    hasJDAnalysis: !!store.jdAnalysis,
    isReady: !!store.interview && !!store.cvAnalysis && !!store.jdAnalysis,
    messageCount: store.messages.length,
    feedbackCount: store.allFeedbacks.length,
    averageScore: store.allFeedbacks.length > 0 
      ? store.allFeedbacks.reduce((sum, f) => sum + f.overall_score, 0) / store.allFeedbacks.length 
      : 0,
    
    // Status checks
    isConnected: store.websocketConnected,
    isActive: store.status === 'active',
    isPaused: store.status === 'paused',
    isCompleted: store.status === 'completed',
    
    // Progress tracking
    progressPercentage: store.totalTurns > 0 
      ? (store.currentTurn / store.totalTurns) * 100 
      : 0,
    
    // Time formatting
    formattedTimer: () => {
      const minutes = Math.floor(store.timer / 60);
      const seconds = store.timer % 60;
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    },
    
    // Latest feedback
    latestFeedback: store.allFeedbacks[store.allFeedbacks.length - 1] || null,
    
    // Message filtering
    userMessages: store.messages.filter(m => m.sender === 'user'),
    interviewerMessages: store.messages.filter(m => m.sender === 'interviewer'),
    
    // Skills analysis
    cvSkills: store.cvAnalysis?.skills.technical || [],
    jdRequiredSkills: store.jdAnalysis?.required_skills || [],
    skillsMatch: () => {
      const cvSkills = store.cvAnalysis?.skills.technical || [];
      const jdSkills = store.jdAnalysis?.required_skills || [];
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
  };
};