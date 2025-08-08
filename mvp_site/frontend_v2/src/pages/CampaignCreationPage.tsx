import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CampaignCreationV2 } from '../components/CampaignCreationV2'
import { handleAsyncError, showSuccessToast } from '../utils/errorHandling'
import { apiService } from '../services'
import { campaignService } from '../services'
import type { CampaignCreateRequest } from '../services/api.types'
import type { Theme } from '../types'

export function CampaignCreationPage() {
  const navigate = useNavigate()
  const [isCreatingCampaign, setIsCreatingCampaign] = useState(false)
  const [theme] = useState<Theme>('fantasy')

  const handleCreateCampaign = async (campaign: {
    title: string;
    type?: 'dragon-knight' | 'custom';
    character?: string;
    setting?: string;
    description?: string;
    aiPersonalities?: {
      defaultWorld: boolean;
      mechanicalPrecision: boolean;
      companions: boolean;
    };
  }) => {
    setIsCreatingCampaign(true)
    const result = await handleAsyncError(
      async () => {
        // Convert campaign data to API request format with proper mapping
        const apiRequest: CampaignCreateRequest = {
          title: campaign.title,
          character: campaign.character || undefined,
          setting: campaign.setting || undefined,
          description: campaign.description || undefined,
          // Map aiPersonalities boolean flags to API selected_prompts format
          selected_prompts: campaign.aiPersonalities ? Object.entries(campaign.aiPersonalities)
            .filter(([_, enabled]) => enabled)
            .map(([key, _]) => {
              switch (key) {
                case 'defaultWorld': return 'narrative'
                case 'mechanicalPrecision': return 'mechanics'
                case 'companions': return 'companions'
                default: return key
              }
            }) : undefined,
          // Add campaign type as custom option for backend processing
          custom_options: campaign.type ? [campaign.type] : undefined
        }

        // Call actual API service
        const campaignId = await campaignService.createCampaign(apiRequest)

        // Remove console.log for production
        if (import.meta.env?.DEV) {
          console.log('Campaign created successfully with ID:', campaignId)
        }

        return { ...campaign, id: campaignId }
      },
      {
        context: 'CampaignCreation',
        fallbackMessage: 'Failed to create campaign. Please try again.',
        showToast: true
      }
    )

    setIsCreatingCampaign(false)

    if (result) {
      showSuccessToast('Campaign created successfully!')
      // Navigate directly to the new campaign page
      navigate(`/campaigns/${result.id}`)
    }
  }

  const handleBack = () => {
    navigate('/campaigns')
  }

  return (
    <CampaignCreationV2
      onCreateCampaign={handleCreateCampaign}
      onBack={handleBack}
      theme={theme}
      isCreating={isCreatingCampaign}
    />
  )
}
