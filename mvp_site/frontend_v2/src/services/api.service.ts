/**
 * API Service for WorldArchitect.AI
 *
 * Handles all API communication with the Flask backend including:
 * - Authentication via Firebase
 * - Campaign CRUD operations
 * - Game interactions
 * - User settings
 * - Campaign exports
 */

import {
  User,
  Campaign,
  CampaignCreateRequest,
  CampaignUpdateRequest,
  CampaignDetailResponse,
  CampaignCreateResponse,
  InteractionRequest,
  InteractionResponse,
  UserSettings,
  ExportFormat,
  ApiResponse,
  ApiError
} from './api.types';

// Import Firebase v9+ SDK
import { auth, googleProvider } from '../lib/firebase';
import { signInWithPopup, signOut, onAuthStateChanged, User as FirebaseUser } from 'firebase/auth';

class ApiService {
  private baseUrl = '/api';

  /**
   * Test mode configuration for bypassing authentication
   */
  private testAuthBypass: { enabled: boolean; userId: string } | null = null;

  constructor() {
    // Check for test mode using environment variables OR URL parameters (development only)
    const isDevEnvironment = import.meta.env.DEV === true;
    const testModeEnabled = import.meta.env.VITE_TEST_MODE === 'true';
    const testUserId = import.meta.env.VITE_TEST_USER_ID || 'test-user-123';

    // Also check URL parameters for test mode
    const urlParams = new URLSearchParams(window.location.search);
    const urlTestMode = urlParams.get('test_mode') === 'true';
    const urlTestUserId = urlParams.get('test_user_id') || 'test-user-123';

    // Enable test mode if either env var or URL param indicates test mode
    const shouldEnableTestMode = isDevEnvironment && (testModeEnabled || urlTestMode);
    const finalTestUserId = urlTestUserId || testUserId;

    if (shouldEnableTestMode) {
      console.warn('⚠️ Test mode enabled - Authentication bypass active (DEV ONLY)');
      this.testAuthBypass = {
        enabled: true,
        userId: finalTestUserId
      };
    }
  }

