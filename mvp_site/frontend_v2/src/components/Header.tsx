import { Badge } from './ui/badge'
import { Avatar, AvatarFallback } from './ui/avatar'
import { useAuth } from '../hooks/useAuth'

export function Header() {
  const { user, loading } = useAuth()

  return (
    <header className="w-full bg-gradient-to-r from-purple-900/80 to-purple-800/80 backdrop-blur-sm border-b border-purple-700/30">
      <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between">
        {/* Logo and Brand */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
            <span className="text-white text-lg sm:text-xl">🎲</span>
          </div>
          <div>
            <h1 className="text-white text-lg sm:text-xl">WorldAI</h1>
            <p className="text-purple-200 text-xs sm:text-sm">Campaign Dashboard</p>
          </div>
        </div>

        {/* Center Badge - Hidden on small screens, shown on desktop */}
        <Badge variant="outline" className="bg-purple-700/50 text-purple-100 border-purple-500/50 hidden md:inline-flex">
          🌟 Fantasy
        </Badge>

        {/* Profile Section - Enhanced with better transitions */}
        {user && (
          <div className="flex items-center space-x-2 sm:space-x-4 animate-fade-in">
            <div className="text-right hidden md:block">
              <div className="flex items-center gap-2">
                <span className="text-green-400 text-xs">●</span>
                <p className="text-white font-medium">{user.displayName || 'Adventurer'}</p>
              </div>
              <p className="text-purple-200 text-sm">{user.email}</p>
            </div>
            <div className="relative">
              <Avatar className="w-8 h-8 sm:w-10 sm:h-10 ring-2 ring-purple-500/50 hover:ring-purple-400/70 transition-all duration-300">
                <AvatarFallback className="bg-gradient-to-br from-purple-600 to-purple-700 text-white text-sm font-semibold">
                  {user.displayName ? user.displayName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'A'}
                </AvatarFallback>
              </Avatar>
              {/* Online indicator */}
              <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-purple-900 animate-pulse"></div>
            </div>
          </div>
        )}

        {/* Enhanced loading state with branded spinner */}
        {loading && !user && (
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-8 h-8 animate-spin rounded-full border-2 border-purple-300 border-t-purple-600"></div>
              <div className="absolute inset-0 rounded-full border border-purple-400 opacity-20 animate-pulse"></div>
            </div>
            <span className="text-purple-200 text-sm hidden sm:inline">Checking authentication...</span>
          </div>
        )}

        {/* Sign in prompt for unauthenticated users */}
        {!loading && !user && (
          <div className="flex items-center space-x-2 animate-fade-in">
            <div className="text-right hidden md:block">
              <p className="text-purple-200 text-sm">Ready to begin?</p>
              <p className="text-purple-300 text-xs">Sign in to save progress</p>
            </div>
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-purple-600/50 to-purple-700/50 rounded-full flex items-center justify-center border border-purple-500/30">
              <span className="text-purple-300 text-sm">👤</span>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
