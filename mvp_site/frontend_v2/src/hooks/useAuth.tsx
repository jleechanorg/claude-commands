import { useState, useEffect } from 'react'
import { apiService } from '../services'
import type { User } from '../services/api.types'

export interface AuthState {
  user: User | null
  loading: boolean
  error: string | null
  isAuthenticated: boolean
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
    isAuthenticated: false,
  })

  useEffect(() => {
    // Use apiService for Firebase auth state changes
    const unsubscribe = apiService.onAuthStateChanged((user) => {
      setAuthState(prev => ({
        ...prev,
        user,
        loading: false,
        isAuthenticated: !!user
      }))
    })

    return unsubscribe
  }, [])

  const signInWithGoogle = async () => {
    try {
      setAuthState(prev => ({ ...prev, loading: true, error: null }))
      const user = await apiService.login()
      // Don't manually set auth state - let onAuthStateChanged handle it
      // This prevents race conditions between manual updates and Firebase listener
      return user
    } catch (error) {
      console.error('Sign-in error:', error)
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Sign-in failed'
      }))
      throw error
    }
  }

  const signOutUser = async () => {
    try {
      setAuthState(prev => ({ ...prev, loading: true, error: null }))
      await apiService.logout()
      // Don't manually set auth state - let onAuthStateChanged handle it
      // This prevents race conditions between manual updates and Firebase listener
    } catch (error) {
      console.error('Sign-out error:', error)
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Sign-out failed'
      }))
      throw error
    }
  }

  const clearError = () => {
    setAuthState(prev => ({ ...prev, error: null }))
  }

  return {
    ...authState,
    signInWithGoogle,
    signOut: signOutUser,
    clearError,
  }
}
