'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent } from './ui/card'
import { Badge } from './ui/badge'
import { Textarea } from './ui/textarea'
import { ScrollArea } from './ui/scroll-area'
import {
  ArrowLeft,
  Send,
  Dice6,
  Crown,
  BookOpen,
  Settings,
  Download,
  RefreshCw,
  Lightbulb,
  MessageSquare,
  Eye,
  Target,
  Move,
  Sparkles,
  Gift
} from 'lucide-react'
import type { Campaign, Theme } from '../types'
import { apiService } from '../services/api.service'
import { handleAsyncError, showErrorToast, showSuccessToast, LoadingState } from '../utils/errorHandling'
import type { InteractionRequest, InteractionResponse } from '../services/api.types'
import { formatDiceRolls, DiceRoll, formatDiceRoll } from '../utils/diceUtils'
import { DiceRollDisplay } from './DiceRollDisplay'

interface GameViewProps {
  campaign: Campaign
  theme: Theme
  onUpdateCampaign: (campaign: Campaign) => void
  onBack: () => void
}

interface StoryEntry {
  id: string
  type: 'narration' | 'action' | 'dialogue' | 'system' | 'rewards' | 'error'
  content: string
  timestamp: string
  author?: 'player' | 'ai' | 'system'
  isError?: boolean
  isRetryable?: boolean
  originalInput?: string
  dice_rolls?: (string | DiceRoll | unknown)[]
  god_mode_response?: string
  narrative?: string
}


