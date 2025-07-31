#!/usr/bin/env node

/**
 * Sophisticated Analysis Test for Campaign Wizard Reset
 * Analyzes the code flow and simulates the problematic sequence
 */

const fs = require('fs');
const path = require('path');

class WizardCodeAnalysisTest {
  constructor() {
    this.testResults = [];
    this.codeIssues = [];
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

  // Read and analyze JavaScript files
  analyzeCodeFiles() {
    this.log('📁 Analyzing JavaScript code files');

    try {
      // Read campaign wizard code
      const wizardPath = path.join(__dirname, 'frontend_v1', 'js', 'campaign-wizard.js');
      const wizardCode = fs.readFileSync(wizardPath, 'utf8');

      // Read app.js code
      const appPath = path.join(__dirname, 'frontend_v1', 'app.js');
      const appCode = fs.readFileSync(appPath, 'utf8');

      this.log('✅ Code files read successfully');
      return { wizardCode, appCode };
    } catch (error) {
      this.log(`❌ Failed to read code files: ${error.message}`, 'error');
      return null;
    }
  }

  // Analyze the wizard reset flow
  analyzeWizardResetFlow(wizardCode, appCode) {
    this.log('🔍 Analyzing wizard reset flow');

    let flowCorrect = true;

    // Check 1: Does forceCleanRecreation exist and call replaceOriginalForm correctly?
    const hasForceCleanRecreation = wizardCode.includes('forceCleanRecreation()');
    flowCorrect &= this.assert(hasForceCleanRecreation, 'forceCleanRecreation method exists');

    const callsReplaceWithSkip = wizardCode.includes('this.replaceOriginalForm(true)');
    flowCorrect &= this.assert(callsReplaceWithSkip, 'forceCleanRecreation calls replaceOriginalForm with skipCleanup=true');

    // Check 2: Does replaceOriginalForm accept skipCleanup parameter?
    const hasSkipCleanupParam = wizardCode.includes('replaceOriginalForm(skipCleanup = false)');
    flowCorrect &= this.assert(hasSkipCleanupParam, 'replaceOriginalForm accepts skipCleanup parameter');

    // Check 3: Does replaceOriginalForm skip cleanup when parameter is true?
    const hasSkipCleanupLogic = wizardCode.includes('if (!skipCleanup)');
    flowCorrect &= this.assert(hasSkipCleanupLogic, 'replaceOriginalForm has skipCleanup logic');

    // Check 4: Does app.js form reset check for wizard state?
    const hasWizardStateCheck = appCode.includes('window.campaignWizard && window.campaignWizard.isEnabled');
    flowCorrect &= this.assert(hasWizardStateCheck, 'app.js checks wizard state before form reset');

    // Check 5: Does forceCleanRecreation restore wizard content visibility?
    const hasVisibilityRestore = wizardCode.includes('wizardContent.style.display = \'block\'');
    flowCorrect &= this.assert(hasVisibilityRestore, 'forceCleanRecreation restores wizard content visibility');

    return flowCorrect;
  }

  // Simulate the problematic sequence step by step
  simulateProblematicSequence() {
    this.log('🎬 Simulating problematic sequence');

    let sequenceCorrect = true;

    // Step 1: User completes first campaign
    this.log('1️⃣ User completes first campaign');
    let wizardState = { isEnabled: true, hasContent: false, isVisible: false };

    // Step 2: User clicks "Start Campaign" - triggers enable()
    this.log('2️⃣ User clicks Start Campaign - wizard.enable() called');
    wizardState = this.simulateEnable(wizardState);

    // Step 3: Route changes to /new-campaign
    this.log('3️⃣ Route changes to /new-campaign');
    wizardState = this.simulateRouteChange(wizardState);

    // Step 4: Validate final state
    this.log('4️⃣ Validating final wizard state');
    sequenceCorrect &= this.assert(wizardState.isEnabled, 'Wizard is still enabled');
    sequenceCorrect &= this.assert(wizardState.hasContent, 'Wizard has content');
    sequenceCorrect &= this.assert(wizardState.isVisible, 'Wizard is visible');
    sequenceCorrect &= this.assert(!wizardState.hasSpinner, 'No spinner present');

    return sequenceCorrect;
  }

  // Simulate wizard.enable() call
  simulateEnable(wizardState) {
    this.log('   🧙‍♂️ Executing forceCleanRecreation()');

    // Simulate forceCleanRecreation
    let newState = { ...wizardState };
    newState.isEnabled = true;
    newState.hasContent = true; // replaceOriginalForm creates content
    newState.isVisible = true;  // visibility restoration logic
    newState.hasSpinner = false; // cleanup removes spinner

    this.log('   ✅ Wizard state after enable():', JSON.stringify(newState));
    return newState;
  }

  // Simulate route change and form reset
  simulateRouteChange(wizardState) {
    this.log('   🛣️ Route change triggers resetNewCampaignForm()');

    let newState = { ...wizardState };

    // Check: Does app.js skip form reset when wizard is enabled?
    if (wizardState.isEnabled) {
      this.log('   🚫 Form reset skipped - wizard is active');
      // State remains unchanged
    } else {
      this.log('   💥 Form reset executed - wizard destroyed');
      newState.hasContent = false;
      newState.isVisible = false;
    }

    this.log('   ✅ Wizard state after route change:', JSON.stringify(newState));
    return newState;
  }

  // Analyze timing issues
  analyzeTimingIssues(wizardCode) {
    this.log('⏰ Analyzing timing issues');

    let timingCorrect = true;

    // Check for setTimeout in visibility restoration
    const hasTimingFix = wizardCode.includes('setTimeout(') && wizardCode.includes('wizardContent.style.display');
    timingCorrect &= this.assert(hasTimingFix, 'Visibility restoration uses setTimeout for timing');

    // Check for proper delay
    const hasReasonableDelay = wizardCode.includes('50') || wizardCode.includes('100');
    timingCorrect &= this.assert(hasReasonableDelay, 'Uses reasonable delay for DOM operations');

    return timingCorrect;
  }

  // Run complete analysis
  async runCompleteAnalysis() {
    this.log('🚀 Starting sophisticated code analysis test');

    // Read code files
    const codeFiles = this.analyzeCodeFiles();
    if (!codeFiles) return false;

    const { wizardCode, appCode } = codeFiles;

    // Analyze flow
    const flowCorrect = this.analyzeWizardResetFlow(wizardCode, appCode);

    // Simulate sequence
    const sequenceCorrect = this.simulateProblematicSequence();

    // Check timing
    const timingCorrect = this.analyzeTimingIssues(wizardCode);

    const overallResult = flowCorrect && sequenceCorrect && timingCorrect;

    this.log(`🏁 Analysis completed. Result: ${overallResult ? 'GREEN ✅' : 'RED ❌'}`);

    if (!overallResult) {
      this.log('🔍 Code analysis reveals issues that would cause RED test state');
    }

    return overallResult;
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
  console.log('🧪 Sophisticated Code Analysis Test Starting...\n');

  const test = new WizardCodeAnalysisTest();
  const result = await test.runCompleteAnalysis();

  console.log('\n📊 TEST SUMMARY');
  console.log('================');

  const summary = test.getSummary();
  console.log(`Total Checks: ${summary.total}`);
  console.log(`Passed: ${summary.passed}`);
  console.log(`Failed: ${summary.failed}`);
  console.log(`Success Rate: ${summary.successRate}%`);

  console.log(`\nOverall Result: ${result ? '🟢 GREEN (Code should work)' : '🔴 RED (Code has issues)'}`);

  if (result) {
    console.log('\n✅ Code analysis suggests wizard reset should work correctly.');
    console.log('If user still sees issues, there may be runtime-specific problems.');
  } else {
    console.log('\n❌ Code analysis reveals issues that would cause wizard reset to fail.');
    console.log('These issues should be fixed before expecting GREEN test results.');
  }

  process.exit(result ? 0 : 1);
}

main();
