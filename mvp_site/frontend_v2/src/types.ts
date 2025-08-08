// Re-export types from api.types for consistency
export type { User, Campaign } from './services/api.types'

export type Theme = 'light' | 'dark' | 'fantasy' | 'dark-fantasy' | 'cyberpunk'

export type AppView = 'home' | 'browse' | 'dashboard' | 'campaign-details' | 'create-campaign' | 'product' | 'cart'

export type Sport = 'All' | 'NFL' | 'NBA' | 'MLB' | 'NHL' | 'Soccer'

export interface Jersey {
  id: string
  name: string
  player: string
  team: string
  number: string
  sport: Sport
  price: number
  size: string
  condition: string
  isAuthentic: boolean
  isVintage: boolean
  imageUrl: string
  description: string
  sellerRating: number
}

