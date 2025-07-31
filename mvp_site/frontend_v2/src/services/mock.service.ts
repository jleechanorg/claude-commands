/**
 * Mock API Service for Frontend v2
 *
 * Intercepts API calls and returns mock data for development/testing.
 * Based on patterns from testing_ui folder.
 */

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
  ExportFormat,
  ApiResponse,
  ApiError,
  GameState,
  StoryEntry,
  DiceRoll
} from './api.types';

import {
  mockUsers,
  mockCampaigns,
  mockGameStates,
  mockStoryEntries,
  mockUserSettings,
  mockErrors,
  mockDelay
} from './mock-data';

class MockApiService {
  private mockMode = false;
  private currentUserId = 'test-user-basic';
  private errorRate = 0; // Percentage chance of random errors
  private campaigns: Campaign[] = [...mockCampaigns];
  private gameStates: Record<string, GameState> = { ...mockGameStates };
  private storyEntries: Record<string, StoryEntry[]> = { ...mockStoryEntries };

  /**
   * Enable or disable mock mode
   */
  setMockMode(enabled: boolean, userId?: string) {
    this.mockMode = enabled;
    if (userId) {
      this.currentUserId = userId;
    }
    console.log(`🎭 Mock mode ${enabled ? 'enabled' : 'disabled'} for user: ${this.currentUserId}`);
  }

  /**
   * Set error rate for testing error handling
   */
  setErrorRate(rate: number) {
    this.errorRate = Math.max(0, Math.min(100, rate));
    console.log(`🎲 Mock error rate set to ${this.errorRate}%`);
  }

  /**
   * Check if should return mock data
   */
  private shouldUseMock(): boolean {
    const urlParams = new URLSearchParams(window.location.search);
    const hasTestMode = urlParams.get('test_mode') === 'true';
    return this.mockMode || hasTestMode || (import.meta.env as any).VITE_MOCK_MODE === 'true';
  }

  /**
   * Simulate random errors for testing
   */
  private async maybeThrowError() {
    if (Math.random() * 100 < this.errorRate) {
      await mockDelay(200);
      const errors = Object.values(mockErrors);
      throw errors[Math.floor(Math.random() * errors.length)];
    }
  }

  /**
   * Auth endpoints
   */
  async getCurrentUser(): Promise<User> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay();
    await this.maybeThrowError();

