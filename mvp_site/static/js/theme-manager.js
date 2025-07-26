class ThemeManager {
  constructor() {
    this.themes = {
      light: { name: 'Light', icon: '☀️', description: 'Clean and bright' },
      dark: { name: 'Dark', icon: '🌙', description: 'Easy on the eyes' },
      fantasy: {
        name: 'Fantasy',
        icon: '⚔️',
        description: 'Medieval adventure',
      },
      cyberpunk: {
        name: 'Cyberpunk',
        icon: '🤖',
        description: 'Futuristic neon',
      },
    };

    this.currentTheme = 'light';
    // Enable modern features by default (user doesn't need console commands)
    this.modernThemesEnabled =
      localStorage.getItem('feature_new_themes') !== 'false';
    this.init();
  }

  init() {
    // Force cleanup any problematic CSS
    this.forceCleanupProblematicCSS();

    this.loadModernCSS();
    this.loadSavedTheme();
    this.setupEventListeners();
    this.updateThemeIcon();
  }

  forceCleanupProblematicCSS() {
    // Remove any existing problematic CSS files
    const problematicFiles = [
      'globals.css',
      'components.css',
      'bridge.css',
      'enhanced-components.css',
    ];

    problematicFiles.forEach((fileName) => {
      const existing = document.querySelector(`link[href*="${fileName}"]`);
      if (existing) {
        existing.remove();
        console.log(`Removed problematic CSS: ${fileName}`);
      }
    });

    // Remove modern-themes class if it exists
    document.body.classList.remove('modern-themes');

    // Clean up any enhanced classes that might be causing conflicts
    const elementsWithEnhanced = document.querySelectorAll(
      '[class*="-enhanced"]',
    );
    elementsWithEnhanced.forEach((element) => {
      element.className = element.className
        .replace(/\b\w+-enhanced\b/g, '')
        .trim();
    });
  }

  loadModernCSS() {
    if (this.modernThemesEnabled) {
      // TEMPORARILY DISABLED - CSS conflicts causing layout issues
      console.log(
        '🎨 Modern theme system temporarily disabled due to layout conflicts',
      );
      return;

      // Load modern CSS files
      const cssFiles = [
        '/static/styles/globals.css',
        '/static/styles/components.css',
        '/static/styles/bridge.css',
      ];

      cssFiles.forEach((file) => {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = file;
        document.head.appendChild(link);
      });

      // Add a class to body to indicate modern themes are active
      document.body.classList.add('modern-themes');

      console.log('🎨 Modern theme system activated');
    }
  }

  setTheme(themeName) {
    if (!this.themes[themeName]) {
      console.warn(`Theme '${themeName}' not found`);
      return;
    }

    // Add transition class to body for smooth theme switching
    document.body.classList.add('theme-transitioning');

    // Set the theme
    document.documentElement.setAttribute('data-theme', themeName);

    // Save preference
    localStorage.setItem('preferred-theme', themeName);
    this.currentTheme = themeName;

    // Update UI
    this.updateThemeIcon();
    this.updateActiveMenuItem();

    // Remove transition class after animation
    setTimeout(() => {
      document.body.classList.remove('theme-transitioning');
    }, 300);

    // Dispatch custom event for other components
    window.dispatchEvent(
      new CustomEvent('themeChanged', {
        detail: { theme: themeName },
      }),
    );
  }

  loadSavedTheme() {
    const savedTheme = localStorage.getItem('preferred-theme');
    if (savedTheme && this.themes[savedTheme]) {
      this.setTheme(savedTheme);
    } else {
      // Check for system preference
      if (
        window.matchMedia &&
        window.matchMedia('(prefers-color-scheme: dark)').matches
      ) {
        this.setTheme('dark');
      } else {
        this.setTheme('light');
      }
    }
  }

  updateThemeIcon() {
    const iconElement = document.getElementById('current-theme-icon');
    if (iconElement) {
      iconElement.textContent = this.themes[this.currentTheme].icon;
    }
  }

  updateActiveMenuItem() {
    // Remove active class from all theme menu items
    document.querySelectorAll('[data-theme-menu-item]').forEach((item) => {
      item.classList.remove('active');
    });

    // Add active class to current theme
    const currentItem = document.querySelector(
      `[data-theme-menu-item="${this.currentTheme}"]`,
    );
    if (currentItem) {
      currentItem.classList.add('active');
    }
  }

  setupEventListeners() {
    // Handle theme selection clicks - only for dropdown menu items
    document.addEventListener('click', (e) => {
      const themeItem = e.target.closest('[data-theme-menu-item]');
      if (themeItem) {
        e.preventDefault();
        const theme = themeItem.getAttribute('data-theme');
        this.setTheme(theme);
      }
    });

    // Listen for system theme changes
    if (window.matchMedia) {
      window
        .matchMedia('(prefers-color-scheme: dark)')
        .addEventListener('change', (e) => {
          // Only auto-switch if user hasn't manually selected a theme
          if (!localStorage.getItem('preferred-theme')) {
            this.setTheme(e.matches ? 'dark' : 'light');
          }
        });
    }
  }

  getThemeInfo(themeName) {
    return this.themes[themeName] || null;
  }

  getCurrentTheme() {
    return this.currentTheme;
  }

  getAllThemes() {
    return this.themes;
  }

  isModernThemesEnabled() {
    return this.modernThemesEnabled;
  }

  toggleModernThemes() {
    this.modernThemesEnabled = !this.modernThemesEnabled;
    localStorage.setItem(
      'feature_new_themes',
      this.modernThemesEnabled ? 'true' : 'false',
    );

    // Reload the page to apply changes
    window.location.reload();
  }

  // Enhanced Components Integration
  isEnhancedComponentsEnabled() {
    return localStorage.getItem('feature_enhanced_components') === 'true';
  }

  toggleEnhancedComponents() {
    const isEnabled = this.isEnhancedComponentsEnabled();
    localStorage.setItem(
      'feature_enhanced_components',
      !isEnabled ? 'true' : 'false',
    );

    // Use component enhancer if available, otherwise reload
    if (window.componentEnhancer) {
      window.componentEnhancer.toggle();
    } else {
      window.location.reload();
    }

    console.log(`Enhanced components ${!isEnabled ? 'enabled' : 'disabled'}`);
    return !isEnabled;
  }

  enableEnhancedComponents() {
    localStorage.setItem('feature_enhanced_components', 'true');
    if (window.componentEnhancer) {
      window.componentEnhancer.enable();
    } else {
      window.location.reload();
    }
  }

  disableEnhancedComponents() {
    localStorage.setItem('feature_enhanced_components', 'false');
    if (window.componentEnhancer) {
      window.componentEnhancer.disable();
    } else {
      window.location.reload();
    }
  }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.themeManager = new ThemeManager();
});
