'use client'

import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Separator } from './ui/separator'
import { ThemeSwitcher } from './ThemeSwitcher'
import { 
  Plus, 
  PlayCircle, 
  Calendar, 
  Clock, 
  Trash2, 
  BookOpen, 
  Users, 
  Crown,
  LogOut,
  Sparkles,
  Settings,
  MoreVertical,
  TrendingUp,
  Scroll,
  Sword,
  Wand2
} from 'lucide-react'

import heroImage from 'figma:asset/ecab425a7edc8f80fb8ff5feaec1011c3fd50550.png'
import type { User, Campaign, Theme } from '../App'

interface DashboardProps {
  user: User
  campaigns: Campaign[]
  theme: Theme
  onThemeChange: (theme: Theme) => void
  onLogout: () => void
  onCreateCampaign: () => void
  onSelectCampaign: (campaign: Campaign) => void
  onDeleteCampaign: (campaignId: string) => void
}

export function Dashboard({ 
  user, 
  campaigns, 
  theme,
  onThemeChange,
  onLogout, 
  onCreateCampaign, 
  onSelectCampaign, 
  onDeleteCampaign 
}: DashboardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const getTimeSince = (dateString: string) => {
    const now = new Date()
    const date = new Date(dateString)
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return `${Math.floor(diffDays / 30)} months ago`
  }

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

  const totalStoryLength = campaigns.reduce((total, campaign) => total + campaign.storyLength, 0)
  const recentCampaigns = campaigns.sort((a, b) => new Date(b.lastPlayed).getTime() - new Date(a.lastPlayed).getTime()).slice(0, 3)

  // Empty state with hero image
  if (campaigns.length === 0) {
    return (
      <div className={`min-h-screen ${getThemeGradient()} relative overflow-hidden`}>
        {/* Header */}
        <header className="border-b border-border/20 bg-card/10 backdrop-blur-md sticky top-0 z-40">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`w-10 h-10 bg-gradient-to-r ${colors.accent} rounded-xl flex items-center justify-center shadow-lg`}>
                  <Crown className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-foreground text-2xl">WorldArchitect.AI</h1>
                  <p className="text-muted-foreground text-sm">Campaign Dashboard</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-6">
                <div className="relative z-50">
                  <ThemeSwitcher currentTheme={theme} onThemeChange={onThemeChange} />
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-foreground">{user.name}</p>
                    <p className="text-muted-foreground text-sm">{user.email}</p>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={onLogout}
                    className="text-muted-foreground hover:text-foreground hover:bg-accent/10"
                  >
                    <LogOut className="w-5 h-5" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <div className="relative min-h-[calc(100vh-80px)] flex items-center justify-center">
          {/* Hero Background Image */}
          <div 
            className="absolute inset-0 bg-cover bg-no-repeat opacity-80"
            style={{ 
              backgroundImage: `url(${heroImage})`,
              backgroundPosition: 'center center'
            }}
          />
          
          {/* Dark overlay for better text readability */}
          <div className="absolute inset-0 bg-gradient-to-t from-background/95 via-background/60 to-background/30" />
          
          {/* Floating particles effect */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            {[...Array(15)].map((_, i) => (
              <div
                key={i}
                className="absolute w-1 h-1 bg-foreground/30 rounded-full animate-pulse"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 3}s`,
                  animationDuration: `${3 + Math.random() * 2}s`
                }}
              />
            ))}
          </div>

          {/* Main Content */}
          <div className="relative z-10 text-center max-w-4xl mx-auto px-6">
            {/* Welcome Message */}
            <div className="mb-12">
              <h2 className="text-5xl md:text-7xl text-foreground mb-6 leading-tight">
                Welcome, {user.name.split(' ')[0]}
              </h2>
              <p className="text-xl md:text-2xl text-muted-foreground mb-4 max-w-2xl mx-auto leading-relaxed">
                Every hero's journey begins with a single step. Create your campaign and let the AI Game Master guide you through an unforgettable adventure.
              </p>
            </div>

            {/* Main CTA - Takes up about 25% of screen height */}
            <div className="min-h-[25vh] flex items-center justify-center">
              <div className="text-center space-y-8 max-w-2xl w-full">
                {/* Title */}
                <div>
                  <h3 className="text-3xl md:text-4xl text-foreground mb-4">
                    Forge Your Legend
                  </h3>
                </div>

                {/* CTA Button */}
                <Button 
                  onClick={onCreateCampaign}
                  size="lg"
                  className={`h-16 px-12 text-xl bg-gradient-to-r ${colors.primary} hover:opacity-90 shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-110`}
                >
                  <Sparkles className="w-6 h-6 mr-3" />
                  Create Your First Campaign
                  <Sparkles className="w-6 h-6 ml-3" />
                </Button>

                {/* Features */}
                <div className="grid md:grid-cols-3 gap-6 mt-12">
                  <div className="text-center">
                    <Crown className="w-8 h-8 text-primary mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">AI Game Master</p>
                  </div>
                  <div className="text-center">
                    <BookOpen className="w-8 h-8 text-primary mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">Rich Storytelling</p>
                  </div>
                  <div className="text-center">
                    <Sword className="w-8 h-8 text-primary mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">Epic Adventures</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Regular dashboard with campaigns
  return (
    <div className={`min-h-screen ${getThemeGradient()} relative overflow-hidden`}>
      {/* Background effects */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-20 right-20 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 left-20 w-72 h-72 bg-accent/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      {/* Header */}
      <header className="border-b border-border/20 bg-card/10 backdrop-blur-md sticky top-0 z-40">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`w-10 h-10 bg-gradient-to-r ${colors.accent} rounded-xl flex items-center justify-center shadow-lg`}>
                <Crown className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-foreground text-2xl">WorldArchitect.AI</h1>
                <p className="text-muted-foreground text-sm">Campaign Dashboard</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="relative z-50">
                <ThemeSwitcher currentTheme={theme} onThemeChange={onThemeChange} />
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-foreground">{user.name}</p>
                  <p className="text-muted-foreground text-sm">{user.email}</p>
                </div>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={onLogout}
                  className="text-muted-foreground hover:text-foreground hover:bg-accent/10"
                >
                  <LogOut className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="relative z-10">
        <main className="container mx-auto px-6 py-8">
          {/* Welcome Section with Stats */}
          <div className="mb-8">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-8">
              <div>
                <h2 className="text-4xl text-foreground mb-2">
                  Welcome back, {user.name.split(' ')[0]}!
                </h2>
                <p className="text-xl text-muted-foreground">
                  Ready to continue your epic adventures?
                </p>
              </div>

              <div className="flex flex-wrap gap-4">
                <Card className="bg-card/30 backdrop-blur-sm border-border/50">
                  <CardContent className="p-4 text-center">
                    <div className="flex items-center space-x-2">
                      <Scroll className="w-5 h-5 text-primary" />
                      <div>
                        <p className="text-2xl text-foreground">{campaigns.length}</p>
                        <p className="text-sm text-muted-foreground">Campaigns</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-card/30 backdrop-blur-sm border-border/50">
                  <CardContent className="p-4 text-center">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-5 h-5 text-accent" />
                      <div>
                        <p className="text-2xl text-foreground">{totalStoryLength.toLocaleString()}</p>
                        <p className="text-sm text-muted-foreground">Story Actions</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex flex-wrap gap-4">
              <Button 
                onClick={onCreateCampaign}
                size="lg"
                className={`bg-gradient-to-r ${colors.primary} hover:opacity-90 shadow-lg hover:shadow-xl transition-all duration-300`}
              >
                <Plus className="w-5 h-5 mr-2" />
                Create New Campaign
              </Button>
              
              {recentCampaigns.length > 0 && (
                <Button 
                  onClick={() => onSelectCampaign(recentCampaigns[0])}
                  variant="outline"
                  size="lg"
                  className="border-border/50 hover:bg-card/20"
                >
                  <PlayCircle className="w-5 h-5 mr-2" />
                  Continue Latest
                </Button>
              )}
            </div>
          </div>

          {/* Campaigns Section */}
          <div className="space-y-8">
            {/* Recent Campaigns */}
            {recentCampaigns.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl text-foreground">Recent Adventures</h3>
                  <Badge variant="secondary" className="bg-accent/20 text-accent-foreground border-accent/20">
                    Last Played
                  </Badge>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                  {recentCampaigns.map((campaign) => (
                    <Card 
                      key={campaign.id} 
                      className="bg-card/40 backdrop-blur-sm border-border/50 hover:bg-card/60 transition-all duration-300 group hover:scale-[1.02] cursor-pointer shadow-lg hover:shadow-xl"
                      onClick={() => onSelectCampaign(campaign)}
                    >
                      <CardHeader className="space-y-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <Sword className="w-4 h-4 text-primary" />
                              <Badge variant="outline" className="text-xs border-primary/30 text-primary">
                                Active
                              </Badge>
                            </div>
                            <CardTitle className="text-card-foreground text-lg mb-2 line-clamp-1">
                              {campaign.title}
                            </CardTitle>
                            <CardDescription className="text-muted-foreground line-clamp-2 text-sm">
                              {campaign.description}
                            </CardDescription>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-1">
                          {campaign.aiPersonas.slice(0, 2).map((persona) => (
                            <Badge 
                              key={persona} 
                              variant="outline" 
                              className="text-xs border-secondary/30 text-secondary-foreground"
                            >
                              {persona.replace('Jeff\'s ', '')}
                            </Badge>
                          ))}
                          {campaign.aiPersonas.length > 2 && (
                            <Badge variant="outline" className="text-xs border-muted/30 text-muted-foreground">
                              +{campaign.aiPersonas.length - 2}
                            </Badge>
                          )}
                        </div>
                      </CardHeader>

                      <CardContent className="space-y-3">
                        <div className="flex items-center justify-between text-sm text-muted-foreground">
                          <div className="flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{getTimeSince(campaign.lastPlayed)}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <TrendingUp className="w-3 h-3" />
                            <span>{campaign.storyLength} actions</span>
                          </div>
                        </div>

                        <Button 
                          className={`w-full bg-gradient-to-r ${colors.secondary} hover:opacity-90 transition-all duration-300`}
                          onClick={(e) => {
                            e.stopPropagation()
                            onSelectCampaign(campaign)
                          }}
                        >
                          <PlayCircle className="w-4 h-4 mr-2" />
                          Continue Adventure
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* All Campaigns */}
            <div>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl text-foreground">All Campaigns</h3>
                <Badge variant="secondary" className="bg-accent/20 text-accent-foreground border-accent/20">
                  {campaigns.length} {campaigns.length === 1 ? 'Campaign' : 'Campaigns'}
                </Badge>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {campaigns.map((campaign) => (
                  <Card 
                    key={campaign.id} 
                    className="bg-card/30 backdrop-blur-sm border-border/50 hover:bg-card/50 transition-all duration-300 group hover:scale-[1.02] shadow-lg hover:shadow-xl"
                  >
                    <CardHeader className="space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-card-foreground text-lg mb-2 line-clamp-1">
                            {campaign.title}
                          </CardTitle>
                          <CardDescription className="text-muted-foreground line-clamp-2 text-sm">
                            {campaign.description}
                          </CardDescription>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation()
                            onDeleteCampaign(campaign.id)
                          }}
                          className="text-red-400 hover:text-red-300 hover:bg-red-400/10 opacity-0 group-hover:opacity-100 transition-all duration-300 shrink-0"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>

                      <div className="flex flex-wrap gap-1">
                        {campaign.aiPersonas.map((persona) => (
                          <Badge 
                            key={persona} 
                            variant="outline" 
                            className="text-xs border-primary/30 text-primary"
                          >
                            {persona.replace('Jeff\'s ', '')}
                          </Badge>
                        ))}
                        {campaign.hasCompanions && (
                          <Badge 
                            variant="outline" 
                            className="text-xs border-accent/30 text-accent-foreground"
                          >
                            <Users className="w-3 h-3 mr-1" />
                            Companions
                          </Badge>
                        )}
                        {campaign.useDefaultWorld && (
                          <Badge 
                            variant="outline" 
                            className="text-xs border-secondary/30 text-secondary-foreground"
                          >
                            World of Assiah
                          </Badge>
                        )}
                      </div>
                    </CardHeader>

                    <CardContent className="space-y-4">
                      <Separator className="bg-border/30" />
                      
                      <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDate(campaign.createdAt)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{getTimeSince(campaign.lastPlayed)}</span>
                        </div>
                      </div>

                      <Button 
                        onClick={() => onSelectCampaign(campaign)}
                        className={`w-full bg-gradient-to-r ${colors.secondary} hover:opacity-90 transition-all duration-300`}
                      >
                        <PlayCircle className="w-4 h-4 mr-2" />
                        Continue Adventure
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}