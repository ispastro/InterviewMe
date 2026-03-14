import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { InterviewSettings, UIPreferences } from '@/types';

interface SettingsState {
  // Interview settings
  interview: InterviewSettings;
  
  // UI preferences
  ui: UIPreferences;
  
  // Notification preferences
  notifications: {
    enableSound: boolean;
    enableDesktop: boolean;
    enableEmail: boolean;
    interviewReminders: boolean;
    feedbackAlerts: boolean;
  };
  
  // Privacy settings
  privacy: {
    shareAnalytics: boolean;
    saveInterviewHistory: boolean;
    allowRecording: boolean;
  };
  
  // Actions
  updateInterviewSettings: (settings: Partial<InterviewSettings>) => void;
  updateUIPreferences: (preferences: Partial<UIPreferences>) => void;
  updateNotificationSettings: (notifications: Partial<SettingsState['notifications']>) => void;
  updatePrivacySettings: (privacy: Partial<SettingsState['privacy']>) => void;
  resetToDefaults: () => void;
  resetInterviewSettings: () => void;
}

const defaultInterviewSettings: InterviewSettings = {
  selectedRole: '',
  difficulty: 'medium',
  interviewStyle: 'friendly',
  mode: 'text',
  duration: 30,
  focusAreas: [],
  enableRealTimeFeedback: true,
  autoAdvance: false,
};

const defaultUIPreferences: UIPreferences = {
  theme: 'system',
  fontSize: 'medium',
  reducedMotion: false,
  highContrast: false,
};

const defaultNotifications = {
  enableSound: true,
  enableDesktop: false,
  enableEmail: true,
  interviewReminders: true,
  feedbackAlerts: true,
};

const defaultPrivacy = {
  shareAnalytics: true,
  saveInterviewHistory: true,
  allowRecording: true,
};

const initialState = {
  interview: defaultInterviewSettings,
  ui: defaultUIPreferences,
  notifications: defaultNotifications,
  privacy: defaultPrivacy,
};

export const useSettingsStore = create<SettingsState>()(
  devtools(
    persist(
      (set) => ({
        ...initialState,

        updateInterviewSettings: (settings) =>
          set((state) => ({
            interview: { ...state.interview, ...settings }
          }), false, 'updateInterviewSettings'),

        updateUIPreferences: (preferences) =>
          set((state) => ({
            ui: { ...state.ui, ...preferences }
          }), false, 'updateUIPreferences'),

        updateNotificationSettings: (notifications) =>
          set((state) => ({
            notifications: { ...state.notifications, ...notifications }
          }), false, 'updateNotificationSettings'),

        updatePrivacySettings: (privacy) =>
          set((state) => ({
            privacy: { ...state.privacy, ...privacy }
          }), false, 'updatePrivacySettings'),

        resetToDefaults: () =>
          set(initialState, false, 'resetToDefaults'),

        resetInterviewSettings: () =>
          set((state) => ({
            ...state,
            interview: defaultInterviewSettings
          }), false, 'resetInterviewSettings'),
      }),
      {
        name: 'settings-store',
        version: 1,
      }
    ),
    {
      name: 'settings-store',
    }
  )
);

// Selectors for computed values and convenience
export const useSettingsSelectors = () => {
  const store = useSettingsStore();
  
  return {
    // Interview settings shortcuts
    selectedRole: store.interview.selectedRole,
    difficulty: store.interview.difficulty,
    interviewStyle: store.interview.interviewStyle,
    mode: store.interview.mode,
    duration: store.interview.duration,
    focusAreas: store.interview.focusAreas,
    enableRealTimeFeedback: store.interview.enableRealTimeFeedback,
    autoAdvance: store.interview.autoAdvance,
    
    // UI preferences shortcuts
    theme: store.ui.theme,
    fontSize: store.ui.fontSize,
    reducedMotion: store.ui.reducedMotion,
    highContrast: store.ui.highContrast,
    
    // Notification shortcuts
    soundEnabled: store.notifications.enableSound,
    desktopNotifications: store.notifications.enableDesktop,
    emailNotifications: store.notifications.enableEmail,
    
    // Privacy shortcuts
    analyticsEnabled: store.privacy.shareAnalytics,
    historyEnabled: store.privacy.saveInterviewHistory,
    recordingAllowed: store.privacy.allowRecording,
    
    // Computed values
    isDarkMode: store.ui.theme === 'dark' || 
      (store.ui.theme === 'system' && 
       typeof window !== 'undefined' && 
       window.matchMedia('(prefers-color-scheme: dark)').matches),
    
    isLightMode: store.ui.theme === 'light' || 
      (store.ui.theme === 'system' && 
       typeof window !== 'undefined' && 
       !window.matchMedia('(prefers-color-scheme: dark)').matches),
    
    // Duration in seconds for timers
    durationInSeconds: store.interview.duration * 60,
    
    // Difficulty level as number (for AI processing)
    difficultyLevel: store.interview.difficulty === 'easy' ? 0.3 : 
                    store.interview.difficulty === 'medium' ? 0.6 : 0.9,
    
    // Style preferences for AI
    stylePreferences: {
      tone: store.interview.interviewStyle,
      formality: store.interview.interviewStyle === 'strict' ? 'formal' : 'casual',
      supportiveness: store.interview.interviewStyle === 'friendly' ? 'high' : 'medium',
    },
    
    // Accessibility settings
    accessibilityEnabled: store.ui.reducedMotion || store.ui.highContrast,
    
    // Complete settings object for API calls
    allSettings: {
      interview: store.interview,
      ui: store.ui,
      notifications: store.notifications,
      privacy: store.privacy,
    },
  };
};

// Hook for theme management
export const useTheme = () => {
  const { theme, isDarkMode, isLightMode } = useSettingsSelectors();
  const updateUIPreferences = useSettingsStore(state => state.updateUIPreferences);
  
  const setTheme = (newTheme: UIPreferences['theme']) => {
    updateUIPreferences({ theme: newTheme });
  };
  
  const toggleTheme = () => {
    const newTheme = isDarkMode ? 'light' : 'dark';
    setTheme(newTheme);
  };
  
  return {
    theme,
    isDarkMode,
    isLightMode,
    setTheme,
    toggleTheme,
  };
};