'use client'

import { useState, useEffect } from 'react'
import { ImageWithFallback } from './figma/ImageWithFallback'
import { ChevronLeft, ChevronRight } from 'lucide-react'

const carouselItems = [
  {
    image: 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
    title: 'Connect with Your Team',
    description: 'Collaborate seamlessly with colleagues and bring your ideas to life together.'
  },
  {
    image: 'https://images.unsplash.com/photo-1553877522-43269d4ea984?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
    title: 'Achieve Your Goals',
    description: 'Set meaningful objectives and track your progress with powerful analytics and insights.'
  },
  {
    image: 'https://images.unsplash.com/photo-1556761175-b413da4baf72?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
    title: 'Grow Your Business',
    description: 'Scale your operations with tools designed to help you reach new heights of success.'
  }
]

export function SignupCarousel() {
  const [currentSlide, setCurrentSlide] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % carouselItems.length)
    }, 5000) // Auto-advance every 5 seconds

    return () => clearInterval(timer)
  }, [])

  const goToSlide = (index: number) => {
    setCurrentSlide(index)
  }

  const goToPrevious = () => {
    setCurrentSlide((prev) => (prev - 1 + carouselItems.length) % carouselItems.length)
  }

  const goToNext = () => {
    setCurrentSlide((prev) => (prev + 1) % carouselItems.length)
  }

  return (
    <div className="relative h-full bg-gradient-to-br from-blue-600 to-purple-700 overflow-hidden">
      {/* Background Images */}
      {carouselItems.map((item, index) => (
        <div
          key={index}
          className={`absolute inset-0 transition-opacity duration-1000 ${
            index === currentSlide ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <ImageWithFallback
            src={item.image}
            alt={item.title}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-black/40" />
        </div>
      ))}

      {/* Content Overlay */}
      <div className="relative z-10 flex flex-col justify-center h-full p-12 text-white">
        <div className="max-w-md">
          <div className="transition-all duration-500 transform">
            <h2 className="mb-4 text-white">
              {carouselItems[currentSlide].title}
            </h2>
            <p className="text-white/90 mb-8">
              {carouselItems[currentSlide].description}
            </p>
          </div>

          {/* Navigation Controls */}
          <div className="flex items-center space-x-4">
            <button
              onClick={goToPrevious}
              className="p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
              aria-label="Previous slide"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            
            {/* Dots Indicator */}
            <div className="flex space-x-2">
              {carouselItems.map((_, index) => (
                <button
                  key={index}
                  onClick={() => goToSlide(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentSlide ? 'bg-white w-6' : 'bg-white/50'
                  }`}
                  aria-label={`Go to slide ${index + 1}`}
                />
              ))}
            </div>

            <button
              onClick={goToNext}
              className="p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
              aria-label="Next slide"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}