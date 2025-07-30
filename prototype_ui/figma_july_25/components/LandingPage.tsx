'use client'

import { useState } from 'react'
import backgroundImage from 'figma:asset/11638f062b57e33399d25c2ad25dfa18dc0824c3.png'

interface LandingPageProps {
  onLogin: () => void
}

export function LandingPage({ onLogin }: LandingPageProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleSignIn = () => {
    setIsLoading(true)
    setTimeout(() => {
      onLogin()
      setIsLoading(false)
    }, 1500)
  }

  const features = [
    { title: 'AI Game Master', description: 'Dynamic storytelling powered by AI', icon: '👑' },
    { title: 'Rich Storytelling', description: 'Immersive worlds and characters', icon: '📚' },
    { title: 'Epic Adventures', description: 'Create and evolve your hero', icon: '⚔️' },
    { title: 'Fantasy Worlds', description: 'Explore mystical realms', icon: '🏰' },
    { title: 'Instant Play', description: 'Start adventures immediately', icon: '⚡' },
    { title: 'Create Campaign', description: 'Begin your journey today', icon: '▶️', isAction: true }
  ]

  return (
    <div className="min-h-screen relative">
      {/* Purple Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900" />

      {/* Subtle Pattern Overlay */}
      <div className="absolute inset-0 bg-black/20" />

      {/* Content */}
      <div className="relative z-10 min-h-screen">
        {/* Header */}
        <header className="p-8">
          <h1 className="text-white text-2xl">WorldArchitect.AI</h1>
        </header>

        {/* Main Content */}
        <main className="px-8">
          {/* Title Section */}
          <div className="text-center mb-20 pt-20">
            <h1 className="text-6xl md:text-8xl text-white drop-shadow-2xl">
              Welcome, Epic
            </h1>
          </div>

          {/* Feature Cards */}
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className={`
                    bg-purple-900/40 backdrop-blur-sm border border-purple-300/20 rounded-lg p-6
                    hover:bg-purple-800/50 transition-all duration-300 cursor-pointer
                    ${feature.isAction ? 'ring-2 ring-purple-400/60' : ''}
                  `}
                  onClick={feature.isAction ? handleSignIn : undefined}
                >
                  <div className="text-center">
                    <div className="text-4xl mb-4">{feature.icon}</div>
                    <h3 className="text-xl text-white mb-2">{feature.title}</h3>
                    <p className="text-purple-100 text-sm mb-4">{feature.description}</p>

                    {feature.isAction && (
                      <button
                        onClick={handleSignIn}
                        disabled={isLoading}
                        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-2 px-4 rounded transition-all duration-300"
                      >
                        {isLoading ? (
                          <div className="flex items-center justify-center space-x-2">
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            <span>Starting...</span>
                          </div>
                        ) : (
                          'Begin Adventure'
                        )}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom CTA */}
          <div className="text-center mt-16 pb-16">
            <p className="text-purple-100 mb-6">Ready to start your epic journey?</p>
            <button
              onClick={handleSignIn}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-3 px-8 rounded-lg text-lg transition-all duration-300"
            >
              🚀 Continue with Google
            </button>
            <p className="text-xs text-purple-200 mt-2">
              This is a demo - clicking will simulate Google Sign-In
            </p>
          </div>
        </main>
      </div>
    </div>
  )
}
