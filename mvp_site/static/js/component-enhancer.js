/**
 * Component Enhancer - Component Enhancement Milestone
 * Adds modern interactive behaviors to existing Bootstrap components
 * Feature flag controlled: feature_enhanced_components
 */

class ComponentEnhancer {
  constructor() {
    this.isEnhanced = false;
    this.rippleTimeout = null;

    // Configuration
    this.config = {
      rippleDuration: 600,
      loadingMinDuration: 500,
      debounceDelay: 100,
    };

    console.log('ComponentEnhancer initialized');
  }

  /**
   * Check if enhanced components feature is enabled
   */
  isFeatureEnabled() {
    return localStorage.getItem('feature_enhanced_components') === 'true';
  }

  /**
   * Main initialization method
   */
  init() {
    if (!this.isFeatureEnabled()) {
      console.log('Enhanced components feature is disabled');
      return;
    }

    // TEMPORARILY DISABLED - CSS conflicts causing layout issues
    console.log(
      'Enhanced components temporarily disabled due to layout conflicts',
    );
    return;

    this.loadEnhancedCSS();
    this.enhanceExistingComponents();
    this.setupEventListeners();
    this.setupMutationObserver();

    this.isEnhanced = true;
    console.log('Component enhancement activated');

    // Dispatch custom event
    window.dispatchEvent(
      new CustomEvent('componentsEnhanced', {
        detail: { timestamp: Date.now() },
      }),
    );
  }

  /**
   * Load enhanced components CSS
   */
  loadEnhancedCSS() {
    // DISABLED - CSS causing layout conflicts
    console.log(
      'Enhanced components CSS loading disabled due to layout conflicts',
    );
    return;

    const existingLink = document.querySelector(
      'link[href*="enhanced-components.css"]',
    );
    if (existingLink) return;

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/static/styles/enhanced-components.css';
    link.id = 'enhanced-components-css';
    document.head.appendChild(link);

    console.log('Enhanced components CSS loaded');
  }

  /**
   * Enhance all existing components on the page
   */
  enhanceExistingComponents() {
    this.enhanceButtons();
    this.enhanceCards();
    this.enhanceForms();
    this.enhanceModals();
    this.enhanceNavigation();
    this.enhanceContent();
    this.enhanceLoadingStates();
  }

  /**
   * Enhance all buttons with modern interactions
   */
  enhanceButtons() {
    const buttons = document.querySelectorAll(
      '.btn:not(.btn-enhanced):not(.dropdown-toggle)',
    );

    buttons.forEach((button) => {
      button.classList.add('btn-enhanced');

      // Add ripple effect (don't interfere with dropdown buttons)
      if (!button.closest('.dropdown')) {
        button.addEventListener('click', this.createRippleEffect.bind(this));
      }

      // Add loading state capability (only for form submit buttons)
      if (button.type === 'submit' || button.form) {
        button.addEventListener('click', this.handleButtonLoading.bind(this));
      }
    });

    console.log(`Enhanced ${buttons.length} buttons`);
  }

  /**
   * Enhance cards and list items
   */
  enhanceCards() {
    // Enhance cards
    const cards = document.querySelectorAll('.card:not(.card-enhanced)');
    cards.forEach((card) => card.classList.add('card-enhanced'));

    // Enhance list group items (campaign list)
    const listItems = document.querySelectorAll(
      '.list-group-item:not(.list-group-item-enhanced)',
    );
    listItems.forEach((item) => {
      item.classList.add('list-group-item-enhanced');

      // Add hover sound effect placeholder
      item.addEventListener('mouseenter', this.playHoverSound.bind(this));
    });

    console.log(
      `Enhanced ${cards.length} cards and ${listItems.length} list items`,
    );
  }

  /**
   * Enhance form elements
   */
  enhanceForms() {
    // Enhance form controls
    const formControls = document.querySelectorAll(
      '.form-control:not(.form-control-enhanced)',
    );
    formControls.forEach((control) => {
      control.classList.add('form-control-enhanced');

      // Add focus/blur animations
      control.addEventListener('focus', this.handleFormFocus.bind(this));
      control.addEventListener('blur', this.handleFormBlur.bind(this));
    });

    // Enhance form labels
    const formLabels = document.querySelectorAll(
      '.form-label:not(.form-label-enhanced)',
    );
    formLabels.forEach((label) => label.classList.add('form-label-enhanced'));

    // Enhance form checks (checkboxes and radios)
    const formChecks = document.querySelectorAll(
      '.form-check:not(.form-check-enhanced)',
    );
    formChecks.forEach((check) => check.classList.add('form-check-enhanced'));

    // Enhance input groups
    const inputGroups = document.querySelectorAll(
      '.input-group:not(.input-group-enhanced)',
    );
    inputGroups.forEach((group) => group.classList.add('input-group-enhanced'));

    console.log(
      `Enhanced ${formControls.length} form controls, ${formLabels.length} labels, ${formChecks.length} form checks, ${inputGroups.length} input groups`,
    );
  }

