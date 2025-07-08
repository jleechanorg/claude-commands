/**
 * Campaign Wizard - Milestone 4 Interactive Features
 * Multi-step guided campaign creation with progress tracking
 */

class CampaignWizard {
  constructor() {
    this.currentStep = 1;
    this.totalSteps = 4;
    this.formData = {};
    this.isEnabled = false;
    this.init();
  }

  init() {
    this.checkIfEnabled();
    if (this.isEnabled) {
      this.setupWizard();
      this.setupEventListeners();
      console.log('🧙‍♂️ Campaign Wizard activated');
    }
  }

  checkIfEnabled() {
    // Only enable in modern mode
    if (window.interfaceManager && window.interfaceManager.isModernMode()) {
      this.isEnabled = true;
    }

    // Listen for interface mode changes
    window.addEventListener('interfaceModeChanged', (e) => {
      if (e.detail.mode === 'modern') {
        this.enable();
      } else {
        this.disable();
      }
    });
  }

  enable() {
    this.isEnabled = true;
    this.forceCleanRecreation();
  }

  disable() {
    this.isEnabled = false;
    this.restoreOriginalForm();
  }

  forceCleanRecreation() {
    // Complete cleanup - remove everything related to wizard
    const existingWizard = document.getElementById('campaign-wizard');
    const existingSpinner = document.getElementById('campaign-creation-spinner');
    const originalForm = document.getElementById('new-campaign-form');

    // Remove any wizard or spinner remnants
    if (existingWizard) {
      existingWizard.remove();
    }
    if (existingSpinner) {
      existingSpinner.remove();
    }

    // Ensure original form is visible and clean
    if (originalForm) {
      originalForm.style.display = 'block';
      originalForm.classList.remove('wizard-replaced');
    }

    // Create completely fresh wizard - skip cleanup since we just did it
    this.replaceOriginalForm(true);
    
    // CRITICAL: Ensure wizard content is visible (fix showDetailedSpinner hidden state)
    setTimeout(() => {
      const wizardContent = document.querySelector('.wizard-content');
      const wizardNav = document.querySelector('.wizard-navigation');
      
      if (wizardContent) {
        wizardContent.style.display = 'block';
      }
      if (wizardNav) {
        wizardNav.style.display = 'block';
      }
    }, 50);
    
    // Reset wizard state to defaults
    this.currentStep = 1;
    this.formData = {};
    
    // Set up event listeners for the new wizard
    this.setupEventListeners();
  }

  setupWizard() {
    this.replaceOriginalForm();
  }

  replaceOriginalForm(skipCleanup = false) {
    const originalForm = document.getElementById('new-campaign-form');
    if (!originalForm) {
      return;
    }

    // Only do cleanup if not skipped (prevents race condition with forceCleanRecreation)
    if (!skipCleanup) {
      // Remove any existing wizard to ensure clean state
      const existingWizard = document.getElementById('campaign-wizard');
      if (existingWizard) {
        existingWizard.remove();
      }

      // Remove any leftover spinner elements
      const existingSpinner = document.getElementById('campaign-creation-spinner');
      if (existingSpinner) {
        existingSpinner.remove();
      }
    }

    // Reset original form state
    originalForm.style.display = 'none';
    originalForm.classList.add('wizard-replaced');

    // Create fresh wizard
    const wizardHTML = this.generateWizardHTML();
    originalForm.insertAdjacentHTML('afterend', wizardHTML);

    // Reset wizard state to defaults
    this.currentStep = 1;
    
    this.setupStepNavigation();
    this.populateFromOriginalForm();
  }

  restoreOriginalForm() {
    const originalForm = document.getElementById('new-campaign-form');
    const wizardContainer = document.getElementById('campaign-wizard');
    const spinnerContainer = document.getElementById('campaign-creation-spinner');

    if (originalForm) {
      originalForm.style.display = 'block';
      originalForm.classList.remove('wizard-replaced');
    }
    
    if (wizardContainer) {
      wizardContainer.remove();
    }
    
    // Clean up any leftover spinner
    if (spinnerContainer) {
      spinnerContainer.remove();
    }
  }

