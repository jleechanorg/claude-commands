class ThemeManager {
  constructor() {
    this.themes = {
      light: { name: 'Light', icon: '☀️', description: 'Clean and bright' },
      dark: { name: 'Dark', icon: '🌙', description: 'Easy on the eyes' },
      fantasy: { name: 'Fantasy', icon: '⚔️', description: 'Medieval adventure' },
      cyberpunk: { name: 'Cyberpunk', icon: '🤖', description: 'Futuristic neon' }
    };
    
    this.currentTheme = 'light';
    this.init();
  }

  init() {
    this.loadSavedTheme();
    this.setupEventListeners();
    this.updateThemeIcon();
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
    window.dispatchEvent(new CustomEvent('themeChanged', { 
      detail: { theme: themeName } 
    }));
  }

  loadSavedTheme() {
    const savedTheme = localStorage.getItem('preferred-theme');
    if (savedTheme && this.themes[savedTheme]) {
      this.setTheme(savedTheme);
    } else {
      // Check for system preference
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
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
    document.querySelectorAll('[data-theme-menu-item]').forEach(item => {
      item.classList.remove('active');
    });
    
    // Add active class to current theme
    const currentItem = document.querySelector(`[data-theme-menu-item="${this.currentTheme}"]`);
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
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
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
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.themeManager = new ThemeManager();
});