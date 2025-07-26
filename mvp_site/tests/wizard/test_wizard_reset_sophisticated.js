#!/usr/bin/env node

/**
 * Sophisticated Red/Green Test for Campaign Wizard Reset
 * Uses jsdom to simulate browser environment and test actual user workflow
 */

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

class SophisticatedWizardTest {
  constructor() {
    this.testResults = [];
    this.dom = null;
    this.window = null;
    this.document = null;
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

  // Load and setup browser environment
  async setupBrowserEnvironment() {
    this.log('🌐 Setting up browser environment with jsdom');

    try {
      // Create JSDOM instance with realistic browser environment
      this.dom = new JSDOM(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>WorldArchitect.AI</title>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
          <!-- Mock application structure -->
          <div id="app">
            <div id="new-campaign-view" class="view">
              <form id="new-campaign-form" style="display: block;">
                <input type="text" id="campaign-title" value="">
                <textarea id="campaign-prompt"></textarea>
                <input type="checkbox" id="prompt-narrative">
                <input type="checkbox" id="prompt-mechanics">
                <input type="checkbox" id="prompt-calibration">
                <button type="submit">Create Campaign</button>
              </form>
            </div>
          </div>
        </body>
        </html>
      `, {
        url: 'http://localhost:5000',
        pretendToBeVisual: true,
        resources: 'usable'
      });

      this.window = this.dom.window;
      this.document = this.window.document;

      // Add global objects that the wizard expects
      this.window.console = console;
      this.window.setTimeout = setTimeout;
      this.window.setInterval = setInterval;

      this.log('✅ Browser environment setup complete');
      return true;
    } catch (error) {
      this.log(`❌ Failed to setup browser environment: ${error.message}`, 'error');
      return false;
    }
  }

  // Load JavaScript files
  async loadJavaScriptFiles() {
    this.log('📁 Loading JavaScript files');

    try {
      // Load campaign wizard JavaScript
      const wizardPath = path.join(__dirname, 'static', 'js', 'campaign-wizard.js');
      const wizardJs = fs.readFileSync(wizardPath, 'utf8');

      // Execute in jsdom context
      const script = this.document.createElement('script');
      script.textContent = wizardJs;
      this.document.head.appendChild(script);

      // Load app.js for form reset logic
      const appPath = path.join(__dirname, 'static', 'app.js');
      const appJs = fs.readFileSync(appPath, 'utf8');

      const appScript = this.document.createElement('script');
      appScript.textContent = appJs;
      this.document.head.appendChild(appScript);

      this.log('✅ JavaScript files loaded');
      return true;
    } catch (error) {
      this.log(`❌ Failed to load JavaScript: ${error.message}`, 'error');
      return false;
    }
  }

  // Initialize wizard
  initializeWizard() {
    this.log('🧙‍♂️ Initializing campaign wizard');

    try {
      // Create wizard instance
      if (this.window.CampaignWizard) {
        this.window.campaignWizard = new this.window.CampaignWizard();

        // Force enable for testing
        this.window.campaignWizard.isEnabled = true;

        this.log('✅ Campaign wizard initialized');
        return true;
      } else {
        this.log('❌ CampaignWizard class not found', 'error');
        return false;
      }
    } catch (error) {
      this.log(`❌ Failed to initialize wizard: ${error.message}`, 'error');
      return false;
    }
  }

  // Simulate first campaign creation and completion
  async simulateFirstCampaignFlow() {
    this.log('🎬 Simulating first campaign creation flow');

    try {
      // 1. Enable wizard (user clicks "Start Campaign")
      this.window.campaignWizard.enable();
      await this.wait(100);

      // 2. Simulate wizard usage
      this.fillWizardForm();
      await this.wait(100);

      // 3. Simulate campaign submission (calls showDetailedSpinner)
      this.window.campaignWizard.launchCampaign();
      await this.wait(100);

      // 4. Simulate campaign completion (navigation away)
      this.simulateCampaignCompletion();
      await this.wait(100);

      this.log('✅ First campaign flow completed');
      return true;
    } catch (error) {
      this.log(`❌ First campaign simulation failed: ${error.message}`, 'error');
      return false;
    }
  }

  // Fill wizard form with test data
  fillWizardForm() {
    this.log('📝 Filling wizard form');

    const titleInput = this.document.getElementById('wizard-campaign-title');
    const promptInput = this.document.getElementById('wizard-campaign-prompt');

    if (titleInput) titleInput.value = 'Test Campaign';
    if (promptInput) promptInput.value = 'Test adventure';
  }

  // Simulate campaign completion and navigation
  simulateCampaignCompletion() {
    this.log('🏁 Simulating campaign completion');

    // Simulate navigation to new campaign page (this triggers the bug)
    if (this.window.location) {
      this.window.location.pathname = '/new-campaign';
    }

    // Simulate the form reset that happens on route change
    if (this.window.resetNewCampaignForm) {
      this.window.resetNewCampaignForm();
    }
  }

  // Test wizard reset functionality (the critical test)
  async testWizardReset() {
    this.log('🔥 Testing wizard reset (the critical test)');

    try {
      // This is the moment of truth - second "Start Campaign" click
      this.window.campaignWizard.enable();
      await this.wait(200); // Give time for all operations

      return this.validateWizardState();
    } catch (error) {
      this.log(`❌ Wizard reset test failed: ${error.message}`, 'error');
      return false;
    }
  }

  // Validate wizard state after reset
  validateWizardState() {
    this.log('🔍 Validating wizard state');

    let allPassed = true;

    // Test 1: Wizard container exists
    const wizardContainer = this.document.getElementById('campaign-wizard');
    allPassed &= this.assert(!!wizardContainer, 'Wizard container exists');

    // Test 2: Wizard has content
    const hasContent = wizardContainer && wizardContainer.innerHTML.trim().length > 0;
    allPassed &= this.assert(hasContent, 'Wizard has content');

    // Test 3: No spinner present
    const spinner = this.document.getElementById('campaign-creation-spinner');
    allPassed &= this.assert(!spinner, 'No spinner present');

    // Test 4: Wizard content is visible (check style.display)
    const wizardContent = this.document.querySelector('.wizard-content');
    const isContentVisible = wizardContent && wizardContent.style.display !== 'none';
    allPassed &= this.assert(isContentVisible, 'Wizard content is visible');

    // Test 5: Wizard navigation is visible
    const wizardNav = this.document.querySelector('.wizard-navigation');
    const isNavVisible = wizardNav && wizardNav.style.display !== 'none';
    allPassed &= this.assert(isNavVisible, 'Wizard navigation is visible');

    // Test 6: Original form is hidden
    const originalForm = this.document.getElementById('new-campaign-form');
    const isFormHidden = originalForm && originalForm.style.display === 'none';
    allPassed &= this.assert(isFormHidden, 'Original form is hidden');

    return allPassed;
  }

  // Helper: wait function
  wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Run complete test suite
  async runCompleteTest() {
    this.log('🚀 Starting sophisticated wizard reset test');

    try {
      // Setup
      const setupOk = await this.setupBrowserEnvironment();
      if (!setupOk) return false;

      const jsLoaded = await this.loadJavaScriptFiles();
      if (!jsLoaded) return false;

      const wizardInit = this.initializeWizard();
      if (!wizardInit) return false;

      // Run simulation
      const firstFlowOk = await this.simulateFirstCampaignFlow();
      if (!firstFlowOk) return false;

      // The critical test
      const resetTestPassed = await this.testWizardReset();

      // Results
      this.log(`🏁 Test completed. Result: ${resetTestPassed ? 'GREEN ✅' : 'RED ❌'}`);
      return resetTestPassed;

    } catch (error) {
      this.log(`💥 Test suite error: ${error.message}`, 'error');
      return false;
    }
  }

  // Get summary
  getSummary() {
    const passed = this.testResults.filter(r => r.type === 'pass').length;
    const failed = this.testResults.filter(r => r.type === 'fail').length;
    const total = passed + failed;

    return {
      total,
      passed,
      failed,
      successRate: total > 0 ? (passed / total * 100).toFixed(1) : 0,
      results: this.testResults
    };
  }
}

// Main execution
async function main() {
  console.log('🧪 Sophisticated Wizard Reset Test Starting...\n');

  const test = new SophisticatedWizardTest();
  const result = await test.runCompleteTest();

  console.log('\n📊 TEST SUMMARY');
  console.log('================');

  const summary = test.getSummary();
  console.log(`Total Tests: ${summary.total}`);
  console.log(`Passed: ${summary.passed}`);
  console.log(`Failed: ${summary.failed}`);
  console.log(`Success Rate: ${summary.successRate}%`);

  console.log(`\nOverall Result: ${result ? '🟢 GREEN (PASS)' : '🔴 RED (FAIL)'}`);

  if (!result) {
    console.log('\n🔍 This test should FAIL (Red State) until the wizard reset bug is fixed.');
    console.log('Once fixed, this test should PASS (Green State).');
  }

  process.exit(result ? 0 : 1);
}

// Check if jsdom is available
try {
  require('jsdom');
  main();
} catch (error) {
  console.log('❌ jsdom not available. Install with: npm install jsdom');
  console.log('Falling back to basic test...');

  // Basic fallback test
  console.log('🔴 RED STATE: Cannot run sophisticated test without jsdom');
  process.exit(1);
}