  generateWizardHTML() {
    return `
      <div id="campaign-wizard" class="campaign-wizard">
        <!-- Progress Bar -->
        <div class="wizard-progress mb-4">
          <div class="progress" style="height: 8px;">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 id="wizard-progress-bar" 
                 role="progressbar" 
                 style="width: 25%"></div>
          </div>
          <div class="step-indicators mt-2 d-flex justify-content-between">
            <div class="step-indicator active" data-step="1">
              <div class="step-circle">1</div>
              <div class="step-label">Basics</div>
            </div>
            <div class="step-indicator" data-step="2">
              <div class="step-circle">2</div>
              <div class="step-label">AI Style</div>
            </div>
            <div class="step-indicator" data-step="3">
              <div class="step-circle">3</div>
              <div class="step-label">Options</div>
            </div>
            <div class="step-indicator" data-step="4">
              <div class="step-circle">4</div>
              <div class="step-label">Launch</div>
            </div>
          </div>
        </div>

        <!-- Step Content -->
        <div class="wizard-content">
          <!-- Step 1: Basic Info -->
          <div class="wizard-step active" data-step="1">
            <h3 class="step-title">📝 Campaign Basics</h3>
            <p class="step-description">Let's start with the fundamentals of your adventure.</p>
            
            <div class="mb-4">
              <label for="wizard-campaign-title" class="form-label">
                Campaign Title <span class="text-muted">(Pick anything!)</span>
              </label>
              <input type="text" class="form-control form-control-lg" 
                     id="wizard-campaign-title" 
                     placeholder="My Epic Adventure"
                     required>
              <div class="form-text">This helps you identify your campaign in the dashboard.</div>
            </div>

            <!-- Campaign Type Selection -->
            <div class="mb-4">
              <label class="form-label">Campaign Type</label>
              <div class="campaign-type-cards">
                <div class="campaign-type-card selected" data-type="dragon-knight">
                  <input class="form-check-input" type="radio" name="wizardCampaignType" 
                         id="wizard-dragonKnightCampaign" value="dragon-knight" checked>
                  <label class="campaign-type-label" for="wizard-dragonKnightCampaign">
                    <div class="campaign-type-icon">🐲</div>
                    <div class="campaign-type-content">
                      <h5>Dragon Knight Campaign</h5>
                      <p class="text-muted mb-0">Play as Ser Arion in a morally complex world. Perfect for new players!</p>
                    </div>
                  </label>
                </div>
                
                <div class="campaign-type-card" data-type="custom">
                  <input class="form-check-input" type="radio" name="wizardCampaignType" 
                         id="wizard-customCampaign" value="custom">
                  <label class="campaign-type-label" for="wizard-customCampaign">
                    <div class="campaign-type-icon">✨</div>
                    <div class="campaign-type-content">
                      <h5>Custom Campaign</h5>
                      <p class="text-muted mb-0">Create your own unique world and story from scratch.</p>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div class="mb-4">
              <label for="wizard-campaign-prompt" class="form-label">
                <span id="wizard-prompt-label">Campaign Description</span>
              </label>
              <textarea class="form-control" 
                        id="wizard-campaign-prompt" 
                        rows="4"
                        placeholder="Loading Dragon Knight campaign..."
                        readonly
                        required></textarea>
              <div class="form-text" id="wizard-prompt-help">
                This campaign uses the pre-written Dragon Knight story. Switch to Custom Campaign to write your own.
              </div>
            </div>
          </div>

          <!-- Step 2: AI Personality -->
          <div class="wizard-step" data-step="2">
            <h3 class="step-title">🤖 Choose Your AI's Expertise</h3>
            <p class="step-description">Select which aspects of storytelling you want enhanced.</p>
            
            <div class="row">
              <div class="col-md-4 mb-3">
                <div class="card personality-card" data-personality="narrative">
                  <div class="card-body text-center">
                    <div class="personality-icon">🎭</div>
                    <h5 class="card-title">Narrative Flair</h5>
                    <p class="card-text">Rich storytelling, character development, and immersive descriptions.</p>
                    <div class="form-check">
                      <input class="form-check-input" type="checkbox" id="wizard-narrative" checked>
                      <label class="form-check-label" for="wizard-narrative">Enable</label>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="col-md-4 mb-3">
                <div class="card personality-card" data-personality="mechanics">
                  <div class="card-body text-center">
                    <div class="personality-icon">⚙️</div>
                    <h5 class="card-title">Mechanical Precision</h5>
                    <p class="card-text">Rules accuracy, combat mechanics, and game system expertise.</p>
                    <div class="form-check">
                      <input class="form-check-input" type="checkbox" id="wizard-mechanics" checked>
                      <label class="form-check-label" for="wizard-mechanics">Enable</label>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="col-md-4 mb-3">
                <div class="card personality-card" data-personality="companions">
                  <div class="card-body text-center">
                    <div class="personality-icon">👥</div>
                    <h5 class="card-title">Starting Companions</h5>
                    <p class="card-text">Automatically create complementary party members to join your adventure.</p>
                    <div class="form-check">
                      <input class="form-check-input" type="checkbox" id="wizard-companions" checked>
                      <label class="form-check-label" for="wizard-companions">Generate companions</label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3: Custom Options -->
          <div class="wizard-step" data-step="3">
            <h3 class="step-title">🎮 Campaign Options</h3>
            <p class="step-description">Customize your adventure with these optional features.</p>
            
            <div class="row">
              <div class="col-md-6 mb-4">
                <div class="card option-card" data-option="defaultWorld">
                  <div class="card-body">
                    <div class="d-flex align-items-start">
                      <div class="option-icon me-3">🌍</div>
                      <div class="flex-grow-1">
                        <h5 class="card-title">Default Fantasy World</h5>
                        <p class="card-text">Use the Celestial Wars/Assiah setting with rich lore and characters.</p>
                        <div class="form-check">
                          <input class="form-check-input" type="checkbox" id="wizard-default-world" checked>
                          <label class="form-check-label" for="wizard-default-world">Use default world</label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
            </div>
          </div>

          <!-- Step 4: Launch -->
          <div class="wizard-step" data-step="4">
            <h3 class="step-title">🚀 Ready to Launch!</h3>
            <p class="step-description">Review your settings and start your adventure.</p>
            
            <div class="campaign-preview card">
              <div class="card-body">
                <h5 class="card-title">Campaign Summary</h5>
                <div class="preview-content">
                  <div class="preview-item">
                    <strong>Title:</strong> <span id="preview-title">My Epic Adventure</span>
                  </div>
                  <div class="preview-item">
                    <strong>Description:</strong> <span id="preview-description">A brave knight...</span>
                  </div>
                  <div class="preview-item">
                    <strong>AI Personalities:</strong> <span id="preview-personalities">Narrative, Mechanical, Calibration</span>
                  </div>
                  <div class="preview-item">
                    <strong>Options:</strong> <span id="preview-options">Companions, Default World</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="launch-actions mt-4 text-center">
              <button type="button" class="btn btn-success btn-lg" id="launch-campaign">
                <i class="fas fa-rocket me-2"></i>Begin Adventure!
              </button>
            </div>
          </div>
        </div>

        <!-- Navigation -->
        <div class="wizard-navigation mt-4 d-flex justify-content-between">
          <button type="button" class="btn btn-outline-secondary" id="wizard-prev" disabled>
            <i class="fas fa-chevron-left me-2"></i>Previous
          </button>
          
          <div class="step-counter">
            Step <span id="current-step-num">1</span> of <span id="total-steps-num">4</span>
          </div>
          
          <button type="button" class="btn btn-primary" id="wizard-next">
            Next<i class="fas fa-chevron-right ms-2"></i>
          </button>
        </div>
      </div>
    `;
  }

