import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { User } from '@/types/backend';

interface UserState {
  // User data
  user: User | null;
  isAuthenticated: boolean;
  
  // Loading states
  isLoading: boolean;
  isInitializing: boolean;
  
  // Error state
  error: string | null;
  
  // Actions
  setUser: (user: User | null) => void;
  setAuthenticated: (authenticated: boolean) => void;
  setLoading: (loading: boolean) => void;
  setInitializing: (initializing: boolean) => void;
  setError: (error: string | null) => void;
  login: (user: User) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  reset: () => void;
}

const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  isInitializing: false,
  error: null,
};

export const useUserStore = create<UserState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        setUser: (user) => 
          set({ user }, false, 'setUser'),

        setAuthenticated: (authenticated) => 
          set({ isAuthenticated: authenticated }, false, 'setAuthenticated'),

        setLoading: (loading) => 
          set({ isLoading: loading }, false, 'setLoading'),

        setInitializing: (initializing) => 
          set({ isInitializing: initializing }, false, 'setInitializing'),

        setError: (error) => 
          set({ error }, false, 'setError'),

        login: (user) => 
          set({ 
            user, 
            isAuthenticated: true, 
            error: null,
            isLoading: false 
          }, false, 'login'),

        logout: () => 
          set({ 
            user: null, 
            isAuthenticated: false, 
            error: null,
            isLoading: false 
          }, false, 'logout'),

        updateUser: (updates) =>
          set((state) => ({
            user: state.user ? { ...state.user, ...updates } : null
          }), false, 'updateUser'),

        reset: () => 
          set(initialState, false, 'reset'),
      }),
      {
        name: 'user-store',
        // Only persist essential user data
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    {
      name: 'user-store',
    }
  )
);

// Selectors for computed values
export const useUserSelectors = () => {
  const store = useUserStore();
  
  return {
    // User info
    userId: store.user?.id || null,
    userEmail: store.user?.email || null,
    userName: store.user?.name || null,
    displayName: store.user?.display_name || store.user?.name || store.user?.email || 'User',
    
    // Authentication status
    isLoggedIn: store.isAuthenticated && !!store.user,
    isGuest: !store.isAuthenticated || !store.user,
    
    // OAuth info
    isOAuthUser: !!store.user?.oauth_provider,
    oauthProvider: store.user?.oauth_provider || null,
    
    // Account status
    isActive: store.user?.is_active ?? false,
    
    // Loading states
    isReady: !store.isInitializing,
    hasError: !!store.error,
    
    // User preferences (can be extended)
    preferences: {
      // Add user preferences here when implemented
    },
    
    // Account creation date
    memberSince: store.user?.created_at ? new Date(store.user.created_at) : null,
    lastUpdated: store.user?.updated_at ? new Date(store.user.updated_at) : null,
  };
};