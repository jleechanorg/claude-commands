import { useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Plus, Users, Calendar, Sword, Shield, Crown, BookOpen, Settings, Play } from 'lucide-react'

interface Campaign {
  id: string
  title: string
  description: string
  theme: 'fantasy' | 'cyberpunk' | 'dark-fantasy'
  players: number
  maxPlayers: number
  lastPlayed: string
  status: 'active' | 'recruiting' | 'completed'
  difficulty: 'beginner' | 'intermediate' | 'advanced'
}

const mockCampaigns: Campaign[] = [
  {
    id: '1',
    title: 'The Dragon\'s Hoard',
    description: 'A classic fantasy adventure where brave heroes must infiltrate an ancient dragon\'s lair to recover stolen treasures and save the kingdom.',
    theme: 'fantasy',
    players: 4,
    maxPlayers: 6,
    lastPlayed: '2 days ago',
    status: 'active',
    difficulty: 'intermediate'
  },
  {
    id: '2',
    title: 'Neon Shadows',
    description: 'In the sprawling megacity of Neo-Tokyo 2087, corporate espionage and cyber-enhanced mercenaries clash in the digital underground.',
    theme: 'cyberpunk',
    players: 3,
    maxPlayers: 5,
    lastPlayed: '1 week ago',
    status: 'recruiting',
    difficulty: 'advanced'
  },
  {
    id: '3',
    title: 'The Cursed Crown',
    description: 'Dark magic has corrupted the royal bloodline. Navigate political intrigue and supernatural horrors in this gothic fantasy campaign.',
    theme: 'dark-fantasy',
    players: 5,
    maxPlayers: 6,
    lastPlayed: '3 days ago',
    status: 'active',
    difficulty: 'beginner'
  }
]

const themeColors = {
  fantasy: 'bg-gradient-to-br from-green-500/20 to-emerald-600/20 border-green-500/30',
  cyberpunk: 'bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border-cyan-500/30',
  'dark-fantasy': 'bg-gradient-to-br from-purple-500/20 to-red-600/20 border-purple-500/30'
}

const statusColors = {
  active: 'bg-green-500/20 text-green-300 border-green-500/30',
  recruiting: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  completed: 'bg-gray-500/20 text-gray-300 border-gray-500/30'
}

const difficultyIcons = {
  beginner: Shield,
  intermediate: Sword,
  advanced: Crown
}

interface CampaignListProps {
  onPlayCampaign: (campaignTitle: string) => void
}

export function CampaignList({ onPlayCampaign }: CampaignListProps) {
  const [campaigns] = useState<Campaign[]>(mockCampaigns)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl text-white mb-2">Your Campaigns</h1>
            <p className="text-purple-200">Choose your adventure or create a new one</p>
          </div>
          <Button
            size="lg"
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create New Campaign
          </Button>
        </div>

        {/* Campaign Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {campaigns.map((campaign) => {
            const DifficultyIcon = difficultyIcons[campaign.difficulty]

            return (
              <Card
                key={campaign.id}
                className={`bg-black/60 backdrop-blur-sm border hover:bg-black/70 transition-all duration-300 hover:scale-105 ${themeColors[campaign.theme]}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start mb-2">
                    <CardTitle className="text-white text-xl">{campaign.title}</CardTitle>
                    <Badge className={`${statusColors[campaign.status]} capitalize`}>
                      {campaign.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-purple-200">
                    <DifficultyIcon className="w-4 h-4" />
                    <span className="capitalize">{campaign.difficulty}</span>
                    <span className="text-purple-300/50">•</span>
                    <span className="capitalize">{campaign.theme.replace('-', ' ')}</span>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <p className="text-purple-100 text-sm leading-relaxed line-clamp-3">
                    {campaign.description}
                  </p>

                  <div className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2 text-purple-200">
                      <Users className="w-4 h-4" />
                      <span>{campaign.players}/{campaign.maxPlayers} players</span>
                    </div>
                    <div className="flex items-center gap-2 text-purple-200">
                      <Calendar className="w-4 h-4" />
                      <span>{campaign.lastPlayed}</span>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-2">
                    <Button
                      variant="default"
                      size="sm"
                      className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
                      onClick={() => onPlayCampaign(campaign.title)}
                    >
                      <Play className="w-4 h-4 mr-2" />
                      {campaign.status === 'recruiting' ? 'Join' : 'Continue'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-purple-500/30 text-purple-200 hover:bg-purple-500/20"
                    >
                      <Settings className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}

          {/* Create New Campaign Card */}
          <Card className="bg-black/40 backdrop-blur-sm border-dashed border-purple-500/50 hover:border-purple-400/70 hover:bg-black/50 transition-all duration-300 flex items-center justify-center min-h-[300px] cursor-pointer group">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-purple-600/20 rounded-full flex items-center justify-center group-hover:bg-purple-600/30 transition-colors">
                <Plus className="w-8 h-8 text-purple-300" />
              </div>
              <h3 className="text-white text-xl mb-2">Start New Adventure</h3>
              <p className="text-purple-200 text-sm">Create a custom campaign with AI assistance</p>
            </div>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button
            variant="outline"
            size="lg"
            className="border-purple-500/30 text-purple-200 hover:bg-purple-500/20 h-16"
          >
            <BookOpen className="w-6 h-6 mr-3" />
            Browse Templates
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="border-purple-500/30 text-purple-200 hover:bg-purple-500/20 h-16"
          >
            <Users className="w-6 h-6 mr-3" />
            Find Players
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="border-purple-500/30 text-purple-200 hover:bg-purple-500/20 h-16"
          >
            <Crown className="w-6 h-6 mr-3" />
            AI Game Master
          </Button>
        </div>
      </div>
    </div>
  )
}
