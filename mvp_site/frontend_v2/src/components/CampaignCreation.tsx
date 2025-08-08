'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Badge } from './ui/badge'
import { Switch } from './ui/switch'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Sparkles,
  Crown,
  Brain,
  Target,
  Users,
  Globe,
  Wand2,
  Shield,
  Sword,
  BookOpen,
  Dice6,
  User,
  Play
} from 'lucide-react'
import type { Campaign, Theme } from '../types'

interface CampaignCreationProps {
  onCreateCampaign: (campaign: Omit<Campaign, 'id' | 'createdAt' | 'lastPlayed' | 'storyLength'>) => void
  onBack: () => void
  theme: Theme
}

type CreationStep = 'basic' | 'personas' | 'world' | 'companions' | 'review'

const aiPersonas = [
  {
    id: 'narrative',
    name: "Jeff's Narrative Flair",
    description: 'Focuses on rich storytelling, dramatic moments, and emotional depth',
    icon: BookOpen,
    color: 'from-purple-500 to-pink-500',
    features: ['Rich descriptions', 'Character development', 'Emotional storytelling']
  },
  {
    id: 'mechanical',
    name: "Jeff's Mechanical Precision",
    description: 'Emphasizes rules accuracy, tactical combat, and strategic gameplay',
    icon: Target,
    color: 'from-blue-500 to-cyan-500',
    features: ['Rules accuracy', 'Tactical combat', 'Strategic depth']
  },
  {
    id: 'calibration',
    name: "Jeff's Calibration Rigor",
    description: 'Balances challenge perfectly and adapts to player preferences',
    icon: Brain,
    color: 'from-green-500 to-emerald-500',
    features: ['Perfect balance', 'Adaptive difficulty', 'Player-focused']
  }
]

