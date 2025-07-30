// Loading Messages Module - TASK-005b

class LoadingMessages {
  constructor() {
    // Different message sets for different contexts
    this.messages = {
      newCampaign: [
        '🎲 Rolling for initiative...',
        '🏰 Building your world...',
        '🐉 Awakening ancient dragons...',
        '📜 Writing your destiny...',
        '⚔️ Forging legendary weapons...',
        '🌟 Gathering magical energy...',
        '🗺️ Drawing the map...',
        '🎭 Creating memorable NPCs...',
      ],
      interaction: [
        '🤔 The DM is thinking...',
        '🎲 Rolling dice...',
        '📖 Checking the rulebook...',
        '🗣️ NPCs are discussing...',
        '⚡ Calculating outcomes...',
        '🎯 Determining results...',
        '🌍 Updating the world...',
        '✨ Weaving magic...',
      ],
      loading: [
        '📚 Loading your adventure...',
        '🔮 Consulting the oracle...',
        '🏃 Gathering your party...',
        '💾 Retrieving saved data...',
        '🎪 Setting up the scene...',
        '🧙 Summoning the Game Master...',
      ],
      saving: [
        '💾 Saving your progress...',
        '📝 Recording your deeds...',
        '🏛️ Updating the archives...',
        '✍️ Writing to the chronicle...',
      ],
    };

    this.currentInterval = null;
    this.currentIndex = 0;
    this.currentContext = 'loading';
  }

  // Start showing messages for a specific context
  start(context = 'loading', targetElement = null) {
    // Clear any existing interval
    this.stop();

    // Get the appropriate message container
    const element = targetElement || this.getMessageElement();
    if (!element) return;

    // Set context and reset index
    this.currentContext = context;
    this.currentIndex = 0;

    // Get messages for this context
    const messages = this.messages[context] || this.messages.loading;

    // Show first message immediately
    this.showMessage(element, messages[this.currentIndex]);

    // Rotate through messages
    this.currentInterval = setInterval(() => {
      this.currentIndex = (this.currentIndex + 1) % messages.length;
      this.showMessage(element, messages[this.currentIndex]);
    }, 3000); // Change message every 3 seconds
  }

  // Stop showing messages
  stop() {
    if (this.currentInterval) {
      clearInterval(this.currentInterval);
      this.currentInterval = null;
    }

    // Hide all message elements
    const elements = document.querySelectorAll('.loading-message');
    elements.forEach((el) => {
      el.classList.remove('active');
      el.textContent = '';
    });
  }

  // Show a specific message with fade animation
  showMessage(element, message) {
    // Fade out
    element.classList.remove('active');

    // Change message and fade in after a short delay
    setTimeout(() => {
      element.textContent = message;
      element.classList.add('active');
    }, 200);
  }

  // Get the appropriate message element based on what's visible
  getMessageElement() {
    // Check if overlay is visible
    const overlay = document.getElementById('loading-overlay');
    if (overlay && overlay.style.display !== 'none') {
      return overlay.querySelector('.loading-message');
    }

    // Check if inline spinner is visible
    const spinner = document.getElementById('loading-spinner');
    if (spinner && spinner.style.display !== 'none') {
      return spinner.querySelector('.loading-message');
    }

    return null;
  }

  // Show a single message without rotation
  showSingle(message, duration = 3000) {
    const element = this.getMessageElement();
    if (!element) return;

    this.stop();
    this.showMessage(element, message);

    if (duration > 0) {
      setTimeout(() => this.stop(), duration);
    }
  }
}

// Export as global for use in app.js
window.loadingMessages = new LoadingMessages();
