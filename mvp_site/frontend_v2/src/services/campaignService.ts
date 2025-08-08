/**
 * Campaign Service - Data transformation layer for campaign API
 * 
 * Handles data format mapping between backend API responses and frontend types,
 * transforming raw API data into the format expected by frontend components.
 */

import { apiService } from './api.service';
import type { Campaign } from './api.types';

/**
 * Raw campaign data format from backend API
 */
interface RawCampaign {
  id: string;
  title: string;
  initial_prompt: string; // API returns 'initial_prompt', frontend expects 'prompt'
  created_at: string; // ISO format: "2025-08-07T04:45:14.987866+00:00"
  last_played: string; // ISO format: "2025-08-07T04:45:15.692586+00:00"
  user_id?: string;
  selected_prompts?: string[];
  use_default_world?: boolean;
}

/**
 * Transform raw API campaign data to frontend format
 */
function transformCampaign(rawCampaign: RawCampaign): Campaign {
  return {
    id: rawCampaign.id,
    title: rawCampaign.title,
    prompt: rawCampaign.initial_prompt, // Map initial_prompt -> prompt
    created_at: rawCampaign.created_at,
    last_played: rawCampaign.last_played,
    user_id: rawCampaign.user_id || '',
    selected_prompts: rawCampaign.selected_prompts || [],
    use_default_world: rawCampaign.use_default_world || false,
    // Add default values for optional UI fields
    theme: 'fantasy',
    difficulty: 'intermediate', 
    status: 'active'
  };
}

/**
 * Format ISO date string to human-readable format
 */
function formatDate(isoString: string): string {
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) {
      return 'N/A';
    }
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch (error) {
    console.warn('Error formatting date:', isoString, error);
    return 'N/A';
  }
}

// ---- Runtime validation helpers ----
function isObjectLike(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object';
}

function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isRawCampaign(value: unknown): value is RawCampaign {
  if (!isObjectLike(value)) return false;
  const v = value as Record<string, unknown>;
  return isString(v.id) && isString(v.title) && isString(v.initial_prompt);
}

function isCampaign(value: unknown): value is Campaign {
  if (!isObjectLike(value)) return false;
  const v = value as Record<string, unknown>;
  return isString(v.id) && isString(v.title) && isString(v.prompt);
}

function applyCampaignDefaults(campaign: Campaign): Campaign {
  return {
    ...campaign,
    theme: campaign.theme ?? 'fantasy',
    difficulty: campaign.difficulty ?? 'intermediate',
    status: campaign.status ?? 'active'
  };
}

function normalizeCampaignRecord(record: unknown): Campaign | null {
  if (isRawCampaign(record)) {
    return transformCampaign(record);
  }
  if (isCampaign(record)) {
    return applyCampaignDefaults(record);
  }
  return null;
}

/**
 * Campaign Service - Enhanced wrapper around API service with data transformation
 */
class CampaignService {
  /**
   * Get all campaigns with proper data transformation
   */
  async getCampaigns(): Promise<Campaign[]> {
    const startTime = performance.now();
    
    try {
      if (import.meta.env?.DEV) {
        console.log('🎯 CampaignService: Fetching and transforming campaigns...');
      }

      // Get data from API service and normalize safely
      const apiResult = await apiService.getCampaigns();

      const transformedCampaigns = (Array.isArray(apiResult) ? apiResult : [])
        .map(normalizeCampaignRecord)
        .filter((c): c is Campaign => Boolean(c));
      
      const duration = performance.now() - startTime;
      if (import.meta.env?.DEV) {
        console.log(`✅ CampaignService: Transformed ${transformedCampaigns.length} campaigns in ${duration.toFixed(2)}ms`);
        console.log('Sample transformed campaign:', transformedCampaigns[0]);
      }
      
      return transformedCampaigns;
    } catch (error) {
      const duration = performance.now() - startTime;
      console.error(`❌ CampaignService: Failed to get campaigns after ${duration.toFixed(2)}ms:`, error);
      throw error;
    }
  }

  /**
   * Get campaigns with formatted dates for display
   */
  async getCampaignsForDisplay(): Promise<Campaign[]> {
    const campaigns = await this.getCampaigns();
    
    return campaigns.map(campaign => ({
      ...campaign,
      created_at: formatDate(campaign.created_at),
      last_played: formatDate(campaign.last_played)
    }));
  }

  /**
   * Create a new campaign (delegated to API service)
   */
  async createCampaign(data: {
    title: string;
    character?: string;
    setting?: string;
    description?: string;
    selected_prompts?: string[];
    custom_options?: string[];
  }): Promise<string> {
    return apiService.createCampaign(data);
  }

  /**
   * Get campaign details (delegated to API service)
   */
  async getCampaign(campaignId: string) {
    return apiService.getCampaign(campaignId);
  }

  /**
   * Update campaign (delegated to API service)
   */
  async updateCampaign(campaignId: string, data: {title: string}): Promise<void> {
    return apiService.updateCampaign(campaignId, data);
  }

  /**
   * Delete campaign (delegated to API service)
   */
  async deleteCampaign(campaignId: string): Promise<void> {
    return apiService.deleteCampaign(campaignId);
  }

  /**
   * Clear campaigns cache (delegated to API service)
   */
  clearCache(): void {
    apiService.clearCacheByPath('/campaigns');
  }
}

// Export singleton instance
export const campaignService = new CampaignService();

// Export utility functions for testing
export { transformCampaign, formatDate };
export type { RawCampaign };