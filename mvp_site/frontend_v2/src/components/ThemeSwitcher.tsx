'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from './ui/dropdown-menu'
import { Badge } from './ui/badge'
import {
  Palette,
  Sun,
  Moon,
  Crown,
  Zap,
  Check,
  Skull
} from 'lucide-react'
import type { Theme } from '../App'

interface ThemeSwitcherProps {
  currentTheme: Theme
  onThemeChange: (theme: Theme) => void
}

export function ThemeSwitcher({ currentTheme, onThemeChange }: ThemeSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false)

  const themes = [
    {
      id: 'light' as Theme,
      name: 'Light',
      description: 'Clean and bright interface',
      icon: Sun,
    },
    {
      id: 'dark' as Theme,
      name: 'Dark',
      description: 'Easy on the eyes',
      icon: Moon,
    },
    {
      id: 'fantasy' as Theme,
      name: 'Fantasy',
      description: 'Mystical purple realm',
      icon: Crown,
    },
    {
      id: 'dark-fantasy' as Theme,
      name: 'Dark Fantasy',
      description: 'Gothic mystical realm',
      icon: Skull,
    },
    {
      id: 'cyberpunk' as Theme,
      name: 'Cyberpunk',
      description: 'Neon-lit future',
      icon: Zap,
    }
  ]

  const currentThemeData = themes.find(t => t.id === currentTheme)

  const handleThemeSelect = (theme: Theme) => {
    onThemeChange(theme)
    setIsOpen(false)
  }

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="text-foreground/80 hover:text-foreground hover:bg-accent/20 transition-colors border-0 shadow-none"
        >
          <Palette className="w-4 h-4 mr-2" />
          <span className="hidden sm:inline">{currentThemeData?.name || 'Theme'}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="w-64 bg-popover/95 backdrop-blur-sm border-border shadow-lg"
        sideOffset={8}
      >
        <div className="px-3 py-2 text-sm text-popover-foreground/70 border-b border-border">
          Choose Theme
        </div>
        {themes.map((theme, index) => (
          <div key={theme.id}>
            <DropdownMenuItem
              onClick={() => handleThemeSelect(theme.id)}
              className="flex items-center space-x-3 p-3 cursor-pointer hover:bg-accent/20 focus:bg-accent/20 rounded-sm transition-colors"
            >
              <div className="w-8 h-8 bg-primary/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <theme.icon className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <span className="text-popover-foreground truncate">{theme.name}</span>
                  {currentTheme === theme.id && (
                    <Badge variant="secondary" className="text-xs flex-shrink-0">
                      Active
                    </Badge>
                  )}
                </div>
                <p className="text-popover-foreground/70 text-xs truncate">
                  {theme.description}
                </p>
              </div>
              {currentTheme === theme.id && (
                <Check className="w-4 h-4 text-primary flex-shrink-0" />
              )}
            </DropdownMenuItem>
            {index < themes.length - 1 && (
              <DropdownMenuSeparator className="mx-2" />
            )}
          </div>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