  setupStepNavigation() {
    const prevBtn = document.getElementById('wizard-prev');
    const nextBtn = document.getElementById('wizard-next');
    const launchBtn = document.getElementById('launch-campaign');

    prevBtn?.addEventListener('click', () => this.previousStep());
    nextBtn?.addEventListener('click', () => this.nextStep());
    launchBtn?.addEventListener('click', () => this.launchCampaign());

    // Step indicator clicks
    document.querySelectorAll('.step-indicator').forEach(indicator => {
      indicator.addEventListener('click', (e) => {
        const step = parseInt(e.currentTarget.dataset.step);
        if (step <= this.currentStep) {
          this.goToStep(step);
        }
      });
    });
    
    // Setup campaign type handlers after navigation is ready
    setTimeout(() => {
      this.loadInitialCampaignContent();
    }, 100);
  }

  setupEventListeners() {
    // Real-time preview updates
    document.addEventListener('input', (e) => {
      if (e.target.matches('#wizard-campaign-title')) {
        this.updatePreview('title', e.target.value);
      } else if (e.target.matches('#wizard-campaign-prompt')) {
        this.updatePreview('description', e.target.value);
      }
    });

    document.addEventListener('change', (e) => {
      if (e.target.matches('.wizard-step input[type="checkbox"]')) {
        this.updatePreview();
      } else if (e.target.matches('input[name="wizardCampaignType"]')) {
        this.handleCampaignTypeChange(e.target.value);
      }
    });

    // Campaign type card selection
    document.addEventListener('click', (e) => {
      const typeCard = e.target.closest('.campaign-type-card');
      if (typeCard && !e.target.matches('input')) {
        const radio = typeCard.querySelector('input[type="radio"]');
        if (radio) {
          radio.checked = true;
          radio.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
    });

    // Personality card selection
    document.querySelectorAll('.personality-card').forEach(card => {
      card.addEventListener('click', (e) => {
        if (!e.target.matches('input')) {
          const checkbox = card.querySelector('input[type="checkbox"]');
          checkbox.checked = !checkbox.checked;
          this.updatePreview();
        }
      });
    });

    // Load Dragon Knight content on wizard init if selected
    this.loadInitialCampaignContent();
  }

  async loadInitialCampaignContent() {
    const dragonKnightRadio = document.getElementById('wizard-dragonKnightCampaign');
    if (dragonKnightRadio && dragonKnightRadio.checked) {
      await this.handleCampaignTypeChange('dragon-knight');
    }
  }

  async handleCampaignTypeChange(type) {
    const promptTextarea = document.getElementById('wizard-campaign-prompt');
    const promptLabel = document.getElementById('wizard-prompt-label');
    const promptHelp = document.getElementById('wizard-prompt-help');
    
    // Update visual selection
    document.querySelectorAll('.campaign-type-card').forEach(card => {
      card.classList.toggle('selected', card.dataset.type === type);
    });
    
    if (type === 'dragon-knight') {
      promptTextarea.readOnly = true;
      promptTextarea.value = 'A brave knight in a land of dragons needs to choose between killing an evil dragon or joining its side.';
      promptLabel.textContent = 'Campaign Description';
      promptHelp.textContent = 'This campaign uses the pre-written Dragon Knight story. Switch to Custom Campaign to write your own.';
    } else {
      promptTextarea.readOnly = false;
      promptTextarea.value = '';
      promptLabel.textContent = 'Describe Your World';
      promptHelp.textContent = 'For inspiration, pick your favorite movie, book, or TV show. Describe a scenario where you get to make important decisions.';
      promptTextarea.focus();
    }
    
    this.updatePreview();
  }

  populateFromOriginalForm() {
    const originalForm = document.getElementById('new-campaign-form');
    if (!originalForm) return;

    // Get values from original form
    const titleInput = originalForm.querySelector('#campaign-title');
    const promptInput = originalForm.querySelector('#campaign-prompt');
    const companionsInput = originalForm.querySelector('#generate-companions');

    if (titleInput?.value) {
      document.getElementById('wizard-campaign-title').value = titleInput.value;
    }
    if (promptInput?.value) {
      document.getElementById('wizard-campaign-prompt').value = promptInput.value;
    }
    if (companionsInput) {
      const wizardCompanions = document.getElementById('wizard-companions');
      if (wizardCompanions) {
        wizardCompanions.checked = companionsInput.checked;
      }
    }

    this.updatePreview();
  }

  nextStep() {
    if (!this.validateCurrentStep()) {
      return;
    }

    if (this.currentStep < this.totalSteps) {
      this.goToStep(this.currentStep + 1);
    }
  }

  previousStep() {
    if (this.currentStep > 1) {
      this.goToStep(this.currentStep - 1);
    }
  }

  goToStep(stepNumber) {
    if (stepNumber < 1 || stepNumber > this.totalSteps) {
      return;
    }

    // Hide current step
    document.querySelector('.wizard-step.active')?.classList.remove('active');
    document.querySelector('.step-indicator.active')?.classList.remove('active');

    // Show target step
    document.querySelector(`[data-step="${stepNumber}"].wizard-step`)?.classList.add('active');
    document.querySelector(`[data-step="${stepNumber}"].step-indicator`)?.classList.add('active');

    this.currentStep = stepNumber;
    this.updateUI();
    this.updatePreview();
  }

  updateUI() {
    // Update progress bar
    const progressBar = document.getElementById('wizard-progress-bar');
    const progress = (this.currentStep / this.totalSteps) * 100;
    progressBar.style.width = `${progress}%`;

    // Update navigation buttons
    const prevBtn = document.getElementById('wizard-prev');
    const nextBtn = document.getElementById('wizard-next');

    prevBtn.disabled = this.currentStep === 1;
    
    if (this.currentStep === this.totalSteps) {
      nextBtn.style.display = 'none';
    } else {
      nextBtn.style.display = 'block';
    }

    // Update step counter
    document.getElementById('current-step-num').textContent = this.currentStep;
    document.getElementById('total-steps-num').textContent = this.totalSteps;

    // Mark completed steps
    for (let i = 1; i < this.currentStep; i++) {
      const indicator = document.querySelector(`[data-step="${i}"].step-indicator`);
      indicator?.classList.add('completed');
    }
  }

  validateCurrentStep() {
    const currentStepElement = document.querySelector('.wizard-step.active');
    const requiredInputs = currentStepElement?.querySelectorAll('input[required], textarea[required]');
    
    let isValid = true;
    requiredInputs?.forEach(input => {
      if (!input.value.trim()) {
        input.classList.add('is-invalid');
        isValid = false;
      } else {
        input.classList.remove('is-invalid');
      }
    });

    return isValid;
  }

  updatePreview(field, value) {
    if (field === 'title') {
      document.getElementById('preview-title').textContent = value || 'My Epic Adventure';
    } else if (field === 'description') {
      const truncated = value ? (value.substring(0, 50) + '...') : 'A brave knight...';
      document.getElementById('preview-description').textContent = truncated;
    } else {
      // Update all fields
      const title = document.getElementById('wizard-campaign-title')?.value || 'My Epic Adventure';
      let description = document.getElementById('wizard-campaign-prompt')?.value || 'A brave knight...';
      
      // Check if default world is selected and show preview
      const useDefaultWorld = document.getElementById('wizard-default-world')?.checked;
      if (useDefaultWorld && (description === 'A brave knight...' || description.trim() === '')) {
        description = 'Ser Arion Dragon Knight Campaign (Default World Selected)';
      }
      
      document.getElementById('preview-title').textContent = title;
      document.getElementById('preview-description').textContent = 
        description.length > 50 ? description.substring(0, 50) + '...' : description;

      // Update personalities
      const personalities = [];
      if (document.getElementById('wizard-narrative')?.checked) personalities.push('Narrative');
      if (document.getElementById('wizard-mechanics')?.checked) personalities.push('Mechanics');
      document.getElementById('preview-personalities').textContent = personalities.join(', ') || 'None selected';

      // Update options
      const options = [];
      if (document.getElementById('wizard-companions')?.checked) options.push('Companions');
      if (document.getElementById('wizard-default-world')?.checked) options.push('Dragon Knight World');
      document.getElementById('preview-options').textContent = options.join(', ') || 'None selected';
    }
  }

  collectFormData() {
    const isDragonKnight = document.getElementById('wizard-dragonKnightCampaign')?.checked;
    return {
      title: document.getElementById('wizard-campaign-title')?.value || '',
      prompt: document.getElementById('wizard-campaign-prompt')?.value || '',
      selectedPrompts: [
        ...(document.getElementById('wizard-narrative')?.checked ? ['narrative'] : []),
        ...(document.getElementById('wizard-mechanics')?.checked ? ['mechanics'] : []),
      ],
      customOptions: [
        ...(document.getElementById('wizard-companions')?.checked ? ['companions'] : []),
        ...(isDragonKnight ? ['defaultWorld'] : []),
      ],
      campaignType: isDragonKnight ? 'dragon-knight' : 'custom'
    };
  }

  launchCampaign() {
    const formData = this.collectFormData();
    
    // Populate original form with wizard data first
    this.populateOriginalForm(formData);
    
    // Show detailed spinner
    this.showDetailedSpinner();
    
    // Submit the form IMMEDIATELY - let backend do the work
    const originalForm = document.getElementById('new-campaign-form');
    if (originalForm) {
      originalForm.dispatchEvent(new Event('submit'));
    }
  }

  showDetailedSpinner() {
    // Hide wizard content but preserve structure
    const wizardContent = document.querySelector('.wizard-content');
    const wizardNav = document.querySelector('.wizard-navigation');
    
    if (wizardContent) wizardContent.style.display = 'none';
    if (wizardNav) wizardNav.style.display = 'none';
    
    // Remove any existing spinner first
    const existingSpinner = document.getElementById('campaign-creation-spinner');
    if (existingSpinner) {
      existingSpinner.remove();
    }
    
    // Create detailed spinner with progress (visual feedback only, no delays)
    const spinnerHTML = `
      <div id="campaign-creation-spinner" class="text-center py-5">
        <div class="spinner-container">
          <div class="spinner-border text-primary mb-4" role="status" style="width: 4rem; height: 4rem;">
            <span class="visually-hidden">Loading...</span>
          </div>
          
          <h4 class="text-primary mb-3">🏗️ Building Your Adventure...</h4>
          
          <!-- Progress Bar -->
          <div class="progress mb-4" style="height: 20px; max-width: 400px; margin: 0 auto;">
            <div id="creation-progress-bar" class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
            </div>
          </div>
          
          <!-- Current Task -->
          <div class="mb-3">
            <h5 id="current-task" class="text-secondary mb-2">🚀 Initializing...</h5>
            <p id="task-description" class="text-muted small">Preparing your adventure</p>
          </div>
          
          <!-- Step Indicators -->
          <div class="d-flex justify-content-center gap-3 mb-3">
            <div class="text-center">
              <div id="step-characters" class="step-icon mb-1">⏳</div>
              <small class="step-label d-none d-md-block">Characters</small>
            </div>
            <div class="text-center">
              <div id="step-factions" class="step-icon mb-1">⏳</div>
              <small class="step-label d-none d-md-block">Factions</small>
            </div>
            <div class="text-center">
              <div id="step-world" class="step-icon mb-1">⏳</div>
              <small class="step-label d-none d-md-block">World</small>
            </div>
            <div class="text-center">
              <div id="step-story" class="step-icon mb-1">⏳</div>
              <small class="step-label d-none d-md-block">Story</small>
            </div>
          </div>
        </div>
      </div>
    `;
    
    const container = document.getElementById('campaign-wizard');
    if (container) {
      // CRITICAL FIX: Append spinner instead of replacing entire content
      container.insertAdjacentHTML('beforeend', spinnerHTML);
      // Start progress animation (visual feedback, stops at 90%)
      this.animateCreationProgress();
    }
  }

  animateCreationProgress() {
    const progressBar = document.getElementById('creation-progress-bar');
    const currentTask = document.getElementById('current-task');
    const taskDescription = document.getElementById('task-description');
    
    if (!progressBar || !currentTask || !taskDescription) return;
    
    const steps = [
      {
        progress: 20,
        task: '🧙‍♂️ Building characters...',
        description: 'Creating NPCs, allies, and potential party members',
        icon: 'step-characters',
        duration: 20000
      },
      {
        progress: 40,
        task: '⚔️ Establishing factions...',
        description: 'Designing competing groups, guilds, and political powers',
        icon: 'step-characters',
        duration: 25000
      },
      {
        progress: 60,
        task: '🌍 Defining world rules...',
        description: 'Setting magic systems, geography, and cultural norms',
        icon: 'step-factions',
        duration: 25000
      },
      {
        progress: 90,
        task: '📖 Crafting story hook...',
        description: 'Weaving together an engaging opening scenario',
        icon: 'step-world',
        duration: 20000
      }
    ];
    
    let currentStep = 0;
    
    const updateProgress = () => {
      if (currentStep >= steps.length) {
        // Stay at 90% and wait for real completion
        return;
      }
      
      const step = steps[currentStep];
      
      // Update progress bar
      progressBar.style.width = `${step.progress}%`;
      
      // Update text
      currentTask.textContent = step.task;
      taskDescription.textContent = step.description;
      
      // Update step icons
      if (currentStep > 0) {
        const prevIcon = document.getElementById(steps[currentStep - 1].icon);
        if (prevIcon) prevIcon.textContent = '✅';
      }
      
      const currentIcon = document.getElementById(step.icon);
      if (currentIcon) currentIcon.textContent = '🔄';
      
      currentStep++;
      
      if (currentStep < steps.length) {
        setTimeout(updateProgress, step.duration);
      }
      // When we reach the end, stay at 90% - let real completion handle the final 100%
    };
    
    // Start progress
    setTimeout(updateProgress, 500);
  }

  completeProgress() {
    const progressBar = document.getElementById('creation-progress-bar');
    const currentTask = document.getElementById('current-task');
    const taskDescription = document.getElementById('task-description');
    
    if (!progressBar || !currentTask || !taskDescription) return;
    
    // Jump to 100% when backend actually completes
    progressBar.style.width = '100%';
    currentTask.textContent = '✨ Finalizing adventure...';
    taskDescription.textContent = 'Your world is ready! Launching campaign...';
    
    // Mark final step as complete
    const finalIcon = document.getElementById('step-story');
    if (finalIcon) finalIcon.textContent = '✅';
  }



  resetWizard() {
    // Remove any existing spinner
    const existingSpinner = document.getElementById('campaign-creation-spinner');
    if (existingSpinner) {
      existingSpinner.remove();
    }
    
    // Show wizard content and navigation
    const wizardContent = document.querySelector('.wizard-content');
    const wizardNav = document.querySelector('.wizard-navigation');
    
    if (wizardContent) wizardContent.style.display = 'block';
    if (wizardNav) wizardNav.style.display = 'flex';
    
    // Reset to step 1
    this.currentStep = 1;
    
    // Clear form fields
    const titleInput = document.getElementById('wizard-campaign-title');
    const promptInput = document.getElementById('wizard-campaign-prompt');
    
    if (titleInput) titleInput.value = '';
    if (promptInput) promptInput.value = '';
    
    // Reset all checkboxes to default (checked)
    const checkboxes = [
      'wizard-narrative',
      'wizard-mechanics', 
      'wizard-companions',
      'wizard-default-world'
    ];
    
    checkboxes.forEach(id => {
      const checkbox = document.getElementById(id);
      if (checkbox) checkbox.checked = true;
    });
    
    // Reset step indicators
    document.querySelectorAll('.step-indicator').forEach(indicator => {
      indicator.classList.remove('active', 'completed');
    });
    
    document.querySelectorAll('.wizard-step').forEach(step => {
      step.classList.remove('active');
    });
    
    // Activate step 1
    document.querySelector('[data-step="1"].step-indicator')?.classList.add('active');
    document.querySelector('[data-step="1"].wizard-step')?.classList.add('active');
    
    // Update UI
    this.updateUI();
    this.updatePreview();
  }

  populateOriginalForm(data) {
    const originalForm = document.getElementById('new-campaign-form');
    if (!originalForm) return;

    // Set basic fields
    const titleInput = originalForm.querySelector('#campaign-title');
    const promptInput = originalForm.querySelector('#campaign-prompt');
    
    if (titleInput) titleInput.value = data.title;
    if (promptInput) promptInput.value = data.prompt;

    // Set checkboxes
    originalForm.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
      checkbox.checked = false;
    });

    data.selectedPrompts.forEach(prompt => {
      const checkbox = originalForm.querySelector(`input[value="${prompt}"]`);
      if (checkbox) checkbox.checked = true;
    });

    data.customOptions.forEach(option => {
      const checkbox = originalForm.querySelector(`input[value="${option}"]`);
      if (checkbox) checkbox.checked = true;
    });
  }
}

// Initialize campaign wizard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.campaignWizard = new CampaignWizard();
}); 