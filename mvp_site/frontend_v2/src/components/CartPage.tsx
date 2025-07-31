'use client'

import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Separator } from './ui/separator'
import { Input } from './ui/input'
import { ImageWithFallback } from './figma/ImageWithFallback'
import {
  ShoppingCart,
  ArrowLeft,
  Plus,
  Minus,
  Trash2,
  Shield,
  Truck,
  Lock,
  CreditCard,
  Gift
} from 'lucide-react'
import type { CartItem, AppView } from '../App'

interface CartPageProps {
  cartItems: CartItem[]
  onNavigate: (view: AppView) => void
  onUpdateQuantity: (jerseyId: string, quantity: number) => void
  onRemoveItem: (jerseyId: string) => void
  total: number
}

export function CartPage({
  cartItems,
  onNavigate,
  onUpdateQuantity,
  onRemoveItem,
  total
}: CartPageProps) {
  const subtotal = total
  const shipping = subtotal > 50 ? 0 : 9.99
  const tax = subtotal * 0.0875 // 8.75% tax rate
  const finalTotal = subtotal + shipping + tax

  const handleQuantityChange = (jerseyId: string, newQuantity: number) => {
    if (newQuantity < 1) {
      onRemoveItem(jerseyId)
    } else {
      onUpdateQuantity(jerseyId, newQuantity)
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
                Continue Shopping
              </Button>
              <h1 className="text-2xl text-slate-900 cursor-pointer" onClick={() => onNavigate('home')}>
                🏆 JerseyHub
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="text-sm px-3 py-1">
                {cartItems.reduce((sum, item) => sum + item.quantity, 0)} items
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {cartItems.length === 0 ? (
          /* Empty Cart */
          <div className="text-center py-12">
            <ShoppingCart className="w-24 h-24 text-muted-foreground mx-auto mb-6" />
            <h2 className="text-2xl text-slate-900 mb-4">Your cart is empty</h2>
            <p className="text-muted-foreground mb-8 max-w-md mx-auto">
              Looks like you haven't added any jerseys to your cart yet.
              Browse our collection to find your perfect jersey!
            </p>
            <Button onClick={() => onNavigate('browse')} size="lg">
              Start Shopping
            </Button>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Cart Items */}
            <div className="lg:col-span-2 space-y-6">
              <div>
                <h1 className="text-3xl text-slate-900 mb-2">Shopping Cart</h1>
                <p className="text-muted-foreground">
                  {cartItems.length} {cartItems.length === 1 ? 'item' : 'items'} in your cart
                </p>
              </div>

              <div className="space-y-4">
                {cartItems.map((item) => (
                  <Card key={item.jersey.id} className="p-6">
                    <div className="flex gap-6">
                      <div className="relative flex-shrink-0">
                        <ImageWithFallback
                          src={item.jersey.imageUrl}
                          alt={item.jersey.name}
                          className="w-24 h-24 object-cover rounded-lg"
                        />
                        {item.jersey.isVintage && (
                          <Badge className="absolute -top-2 -right-2 bg-purple-500 text-white text-xs px-2 py-1">
                            Vintage
                          </Badge>
                        )}
                      </div>

                      <div className="flex-1">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="text-lg text-slate-900 mb-1">{item.jersey.name}</h3>
                            <p className="text-muted-foreground text-sm">
                              {item.jersey.team} • #{item.jersey.number} • Size {item.jersey.size}
                            </p>
                            <div className="flex items-center space-x-2 mt-2">
                              <Badge variant="secondary" className="text-xs">
                                {item.jersey.condition}
                              </Badge>
                              {item.jersey.isAuthentic && (
                                <Badge className="bg-blue-500 text-white text-xs">
                                  <Shield className="w-3 h-3 mr-1" />
                                  Authentic
                                </Badge>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onRemoveItem(item.jersey.id)}
                            className="text-red-500 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() => handleQuantityChange(item.jersey.id, item.quantity - 1)}
                              className="h-8 w-8"
                            >
                              <Minus className="w-3 h-3" />
                            </Button>
                            <span className="w-8 text-center">{item.quantity}</span>
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() => handleQuantityChange(item.jersey.id, item.quantity + 1)}
                              className="h-8 w-8"
                            >
                              <Plus className="w-3 h-3" />
                            </Button>
                          </div>
                          <div className="text-right">
                            <p className="text-lg text-slate-900">
                              ${(item.jersey.price * item.quantity).toFixed(2)}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              ${item.jersey.price} each
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>

            {/* Order Summary */}
            <div className="space-y-6">
              <Card className="p-6">
                <h2 className="text-xl text-slate-900 mb-4">Order Summary</h2>

                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span>${subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Shipping</span>
                    <span className={shipping === 0 ? 'text-green-600' : ''}>
                      {shipping === 0 ? 'FREE' : `$${shipping.toFixed(2)}`}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Tax</span>
                    <span>${tax.toFixed(2)}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between text-lg">
                    <span>Total</span>
                    <span className="text-slate-900">${finalTotal.toFixed(2)}</span>
                  </div>
                </div>

                {shipping > 0 && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-700">
                      Add ${(50 - subtotal).toFixed(2)} more for free shipping!
                    </p>
                  </div>
                )}

                <Button className="w-full mt-6 h-12 text-lg bg-green-600 hover:bg-green-700">
                  <Lock className="w-5 h-5 mr-2" />
                  Secure Checkout
                </Button>

                <div className="mt-4 space-y-2">
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Shield className="w-4 h-4" />
                    <span>Secure payment processing</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Truck className="w-4 h-4" />
                    <span>Free returns within 30 days</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <CreditCard className="w-4 h-4" />
                    <span>All major credit cards accepted</span>
                  </div>
                </div>
              </Card>

              {/* Promo Code */}
              <Card className="p-6">
                <h3 className="text-lg text-slate-900 mb-4">Promo Code</h3>
                <div className="flex space-x-2">
                  <Input placeholder="Enter code" className="flex-1" />
                  <Button variant="outline">Apply</Button>
                </div>
              </Card>

              {/* Gift Options */}
              <Card className="p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <Gift className="w-5 h-5 text-purple-600" />
                  <h3 className="text-lg text-slate-900">Gift Options</h3>
                </div>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">This is a gift</span>
                </label>
                <p className="text-xs text-muted-foreground mt-2">
                  We'll include a gift message and hide prices
                </p>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
