'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useUserStore } from '@/stores';
import { authService } from '@/services/auth.service';
import type { User } from '@/types/backend';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const userStore = useUserStore();

  // Try to auto-login in development (non-blocking)
  useEffect(() => {
    if (authService.isDevelopment()) {
      authService.devLogin()
        .then(user => {
          if (user) userStore.login(user);
        })
        .catch(() => {
          // Silently fail - user can login manually
        });
    }
  }, []);

  const login = async (token: string) => {
    userStore.setLoading(true);
    userStore.setError(null);

    try {
      authService.setToken(token);
      const user = await authService.getCurrentUser();
      userStore.login(user);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      userStore.setError(errorMessage);
      authService.logout();
      throw error;
    } finally {
      userStore.setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    userStore.logout();
  };

  const refreshUser = async () => {
    if (!userStore.isAuthenticated) return;

    try {
      const user = await authService.getCurrentUser();
      userStore.setUser(user);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      logout();
    }
  };

  const contextValue: AuthContextType = {
    user: userStore.user,
    isAuthenticated: userStore.isAuthenticated,
    isLoading: userStore.isLoading || userStore.isInitializing,
    error: userStore.error,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Higher-order component for protected routes
export function withAuth<P extends object>(
  Component: React.ComponentType<P>
) {
  return function AuthenticatedComponent(props: P) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-white">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#E5E7EB] border-t-[#0D9488] rounded-full animate-spin mx-auto mb-4" />
            <p className="text-[#475569] font-[Lexend]">Loading...</p>
          </div>
        </div>
      );
    }

    if (!isAuthenticated) {
      // Redirect to login page
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      return null;
    }

    return <Component {...props} />;
  };
}
