import { useState } from 'react'
import backgroundImage from 'figma:asset/7388009b8bbea20b44923143edf5bb1c4c93e240.png'
import { Button } from './components/ui/button'
import { Header } from './components/Header'
import { FeatureCards } from './components/FeatureCards'
import { CampaignList } from './components/CampaignList'
import { GamePlayView } from './components/GamePlayView'
import { CampaignWizard } from './components/CampaignWizard'

interface CampaignData {
  title: string
  type: 'dragon-knight' | 'custom'
  character: string
  setting: string
  description: string
  aiPersonalities: {
    defaultWorld: boolean
    mechanicalPrecision: boolean
    companions: boolean
  }
}

export default function App() {
  const [currentView, setCurrentView] = useState<'landing' | 'campaigns' | 'wizard' | 'gameplay'>('landing')
  const [selectedCampaign, setSelectedCampaign] = useState<string>('The Dragon\'s Hoard')

  // Override global body background with lighter purple theme
  document.body.style.background = 'linear-gradient(135deg, rgb(147 51 234), rgb(126 34 206), rgb(79 70 229))'

  if (currentView === 'campaigns') {
    return <CampaignList
      onPlayCampaign={(campaignTitle) => {
        setSelectedCampaign(campaignTitle)
        setCurrentView('gameplay')
      }}
      onCreateCampaign={() => setCurrentView('wizard')}
    />
  }

  if (currentView === 'wizard') {
    return <CampaignWizard
      onBack={() => setCurrentView('campaigns')}
      onComplete={(campaignData: CampaignData) => {
        setSelectedCampaign(campaignData.title)
        setCurrentView('gameplay')
      }}
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
            backgroundImage: `url(${backgroundImage})`,
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
                  size="lg"
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 sm:px-12 md:px-16 py-4 sm:py-5 md:py-6 text-base sm:text-lg md:text-xl rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 w-full sm:w-auto"
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
    </div>
  )
}
