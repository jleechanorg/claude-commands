'use client'

import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Input } from './ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { ImageWithFallback } from './figma/ImageWithFallback'
import {
  Search,
  Shield,
  Sword,
  Book,
  Users,
  MapPin,
  Sparkles,
  Scroll,
  Crown
} from 'lucide-react'
import type { AppView } from '../App'

interface Campaign {
  id: string
  name: string
  description: string
  gameSystem: string
  playerCount: number
  level: string
  status: 'active' | 'recruiting' | 'completed'
  tags: string[]
  thumbnail?: string
  lastPlayed?: Date
}

interface Character {
  id: string
  name: string
  class: string
  level: number
  race: string
  campaign?: string
  status: 'active' | 'retired' | 'deceased'
  thumbnail?: string
}

interface SearchPageProps {
  onViewChange: (view: AppView) => void
}

export function SearchPage({ onViewChange }: SearchPageProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchType, setSearchType] = useState<'campaigns' | 'characters' | 'all'>('campaigns')
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [characters, setCharacters] = useState<Character[]>([])
  const [loading, setLoading] = useState(false)

  // Mock data for development
  useEffect(() => {
    const mockCampaigns: Campaign[] = [
      {
        id: '1',
        name: 'The Lost Mines of Phandelver',
        description: 'A classic D&D 5e adventure for new players',
        gameSystem: 'D&D 5e',
        playerCount: 4,
        level: '1-5',
        status: 'active',
        tags: ['beginner-friendly', 'classic', 'dungeon-crawl'],
        lastPlayed: new Date('2024-01-15')
      },
      {
        id: '2',
        name: 'Curse of Strahd',
        description: 'Gothic horror in the demiplane of Barovia',
        gameSystem: 'D&D 5e',
        playerCount: 5,
        level: '1-10',
        status: 'recruiting',
        tags: ['horror', 'roleplay-heavy', 'mature']
      }
    ]

    const mockCharacters: Character[] = [
      {
        id: '1',
        name: 'Aelar Moonwhisper',
        class: 'Ranger',
        level: 3,
        race: 'Elf',
        campaign: 'The Lost Mines of Phandelver',
        status: 'active'
      },
      {
        id: '2',
        name: 'Thorek Ironforge',
        class: 'Fighter',
        level: 5,
        race: 'Dwarf',
        campaign: 'Curse of Strahd',
        status: 'active'
      }
    ]

    setCampaigns(mockCampaigns)
    setCharacters(mockCharacters)
  }, [])

  const filteredCampaigns = campaigns.filter(campaign =>
    campaign.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    campaign.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    campaign.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const filteredCharacters = characters.filter(character =>
    character.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    character.class.toLowerCase().includes(searchQuery.toLowerCase()) ||
    character.race.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active': return 'default'
      case 'recruiting': return 'secondary'
      case 'completed': return 'outline'
      default: return 'outline'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-2">
            <Search className="h-8 w-8" />
            Discover Adventures
          </h1>
          <p className="text-purple-200">Find campaigns and characters in the D&D multiverse</p>
        </div>

        {/* Search Controls */}
        <Card className="mb-6 bg-black/20 border-purple-500/30">
          <CardHeader>
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <Input
                  type="text"
                  placeholder="Search campaigns, characters, or tags..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-white/10 border-purple-500/30 text-white placeholder:text-purple-300"
                />
              </div>
              <Select value={searchType} onValueChange={(value: any) => setSearchType(value)}>
                <SelectTrigger className="w-full sm:w-48 bg-white/10 border-purple-500/30 text-white">
                  <SelectValue placeholder="Search type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="campaigns">Campaigns</SelectItem>
                  <SelectItem value="characters">Characters</SelectItem>
                  <SelectItem value="all">All</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
        </Card>

        {/* Campaigns Section */}
        {(searchType === 'campaigns' || searchType === 'all') && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Shield className="h-6 w-6" />
              Campaigns ({filteredCampaigns.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredCampaigns.map((campaign) => (
                <Card key={campaign.id} className="bg-black/20 border-purple-500/30 hover:border-purple-400/50 transition-colors">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-white text-lg">{campaign.name}</CardTitle>
                        <CardDescription className="text-purple-200">{campaign.gameSystem}</CardDescription>
                      </div>
                      <Badge variant={getStatusBadgeVariant(campaign.status)}>
                        {campaign.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-purple-100 text-sm mb-3">{campaign.description}</p>
                    <div className="flex flex-wrap gap-1 mb-3">
                      {campaign.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs border-purple-500/30 text-purple-300">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    <div className="flex justify-between items-center text-sm text-purple-200">
                      <span className="flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        {campaign.playerCount} players
                      </span>
                      <span className="flex items-center gap-1">
                        <Crown className="h-4 w-4" />
                        Level {campaign.level}
                      </span>
                    </div>
                    <Button
                      className="w-full mt-3 bg-purple-600 hover:bg-purple-700"
                      onClick={() => onViewChange('campaign-details')}
                    >
                      View Campaign
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Characters Section */}
        {(searchType === 'characters' || searchType === 'all') && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Sword className="h-6 w-6" />
              Characters ({filteredCharacters.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {filteredCharacters.map((character) => (
                <Card key={character.id} className="bg-black/20 border-purple-500/30 hover:border-purple-400/50 transition-colors">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-white text-lg">{character.name}</CardTitle>
                    <CardDescription className="text-purple-200">
                      Level {character.level} {character.race} {character.class}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {character.campaign && (
                      <div className="flex items-center gap-1 text-sm text-purple-200 mb-2">
                        <MapPin className="h-3 w-3" />
                        {character.campaign}
                      </div>
                    )}
                    <Badge variant={character.status === 'active' ? 'default' : 'outline'} className="mb-3">
                      {character.status}
                    </Badge>
                    <Button
                      size="sm"
                      className="w-full bg-purple-600 hover:bg-purple-700"
                      onClick={() => onViewChange('character-sheet')}
                    >
                      View Character
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {searchQuery && filteredCampaigns.length === 0 && filteredCharacters.length === 0 && (
          <Card className="bg-black/20 border-purple-500/30 text-center py-12">
            <CardContent>
              <Sparkles className="h-12 w-12 text-purple-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">No Results Found</h3>
              <p className="text-purple-200">Try adjusting your search terms or browse all available content.</p>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mt-8">
          <Button
            onClick={() => onViewChange('create-campaign')}
            className="bg-purple-600 hover:bg-purple-700 flex items-center gap-2"
          >
            <Shield className="h-4 w-4" />
            Create New Campaign
          </Button>
          <Button
            onClick={() => onViewChange('character-creator')}
            variant="outline"
            className="border-purple-500/30 text-purple-200 hover:bg-purple-600/20 flex items-center gap-2"
          >
            <Scroll className="h-4 w-4" />
            Create New Character
          </Button>
          <Button
            onClick={() => onViewChange('dashboard')}
            variant="outline"
            className="border-purple-500/30 text-purple-200 hover:bg-purple-600/20 flex items-center gap-2"
          >
            <Book className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    </div>
  )
}
