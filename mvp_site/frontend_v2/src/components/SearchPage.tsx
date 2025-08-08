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
import type { AppView } from '../types'

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


interface SearchPageProps {
  onViewChange: (view: AppView) => void
}

export function SearchPage({ onViewChange }: SearchPageProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchType, setSearchType] = useState<'campaigns'>('campaigns')
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(false)

  // IMPLEMENTATION_NOTE: Search functionality currently operates on local data
  // Full API search will be enabled when backend search endpoints are implemented
  useEffect(() => {
    // Fetch campaigns from API
    const fetchCampaigns = async () => {
      try {
        // BACKEND_LIMITATION: Backend search API not yet implemented
        // Using local filtering for now - will connect to /api/campaigns/search when available
        if (import.meta.env?.DEV) {
          console.log('Campaign search using local data - backend search API pending')
        }
        setCampaigns([]) // Empty state until real API is connected
      } catch (error) {
        console.error('Failed to fetch campaigns:', error)
        setCampaigns([])
      }
    }

    fetchCampaigns()
  }, [])

  const filteredCampaigns = campaigns.filter(campaign =>
    campaign.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    campaign.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    campaign.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
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
                  placeholder="Search campaigns or tags..."
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
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
        </Card>

        {/* Campaigns Section */}
        {searchType === 'campaigns' && (
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


        {/* Empty State */}
        {searchQuery && filteredCampaigns.length === 0 && (
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