    return mockUsers[this.currentUserId] || mockUsers['test-user-basic'];
  }

  async signIn(email: string, password: string): Promise<User> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(500);
    await this.maybeThrowError();

    // Mock auth - accept any email/password in test mode
    const userId = email.includes('pro') ? 'test-user-pro' :
                   email.includes('gm') ? 'test-user-gm' : 'test-user-basic';

    this.currentUserId = userId;
    return mockUsers[userId];
  }

  async signOut(): Promise<void> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(200);
    this.currentUserId = 'test-user-basic';
  }

  /**
   * Campaign endpoints
   */
  async getCampaigns(): Promise<CampaignListResponse> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(400);
    await this.maybeThrowError();

    const userCampaigns = this.campaigns.filter(c =>
      c.user_id === this.currentUserId || this.currentUserId === 'test-user-gm'
    );

    return {
      campaigns: userCampaigns,
      total: userCampaigns.length,
      page: 1,
      limit: 20
    };
  }

  async getCampaignById(id: string): Promise<CampaignDetailResponse> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(300);
    await this.maybeThrowError();

    const campaign = this.campaigns.find(c => c.id === id);
    if (!campaign) {
      throw mockErrors.notFound;
    }

    const story = this.storyEntries[id] || [];
    const game_state = this.gameStates[id] || {};

    return {
      campaign,
      story,
      game_state
    };
  }

  async createCampaign(data: CampaignCreateRequest): Promise<CampaignCreateResponse> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(600);
    await this.maybeThrowError();

    if (!data.title || data.title.trim().length === 0) {
      throw mockErrors.validation;
    }

    const newCampaign: Campaign = {
      id: `camp-${Date.now()}`,
      title: data.title,
      prompt: data.prompt,
      genre: data.genre,
      tone: data.tone,
      created_at: new Date().toISOString(),
      last_played: new Date().toISOString(),
      user_id: this.currentUserId,
      use_default_world: data.use_default_world,
      selected_prompts: data.selected_prompts,
      character_name: data.character_name,
      character_background: data.character_background,
      current_state: {
        scene: 'Your adventure begins...',
        turn_count: 0,
        status: 'active'
      }
    };

    this.campaigns.push(newCampaign);
    this.storyEntries[newCampaign.id] = [];
    this.gameStates[newCampaign.id] = {
      debug_mode: false,
      player_character_data: {
        name: data.character || 'Adventurer',
        level: 1,
        hp: 10,
        max_hp: 10
      }
    };

    return {
      campaign: newCampaign,
      message: 'Campaign created successfully!'
    };
  }

  async updateCampaign(id: string, data: CampaignUpdateRequest): Promise<Campaign> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(400);
    await this.maybeThrowError();

    const index = this.campaigns.findIndex(c => c.id === id);
    if (index === -1) {
      throw mockErrors.notFound;
    }

    this.campaigns[index] = {
      ...this.campaigns[index],
      ...data,
      last_played: new Date().toISOString()
    };

    return this.campaigns[index];
  }

  async deleteCampaign(id: string): Promise<void> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(500);
    await this.maybeThrowError();

    const index = this.campaigns.findIndex(c => c.id === id);
    if (index === -1) {
      throw mockErrors.notFound;
    }

    this.campaigns.splice(index, 1);
    delete this.storyEntries[id];
    delete this.gameStates[id];
  }

  /**
   * Game interaction endpoints
   */
  async sendInteraction(campaignId: string, data: InteractionRequest): Promise<InteractionResponse> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(800); // Simulate AI thinking
    await this.maybeThrowError();

    const campaign = this.campaigns.find(c => c.id === campaignId);
    if (!campaign) {
      throw mockErrors.notFound;
    }

    // Generate mock AI response based on input
    let narrative = '';
    const diceRolls = [];

    if (data.input.toLowerCase().includes('attack') || data.input.toLowerCase().includes('fight')) {
      const roll = Math.floor(Math.random() * 20) + 1;
      narrative = `You swing your weapon! ${roll >= 15 ? 'Critical hit!' : roll >= 10 ? 'Hit!' : 'Miss!'}`;
      diceRolls.push({
        type: 'Attack',
        result: roll,
        modifier: 3,
        total: roll + 3,
        reason: 'Basic attack'
      });
    } else if (data.input.toLowerCase().includes('talk') || data.input.toLowerCase().includes('say')) {
      narrative = `"${data.input.replace(/^(i |I )?(say|talk) /, '')}" you say. The NPC considers your words carefully and responds: "That's an interesting perspective. Tell me more about your journey."`;
    } else {
      narrative = `You ${data.input}. The world responds to your action, and new possibilities unfold before you.`;
    }

    // Add user entry to story
    const userEntry: StoryEntry = {
      actor: 'user',
      text: data.input,
      mode: data.mode || 'character',
      timestamp: new Date().toISOString()
    };

    // Add AI response to story
    const aiEntry: StoryEntry = {
      actor: 'gemini',
      text: narrative,
      narrative,
      dice_rolls: diceRolls.length > 0 ? diceRolls : undefined,
      timestamp: new Date().toISOString()
    };

    // Update story
    if (!this.storyEntries[campaignId]) {
      this.storyEntries[campaignId] = [];
    }
    this.storyEntries[campaignId].push(userEntry, aiEntry);

    // Update campaign
    campaign.last_played = new Date().toISOString();

    // Return response
    return {
      success: true,
      response: narrative,
      narrative,
      dice_rolls: diceRolls.length > 0 ? diceRolls : undefined,
      debug_mode: this.gameStates[campaignId]?.debug_mode || false
    };
  }

  /**
   * User settings endpoints
   */
  async getUserSettings(): Promise<UserSettings> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(200);
    await this.maybeThrowError();

    return mockUserSettings[this.currentUserId] || mockUserSettings['test-user-basic'];
  }

  async updateUserSettings(settings: Partial<UserSettings>): Promise<UserSettings> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(300);
    await this.maybeThrowError();

    mockUserSettings[this.currentUserId] = {
      ...mockUserSettings[this.currentUserId],
      ...settings
    };

    return mockUserSettings[this.currentUserId];
  }

  /**
   * Export endpoints
   */
  async exportCampaign(campaignId: string, format: ExportFormat): Promise<Blob> {
    if (!this.shouldUseMock()) throw new Error('Mock mode not enabled');

    await mockDelay(1000);
    await this.maybeThrowError();

    const campaign = this.campaigns.find(c => c.id === campaignId);
    if (!campaign) {
      throw mockErrors.notFound;
    }

    const story = this.storyEntries[campaignId] || [];
    const content = `# ${campaign.title}\n\n${campaign.prompt}\n\n## Story\n\n${story.map(s => `${s.actor}: ${s.text}`).join('\n\n')}`;

    return new Blob([content], { type: 'text/plain' });
  }

  /**
   * Test helper methods
   */
  resetMockData() {
    this.campaigns = [...mockCampaigns];
    this.gameStates = { ...mockGameStates };
    this.storyEntries = { ...mockStoryEntries };
    console.log('🔄 Mock data reset to defaults');
  }

  switchUser(userId: string) {
    if (mockUsers[userId]) {
      this.currentUserId = userId;
      console.log(`👤 Switched to user: ${userId}`);
    }
  }

  getMockState() {
    return {
      mockMode: this.mockMode,
      currentUserId: this.currentUserId,
      errorRate: this.errorRate,
      campaignCount: this.campaigns.length,
      users: Object.keys(mockUsers)
    };
  }
}

// Export singleton instance
export const mockApiService = new MockApiService();

// Export for testing
export default mockApiService;
