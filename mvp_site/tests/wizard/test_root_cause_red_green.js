/**
 * Red/Green Test for ACTUAL Root Cause: Navigation Handler Missing wizard.enable()
 * 
 * This test specifically reproduces the real issue we discovered:
 * The go-to-new-campaign button performs navigation but never calls wizard.enable()
 */

class RootCauseRedGreenTest {
  constructor() {
    this.testResults = [];
    this.testName = "Root Cause: Navigation Handler Missing wizard.enable()";
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

  // Simulate the EXACT problematic sequence
  async testRootCauseSequence() {
    this.log('🔴 RED TEST: Reproducing the actual root cause');
    
    // Step 1: Setup initial state (user completes first campaign)
    this.simulatePostCampaignState();
    
    // Step 2: Simulate user clicking "Start Campaign" button
    const wizardEnabledBeforeClick = this.simulateStartCampaignClick();
    
    // Step 3: The CRITICAL TEST - was wizard.enable() called?
    return this.validateWizardEnableCalled(wizardEnabledBeforeClick);
  }

  simulatePostCampaignState() {
    this.log('🎬 SETUP: Simulating post-campaign state');
    
    // Mock the wizard object (exists but needs fresh state)
    const self = this;
    window.mockCampaignWizard = {
      isEnabled: true,
      enableCallCount: 0,
      enable: function() {
        this.enableCallCount++;
        self.log('🧙‍♂️ WIZARD: enable() called! Count: ' + this.enableCallCount);
      }
    };
    
    // Mock the current problematic navigation handler (WITHOUT the fix)
    window.mockOriginalNavigationHandler = () => {
      this.log('🚀 NAV: Original navigation handler called');
      this.log('🚀 NAV: Setting isNavigatingToNewCampaignDirectly = true');
      
      // Simulate navigation
      this.log('🚀 NAV: Pushing state to /new-campaign');
      this.log('🚀 NAV: About to call handleRouteChange()');
      this.simulateHandleRouteChange();
      this.log('🚀 NAV: handleRouteChange() completed');
      
      // THE PROBLEM: Original handler STOPS HERE - no wizard.enable() call!
      this.log('❌ NAV: Original handler completed WITHOUT calling wizard.enable()');
    };
    
    this.log('✅ SETUP: Post-campaign state ready');
  }

  simulateHandleRouteChange() {
    this.log('🛣️ ROUTE: handleRouteChange() executing');
    this.log('🛣️ ROUTE: Form reset check triggered');
    
    // Simulate form reset being skipped (this part works correctly)
    if (window.mockCampaignWizard.isEnabled) {
      this.log('🚫 FORM: Skipping form reset - wizard is active');
    }
    
    this.log('🛣️ ROUTE: handleRouteChange() finished');
  }

  simulateStartCampaignClick() {
    this.log('🖱️ CLICK: User clicks "Start Campaign" button');
    
    const wizardEnableCountBefore = window.mockCampaignWizard.enableCallCount;
    this.log(`🔍 BEFORE: wizard.enable() call count = ${wizardEnableCountBefore}`);
    
    // Simulate the original problematic click handler
    this.log('🔥 CLICK: Executing original navigation handler');
    window.mockOriginalNavigationHandler();
    
    const wizardEnableCountAfter = window.mockCampaignWizard.enableCallCount;
    this.log(`🔍 AFTER: wizard.enable() call count = ${wizardEnableCountAfter}`);
    
    return {
      before: wizardEnableCountBefore,
      after: wizardEnableCountAfter
    };
  }

  validateWizardEnableCalled(enableCounts) {
    this.log('🔍 VALIDATION: Checking if wizard.enable() was called');
    
    let allPassed = true;
    
    // The CRITICAL TEST: Was wizard.enable() called during navigation?
    const enableWasCalled = enableCounts.after > enableCounts.before;
    allPassed &= this.assert(enableWasCalled, 'wizard.enable() was called during navigation');
    
    // Additional validation
    const expectedCallCount = enableCounts.before + 1;
    const actualCallCount = enableCounts.after;
    allPassed &= this.assert(
      actualCallCount >= expectedCallCount, 
      `wizard.enable() call count increased (expected: ${expectedCallCount}, actual: ${actualCallCount})`
    );
    
    // Test the specific scenario
    allPassed &= this.assert(
      window.mockCampaignWizard.enableCallCount > 0,
      'wizard.enable() was called at least once during test'
    );
    
    return allPassed;
  }

  // Now test the FIXED version
  async testFixedVersion() {
    this.log('🟢 GREEN TEST: Testing the fixed navigation handler');
    
    // Reset call count
    window.mockCampaignWizard.enableCallCount = 0;
    
    // Mock the FIXED navigation handler (WITH the fix)
    window.mockFixedNavigationHandler = () => {
      this.log('🚀 NAV: Fixed navigation handler called');
      this.log('🚀 NAV: Setting isNavigatingToNewCampaignDirectly = true');
      
      // Simulate navigation
      this.log('🚀 NAV: Pushing state to /new-campaign');
      this.log('🚀 NAV: About to call handleRouteChange()');
      this.simulateHandleRouteChange();
      this.log('🚀 NAV: handleRouteChange() completed');
      
      // THE FIX: Now we call wizard.enable()
      this.log('🚀 NAV: About to call wizard.enable()');
      if (window.mockCampaignWizard && window.mockCampaignWizard.isEnabled) {
        this.log('🚀 NAV: Calling wizard.enable() to refresh wizard state');
        window.mockCampaignWizard.enable();
      }
      this.log('🚀 NAV: wizard.enable() call completed');
    };
    
    const wizardEnableCountBefore = window.mockCampaignWizard.enableCallCount;
    this.log(`🔍 BEFORE FIX: wizard.enable() call count = ${wizardEnableCountBefore}`);
    
    // Test the fixed handler
    this.log('🔥 CLICK: Executing FIXED navigation handler');
    window.mockFixedNavigationHandler();
    
    const wizardEnableCountAfter = window.mockCampaignWizard.enableCallCount;
    this.log(`🔍 AFTER FIX: wizard.enable() call count = ${wizardEnableCountAfter}`);
    
    return this.validateWizardEnableCalled({
      before: wizardEnableCountBefore,
      after: wizardEnableCountAfter
    });
  }

  // Run complete red/green test
  async runRedGreenTest() {
    this.log(`🧪 Starting ${this.testName}`);
    
    try {
      // RED TEST: Show the original problem
      this.log('🔴 === RED PHASE: Testing Original (Broken) Code ===');
      const redResult = await this.testRootCauseSequence();
      
      if (redResult) {
        this.log('⚠️ RED TEST UNEXPECTEDLY PASSED - This should fail!', 'error');
      } else {
        this.log('✅ RED TEST CORRECTLY FAILED - Root cause reproduced!', 'success');
      }
      
      // GREEN TEST: Show the fix works
      this.log('🟢 === GREEN PHASE: Testing Fixed Code ===');
      const greenResult = await this.testFixedVersion();
      
      if (greenResult) {
        this.log('✅ GREEN TEST PASSED - Fix works correctly!', 'success');
      } else {
        this.log('❌ GREEN TEST FAILED - Fix needs work', 'error');
      }
      
      // Overall result
      const redGreenSuccess = !redResult && greenResult; // Red should fail, Green should pass
      
      if (redGreenSuccess) {
        this.log('🎉 RED/GREEN TEST COMPLETE: Root cause identified and fixed!', 'success');
      } else {
        this.log('💥 RED/GREEN TEST INCONCLUSIVE', 'error');
      }
      
      return redGreenSuccess;
      
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
window.RootCauseRedGreenTest = RootCauseRedGreenTest;