export function GameView({ campaign, theme, onUpdateCampaign, onBack }: GameViewProps) {
  const [story, setStory] = useState<StoryEntry[]>([])

  const [playerInput, setPlayerInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingState, setLoadingState] = useState<LoadingState>({ isLoading: false })
  const [retryCount, setRetryCount] = useState(0)
  const [aiError, setAiError] = useState<string | null>(null)
  const [lastFailedInput, setLastFailedInput] = useState<string>('')
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  // Monitor network status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      if (aiError) {
        showSuccessToast('Connection restored - AI is available again', { context: 'Network', duration: 3000 })
        setAiError(null) // Clear AI error when back online
      }
    }

    const handleOffline = () => {
      setIsOnline(false)
      showErrorToast('You are offline - AI responses will be unavailable until connection is restored', {
        context: 'Network',
        persistent: true
      })
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [aiError])
  const [mode] = useState<'god'>('god')
  const [showSuggestions, setShowSuggestions] = useState(true)

  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const actionSuggestions: { icon: any; text: string; type: string }[] = []


  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [story])

  const getThemeGradient = () => {
    switch (theme) {
      case 'light':
        return 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100'
      case 'dark':
        return 'bg-gradient-to-br from-gray-950 via-gray-900 to-slate-900'
      case 'fantasy':
        return 'bg-gradient-to-br from-purple-950 via-indigo-950 to-slate-900'
      case 'dark-fantasy':
        return 'bg-gradient-to-br from-gray-950 via-purple-950 to-indigo-950'
      case 'cyberpunk':
        return 'bg-gradient-to-br from-gray-950 via-cyan-950 to-blue-950'
      default:
        return 'bg-gradient-to-br from-purple-950 via-indigo-950 to-slate-900'
    }
  }

  const getAccentColors = () => {
    switch (theme) {
      case 'light':
        return {
          primary: 'from-blue-600 to-purple-600',
          secondary: 'from-blue-500 to-purple-500',
          accent: 'from-indigo-500 to-purple-500'
        }
      case 'dark':
        return {
          primary: 'from-blue-500 to-purple-500',
          secondary: 'from-blue-400 to-purple-400',
          accent: 'from-slate-400 to-gray-400'
        }
      case 'fantasy':
        return {
          primary: 'from-purple-600 to-pink-600',
          secondary: 'from-purple-500 to-pink-500',
          accent: 'from-purple-400 to-pink-400'
        }
      case 'dark-fantasy':
        return {
          primary: 'from-purple-700 to-red-600',
          secondary: 'from-purple-600 to-red-500',
          accent: 'from-purple-500 to-red-400'
        }
      case 'cyberpunk':
        return {
          primary: 'from-cyan-500 to-blue-500',
          secondary: 'from-cyan-400 to-blue-400',
          accent: 'from-cyan-300 to-blue-300'
        }
      default:
        return {
          primary: 'from-purple-600 to-pink-600',
          secondary: 'from-purple-500 to-pink-500',
          accent: 'from-purple-400 to-pink-400'
        }
    }
  }

  const colors = getAccentColors()

  const handleSubmit = async () => {
    if (!playerInput.trim() || isLoading || loadingState.isLoading) return

    // Check network connectivity
    if (!isOnline) {
      showErrorToast('Cannot send message - you are currently offline', {
        context: 'Offline',
        persistent: false
      })
      return
    }

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

    // Real AI response integration with comprehensive error handling
    try {
      setAiError(null)
      setLoadingState({ isLoading: true, status: 'Connecting to AI...', progress: 10 })

      const interactionRequest: InteractionRequest = {
        input: playerInput,
        mode: mode === 'god' ? 'god' : 'character'
      }

      setLoadingState({ isLoading: true, status: 'Processing your input...', progress: 30 })

      const aiResponse = await handleAsyncError(
        () => apiService.sendInteraction(campaign.id, interactionRequest),
        {
          context: 'AI Game Response',
          showToast: false,
          retryOptions: {
            maxRetries: 2,
            retryDelay: 2000,
            exponentialBackoff: true,
            shouldRetry: (error, retryCount) => {
              // Retry on network errors, timeouts, or server errors
              const errorMessage = error?.message?.toLowerCase() || ''
              const shouldRetry = errorMessage.includes('network') ||
                errorMessage.includes('timeout') ||
                errorMessage.includes('fetch') ||
                error?.status >= 500 ||
                error?.status === 429

              if (shouldRetry) {
                setLoadingState({
                  isLoading: true,
                  status: `Connection failed. Retrying in ${Math.ceil((2000 * Math.pow(2, retryCount)) / 1000)}s...`,
                  progress: 50 + (retryCount * 20)
                })
              }

              return shouldRetry
            }
          },
          onLoadingChange: (loading) => {
            setLoadingState(loading)
          },
          onRetry: (currentRetry, maxRetries) => {
            setRetryCount(currentRetry)
            setLoadingState({
              isLoading: true,
              status: `Retry ${currentRetry}/${maxRetries}...`,
              progress: 40 + (currentRetry * 15)
            })
          }
        }
      )

      setLoadingState({ isLoading: true, status: 'Processing AI response...', progress: 80 })

      if (aiResponse && aiResponse.success) {
        // Create AI response entry with enhanced content handling
        const aiEntry: StoryEntry = {
          id: (Date.now() + 1).toString(),
          type: 'narration',
          content: aiResponse.god_mode_response || aiResponse.narrative || aiResponse.response || 'The AI provided a response, but it was empty.',
          timestamp: new Date().toISOString(),
          author: 'ai',
          dice_rolls: aiResponse.dice_rolls
        }

        const warningEntries: StoryEntry[] = Array.isArray(aiResponse.system_warnings) && aiResponse.system_warnings.length > 0
          ? [
              {
                id: `warnings-${Date.now()}`,
                type: 'system',
                content: `⚠️ System warnings:\n${aiResponse.system_warnings.map((w: any) => `- ${String(w)}`).join('\n')}`,
                timestamp: new Date().toISOString(),
                author: 'system'
              }
            ]
          : []
        setStory(prev => [...prev, aiEntry, ...warningEntries])
        setRetryCount(0)
        setLastFailedInput('')

        // Add rewards box if XP was awarded
        if (aiResponse.rewards_box && (aiResponse.rewards_box.xp_gained || 0) > 0) {
          const rb = aiResponse.rewards_box
          const lootText = rb.loot && rb.loot.length > 0 && rb.loot[0] !== 'None'
            ? rb.loot.join(', ')
            : null
          const goldText = rb.gold && rb.gold > 0 ? `${rb.gold} gold` : null
          const levelUpText = rb.level_up_available ? ' 🎉 LEVEL UP AVAILABLE!' : ''

          let rewardsContent = `✨ REWARDS (${rb.source || 'earned'}): +${rb.xp_gained} XP`
          if (rb.current_xp !== undefined && rb.next_level_xp !== undefined) {
            rewardsContent += ` | XP: ${rb.current_xp}/${rb.next_level_xp}`
            if (rb.progress_percent !== undefined) {
              rewardsContent += ` (${Math.round(rb.progress_percent)}%)`
            }
          }
          if (goldText || lootText) {
            rewardsContent += ` | Loot: ${[goldText, lootText].filter(Boolean).join(', ')}`
          }
          rewardsContent += levelUpText

          const rewardsEntry: StoryEntry = {
            id: (Date.now() + 3).toString(),
            type: 'rewards',
            content: rewardsContent,
            timestamp: new Date().toISOString(),
            author: 'system'
          }
          setStory(prev => [...prev, rewardsEntry])
        }

        setLoadingState({ isLoading: false, status: 'Success!', progress: 100 })
        showSuccessToast('AI response received', { context: 'Game', duration: 2000 })
      } else {
        // Handle API success=false responses
        const errorMessage = aiResponse?.error || 'AI failed to generate a response'
        console.error('AI API returned success=false:', aiResponse)
        throw new Error(errorMessage)
      }

    } catch (error: any) {
      const errorMessage = error?.message || 'An unexpected error occurred while getting AI response'
      setAiError(errorMessage)
      setLastFailedInput(playerInput)

      // Create error entry in story
      const errorEntry: StoryEntry = {
        id: (Date.now() + 1).toString(),
        type: 'error',
        content: `❌ AI Error: ${errorMessage}. You can retry this action.`,
        timestamp: new Date().toISOString(),
        author: 'system',
        isError: true,
        isRetryable: true,
        originalInput: playerInput
      }

      setStory(prev => [...prev, errorEntry])

      // Show error toast with actionable retry option
      showErrorToast(
        `AI response failed: ${errorMessage}`,
        {
          actionable: true,
          context: 'Game AI',
          persistent: false
        }
      )

      setLoadingState({ isLoading: false })
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickAction = (action: string) => {
    setPlayerInput(action)
  }

  const handleRetryAI = async (originalInput?: string) => {
    const inputToRetry = originalInput || lastFailedInput || playerInput
    if (!inputToRetry.trim()) return

    // Remove the last error entry from story
    setStory(prev => prev.filter(entry => !(entry.isError && entry.originalInput === inputToRetry)))

    // Temporarily set input and trigger AI response
    const currentInput = playerInput
    setPlayerInput(inputToRetry)

    // Create user action entry for retry
    const retryUserAction: StoryEntry = {
      id: Date.now().toString(),
      type: 'action',
      content: `${inputToRetry} 🔄`,
      timestamp: new Date().toISOString(),
      author: 'player'
    }

    setStory(prev => [...prev, retryUserAction])
    setIsLoading(true)

    // Call the same AI logic with the retry input
    try {
      setAiError(null)
      setLoadingState({ isLoading: true, status: 'Retrying AI request...', progress: 10 })

      const interactionRequest: InteractionRequest = {
        input: inputToRetry,
        mode: mode === 'god' ? 'god' : 'character'
      }

      const aiResponse = await handleAsyncError(
        () => apiService.sendInteraction(campaign.id, interactionRequest),
        {
          context: 'AI Game Response Retry',
          showToast: false,
          retryOptions: {
            maxRetries: 1, // Fewer retries for manual retries
            retryDelay: 1000,
            exponentialBackoff: false
          },
          onLoadingChange: (loading) => {
            setLoadingState(loading)
          }
        }
      )

      if (aiResponse && aiResponse.success) {
        const aiEntry: StoryEntry = {
          id: (Date.now() + 1).toString(),
          type: 'narration',
          content: aiResponse.god_mode_response || aiResponse.narrative || aiResponse.response || 'The AI provided a response, but it was empty.',
          timestamp: new Date().toISOString(),
          author: 'ai',
          dice_rolls: aiResponse.dice_rolls
        }

        const warningEntries: StoryEntry[] = Array.isArray(aiResponse.system_warnings) && aiResponse.system_warnings.length > 0
          ? [
              {
                id: `warnings-${Date.now()}`,
                type: 'system',
                content: `⚠️ System warnings:\n${aiResponse.system_warnings.map((w: any) => `- ${String(w)}`).join('\n')}`,
                timestamp: new Date().toISOString(),
                author: 'system'
              }
            ]
          : []
        setStory(prev => [...prev, aiEntry, ...warningEntries])
        setRetryCount(0)
        setLastFailedInput('')
        setAiError(null)

        showSuccessToast('AI response received on retry!', { context: 'Game Retry', duration: 3000 })
      } else {
        throw new Error(aiResponse?.error || 'AI failed to generate a response on retry')
      }

    } catch (error: any) {
      const errorMessage = error?.message || 'Retry failed'

      const errorEntry: StoryEntry = {
        id: (Date.now() + 1).toString(),
        type: 'error',
        content: `❌ Retry failed: ${errorMessage}. The AI service may be temporarily unavailable.`,
        timestamp: new Date().toISOString(),
        author: 'system',
        isError: true,
        isRetryable: false
      }

      setStory(prev => [...prev, errorEntry])
      showErrorToast(`Retry failed: ${errorMessage}`, { context: 'Game Retry' })
    } finally {
      setIsLoading(false)
      setLoadingState({ isLoading: false })
      setPlayerInput(currentInput) // Restore original input
    }
  }

  // Listen for retry events from error toasts
  useEffect(() => {
    const handleRetryEvent = (event: any) => {
      if (event.detail?.context === 'Game AI' && lastFailedInput) {
        handleRetryAI(lastFailedInput)
      }
    }

    window.addEventListener('error-toast-retry', handleRetryEvent)
    return () => window.removeEventListener('error-toast-retry', handleRetryEvent)
  }, [lastFailedInput])


  const getEntryIcon = (entry: StoryEntry) => {
    switch (entry.type) {
      case 'action':
        return <MessageSquare className="w-4 h-4" />
      case 'narration':
        return <BookOpen className="w-4 h-4" />
      case 'dialogue':
        return <MessageSquare className="w-4 h-4" />
      case 'system':
        return <Settings className="w-4 h-4" />
      case 'rewards':
        return <Gift className="w-4 h-4 text-green-400" />
      case 'error':
        return <Sparkles className="w-4 h-4 text-red-400" />
      default:
        return <BookOpen className="w-4 h-4" />
    }
  }

  const getEntryStyle = (entry: StoryEntry) => {
    switch (entry.type) {
      case 'action':
        return 'bg-primary/10 border-primary/20 text-primary'
      case 'narration':
        return 'bg-card/50 border-border/50 text-card-foreground'
      case 'dialogue':
        return 'bg-accent/20 border-accent/30 text-accent-foreground'
      case 'system':
        return 'bg-muted/30 border-muted/40 text-muted-foreground'
      case 'rewards':
        return 'bg-green-500/10 border-green-500/20 text-green-400'
      case 'error':
        return 'bg-red-500/10 border-red-500/20 text-red-400'
      default:
        return 'bg-card/50 border-border/50 text-card-foreground'
    }
  }


  return (
    <div className={`min-h-screen ${getThemeGradient()} relative overflow-hidden`}>
      {/* Background effects */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-20 right-20 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 left-20 w-72 h-72 bg-accent/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="relative z-10 h-screen flex flex-col">
        {/* Header */}
        <header className="border-b border-border/20 bg-card/10 backdrop-blur-md px-6 py-4 shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={onBack}
                className="text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>

              <div>
                <h1 className="text-foreground text-xl">{campaign.title}</h1>
                <p className="text-muted-foreground text-sm">
                  {campaign.aiPersonas.join(', ')} • {story.length} actions
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Badge
                  variant="default"
                  className="cursor-default"
                >
                  <Crown className="w-3 h-3 mr-1" />
                  God Mode
                </Badge>
              </div>

              <Button variant="ghost" size="icon">
                <Download className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden">

          {/* Main Content */}
          <main className="flex-1 flex flex-col">
            {/* Story Area */}
            <div className="flex-1 p-6 overflow-hidden">
              <ScrollArea ref={scrollAreaRef} className="h-full">
                <div className="space-y-4 pb-6">
                  {story.map((entry) => (
                    <Card
                      key={entry.id}
                      className={`${getEntryStyle(entry)} backdrop-blur-sm transition-all duration-300 hover:shadow-lg`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-3">
                          <div className="flex items-center space-x-2 shrink-0">
                            {getEntryIcon(entry)}
                            <Badge variant="outline" className="text-xs">
                              {entry.author === 'player' ? 'You' :
                                entry.author === 'ai' ? 'GM' :
                                  entry.type === 'rewards' ? 'Rewards' : 'System'}
                            </Badge>
                          </div>
                          <div className="flex-1">
                            <p className="leading-relaxed">{entry.content}</p>
                            {/* Display dice_rolls if present (from loaded story entries) */}
                            <DiceRollDisplay dice_rolls={entry.dice_rolls} />
                            {entry.isError && entry.isRetryable && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRetryAI(entry.originalInput)}
                                className="mt-2 text-xs border-red-300 hover:bg-red-50 text-red-600"
                                disabled={isLoading}
                              >
                                <RefreshCw className={`w-3 h-3 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
                                Retry AI Request
                              </Button>
                            )
                            }
                            < p className="text-muted-foreground text-xs mt-2">
                              {new Date(entry.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}

                  {(isLoading || loadingState.isLoading) && (
                    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-3">
                          <RefreshCw className="w-4 h-4 text-primary animate-spin" />
                          <div className="flex-1">
                            <div className="flex items-center space-between">
                              <div className="flex items-center space-x-2 flex-1">
                                <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                                <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-150"></div>
                                <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-300"></div>
                                <span className="text-muted-foreground ml-2">
                                  {loadingState.status || 'The Game Master is thinking...'}
                                </span>
                              </div>
                              {retryCount > 0 && (
                                <Badge variant="outline" className="text-xs ml-2">
                                  Retry {retryCount}
                                </Badge>
                              )}
                            </div>
                            {loadingState.progress !== undefined && loadingState.progress > 0 && (
                              <div className="mt-3">
                                <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                                  <div
                                    className="bg-primary h-2 rounded-full transition-all duration-300"
                                    style={{ width: `${Math.min(loadingState.progress, 100)}%` }}
                                  ></div>
                                </div>
                                <p className="text-xs text-muted-foreground mt-1">
                                  {Math.round(loadingState.progress)}% complete
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {aiError && !isLoading && !loadingState.isLoading && (
                    <Card className="bg-red-500/10 backdrop-blur-sm border-red-500/20">
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-3">
                          <Sparkles className="w-4 h-4 text-red-400" />
                          <div className="flex-1">
                            <p className="text-red-400 text-sm font-medium mb-2">
                              AI Service Temporarily Unavailable
                            </p>
                            <p className="text-red-300 text-xs mb-3">
                              {aiError}
                            </p>
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRetryAI()}
                                className="text-xs border-red-300 hover:bg-red-50 text-red-600"
                              >
                                <RefreshCw className="w-3 h-3 mr-1" />
                                Retry Last Request
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setAiError(null)}
                                className="text-xs text-red-400 hover:text-red-300"
                              >
                                Dismiss
                              </Button>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </ScrollArea>
            </div>

            {/* Input Area */}
            <div className="border-t border-border/20 bg-card/10 backdrop-blur-md p-6 space-y-4">
              {/* Action Suggestions */}
              {showSuggestions && (
                <div className="flex flex-wrap gap-2">
                  {actionSuggestions.map((suggestion, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      className="border-border/50 hover:bg-card/20 text-xs"
                      onClick={() => handleQuickAction(suggestion.text)}
                    >
                      <suggestion.icon className="w-3 h-3 mr-1" />
                      {suggestion.text}
                    </Button>
                  ))}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowSuggestions(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Hide suggestions
                  </Button>
                </div>
              )}

              {/* Connection Status */}
              {(aiError || !isOnline) && (
                <div className={`mb-3 p-3 rounded-md ${!isOnline
                  ? 'bg-red-500/10 border border-red-500/20'
                  : 'bg-yellow-500/10 border border-yellow-500/20'
                  }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Sparkles className={`w-4 h-4 ${!isOnline ? 'text-red-400' : 'text-yellow-400'
                        }`} />
                      <span className={`text-sm font-medium ${!isOnline ? 'text-red-400' : 'text-yellow-400'
                        }`}>
                        {!isOnline
                          ? 'No internet connection - AI responses unavailable'
                          : 'AI connection issues detected - some features may be limited'
                        }
                      </span>
                    </div>
                    {isOnline && aiError && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setAiError(null)}
                        className="text-xs text-yellow-400 hover:text-yellow-300"
                      >
                        Dismiss
                      </Button>
                    )}
                  </div>
                </div>
              )}

              {/* Input Form */}
              <div className="flex space-x-4">
                <div className="flex-1 relative">
                  <Textarea
                    ref={textareaRef}
                    value={playerInput}
                    onChange={(e) => setPlayerInput(e.target.value)}
                    placeholder="Describe what happens next..."
                    className="min-h-[80px] resize-none bg-card/50 backdrop-blur-sm border-border/50 focus:border-primary/50"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSubmit()
                      }
                    }}
                  />

                  {/* Character counter */}
                  <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
                    {playerInput.length}/500
                  </div>
                </div>

                <div className="flex flex-col space-y-2">
                  <Button
                    onClick={handleSubmit}
                    disabled={!playerInput.trim() || isLoading || loadingState.isLoading || !isOnline}
                    className={`bg-gradient-to-r ${colors.primary} hover:opacity-90 px-6 relative`}
                  >
                    {(isLoading || loadingState.isLoading) ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        {loadingState.status ? 'Processing...' : 'Sending...'}
                      </>
                    ) : !isOnline ? (
                      <>
                        <Sparkles className="w-4 h-4 mr-2 opacity-50" />
                        Offline
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Continue
                      </>
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    size="icon"
                    className="border-border/50 hover:bg-card/20"
                    onClick={() => setPlayerInput('')}
                  >
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Mode Info */}
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Crown className="w-4 h-4" />
                    <span>God Mode • You control the narrative</span>
                  </div>

                  {/* Network Status Indicator */}
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
                    <span className={`text-xs ${isOnline ? 'text-green-400' : 'text-red-400'}`}>
                      {isOnline ? 'AI Online' : 'AI Offline'}
                    </span>
                  </div>

                  {/* AI Status */}
                  {aiError && (
                    <div className="flex items-center space-x-1">
                      <Sparkles className="w-3 h-3 text-yellow-400" />
                      <span className="text-xs text-yellow-400">AI Issues</span>
                    </div>
                  )}
                </div>

                {!showSuggestions && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowSuggestions(true)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <Sparkles className="w-3 h-3 mr-1" />
                    Show suggestions
                  </Button>
                )}
              </div>
            </div>
          </main>
        </div>
      </div >
    </div >
  )
}
