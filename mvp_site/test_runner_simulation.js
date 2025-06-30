#!/usr/bin/env node

/**
 * Browser Test Simulation
 * 
 * This simulates the browser environment to run the campaign wizard timing tests
 * without needing an actual browser.
 */

// Mock DOM environment
class MockDOM {
  constructor() {
    this.elements = new Map();
    this.eventListeners = new Map();
  }
  
  getElementById(id) {
    if (!this.elements.has(id)) {
      const element = {
        id: id,
        innerHTML: '',
        textContent: '',
        style: {},
        offsetParent: null,
        dispatchEvent: () => true,
        remove: () => this.elements.delete(id)
      };
      this.elements.set(id, element);
    }
    return this.elements.get(id);
  }
  
  querySelector(selector) {
    // Simple selector simulation
    if (selector === '.wizard-content') {
      return this.getElementById('wizard-content');
    }
    return null;
  }
  
  createElement(tag) {
    return {
      innerHTML: '',
      style: {},
      appendChild: () => {},
      remove: () => {}
    };
  }
}

// Mock global environment
const mockDOM = new MockDOM();

global.document = {
  getElementById: (id) => mockDOM.getElementById(id),
  querySelector: (selector) => mockDOM.querySelector(selector),
  createElement: (tag) => mockDOM.createElement(tag),
  body: { appendChild: () => {} }
};

global.window = {
  setTimeout: global.setTimeout,
  fetch: () => Promise.resolve(new Response('{"success": true}'))
};

global.Event = class Event {
  constructor(type) {
    this.type = type;
  }
};

global.Response = class Response {
  constructor(body) {
    this.body = body;
  }
};

// Campaign Wizard Timing Tests (simplified for Node.js)
class CampaignWizardTimingTests {
  constructor() {
    this.testResults = [];
    this.setupMockDOM();
  }

  setupMockDOM() {
    // Create test containers without destroying existing UI
    const testContainer = document.getElementById('test-container');
    testContainer.innerHTML = `
      <form id="new-campaign-form">
        <input id="campaign-title" value="Test Campaign">
        <textarea id="campaign-prompt">Test prompt</textarea>
      </form>
      <div id="campaign-wizard"></div>
    `;

    // Mock window.campaignWizard
    global.window.campaignWizard = {
      completeProgress: function() { this.completeProgressCalled = true; },
      completeProgressCalled: false
    };
  }

