import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Plus, Calendar, Sword, Shield, Crown, BookOpen, Settings, Play } from 'lucide-react'
import { apiService } from '../services/api.service'
import { useAuth } from '../hooks/useAuth'
import type { Campaign as ApiCampaign } from '../services/api.types'



const themeColors = {
  fantasy: 'bg-gradient-to-br from-green-500/20 to-emerald-600/20 border-green-500/30',
  cyberpunk: 'bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border-cyan-500/30',
  'dark-fantasy': 'bg-gradient-to-br from-purple-500/20 to-red-600/20 border-purple-500/30'
}

const statusColors = {
  active: 'bg-green-500/20 text-green-300 border-green-500/30',
  recruiting: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  completed: 'bg-gray-500/20 text-gray-300 border-gray-500/30'
}

const difficultyIcons = {
  beginner: Shield,
  intermediate: Sword,
  advanced: Crown
}

interface CampaignListProps {
  onPlayCampaign: (campaignId: string) => void
  onCreateCampaign: () => void
  isLoading?: boolean
}

export function CampaignList({ onPlayCampaign, onCreateCampaign, isLoading }: CampaignListProps) {
  const [campaigns, setCampaigns] = useState<ApiCampaign[]>([])
  const [loadingCampaigns, setLoadingCampaigns] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Use Firebase auth state instead of apiService auth
  const { user, loading: authLoading } = useAuth()

  // Load campaigns from API
  useEffect(() => {
    async function loadCampaigns() {
      try {
        setLoadingCampaigns(true)
        setError(null)

        // Check authentication - user must be authenticated to load campaigns
        if (!user) {
          console.log('User not authenticated, skipping campaign load')
          setCampaigns([])
          return
        }

        console.log('Loading campaigns for user:', user.uid)

        // Use real apiService for authenticated requests
        const apiCampaigns = await apiService.getCampaigns()
        setCampaigns(apiCampaigns)
      } catch (err) {
        console.error('Failed to load campaigns:', err)
        let errorMessage = 'Failed to load campaigns. Please try again.'
        if (err instanceof Error) {
          errorMessage = `Failed to load campaigns: ${err.message}`
        }
        setError(errorMessage)
        setCampaigns([])
      } finally {
        setLoadingCampaigns(false)
      }
    }

    // Only load campaigns if auth is not loading
    if (!authLoading) {
      loadCampaigns()
    }
  }, [user, authLoading])

  // Apply campaigns-view body class when component mounts
  useEffect(() => {
    document.body.classList.add('campaigns-view')
    return () => {
      document.body.classList.remove('campaigns-view')
    }
  }, [])

  // Show loading state (either auth loading or campaigns loading)
  if (authLoading || loadingCampaigns) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white text-lg">
            {authLoading ? 'Checking authentication...' : 'Loading campaigns...'}
          </p>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-4">{error}</p>
          <Button onClick={() => window.location.reload()} className="bg-purple-600 hover:bg-purple-700">
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-5xl text-white mb-2">Your Campaigns</h1>
            <p className="text-purple-200 text-lg">Choose your adventure or create a new one</p>
          </div>
          <Button
            size="lg"
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 text-lg"
            onClick={onCreateCampaign}
          >
            <Plus className="w-5 h-5 mr-2" />
            Create V2 Campaign
          </Button>
        </div>

        {/* Campaign Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {campaigns.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-400 text-lg mb-4">No campaigns yet</p>
              <p className="text-gray-500 mb-6">Create your first campaign to start your adventure!</p>
              <Button onClick={onCreateCampaign} className="bg-purple-600 hover:bg-purple-700">
                <Plus className="h-5 w-5 mr-2" />
                Create Campaign
              </Button>
            </div>
          ) : (
            campaigns.map((campaign) => {
              // Use real campaign data or fallback values
              const theme = campaign.theme || 'fantasy'
              const difficulty = campaign.difficulty || 'intermediate'
              const status = campaign.status || 'active'

              // Type-safe icon and color lookups
              const isValidDifficulty = difficulty in difficultyIcons
              const DifficultyIcon = isValidDifficulty ? difficultyIcons[difficulty as keyof typeof difficultyIcons] : difficultyIcons['intermediate']

              const isValidTheme = theme in themeColors
              const themeClass = isValidTheme ? themeColors[theme as keyof typeof themeColors] : themeColors['fantasy']

              const isValidStatus = status in statusColors
              const statusClass = isValidStatus ? statusColors[status as keyof typeof statusColors] : statusColors['active']

              return (
                <Card
                  key={campaign.id}
                  className={`bg-black/60 backdrop-blur-sm border hover:bg-black/70 transition-all duration-300 hover:scale-105 ${themeClass}`}
                >
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start mb-2">
                      <CardTitle className="text-white text-2xl">{campaign.title}</CardTitle>
                      <Badge className={`${statusClass} capitalize`}>
                        {status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-base text-purple-200">
                      <DifficultyIcon className="w-4 h-4" />
                      <span className="capitalize">{difficulty}</span>
                      <span className="text-purple-300/50">•</span>
                      <span className="capitalize">{theme.replace('-', ' ')}</span>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <p className="text-purple-100 text-base leading-relaxed line-clamp-3">
                      {campaign.prompt || 'Loading campaign details...'}
                    </p>

                    <div className="flex justify-between items-center text-base">
                      <div className="flex items-center gap-2 text-purple-200">
                        <Calendar className="w-4 h-4" />
                        <span>
                          Created: {campaign.created_at && !isNaN(new Date(campaign.created_at).getTime())
                            ? new Date(campaign.created_at).toLocaleDateString()
                            : 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-purple-200">
                        <Calendar className="w-4 h-4" />
                        <span>
                          Last played: {campaign.last_played && !isNaN(new Date(campaign.last_played).getTime())
                            ? new Date(campaign.last_played).toLocaleDateString()
                            : 'N/A'}
                        </span>
                      </div>
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button
                        variant="default"
                        size="sm"
                        className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
                        onClick={() => onPlayCampaign(campaign.id)}
                        disabled={isLoading}
                      >
                        <Play className="w-4 h-4 mr-2" />
                        {isLoading ? 'Loading...' : 'Continue'}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-purple-500/30 text-purple-200 hover:bg-purple-500/20"
                      >
                        <Settings className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })
          )}

          {/* Create New Campaign Card */}
          <Card
            className="bg-black/40 backdrop-blur-sm border-dashed border-purple-500/50 hover:border-purple-400/70 hover:bg-black/50 transition-all duration-300 flex items-center justify-center min-h-[300px] cursor-pointer group"
            onClick={onCreateCampaign}
          >
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-purple-600/20 rounded-full flex items-center justify-center group-hover:bg-purple-600/30 transition-colors">
                <Plus className="w-8 h-8 text-purple-300" />
              </div>
              <h3 className="text-white text-2xl mb-2">Start V2 Adventure</h3>
              <p className="text-purple-200 text-base">Enhanced campaign creation with real data integration</p>
            </div>
          </Card>
        </div>

      </div>
    </div>
  )
}
