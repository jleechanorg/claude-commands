import { Badge } from './ui/badge'
import { Avatar, AvatarFallback } from './ui/avatar'

export function Header() {
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

        {/* Profile Section */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          <div className="text-right hidden md:block">
            <p className="text-white">Epic Adventurer</p>
            <p className="text-purple-200 text-sm">adventurer@worldai.com</p>
          </div>
          <Avatar className="w-8 h-8 sm:w-10 sm:h-10">
            <AvatarFallback className="bg-purple-600 text-white text-sm">EA</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  )
}