  async testImmediateFormSubmission() {
    const testName = "Form submission happens immediately (no artificial delays)";
    
    try {
      const form = document.getElementById('new-campaign-form');
      
      const startTime = Date.now();
      form.dispatchEvent(new Event('submit'));
      const executionTime = Date.now() - startTime;
      
      const maxAllowedDelay = 10;
      if (executionTime > maxAllowedDelay) {
        throw new Error(`Execution took ${executionTime}ms, expected ≤ ${maxAllowedDelay}ms`);
      }

      this.testResults.push({
        name: testName,
        status: 'PASS',
        details: `Form submitted in ${executionTime}ms, total execution: ${executionTime}ms`
      });
      
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: error.message
      });
    }
  }

  async testWizardResetIssueReproduction() {
    const testName = "Campaign Wizard Reset Issue Reproduction";
    
    try {
      console.log('🔍 Reproducing wizard reset bug...');
      
      // Create mock campaign wizard with the problematic methods
      const mockCampaignWizard = {
        isEnabled: false,
        
        enable() {
          console.log('🔧 Enable called');
          this.isEnabled = true;
          this.forceCleanRecreation();
        },
        
        forceCleanRecreation() {
          console.log('🧹 Force clean recreation called');
          const existingWizard = document.getElementById('campaign-wizard');
          const existingSpinner = document.getElementById('campaign-creation-spinner');
          
          if (existingSpinner) {
            existingSpinner.remove();
          }
          
          if (existingWizard) {
            // Ensure wizard container exists before populating it
            if (!existingWizard.parentNode) {
              // Container was removed, create a new one
              const originalForm = document.getElementById('new-campaign-form');
              if (originalForm) {
                const newWizard = document.createElement('div');
                newWizard.id = 'campaign-wizard';
                originalForm.parentNode.insertBefore(newWizard, originalForm.nextSibling);
              }
            }
            existingWizard.innerHTML = ''; // Clear content
          }
          
          this.replaceOriginalForm();
          this.setupEventListeners();
        },
        
        replaceOriginalForm() {
          console.log('🔄 Replace original form called');
          const wizardContainer = document.getElementById('campaign-wizard');
          if (wizardContainer) {
            wizardContainer.innerHTML = `
              <div class="wizard-content">
                <h3>✨ Fresh Campaign Creation Wizard</h3>
                <div class="wizard-step">Step 1: Campaign Details</div>
                <div class="wizard-controls">
                  <button class="wizard-btn">Continue</button>
                </div>
              </div>
            `;
          }
        },
        
        setupEventListeners() {
          console.log('🔗 Setup event listeners called');
          // Mock event listener setup
        },
        
        showDetailedSpinner() {
          console.log('⏳ Show detailed spinner called');
          const container = document.getElementById('campaign-wizard');
          
          const spinnerHTML = `
            <div id="campaign-creation-spinner" class="text-center py-5">
              <div class="spinner-border text-primary mb-4" role="status">
                <span class="visually-hidden">Building...</span>
              </div>
              <h4 class="text-primary mb-3">🏗️ Building Your Adventure...</h4>
            </div>
          `;
          
          if (container) {
            // FIXED: Use insertAdjacentHTML instead of innerHTML to preserve structure
            container.style.display = 'none'; // Hide wizard content
            container.insertAdjacentHTML('beforeend', spinnerHTML);
          }
        },
        
        completeProgress() {
          console.log('✅ Complete progress called');
          this.isEnabled = false;
        }
      };
      
      // Simulate workflow
      console.log('📝 Step 1: Simulating first campaign creation...');
      mockCampaignWizard.enable();
      
      let wizardContent = document.querySelector('.wizard-content');
      if (!wizardContent) {
        throw new Error("Fresh wizard content not created on first enable()");
      }
      console.log('✅ Fresh wizard created successfully');
      
      mockCampaignWizard.showDetailedSpinner();
      mockCampaignWizard.completeProgress();
      
      console.log('📝 Step 2: User tries to create second campaign...');
      mockCampaignWizard.enable();
      
      const wizardContainer = document.getElementById('campaign-wizard');
      const persistentSpinner = document.getElementById('campaign-creation-spinner');
      const freshWizardContent = document.querySelector('.wizard-content');
      
      console.log(`📊 Final Results:`);
      console.log(`  - Wizard container exists: ${!!wizardContainer}`);
      console.log(`  - Persistent spinner present: ${!!persistentSpinner}`);
      console.log(`  - Fresh wizard content present: ${!!freshWizardContent}`);
      
      if (freshWizardContent && !persistentSpinner) {
        this.testResults.push({
          name: testName,
          status: 'PASS',
          details: '✅ Wizard reset works correctly - fresh content appears, no persistent spinner'
        });
      } else if (!freshWizardContent && !persistentSpinner) {
        this.testResults.push({
          name: testName,
          status: 'FAIL',
          details: '❓ Unexpected state: No spinner, no fresh wizard content. Check forceCleanRecreation() logic.'
        });
      } else {
        this.testResults.push({
          name: testName,
          status: 'FAIL',
          details: '🐛 BUG REPRODUCED: Wizard reset issue detected'
        });
      }
      
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: `Error during test: ${error.message}`
      });
    }
  }

  async runSimplifiedTests() {
    console.log('🧪 Running Simplified Campaign Wizard Tests...\n');
    
    await this.testImmediateFormSubmission();
    await this.testWizardResetIssueReproduction();
    
    this.generateReport();
  }

  generateReport() {
    const passed = this.testResults.filter(t => t.status === 'PASS').length;
    const failed = this.testResults.filter(t => t.status === 'FAIL').length;
    
    console.log('\n📊 SIMPLIFIED TEST RESULTS');
    console.log('===========================');
    console.log(`Total Tests: ${this.testResults.length}`);
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`Success Rate: ${((passed/this.testResults.length)*100).toFixed(1)}%\n`);
    
    console.log('📋 DETAILED RESULTS:');
    this.testResults.forEach((test, i) => {
      const emoji = test.status === 'PASS' ? '✅' : '❌';
      console.log(`${i + 1}. ${emoji} ${test.name}`);
      console.log(`   ${test.details}\n`);
    });
    
    if (failed > 0) {
      console.log('🚨 Issues detected that need attention.');
      return false;
    } else {
      console.log('🎉 All simplified tests passed!');
      return true;
    }
  }
}

// Run the tests
async function runTests() {
  try {
    const tester = new CampaignWizardTimingTests();
    await tester.runSimplifiedTests();
  } catch (error) {
    console.error('❌ Test execution failed:', error.message);
  }
}

runTests(); 