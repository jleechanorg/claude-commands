'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Input } from './ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Checkbox } from './ui/checkbox'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from './ui/sheet'
import { ImageWithFallback } from './figma/ImageWithFallback'
import {
  Search,
  ShoppingCart,
  Star,
  Filter,
  Shield,
  SlidersHorizontal,
  Grid,
  List,
  ArrowUpDown
} from 'lucide-react'
import type { Jersey, AppView, Sport } from '../App'

interface BrowsePageProps {
  jerseys: Jersey[]
  onNavigate: (view: AppView, jersey?: Jersey) => void
  onSearch: (query: string, sport?: Sport) => void
  cartItemCount: number
  selectedSport: Sport
  onSportChange: (sport: Sport) => void
}

type SortOption = 'price-low' | 'price-high' | 'condition' | 'newest' | 'rating'
type ViewMode = 'grid' | 'list'

export function BrowsePage({
  jerseys,
  onNavigate,
  onSearch,
  cartItemCount,
  selectedSport,
  onSportChange
}: BrowsePageProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<SortOption>('newest')
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 500])
  const [selectedSizes, setSelectedSizes] = useState<string[]>([])
  const [selectedConditions, setSelectedConditions] = useState<string[]>([])
  const [showAuthentic, setShowAuthentic] = useState(false)
  const [showVintage, setShowVintage] = useState(false)

  const sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']
  const conditions = ['Excellent', 'Very Good', 'Good', 'Fair']
  const sports: Sport[] = ['All', 'NFL', 'NBA', 'MLB', 'NHL', 'Soccer']

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      onSearch(searchQuery.trim(), selectedSport)
    }
  }

  const toggleSize = (size: string) => {
    setSelectedSizes(prev =>
      prev.includes(size)
        ? prev.filter(s => s !== size)
        : [...prev, size]
    )
  }

  const toggleCondition = (condition: string) => {
    setSelectedConditions(prev =>
      prev.includes(condition)
        ? prev.filter(c => c !== condition)
        : [...prev, condition]
    )
  }

  const filteredAndSortedJerseys = jerseys
    .filter(jersey => {
      const matchesQuery = searchQuery === '' ||
        jersey.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        jersey.player.toLowerCase().includes(searchQuery.toLowerCase()) ||
        jersey.team.toLowerCase().includes(searchQuery.toLowerCase())

      const matchesSport = selectedSport === 'All' || jersey.sport === selectedSport
      const matchesPrice = jersey.price >= priceRange[0] && jersey.price <= priceRange[1]
      const matchesSize = selectedSizes.length === 0 || selectedSizes.includes(jersey.size)
      const matchesCondition = selectedConditions.length === 0 || selectedConditions.includes(jersey.condition)
      const matchesAuthentic = !showAuthentic || jersey.isAuthentic
      const matchesVintage = !showVintage || jersey.isVintage

      return matchesQuery && matchesSport && matchesPrice && matchesSize &&
             matchesCondition && matchesAuthentic && matchesVintage
    })
    .sort((a, b) => {
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
        case 'newest':
        default:
          return 0
      }
    })

  const clearFilters = () => {
    setSearchQuery('')
    setPriceRange([0, 500])
    setSelectedSizes([])
    setSelectedConditions([])
    setShowAuthentic(false)
    setShowVintage(false)
    onSportChange('All')
  }

  const FilterPanel = () => (
    <div className="space-y-6">
      <div>
        <h3 className="mb-3">Sport</h3>
        <div className="space-y-2">
          {sports.map(sport => (
            <div key={sport} className="flex items-center space-x-2">
              <Checkbox
                id={sport}
                checked={selectedSport === sport}
                onCheckedChange={() => onSportChange(sport)}
              />
              <label htmlFor={sport} className="text-sm">{sport}</label>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-3">Size</h3>
        <div className="space-y-2">
          {sizes.map(size => (
            <div key={size} className="flex items-center space-x-2">
              <Checkbox
                id={size}
                checked={selectedSizes.includes(size)}
                onCheckedChange={() => toggleSize(size)}
              />
              <label htmlFor={size} className="text-sm">{size}</label>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-3">Condition</h3>
        <div className="space-y-2">
          {conditions.map(condition => (
            <div key={condition} className="flex items-center space-x-2">
              <Checkbox
                id={condition}
                checked={selectedConditions.includes(condition)}
                onCheckedChange={() => toggleCondition(condition)}
              />
              <label htmlFor={condition} className="text-sm">{condition}</label>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-3">Special Features</h3>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="authentic"
              checked={showAuthentic}
              onCheckedChange={(checked) => setShowAuthentic(checked === true)}
            />
            <label htmlFor="authentic" className="text-sm">Authentic Only</label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox
              id="vintage"
              checked={showVintage}
              onCheckedChange={(checked) => setShowVintage(checked === true)}
            />
            <label htmlFor="vintage" className="text-sm">Vintage Only</label>
          </div>
        </div>
      </div>

      <Button variant="outline" onClick={clearFilters} className="w-full">
        Clear All Filters
      </Button>
    </div>
  )

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

      {/* Search and Filter Bar */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <form onSubmit={handleSearchSubmit} className="flex-1 max-w-2xl">
              <div className="flex">
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search jerseys..."
                  className="flex-1"
                />
                <Button type="submit" className="ml-2">
                  <Search className="w-4 h-4" />
                </Button>
              </div>
            </form>

            <div className="flex items-center space-x-4">
              <Select value={sortBy} onValueChange={(value: SortOption) => setSortBy(value)}>
                <SelectTrigger className="w-48">
                  <ArrowUpDown className="w-4 h-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="newest">Newest First</SelectItem>
                  <SelectItem value="price-low">Price: Low to High</SelectItem>
                  <SelectItem value="price-high">Price: High to Low</SelectItem>
                  <SelectItem value="condition">Best Condition</SelectItem>
                  <SelectItem value="rating">Highest Rated</SelectItem>
                </SelectContent>
              </Select>

              <div className="flex items-center space-x-1 border rounded-md">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  <Grid className="w-4 h-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                >
                  <List className="w-4 h-4" />
                </Button>
              </div>

              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline">
                    <SlidersHorizontal className="w-4 h-4 mr-2" />
                    Filters
                  </Button>
                </SheetTrigger>
                <SheetContent>
                  <SheetHeader>
                    <SheetTitle>Filter Jerseys</SheetTitle>
                    <SheetDescription>
                      Narrow down your search with these filters
                    </SheetDescription>
                  </SheetHeader>
                  <div className="mt-6">
                    <FilterPanel />
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Desktop Filters Sidebar */}
          <div className="hidden lg:block w-64 flex-shrink-0">
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <h2 className="text-lg mb-4">Filters</h2>
              <FilterPanel />
            </div>
          </div>

          {/* Results */}
          <div className="flex-1">
            <div className="mb-6">
              <h2 className="text-2xl text-slate-900 mb-2">
                {selectedSport === 'All' ? 'All Jerseys' : `${selectedSport} Jerseys`}
              </h2>
              <p className="text-muted-foreground">
                {filteredAndSortedJerseys.length} jerseys found
              </p>
            </div>

            {viewMode === 'grid' ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredAndSortedJerseys.map((jersey) => (
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
                      <CardTitle className="text-lg line-clamp-2">{jersey.name}</CardTitle>
                      <CardDescription className="line-clamp-1">{jersey.team}</CardDescription>
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
              <div className="space-y-4">
                {filteredAndSortedJerseys.map((jersey) => (
                  <Card
                    key={jersey.id}
                    className="group hover:shadow-lg transition-all duration-300 cursor-pointer"
                    onClick={() => onNavigate('product', jersey)}
                  >
                    <CardContent className="p-6">
                      <div className="flex gap-6">
                        <div className="relative flex-shrink-0">
                          <ImageWithFallback
                            src={jersey.imageUrl}
                            alt={jersey.name}
                            className="w-32 h-32 object-cover rounded-lg"
                          />
                          {jersey.isVintage && (
                            <Badge className="absolute top-2 right-2 bg-purple-500 text-white text-xs">
                              Vintage
                            </Badge>
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <h3 className="text-xl text-slate-900 mb-1">{jersey.name}</h3>
                              <p className="text-muted-foreground">{jersey.team} • #{jersey.number}</p>
                            </div>
                            <div className="text-right">
                              <div className="text-2xl text-slate-900 mb-1">${jersey.price}</div>
                              <div className="flex items-center space-x-1">
                                <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                                <span className="text-sm text-muted-foreground">{jersey.sellerRating}</span>
                              </div>
                            </div>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                            {jersey.description}
                          </p>
                          <div className="flex items-center space-x-3">
                            <Badge variant="outline">{jersey.size}</Badge>
                            <Badge variant="secondary">{jersey.condition}</Badge>
                            {jersey.isAuthentic && (
                              <Badge className="bg-blue-500 text-white">
                                <Shield className="w-3 h-3 mr-1" />
                                Authentic
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {filteredAndSortedJerseys.length === 0 && (
              <div className="text-center py-12">
                <Filter className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg text-slate-900 mb-2">No jerseys found</h3>
                <p className="text-muted-foreground mb-4">Try adjusting your filters or search terms</p>
                <Button onClick={clearFilters}>Clear All Filters</Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