export function CampaignCreation({ onCreateCampaign, onBack, theme }: CampaignCreationProps) {
  const [currentStep, setCurrentStep] = useState<CreationStep>('basic')
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    aiPersonas: [] as string[],
    hasCompanions: false,
    useDefaultWorld: true,
    customWorldDescription: ''
  })

  const steps = [
    { id: 'basic', title: 'Campaign Basics', icon: BookOpen },
    { id: 'personas', title: 'AI Personalities', icon: Crown },
    { id: 'world', title: 'World Setting', icon: Globe },
    { id: 'companions', title: 'Companions', icon: Users },
    { id: 'review', title: 'Review & Create', icon: Check }
  ]

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

  const updateFormData = (updates: Partial<typeof formData>) => {
    setFormData(prev => ({ ...prev, ...updates }))
  }

  const togglePersona = (personaName: string) => {
    const isSelected = formData.aiPersonas.includes(personaName)
    if (isSelected) {
      updateFormData({
        aiPersonas: formData.aiPersonas.filter(p => p !== personaName)
      })
    } else {
      updateFormData({
        aiPersonas: [...formData.aiPersonas, personaName]
      })
    }
  }

  const canProceed = () => {
    switch (currentStep) {
      case 'basic':
        return formData.title.trim() && formData.description.trim()
      case 'personas':
        return formData.aiPersonas.length > 0
      case 'world':
        return formData.useDefaultWorld || formData.customWorldDescription.trim()
      case 'companions':
        return true
      case 'review':
        return true
      default:
        return false
    }
  }

  const nextStep = () => {
    const stepOrder: CreationStep[] = ['basic', 'personas', 'world', 'companions', 'review']
    const currentIndex = stepOrder.indexOf(currentStep)
    if (currentIndex < stepOrder.length - 1) {
      setCurrentStep(stepOrder[currentIndex + 1])
    }
  }

  const prevStep = () => {
    const stepOrder: CreationStep[] = ['basic', 'personas', 'world', 'companions', 'review']
    const currentIndex = stepOrder.indexOf(currentStep)
    if (currentIndex > 0) {
      setCurrentStep(stepOrder[currentIndex - 1])
    }
  }

  const handleCreate = () => {
    onCreateCampaign(formData)
  }

  const renderBasicStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className={`w-16 h-16 bg-gradient-to-r ${colors.primary} rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg`}>
          <BookOpen className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-2xl text-foreground mb-2">Campaign Basics</h2>
        <p className="text-muted-foreground">Give your adventure a name and story</p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="title">Campaign Title</Label>
          <Input
            id="title"
            value={formData.title}
            onChange={(e) => updateFormData({ title: e.target.value })}
            placeholder="Enter your campaign title..."
            className="bg-card/50 backdrop-blur-sm border-border/50"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Campaign Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => updateFormData({ description: e.target.value })}
            placeholder="Describe your campaign setting, theme, and goals..."
            className="min-h-[120px] bg-card/50 backdrop-blur-sm border-border/50"
          />
          <p className="text-sm text-muted-foreground">
            This helps the AI understand the tone and style of your adventure
          </p>
        </div>
      </div>
    </div>
  )

  const renderPersonasStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className={`w-16 h-16 bg-gradient-to-r ${colors.primary} rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg`}>
          <Crown className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-2xl text-foreground mb-2">Choose Your AI Game Master</h2>
        <p className="text-muted-foreground">Select one or more AI personalities to guide your adventure</p>
      </div>

      <div className="grid gap-4">
        {aiPersonas.map((persona) => {
          const isSelected = formData.aiPersonas.includes(persona.name)
          return (
            <Card
              key={persona.id}
              className={`cursor-pointer transition-all duration-300 hover:scale-[1.02] ${
                isSelected
                  ? 'bg-primary/20 border-primary/50 shadow-lg'
                  : 'bg-card/50 backdrop-blur-sm border-border/50 hover:bg-card/70'
              }`}
              onClick={() => togglePersona(persona.name)}
            >
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                  <div className={`w-12 h-12 bg-gradient-to-r ${persona.color} rounded-xl flex items-center justify-center shadow-lg`}>
                    <persona.icon className="w-6 h-6 text-white" />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-lg text-card-foreground">{persona.name}</h3>
                      {isSelected && <Check className="w-5 h-5 text-primary" />}
                    </div>

                    <p className="text-muted-foreground mb-3">{persona.description}</p>

                    <div className="flex flex-wrap gap-2">
                      {persona.features.map((feature, index) => (
                        <Badge key={index} variant="outline" className="text-xs border-primary/30 text-primary">
                          {feature}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="bg-accent/10 border border-accent/20 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Sparkles className="w-5 h-5 text-accent shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-accent-foreground">
              <span className="font-medium">Pro Tip:</span> You can select multiple personas! They'll work together to create a richer, more dynamic experience that adapts to different aspects of your adventure.
            </p>
          </div>
        </div>
      </div>
    </div>
  )

  const renderWorldStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className={`w-16 h-16 bg-gradient-to-r ${colors.primary} rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg`}>
          <Globe className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-2xl text-foreground mb-2">Choose Your World</h2>
        <p className="text-muted-foreground">Select a setting for your adventure</p>
      </div>

      <div className="space-y-4">
        {/* Default World Option */}
        <Card
          className={`cursor-pointer transition-all duration-300 hover:scale-[1.02] ${
            formData.useDefaultWorld
              ? 'bg-primary/20 border-primary/50 shadow-lg'
              : 'bg-card/50 backdrop-blur-sm border-border/50 hover:bg-card/70'
          }`}
          onClick={() => updateFormData({ useDefaultWorld: true })}
        >
          <CardContent className="p-6">
            <div className="flex items-start space-x-4">
              <div className={`w-12 h-12 bg-gradient-to-r ${colors.accent} rounded-xl flex items-center justify-center shadow-lg`}>
                <Wand2 className="w-6 h-6 text-white" />
              </div>

              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h3 className="text-lg text-card-foreground">World of Assiah</h3>
                  {formData.useDefaultWorld && <Check className="w-5 h-5 text-primary" />}
                  <Badge variant="secondary" className="text-xs">Recommended</Badge>
                </div>

                <p className="text-muted-foreground mb-3">
                  A rich fantasy realm with ancient kingdoms, mystical forests, and legendary artifacts.
                  Perfect for classic D&D adventures with established lore and locations.
                </p>

                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="text-xs border-primary/30 text-primary">High Fantasy</Badge>
                  <Badge variant="outline" className="text-xs border-primary/30 text-primary">Rich Lore</Badge>
                  <Badge variant="outline" className="text-xs border-primary/30 text-primary">Multiple Kingdoms</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Custom World Option */}
        <Card
          className={`cursor-pointer transition-all duration-300 hover:scale-[1.02] ${
            !formData.useDefaultWorld
              ? 'bg-primary/20 border-primary/50 shadow-lg'
              : 'bg-card/50 backdrop-blur-sm border-border/50 hover:bg-card/70'
          }`}
          onClick={() => updateFormData({ useDefaultWorld: false })}
        >
          <CardContent className="p-6">
            <div className="flex items-start space-x-4">
              <div className={`w-12 h-12 bg-gradient-to-r ${colors.secondary} rounded-xl flex items-center justify-center shadow-lg`}>
                <User className="w-6 h-6 text-white" />
              </div>

              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <h3 className="text-lg text-card-foreground">Custom World</h3>
                  {!formData.useDefaultWorld && <Check className="w-5 h-5 text-primary" />}
                </div>

                <p className="text-muted-foreground mb-3">
                  Create your own unique world with custom lore, locations, and themes.
                  Perfect for specific campaign ideas or alternative settings.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Custom World Description */}
        {!formData.useDefaultWorld && (
          <div className="space-y-2 mt-4">
            <Label htmlFor="world-description">Describe Your World</Label>
            <Textarea
              id="world-description"
              value={formData.customWorldDescription}
              onChange={(e) => updateFormData({ customWorldDescription: e.target.value })}
              placeholder="Describe your world's setting, history, major locations, and unique elements..."
              className="min-h-[120px] bg-card/50 backdrop-blur-sm border-border/50"
            />
            <p className="text-sm text-muted-foreground">
              Include details about the world's tone, technology level, magic system, and key locations
            </p>
          </div>
        )}
      </div>
    </div>
  )

  const renderCompanionsStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className={`w-16 h-16 bg-gradient-to-r ${colors.primary} rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg`}>
          <Users className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-2xl text-foreground mb-2">AI Companions</h2>
        <p className="text-muted-foreground">Choose whether to include AI-controlled party members</p>
      </div>

      <div className="space-y-4">
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="text-lg text-card-foreground mb-2">Include AI Companions</h3>
                <p className="text-muted-foreground">
                  AI companions will join your party as NPCs, helping in combat and providing
                  roleplay opportunities. They adapt to your playstyle and the story.
                </p>
              </div>
              <Switch
                checked={formData.hasCompanions}
                onCheckedChange={(checked) => updateFormData({ hasCompanions: checked })}
              />
            </div>
          </CardContent>
        </Card>

        {formData.hasCompanions && (
          <div className="grid md:grid-cols-2 gap-4">
            <Card className="bg-accent/10 border-accent/20">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3 mb-3">
                  <Sword className="w-5 h-5 text-accent" />
                  <h4 className="text-accent-foreground">Combat Support</h4>
                </div>
                <p className="text-sm text-muted-foreground">
                  Companions provide tactical assistance in fights and can help balance encounters
                </p>
              </CardContent>
            </Card>

            <Card className="bg-accent/10 border-accent/20">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3 mb-3">
                  <Shield className="w-5 h-5 text-accent" />
                  <h4 className="text-accent-foreground">Story Integration</h4>
                </div>
                <p className="text-sm text-muted-foreground">
                  Each companion has their own personality, goals, and character development
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Dice6 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-primary">
                <span className="font-medium">Note:</span> You can always add or remove companions later during your campaign.
                The AI will seamlessly integrate them into your ongoing story.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderReviewStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className={`w-16 h-16 bg-gradient-to-r ${colors.primary} rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg`}>
          <Check className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-2xl text-foreground mb-2">Review Your Campaign</h2>
        <p className="text-muted-foreground">Everything looks good? Let's start your adventure!</p>
      </div>

      <div className="space-y-4">
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BookOpen className="w-5 h-5" />
              <span>Campaign Details</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground">Title</p>
              <p className="text-foreground">{formData.title}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Description</p>
              <p className="text-foreground">{formData.description}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Crown className="w-5 h-5" />
              <span>AI Game Masters</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {formData.aiPersonas.map((persona) => (
                <Badge key={persona} variant="secondary">
                  {persona}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Globe className="w-5 h-5" />
              <span>World Setting</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {formData.useDefaultWorld ? (
              <div className="flex items-center space-x-2">
                <Badge variant="secondary">World of Assiah</Badge>
                <span className="text-muted-foreground text-sm">Default fantasy world</span>
              </div>
            ) : (
              <div>
                <Badge variant="secondary">Custom World</Badge>
                <p className="text-muted-foreground text-sm mt-2">{formData.customWorldDescription}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="w-5 h-5" />
              <span>Companions</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={formData.hasCompanions ? "secondary" : "outline"}>
              {formData.hasCompanions ? "AI Companions Enabled" : "Solo Adventure"}
            </Badge>
          </CardContent>
        </Card>
      </div>
    </div>
  )

  const renderStepContent = () => {
    switch (currentStep) {
      case 'basic':
        return renderBasicStep()
      case 'personas':
        return renderPersonasStep()
      case 'world':
        return renderWorldStep()
      case 'companions':
        return renderCompanionsStep()
      case 'review':
        return renderReviewStep()
      default:
        return null
    }
  }

  const getCurrentStepIndex = () => {
    return steps.findIndex(step => step.id === currentStep)
  }

  return (
    <div className={`min-h-screen ${getThemeGradient()} relative overflow-hidden`}>
      {/* Background effects */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-20 right-20 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 left-20 w-72 h-72 bg-accent/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-border/20 bg-card/10 backdrop-blur-md px-6 py-4">
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
                <h1 className="text-foreground text-xl">Create New Campaign</h1>
                <p className="text-muted-foreground text-sm">
                  Step {getCurrentStepIndex() + 1} of {steps.length}
                </p>
              </div>
            </div>

            {/* Progress Steps */}
            <div className="hidden md:flex items-center space-x-2">
              {steps.map((step, index) => {
                const isActive = step.id === currentStep
                const isCompleted = getCurrentStepIndex() > index

                return (
                  <div key={step.id} className="flex items-center space-x-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                      isActive ? `bg-gradient-to-r ${colors.primary} text-white` :
                      isCompleted ? 'bg-primary/20 text-primary' :
                      'bg-muted/30 text-muted-foreground'
                    }`}>
                      {isCompleted ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <step.icon className="w-4 h-4" />
                      )}
                    </div>

                    {index < steps.length - 1 && (
                      <div className={`w-8 h-0.5 transition-all duration-300 ${
                        isCompleted ? 'bg-primary' : 'bg-border/30'
                      }`} />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-6 py-8 max-w-4xl">
          <Card className="bg-card/30 backdrop-blur-sm border-border/50 shadow-2xl">
            <CardContent className="p-8">
              {renderStepContent()}
            </CardContent>
          </Card>

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8">
            <Button
              variant="outline"
              onClick={prevStep}
              disabled={getCurrentStepIndex() === 0}
              className="border-border/50 hover:bg-card/20"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Previous
            </Button>

            <div className="flex md:hidden items-center space-x-1">
              {steps.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full transition-all duration-300 ${
                    getCurrentStepIndex() >= index ? 'bg-primary' : 'bg-border/30'
                  }`}
                />
              ))}
            </div>

            {currentStep === 'review' ? (
              <Button
                onClick={handleCreate}
                disabled={!canProceed()}
                className={`bg-gradient-to-r ${colors.primary} hover:opacity-90 shadow-lg hover:shadow-xl transition-all duration-300`}
              >
                <Play className="w-4 h-4 mr-2" />
                Start Adventure
              </Button>
            ) : (
              <Button
                onClick={nextStep}
                disabled={!canProceed()}
                className={`bg-gradient-to-r ${colors.secondary} hover:opacity-90`}
              >
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
