/**
 * Red/Green Test for Campaign Wizard Reset Issue
 * Tests the exact user workflow: Create campaign → Complete → Navigate back → Click "Start Campaign"
 */

class WizardResetTest {
  constructor() {
    this.testResults = [];
    this.testName = "Campaign Wizard Reset Functionality";
  }

  log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${type.toUpperCase()}: ${message}`;
    console.log(logEntry);
    this.testResults.push({ message, type, timestamp });
  }

  assert(condition, message) {
    if (condition) {
      this.log(`✅ PASS: ${message}`, 'pass');
      return true;
    } else {
      this.log(`❌ FAIL: ${message}`, 'fail');
      return false;
    }
  }

  // Simulate the state after campaign creation completes
  simulateCampaignCompletionState() {
    this.log('🎬 Simulating campaign completion state');
    
    // Ensure we have the basic DOM structure
    let originalForm = document.getElementById('new-campaign-form');
    if (!originalForm) {
      this.log('⚠️ No original form found, creating mock form');
      originalForm = document.createElement('form');
      originalForm.id = 'new-campaign-form';
      document.body.appendChild(originalForm);
    }

    // Remove any existing wizard or spinner (clean slate)
    const existingWizard = document.getElementById('campaign-wizard');
    const existingSpinner = document.getElementById('campaign-creation-spinner');
    
    if (existingWizard) {
      existingWizard.remove();
      this.log('🗑️ Removed existing wizard');
    }
    
    if (existingSpinner) {
      existingSpinner.remove();
      this.log('🗑️ Removed existing spinner');
    }

    // Simulate form reset (this is what app.js:56 does)
    this.simulateFormReset();
  }

  // Simulate the form reset behavior from app.js:56
  simulateFormReset() {
    this.log('🔄 Simulating form reset behavior');
    
    const form = document.getElementById('new-campaign-form');
    if (form) {
      form.reset();
      form.style.display = 'block';
      form.classList.remove('wizard-replaced');
      this.log('📝 Form reset to defaults');
    }
  }

  // Test the wizard reset functionality
  async testWizardReset() {
    this.log('🚀 Starting wizard reset test');
    
    // Step 1: Simulate campaign completion state
    this.simulateCampaignCompletionState();
    
    // Step 2: Trigger wizard enable (this happens when user clicks "Start Campaign" again)
    if (window.campaignWizard) {
      this.log('🧙‍♂️ Triggering wizard.enable()');
      window.campaignWizard.enable();
      
      // Give it a moment to process
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Step 3: Check if wizard was created properly
      return this.validateWizardState();
    } else {
      this.log('❌ No campaignWizard found on window object');
      return false;
    }
  }

  // Validate the wizard state after reset
  validateWizardState() {
    this.log('🔍 Validating wizard state');
    
    let allPassed = true;
    
    // Test 1: Wizard container should exist
    const wizardContainer = document.getElementById('campaign-wizard');
    allPassed &= this.assert(!!wizardContainer, 'Wizard container exists');
    
    // Test 2: Wizard should have content (not empty)
    const hasContent = wizardContainer && wizardContainer.innerHTML.trim().length > 0;
    allPassed &= this.assert(hasContent, 'Wizard has content');
    
    // Test 3: No spinner should be present
    const spinner = document.getElementById('campaign-creation-spinner');
    allPassed &= this.assert(!spinner, 'No spinner present');
    
    // Test 4: Wizard should have step navigation
    const stepNav = wizardContainer && wizardContainer.querySelector('.wizard-step');
    allPassed &= this.assert(!!stepNav, 'Wizard has step navigation');
    
    // Test 5: Original form should be hidden
    const originalForm = document.getElementById('new-campaign-form');
    const formHidden = originalForm && originalForm.style.display === 'none';
    allPassed &= this.assert(formHidden, 'Original form is hidden');
    
    return allPassed;
  }

  // Run the complete test
  async runTest() {
    this.log(`🧪 Starting ${this.testName}`);
    
    try {
      const result = await this.testWizardReset();
      
      if (result) {
        this.log('🎉 All tests passed!', 'success');
      } else {
        this.log('💥 Some tests failed', 'error');
      }
      
      return result;
    } catch (error) {
      this.log(`🔥 Test error: ${error.message}`, 'error');
      return false;
    }
  }

  // Get test results summary
  getResults() {
    const passed = this.testResults.filter(r => r.type === 'pass').length;
    const failed = this.testResults.filter(r => r.type === 'fail').length;
    const total = passed + failed;
    
    return {
      total,
      passed,
      failed,
      results: this.testResults
    };
  }
}

// Make test available globally
window.WizardResetTest = WizardResetTest;