import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CampaignList } from '../components/CampaignList'

export function CampaignListPage() {
  const navigate = useNavigate()
  const [isLoadingCampaign, setIsLoadingCampaign] = useState(false)

  const handlePlayCampaign = async (campaignId: string) => {
    setIsLoadingCampaign(true)
    try {
      // Navigate to the specific campaign page
      navigate(`/campaigns/${campaignId}`)
    } finally {
      // Reset loading state after navigation
      setIsLoadingCampaign(false)
    }
  }

  const handleCreateCampaign = () => {
    navigate('/campaigns/create')
  }

  return (
    <CampaignList
      onPlayCampaign={handlePlayCampaign}
      onCreateCampaign={handleCreateCampaign}
      isLoading={isLoadingCampaign}
    />
  )
}
