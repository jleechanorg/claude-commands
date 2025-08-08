import { useState, useEffect, useRef } from 'react'
import { useTestMode } from '../hooks/useTestMode'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Card, CardContent } from './ui/card'
import { Badge } from './ui/badge'
import { Checkbox } from './ui/checkbox'
import { ArrowLeft, ChevronDown, ChevronUp, Sparkles, Users, Settings, Globe, Loader2, Clock, Zap, RefreshCw, AlertTriangle, CheckCircle, WifiOff } from 'lucide-react'
import { DRAGON_KNIGHT_DESCRIPTION, DRAGON_KNIGHT_DESCRIPTION_SHORT, DRAGON_KNIGHT_SUMMARY, DRAGON_KNIGHT_CHARACTER, MAX_DESCRIPTION_LENGTH } from '../constants/campaignDescriptions'

import type { Campaign, Theme } from '../types'

// Configuration constants
const DRAGON_KNIGHT_DEFAULT_WORLD = true

interface CampaignCreationV2Props {
  onCreateCampaign: (campaign: Omit<Campaign, 'id' | 'createdAt' | 'lastPlayed' | 'storyLength'> & {
    type?: 'dragon-knight' | 'custom';
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
  const isTestMode = useTestMode()
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const completionTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false)
  const [creationProgress, setCreationProgress] = useState(0)
  const [creationStatus, setCreationStatus] = useState('')
  const [showOptimisticUI, setShowOptimisticUI] = useState(false)

  // Default values for each campaign type
  const dragonKnightDefaults = {
    character: DRAGON_KNIGHT_CHARACTER,
    setting: 'World of Assiah. Caught between an oath to a ruthless tyrant who enforces a prosperous peace and the call of a chaotic dragon promising true freedom, a young knight must decide whether to slaughter innocents to preserve order or start a war to reclaim the world\'s soul.',
    description: DRAGON_KNIGHT_DESCRIPTION
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
    description: dragonKnightDefaults.description,
    aiPersonalities: {
      defaultWorld: true,
      mechanicalPrecision: true,
      companions: true
    }
  })

  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [isTimeout, setIsTimeout] = useState(false)

  // Dragon Knight narrative logic: Auto-enable defaultWorld and make it non-optional
  useEffect(() => {
    if (campaignData.type === 'dragon-knight') {
      setCampaignData(prev => ({
        ...prev,
        aiPersonalities: {
          ...prev.aiPersonalities,
          defaultWorld: DRAGON_KNIGHT_DEFAULT_WORLD // Always true for Dragon Knight campaigns
        }
      }))
    }
  }, [campaignData.type])

