#!/usr/bin/env node

/**
 * Frontend Structured Fields Tests (Simple Version)
 * Tests the structured fields rendering logic without browser dependencies
 */

class StructuredFieldsSimpleTest {
  constructor() {
    this.testResults = [];
    this.passCount = 0;
    this.failCount = 0;
  }

  log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${type.toUpperCase()}: ${message}`;
    console.log(logEntry);
  }

  assert(condition, message) {
    if (condition) {
      this.log(`✅ PASS: ${message}`, 'pass');
      this.passCount++;
      return true;
    } else {
      this.log(`❌ FAIL: ${message}`, 'fail');
      this.failCount++;
      return false;
    }
  }

  // Mock implementation of generateStructuredFieldsHTML
  generateStructuredFieldsHTML(fullData, debugMode) {
    let html = '';

    // Add dice rolls if present
    if (fullData.dice_rolls && fullData.dice_rolls.length > 0) {
      html += '<div class="dice-rolls">';
      html += '<strong>🎲 Dice Rolls:</strong><ul>';
      fullData.dice_rolls.forEach(roll => {
        html += `<li>${this.escapeHtml(roll)}</li>`;
      });
      html += '</ul></div>';
    }

    // Add resources if present
    if (fullData.resources) {
      html += `<div class="resources"><strong>📊 Resources:</strong> ${this.escapeHtml(fullData.resources)}</div>`;
    }

    // Add planning block if present (always at the bottom)
    if (fullData.planning_block) {
      html += `<div class="planning-block">${this.escapeHtml(fullData.planning_block)}</div>`;
    }

    // Add debug info if in debug mode
    if (debugMode && fullData.debug_info && Object.keys(fullData.debug_info).length > 0) {
      html += '<div class="debug-info">';
      html += '<strong>🔍 Debug Info:</strong><br>';
      html += '<pre>' + this.escapeHtml(JSON.stringify(fullData.debug_info, null, 2)) + '</pre>';
      html += '</div>';
    }

    return html;
  }

  // Simple HTML escape function
  escapeHtml(text) {
    if (typeof text !== 'string') return String(text);
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Test 1: Basic HTML generation for all fields
  testGenerateStructuredFieldsHTML() {
    this.log('📝 Test 1: Basic HTML generation for all fields');

    const testData = {
      dice_rolls: ["Attack: 1d20+5 = 18", "Damage: 2d6+3 = 11"],
      resources: "HP: 45/50 | Gold: 120",
      planning_block: "**Next Steps:**\n1. Explore\n2. Rest",
      debug_info: { tokens: 100, model: "gemini-2.5-flash" }
    };

    const html = this.generateStructuredFieldsHTML(testData, true);

    // Check that all fields are present
    this.assert(html.includes('🎲 Dice Rolls:'), 'Dice rolls header present');
    this.assert(html.includes('Attack: 1d20+5 = 18'), 'First dice roll present');
    this.assert(html.includes('Damage: 2d6+3 = 11'), 'Second dice roll present');
    this.assert(html.includes('📊 Resources:'), 'Resources header present');
    this.assert(html.includes('HP: 45/50'), 'Resources content present');
    this.assert(html.includes('**Next Steps:**'), 'Planning block present');
    this.assert(html.includes('🔍 Debug Info:'), 'Debug info header present (debug mode on)');
    this.assert(html.includes('tokens') && html.includes('100'), 'Debug info content present');

    // Test without debug mode
    const htmlNoDebug = this.generateStructuredFieldsHTML(testData, false);
    this.assert(!htmlNoDebug.includes('🔍 Debug Info:'), 'Debug info hidden when debug mode off');
  }

  // Test 2: Empty fields handling
  testEmptyFieldsHandling() {
    this.log('📝 Test 2: Empty fields handling');

    const emptyData = {
      dice_rolls: [],
      resources: "",
      planning_block: "",
      debug_info: {}
    };

    const html = this.generateStructuredFieldsHTML(emptyData, true);

    // Check that empty fields are not rendered
    this.assert(!html.includes('🎲 Dice Rolls:'), 'Empty dice rolls not rendered');
    this.assert(!html.includes('📊 Resources:'), 'Empty resources not rendered');
    this.assert(!html.includes('planning-block'), 'Empty planning block not rendered');
    this.assert(!html.includes('🔍 Debug Info:'), 'Empty debug info not rendered');
    this.assert(html === '', 'Empty data returns empty string');
  }

  // Test 3: Missing fields handling
  testMissingFieldsHandling() {
    this.log('📝 Test 3: Missing fields handling');

    const partialData = {
      dice_rolls: ["Critical Hit: 20"],
      // resources missing
      planning_block: "Continue forward"
      // debug_info missing
    };

    const html = this.generateStructuredFieldsHTML(partialData, true);

    // Check that present fields are rendered
    this.assert(html.includes('Critical Hit: 20'), 'Present dice roll rendered');
    this.assert(html.includes('Continue forward'), 'Present planning block rendered');

    // Check that missing fields are not causing errors
    this.assert(!html.includes('📊 Resources:'), 'Missing resources field handled gracefully');
    this.assert(!html.includes('🔍 Debug Info:'), 'Missing debug info field handled gracefully');
  }

  // Test 4: XSS prevention
  testXSSPrevention() {
    this.log('📝 Test 4: XSS prevention');

    const maliciousData = {
      dice_rolls: ["<script>alert('XSS')</script>"],
      resources: "<img src=x onerror='alert(1)'>",
      planning_block: "Normal text & special <characters>",
      debug_info: { script: "<script>evil()</script>" }
    };

    const html = this.generateStructuredFieldsHTML(maliciousData, true);

    // Check that dangerous content is escaped
    this.assert(!html.includes('<script>'), 'Script tags are escaped');
    this.assert(html.includes('onerror=&#039;') || !html.includes('onerror'), 'Event handlers are escaped');
    this.assert(html.includes('&lt;script&gt;'), 'Script tags converted to entities');
    this.assert(html.includes('&amp;'), 'Ampersands are escaped');
    this.assert(html.includes('&lt;characters&gt;'), 'Angle brackets are escaped');
  }

  // Test 5: Special characters and formatting
  testSpecialCharacters() {
    this.log('📝 Test 5: Special characters and formatting');

    const specialData = {
      dice_rolls: ["🎲 Natural 20! 🎉", "Fire damage: 🔥 2d6"],
      resources: "💰 Gold: 500 | ❤️ HP: 100/100",
      planning_block: "→ Next: Talk to the 🧙‍♂️ wizard\n• Find the 🗝️ key",
      debug_info: { emojis: "✅ Working!" }
    };

    const html = this.generateStructuredFieldsHTML(specialData, true);

    // Check that emojis and special characters are preserved
    this.assert(html.includes('🎲 Natural 20! 🎉'), 'Emojis in dice rolls preserved');
    this.assert(html.includes('💰 Gold:'), 'Emojis in resources preserved');
    this.assert(html.includes('🧙‍♂️ wizard'), 'Complex emojis preserved');
    this.assert(html.includes('→ Next:'), 'Special arrows preserved');
    this.assert(html.includes('• Find'), 'Bullet points preserved');
  }

  // Test 6: Structured field CSS classes
  testCSSClasses() {
    this.log('📝 Test 6: CSS class structure');

    const testData = {
      dice_rolls: ["Test roll"],
      resources: "Test resources",
      planning_block: "Test planning",
      debug_info: { test: true }
    };

    const html = this.generateStructuredFieldsHTML(testData, true);

    // Check that proper CSS classes are applied
    this.assert(html.includes('class="dice-rolls"'), 'Dice rolls have correct CSS class');
    this.assert(html.includes('class="resources"'), 'Resources have correct CSS class');
    this.assert(html.includes('class="planning-block"'), 'Planning block has correct CSS class');
    this.assert(html.includes('class="debug-info"'), 'Debug info has correct CSS class');
  }

  // Run all tests
  runTests() {
    this.log('🚀 Starting Structured Fields Frontend Tests (Simple Version)', 'info');
    this.log('='.repeat(60), 'info');

    // Run test suite
    this.testGenerateStructuredFieldsHTML();
    this.testEmptyFieldsHandling();
    this.testMissingFieldsHandling();
    this.testXSSPrevention();
    this.testSpecialCharacters();
    this.testCSSClasses();

    // Summary
    this.log('='.repeat(60), 'info');
    const total = this.passCount + this.failCount;
    this.log(`Test Summary: ${this.passCount}/${total} passed`, 'info');

    if (this.failCount > 0) {
      this.log(`❌ ${this.failCount} tests failed`, 'fail');
      process.exit(1);
    } else {
      this.log('✅ All tests passed!', 'pass');
      process.exit(0);
    }
  }
}

// Run tests if executed directly
if (require.main === module) {
  const test = new StructuredFieldsSimpleTest();
  test.runTests();
}

module.exports = StructuredFieldsSimpleTest;
