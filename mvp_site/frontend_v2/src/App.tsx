import { useState } from 'react'
import { backgroundImage1 } from './assets/figma-assets'
import { Button } from './components/ui/button'
import { Header } from './components/Header'
import { FeatureCards } from './components/FeatureCards'
import { CampaignList } from './components/CampaignList'
import { GamePlayView } from './components/GamePlayView'
import { CampaignCreationV2 } from './components/CampaignCreationV2'
import { MockModeToggle } from './components/MockModeToggle'
import { handleAsyncError, showSuccessToast, logError } from './utils/errorHandling'

// Types for V2 Campaign System
export interface Campaign {
  id: string
  title: string
  description: string
  createdAt: string
  lastPlayed: string
  storyLength: number
}

export type Theme = 'light' | 'dark' | 'fantasy' | 'dark-fantasy' | 'cyberpunk'

export default function App() {
  const [currentView, setCurrentView] = useState<'landing' | 'campaigns' | 'gameplay' | 'create-campaign-v2'>('landing')
  const [selectedCampaign, setSelectedCampaign] = useState<string>('The Dragon\'s Hoard')
  const [theme] = useState<Theme>('fantasy')
  const [isCreatingCampaign, setIsCreatingCampaign] = useState(false)
  const [isLoadingCampaign, setIsLoadingCampaign] = useState(false)

  if (currentView === 'campaigns') {
    return <CampaignList
      onPlayCampaign={async (campaignTitle) => {
        setIsLoadingCampaign(true);
        const result = await handleAsyncError(
          async () => {
            setSelectedCampaign(campaignTitle);
            // Add any async operations here if needed
            return true;
          },
          {
            context: 'LoadCampaign',
            fallbackMessage: 'Failed to load campaign. Please try again.'
          }
        );

        setIsLoadingCampaign(false);

        if (result) {
          setCurrentView('gameplay');
        }
      }}
      onCreateCampaign={() => setCurrentView('create-campaign-v2')}
      isLoading={isLoadingCampaign}
    />
  }

  if (currentView === 'create-campaign-v2') {
    return <CampaignCreationV2
      onCreateCampaign={async (campaign) => {
        setIsCreatingCampaign(true);
        const result = await handleAsyncError(
          async () => {
            // TODO: Call actual API service here
            // const createdCampaign = await apiService.createCampaign(campaign);

            // Simulate API call for now
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Remove console.log for production
            if (import.meta.env?.DEV) {
              console.log('Campaign created (mock):', campaign);
            }

            return campaign;
          },
          {
            context: 'CampaignCreation',
            fallbackMessage: 'Failed to create campaign. Please try again.',
            showToast: true
          }
        );

        setIsCreatingCampaign(false);

        if (result) {
          showSuccessToast('Campaign created successfully!');
          setCurrentView('campaigns');
        }
      }}
      onBack={() => setCurrentView('campaigns')}
      theme={theme}
      isCreating={isCreatingCampaign}
    />
  }

  if (currentView === 'gameplay') {
    return <GamePlayView
      campaignTitle={selectedCampaign}
      onBack={() => setCurrentView('campaigns')}
    />
  }

  return (
    <div className="min-h-screen">
      {/* Background Section */}
      <div className="relative min-h-screen">
        {/* Fantasy Background Image */}
        <div
          className="absolute inset-0 bg-center bg-cover md:bg-center"
          style={{
            backgroundImage: `url(${backgroundImage1})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center center'
          }}
        />

        {/* Light Purple Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-600/40 via-purple-500/35 to-indigo-600/40" />

        {/* Content over background */}
        <div className="relative z-10 min-h-screen flex flex-col">
          <Header />

          {/* Main Content - Upper portion */}
          <main className="flex-1 flex flex-col items-center justify-start px-4 sm:px-6 pt-4 sm:pt-8 md:pt-8 pb-8 sm:pb-12">
            <div className="text-center max-w-4xl mx-auto">
              {/* Welcome Section */}
              <div className="mb-8 sm:mb-12 md:mb-16">
                <h1 className="text-3xl sm:text-4xl md:text-6xl lg:text-7xl text-white mb-4 sm:mb-6 leading-tight">
                  Welcome, Adventurer
                </h1>
                <p className="text-sm sm:text-lg md:text-xl text-purple-200 mb-8 sm:mb-12 max-w-2xl mx-auto leading-relaxed px-2 md:px-0">
                  Every hero's journey begins with a single step. Create your campaign and let the AI Game Master guide you through an unforgettable adventure.
                </p>
              </div>

              {/* Forge Your Legend Section */}
              <div className="mb-8 sm:mb-12 md:mb-16">
                <h2 className="text-2xl sm:text-3xl md:text-5xl text-white mb-6 sm:mb-8 leading-tight">
                  Forge Your Legend
                </h2>
                <Button
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-12 py-6 text-3xl rounded-xl shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105"
                  onClick={() => setCurrentView('campaigns')}
                >
                  <span className="hidden sm:inline">✨ Create Your First Campaign ✨</span>
                  <span className="sm:hidden">✨ Start Adventure ✨</span>
                </Button>
              </div>
            </div>
          </main>

          {/* Bottom section for Feature Cards */}
          <div className="flex-shrink-0 px-4 sm:px-6 pb-6 md:h-48 md:flex md:items-center md:justify-center">
            <FeatureCards />
          </div>
        </div>
      </div>

      {/* Mock Mode Toggle - Only in development */}
      <MockModeToggle />
    </div>
  )
}
