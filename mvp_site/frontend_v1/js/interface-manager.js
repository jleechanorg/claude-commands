/**
 * Interface Manager - Modern Interface System
 * Controls Modern Mode interface features
 */

class InterfaceManager {
  constructor() {
    this.modes = {
      modern: {
        name: 'Modern Interface',
        icon: '✨',
        description: 'Enhanced with animations and modern UX',
      },
    };

    // Always use modern mode
    this.currentMode = 'modern';
    localStorage.setItem('interface_mode', 'modern');
    this.init();
  }

  init() {
    this.applyMode(this.currentMode);
    this.setupEventListeners();
    this.updateModeIndicator();
    console.log(`🎛️ Interface Manager initialized in ${this.currentMode} mode`);
  }

  setMode(modeName) {
    if (!this.modes[modeName]) {
      console.warn(`Interface mode '${modeName}' not found`);
      return;
    }

    this.currentMode = modeName;
    localStorage.setItem('interface_mode', modeName);

    console.log(`🔄 Switching to ${modeName} mode...`);
    this.applyMode(modeName);
    this.updateModeIndicator();

    // Dispatch event for other components
    window.dispatchEvent(
      new CustomEvent('interfaceModeChanged', {
        detail: { mode: modeName },
      }),
    );
  }

  applyMode(mode) {
    document.body.setAttribute('data-interface-mode', mode);
    this.enableModernMode();
  }

  enableModernMode() {
    // Enable modern features progressively
    this.enableAnimations();
    this.enableEnhancedComponents();
    this.enableModernThemes();
    this.enableInteractiveFeatures();

    document.body.classList.add('modern-mode');

    console.log('✨ Modern interface activated - enhanced features enabled');
  }

  // Animation System Control
  disableAnimations() {
    const animationCSS = document.querySelector('link[href*="animations.css"]');
    if (animationCSS) {
      animationCSS.disabled = true;
    }

    if (window.animationHelpers) {
      window.animationHelpers.disable?.();
    }
  }

  enableAnimations() {
    const animationCSS = document.querySelector('link[href*="animations.css"]');
    if (animationCSS) {
      animationCSS.disabled = false;
    }

    if (window.animationHelpers) {
      window.animationHelpers.enable?.();
    }
  }

  // Enhanced Components Control
  disableEnhancedComponents() {
    localStorage.setItem('feature_enhanced_components', 'false');

    if (window.componentEnhancer) {
      window.componentEnhancer.disable();
    }
  }

  enableEnhancedComponents() {
    localStorage.setItem('feature_enhanced_components', 'true');

    if (window.componentEnhancer) {
      window.componentEnhancer.enable();
    }
  }

  // Modern Theme System Control
  disableModernThemes() {
    localStorage.setItem('feature_new_themes', 'false');

    if (window.themeManager) {
      window.themeManager.modernThemesEnabled = false;
    }
  }

  enableModernThemes() {
    localStorage.setItem('feature_new_themes', 'true');

    if (window.themeManager) {
      window.themeManager.modernThemesEnabled = true;
    }
  }

  // Interactive Features Control (Milestone 4)
  disableInteractiveFeatures() {
    localStorage.setItem('feature_interactive_features', 'false');
    document.body.classList.remove('interactive-features-enabled');
  }

  enableInteractiveFeatures() {
    localStorage.setItem('feature_interactive_features', 'true');
    document.body.classList.add('interactive-features-enabled');
  }

  setupEventListeners() {
    // Handle interface mode selection clicks
    document.addEventListener('click', (e) => {
      const modeItem = e.target.closest('[data-interface-mode-item]');
      if (modeItem) {
        e.preventDefault();
        const mode = modeItem.getAttribute('data-interface-mode');
        this.setMode(mode);
      }
    });
  }

  updateModeIndicator() {
    // Update mode indicator in UI
    const modeIcon = document.getElementById('current-mode-icon');
    if (modeIcon) {
      modeIcon.textContent = this.modes[this.currentMode].icon;
    }

    // Update active menu item
    document.querySelectorAll('[data-interface-mode-item]').forEach((item) => {
      item.classList.remove('active');
    });

    const currentItem = document.querySelector(
      `[data-interface-mode-item][data-interface-mode="${this.currentMode}"]`,
    );
    if (currentItem) {
      currentItem.classList.add('active');
    }
  }

  getCurrentMode() {
    return this.currentMode;
  }

  getModeInfo(modeName) {
    return this.modes[modeName] || null;
  }

  isModernMode() {
    return this.currentMode === 'modern';
  }

  // Feature-specific checks
  isFeatureEnabled(featureName) {
    switch (featureName) {
      case 'animations':
        return localStorage.getItem('feature_animations') !== 'false';
      case 'enhanced_components':
        return localStorage.getItem('feature_enhanced_components') === 'true';
      case 'interactive_features':
        return localStorage.getItem('feature_interactive_features') === 'true';
      default:
        return true;
    }
  }

  // Utility methods

  // Analytics and tracking
  trackModeUsage() {
    const usage = JSON.parse(localStorage.getItem('mode_usage') || '{}');
    const today = new Date().toDateString();

    if (!usage[today]) {
      usage[today] = { modern: 0 };
    }

    usage[today]['modern']++;
    localStorage.setItem('mode_usage', JSON.stringify(usage));
  }
}

// Initialize interface manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.interfaceManager = new InterfaceManager();

  // Track session for analytics
  const sessions = parseInt(localStorage.getItem('user_sessions') || '0') + 1;
  localStorage.setItem('user_sessions', sessions.toString());
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = InterfaceManager;
}
