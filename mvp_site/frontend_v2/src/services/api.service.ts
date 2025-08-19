/**
 * API Service for WorldArchitect.AI - REAL PRODUCTION MODE
 *
 * Handles all API communication with the Flask backend including:
 * - Authentication via Firebase
 * - Campaign CRUD operations
 * - Game interactions
 * - User settings
 * - Campaign exports
 */

import { devLog, devWarn, devError } from '../utils/dev';
import { MAX_DESCRIPTION_LENGTH } from '../constants/campaignDescriptions';
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
  private defaultTimeout = 30000; // 30 seconds
  private maxRetries = 3;
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  private cacheDefaultTTL = 5 * 60 * 1000; // 5 minutes
  private clockSkewOffset = 0; // Detected clock skew in milliseconds
  private clockSkewDetected = false;

  /**
   * Authentication bypass for development mode
   */
  private testAuthBypass: { enabled: boolean; userId: string } | null = null;

  constructor() {
    // SECURITY: Only enable test mode authentication bypass in non-production environments
    // This prevents authentication bypass in production builds via URL manipulation
    if (import.meta.env.MODE !== 'production') {
      // Enable test mode authentication bypass only when explicitly requested via URL
      const urlParams = new URLSearchParams(window.location.search);
      const isTestMode = urlParams.get('test_mode') === 'true';
      
      if (isTestMode) {
        const testUserId = urlParams.get('test_user_id') || 'test-user-123';
        this.testAuthBypass = {
          enabled: true,
          userId: testUserId
        };
        
        if (import.meta.env?.DEV) {
          devLog('🧪 Test authentication bypass enabled for user:', testUserId);
        }
      } else {
        this.testAuthBypass = null;
      }
    } else {
      // SECURITY: In production, test authentication bypass is completely disabled
      this.testAuthBypass = null;
      
      // Only log in development mode to avoid production console noise
      if (import.meta.env?.DEV) {
        devLog('🔒 Test authentication bypass disabled in production mode');
      }
    }

    // Clean up expired cache entries periodically
    setInterval(() => this.cleanupCache(), 10 * 60 * 1000); // Every 10 minutes

    // Set up network monitoring
    this.setupNetworkMonitoring();

    // Proactively detect clock skew on initialization
    this.detectClockSkew().catch(error => {
      if (import.meta.env?.DEV) {
        devWarn('Could not perform initial clock skew detection:', error);
      }
    });
  }

  /**
   * Detect and compensate for clock skew between client and server
   */
  private async detectClockSkew(): Promise<void> {
    try {
      const clientTimeBefore = Date.now();
      const response = await fetch(`${this.baseUrl}/time`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        const clientTimeAfter = Date.now();
        const roundTripTime = clientTimeAfter - clientTimeBefore;
        
        // Estimate server time at the moment we made the request
        const estimatedServerTime = data.server_timestamp_ms + (roundTripTime / 2);
        const clientTimeAtRequest = clientTimeBefore + (roundTripTime / 2);
        
        // Calculate clock skew (positive means client is ahead, negative means behind)
        this.clockSkewOffset = clientTimeAtRequest - estimatedServerTime;
        this.clockSkewDetected = true;
        
        if (import.meta.env?.DEV) {
          devLog(`🕐 Clock skew detected: ${this.clockSkewOffset}ms (client ${this.clockSkewOffset > 0 ? 'ahead' : 'behind'})`);
          devLog(`   Round trip time: ${roundTripTime}ms`);
          devLog(`   Server time: ${new Date(data.server_timestamp_ms).toISOString()}`);
          devLog(`   Client time: ${new Date(clientTimeAtRequest).toISOString()}`);
        }
      }
    } catch (error) {
      if (import.meta.env?.DEV) {
        devWarn('⚠️ Could not detect clock skew:', error);
      }
    }
  }

  /**
   * Apply clock skew compensation to token timing
   */
  private async getCompensatedToken(forceRefresh = false): Promise<string> {
    const user = auth.currentUser;
    if (!user) {
      throw new Error('User not authenticated');
    }

    // If we have detected clock skew and client is behind, wait before token generation
    if (this.clockSkewDetected && this.clockSkewOffset < 0) {
      const waitTime = Math.abs(this.clockSkewOffset) + 500; // Add 500ms buffer
      if (import.meta.env?.DEV) {
        devLog(`⏱️ Applying clock skew compensation: waiting ${waitTime}ms before token generation`);
      }
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    const token = await user.getIdToken(forceRefresh);
    
    // Validate token structure
    if (!token || typeof token !== 'string') {
      throw new Error('Authentication token is not a valid string');
    }

    const tokenParts = token.split('.');
    if (tokenParts.length !== 3) {
      throw new Error('Authentication token is not a valid JWT format');
    }

    if (tokenParts.some(part => !part || part.length === 0)) {
      throw new Error('Authentication token has invalid JWT structure');
    }

    return token;
  }

  /**
   * Handle clock skew errors with enhanced detection and compensation
   */
  private async handleClockSkewError(errorData: any): Promise<void> {
    if (errorData.error_type === 'clock_skew' && errorData.server_time_ms) {
      const serverTime = errorData.server_time_ms;
      const clientTime = Date.now();
      const detectedSkew = clientTime - serverTime;
      
      // Update our clock skew offset with the server's measurement
      this.clockSkewOffset = detectedSkew;
      this.clockSkewDetected = true;
      
      if (import.meta.env?.DEV) {
        devLog(`🔄 Updated clock skew from server error: ${detectedSkew}ms`);
        devLog(`   Server reported time: ${new Date(serverTime).toISOString()}`);
        devLog(`   Client time: ${new Date(clientTime).toISOString()}`);
      }
    } else if (!this.clockSkewDetected) {
      // Fallback: detect clock skew if we haven't already
      await this.detectClockSkew();
    }
  }

  /**
   * Set up network monitoring for offline/online detection
   */
  private setupNetworkMonitoring(): void {
    if (typeof window === 'undefined') return;

    window.addEventListener('online', () => {
      if (import.meta.env?.DEV) {
        devLog('🌐 Network connection restored');
      }
      // Clear cache to ensure fresh data when back online
      this.clearCache();
    });

    window.addEventListener('offline', () => {
      if (import.meta.env?.DEV) {
        devLog('🌐 Network connection lost - using cached data where available');
      }
    });
  }

  /**
   * Makes an authenticated API request with enhanced error handling, retry logic, and caching
   */
  private async fetchApi<T = any>(
    path: string,
    options: RequestInit = {},
    retryCount = 0,
    timeout?: number,
    useCache = true
  ): Promise<T> {
    const startTime = performance.now();
    const method = options.method || 'GET';
    const cacheKey = this.getCacheKey(path, options);

    // Check cache for GET requests
    if (method === 'GET' && useCache && retryCount === 0) {
      const cached = this.getFromCache<T>(cacheKey);
      if (cached) {
        if (import.meta.env?.DEV) {
          devLog(`⚡ Cache hit for: ${path}`);
        }
        return cached;
      }
    }

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

      // Get fresh token, forcing refresh on retries and applying clock skew compensation
      const forceRefresh = retryCount > 0;
      try {
        const token = await this.getCompensatedToken(forceRefresh);
        headers = {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        };
      } catch (tokenError) {
        devError('Token retrieval error:', tokenError);
        throw new Error(`Authentication token error: ${tokenError instanceof Error ? tokenError.message : 'Unknown error'}`);
      }
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
      signal: AbortSignal.timeout(timeout || this.defaultTimeout),
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

        // Enhanced retry logic for various error conditions
        if (this.shouldRetry(response.status, errorData, retryCount)) {
          // Handle clock skew errors with enhanced compensation
          if (response.status === 401) {
            await this.handleClockSkewError(errorData);
          }
          
          const delay = this.calculateRetryDelay(retryCount, response.status);

          if (import.meta.env?.DEV) {
            devLog(`🔄 Retrying API call (${retryCount + 1}/${this.maxRetries}) after ${delay}ms delay. Status: ${response.status}`);
          }

          await new Promise(resolve => setTimeout(resolve, delay));
          return this.fetchApi<T>(path, options, retryCount + 1, timeout, useCache);
        }

        const errorMessage = errorData.error || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
        const error: ApiError = new Error(errorMessage);
        error.traceback = errorData.traceback;
        error.status = response.status;
        throw error;
      }

      const data = await response.json();

      // Cache successful GET requests
      if (method === 'GET' && useCache) {
        this.setCache(cacheKey, data);
      }

      if (import.meta.env?.DEV) {
        devLog(`✅ API call completed in ${duration}s:`, path);
      }
      return data;

    } catch (error) {
      // Handle network errors and timeouts with retry logic
      if (this.shouldRetryOnError(error, retryCount)) {
        const delay = this.calculateRetryDelay(retryCount, 0);

        if (import.meta.env?.DEV) {
          devLog(`🔄 Network error, retrying (${retryCount + 1}/${this.maxRetries}) after ${delay}ms delay:`, error);
        }

        await new Promise(resolve => setTimeout(resolve, delay));
        return this.fetchApi<T>(path, options, retryCount + 1, timeout, useCache);
      }

      devError('API call failed:', path, error);
      throw this.enhanceError(error, path);
    }
  }

  /**
   * Cache management methods
   */
  private getCacheKey(path: string, options: RequestInit = {}): string {
    const method = options.method || 'GET';
    const body = options.body || '';
    return `${method}:${path}:${typeof body === 'string' ? body : JSON.stringify(body)}`;
  }

  private getFromCache<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (!cached) return null;

    if (Date.now() - cached.timestamp > cached.ttl) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  private setCache<T>(key: string, data: T, ttl: number = this.cacheDefaultTTL): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  private cleanupCache(): void {
    const now = Date.now();
    for (const [key, cached] of this.cache.entries()) {
      if (now - cached.timestamp > cached.ttl) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Clear all cached data
   */
  public clearCache(): void {
    this.cache.clear();
    if (import.meta.env?.DEV) {
      devLog('🗑️ All API cache cleared');
    }
  }

  /**
   * Clear cache for specific path patterns
   */
  public clearCacheByPath(pathPattern: string): void {
    let cleared = 0;
    for (const [key] of this.cache.entries()) {
      if (key.includes(pathPattern)) {
        this.cache.delete(key);
        cleared++;
      }
    }
    if (import.meta.env?.DEV && cleared > 0) {
      console.log(`🗑️ Cleared ${cleared} cache entries for pattern: ${pathPattern}`);
    }
  }

  /**
   * Get cache statistics for debugging
   */
  public getCacheStats(): { size: number; entries: string[] } {
    return {
      size: this.cache.size,
      entries: Array.from(this.cache.keys())
    };
  }

  /**
   * Determines if a request should be retried based on status code and error data
   */
  private shouldRetry(status: number, errorData: any, retryCount: number): boolean {
    if (retryCount >= this.maxRetries - 1) return false;

    // Retry on server errors (5xx)
    if (status >= 500) {
      if (import.meta.env?.DEV) {
        console.log(`🔄 Retrying server error ${status} (attempt ${retryCount + 1}/${this.maxRetries})`);
      }
      return true;
    }

    // Retry on specific 4xx errors
    if (status === 429) {
      if (import.meta.env?.DEV) {
        console.log(`🔄 Retrying rate limit error (attempt ${retryCount + 1}/${this.maxRetries})`);
      }
      return true; // Rate limiting
    }
    if (status === 408) {
      if (import.meta.env?.DEV) {
        console.log(`🔄 Retrying timeout error (attempt ${retryCount + 1}/${this.maxRetries})`);
      }
      return true; // Request timeout
    }

    // Retry on authentication errors with clock skew or token refresh needed
    if (status === 401) {
      const errorMessage = errorData.error || errorData.message || '';
      const shouldRetryAuth = errorMessage.includes('Token used too early') ||
                              errorMessage.includes('clock') ||
                              errorMessage.includes('time') ||
                              errorMessage.includes('Authentication failed: Token used too early') ||
                              errorMessage.includes('token') ||
                              errorMessage.includes('expired');
      if (shouldRetryAuth && import.meta.env?.DEV) {
        console.log(`🔄 Retrying auth error: ${errorMessage} (attempt ${retryCount + 1}/${this.maxRetries})`);
      }
      return shouldRetryAuth;
    }

    // Retry on specific network-related 400 errors
    if (status === 400 && errorData) {
      const errorMessage = errorData.error || errorData.message || '';
      const shouldRetryBadRequest = errorMessage.includes('network') ||
                                    errorMessage.includes('connection') ||
                                    errorMessage.includes('timeout');
      if (shouldRetryBadRequest && import.meta.env?.DEV) {
        console.log(`🔄 Retrying network-related 400 error: ${errorMessage}`);
      }
      return shouldRetryBadRequest;
    }

    return false;
  }

  /**
   * Determines if a request should be retried based on network error
   */
  private shouldRetryOnError(error: any, retryCount: number): boolean {
    if (retryCount >= this.maxRetries - 1) return false;

    // Retry on network errors
    if (error.name === 'NetworkError') return true;
    if (error.name === 'TimeoutError') return true;
    if (error.message?.includes('fetch')) return true;
    if (error.message?.includes('network')) return true;
    if (error.message?.includes('timeout')) return true;

    return false;
  }

  /**
   * Calculates exponential backoff delay with jitter and clock skew compensation
   */
  private calculateRetryDelay(retryCount: number, status: number): number {
    // Base delay with exponential backoff
    let delay = Math.min(1000 * Math.pow(2, retryCount), 10000);

    // Enhanced handling for clock skew errors
    if (status === 401) {
      // Start with longer base delay for auth errors
      delay = Math.max(2000, (retryCount + 1) * 2000);
      
      // Add additional delay if we've detected significant clock skew
      if (this.clockSkewDetected && Math.abs(this.clockSkewOffset) > 1000) {
        delay += Math.abs(this.clockSkewOffset);
        if (import.meta.env?.DEV) {
          console.log(`⏱️ Adding ${Math.abs(this.clockSkewOffset)}ms delay for clock skew compensation`);
        }
      }
    }

    // Add jitter to prevent thundering herd
    const jitter = Math.random() * 0.3 * delay;
    return Math.floor(delay + jitter);
  }

  /**
   * Enhances error objects with additional context and user-friendly messages
   */
  private enhanceError(error: any, path: string): Error {
    const enhanced = error instanceof Error ? error : new Error(String(error));
    const isOffline = typeof navigator !== 'undefined' && !navigator.onLine;

    if (error.name === 'TimeoutError' || error.name === 'AbortError') {
      enhanced.message = isOffline
        ? 'Connection timeout - you appear to be offline. Please check your internet connection.'
        : 'Request timeout: The server took too long to respond. Please try again.';
    } else if (error.message?.includes('fetch') || error.message?.includes('Failed to fetch')) {
      enhanced.message = isOffline
        ? 'Unable to connect - you appear to be offline. Please check your internet connection.'
        : 'Network error: Please check your internet connection and try again.';
    } else if (error.message?.includes('NetworkError')) {
      enhanced.message = 'Network error occurred. This might be due to connection issues or server problems.';
    } else if (error.message?.includes('CORS')) {
      enhanced.message = 'Security error: Cross-origin request blocked. Please contact support.';
    }

    (enhanced as any).originalError = error;
    (enhanced as any).path = path;
    (enhanced as any).isOffline = isOffline;
    return enhanced;
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
   * Get all campaigns for the current user with caching and validation
   */
  async getCampaigns(): Promise<Campaign[]> {
    const startTime = performance.now();

    try {
      if (import.meta.env?.DEV) {
        console.log('🎯 API: Fetching campaigns for user...');
      }

      const response = await this.fetchApi<Campaign[]>('/campaigns', {}, 0, 15000);

      // Enhanced validation with detailed error reporting
      if (!Array.isArray(response)) {
        const actualType = response === null ? 'null' : typeof response;
        throw new Error(`Invalid campaigns data format: expected array, got ${actualType}`);
      }

      // Validate each campaign object with comprehensive checks
      const validatedCampaigns = response.filter((campaign, index): campaign is Campaign => {
        if (!campaign || typeof campaign !== 'object') {
          console.warn(`Campaign at index ${index} is not an object:`, campaign);
          return false;
        }
        if (!campaign.id || typeof campaign.id !== 'string') {
          console.warn(`Campaign at index ${index} has invalid ID:`, campaign.id);
          return false;
        }
        if (!campaign.title || typeof campaign.title !== 'string') {
          console.warn(`Campaign at index ${index} has invalid title:`, campaign.title);
          return false;
        }
        // Validate optional fields
        if (campaign.created_at && typeof campaign.created_at !== 'string') {
          console.warn(`Campaign ${campaign.id} has invalid created_at:`, campaign.created_at);
        }
        if (campaign.last_played && typeof campaign.last_played !== 'string') {
          console.warn(`Campaign ${campaign.id} has invalid last_played:`, campaign.last_played);
        }
        return true;
      });

      if (validatedCampaigns.length !== response.length) {
        const filteredCount = response.length - validatedCampaigns.length;
        console.warn(`⚠️ Filtered out ${filteredCount} invalid campaigns out of ${response.length} total`);
      }

      const duration = performance.now() - startTime;
      if (import.meta.env?.DEV) {
        console.log(`✅ API: Fetched ${validatedCampaigns.length} campaigns in ${duration.toFixed(2)}ms`);
      }

      return validatedCampaigns;
    } catch (error) {
      const duration = performance.now() - startTime;
      console.error(`❌ API: Failed to get campaigns after ${duration.toFixed(2)}ms:`, error);
      throw this.enhanceError(error, '/campaigns');
    }
  }

  /**
   * Get a specific campaign with full details
   */
  async getCampaign(campaignId: string): Promise<CampaignDetailResponse> {
    const response = await this.fetchApi<CampaignDetailResponse>(`/campaigns/${campaignId}`, {}, 0, 15000);
    return response;
  }

  /**
   * Create a new campaign with extended timeout for AI processing and validation
   */
  async createCampaign(data: CampaignCreateRequest): Promise<string> {
    const startTime = performance.now();

    // Enhanced client-side validation with detailed error messages
    if (!data.title || typeof data.title !== 'string') {
      throw new Error('Campaign title is required and must be a valid string');
    }

    const trimmedTitle = data.title.trim();
    if (trimmedTitle.length === 0) {
      throw new Error('Campaign title cannot be empty or contain only whitespace');
    }

    if (trimmedTitle.length > 100) {
      throw new Error(`Campaign title is too long: ${trimmedTitle.length} characters (max 100)`);
    }

    if (data.prompt && data.prompt.length > MAX_DESCRIPTION_LENGTH) {
      throw new Error(`Campaign prompt is too long: ${data.prompt.length} characters (max ${MAX_DESCRIPTION_LENGTH.toLocaleString()})`);
    }

    // Validate other optional fields
    if (data.character && typeof data.character !== 'string') {
      throw new Error('Character field must be a string if provided');
    }

    if (data.setting && typeof data.setting !== 'string') {
      throw new Error('Setting field must be a string if provided');
    }

    if (data.description && typeof data.description !== 'string') {
      throw new Error('Description field must be a string if provided');
    }

    if (data.selected_prompts && !Array.isArray(data.selected_prompts)) {
      throw new Error('Selected prompts must be an array if provided');
    }

    if (data.custom_options && !Array.isArray(data.custom_options)) {
      throw new Error('Custom options must be an array if provided');
    }

    try {
      if (import.meta.env?.DEV) {
        console.log('🚀 API: Creating campaign:', {
          title: trimmedTitle,
          character: data.character || 'none',
          setting: data.setting || 'none',
          description: data.description ? `${data.description.substring(0, 50)}...` : 'none',
          selectedPrompts: data.selected_prompts?.length || 0,
          customOptions: data.custom_options?.length || 0
        });
      }

      // Clear campaigns cache since we're creating a new one
      this.clearCacheByPath('/campaigns');

      const response = await this.fetchApi<CampaignCreateResponse>('/campaigns', {
        method: 'POST',
        body: JSON.stringify({
          ...data,
          title: trimmedTitle // Use trimmed title
        })
      }, 0, 60000); // 60 second timeout for campaign creation

      // Enhanced response validation
      if (!response || typeof response !== 'object') {
        throw new Error('Invalid response format from server');
      }

      if (!response.success) {
        const errorMsg = (response as ApiResponse).error || 'Unknown server error occurred';
        throw new Error(`Server error: ${errorMsg}`);
      }

      if (!response.campaign_id) {
        throw new Error('Server did not return a campaign ID');
      }

      if (typeof response.campaign_id !== 'string' || response.campaign_id.length === 0) {
        throw new Error('Invalid campaign ID format received from server');
      }

      const duration = performance.now() - startTime;
      if (import.meta.env?.DEV) {
        console.log(`✅ API: Campaign created successfully in ${duration.toFixed(2)}ms, ID: ${response.campaign_id}`);
      }

      return response.campaign_id;
    } catch (error) {
      const duration = performance.now() - startTime;
      console.error(`❌ API: Failed to create campaign after ${duration.toFixed(2)}ms:`, error);
      throw this.enhanceError(error, '/campaigns (POST)');
    }
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
    // BACKEND_LIMITATION: DELETE endpoint not implemented in backend API
    // Tracked in backend roadmap for future implementation
    throw new Error('Delete campaign not implemented in backend');

    // When implemented, it would be:
    // await this.fetchApi(`/campaigns/${campaignId}`, {
    //   method: 'DELETE'
    // });
  }

  /**
   * Send a game interaction (user input) with extended timeout for AI processing
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
      },
      0,
      45000 // 45 second timeout for AI interactions
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
