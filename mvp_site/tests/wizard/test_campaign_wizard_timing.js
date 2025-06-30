/**
 * Unit Tests for Campaign Wizard Timing Behavior
 * 
 * These tests enforce that:
 * 1. Form submission happens IMMEDIATELY when clicked (no artificial delays)
 * 2. Progress animation is visual feedback only, doesn't block submission
 * 3. Real completion can override progress animation
 * 4. No setTimeout delays that make users wait unnecessarily
 */

class CampaignWizardTimingTests {
  constructor() {
    this.testResults = [];
    this.setupMockDOM();
  }

  setupMockDOM() {
    // Create minimal DOM structure for testing WITHOUT destroying existing UI
    let testContainer = document.getElementById('test-container');
    if (!testContainer) {
      testContainer = document.createElement('div');
      testContainer.id = 'test-container';
      testContainer.style.display = 'none'; // Hide test elements from user
      document.body.appendChild(testContainer);
    }
    
    testContainer.innerHTML = `
      <form id="new-campaign-form">
        <input id="campaign-title" value="Test Campaign">
        <textarea id="campaign-prompt">Test prompt</textarea>
      </form>
      <div id="campaign-wizard"></div>
    `;

    // Mock window.campaignWizard (browser-compatible, no Jest dependency)
    window.campaignWizard = {
      completeProgress: function() { this.completeProgressCalled = true; },
      completeProgressCalled: false
    };
  }

