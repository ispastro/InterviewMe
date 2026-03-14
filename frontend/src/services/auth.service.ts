import { apiClient } from '@/lib/api-client';
import type { User } from '@/types/backend';

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface TokenValidationResponse {
  valid: boolean;
  user?: User;
  error?: string;
}

class AuthService {
  // Note: The backend uses NextAuth.js for authentication
  // These methods are for direct API authentication if needed
  
  async validateToken(): Promise<TokenValidationResponse> {
    try {
      const response = await apiClient.post<TokenValidationResponse>('/api/auth/validate');
      return response;
    } catch (error) {
      return { valid: false, error: 'Token validation failed' };
    }
  }

  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/api/auth/me');
  }

  // For development - create test token
  async createTestToken(email: string = 'test@example.com', name: string = 'Test User'): Promise<string> {
    const response = await apiClient.get<{ token: string }>('/dev/test-auth');
    return response.token;
  }

  // Set authentication token
  setToken(token: string): void {
    apiClient.setToken(token);
  }

  // Clear authentication
  logout(): void {
    apiClient.clearToken();
    // Redirect to login or home page
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    const token = localStorage.getItem('interviewme_token');
    return !!token;
  }

  // Get stored token
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('interviewme_token');
  }

  // Initialize authentication on app start
  async initializeAuth(): Promise<User | null> {
    if (!this.isAuthenticated()) {
      return null;
    }

    try {
      const validation = await this.validateToken();
      if (validation.valid && validation.user) {
        return validation.user;
      } else {
        this.logout();
        return null;
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      this.logout();
      return null;
    }
  }

  // For NextAuth.js integration
  handleNextAuthCallback(token: string): void {
    this.setToken(token);
  }

  // Development helper - auto-login for testing
  async devLogin(): Promise<User> {
    try {
      const token = await this.createTestToken();
      this.setToken(token);
      return await this.getCurrentUser();
    } catch (error) {
      throw new Error('Development login failed');
    }
  }

  // Login method (for development/testing)
  async login(email: string, password: string): Promise<User> {
    // TODO: Implement actual login when backend auth is ready
    // For now, use dev login
    if (this.isDevelopment()) {
      return this.devLogin();
    }
    throw new Error('Login not implemented - use NextAuth.js');
  }

  // Register method (for development/testing)
  async register(name: string, email: string, password: string): Promise<User> {
    // TODO: Implement actual registration when backend auth is ready
    if (this.isDevelopment()) {
      return this.devLogin();
    }
    throw new Error('Registration not implemented - use NextAuth.js');
  }

  // Check if running in development mode
  isDevelopment(): boolean {
    return process.env.NODE_ENV === 'development';
  }
}

export const authService = new AuthService();