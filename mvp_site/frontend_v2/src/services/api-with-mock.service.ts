/**
 * Enhanced API Service with Mock Mode Integration
 *
 * Wraps the real API service and intercepts calls when in mock mode.
 * Based on testing_ui patterns for seamless test/development experience.
 */

import { apiService } from './api.service';
import { mockApiService } from './mock.service';
import type {
  User,
  Campaign,
  CampaignCreateRequest,
  CampaignUpdateRequest,
  CampaignListResponse,
  CampaignDetailResponse,
  CampaignCreateResponse,
  InteractionRequest,
  InteractionResponse,
  UserSettings,
  ExportFormat
} from './api.types';

class ApiWithMockService {
  private useMock = false;

  constructor() {
    // Check URL params and environment
    const urlParams = new URLSearchParams(window.location.search);
    const hasTestMode = urlParams.get('test_mode') === 'true';
    const mockEnv = (import.meta.env as any).VITE_MOCK_MODE === 'true';

    this.useMock = hasTestMode || mockEnv;

    if (this.useMock) {
      const testUserId = urlParams.get('test_user_id') || 'test-user-basic';
      mockApiService.setMockMode(true, testUserId);
      console.log(`🎭 API Mock Mode Enabled - User: ${testUserId}`);
    }
  }

  /**
   * Enable or disable mock mode dynamically
   */
  setMockMode(enabled: boolean, userId?: string) {
    this.useMock = enabled;
    mockApiService.setMockMode(enabled, userId);
  }

  /**
   * Check if currently using mock mode
   */
  isMockMode(): boolean {
    return this.useMock;
  }

  /**
   * Auth endpoints
   */
  async getCurrentUser(): Promise<User | null> {
    if (this.useMock) {
      try {
        return await mockApiService.getCurrentUser();
      } catch {
        return null;
      }
    }
    return apiService.getCurrentUser();
  }

  async login(): Promise<User> {
    if (this.useMock) {
      return mockApiService.signIn('test@worldarchitect.ai', 'test123');
    }
    return apiService.login();
  }

  async logout(): Promise<void> {
    if (this.useMock) {
      return mockApiService.signOut();
    }
    return apiService.logout();
  }

  /**
   * Campaign endpoints
   */
  async getCampaigns(): Promise<Campaign[]> {
    if (this.useMock) {
      const response = await mockApiService.getCampaigns();
      return response.campaigns;
    }
    return apiService.getCampaigns();
  }

  async getCampaign(campaignId: string): Promise<CampaignDetailResponse> {
    if (this.useMock) {
      return mockApiService.getCampaignById(campaignId);
    }
    return apiService.getCampaign(campaignId);
  }

  async createCampaign(data: CampaignCreateRequest): Promise<string> {
    if (this.useMock) {
      const response = await mockApiService.createCampaign(data);
      return response.campaign.id;
    }
    return apiService.createCampaign(data);
  }

  async updateCampaign(campaignId: string, data: CampaignUpdateRequest): Promise<void> {
    if (this.useMock) {
      await mockApiService.updateCampaign(campaignId, data);
      return;
    }
    return apiService.updateCampaign(campaignId, data);
  }

  async deleteCampaign(campaignId: string): Promise<void> {
    if (this.useMock) {
      return mockApiService.deleteCampaign(campaignId);
    }
    return apiService.deleteCampaign(campaignId);
  }

  /**
   * Game interaction endpoints
   */
  async sendInteraction(
    campaignId: string,
    data: InteractionRequest
  ): Promise<InteractionResponse> {
    if (this.useMock) {
      return mockApiService.sendInteraction(campaignId, data);
    }
    return apiService.sendInteraction(campaignId, data);
  }

  /**
   * Export endpoints
   */
  async exportCampaign(
    campaignId: string,
    format: ExportFormat = 'txt'
  ): Promise<Blob> {
    if (this.useMock) {
      return mockApiService.exportCampaign(campaignId, format);
    }
    return apiService.exportCampaign(campaignId, format);
  }

  /**
   * Settings endpoints
   */
  async getUserSettings(): Promise<UserSettings> {
    if (this.useMock) {
      return mockApiService.getUserSettings();
    }
    return apiService.getUserSettings();
  }

  async updateUserSettings(settings: Partial<UserSettings>): Promise<void> {
    if (this.useMock) {
      await mockApiService.updateUserSettings(settings);
      return;
    }
    return apiService.updateUserSettings(settings);
  }

  /**
   * Utility methods
   */
  isAuthenticated(): boolean {
    if (this.useMock) {
      return true; // Always authenticated in mock mode
    }
    return apiService.isAuthenticated();
  }

  onAuthStateChanged(callback: (user: User | null) => void): () => void {
    if (this.useMock) {
      // Immediately call with mock user
      mockApiService.getCurrentUser().then(callback).catch(() => callback(null));

      // Return empty unsubscribe
      return () => {};
    }
    return apiService.onAuthStateChanged(callback);
  }

  /**
   * Mock-specific utilities
   */
  getMockService() {
    return this.useMock ? mockApiService : null;
  }

  setErrorRate(rate: number) {
    if (this.useMock) {
      mockApiService.setErrorRate(rate);
    }
  }

  resetMockData() {
    if (this.useMock) {
      mockApiService.resetMockData();
    }
  }

  switchMockUser(userId: string) {
    if (this.useMock) {
      mockApiService.switchUser(userId);
    }
  }
}

// Export singleton instance
export const apiWithMock = new ApiWithMockService();

// Export as default for easy drop-in replacement
export default apiWithMock;
