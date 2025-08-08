import { useState, useRef, useEffect } from 'react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Textarea } from './ui/textarea'
import { ScrollArea } from './ui/scroll-area'
import { apiService } from '../services/api.service'
import {
  ArrowLeft,
  Send,
  User,
  Crown,
  Settings,
  RefreshCw,
  Download,
  Share,
  Volume2,
  VolumeX,
  Sparkles,
  Heart,
  Shield,
  Swords
} from 'lucide-react'


interface GamePlayViewProps {
  onBack: () => void
  campaignTitle: string
  campaignId?: string
}

interface StoryEntry {
  id: string
  type: 'narration' | 'action' | 'dialogue' | 'system' | 'choices'
  content: string
  timestamp: string
  author: 'player' | 'ai' | 'system'
  choices?: string[]
}

export function GamePlayView({ onBack, campaignTitle, campaignId }: GamePlayViewProps) {
  console.log('🎯 GAMEPLAYVIEW received campaignTitle:', campaignTitle)
  console.log('🎯 GAMEPLAYVIEW received campaignId:', campaignId)
  
  const [story, setStory] = useState<StoryEntry[]>([])

  const [playerInput, setPlayerInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isInitializing, setIsInitializing] = useState(true)
  const [isSoundEnabled, setIsSoundEnabled] = useState(true)
  const [mode, setMode] = useState<'god'>('god')

  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const initialStoryCreatedRef = useRef(false)

  // Load existing campaign data when component mounts (like V1 does)
  useEffect(() => {
    if (!campaignId || initialStoryCreatedRef.current) {
      return
    }

    initialStoryCreatedRef.current = true

    const loadCampaignData = async () => {
      try {
        setIsInitializing(true)

        // First, try to load existing campaign data (like V1 does)
        console.log('🎯 GAMEPLAYVIEW loading existing campaign data for:', campaignId)
        
        try {
          const campaignData = await apiService.getCampaign(campaignId)
          console.log('🎯 GAMEPLAYVIEW loaded campaign data:', campaignData)

          // Convert existing story entries to V2 format
          if (campaignData.story && Array.isArray(campaignData.story) && campaignData.story.length > 0) {
            console.log('🎯 GAMEPLAYVIEW found existing story entries:', campaignData.story.length)
            
            const convertedStory = campaignData.story.map((entry: any, index: number) => ({
              id: `story-${index}`,
              type: entry.mode === 'god' ? 'narration' : 'action' as 'narration' | 'action',
              content: entry.text || entry.narrative || '',
              timestamp: entry.timestamp || new Date().toISOString(),
              author: entry.actor === 'user' ? 'player' : (entry.actor === 'gemini' ? 'ai' : 'system') as 'player' | 'ai' | 'system'
            }))

            setStory(convertedStory)
            setIsInitializing(false)
            return // Exit early if we successfully loaded existing story
          }
        } catch (error) {
          console.warn('🎯 GAMEPLAYVIEW failed to load existing campaign data, creating new content:', error)
        }

        // Fallback: Create initial content if no existing story (new campaign or API error)
        console.log('🎯 GAMEPLAYVIEW creating initial content for new campaign')
        const welcomeMessage = `Welcome to ${campaignTitle}! Your adventure begins now...`
        
        const initialStory: StoryEntry = {
          id: '1',
          type: 'system',
          content: welcomeMessage,
          timestamp: new Date().toISOString(),
          author: 'system'
        }
        setStory([initialStory])

        // Send initial prompt to get story content
        const response = await apiService.sendInteraction(campaignId, {
          input: 'Begin the adventure',
          mode: 'god' // Use god mode for content generation
        })

        if (response.success && (response.response || response.narrative)) {
          const content = response.response || response.narrative || ''
          const aiStory: StoryEntry = {
            id: `init-${Date.now()}`,
            type: 'narration',
            content: content,
            timestamp: new Date().toISOString(),
            author: 'ai'
          }

          setStory(prev => [...prev, aiStory])
        }
      } catch (error) {
        console.error('Failed to load campaign or generate initial content:', error)
        // Fall back to a generic message without hardcoded character names
        const fallbackStory: StoryEntry = {
          id: `fallback-${Date.now()}`,
          type: 'narration',
          content: 'Your adventure is about to begin. The world awaits your first move...',
          timestamp: new Date().toISOString(),
          author: 'ai'
        }
        setStory(prev => [...prev, fallbackStory])
      } finally {
        setIsInitializing(false)
      }
    }

    loadCampaignData()
  }, [campaignId])

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [story])

  const handleSubmit = async () => {
    if (!playerInput.trim() || isLoading) return

    const userAction: StoryEntry = {
      id: Date.now().toString(),
      type: 'action',
      content: playerInput,
      timestamp: new Date().toISOString(),
      author: 'player'
    }

    setStory(prev => [...prev, userAction])
    setPlayerInput('')
    setIsLoading(true)

    // Generate real AI response
    try {
      const response = await apiService.sendInteraction(campaignId || '', {
        input: playerInput,
        mode: mode
      })

      if (response.success && (response.response || response.narrative)) {
        const content = response.response || response.narrative || 'The AI ponders your action...'
        const aiResponse: StoryEntry = {
          id: (Date.now() + 1).toString(),
          type: 'narration',
          content: content,
          timestamp: new Date().toISOString(),
          author: 'ai'
        }

        setStory(prev => [...prev, aiResponse])
      } else {
        // Fallback response
        const aiResponse: StoryEntry = {
          id: (Date.now() + 1).toString(),
          type: 'narration',
          content: 'Your action ripples through the world, creating new possibilities...',
          timestamp: new Date().toISOString(),
          author: 'ai'
        }

        setStory(prev => [...prev, aiResponse])
      }
    } catch (error) {
      console.error('Failed to get AI response:', error)
      // Error fallback response
      const aiResponse: StoryEntry = {
        id: (Date.now() + 1).toString(),
        type: 'narration',
        content: 'The world seems to pause, waiting for the next moment to unfold...',
        timestamp: new Date().toISOString(),
        author: 'ai'
      }

      setStory(prev => [...prev, aiResponse])
    } finally {
      setIsLoading(false)
    }
  }

  const handleChoiceClick = (choice: string) => {
    setPlayerInput(choice)
    textareaRef.current?.focus()
  }




  const renderStoryEntry = (entry: StoryEntry) => {
    if (entry.type === 'choices' && entry.choices) {
      return (
        <div key={entry.id} className="mb-6">
          <div className="bg-purple-100/50 border-l-4 border-purple-400 p-4 mb-4 rounded-r-lg backdrop-blur-sm">
            <div className="flex items-center justify-between mb-2">
              <Badge className="bg-purple-200 text-purple-800 border-purple-300">Game Master</Badge>
              <span className="text-xs text-purple-600">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <p className="text-purple-900 leading-relaxed italic">{entry.content}</p>
          </div>
          <div className="space-y-2">
            {entry.choices.map((choice, index) => (
              <div
                key={index}
                className="bg-white/80 hover:bg-purple-50/80 border border-purple-200 rounded-lg p-3 cursor-pointer transition-all duration-200 backdrop-blur-sm hover:border-purple-300 hover:shadow-sm"
                onClick={() => handleChoiceClick(choice)}
              >
                <p className="text-purple-800 text-sm">{choice}</p>
              </div>
            ))}
          </div>
        </div>
      )
    }

    const getEntryStyle = () => {
      switch (entry.type) {
        case 'action':
          return 'bg-green-100/50 border-l-4 border-green-400'
        case 'narration':
          return 'bg-white/60'
        case 'dialogue':
          return 'bg-yellow-100/50 border-l-4 border-yellow-400'
        case 'system':
          return 'bg-purple-100/50 border-l-4 border-purple-400'
        default:
          return 'bg-white/60'
      }
    }

    const getAuthorBadge = () => {
      switch (entry.author) {
        case 'player':
          return <Badge className="bg-green-200 text-green-800 border-green-300">You</Badge>
        case 'ai':
          return <Badge className="bg-purple-200 text-purple-800 border-purple-300">Game Master</Badge>
        case 'system':
          return <Badge className="bg-orange-200 text-orange-800 border-orange-300">System</Badge>
        default:
          return null
      }
    }

    return (
      <div key={entry.id} className={`p-4 rounded-lg mb-4 backdrop-blur-sm border border-purple-200/50 ${getEntryStyle()}`}>
        <div className="flex items-start justify-between mb-2">
          {getAuthorBadge()}
          <span className="text-xs text-purple-600">
            {new Date(entry.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <p className="text-purple-900 leading-relaxed">{entry.content}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-purple-50 to-indigo-100">
      {/* Subtle background effects */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-20 right-20 w-96 h-96 bg-purple-300/30 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 left-20 w-72 h-72 bg-pink-300/30 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="relative z-10">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-md border-b border-purple-200 px-6 py-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                  <span className="text-white text-lg">🎲</span>
                </div>
                <h1 className="text-xl font-semibold text-purple-900">WorldArchitect.AI</h1>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-purple-700">Epic Adventurer</span>
              <div className="flex items-center space-x-1">
                <span className="text-yellow-500">⭐</span>
                <span className="text-yellow-500">😀</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsSoundEnabled(!isSoundEnabled)}
                className="text-purple-700 hover:text-purple-900 hover:bg-purple-100"
              >
                {isSoundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-purple-700 hover:text-purple-900 hover:bg-purple-100"
              >
                <Settings className="w-4 h-4 mr-1" />
                Settings
              </Button>
            </div>
          </div>
        </header>

        {/* Campaign Header */}
        <div className="bg-white/60 backdrop-blur-md border-b border-purple-200 px-6 py-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                className="text-purple-700 hover:text-purple-900 hover:bg-purple-100"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <h2 className="text-2xl font-semibold text-purple-900">{campaignTitle}</h2>
              <Badge className="bg-purple-200 text-purple-800 border-purple-300">
                <Sparkles className="w-3 h-3 mr-1" />
                Fantasy Campaign
              </Badge>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                className="text-purple-700 hover:text-purple-900 hover:bg-purple-100"
              >
                <Download className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-purple-700 hover:text-purple-900 hover:bg-purple-100"
              >
                <Share className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex gap-6">
            {/* Main Game Area */}
            <div className="flex-1">
              {/* Story Area */}
              <div className="mb-6">
                <ScrollArea ref={scrollAreaRef} className="h-[60vh] rounded-lg">
                  <div className="space-y-4 pr-4">
                    {story.map((entry) => renderStoryEntry(entry))}

                    {isInitializing && (
                      <div className="bg-blue-100/50 border-l-4 border-blue-400 p-4 rounded-r-lg backdrop-blur-sm">
                        <div className="flex items-center space-x-3">
                          <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-150"></div>
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-300"></div>
                            <span className="text-blue-700 ml-2 text-sm">Crafting your personalized adventure...</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {isLoading && (
                      <div className="bg-purple-100/50 border-l-4 border-purple-400 p-4 rounded-r-lg backdrop-blur-sm">
                        <div className="flex items-center space-x-3">
                          <RefreshCw className="w-4 h-4 text-purple-600 animate-spin" />
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse delay-150"></div>
                            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse delay-300"></div>
                            <span className="text-purple-700 ml-2 text-sm">The Game Master is thinking...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </div>

              {/* Input Area */}
              <div className="bg-white/80 backdrop-blur-md border border-purple-200 rounded-lg p-6 shadow-lg">
            <div className="mb-4">
              <Textarea
                ref={textareaRef}
                value={playerInput}
                onChange={(e) => setPlayerInput(e.target.value)}
                placeholder="What do you do? Describe your action..."
                className="min-h-[100px] resize-none border-purple-200 focus:border-purple-400 focus:ring-purple-400 bg-white/70 backdrop-blur-sm"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSubmit()
                  }
                }}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-purple-700 bg-purple-100 hover:bg-purple-100"
                    disabled
                  >
                    <Crown className="w-4 h-4 mr-1" />
                    God Mode
                  </Button>
                </div>
              </div>

              <Button
                onClick={handleSubmit}
                disabled={!playerInput.trim() || isLoading}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-2 shadow-lg"
              >
                <Send className="w-4 h-4 mr-2" />
                Send
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
  )
}
