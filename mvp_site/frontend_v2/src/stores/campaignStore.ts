import { create } from 'zustand';
import { apiService } from '../services/api.service';
import type {
  Campaign,
  CampaignCreateRequest,
  CampaignUpdateRequest
} from '../services/api.types';

interface CampaignState {
  // State
  campaigns: Campaign[];
  selectedCampaign: Campaign | null;
  selectedCampaignId: string | null;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  error: string | null;

  // Actions
  fetchCampaigns: () => Promise<void>;
  fetchCampaignById: (id: string) => Promise<void>;
  createCampaign: (data: CampaignCreateRequest) => Promise<string>;
  updateCampaign: (id: string, data: CampaignUpdateRequest) => Promise<void>;
  deleteCampaign: (id: string) => Promise<void>;
  selectCampaign: (campaign: Campaign | null) => void;
  clearError: () => void;
}

export const useCampaignStore = create<CampaignState>((set, get) => ({
  // Initial state
  campaigns: [],
  selectedCampaign: null,
  selectedCampaignId: null,
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isDeleting: false,
  error: null,

  // Fetch all campaigns
  fetchCampaigns: async () => {
    set({ isLoading: true, error: null });
    try {
      const campaigns = await apiService.getCampaigns();
      set({
        campaigns,
        isLoading: false
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch campaigns',
        isLoading: false
      });
      throw error;
    }
  },

  // Fetch single campaign by ID
  fetchCampaignById: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.getCampaign(id);
      const campaign = response.campaign;

      set({
        selectedCampaign: campaign,
        selectedCampaignId: id,
        isLoading: false
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch campaign',
        isLoading: false
      });
      throw error;
    }
  },

  // Create new campaign
  createCampaign: async (data: CampaignCreateRequest) => {
    set({ isCreating: true, error: null });
    try {
      const campaignId = await apiService.createCampaign(data);

      // Refresh campaigns list
      await get().fetchCampaigns();

      set({ isCreating: false });
      return campaignId;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to create campaign',
        isCreating: false
      });
      throw error;
    }
  },

  // Update campaign
  updateCampaign: async (id: string, data: CampaignUpdateRequest) => {
    set({ isUpdating: true, error: null });
    try {
      await apiService.updateCampaign(id, data);

      // Refresh campaigns list
      await get().fetchCampaigns();

      // Update selected campaign if it's the one being updated
      if (get().selectedCampaignId === id) {
        await get().fetchCampaignById(id);
      }

      set({ isUpdating: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to update campaign',
        isUpdating: false
      });
      throw error;
    }
  },

  // Delete campaign
  deleteCampaign: async (id: string) => {
    set({ isDeleting: true, error: null });
    try {
      await apiService.deleteCampaign(id);

      // Update local state
      set(state => ({
        campaigns: state.campaigns.filter(campaign => campaign.id !== id),
        selectedCampaign: state.selectedCampaign?.id === id ? null : state.selectedCampaign,
        selectedCampaignId: state.selectedCampaignId === id ? null : state.selectedCampaignId,
        isDeleting: false
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to delete campaign',
        isDeleting: false
      });
      throw error;
    }
  },

  // Select a campaign
  selectCampaign: (campaign: Campaign | null) => {
    set({
      selectedCampaign: campaign,
      selectedCampaignId: campaign?.id || null
    });
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },
}));
