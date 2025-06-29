/**
 * Animation Helpers - Milestone 3
 * Utilities for smooth transitions and micro-interactions
 * Works with existing app.js without conflicts
 */

class AnimationHelpers {
  constructor() {
    this.transitionDuration = 300; // matches CSS --animation-duration-normal
    this.activeView = null;
    this.init();
  }

  init() {
    this.enhanceExistingFunctionality();
    this.setupViewTransitions();
    this.setupLoadingStates();
    console.log('🎬 Animation system activated');
  }

  /**
   * Enhance existing app functionality with animations
   */
  enhanceExistingFunctionality() {
    // Enhance existing view switching with animations
    this.interceptViewSwitching();
    
    // Enhance form submissions with loading animations
    this.enhanceFormSubmissions();
    
    // Enhance story content updates with animations
    this.enhanceStoryUpdates();
  }

  /**
   * Smooth view transitions for existing app.js functionality
   */
  interceptViewSwitching() {
    // Store original showView function if it exists
    if (window.showView) {
      this.originalShowView = window.showView;
      
      // Replace with animated version
      window.showView = (viewName) => {
        this.animatedShowView(viewName);
      };
    }
  }

  /**
   * Animated version of showView that works with existing app.js
   */
  animatedShowView(viewName) {
    const newView = document.getElementById(viewName);
    const currentView = document.querySelector('.container > div[id$="-view"]:not([style*="display: none"])');
    
    if (!newView) {
      // Fallback to original function if view not found
      if (this.originalShowView) {
        this.originalShowView(viewName);
      }
      return;
    }

    // If same view, no animation needed
    if (currentView && currentView.id === viewName) {
      return;
    }

    // Start transition
    if (currentView) {
      this.fadeOutView(currentView).then(() => {
        this.fadeInView(newView);
      });
    } else {
      this.fadeInView(newView);
    }

    this.activeView = viewName;
  }

  /**
   * Fade out current view
   */
  fadeOutView(view) {
    return new Promise((resolve) => {
      view.style.opacity = '0';
      view.style.transform = 'translateY(-20px)';
      
      setTimeout(() => {
        view.style.display = 'none';
        resolve();
      }, this.transitionDuration);
    });
  }

  /**
   * Fade in new view
   */
  fadeInView(view) {
    view.style.display = 'block';
    view.classList.add('active');
    
    // Force reflow
    view.offsetHeight;
    
    view.style.opacity = '1';
    view.style.transform = 'translateY(0)';
  }

  /**
   * Setup loading states for existing elements
   */
  setupLoadingStates() {
    // Enhance existing loading overlay
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
      this.originalShowLoading = () => {
        loadingOverlay.style.display = 'flex';
        loadingOverlay.classList.add('show');
      };
      
      this.originalHideLoading = () => {
        loadingOverlay.classList.remove('show');
        setTimeout(() => {
          loadingOverlay.style.display = 'none';
        }, this.transitionDuration);
      };
    }

