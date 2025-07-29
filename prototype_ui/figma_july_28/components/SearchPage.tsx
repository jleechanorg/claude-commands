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
  ShoppingCart, 
  Star, 
  Shield,
  ArrowUpDown,
  X,
  TrendingUp
} from 'lucide-react'
import type { Jersey, AppView, Sport } from '../App'

interface SearchPageProps {
  jerseys: Jersey[]
  searchQuery: string
  selectedSport: Sport
  onNavigate: (view: AppView, jersey?: Jersey) => void
  onSearch: (query: string, sport?: Sport) => void
  onSportChange: (sport: Sport) => void
  cartItemCount: number
}

type SortOption = 'relevance' | 'price-low' | 'price-high' | 'condition' | 'rating'

export function SearchPage({ 
  jerseys, 
  searchQuery: initialQuery,
  selectedSport,
  onNavigate, 
  onSearch,
  onSportChange,
  cartItemCount
}: SearchPageProps) {
  const [searchQuery, setSearchQuery] = useState(initialQuery)
  const [sortBy, setSortBy] = useState<SortOption>('relevance')
  const [suggestions] = useState([
    'Tom Brady', 'Michael Jordan', 'Kobe Bryant', 'Derek Jeter', 
    'Wayne Gretzky', 'Messi', 'Lakers', 'Patriots', 'Bulls', 'Yankees'
  ])

  const sports: Sport[] = ['All', 'NFL', 'NBA', 'MLB', 'NHL', 'Soccer']

  useEffect(() => {
    setSearchQuery(initialQuery)
  }, [initialQuery])

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      onSearch(searchQuery.trim(), selectedSport)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setSearchQuery(suggestion)
    onSearch(suggestion, selectedSport)
  }

  const clearSearch = () => {
    setSearchQuery('')
    onSearch('', selectedSport)
  }

  const sortedJerseys = [...jerseys].sort((a, b) => {
    switch (sortBy) {
      case 'price-low':
        return a.price - b.price
      case 'price-high':
        return b.price - a.price
      case 'condition':
        const conditionOrder = { 'Excellent': 4, 'Very Good': 3, 'Good': 2, 'Fair': 1 }
        return conditionOrder[b.condition] - conditionOrder[a.condition]
      case 'rating':
        return b.sellerRating - a.sellerRating
      case 'relevance':
      default:
        return 0
    }
  })

  const getHighlightedText = (text: string, query: string) => {
    if (!query) return text
    const parts = text.split(new RegExp(`(${query})`, 'gi'))
    return parts.map((part, index) => 
      part.toLowerCase() === query.toLowerCase() ? 
        <mark key={index} className="bg-yellow-200 px-1 rounded">{part}</mark> : 
        part
    )
  }

  const popularSearches = [
    { term: 'Tom Brady Patriots', count: '245 results' },
    { term: 'Michael Jordan Bulls', count: '189 results' },
    { term: 'Vintage NBA jerseys', count: '156 results' },
    { term: 'Lakers jerseys', count: '123 results' }
  ]

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl text-slate-900 cursor-pointer" onClick={() => onNavigate('home')}>
                🏆 JerseyHub
              </h1>
              <nav className="hidden md:flex space-x-6">
                <Button variant="ghost" onClick={() => onNavigate('browse')}>
                  Browse
                </Button>
                <Button variant="ghost" onClick={() => onSearch('', 'NFL')}>
                  NFL
                </Button>
                <Button variant="ghost" onClick={() => onSearch('', 'NBA')}>
                  NBA
                </Button>
                <Button variant="ghost" onClick={() => onSearch('', 'MLB')}>
                  MLB
                </Button>
                <Button variant="ghost" onClick={() => onSearch('', 'NHL')}>
                  NHL
                </Button>
                <Button variant="ghost" onClick={() => onSearch('', 'Soccer')}>
                  Soccer
                </Button>
              </nav>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button 
                variant="outline" 
                size="icon"
                onClick={() => onNavigate('cart')}
                className="relative"
              >
                <ShoppingCart className="w-4 h-4" />
                {cartItemCount > 0 && (
                  <Badge className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs">
                    {cartItemCount}
                  </Badge>
                )}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Search Section */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <form onSubmit={handleSearchSubmit} className="max-w-4xl mx-auto">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1 relative">
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search for jerseys, players, teams..."
                  className="h-12 pr-10"
                />
                {searchQuery && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={clearSearch}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>
              
              <Select value={selectedSport} onValueChange={onSportChange}>
                <SelectTrigger className="w-full lg:w-48 h-12">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {sports.map(sport => (
                    <SelectItem key={sport} value={sport}>{sport}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Button type="submit" size="lg" className="h-12 px-8">
                <Search className="w-5 h-5 mr-2" />
                Search
              </Button>
            </div>
          </form>

          {/* Search Suggestions */}
          {!searchQuery && (
            <div className="mt-6 max-w-4xl mx-auto">
              <div className="mb-4">
                <h3 className="text-sm text-muted-foreground mb-3">Popular searches:</h3>
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((suggestion) => (
                    <Button
                      key={suggestion}
                      variant="outline"
                      size="sm"
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="text-sm"
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>
              
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
                {popularSearches.map((search, index) => (
                  <div 
                    key={index}
                    className="p-3 bg-slate-100 rounded-lg cursor-pointer hover:bg-slate-200 transition-colors"
                    onClick={() => handleSuggestionClick(search.term)}
                  >
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-blue-500" />
                      <div>
                        <p className="text-sm">{search.term}</p>
                        <p className="text-xs text-muted-foreground">{search.count}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {searchQuery && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-2xl text-slate-900 mb-2">
                Search Results for "{searchQuery}"
              </h2>
              <p className="text-muted-foreground">
                {sortedJerseys.length} jerseys found
                {selectedSport !== 'All' && ` in ${selectedSport}`}
              </p>
            </div>
            
            <Select value={sortBy} onValueChange={(value: SortOption) => setSortBy(value)}>
              <SelectTrigger className="w-full lg:w-48">
                <ArrowUpDown className="w-4 h-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="relevance">Most Relevant</SelectItem>
                <SelectItem value="price-low">Price: Low to High</SelectItem>
                <SelectItem value="price-high">Price: High to Low</SelectItem>
                <SelectItem value="condition">Best Condition</SelectItem>
                <SelectItem value="rating">Highest Rated</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {sortedJerseys.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {sortedJerseys.map((jersey) => (
                <Card 
                  key={jersey.id} 
                  className="group hover:shadow-lg transition-all duration-300 cursor-pointer"
                  onClick={() => onNavigate('product', jersey)}
                >
                  <CardHeader className="p-4">
                    <div className="relative">
                      <ImageWithFallback
                        src={jersey.imageUrl}
                        alt={jersey.name}
                        className="w-full h-48 object-cover rounded-lg mb-4"
                      />
                      {jersey.isVintage && (
                        <Badge className="absolute top-2 right-2 bg-purple-500 text-white">
                          Vintage
                        </Badge>
                      )}
                      {jersey.isAuthentic && (
                        <Badge className="absolute top-2 left-2 bg-blue-500 text-white">
                          <Shield className="w-3 h-3 mr-1" />
                          Authentic
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="text-lg line-clamp-2">
                      {getHighlightedText(jersey.name, searchQuery)}
                    </CardTitle>
                    <CardDescription className="line-clamp-1">
                      {getHighlightedText(jersey.team, searchQuery)} • #{jersey.number}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-4 pt-0">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-2xl text-slate-900">${jersey.price}</span>
                      <Badge variant="outline" className="text-xs">
                        {jersey.size}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <Badge variant="secondary" className="text-xs">
                        {jersey.condition}
                      </Badge>
                      <div className="flex items-center space-x-1">
                        <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                        <span className="text-xs text-muted-foreground">{jersey.sellerRating}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Search className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg text-slate-900 mb-2">No results found</h3>
              <p className="text-muted-foreground mb-6">
                Try searching for different terms or check your spelling
              </p>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground mb-3">Try these popular searches instead:</p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {suggestions.slice(0, 5).map((suggestion) => (
                      <Button
                        key={suggestion}
                        variant="outline"
                        size="sm"
                        onClick={() => handleSuggestionClick(suggestion)}
                      >
                        {suggestion}
                      </Button>
                    ))}
                  </div>
                </div>
                <Button onClick={() => onNavigate('browse')}>
                  Browse All Jerseys
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}