  /**
   * Enhance modals
   */
  enhanceModals() {
    const modals = document.querySelectorAll('.modal:not(.modal-enhanced)');
    modals.forEach((modal) => {
      modal.classList.add('modal-enhanced');

      // Add show/hide animations
      modal.addEventListener('show.bs.modal', this.handleModalShow.bind(this));
      modal.addEventListener('hide.bs.modal', this.handleModalHide.bind(this));
    });

    console.log(`Enhanced ${modals.length} modals`);
  }

  /**
   * Enhance navigation
   */
  enhanceNavigation() {
    // Enhance navbar
    const navbar = document.querySelector('.navbar:not(.navbar-enhanced)');
    if (navbar) {
      navbar.classList.add('navbar-enhanced');
    }

    // Enhance dropdowns (but don't interfere with functionality)
    const dropdowns = document.querySelectorAll(
      '.dropdown:not(.dropdown-enhanced)',
    );
    dropdowns.forEach((dropdown) => {
      dropdown.classList.add('dropdown-enhanced');

      // Add dropdown animation without interfering with Bootstrap
      const menu = dropdown.querySelector('.dropdown-menu');
      if (menu) {
        menu.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      }
    });

    console.log(`Enhanced navbar and ${dropdowns.length} dropdowns`);
  }

  /**
   * Enhance content areas
   */
  enhanceContent() {
    // Enhance story content
    const storyContent = document.querySelector(
      '#story-content:not(.story-content-enhanced)',
    );
    if (storyContent) {
      storyContent.classList.add('story-content-enhanced');
    }

    // Enhance general content areas
    const contentAreas = document.querySelectorAll(
      '.content:not(.content-enhanced)',
    );
    contentAreas.forEach((area) => area.classList.add('content-enhanced'));

    console.log(
      `Enhanced story content and ${contentAreas.length} content areas`,
    );
  }

  /**
   * Enhance loading states
   */
  enhanceLoadingStates() {
    // Enhance spinners
    const spinners = document.querySelectorAll(
      '.spinner-border:not(.spinner-enhanced)',
    );
    spinners.forEach((spinner) => spinner.classList.add('spinner-enhanced'));

    // Enhance loading overlay
    const loadingOverlay = document.querySelector(
      '#loading-overlay:not(.loading-overlay-enhanced)',
    );
    if (loadingOverlay) {
      loadingOverlay.classList.add('loading-overlay-enhanced');
    }

    console.log(`Enhanced ${spinners.length} spinners and loading overlay`);
  }

  /**
   * Create ripple effect for buttons
   */
  createRippleEffect(event) {
    const button = event.currentTarget;

    // Clear any existing ripple
    if (this.rippleTimeout) {
      clearTimeout(this.rippleTimeout);
      button.classList.remove('ripple-active');
    }

    // Add ripple class
    button.classList.add('ripple-active');

    // Remove ripple after animation
    this.rippleTimeout = setTimeout(() => {
      button.classList.remove('ripple-active');
    }, this.config.rippleDuration);
  }

  /**
   * Handle button loading states
   */
  handleButtonLoading(event) {
    const button = event.currentTarget;
    const form = button.closest('form');

    // Only apply loading to submit buttons in forms
    if (form && (button.type === 'submit' || button.form)) {
      button.classList.add('loading');

      // Store original text
      const originalText = button.textContent;

      // Set minimum loading duration
      setTimeout(() => {
        button.classList.remove('loading');
        button.textContent = originalText;
      }, this.config.loadingMinDuration);
    }
  }

  /**
   * Handle form focus events
   */
  handleFormFocus(event) {
    const control = event.currentTarget;
    const container = control.closest('.mb-3, .form-group, .input-group');

    if (container) {
      container.classList.add('focused');
    }
  }

  /**
   * Handle form blur events
   */
  handleFormBlur(event) {
    const control = event.currentTarget;
    const container = control.closest('.mb-3, .form-group, .input-group');

    if (container) {
      container.classList.remove('focused');
    }
  }

  /**
   * Handle modal show events
   */
  handleModalShow(event) {
    const modal = event.currentTarget;
    modal.style.transform = 'scale(0.8)';
    modal.style.opacity = '0';

    setTimeout(() => {
      modal.style.transform = 'scale(1)';
      modal.style.opacity = '1';
    }, 10);
  }

  /**
   * Handle modal hide events
   */
  handleModalHide(event) {
    const modal = event.currentTarget;
    modal.style.transform = 'scale(0.8)';
    modal.style.opacity = '0';
  }

  /**
   * Placeholder for hover sound effect
   */
  playHoverSound(event) {
    // Placeholder for future audio enhancement
    // console.log('Hover sound effect placeholder');
  }

  /**
   * Setup global event listeners
   */
  setupEventListeners() {
    // Enhanced keyboard navigation
    document.addEventListener(
      'keydown',
      this.handleKeyboardNavigation.bind(this),
    );

    // Enhanced scroll effects
    window.addEventListener(
      'scroll',
      this.debounce(this.handleScroll.bind(this), this.config.debounceDelay),
    );

    // Theme change integration
    window.addEventListener('themeChanged', this.handleThemeChange.bind(this));

    console.log('Component enhancer event listeners setup');
  }