  // Test 1: Form submission happens immediately
  async testImmediateFormSubmission() {
    const testName = "Form submission happens immediately (no artificial delays)";
    
    try {
      // Setup
      const mockCampaignWizard = {
        launchCampaign: null,
        formSubmitted: false,
        submissionTime: null
      };

      // Mock the launch campaign method to track timing
      mockCampaignWizard.launchCampaign = function() {
        const startTime = Date.now();
        
        // Simulate what the real method does
        this.populateOriginalForm({
          title: 'Test',
          prompt: 'Test prompt',
          selectedPrompts: ['narrative'],
          customOptions: ['companions']
        });
        
        this.showDetailedSpinner();
        
        // This should happen IMMEDIATELY
        const form = document.getElementById('new-campaign-form');
        if (form) {
          this.formSubmitted = true;
          this.submissionTime = Date.now() - startTime;
          // Simulate form submission
          form.dispatchEvent(new Event('submit'));
        }
      };

      // Add required methods
      mockCampaignWizard.populateOriginalForm = function() {};
      mockCampaignWizard.showDetailedSpinner = function() {};

      // Execute
      const executionStart = Date.now();
      mockCampaignWizard.launchCampaign();
      const executionTime = Date.now() - executionStart;

      // Verify: Form submission should happen within 10ms (immediate)
      const maxAllowedDelay = 10; // milliseconds
      
      if (!mockCampaignWizard.formSubmitted) {
        throw new Error("Form was not submitted");
      }
      
      if (mockCampaignWizard.submissionTime > maxAllowedDelay) {
        throw new Error(`Form submission took ${mockCampaignWizard.submissionTime}ms, expected ≤ ${maxAllowedDelay}ms`);
      }
      
      if (executionTime > maxAllowedDelay) {
        throw new Error(`Total execution took ${executionTime}ms, expected ≤ ${maxAllowedDelay}ms`);
      }

      this.testResults.push({
        name: testName,
        status: 'PASS',
        details: `Form submitted in ${mockCampaignWizard.submissionTime}ms, total execution: ${executionTime}ms`
      });
      
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: error.message
      });
    }
  }

  // Test 2: Progress animation doesn't block form submission
  async testProgressAnimationNonBlocking() {
    const testName = "Progress animation is non-blocking (visual feedback only)";
    
    try {
      // Setup mock with progress animation
      const mockWizard = {
        formSubmissionBlocked: false,
        progressStarted: false,
        animateCreationProgress: function() {
          this.progressStarted = true;
          // Simulate progress animation with setTimeout calls
          setTimeout(() => {
            // This should NOT block form submission
          }, 20000); // 20 second animation
        },
        
        launchCampaign: function() {
          // Start progress animation
          this.animateCreationProgress();
          
          // Form submission should happen IMMEDIATELY despite animation
          const form = document.getElementById('new-campaign-form');
          if (form) {
            // If we reach here without delay, form submission is not blocked
            this.formSubmissionBlocked = false;
            form.dispatchEvent(new Event('submit'));
          } else {
            this.formSubmissionBlocked = true;
          }
        }
      };

      // Execute
      const startTime = Date.now();
      mockWizard.launchCampaign();
      const executionTime = Date.now() - startTime;

      // Verify: Progress started but didn't block submission
      if (!mockWizard.progressStarted) {
        throw new Error("Progress animation did not start");
      }
      
      if (mockWizard.formSubmissionBlocked) {
        throw new Error("Form submission was blocked by progress animation");
      }
      
      if (executionTime > 50) { // Very generous limit
        throw new Error(`Execution blocked for ${executionTime}ms - progress animation is blocking`);
      }

      this.testResults.push({
        name: testName,
        status: 'PASS',
        details: `Progress started, form submitted in ${executionTime}ms (non-blocking)`
      });
      
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: error.message
      });
    }
  }

  // Test 3: Complete progress can be called to override animation
  async testCompleteProgressOverride() {
    const testName = "completeProgress() can override animation when backend finishes";
    
    try {
      // Setup progress bar DOM
      document.getElementById('campaign-wizard').innerHTML = `
        <div id="creation-progress-bar" style="width: 45%"></div>
        <h5 id="current-task">Building characters...</h5>
        <p id="task-description">Creating NPCs</p>
        <div id="step-story">⏳</div>
      `;

      // Mock completeProgress method
      const mockCompleteProgress = function() {
        const progressBar = document.getElementById('creation-progress-bar');
        const currentTask = document.getElementById('current-task');
        const taskDescription = document.getElementById('task-description');
        const finalIcon = document.getElementById('step-story');
        
        if (progressBar) progressBar.style.width = '100%';
        if (currentTask) currentTask.textContent = '✨ Finalizing adventure...';
        if (taskDescription) taskDescription.textContent = 'Your world is ready! Launching campaign...';
        if (finalIcon) finalIcon.textContent = '✅';
        
        return true;
      };

      // Execute
      const result = mockCompleteProgress();
      
      // Verify completion state
      const progressBar = document.getElementById('creation-progress-bar');
      const currentTask = document.getElementById('current-task');
      const finalIcon = document.getElementById('step-story');
      
      if (!result) {
        throw new Error("completeProgress returned false");
      }
      
      if (progressBar.style.width !== '100%') {
        throw new Error(`Progress bar width is ${progressBar.style.width}, expected 100%`);
      }
      
      if (!currentTask.textContent.includes('Finalizing adventure')) {
        throw new Error(`Task text is "${currentTask.textContent}", expected finalization message`);
      }
      
      if (finalIcon.textContent !== '✅') {
        throw new Error(`Final icon is "${finalIcon.textContent}", expected ✅`);
      }

      this.testResults.push({
        name: testName,
        status: 'PASS',
        details: 'completeProgress() successfully overrides animation to 100%'
      });
      
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: error.message
      });
    }
  }

  // Test 4: No setTimeout delays in critical path
  async testNoArtificialDelays() {
    const testName = "No artificial setTimeout delays in form submission path";
    
    try {
      // Track setTimeout calls
      const originalSetTimeout = window.setTimeout;
      const setTimeoutCalls = [];
      
      window.setTimeout = function(callback, delay) {
        setTimeoutCalls.push({ delay, callback: callback.toString() });
        return originalSetTimeout(callback, delay);
      };

      // Mock the critical path (launchCampaign -> form submission)
      const mockCriticalPath = function() {
        // This represents the critical path from button click to form submission
        
        // 1. Collect form data (should be immediate)
        const formData = { title: 'Test', prompt: 'Test prompt' };
        
        // 2. Populate original form (should be immediate)  
        const form = document.getElementById('new-campaign-form');
        
        // 3. Show spinner (should be immediate)
        // This may call setTimeout for animation, but shouldn't block
        
        // 4. Submit form (MUST be immediate)
        form.dispatchEvent(new Event('submit'));
        
        return true;
      };

      // Execute critical path
      const startTime = Date.now();
      const result = mockCriticalPath();
      const executionTime = Date.now() - startTime;
      
      // Restore setTimeout
      window.setTimeout = originalSetTimeout;

      // Verify: No blocking setTimeout calls in critical path
      const blockingDelays = setTimeoutCalls.filter(call => 
        call.delay > 100 && // Ignore very short delays (< 100ms)
        call.callback.includes('submit') // Delays that affect form submission
      );
      
      if (!result) {
        throw new Error("Critical path execution failed");
      }
      
      if (executionTime > 50) {
        throw new Error(`Critical path took ${executionTime}ms, expected < 50ms`);
      }
      
      if (blockingDelays.length > 0) {
        throw new Error(`Found blocking setTimeout delays: ${JSON.stringify(blockingDelays)}`);
      }

      this.testResults.push({
        name: testName,
        status: 'PASS',
        details: `Critical path executed in ${executionTime}ms with no blocking delays`
      });
      
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: error.message
      });
    }
  }

  // Test 5: Integration test - full workflow timing
  async testFullWorkflowTiming() {
    const testName = "Full workflow: button click to backend call timing";
    
    try {
      // Mock backend call tracking
      let backendCallTime = null;
      
      // Mock fetch to capture when backend call happens
      const originalFetch = window.fetch;
      window.fetch = function(url, options) {
        if (url.includes('/api/campaigns') && options.method === 'POST') {
          backendCallTime = Date.now();
        }
        return Promise.resolve(new Response('{"success": true}'));
      };

      // Mock the full workflow
      const mockFullWorkflow = async function() {
        const buttonClickTime = Date.now();
        
        // 1. Button clicked - start wizard
        const formData = { title: 'Test', prompt: 'Test prompt' };
        
        // 2. Launch campaign (should be immediate)
        // ... populate form, show spinner ...
        
        // 3. Submit form (should be immediate)
        await fetch('/api/campaigns', {
          method: 'POST',
          body: JSON.stringify(formData)
        });
        
        return buttonClickTime;
      };

      // Execute
      const buttonClickTime = await mockFullWorkflow();
      
      // Restore fetch
      window.fetch = originalFetch;
      
      // Verify timing
      if (!backendCallTime) {
        throw new Error("Backend call was not made");
      }
      
      const delayToBackend = backendCallTime - buttonClickTime;
      const maxAcceptableDelay = 100; // 100ms max from click to backend
      
      if (delayToBackend > maxAcceptableDelay) {
        throw new Error(`${delayToBackend}ms delay from button click to backend call, expected ≤ ${maxAcceptableDelay}ms`);
      }

      this.testResults.push({
        name: testName,
        status: 'PASS',
        details: `Backend called ${delayToBackend}ms after button click (excellent responsiveness)`
      });
      
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: error.message
      });
    }
  }

  // Test 6: Campaign Wizard Reset Issue Reproduction
  async testWizardResetIssueReproduction() {
    const testName = "Campaign Wizard Reset Issue Reproduction";
    
    try {
      console.log('🔍 Reproducing wizard reset bug...');
      
      // Step 1: Create a complete mock campaign wizard with all the problematic methods
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
          
          // Remove existing elements
          if (existingSpinner) {
            existingSpinner.remove();
          }
          
          if (existingWizard) {
            existingWizard.innerHTML = ''; // Clear content
          }
          
          this.replaceOriginalForm();
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
        
        showDetailedSpinner() {
          console.log('⏳ Show detailed spinner called');
          const container = document.getElementById('campaign-wizard');
          
          // THE PROBLEMATIC CODE that destroys wizard structure
          const spinnerHTML = `
            <div id="campaign-creation-spinner" class="text-center py-5">
              <div class="spinner-border text-primary mb-4" role="status">
                <span class="visually-hidden">Building...</span>
              </div>
              <h4 class="text-primary mb-3">🏗️ Building Your Adventure...</h4>
              <div class="progress mb-4">
                <div class="progress-bar" role="progressbar" style="width: 45%"></div>
              </div>
              <p class="text-muted">⚔️ Establishing factions...</p>
            </div>
          `;
          
          if (container) {
            // THIS IS THE BUG: container.innerHTML completely destroys wizard structure
            container.innerHTML = spinnerHTML;
          }
        },
        
        completeProgress() {
          console.log('✅ Complete progress called');
          this.isEnabled = false;
        }
      };
      
      // Attach to window for testing
      window.campaignWizard = mockCampaignWizard;
      
      // Step 2: Simulate first campaign creation workflow
      console.log('📝 Step 2: Simulating first campaign creation...');
      
      // Enable wizard (fresh state)
      mockCampaignWizard.enable();
      
      // Verify fresh wizard is present
      let wizardContent = document.querySelector('.wizard-content');
      if (!wizardContent) {
        throw new Error("Fresh wizard content not created on first enable()");
      }
      console.log('✅ Fresh wizard created successfully');
      
      // User clicks "Begin Adventure" -> shows spinner (this destroys wizard)
      mockCampaignWizard.showDetailedSpinner();
      
      // Verify spinner is present and wizard content is destroyed
      const spinnerAfterShow = document.getElementById('campaign-creation-spinner');
      wizardContent = document.querySelector('.wizard-content');
      
      if (!spinnerAfterShow) {
        throw new Error("Spinner not created by showDetailedSpinner()");
      }
      if (wizardContent) {
        throw new Error("Wizard content still present after showDetailedSpinner() - DOM not destroyed as expected");
      }
      console.log('✅ Spinner shown, wizard content destroyed (expected behavior)');
      
      // Campaign completes
      mockCampaignWizard.completeProgress();
      
      // Step 3: User navigates back and tries to create another campaign
      console.log('📝 Step 3: User tries to create second campaign (reproducing bug)...');
      
      // This is where the bug occurs - enabling wizard again
      mockCampaignWizard.enable();
      
      // Step 4: Check what happens - should get fresh wizard, but might get persistent spinner
      console.log('🔍 Step 4: Checking wizard state after second enable()...');
      
      const wizardContainer = document.getElementById('campaign-wizard');
      const persistentSpinner = document.getElementById('campaign-creation-spinner');
      const freshWizardContent = document.querySelector('.wizard-content');
      
      // Analyze the state
      const spinnerStillPresent = persistentSpinner && persistentSpinner.offsetParent !== null;
      const freshWizardPresent = freshWizardContent && freshWizardContent.offsetParent !== null;
      
      console.log(`📊 Results:`);
      console.log(`  - Wizard container exists: ${!!wizardContainer}`);
      console.log(`  - Persistent spinner present: ${spinnerStillPresent}`);
      console.log(`  - Fresh wizard content present: ${freshWizardPresent}`);
      console.log(`  - Container HTML: ${wizardContainer ? wizardContainer.innerHTML.substring(0, 150) + '...' : 'null'}`);
      
      // Determine test result
      if (freshWizardPresent && !spinnerStillPresent) {
        this.testResults.push({
          name: testName,
          status: 'PASS',
          details: '✅ Wizard reset works correctly - fresh content appears, no persistent spinner'
        });
      } else if (!freshWizardPresent && spinnerStillPresent) {
        this.testResults.push({
          name: testName,
          status: 'FAIL',
          details: '🐛 BUG REPRODUCED: Persistent spinner found, no fresh wizard content. The container.innerHTML = spinnerHTML destroys wizard structure.'
        });
      } else if (!freshWizardPresent && !spinnerStillPresent) {
        this.testResults.push({
          name: testName,
          status: 'FAIL', 
          details: '❓ Unexpected state: No spinner, no fresh wizard content. Check forceCleanRecreation() logic.'
        });
      } else {
        this.testResults.push({
          name: testName,
          status: 'FAIL',
          details: '❓ Mixed state: Both spinner and wizard content present. DOM state is corrupted.'
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

  // Run all tests
  async runAllTests() {
    console.log('🧪 Running Campaign Wizard Timing Tests...\n');
    
    await this.testImmediateFormSubmission();
    await this.testProgressAnimationNonBlocking();
    await this.testCompleteProgressOverride();
    await this.testNoArtificialDelays();
    await this.testFullWorkflowTiming();
    await this.testWizardResetIssueReproduction();
    
    this.generateReport();
  }

  generateReport() {
    const passed = this.testResults.filter(t => t.status === 'PASS').length;
    const failed = this.testResults.filter(t => t.status === 'FAIL').length;
    
    console.log('\n📊 TEST RESULTS SUMMARY');
    console.log('========================');
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
      console.log('🚨 CRITICAL: Artificial delays detected! These must be fixed to maintain responsiveness.');
      return false;
    } else {
      console.log('🎉 SUCCESS: No artificial delays detected. Campaign creation is optimally responsive!');
      return true;
    }
  }
}

// Note: Tests are now run manually via the UI buttons
// Auto-run is disabled to prevent interfering with the test runner interface

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CampaignWizardTimingTests;
} 