'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Separator } from './ui/separator'
import { ImageWithFallback } from './figma/ImageWithFallback'
import {
  ShoppingCart,
  Star,
  Shield,
  ArrowLeft,
  Heart,
  Share,
  Truck,
  RotateCcw,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import type { Jersey, AppView } from '../types'

interface ProductPageProps {
  jersey: Jersey
  onNavigate: (view: AppView, jersey?: Jersey) => void
  onAddToCart: (jersey: Jersey) => void
  cartItemCount: number
}

export function ProductPage({ jersey, onNavigate, onAddToCart, cartItemCount }: ProductPageProps) {
  const [isAddingToCart, setIsAddingToCart] = useState(false)

  const handleAddToCart = async () => {
    setIsAddingToCart(true)
    await new Promise(resolve => setTimeout(resolve, 500)) // Simulate API call
    onAddToCart(jersey)
    setIsAddingToCart(false)
  }

  const getSavingsPercentage = () => {
    return Math.round(((jersey.originalPrice - jersey.price) / jersey.originalPrice) * 100)
  }

  const getConditionColor = (condition: string) => {
    switch (condition) {
      case 'Excellent': return 'bg-green-100 text-green-800'
      case 'Very Good': return 'bg-blue-100 text-blue-800'
      case 'Good': return 'bg-yellow-100 text-yellow-800'
      case 'Fair': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={() => onNavigate('home')}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <h1 className="text-2xl text-slate-900 cursor-pointer" onClick={() => onNavigate('home')}>
                🏆 JerseyHub
              </h1>
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-2 gap-12">
          {/* Image Section */}
          <div className="space-y-4">
            <div className="relative">
              <ImageWithFallback
                src={jersey.imageUrl}
                alt={jersey.name}
                className="w-full h-96 lg:h-[500px] object-cover rounded-xl shadow-lg"
              />
              {jersey.isVintage && (
                <Badge className="absolute top-4 right-4 bg-purple-500 text-white text-sm px-3 py-1">
                  Vintage
                </Badge>
              )}
              {jersey.isAuthentic && (
                <Badge className="absolute top-4 left-4 bg-blue-500 text-white text-sm px-3 py-1">
                  <Shield className="w-4 h-4 mr-1" />
                  Authentic
                </Badge>
              )}
              {getSavingsPercentage() > 20 && (
                <Badge className="absolute bottom-4 right-4 bg-red-500 text-white text-lg px-4 py-2">
                  {getSavingsPercentage()}% OFF
                </Badge>
              )}
            </div>
          </div>

          {/* Product Details */}
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl text-slate-900 mb-3">{jersey.name}</h1>
              <p className="text-xl text-muted-foreground mb-4">
                {jersey.team} • #{jersey.number} • {jersey.year && `${jersey.year} Season`}
              </p>

              <div className="flex items-center space-x-4 mb-6">
                <div className="flex items-center space-x-1">
                  <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                  <span className="text-lg">{jersey.sellerRating}</span>
                  <span className="text-muted-foreground">(127 reviews)</span>
                </div>
                <Badge className={`${getConditionColor(jersey.condition)} text-sm px-3 py-1`}>
                  {jersey.condition} Condition
                </Badge>
              </div>
            </div>

            {/* Pricing */}
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <div className="flex items-center space-x-4 mb-4">
                <span className="text-4xl text-slate-900">${jersey.price}</span>
                {jersey.originalPrice > jersey.price && (
                  <div className="space-y-1">
                    <span className="text-xl text-muted-foreground line-through">
                      ${jersey.originalPrice}
                    </span>
                    <Badge className="bg-green-100 text-green-800 text-sm">
                      Save ${(jersey.originalPrice - jersey.price).toFixed(2)}
                    </Badge>
                  </div>
                )}
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Size:</span>
                  <Badge variant="outline" className="text-lg px-4 py-1">{jersey.size}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Sport:</span>
                  <span>{jersey.sport}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Availability:</span>
                  <div className="flex items-center space-x-1">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-green-600">In Stock</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <Button
                  onClick={handleAddToCart}
                  disabled={isAddingToCart}
                  className="w-full h-12 text-lg bg-blue-600 hover:bg-blue-700"
                >
                  {isAddingToCart ? (
                    "Adding to Cart..."
                  ) : (
                    <>
                      <ShoppingCart className="w-5 h-5 mr-2" />
                      Add to Cart
                    </>
                  )}
                </Button>

                <div className="flex space-x-2">
                  <Button variant="outline" className="flex-1">
                    <Heart className="w-4 h-4 mr-2" />
                    Save
                  </Button>
                  <Button variant="outline" size="icon">
                    <Share className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Shipping Info */}
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <h3 className="text-lg mb-4">Shipping & Returns</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <Truck className="w-5 h-5 text-green-600" />
                  <div>
                    <p className="text-sm">Free shipping on orders over $50</p>
                    <p className="text-xs text-muted-foreground">Estimated delivery: 2-3 business days</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <RotateCcw className="w-5 h-5 text-blue-600" />
                  <div>
                    <p className="text-sm">30-day return policy</p>
                    <p className="text-xs text-muted-foreground">Free returns for any reason</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Product Description */}
        <div className="mt-12 bg-white p-8 rounded-xl shadow-sm border">
          <h2 className="text-2xl text-slate-900 mb-6">Product Description</h2>
          <div className="prose max-w-none">
            <p className="text-muted-foreground leading-relaxed">
              {jersey.description}
            </p>

            <div className="mt-6 grid md:grid-cols-2 gap-6">
              <div>
                <h3>Jersey Details</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>• Player: {jersey.player}</li>
                  <li>• Team: {jersey.team}</li>
                  <li>• Number: #{jersey.number}</li>
                  <li>• Size: {jersey.size}</li>
                  <li>• Sport: {jersey.sport}</li>
                  {jersey.year && <li>• Year: {jersey.year}</li>}
                </ul>
              </div>

              <div>
                <h3>Quality & Authentication</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Condition: {jersey.condition}</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    {jersey.isAuthentic ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-yellow-500" />
                    )}
                    <span>{jersey.isAuthentic ? 'Authenticity verified' : 'Replica jersey'}</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Quality inspected</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Professionally cleaned</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Seller Info */}
        <div className="mt-8 bg-white p-8 rounded-xl shadow-sm border">
          <h2 className="text-2xl text-slate-900 mb-6">Seller Information</h2>
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-slate-200 rounded-full flex items-center justify-center text-2xl">
              👤
            </div>
            <div>
              <h3 className="text-lg">Seller #{jersey.sellerId}</h3>
              <div className="flex items-center space-x-2 mt-1">
                <div className="flex items-center space-x-1">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  <span>{jersey.sellerRating}</span>
                </div>
                <span className="text-muted-foreground">• 500+ sales</span>
                <Badge className="bg-green-100 text-green-800">Top Rated</Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                Trusted seller specializing in authentic sports memorabilia
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