  /**
   * Makes an authenticated API request
   */
  private async fetchApi<T = any>(
    path: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    const startTime = performance.now();

    // Build headers based on auth mode
    let headers: Record<string, string>;

    if (this.testAuthBypass?.enabled) {
      // Test mode headers
      headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': this.testAuthBypass.userId,
        'Content-Type': 'application/json',
      };
    } else {
      // Normal Firebase authentication
      const user = auth.currentUser;
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Get fresh token, forcing refresh on retries
      const forceRefresh = retryCount > 0;
      try {
        const token = await user.getIdToken(forceRefresh);
        if (!token) {
          throw new Error('Failed to get authentication token');
        }
        // Validate JWT token structure and content
        if (!token || typeof token !== 'string') {
          throw new Error('Authentication token is not a valid string');
        }

        // JWT tokens have 3 parts separated by dots (header.payload.signature)
        const tokenParts = token.split('.');
        if (tokenParts.length !== 3) {
          throw new Error('Authentication token is not a valid JWT format');
        }

        // Basic validation that each part is not empty
        if (tokenParts.some(part => !part || part.length === 0)) {
          throw new Error('Authentication token has invalid JWT structure');
        }

        headers = {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        };
      } catch (tokenError) {
        console.error('Token retrieval error:', tokenError);
        throw new Error(`Authentication token error: ${tokenError instanceof Error ? tokenError.message : 'Unknown error'}`);
      }
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(`${this.baseUrl}${path}`, config);
      const duration = ((performance.now() - startTime) / 1000).toFixed(2);

      if (!response.ok) {
        // Handle error responses
        let errorData: ApiResponse;
        try {
          errorData = await response.json();
        } catch {
          errorData = {
            error: `HTTP Error: ${response.status} ${response.statusText}`,
            traceback: `Status code ${response.status} indicates a server-side problem.`
          };
        }

        // Handle clock skew errors with retry
        if (response.status === 401 && retryCount < 2) {
          const errorMessage = errorData.error || errorData.message || '';
          const isClockSkewError =
            errorMessage.includes('Token used too early') ||
            errorMessage.includes('clock') ||
            errorMessage.includes('time') ||
            errorMessage.includes('Authentication failed: Token used too early');

          if (isClockSkewError) {
            if (import.meta.env?.DEV) {
              console.log(`🔄 Clock skew detected, retrying (${retryCount + 1}/2) after ${(retryCount + 1) * 1500}ms delay`);
            }
            // Increasing delay for clock skew - allows time for clock drift correction
            await new Promise(resolve => setTimeout(resolve, (retryCount + 1) * 1500));
            return this.fetchApi<T>(path, options, retryCount + 1);
          }
        }

        const errorMessage = errorData.error || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
        const error: ApiError = new Error(errorMessage);
        error.traceback = errorData.traceback;
        error.status = response.status;
        throw error;
      }

      const data = await response.json();
      if (import.meta.env?.DEV) {
        console.log(`✅ API call completed in ${duration}s:`, path);
      }
      return data;

    } catch (error) {
      console.error('API call failed:', path, error);
      throw error;
    }
  }

  /**
   * Get the current authenticated user
   */
  async getCurrentUser(): Promise<User | null> {
    if (this.testAuthBypass?.enabled) {
      // Return test user
      return {
        uid: this.testAuthBypass.userId,
        email: `${this.testAuthBypass.userId}@test.com`,
        displayName: 'Test User'
      };
    }

    const firebaseUser = auth.currentUser;
    if (!firebaseUser) {
      return null;
    }

    return {
      uid: firebaseUser.uid,
      email: firebaseUser.email,
      displayName: firebaseUser.displayName,
      photoURL: firebaseUser.photoURL
    };
  }

  /**
   * Sign in with Google (Firebase)
   */
  async login(): Promise<User> {
    if (this.testAuthBypass?.enabled) {
      throw new Error('Cannot login in test mode');
    }

    const result = await signInWithPopup(auth, googleProvider);

    return {
      uid: result.user.uid,
      email: result.user.email,
      displayName: result.user.displayName,
      photoURL: result.user.photoURL
    };
  }

  /**
   * Sign out
   */
  async logout(): Promise<void> {
    if (this.testAuthBypass?.enabled) {
      throw new Error('Cannot logout in test mode');
    }

    await signOut(auth);
  }

  /**
   * Get all campaigns for the current user
   */
  async getCampaigns(): Promise<Campaign[]> {
    const response = await this.fetchApi<Campaign[]>('/campaigns');
    return response;
  }

  /**
   * Get a specific campaign with full details
   */
  async getCampaign(campaignId: string): Promise<CampaignDetailResponse> {
    const response = await this.fetchApi<CampaignDetailResponse>(`/campaigns/${campaignId}`);
    return response;
  }

  /**
   * Create a new campaign
   */
  async createCampaign(data: CampaignCreateRequest): Promise<string> {
    const response = await this.fetchApi<CampaignCreateResponse>('/campaigns', {
      method: 'POST',
      body: JSON.stringify(data)
    });

    if (!response.success || !response.campaign_id) {
      throw new Error('Failed to create campaign');
    }

    return response.campaign_id;
  }

  /**
   * Update campaign details (currently only title)
   */
  async updateCampaign(campaignId: string, data: CampaignUpdateRequest): Promise<void> {
    const response = await this.fetchApi<ApiResponse>(`/campaigns/${campaignId}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });

    if (!response.success) {
      throw new Error(response.error || 'Failed to update campaign');
    }
  }

  /**
   * Delete a campaign
   * Note: This endpoint doesn't exist in the current Flask backend
   * This is documented as a missing API endpoint
   */
  async deleteCampaign(campaignId: string): Promise<void> {
    // TODO: Backend doesn't implement DELETE endpoint yet
    throw new Error('Delete campaign not implemented in backend');

    // When implemented, it would be:
    // await this.fetchApi(`/campaigns/${campaignId}`, {
    //   method: 'DELETE'
    // });
  }

  /**
   * Send a game interaction (user input)
   */
  async sendInteraction(
    campaignId: string,
    data: InteractionRequest
  ): Promise<InteractionResponse> {
    const response = await this.fetchApi<InteractionResponse>(
      `/campaigns/${campaignId}/interaction`,
      {
        method: 'POST',
        body: JSON.stringify(data)
      }
    );

    return response;
  }

  /**
   * Export a campaign to various formats
   */
  async exportCampaign(
    campaignId: string,
    format: ExportFormat = 'txt'
  ): Promise<Blob> {
    const response = await fetch(
      `${this.baseUrl}/campaigns/${campaignId}/export?format=${format}`,
      {
        method: 'GET',
        headers: await this.getAuthHeaders()
      }
    );

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * Get user settings
   */
  async getUserSettings(): Promise<UserSettings> {
    const response = await this.fetchApi<UserSettings>('/settings');
    return response;
  }

  /**
   * Update user settings
   */
  async updateUserSettings(settings: Partial<UserSettings>): Promise<void> {
    const response = await this.fetchApi<ApiResponse>('/settings', {
      method: 'POST',
      body: JSON.stringify(settings)
    });

    if (!response.success) {
      throw new Error(response.error || 'Failed to update settings');
    }
  }

  /**
   * Helper method to get auth headers for non-JSON requests
   */
  private async getAuthHeaders(): Promise<Record<string, string>> {
    if (this.testAuthBypass?.enabled) {
      return {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': this.testAuthBypass.userId,
      };
    }

    const user = auth.currentUser;
    if (!user) {
      throw new Error('User not authenticated');
    }

    const token = await user.getIdToken();
    return {
      'Authorization': `Bearer ${token}`,
    };
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    if (this.testAuthBypass?.enabled) {
      return true;
    }

    return auth.currentUser !== null;
  }

  /**
   * Listen to auth state changes
   */
  onAuthStateChanged(callback: (user: User | null) => void): () => void {
    if (this.testAuthBypass?.enabled) {
      // Call immediately with test user
      callback({
        uid: this.testAuthBypass.userId,
        email: `${this.testAuthBypass.userId}@test.com`,
        displayName: 'Test User'
      });

      // Return empty unsubscribe function
      return () => {};
    }

    // Normal Firebase auth state listener
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser: FirebaseUser | null) => {
      if (firebaseUser) {
        callback({
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName,
          photoURL: firebaseUser.photoURL
        });
      } else {
        callback(null);
      }
    });

    return unsubscribe;
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Also export the class for testing purposes
export { ApiService };
