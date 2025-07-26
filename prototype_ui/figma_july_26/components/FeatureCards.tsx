import { Crown, BookOpen, Globe } from 'lucide-react'

export function FeatureCards() {
  const features = [
    {
      icon: Crown,
      title: 'AI Game Master',
      description: 'Experience dynamic storytelling powered by an advanced AI that adapts to your choices'
    },
    {
      icon: BookOpen,
      title: 'Rich Storytelling',
      description: 'Explore immersive worlds with deep lore, unique characters, and endless possibilities'
    },
    {
      icon: Globe,
      title: 'Dynamic World',
      description: 'Create and evolve your hero through meaningful choices that the world will react and adapt to.'
    }
  ]

  return (
    <div className="max-w-6xl mx-auto">
      {/* Mobile: Vertical stack, Desktop: Horizontal row */}
      <div className="flex flex-col gap-4 sm:gap-6 md:flex-row md:justify-center md:items-center md:gap-8">
        {features.map((feature, index) => {
          const Icon = feature.icon
          return (
            <div key={index} className="bg-black/50 backdrop-blur-md rounded-lg border border-purple-300/30 hover:border-purple-200/50 hover:bg-black/40 transition-all duration-300 p-4 sm:p-6 min-h-[180px] sm:min-h-[200px] md:w-80 md:h-48 flex flex-col items-center justify-center text-center">
              <div className="w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 mb-3 sm:mb-4 bg-purple-500/30 rounded-full flex items-center justify-center backdrop-blur-sm border border-purple-300/40">
                <Icon className="w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8 text-purple-100" />
              </div>
              <h3 className="text-white text-lg sm:text-xl mb-2 sm:mb-3 drop-shadow-lg">{feature.title}</h3>
              <p className="text-purple-100 text-xs sm:text-sm leading-relaxed drop-shadow-md">{feature.description}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}