import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { GamePlayView } from '../components/GamePlayView'
import { apiService } from '../services'
import { handleAsyncError } from '../utils/errorHandling'

export function CampaignPage() {
  const { campaignId } = useParams<{ campaignId: string }>()
  const navigate = useNavigate()
  const [campaignTitle, setCampaignTitle] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!campaignId) {
      navigate('/campaigns')
      return
    }

    // Load campaign details
    const loadCampaign = async () => {
      setIsLoading(true)
      const result = await handleAsyncError(
        async () => {
          const campaignDetails = await apiService.getCampaign(campaignId!)
          console.log('🎯 FRONTEND RECEIVED campaign details:', campaignDetails)
          console.log('🎯 FRONTEND campaign object:', campaignDetails.campaign)
          console.log('🎯 FRONTEND direct title:', campaignDetails.title)
          console.log('🎯 FRONTEND campaign.title:', campaignDetails.campaign?.title)
          
          const extractedTitle = campaignDetails.title || campaignDetails.campaign?.title
          console.log('🎯 FRONTEND extracted title:', extractedTitle)
          
          return {
            title: extractedTitle
          }
        },
        {
          context: 'LoadCampaign',
          fallbackMessage: 'Failed to load campaign'
        }
      )

      if (result) {
        console.log('🎯 FRONTEND setting campaignTitle to:', result.title)
        setCampaignTitle(result.title)
      }
      setIsLoading(false)
    }

    loadCampaign()
  }, [campaignId, navigate])

  const handleBack = () => {
    navigate('/campaigns')
  }


  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-purple-50 to-indigo-100 flex items-center justify-center">
        <div className="text-purple-700">Loading campaign...</div>
      </div>
    )
  }

  if (!campaignId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-purple-50 to-indigo-100 flex items-center justify-center">
        <div className="text-red-700">Invalid campaign ID</div>
      </div>
    )
  }

  return (
    <GamePlayView
      campaignTitle={campaignTitle}
      campaignId={campaignId}
      onBack={handleBack}
    />
  )
}
