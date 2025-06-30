/**
 * Interface Manager - Master Toggle System
 * Controls Classic Mode vs Modern Mode for backward compatibility
 */

class InterfaceManager {
  constructor() {
    this.modes = {
      classic: { 
        name: 'Classic Interface', 
        icon: '📰', 
        description: 'Original familiar interface' 
      },
      modern: { 
        name: 'Modern Interface', 
        icon: '✨', 
        description: 'Enhanced with animations and modern UX' 
      }
    };
    
    // Default to modern mode as requested by user
    this.currentMode = localStorage.getItem('interface_mode') || 'modern';
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
    window.dispatchEvent(new CustomEvent('interfaceModeChanged', { 
      detail: { mode: modeName } 
    }));
  }

  applyMode(mode) {
    document.body.setAttribute('data-interface-mode', mode);
    
    if (mode === 'classic') {
      this.enableClassicMode();
    } else {
      this.enableModernMode();
    }
  }

  enableClassicMode() {
    // Disable all modern features for safety
    this.disableAnimations();
    this.disableEnhancedComponents();
    this.disableModernThemes();
    this.disableInteractiveFeatures();
    
    document.body.classList.add('classic-mode');
    document.body.classList.remove('modern-mode');
    
    console.log('📰 Classic interface activated - all modern features disabled');
  }

  enableModernMode() {
    // Enable modern features progressively
    this.enableAnimations();
    this.enableEnhancedComponents();
    this.enableModernThemes();
    this.enableInteractiveFeatures();
    
    document.body.classList.add('modern-mode');
    document.body.classList.remove('classic-mode');
    
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
    document.querySelectorAll('[data-interface-mode-item]').forEach(item => {
      item.classList.remove('active');
    });
    
    const currentItem = document.querySelector(`[data-interface-mode-item][data-interface-mode="${this.currentMode}"]`);
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

  isClassicMode() {
    return this.currentMode === 'classic';
  }

  // Feature-specific checks
  isFeatureEnabled(featureName) {
    if (this.currentMode === 'classic') {
      return false; // All modern features disabled in classic mode
    }
    
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
  showModePromotion() {
    if (this.currentMode === 'classic') {
      const userSessions = parseInt(localStorage.getItem('user_sessions') || '0');
      
      if (userSessions > 3 && !localStorage.getItem('modern_mode_dismissed')) {
        this.showModernModePromo();
      }
    }
  }

  showModernModePromo() {
    // Create a subtle promotion banner for modern mode
    const promoHTML = `
      <div id="modern-mode-promo" class="alert alert-info alert-dismissible fade show" role="alert">
        <strong>✨ Try the Modern Interface!</strong> 
        Enhanced animations, improved interactions, and a smoother experience.
        <button type="button" class="btn btn-sm btn-outline-primary ms-2" onclick="window.interfaceManager.setMode('modern')">
          Try Modern Mode
        </button>
        <button type="button" class="btn-close" data-bs-dismiss="alert" onclick="localStorage.setItem('modern_mode_dismissed', 'true')"></button>
      </div>
    `;
    
    const container = document.querySelector('.container');
    if (container && !document.getElementById('modern-mode-promo')) {
      container.insertAdjacentHTML('afterbegin', promoHTML);
    }
  }

  // Analytics and tracking
  trackModeUsage() {
    const usage = JSON.parse(localStorage.getItem('mode_usage') || '{}');
    const today = new Date().toDateString();
    
    if (!usage[today]) {
      usage[today] = { classic: 0, modern: 0 };
    }
    
    usage[today][this.currentMode]++;
    localStorage.setItem('mode_usage', JSON.stringify(usage));
  }
}

// Initialize interface manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.interfaceManager = new InterfaceManager();
  
  // Track session for promotion logic
  const sessions = parseInt(localStorage.getItem('user_sessions') || '0') + 1;
  localStorage.setItem('user_sessions', sessions.toString());
  
  // Show promotion after a few sessions
  setTimeout(() => {
    window.interfaceManager.showModePromotion();
  }, 5000);
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = InterfaceManager;
} 