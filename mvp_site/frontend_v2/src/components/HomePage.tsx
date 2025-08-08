'use client'

import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Input } from './ui/input'
import { ImageWithFallback } from './figma/ImageWithFallback'
import {
  Search,
  ShoppingCart,
  Star,
  TrendingUp,
  Filter,
  Heart,
  Shield,
  Truck,
  RotateCcw
} from 'lucide-react'
import type { Jersey, AppView, Sport } from '../types'

interface HomePageProps {
  jerseys: Jersey[]
  onNavigate: (view: AppView, jersey?: Jersey) => void
  onSearch: (query: string, sport?: Sport) => void
  cartItemCount: number
}

export function HomePage({ jerseys, onNavigate, onSearch, cartItemCount }: HomePageProps) {
  const featuredJerseys = jerseys.filter(jersey => jersey.isVintage || jersey.sellerRating >= 4.8).slice(0, 6)
  const dealJerseys = jerseys.filter(jersey => (jersey.originalPrice - jersey.price) / jersey.originalPrice > 0.3).slice(0, 4)

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const query = formData.get('search') as string
    if (query.trim()) {
      onSearch(query.trim())
    }
  }

  const getSavingsPercentage = (originalPrice: number, currentPrice: number) => {
    return Math.round(((originalPrice - currentPrice) / originalPrice) * 100)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
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

      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-5xl mb-6">
            Find Your Perfect Jersey
          </h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto opacity-90">
            Discover authentic used sports jerseys from your favorite teams and players. Great condition, unbeatable prices.
          </p>

          {/* Search Bar */}
          <form onSubmit={handleSearchSubmit} className="max-w-2xl mx-auto mb-8">
            <div className="flex">
              <Input
                name="search"
                placeholder="Search by player, team, or sport..."
                className="flex-1 h-12 text-slate-900 bg-white"
              />
              <Button type="submit" size="lg" className="ml-2 h-12 px-8 bg-orange-500 hover:bg-orange-600">
                <Search className="w-5 h-5 mr-2" />
                Search
              </Button>
            </div>
          </form>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
            <div className="text-center">
              <div className="text-3xl mb-2">1000+</div>
              <div className="text-sm opacity-75">Jerseys Available</div>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">98%</div>
              <div className="text-sm opacity-75">Customer Satisfaction</div>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">5★</div>
              <div className="text-sm opacity-75">Average Rating</div>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">50%</div>
              <div className="text-sm opacity-75">Average Savings</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <Shield className="w-12 h-12 text-blue-600 mx-auto mb-4" />
              <h3 className="mb-2">Authenticity Guaranteed</h3>
              <p className="text-sm text-muted-foreground">All jerseys verified for authenticity</p>
            </div>
            <div className="text-center">
              <Truck className="w-12 h-12 text-green-600 mx-auto mb-4" />
              <h3 className="mb-2">Fast Shipping</h3>
              <p className="text-sm text-muted-foreground">2-3 day delivery nationwide</p>
            </div>
            <div className="text-center">
              <RotateCcw className="w-12 h-12 text-purple-600 mx-auto mb-4" />
              <h3 className="mb-2">Easy Returns</h3>
              <p className="text-sm text-muted-foreground">30-day return policy</p>
            </div>
            <div className="text-center">
              <Star className="w-12 h-12 text-yellow-600 mx-auto mb-4" />
              <h3 className="mb-2">Top Rated</h3>
              <p className="text-sm text-muted-foreground">Trusted by thousands of customers</p>
            </div>
          </div>
        </div>
      </section>

      {/* Hot Deals */}
      <section className="py-16 bg-gradient-to-r from-red-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl text-slate-900 mb-2">🔥 Hot Deals</h2>
              <p className="text-muted-foreground">Limited time offers on premium jerseys</p>
            </div>
            <Button variant="outline" onClick={() => onNavigate('browse')}>
              View All Deals
            </Button>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {dealJerseys.map((jersey) => (
              <Card
                key={jersey.id}
                className="group hover:shadow-lg transition-all duration-300 cursor-pointer border-2 border-red-200"
                onClick={() => onNavigate('product', jersey)}
              >
                <CardHeader className="p-4">
                  <div className="relative">
                    <ImageWithFallback
                      src={jersey.imageUrl}
                      alt={jersey.name}
                      className="w-full h-48 object-cover rounded-lg mb-4"
                    />
                    <Badge className="absolute top-2 right-2 bg-red-500 text-white">
                      {getSavingsPercentage(jersey.originalPrice, jersey.price)}% OFF
                    </Badge>
                    <Badge className="absolute top-2 left-2 bg-orange-500 text-white">
                      HOT DEAL
                    </Badge>
                  </div>
                  <CardTitle className="text-lg line-clamp-2">{jersey.name}</CardTitle>
                  <CardDescription className="line-clamp-1">{jersey.team}</CardDescription>
                </CardHeader>
                <CardContent className="p-4 pt-0">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl text-slate-900">${jersey.price}</span>
                      <span className="text-lg text-muted-foreground line-through">${jersey.originalPrice}</span>
                    </div>
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
        </div>
      </section>

      {/* Featured Jerseys */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl text-slate-900 mb-2">⭐ Featured Jerseys</h2>
              <p className="text-muted-foreground">Rare finds and vintage classics</p>
            </div>
            <Button variant="outline" onClick={() => onNavigate('browse')}>
              View All
            </Button>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featuredJerseys.map((jersey) => (
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
                  <CardDescription className="line-clamp-1">{jersey.team} • #{jersey.number}</CardDescription>
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
        </div>
      </section>

      {/* Newsletter */}
      <section className="py-16 bg-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl mb-4">Never Miss a Deal</h2>
          <p className="text-lg mb-8 opacity-75">
            Get notified about new arrivals, exclusive deals, and rare vintage finds
          </p>
          <div className="flex max-w-md mx-auto">
            <Input
              placeholder="Enter your email"
              className="flex-1 h-12 text-slate-900 bg-white"
            />
            <Button className="ml-2 h-12 px-8 bg-blue-600 hover:bg-blue-700">
              Subscribe
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-800 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-lg mb-4">🏆 JerseyHub</h3>
              <p className="text-sm opacity-75">
                Your trusted source for authentic used sports jerseys.
              </p>
            </div>
            <div>
              <h4 className="mb-4">Shop</h4>
              <div className="space-y-2 text-sm opacity-75">
                <div>NFL Jerseys</div>
                <div>NBA Jerseys</div>
                <div>MLB Jerseys</div>
                <div>NHL Jerseys</div>
                <div>Soccer Jerseys</div>
              </div>
            </div>
            <div>
              <h4 className="mb-4">Support</h4>
              <div className="space-y-2 text-sm opacity-75">
                <div>Contact Us</div>
                <div>Shipping Info</div>
                <div>Returns</div>
                <div>Size Guide</div>
                <div>Authentication</div>
              </div>
            </div>
            <div>
              <h4 className="mb-4">Company</h4>
              <div className="space-y-2 text-sm opacity-75">
                <div>About Us</div>
                <div>Careers</div>
                <div>Privacy Policy</div>
                <div>Terms of Service</div>
              </div>
            </div>
          </div>
          <div className="border-t border-slate-700 mt-8 pt-8 text-center text-sm opacity-75">
            © 2024 JerseyHub. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