  // Helper function to clear all timers
  const clearAllTimers = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current)
      progressIntervalRef.current = null
    }
    if (completionTimeoutRef.current) {
      clearTimeout(completionTimeoutRef.current)
      completionTimeoutRef.current = null
    }
  }

  // Cleanup all timers on unmount
  useEffect(() => {
    return () => {
      clearAllTimers()
    }
  }, [])

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
    setError(null) // Clear any existing errors when validating

    switch (currentStep) {
      case 1:
        if (!campaignData.title.trim()) {
          setError('Please enter a campaign title')
          return false
        }
        if (campaignData.title.length > 100) {
          setError('Campaign title must be 100 characters or less')
          return false
        }
        if (campaignData.character && campaignData.character.length > 100) {
          setError('Character name must be 100 characters or less')
          return false
        }
        if (campaignData.setting && campaignData.setting.length > 5000) {
          setError('Setting description must be 5000 characters or less')
          return false
        }
        if (campaignData.description && campaignData.description.length > MAX_DESCRIPTION_LENGTH) {
          setError(`Campaign description must be ${MAX_DESCRIPTION_LENGTH.toLocaleString()} characters or less`)
          return false
        }
        return true
      case 2:
        if (!Object.values(campaignData.aiPersonalities).some(Boolean)) {
          setError('Please select at least one AI personality to enhance your campaign')
          return false
        }
        return true
      default:
        return true
    }
  }

  const handleCampaignCreation = async () => {
    setError(null)
    setShowOptimisticUI(true)
    setCreationProgress(0)
    setIsTimeout(false)

    // Enhanced progress simulation with better UX
    const progressSteps = [
      { progress: 15, status: 'Initializing campaign world...', duration: 1000 },
      { progress: 30, status: 'Processing AI personalities...', duration: 1200 },
      { progress: 45, status: 'Generating character details...', duration: 1000 },
      { progress: 60, status: 'Building story foundation...', duration: 1500 },
      { progress: 75, status: 'Weaving narrative threads...', duration: 1200 },
      { progress: 90, status: 'Finalizing campaign setup...', duration: 800 },
      { progress: 95, status: 'Almost ready...', duration: 500 }
    ]

    let currentStepIndex = 0

    // More realistic progress updates
    const progressInterval = setInterval(() => {
      if (currentStepIndex < progressSteps.length) {
        const step = progressSteps[currentStepIndex]
        setCreationProgress(step.progress)
        setCreationStatus(step.status)
        currentStepIndex++
      }
    }, 1000)
    
    // Store interval ref for cleanup
    progressIntervalRef.current = progressInterval

    // Enhanced timeout handling with multiple warnings  
    try {
      // Store timeout in ref for proper cleanup
      timeoutRef.current = setTimeout(() => {
        setIsTimeout(true)
        setCreationStatus('Taking longer than usual - complex campaigns need more time...')
      }, 20000) // 20 second timeout warning

      // const criticalTimeoutId = setTimeout(() => {
      //   setCreationStatus('Still working... This might indicate a server issue.')
      // }, 45000) // 45 second critical warning

      // Convert to Campaign format with additional data
      const campaign = {
        title: campaignData.title,
        type: campaignData.type,
        // Use short version for Dragon Knight to stay under 5000 char API limit
        description: campaignData.type === 'dragon-knight' ? DRAGON_KNIGHT_DESCRIPTION_SHORT : campaignData.description,
        character: campaignData.character,
        setting: campaignData.setting,
        aiPersonalities: campaignData.aiPersonalities
      }

      await onCreateCampaign(campaign)

      // Complete the progress with satisfying animation
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
      clearInterval(progressInterval)
      progressIntervalRef.current = null

      // Smooth completion animation
      setCreationProgress(100)
      setCreationStatus('🎉 Campaign ready! Taking you to your adventure... 🎉')

      // Brief celebration with proper timeout tracking to prevent memory leaks
      await new Promise<void>((resolve) => {
        const completionTimeout = setTimeout(() => {
          resolve()
        }, 1200)
        completionTimeoutRef.current = completionTimeout
      })

    } catch (error) {
      // Clean up all timers on error
      clearInterval(progressInterval)
      progressIntervalRef.current = null
      
      // Clear the timeout warning timer if it exists
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
      
      setShowOptimisticUI(false)
      setIsTimeout(false)
      console.error('Failed to create campaign:', error)

      // Enhanced error messaging with recovery suggestions and offline detection
      let errorMessage = 'Campaign creation failed. Please try again.'
      let isRetryable = true
      const isOffline = !navigator.onLine

      if (isOffline) {
        errorMessage = 'You appear to be offline. Please check your internet connection and try again.'
        isRetryable = false
      } else if (error instanceof Error) {
        if (error.message.includes('timeout') || error.message.includes('network')) {
          errorMessage = 'Connection timeout. The server took too long to respond. This often happens with complex campaigns.'
        } else if (error.message.includes('authentication') || error.message.includes('401')) {
          errorMessage = 'Authentication expired. Please refresh the page and sign in again.'
          isRetryable = false
        } else if (error.message.includes('server') || error.message.includes('500')) {
          errorMessage = 'Server error. Our AI is temporarily overwhelmed. Please try again in a moment.'
        } else if (error.message.includes('validation') || error.message.includes('400')) {
          errorMessage = 'Invalid campaign data. Please check your inputs and try again.'
          isRetryable = false
          // Go back to step 1 to let user fix the data
          setCurrentStep(1)
        } else if (error.message.includes('Required field')) {
          errorMessage = `Validation error: ${error.message}`
          isRetryable = false
          setCurrentStep(1)
        } else {
          errorMessage = error.message
        }
      }

      setError(errorMessage)

      // Auto-retry for certain errors (not when offline)
      if (isRetryable && retryCount < 2 && !isOffline && (error as any)?.message?.includes('timeout')) {
        console.log(`Auto-retrying campaign creation (${retryCount + 1}/2) after timeout`)
        
        // Clear any existing timeout before setting a new one
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
          timeoutRef.current = null
        }
        
        const retryTimeoutId = setTimeout(() => {
          // Only retry if this timeout is still active and component is mounted
          if (timeoutRef.current === retryTimeoutId) {
            timeoutRef.current = null
            setRetryCount(prev => prev + 1)
            setError(null)
            handleCampaignCreation()
          }
        }, 3000)

        // Store timeout ID for cleanup on unmount
        timeoutRef.current = retryTimeoutId
      }
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
            maxLength={100}
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
                updateCampaignData('description', dragonKnightDefaults.description)
              }}
            >
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <div className="text-2xl">🐉</div>
                  <div className="flex-1">
                    <h3 className="text-white mb-1 text-lg">Dragon Knight Campaign</h3>
                    <p className="text-base text-purple-200">
                      {DRAGON_KNIGHT_SUMMARY}
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
                updateCampaignData('description', '')
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
            placeholder={campaignData.type === 'dragon-knight' ? 'Your knight character name' : 'Your character name'}
            maxLength={100}
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
            placeholder={campaignData.type === 'dragon-knight'
              ? 'World of Assiah (Dragon Knight setting will be used by default)'
              : 'Describe the world where your adventure takes place...'
            }
            maxLength={MAX_DESCRIPTION_LENGTH}
          />
          <p className="text-base text-purple-300 mt-1">
            {campaignData.type === 'dragon-knight'
              ? 'Dragon Knight uses the World of Assiah by default. Customize or leave blank to use default.'
              : 'Leave blank for a randomly generated world'
            }
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
                maxLength={MAX_DESCRIPTION_LENGTH}
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
                disabled={campaignData.type === 'dragon-knight'}
                aria-label={campaignData.type === 'dragon-knight' ? 'Default world setting is required and cannot be changed for Dragon Knight campaigns' : 'Enable default world setting'}
                className="border-purple-400 data-[state=checked]:bg-cyan-500 data-[state=checked]:border-cyan-500 disabled:opacity-50"
              />
              <span className={`text-base ${campaignData.type === 'dragon-knight' ? 'text-purple-300' : 'text-purple-200'}`}>
                {campaignData.type === 'dragon-knight' ? 'Required for Dragon Knight' : 'Use default world'}
              </span>
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
              <span className="text-purple-300 font-medium w-32 flex-shrink-0 text-lg">Setting:</span>
              <span className="text-purple-200 text-lg sm:ml-4">
                {campaignData.setting || (campaignData.type === 'dragon-knight' ? 'World of Assiah (Default)' : 'Random World')}
              </span>
            </div>
            {campaignData.description && (
              <div className="flex flex-col sm:flex-row sm:items-start gap-2">
                <span className="text-purple-300 font-medium w-32 flex-shrink-0 text-lg">Description:</span>
                <span className="text-purple-200 text-lg sm:ml-4">
                  {campaignData.description}
                </span>
              </div>
            )}

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

      {showOptimisticUI ? (
        <div className="space-y-6">
          {/* Progress Indicator */}
          <Card className="bg-black/50 backdrop-blur-md border border-purple-300/30">
            <CardContent className="p-6">
              <div className="text-center space-y-4">
                <div className="flex items-center justify-center space-x-3 mb-4">
                  <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
                  <h3 className="text-xl text-white font-medium">Creating Your Campaign</h3>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500 ease-out rounded-full"
                    style={{ width: `${creationProgress}%` }}
                  />
                </div>

                {/* Status Message */}
                <p className="text-purple-200 text-lg animate-pulse">{creationStatus}</p>

                {/* Progress Percentage */}
                <p className="text-purple-300 text-sm">{creationProgress}% Complete</p>

                {/* Enhanced Timeout Warning with Actions */}
                {isTimeout ? (
                  <div className="mt-6 p-4 bg-yellow-900/20 rounded-lg border border-yellow-500/20">
                    <div className="flex items-center space-x-2 mb-2">
                      <Clock className="w-4 h-4 text-yellow-400" />
                      <span className="text-yellow-200 text-sm font-medium">Taking longer than usual</span>
                    </div>
                    <p className="text-yellow-200 text-sm mb-3">
                      Complex campaigns require more processing time. This is normal for detailed world-building.
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setIsTimeout(false)
                          setCreationStatus('Continuing campaign creation...')
                        }}
                        className="text-yellow-300 hover:text-yellow-100 text-xs"
                      >
                        Keep Waiting
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="mt-6 p-4 bg-purple-900/20 rounded-lg border border-purple-500/20">
                    <div className="flex items-center space-x-2 mb-2">
                      <Zap className="w-4 h-4 text-yellow-400" />
                      <span className="text-yellow-200 text-sm font-medium">Did you know?</span>
                    </div>
                    <p className="text-purple-200 text-sm">
                      {campaignData.type === 'dragon-knight'
                        ? "The Dragon Knight campaign features dynamic moral choices that affect the story's outcome and your character's path."
                        : "Custom campaigns allow for unlimited creativity - your AI Game Master adapts to any world you can imagine!"}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="flex flex-col items-center space-y-4">
          <Button
            onClick={handleNext}
            disabled={isCreating || showOptimisticUI}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-12 py-3 text-lg shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <Sparkles className="w-5 h-5 mr-2 group-hover:animate-pulse" />
            {isCreating || showOptimisticUI ? 'Creating Campaign...' : 'Begin Adventure!'}
          </Button>

          {/* Quick Tip */}
          <p className="text-purple-300 text-sm text-center max-w-md">
            Your campaign will be created in a few moments. You can customize settings later in the game.
          </p>
        </div>
      )}
    </div>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Test Mode Indicator */}
      {isTestMode && (
        <div className="fixed top-4 right-4 z-50 bg-yellow-500/90 text-black px-3 py-1 rounded-lg text-sm font-medium shadow-lg">
          🧪 TEST MODE
        </div>
      )}

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

          {/* Enhanced Error Display with Better Recovery Options */}
          {error && (
            <Card className="bg-red-900/50 backdrop-blur-md border border-red-400/50 shadow-xl mb-6">
              <CardContent className="p-6">
                <div className="text-center">
                  <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    {!navigator.onLine ? (
                      <WifiOff className="w-8 h-8 text-red-400" />
                    ) : (
                      <AlertTriangle className="w-8 h-8 text-red-400" />
                    )}
                  </div>
                  <h3 className="text-red-200 font-medium text-lg mb-2">
                    {!navigator.onLine ? 'Connection Issue' : 'Campaign Creation Failed'}
                  </h3>
                  <p className="text-red-300 text-sm mb-4 max-w-md mx-auto leading-relaxed">{error}</p>

                  {retryCount > 0 && navigator.onLine && (
                    <p className="text-red-400 text-xs mb-4">
                      Attempt {retryCount + 1} of 3 • Don't worry, this happens sometimes
                    </p>
                  )}

                  <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
                    {/* Show retry button only if online and haven't exceeded retries */}
                    {navigator.onLine && retryCount < 2 && !error.includes('validation') && !error.includes('Authentication') && (
                      <Button
                        onClick={() => {
                          setRetryCount(prev => prev + 1)
                          setError(null)
                          handleCampaignCreation()
                        }}
                        className="bg-red-600 hover:bg-red-700 text-white px-6 py-2"
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Retry Creation
                      </Button>
                    )}

                    {/* Always show modify settings button */}
                    <Button
                      variant="outline"
                      onClick={() => {
                        setError(null)
                        setRetryCount(0)
                        // Go to appropriate step based on error type
                        if (error.includes('validation') || error.includes('Required field')) {
                          setCurrentStep(1) // Data validation issues
                        } else {
                          setCurrentStep(2) // AI settings issues
                        }
                      }}
                      className="border-red-400/50 text-red-300 hover:bg-red-500/20"
                    >
                      {error.includes('validation') ? 'Fix Campaign Data' : 'Modify Settings'}
                    </Button>

                    <Button
                      variant="ghost"
                      onClick={() => {
                        setError(null)
                        setRetryCount(0)
                      }}
                      className="text-red-300 hover:text-red-100 hover:bg-red-500/10"
                    >
                      Dismiss
                    </Button>
                  </div>

                  {/* Show helpful tips based on situation */}
                  {!navigator.onLine ? (
                    <div className="mt-4 p-3 bg-yellow-900/20 rounded-lg border border-yellow-500/20">
                      <div className="flex items-center justify-center mb-2">
                        <WifiOff className="w-4 h-4 text-yellow-400 mr-2" />
                        <span className="text-yellow-200 text-sm font-medium">Offline Mode</span>
                      </div>
                      <p className="text-yellow-200 text-xs">
                        Campaign creation requires an internet connection. Please check your network and try again.
                      </p>
                    </div>
                  ) : retryCount >= 2 ? (
                    <div className="mt-4 p-3 bg-blue-900/20 rounded-lg border border-blue-500/20">
                      <p className="text-blue-200 text-xs">
                        💡 Try simplifying your campaign settings, using shorter descriptions, or waiting a moment before trying again
                      </p>
                    </div>
                  ) : error.includes('validation') ? (
                    <div className="mt-4 p-3 bg-amber-900/20 rounded-lg border border-amber-500/20">
                      <p className="text-amber-200 text-xs">
                        ✏️ Please check your campaign information for any missing or invalid data
                      </p>
                    </div>
                  ) : null}
                </div>
              </CardContent>
            </Card>
          )}

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