  /**
   * Setup mutation observer for dynamic content
   */
  setupMutationObserver() {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1) {
              // Element node
              this.enhanceNewElement(node);
            }
          });
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    console.log('Component enhancer mutation observer setup');
  }

  /**
   * Enhance newly added elements
   */
  enhanceNewElement(element) {
    // Enhance buttons (but not dropdown toggles)
    const buttons = element.querySelectorAll
      ? element.querySelectorAll(
          '.btn:not(.btn-enhanced):not(.dropdown-toggle)',
        )
      : [];
    buttons.forEach((button) => {
      if (!button.closest('.dropdown')) {
        button.classList.add('btn-enhanced');
        if (button.type === 'submit' || button.form) {
          button.addEventListener('click', this.createRippleEffect.bind(this));
        }
      }
    });

    // Enhance other elements as needed
    if (element.classList) {
      if (
        element.classList.contains('btn') &&
        !element.classList.contains('btn-enhanced') &&
        !element.classList.contains('dropdown-toggle') &&
        !element.closest('.dropdown')
      ) {
        element.classList.add('btn-enhanced');
        if (element.type === 'submit' || element.form) {
          element.addEventListener('click', this.createRippleEffect.bind(this));
        }
      }

      if (
        element.classList.contains('form-control') &&
        !element.classList.contains('form-control-enhanced')
      ) {
        element.classList.add('form-control-enhanced');
        element.addEventListener('focus', this.handleFormFocus.bind(this));
        element.addEventListener('blur', this.handleFormBlur.bind(this));
      }
    }
  }

  /**
   * Handle keyboard navigation enhancements
   */
  handleKeyboardNavigation(event) {
    // Enhanced keyboard shortcuts could go here
    // For now, just ensure accessibility
    if (event.key === 'Tab') {
      document.body.classList.add('keyboard-nav');
    }
  }

  /**
   * Handle scroll events for enhanced effects
   */
  handleScroll() {
    // Could add scroll-based animations here
    // For now, just remove keyboard navigation class
    document.body.classList.remove('keyboard-nav');
  }

  /**
   * Handle theme changes
   */
  handleThemeChange(event) {
    console.log(
      `Component enhancer responding to theme change: ${event.detail.theme}`,
    );
    // Could add theme-specific component adjustments here
  }

  /**
   * Utility: Debounce function
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * Public API: Enable enhanced components
   */
  enable() {
    localStorage.setItem('feature_enhanced_components', 'true');
    this.init();
    console.log('Enhanced components enabled');
  }

  /**
   * Public API: Disable enhanced components
   */
  disable() {
    localStorage.setItem('feature_enhanced_components', 'false');
    this.cleanup();
    console.log('Enhanced components disabled');
  }

  /**
   * Public API: Toggle enhanced components
   */
  toggle() {
    if (this.isFeatureEnabled()) {
      this.disable();
    } else {
      this.enable();
    }
    return this.isFeatureEnabled();
  }

  /**
   * Cleanup enhanced components
   */
  cleanup() {
    // Remove enhanced CSS
    const cssLink = document.querySelector('#enhanced-components-css');
    if (cssLink) {
      cssLink.remove();
    }

    // Also remove any existing enhanced CSS that might be causing conflicts
    const existingEnhancedCSS = document.querySelector(
      'link[href*="enhanced-components.css"]',
    );
    if (existingEnhancedCSS) {
      existingEnhancedCSS.remove();
    }

    // Remove enhanced classes
    const enhancedElements = document.querySelectorAll('[class*="-enhanced"]');
    enhancedElements.forEach((element) => {
      element.className = element.className
        .replace(/\b\w+-enhanced\b/g, '')
        .trim();
    });

    this.isEnhanced = false;

    // Dispatch cleanup event
    window.dispatchEvent(
      new CustomEvent('componentsCleanedUp', {
        detail: { timestamp: Date.now() },
      }),
    );
  }

  /**
   * Get enhancement status
   */
  getStatus() {
    return {
      featureEnabled: this.isFeatureEnabled(),
      isEnhanced: this.isEnhanced,
      enhancedButtons: document.querySelectorAll('.btn-enhanced').length,
      enhancedCards: document.querySelectorAll('.card-enhanced').length,
      enhancedForms: document.querySelectorAll('.form-control-enhanced').length,
    };
  }
}

// Initialize component enhancer when DOM is ready
let componentEnhancer;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    componentEnhancer = new ComponentEnhancer();
    componentEnhancer.init();
  });
} else {
  componentEnhancer = new ComponentEnhancer();
  componentEnhancer.init();
}

// Expose to global scope for debugging and manual control
window.ComponentEnhancer = ComponentEnhancer;
window.componentEnhancer = componentEnhancer;

// Console helper for development
if (
  window.location.hostname === 'localhost' ||
  window.location.hostname.includes('127.0.0.1')
) {
  console.log(
    '%cComponent Enhancer Development Mode',
    'color: #2196F3; font-weight: bold',
  );
  console.log('Available commands:');
  console.log('- componentEnhancer.enable()');
  console.log('- componentEnhancer.disable()');
  console.log('- componentEnhancer.toggle()');
  console.log('- componentEnhancer.getStatus()');
}
