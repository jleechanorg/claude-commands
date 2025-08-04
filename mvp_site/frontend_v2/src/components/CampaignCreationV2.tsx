import { useState } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Card, CardContent } from './ui/card'
import { Badge } from './ui/badge'
import { Checkbox } from './ui/checkbox'
import { ArrowLeft, ChevronDown, ChevronUp, Sparkles, Users, Settings, Globe } from 'lucide-react'

import type { Campaign, Theme } from '../App'

interface CampaignCreationV2Props {
  onCreateCampaign: (campaign: Omit<Campaign, 'id' | 'createdAt' | 'lastPlayed' | 'storyLength'> & {
    character?: string;
    setting?: string;
    aiPersonalities?: {
      defaultWorld: boolean;
      mechanicalPrecision: boolean;
      companions: boolean;
    };
  }) => void
  onBack: () => void
  theme: Theme
  isCreating?: boolean
}

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

export function CampaignCreationV2({ onCreateCampaign, onBack, isCreating }: CampaignCreationV2Props) {
  const [currentStep, setCurrentStep] = useState(1)
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false)

  // Default values for each campaign type
  const dragonKnightDefaults = {
    character: '',  // Remove hardcoded character name
    setting: 'World of Assiah. Caught between an oath to a ruthless tyrant who enforces a prosperous peace and the call of a chaotic dragon promising true freedom, a young knight must decide whether to slaughter innocents to preserve order or start a war to reclaim the world\'s soul.'
  }

  const customDefaults = {
    character: '',
    setting: ''
  }

  // Store user's custom values separately
  const [savedCustomValues, setSavedCustomValues] = useState({
    character: '',
    setting: ''
  })

  const [campaignData, setCampaignData] = useState<CampaignData>({
    title: 'My Epic Adventure',
    type: 'dragon-knight',
    character: dragonKnightDefaults.character,
    setting: dragonKnightDefaults.setting,
    description: '',
    aiPersonalities: {
      defaultWorld: true,
      mechanicalPrecision: true,
      companions: true
    }
  })

  const handleNext = () => {
    // Validate current step before proceeding
    if (!validateCurrentStep()) {
      return
    }

    if (currentStep < 3) {
      setCurrentStep(currentStep + 1)
    } else {
      handleCampaignCreation()
    }
  }

  const validateCurrentStep = (): boolean => {
    switch (currentStep) {
      case 1:
        return campaignData.title.trim().length > 0
      case 2:
        return Object.values(campaignData.aiPersonalities).some(Boolean)
      default:
        return true
    }
  }

  const handleCampaignCreation = async () => {
    try {
      // Convert to Campaign format with additional data
      const campaign = {
        title: campaignData.title,
        description: campaignData.type === 'dragon-knight'
          ? 'Embark on an epic journey as a knight in the world of Assiah'
          : `A custom adventure: ${campaignData.setting}`,
        character: campaignData.character,
        setting: campaignData.setting,
        aiPersonalities: campaignData.aiPersonalities
      }
      onCreateCampaign(campaign)
    } catch (error) {
      console.error('Failed to create campaign:', error)
      // TODO: Show error toast to user
    }
  }

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const updateCampaignData = (field: keyof CampaignData, value: any) => {
    setCampaignData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const updateAIPersonality = (field: keyof CampaignData['aiPersonalities'], value: boolean) => {
    setCampaignData(prev => ({
      ...prev,
      aiPersonalities: {
        ...prev.aiPersonalities,
        [field]: value
      }
    }))
  }

  const renderProgressStepper = () => (
    <div className="flex items-center justify-center mb-8">
      <div className="flex items-center space-x-4 md:space-x-8">
        {/* Step 1 */}
        <div className="flex items-center space-x-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            currentStep >= 1
              ? 'bg-purple-600 text-white'
              : 'bg-gray-600 text-gray-300'
          }`}>
            {currentStep > 1 ? '✓' : '1'}
          </div>
          <span className={`text-base ${
            currentStep >= 1 ? 'text-purple-300' : 'text-gray-400'
          }`}>
            Basics
          </span>
        </div>

        {/* Progress Line 1 */}
        <div className={`w-12 md:w-24 h-1 ${
          currentStep >= 2 ? 'bg-purple-600' : 'bg-gray-600'
        }`} />

        {/* Step 2 */}
        <div className="flex items-center space-x-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            currentStep >= 2
              ? 'bg-purple-600 text-white'
              : 'bg-gray-600 text-gray-300'
          }`}>
            {currentStep > 2 ? '✓' : '2'}
          </div>
          <span className={`text-base ${
            currentStep >= 2 ? 'text-purple-300' : 'text-gray-400'
          }`}>
            AI Style
          </span>
        </div>

        {/* Progress Line 2 */}
        <div className={`w-12 md:w-24 h-1 ${
          currentStep >= 3 ? 'bg-purple-600' : 'bg-gray-600'
        }`} />

        {/* Step 3 */}
        <div className="flex items-center space-x-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            currentStep >= 3
              ? 'bg-purple-600 text-white'
              : 'bg-gray-600 text-gray-300'
          }`}>
            3
          </div>
          <span className={`text-base ${
            currentStep >= 3 ? 'text-purple-300' : 'text-gray-400'
          }`}>
            Launch
          </span>
        </div>
      </div>
    </div>
  )

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="flex items-center space-x-3 mb-6">
        <div className="text-2xl">🏰</div>
        <div>
          <h2 className="text-3xl text-white mb-2">Campaign Basics</h2>
          <p className="text-purple-200 text-lg">Let's start with the fundamentals of your adventure.</p>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-purple-200 mb-2 text-lg">
            Campaign Title <span className="text-purple-300">(Pick anything!)</span>
          </label>
          <Input
            value={campaignData.title}
            onChange={(e) => updateCampaignData('title', e.target.value)}
            className="bg-black/40 border-purple-500/30 text-white placeholder-purple-300/50 focus:border-purple-400 focus:ring-purple-400 text-lg md:text-xl"
            placeholder="My Epic Adventure"
          />
          <p className="text-base text-purple-300 mt-1">
            This helps you identify your campaign in the dashboard.
          </p>
        </div>

        <div>
          <label className="block text-purple-200 mb-3 text-lg">Campaign Type</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card
              className={`cursor-pointer transition-all duration-200 bg-black/50 backdrop-blur-md border border-purple-300/30 hover:border-purple-200/50 hover:bg-black/40 ${
                campaignData.type === 'dragon-knight'
                  ? 'border-purple-400 border-2 bg-gradient-to-br from-purple-500/20 to-pink-600/20'
                  : 'border-purple-500/30 hover:border-purple-400/50'
              }`}
              onClick={() => {
                // Save current custom values if switching from custom
                if (campaignData.type === 'custom') {
                  setSavedCustomValues({
                    character: campaignData.character,
                    setting: campaignData.setting
                  })
                }
                updateCampaignData('type', 'dragon-knight')
                updateCampaignData('character', dragonKnightDefaults.character)
                updateCampaignData('setting', dragonKnightDefaults.setting)
              }}
            >
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <div className="text-2xl">🐉</div>
                  <div className="flex-1">
                    <h3 className="text-white mb-1 text-lg">Dragon Knight Campaign</h3>
                    <p className="text-base text-purple-200">
                      Play as a knight in a morally complex world. Perfect for new players!
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card
              className={`cursor-pointer transition-all duration-200 bg-black/50 backdrop-blur-md border border-purple-300/30 hover:border-purple-200/50 hover:bg-black/40 ${
                campaignData.type === 'custom'
                  ? 'border-purple-400 border-2 bg-gradient-to-br from-purple-500/20 to-pink-600/20'
                  : 'border-purple-500/30 hover:border-purple-400/50'
              }`}
              onClick={() => {
                updateCampaignData('type', 'custom')
                // Restore saved custom values if they exist, otherwise use defaults
                updateCampaignData('character', savedCustomValues.character || customDefaults.character)
                updateCampaignData('setting', savedCustomValues.setting || customDefaults.setting)
              }}
            >
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <div className="text-2xl">✨</div>
                  <div className="flex-1">
                    <h3 className="text-white mb-1 text-lg">Custom Campaign</h3>
                    <p className="text-base text-purple-200">
                      Create your own unique world and story from scratch.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div>
          <label className="block text-purple-200 mb-2 text-lg">Character you want to play</label>
          <Input
            value={campaignData.character}
            onChange={(e) => updateCampaignData('character', e.target.value)}
            className="bg-black/40 border-purple-500/30 text-white placeholder-purple-300/50 focus:border-purple-400 focus:ring-purple-400 text-lg md:text-xl"
            placeholder={campaignData.type === 'dragon-knight' ? 'Knight of Assiah' : 'Your character name'}
          />
          <p className="text-base text-purple-300 mt-1">
            Leave blank for a randomly generated character
          </p>
        </div>

        <div>
          <label className="block text-purple-200 mb-2 text-lg">Setting/world for your adventure</label>
          <Textarea
            value={campaignData.setting}
            onChange={(e) => updateCampaignData('setting', e.target.value)}
            className="bg-black/40 border-purple-500/30 text-white placeholder-purple-300/50 focus:border-purple-400 focus:ring-purple-400 min-h-[120px] text-lg md:text-xl"
            placeholder="Describe the world where your adventure takes place..."
          />
          <p className="text-base text-purple-300 mt-1">
            Leave blank for a randomly generated world
          </p>
        </div>

        <div>
          <Button
            variant="ghost"
            onClick={() => setIsDescriptionExpanded(!isDescriptionExpanded)}
            className="text-purple-300 hover:text-white hover:bg-purple-500/20 p-0 h-auto text-lg"
            aria-expanded={isDescriptionExpanded}
            aria-controls="campaign-description-content"
          >
            Campaign description prompt
            {isDescriptionExpanded ?
              <ChevronUp className="w-4 h-4 ml-2" /> :
              <ChevronDown className="w-4 h-4 ml-2" />
            }
          </Button>

          {isDescriptionExpanded && (
            <div className="mt-3" id="campaign-description-content">
              <Textarea
                value={campaignData.description}
                onChange={(e) => updateCampaignData('description', e.target.value)}
                className="bg-black/40 border-purple-500/30 text-white placeholder-purple-300/50 focus:border-purple-400 focus:ring-purple-400 min-h-[100px] text-lg md:text-xl"
                placeholder="Additional details about your campaign..."
                aria-describedby="description-help"
              />
              <p id="description-help" className="text-sm text-purple-300 mt-1">
                Optional: Provide additional context for your campaign world
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="flex items-center space-x-3 mb-6">
        <div className="text-2xl">🤖</div>
        <div>
          <h2 className="text-3xl text-white mb-2">Choose Your AI's Expertise</h2>
          <p className="text-purple-200 text-lg">Select which aspects of storytelling you want enhanced.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Default Fantasy World */}
        <Card className={`bg-black/50 backdrop-blur-md border border-purple-300/30 transition-all duration-200 hover:border-purple-200/50 hover:bg-black/40 ${
          campaignData.aiPersonalities.defaultWorld
            ? 'border-cyan-400/50 bg-gradient-to-br from-cyan-500/20 to-blue-600/20'
            : 'border-purple-500/30 hover:border-purple-400/50'
        }`}>
          <CardContent className="p-6 text-center">
            <div className="flex justify-center mb-4">
              <Globe className="w-12 h-12 text-cyan-400" />
            </div>
            <h3 className="text-white mb-3 text-xl">Default Fantasy World</h3>
            <p className="text-base text-purple-200 mb-4">
              Use the Celestial Wars/Assiah setting with rich lore and characters.
            </p>
            <div className="flex items-center justify-center space-x-2">
              <Checkbox
                checked={campaignData.aiPersonalities.defaultWorld}
                onCheckedChange={(checked) => updateAIPersonality('defaultWorld', !!checked)}
                className="border-purple-400 data-[state=checked]:bg-cyan-500 data-[state=checked]:border-cyan-500"
              />
              <span className="text-base text-purple-200">Use default world</span>
            </div>
          </CardContent>
        </Card>

        {/* Mechanical Precision */}
        <Card className={`bg-black/50 backdrop-blur-md border border-purple-300/30 transition-all duration-200 hover:border-purple-200/50 hover:bg-black/40 ${
          campaignData.aiPersonalities.mechanicalPrecision
            ? 'border-purple-400/50 bg-gradient-to-br from-purple-500/20 to-pink-600/20'
            : 'border-purple-500/30 hover:border-purple-400/50'
        }`}>
          <CardContent className="p-6 text-center">
            <div className="flex justify-center mb-4">
              <Settings className="w-12 h-12 text-purple-400" />
            </div>
            <h3 className="text-white mb-3 text-xl">Mechanical Precision</h3>
            <p className="text-base text-purple-200 mb-4">
              Rules accuracy, combat mechanics, and game system expertise.
            </p>
            <div className="flex items-center justify-center space-x-2">
              <Checkbox
                checked={campaignData.aiPersonalities.mechanicalPrecision}
                onCheckedChange={(checked) => updateAIPersonality('mechanicalPrecision', !!checked)}
                className="border-purple-400 data-[state=checked]:bg-purple-500 data-[state=checked]:border-purple-500"
              />
              <span className="text-base text-purple-200">Enable</span>
            </div>
          </CardContent>
        </Card>

        {/* Starting Companions */}
        <Card className={`bg-black/50 backdrop-blur-md border border-purple-300/30 transition-all duration-200 hover:border-purple-200/50 hover:bg-black/40 ${
          campaignData.aiPersonalities.companions
            ? 'border-green-400/50 bg-gradient-to-br from-green-500/20 to-emerald-600/20'
            : 'border-purple-500/30 hover:border-purple-400/50'
        }`}>
          <CardContent className="p-6 text-center">
            <div className="flex justify-center mb-4">
              <Users className="w-12 h-12 text-green-400" />
            </div>
            <h3 className="text-white mb-3 text-xl">Starting Companions</h3>
            <p className="text-base text-purple-200 mb-4">
              Automatically create complementary party members to join your adventure.
            </p>
            <div className="flex items-center justify-center space-x-2">
              <Checkbox
                checked={campaignData.aiPersonalities.companions}
                onCheckedChange={(checked) => updateAIPersonality('companions', !!checked)}
                className="border-purple-400 data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500"
              />
              <span className="text-base text-purple-200">Generate companions</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="flex items-center space-x-3 mb-6">
        <div className="text-2xl">🚀</div>
        <div>
          <h2 className="text-3xl text-white mb-2">Ready to Launch!</h2>
          <p className="text-purple-200 text-lg">Review your settings and start your adventure.</p>
        </div>
      </div>

      <Card className="bg-black/50 backdrop-blur-md border border-purple-300/30">
        <CardContent className="p-6">
          <h3 className="text-xl text-white mb-4">Campaign Summary</h3>

          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <span className="text-purple-300 font-medium w-32 flex-shrink-0 text-lg">Title:</span>
              <span className="text-white text-lg sm:ml-4">{campaignData.title}</span>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <span className="text-purple-300 font-medium w-32 flex-shrink-0 text-lg">Character:</span>
              <span className="text-white text-lg sm:ml-4">{campaignData.character || 'Random Character'}</span>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-start gap-2">
              <span className="text-purple-300 font-medium w-32 flex-shrink-0 text-lg">Description:</span>
              <span className="text-purple-200 text-lg sm:ml-4">
                # Campaign summary You are {campaignData.character}, a 16 year o...
              </span>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <span className="text-purple-300 font-medium w-32 flex-shrink-0 text-lg">AI Personalities:</span>
              <div className="flex flex-wrap gap-2 sm:ml-4">
                {campaignData.aiPersonalities.defaultWorld && (
                  <Badge className="bg-cyan-500/20 text-cyan-300 border-cyan-500/30 text-base px-3 py-1">Narrative</Badge>
                )}
                {campaignData.aiPersonalities.mechanicalPrecision && (
                  <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30 text-base px-3 py-1">Mechanics</Badge>
                )}
                {campaignData.aiPersonalities.companions && (
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30 text-base px-3 py-1">Companions</Badge>
                )}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <span className="text-purple-300 font-medium w-32 flex-shrink-0 text-lg">Options:</span>
              <div className="flex flex-wrap gap-2 sm:ml-4">
                <Badge className="bg-yellow-500/20 text-yellow-300 border-yellow-500/30 text-base px-3 py-1">
                  {campaignData.type === 'dragon-knight' ? 'Dragon Knight World' : 'Custom World'}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-center">
        <Button
          onClick={handleNext}
          disabled={isCreating}
          className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-12 py-3 text-lg shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Sparkles className="w-5 h-5 mr-2" />
          {isCreating ? 'Creating Campaign...' : 'Begin Adventure!'}
        </Button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Subtle background effects */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-20 right-20 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 left-20 w-72 h-72 bg-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="relative z-10 min-h-screen py-8 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl md:text-4xl text-white mb-2">Start a New Campaign</h1>
          </div>

          {/* Progress Stepper */}
          {renderProgressStepper()}

          {/* Main Content Card */}
          <Card className="bg-black/50 backdrop-blur-md border border-purple-300/30 shadow-xl">
            <CardContent className="p-6 md:p-8">
              {currentStep === 1 && renderStep1()}
              {currentStep === 2 && renderStep2()}
              {currentStep === 3 && renderStep3()}
            </CardContent>
          </Card>

          {/* Navigation Buttons */}
          {currentStep < 3 && (
            <div className="flex justify-between items-center mt-8">
              <Button
                variant="ghost"
                onClick={currentStep === 1 ? onBack : handlePrevious}
                className="text-purple-200 hover:text-white hover:bg-purple-500/20"
              >
                {currentStep === 1 ? (
                  <>
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back
                  </>
                ) : (
                  'Previous'
                )}
              </Button>

              <span className="text-base text-purple-300">
                Step {currentStep} of 3
              </span>

              <Button
                onClick={handleNext}
                className="bg-purple-600 hover:bg-purple-700 text-white px-8"
              >
                Next
              </Button>
            </div>
          )}

          {currentStep === 3 && (
            <div className="flex justify-between items-center mt-8">
              <Button
                variant="ghost"
                onClick={handlePrevious}
                className="text-purple-200 hover:text-white hover:bg-purple-500/20"
              >
                Previous
              </Button>

              <span className="text-base text-purple-300">
                Step 3 of 3
              </span>

              <div></div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
