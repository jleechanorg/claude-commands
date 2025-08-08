import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiService } from '../services/api.service';
import type { User } from '../services/api.types';

interface AuthState {
  // State
  user: User | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setUser: (user: User | null) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      isLoading: false,
      error: null,
      isAuthenticated: false,

      // Login with email/password
      login: async (email: string, _password: string) => {
        set({ isLoading: true, error: null });
        try {
          // FRONTEND_LIMITATION: Using mock authentication until Firebase integration
          // Real authentication will be implemented with Firebase Auth SDK
          // const response = await apiService.login(email, password);

          // Simulated login for now
          const mockUser: User = {
            uid: 'mock-user-id',
            email,
            displayName: email.split('@')[0],
          };

          set({
            user: mockUser,
            isAuthenticated: true,
            isLoading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Login failed',
            isLoading: false
          });
          throw error;
        }
      },

      // Login with Google
      loginWithGoogle: async () => {
        set({ isLoading: true, error: null });
        try {
          const user = await apiService.login();

          set({
            user,
            isAuthenticated: true,
            isLoading: false
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Google login failed',
            isLoading: false
          });
          throw error;
        }
      },

      // Logout
      logout: async () => {
        set({ isLoading: true });
        try {
          await apiService.logout();

          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Logout failed',
            isLoading: false
          });
        }
      },

      // Check authentication status
      checkAuth: async () => {
        set({ isLoading: true });
        try {
          const user = await apiService.getCurrentUser();

          if (user) {
            set({
              user,
              isAuthenticated: true,
              isLoading: false
            });
          } else {
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false
            });
          }
        } catch (error) {
          set({
            user: null,
            isAuthenticated: false,
            error: null, // Don't show error for auth check
            isLoading: false
          });
        }
      },

      // Set user directly
      setUser: (user: User | null) => {
        set({
          user,
          isAuthenticated: !!user,
          error: null
        });
      },

      // Error management
      setError: (error: string | null) => {
        set({ error });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user }), // Only persist user data
    }
  )
);
