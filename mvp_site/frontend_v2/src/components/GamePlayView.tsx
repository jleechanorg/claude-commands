import { useState, useRef, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent } from './ui/card'
import { Badge } from './ui/badge'
import { Textarea } from './ui/textarea'
import { ScrollArea } from './ui/scroll-area'
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
  Sparkles
} from 'lucide-react'

interface GamePlayViewProps {
  onBack: () => void
  campaignTitle: string
}

interface StoryEntry {
  id: string
  type: 'narration' | 'action' | 'dialogue' | 'system' | 'choices'
  content: string
  timestamp: string
  author: 'player' | 'ai' | 'system'
  choices?: string[]
}

export function GamePlayView({ onBack, campaignTitle }: GamePlayViewProps) {
  const [story, setStory] = useState<StoryEntry[]>([
    {
      id: '1',
      type: 'system',
      content: `Welcome to ${campaignTitle}! Your adventure begins now...`,
      timestamp: new Date().toISOString(),
      author: 'system'
    },
    {
      id: '2',
      type: 'narration',
      content: `And above all, the "Manifest Shadow Servant" was a cold, precise eye. Its reconnaissance reports were chillingly accurate: a detailed map of the Bastion's internal layout, including patrol routes, key guard shifts, and the precise location of the "Sacred Sunstone," the relic radiating the Bastion's core light. It had even identified a series of little-used maintenance tunnels beneath the structure, offering a covert entry point.

Shadowheart opened her eyes, a grim satisfaction settling over her. The data was clear. The multi-pronged assault was underway, each Justiciar a specialized tool, and her Shadow Servant the perfect scout. The Bastion of Eternal Radiance, so full of its arrogant light, was already beginning to feel the insidious touch of Shar's encroaching night.`,
      timestamp: new Date().toISOString(),
      author: 'ai'
    },
    {
      id: '3',
      type: 'choices',
      content: `The initial intelligence and operational reports from the Justiciars and Manifest Shadow Servant are positive. The strategy is well underway, and immediate vulnerabilities have been identified. The Bastion is indeed complacent.

The Bastion of Eternal Radiance is proving to be less fortified against insidious attacks than expected, its faith in Lathander blinding it to the shadows.`,
      timestamp: new Date().toISOString(),
      author: 'ai',
      choices: [
        'Evaluate New Recruits: Focus on the desperate individuals Roric\'s overt displays have attracted, consolidating their loyalty to Shar.',
        'Exploit Supply Lines: Direct Thane and Kaelen to immediately exploit the identified vulnerabilities in the Bastion\'s supply lines.',
        'Intensify Psychological Warfare: Instruct Seraphina to escalate her efforts to sow despair and doubt within the Bastion\'s ranks.',
        'Plan Covert Entry: Utilize the Manifest Shadow Servant\'s detailed intel to prepare a covert entry for a personal strike or to send a smaller, elite force.',
        'Custom Action'
      ]
    }
  ])

  const [playerInput, setPlayerInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSoundEnabled, setIsSoundEnabled] = useState(true)
  const [mode, setMode] = useState<'character' | 'god'>('character')

  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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
    }, 2000)
  }

  const handleChoiceClick = (choice: string) => {
    setPlayerInput(choice)
    textareaRef.current?.focus()
  }



  const generateAIResponse = (input: string): string => {
    const responses = [
      "Your strategic decision proves effective. The shadows deepen around the Bastion as your operatives move into position. The faithful within grow increasingly uneasy, their prayers becoming more desperate as doubt creeps into their hearts.",
      "The operation unfolds smoothly. Your agents report back with updates on their progress, each piece of intelligence revealing new opportunities to exploit. The Bastion's defenses, once thought impregnable, show clear vulnerabilities.",
      "As your plan advances, unexpected complications arise. A patrol changes its route, forcing your operatives to adapt. However, this setback reveals an even more promising avenue of approach that had previously gone unnoticed.",
      "The psychological warfare begins to take its toll. Reports reach you of increased anxiety among the Bastion's defenders, whispered conversations about strange shadows and unexplained sounds in the night. Your influence spreads like a creeping darkness.",
      "Your tactical approach yields immediate results. The supply lines prove more vulnerable than anticipated, and your operatives successfully implement the first phase of disruption. The Bastion's resources begin to strain under the subtle assault."
    ]
    return responses[Math.floor(Math.random() * responses.length)]
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

        <div className="max-w-5xl mx-auto px-6 py-6">
          {/* Story Area */}
          <div className="mb-6">
            <ScrollArea ref={scrollAreaRef} className="h-[60vh] rounded-lg">
              <div className="space-y-4 pr-4">
                {story.map((entry) => renderStoryEntry(entry))}

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
                  <div className={`w-3 h-3 rounded-full ${mode === 'character' ? 'bg-purple-500' : 'bg-purple-300'}`}></div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setMode('character')}
                    className={`${mode === 'character' ? 'text-purple-700 bg-purple-100' : 'text-purple-600'} hover:bg-purple-100`}
                  >
                    <User className="w-4 h-4 mr-1" />
                    Character Mode
                  </Button>
                </div>

                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${mode === 'god' ? 'bg-purple-500' : 'bg-purple-300'}`}></div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setMode('god')}
                    className={`${mode === 'god' ? 'text-purple-700 bg-purple-100' : 'text-purple-600'} hover:bg-purple-100`}
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
  )
}