    // Enhance story loading spinner
    const loadingSpinner = document.getElementById('loading-spinner');
    if (loadingSpinner) {
      // Add smooth show/hide for spinner
      const originalSpinnerShow = () => {
        loadingSpinner.style.display = 'block';
        setTimeout(() => {
          loadingSpinner.style.opacity = '1';
        }, 10);
      };
      
      const originalSpinnerHide = () => {
        loadingSpinner.style.opacity = '0';
        setTimeout(() => {
          loadingSpinner.style.display = 'none';
        }, this.transitionDuration);
      };

      // Make methods available globally for existing app.js
      window.animatedShowSpinner = originalSpinnerShow;
      window.animatedHideSpinner = originalSpinnerHide;
    }
  }

  /**
   * Enhance form submissions with loading animations
   */
  enhanceFormSubmissions() {
    // Campaign creation form
    const campaignForm = document.getElementById('new-campaign-form');
    if (campaignForm) {
      campaignForm.addEventListener('submit', (e) => {
        const submitBtn = campaignForm.querySelector('button[type="submit"]');
        if (submitBtn) {
          this.addButtonLoadingState(submitBtn);
        }
      });
    }

    // Interaction form
    const interactionForm = document.getElementById('interaction-form');
    if (interactionForm) {
      interactionForm.addEventListener('submit', (e) => {
        const submitBtn = interactionForm.querySelector('button[type="submit"]');
        if (submitBtn) {
          this.addButtonLoadingState(submitBtn);
        }
      });
    }
  }

  /**
   * Add loading animation to button
   */
  addButtonLoadingState(button) {
    if (!button) return;
    
    button.classList.add('loading');
    button.disabled = true;
    
    // Auto-remove after reasonable time (in case of errors)
    setTimeout(() => {
      this.removeButtonLoadingState(button);
    }, 30000); // 30 seconds max
  }

  /**
   * Remove loading animation from button
   */
  removeButtonLoadingState(button) {
    if (!button) return;
    
    button.classList.remove('loading');
    button.disabled = false;
  }

  /**
   * Enhance story content updates with animations
   */
  enhanceStoryUpdates() {
    const storyContent = document.getElementById('story-content');
    if (!storyContent) return;

    // Create observer for story content changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          // Animate new story content
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1 && node.tagName === 'P') {
              node.style.opacity = '0';
              node.style.transform = 'translateY(10px)';
              
              setTimeout(() => {
                node.style.opacity = '1';
                node.style.transform = 'translateY(0)';
              }, 50);
            }
          });
        }
      });
    });

    observer.observe(storyContent, {
      childList: true,
      subtree: true
    });

    // Store observer for cleanup if needed
    this.storyObserver = observer;
  }

  /**
   * Setup smooth view transitions
   */
  setupViewTransitions() {
    // Initialize all views with proper states
    const views = document.querySelectorAll('#auth-view, #dashboard-view, #new-campaign-view, #game-view');
    
    views.forEach(view => {
      // Set initial state
      if (view.style.display !== 'none') {
        view.classList.add('active');
      } else {
        view.classList.remove('active');
      }
    });
  }

  /**
   * Animate button clicks for enhanced feedback
   */
  enhanceButtonFeedback() {
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn')) {
        this.animateButtonClick(e.target);
      }
    });
  }

  /**
   * Button click animation
   */
  animateButtonClick(button) {
    button.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
      button.style.transform = '';
    }, 150);
  }

  /**
   * Utility: Show loading state on story content
   */
  showStoryLoading() {
    const storyContent = document.getElementById('story-content');
    if (storyContent) {
      storyContent.classList.add('loading');
    }
  }

  /**
   * Utility: Hide loading state on story content
   */
  hideStoryLoading() {
    const storyContent = document.getElementById('story-content');
    if (storyContent) {
      storyContent.classList.remove('loading');
    }
  }

  /**
   * Public API for existing app.js integration
   */
  getAPI() {
    return {
      showView: (viewName) => this.animatedShowView(viewName),
      showLoading: () => this.originalShowLoading?.(),
      hideLoading: () => this.originalHideLoading?.(),
      addButtonLoading: (btn) => this.addButtonLoadingState(btn),
      removeButtonLoading: (btn) => this.removeButtonLoadingState(btn),
      showStoryLoading: () => this.showStoryLoading(),
      hideStoryLoading: () => this.hideStoryLoading()
    };
  }
}

// Initialize animation helpers when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const animationHelpers = new AnimationHelpers();
  
  // Make API available globally for existing app.js
  window.animations = animationHelpers.getAPI();
  window.animationHelpers = animationHelpers;
});

// Helper function for smooth scrolling
function smoothScrollTo(element, offset = 0) {
  if (!element) return;
  
  const targetPosition = element.offsetTop - offset;
  window.scrollTo({
    top: targetPosition,
    behavior: 'smooth'
  });
}

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AnimationHelpers;
} 