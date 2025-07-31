'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Textarea } from './ui/textarea'
import { Separator } from './ui/separator'
import { ScrollArea } from './ui/scroll-area'
import {
  ArrowLeft,
  Send,
  Dice6,
  User,
  Crown,
  Sword,
  Shield,
  Heart,
  Zap,
  BookOpen,
  Settings,
  Download,
  RefreshCw,
  Lightbulb,
  MessageSquare,
  Eye,
  Target,
  Move,
  Sparkles
} from 'lucide-react'
import type { User, Campaign, Theme } from '../App'

interface GameViewProps {
  user: User
  campaign: Campaign
  theme: Theme
  onUpdateCampaign: (campaign: Campaign) => void
  onBack: () => void
}

interface StoryEntry {
  id: string
  type: 'narration' | 'action' | 'dialogue' | 'system'
  content: string
  timestamp: string
  author?: 'player' | 'ai' | 'system'
}

interface Character {
  name: string
  level: number
  hp: number
  maxHp: number
  ac: number
  class: string
  status: 'healthy' | 'injured' | 'critical'
}

export function GameView({ user, campaign, theme, onUpdateCampaign, onBack }: GameViewProps) {
  const [story, setStory] = useState<StoryEntry[]>([
    {
      id: '1',
      type: 'system',
      content: `Welcome to ${campaign.title}! Your adventure begins now...`,
      timestamp: new Date().toISOString(),
      author: 'system'
    },
    {
      id: '2',
      type: 'narration',
      content: `You find yourself standing at the edge of a misty forest. Ancient trees tower above you, their branches intertwining to form a natural canopy that blocks most of the sunlight. The air is thick with the scent of moss and wildflowers. A narrow path winds deeper into the woods, disappearing around a bend. You can hear the distant sound of running water and the occasional chirp of unseen birds.`,
      timestamp: new Date().toISOString(),
      author: 'ai'
    }
  ])

  const [playerInput, setPlayerInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [character] = useState<Character>({
    name: 'Adventurer',
    level: 1,
    hp: 12,
    maxHp: 15,
    ac: 14,
    class: 'Fighter',
    status: 'injured'
  })
  const [mode, setMode] = useState<'character' | 'god'>('character')
  const [showSuggestions, setShowSuggestions] = useState(true)

  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const actionSuggestions = [
    { icon: Eye, text: "Look around for clues", type: "observation" },
    { icon: Move, text: "Follow the forest path", type: "movement" },
    { icon: MessageSquare, text: "Call out to see if anyone responds", type: "social" },
    { icon: Target, text: "Search for tracks or signs", type: "investigation" }
  ]

  const quickActions = [
    { icon: Dice6, text: "Roll for perception", action: () => handleQuickAction("I roll to perceive my surroundings") },
    { icon: Sword, text: "Draw weapon", action: () => handleQuickAction("I draw my weapon and prepare for danger") },
    { icon: Lightbulb, text: "Use a skill", action: () => handleQuickAction("I use my skills to") },
  ]

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

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: StoryEntry = {
        id: (Date.now() + 1).toString(),
        type: 'narration',
        content: generateAIResponse(playerInput),
        timestamp: new Date().toISOString(),
        author: 'ai'
      }

      setStory(prev => [...prev, aiResponse])
      setIsLoading(false)

      // Update campaign
      const updatedCampaign = {
        ...campaign,
        lastPlayed: new Date().toISOString(),
        storyLength: campaign.storyLength + 1
      }
      onUpdateCampaign(updatedCampaign)
    }, 2000)
  }

  const handleQuickAction = (action: string) => {
    setPlayerInput(action)
  }

  const generateAIResponse = (input: string): string => {
    const responses = [
      "As you venture forward, the forest seems to come alive around you. Leaves rustle mysteriously overhead, and you catch glimpses of small creatures darting between the trees. The path ahead splits into two directions - one leading uphill toward what appears to be ruins, the other descending toward the sound of water.",
      "Your keen observation reveals fresh footprints in the soft earth - humanoid, but larger than normal. They seem to lead deeper into the forest. Suddenly, you hear a branch snap behind you, and you spin around to see a pair of glowing eyes watching you from the shadows.",
      "The forest responds to your call with an eerie silence. Then, slowly, a melodic voice drifts through the trees: 'Lost traveler, the path you seek is not the one beneath your feet.' A figure emerges from behind an ancient oak - an ethereal being with bark-like skin and leaves for hair.",
    ]
    return responses[Math.floor(Math.random() * responses.length)]
  }

  const getEntryIcon = (entry: StoryEntry) => {
    switch (entry.type) {
      case 'action':
        return <User className="w-4 h-4" />
      case 'narration':
        return <BookOpen className="w-4 h-4" />
      case 'dialogue':
        return <MessageSquare className="w-4 h-4" />
      case 'system':
        return <Settings className="w-4 h-4" />
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
      default:
        return 'bg-card/50 border-border/50 text-card-foreground'
    }
  }

  const getCharacterStatusColor = () => {
    switch (character.status) {
      case 'healthy':
        return 'text-green-400'
      case 'injured':
        return 'text-yellow-400'
      case 'critical':
        return 'text-red-400'
      default:
        return 'text-gray-400'
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
                  variant={mode === 'character' ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => setMode('character')}
                >
                  <User className="w-3 h-3 mr-1" />
                  Character Mode
                </Badge>
                <Badge
                  variant={mode === 'god' ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => setMode('god')}
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
          {/* Sidebar - Character Info */}
          <aside className="w-80 border-r border-border/20 bg-card/5 backdrop-blur-sm p-6 overflow-y-auto">
            <Card className="bg-card/50 backdrop-blur-sm border-border/50 mb-6">
              <CardHeader>
                <CardTitle className="text-lg flex items-center space-x-2">
                  <div className={`w-8 h-8 bg-gradient-to-r ${colors.primary} rounded-lg flex items-center justify-center`}>
                    <User className="w-4 h-4 text-white" />
                  </div>
                  <span>{character.name}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Level</span>
                  <Badge variant="secondary">{character.level}</Badge>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Class</span>
                  <span className="text-foreground">{character.class}</span>
                </div>

                <Separator className="bg-border/30" />

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Heart className={`w-4 h-4 ${getCharacterStatusColor()}`} />
                      <span className="text-muted-foreground">HP</span>
                    </div>
                    <span className="text-foreground">{character.hp}/{character.maxHp}</span>
                  </div>

                  <div className="w-full bg-muted/30 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full bg-gradient-to-r ${
                        character.hp / character.maxHp > 0.6 ? 'from-green-500 to-green-400' :
                        character.hp / character.maxHp > 0.3 ? 'from-yellow-500 to-yellow-400' :
                        'from-red-500 to-red-400'
                      }`}
                      style={{ width: `${(character.hp / character.maxHp) * 100}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Shield className="w-4 h-4 text-blue-400" />
                      <span className="text-muted-foreground">AC</span>
                    </div>
                    <span className="text-foreground">{character.ac}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="bg-card/50 backdrop-blur-sm border-border/50">
              <CardHeader>
                <CardTitle className="text-lg flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-accent" />
                  <span>Quick Actions</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {quickActions.map((action, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    className="w-full justify-start text-left h-auto p-3 hover:bg-accent/10"
                    onClick={action.action}
                  >
                    <action.icon className="w-4 h-4 mr-2 shrink-0" />
                    <span className="text-sm">{action.text}</span>
                  </Button>
                ))}
              </CardContent>
            </Card>
          </aside>

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
                               entry.author === 'ai' ? 'GM' : 'System'}
                            </Badge>
                          </div>
                          <div className="flex-1">
                            <p className="leading-relaxed">{entry.content}</p>
                            <p className="text-muted-foreground text-xs mt-2">
                              {new Date(entry.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}

                  {isLoading && (
                    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-3">
                          <RefreshCw className="w-4 h-4 text-primary animate-spin" />
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                              <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-150"></div>
                              <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-300"></div>
                              <span className="text-muted-foreground ml-2">The Game Master is thinking...</span>
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

              {/* Input Form */}
              <div className="flex space-x-4">
                <div className="flex-1 relative">
                  <Textarea
                    ref={textareaRef}
                    value={playerInput}
                    onChange={(e) => setPlayerInput(e.target.value)}
                    placeholder={mode === 'character' ? "What do you do?" : "Describe what happens next..."}
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
                    disabled={!playerInput.trim() || isLoading}
                    className={`bg-gradient-to-r ${colors.primary} hover:opacity-90 px-6`}
                  >
                    <Send className="w-4 h-4 mr-2" />
                    {mode === 'character' ? 'Act' : 'Continue'}
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
                <div className="flex items-center space-x-2">
                  {mode === 'character' ? (
                    <>
                      <User className="w-4 h-4" />
                      <span>Playing as {character.name} • Press Enter to send • Shift+Enter for new line</span>
                    </>
                  ) : (
                    <>
                      <Crown className="w-4 h-4" />
                      <span>God Mode • You control the narrative</span>
                    </>
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
      </div>
    </div>
  )
}
