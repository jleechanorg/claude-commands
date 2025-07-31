import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Theme } from '../types/theme';

interface ThemeState {
  // State
  currentTheme: Theme;
  availableThemes: Theme[];

  // Actions
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  applyTheme: (theme: Theme) => void;
}

const THEME_CONFIGS = {
  light: {
    name: 'Light',
    colors: {
      primary: '#6b46c1',
      background: '#ffffff',
      text: '#1a1a1a',
    }
  },
  dark: {
    name: 'Dark',
    colors: {
      primary: '#9333ea',
      background: '#1a1a1a',
      text: '#ffffff',
    }
  },
  fantasy: {
    name: 'Fantasy',
    colors: {
      primary: '#a855f7',
      background: '#2e1065',
      text: '#f3e8ff',
    }
  },
  cyberpunk: {
    name: 'Cyberpunk',
    colors: {
      primary: '#14b8a6',
      background: '#042f2e',
      text: '#5eead4',
    }
  },
  spooky: {
    name: 'Spooky',
    colors: {
      primary: '#dc2626',
      background: '#450a0a',
      text: '#fecaca',
    }
  }
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentTheme: 'fantasy' as Theme,
      availableThemes: ['light', 'dark', 'fantasy', 'cyberpunk', 'spooky'] as Theme[],

      // Set theme
      setTheme: (theme: Theme) => {
        const { applyTheme } = get();
        set({ currentTheme: theme });
        applyTheme(theme);
      },

      // Toggle between themes
      toggleTheme: () => {
        const { currentTheme, availableThemes, setTheme } = get();
        const currentIndex = availableThemes.indexOf(currentTheme);
        const nextIndex = (currentIndex + 1) % availableThemes.length;
        setTheme(availableThemes[nextIndex]);
      },

      // Apply theme to DOM
      applyTheme: (theme: Theme) => {
        // Remove all theme classes
        document.documentElement.classList.remove(...Object.keys(THEME_CONFIGS));

        // Add new theme class
        document.documentElement.classList.add(theme);

        // Apply theme-specific styles
        const config = THEME_CONFIGS[theme];
        if (config) {
          // Set CSS variables for the theme
          const root = document.documentElement;
          root.style.setProperty('--theme-primary', config.colors.primary);
          root.style.setProperty('--theme-background', config.colors.background);
          root.style.setProperty('--theme-text', config.colors.text);

          // Apply theme-specific body styles
          switch (theme) {
            case 'light':
              document.body.style.background = 'linear-gradient(135deg, #e9d5ff, #c084fc)';
              break;
            case 'dark':
              document.body.style.background = 'linear-gradient(135deg, #1e1b4b, #312e81)';
              break;
            case 'fantasy':
              document.body.style.background = 'linear-gradient(135deg, rgb(147 51 234), rgb(126 34 206), rgb(79 70 229))';
              break;
            case 'cyberpunk':
              document.body.style.background = 'linear-gradient(135deg, #134e4a, #0f766e, #14b8a6)';
              break;
            case 'spooky':
              document.body.style.background = 'linear-gradient(135deg, #7f1d1d, #991b1b, #dc2626)';
              break;
          }
        }
      }
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => (state) => {
        // Apply theme on app load
        if (state) {
          state.applyTheme(state.currentTheme);
        }
      }
    }
  )
);
