import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authService } from '@/services/auth.service';
import { useUserStore } from '@/stores';
import type { User } from '@/types/backend';

// Query keys for auth operations
export const authKeys = {
  all: ['auth'] as const,
  user: () => [...authKeys.all, 'user'] as const,
  validation: () => [...authKeys.all, 'validation'] as const,
};

// Validate current token
export function useTokenValidation(enabled = true) {
  return useQuery({
    queryKey: authKeys.validation(),
    queryFn: () => authService.validateToken(),
    enabled: enabled && authService.isAuthenticated(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1, // Only retry once for auth validation
    refetchOnWindowFocus: true, // Check auth status when window regains focus
  });
}

// Get current user
export function useCurrentUser(enabled = true) {
  return useQuery({
    queryKey: authKeys.user(),
    queryFn: () => authService.getCurrentUser(),
    enabled: enabled && authService.isAuthenticated(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: (failureCount, error: any) => {
      // Don't retry if it's an auth error (401)
      if (error?.status === 401) return false;
      return failureCount < 2;
    },
  });
}

// Development login mutation
export function useDevLogin() {
  const queryClient = useQueryClient();
  const userStore = useUserStore();

  return useMutation({
    mutationFn: () => authService.devLogin(),
    onSuccess: (user) => {
      // Update user store
      userStore.login(user);
      
      // Update query cache
      queryClient.setQueryData(authKeys.user(), user);
      queryClient.setQueryData(authKeys.validation(), { valid: true, user });
      
      console.log('Development login successful');
    },
    onError: (error) => {
      console.error('Development login failed:', error);
      userStore.setError('Development login failed');
    },
  });
}

// Logout mutation
export function useLogout() {
  const queryClient = useQueryClient();
  const userStore = useUserStore();

  return useMutation({
    mutationFn: () => Promise.resolve(), // Logout is synchronous
    onMutate: () => {
      // Immediately clear auth state
      authService.logout();
      userStore.logout();
      
      // Clear all auth-related queries
      queryClient.removeQueries({ queryKey: authKeys.all });
      
      // Clear all other queries that might contain user-specific data
      queryClient.clear();
    },
    onSuccess: () => {
      console.log('Logout successful');
    },
  });
}

// Refresh user data
export function useRefreshUser() {
  const queryClient = useQueryClient();
  const userStore = useUserStore();

  return useMutation({
    mutationFn: () => authService.getCurrentUser(),
    onSuccess: (user) => {
      // Update user store
      userStore.setUser(user);
      
      // Update query cache
      queryClient.setQueryData(authKeys.user(), user);
    },
    onError: (error) => {
      console.error('Failed to refresh user:', error);
      
      // If refresh fails, user might need to re-authenticate
      if ((error as any)?.status === 401) {
        authService.logout();
        userStore.logout();
        queryClient.clear();
      }
    },
  });
}

// Custom hook for auth state management
export function useAuthState() {
  const userStore = useUserStore();
  const tokenValidation = useTokenValidation();
  const currentUser = useCurrentUser();
  const devLogin = useDevLogin();
  const logout = useLogout();
  const refreshUser = useRefreshUser();

  // Determine overall auth state
  const isLoading = userStore.isInitializing || 
                   tokenValidation.isLoading || 
                   currentUser.isLoading ||
                   devLogin.isPending ||
                   logout.isPending ||
                   refreshUser.isPending;

  const isAuthenticated = userStore.isAuthenticated && 
                         tokenValidation.data?.valid !== false;

  const error = userStore.error || 
               tokenValidation.error?.message ||
               currentUser.error?.message ||
               devLogin.error?.message ||
               refreshUser.error?.message;

  return {
    // State
    user: userStore.user,
    isAuthenticated,
    isLoading,
    error,
    
    // Token validation
    tokenValid: tokenValidation.data?.valid ?? null,
    tokenError: tokenValidation.error,
    
    // User data
    userData: currentUser.data,
    userError: currentUser.error,
    
    // Actions
    devLogin: devLogin.mutate,
    logout: logout.mutate,
    refreshUser: refreshUser.mutate,
    
    // Loading states for individual actions
    isDevLoggingIn: devLogin.isPending,
    isLoggingOut: logout.isPending,
    isRefreshing: refreshUser.isPending,
    
    // Success states
    devLoginSuccess: devLogin.isSuccess,
    logoutSuccess: logout.isSuccess,
    refreshSuccess: refreshUser.isSuccess,
  };
}