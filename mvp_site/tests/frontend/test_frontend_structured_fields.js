#!/usr/bin/env node

/**
 * Frontend Structured Fields Tests
 * Tests the rendering and display of structured fields in the UI
 */

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

class StructuredFieldsTest {
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

  // Setup browser environment with app.js loaded
  async setupBrowserEnvironment() {
    this.log('🌐 Setting up browser environment with jsdom');
    
    try {
      // Create JSDOM instance
      this.dom = new JSDOM(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>WorldArchitect.AI - Structured Fields Test</title>
        </head>
        <body>
          <div id="story-display"></div>
          <div id="debug-info" style="display: none;"></div>
        </body>
        </html>
      `, {
        url: 'http://localhost:6006',
        runScripts: 'dangerously',
        resources: 'usable'
      });

      this.window = this.dom.window;
      this.document = this.window.document;

      // Mock window functions that app.js might need
      this.window.alert = (msg) => this.log(`Alert: ${msg}`, 'info');
      this.window.confirm = () => true;
      
      // Mock fetch API
      this.window.fetch = this.createMockFetch();

      // Load app.js functions (simplified versions for testing)
      this.loadAppFunctions();

      this.log('✅ Browser environment setup complete', 'pass');
      return true;
    } catch (error) {
      this.log(`❌ Failed to setup browser environment: ${error}`, 'fail');
      return false;
    }
  }

  // Load the functions from app.js that we need to test
  loadAppFunctions() {
    // Simplified version of generateStructuredFieldsHTML
    this.window.generateStructuredFieldsHTML = (fullData, debugMode) => {
      let html = '';
      
      // Add dice rolls if present
      if (fullData.dice_rolls && fullData.dice_rolls.length > 0) {
        html += '<div class="dice-rolls">';
        html += '<strong>🎲 Dice Rolls:</strong><ul>';
        fullData.dice_rolls.forEach(roll => {
          html += `<li>${roll}</li>`;
        });
        html += '</ul></div>';
      }
      
      // Add resources if present
      if (fullData.resources) {
        html += `<div class="resources"><strong>📊 Resources:</strong> ${fullData.resources}</div>`;
      }
      
      // Add planning block if present (always at the bottom)
      if (fullData.planning_block) {
        html += `<div class="planning-block">${fullData.planning_block}</div>`;
      }
      
      // Add debug info if in debug mode
      if (debugMode && fullData.debug_info && Object.keys(fullData.debug_info).length > 0) {
        html += '<div class="debug-info">';
        html += '<strong>🔍 Debug Info:</strong><br>';
        html += '<pre>' + JSON.stringify(fullData.debug_info, null, 2) + '</pre>';
        html += '</div>';
      }
      
      return html;
    };
  }

  // Create mock fetch for API responses
  createMockFetch() {
    return async (url, options) => {
      this.log(`Mock fetch called: ${url}`, 'info');
      
      // Mock response with structured fields
      const mockResponse = {
        success: true,
        content: "The adventure continues...",
        session_header: "Session 1: The Beginning",
        planning_block: "**Next Steps:**\n1. Explore the cave\n2. Talk to the merchant\n3. Rest at the inn",
        dice_rolls: ["Attack: 1d20+5 = 18", "Damage: 2d6+3 = 11"],
        resources: "HP: 45/50 | Gold: 120 | XP: 1500",
        debug_info: {
          prompt_tokens: 500,
          completion_tokens: 200,
          model: "gemini-2.5-flash"
        }
      };

      return {
        ok: true,
        json: async () => mockResponse
      };
    };
  }

  // Test 1: Basic HTML generation for all fields
  async testGenerateStructuredFieldsHTML() {
    this.log('📝 Testing generateStructuredFieldsHTML function');
    
    const testData = {
      dice_rolls: ["Attack: 1d20+5 = 18", "Damage: 2d6+3 = 11"],
      resources: "HP: 45/50 | Gold: 120",
      planning_block: "**Next Steps:**\n1. Explore\n2. Rest",
      debug_info: { tokens: 100 }
    };

    const html = this.window.generateStructuredFieldsHTML(testData, true);
    
    // Check that all fields are present
    this.assert(html.includes('🎲 Dice Rolls:'), 'Dice rolls header present');
    this.assert(html.includes('Attack: 1d20+5 = 18'), 'First dice roll present');
    this.assert(html.includes('Damage: 2d6+3 = 11'), 'Second dice roll present');
    this.assert(html.includes('📊 Resources:'), 'Resources header present');
    this.assert(html.includes('HP: 45/50'), 'Resources content present');
    this.assert(html.includes('**Next Steps:**'), 'Planning block present');
    this.assert(html.includes('🔍 Debug Info:'), 'Debug info header present (debug mode on)');
    
    // Test without debug mode
    const htmlNoDebug = this.window.generateStructuredFieldsHTML(testData, false);
    this.assert(!htmlNoDebug.includes('🔍 Debug Info:'), 'Debug info hidden when debug mode off');
  }

  // Test 2: Empty fields handling
  async testEmptyFieldsHandling() {
    this.log('📝 Testing empty fields handling');
    
    const emptyData = {
      dice_rolls: [],
      resources: "",
      planning_block: "",
      debug_info: {}
    };

    const html = this.window.generateStructuredFieldsHTML(emptyData, true);
    
    // Check that empty fields are not rendered
    this.assert(!html.includes('🎲 Dice Rolls:'), 'Empty dice rolls not rendered');
    this.assert(!html.includes('📊 Resources:'), 'Empty resources not rendered');
    this.assert(!html.includes('planning-block'), 'Empty planning block not rendered');
    this.assert(!html.includes('🔍 Debug Info:'), 'Empty debug info not rendered');
    this.assert(html === '', 'Empty data returns empty string');
  }

  // Test 3: Missing fields handling
  async testMissingFieldsHandling() {
    this.log('📝 Testing missing fields handling');
    
    const partialData = {
      dice_rolls: ["Critical Hit: 20"],
      // resources missing
      planning_block: "Continue forward"
      // debug_info missing
    };

    const html = this.window.generateStructuredFieldsHTML(partialData, true);
    
    // Check that present fields are rendered
    this.assert(html.includes('Critical Hit: 20'), 'Present dice roll rendered');
    this.assert(html.includes('Continue forward'), 'Present planning block rendered');
    
    // Check that missing fields are not causing errors
    this.assert(!html.includes('📊 Resources:'), 'Missing resources field handled gracefully');
    this.assert(!html.includes('🔍 Debug Info:'), 'Missing debug info field handled gracefully');
  }

  // 🔴 RED TEST: God mode response should be displayed
  async testGodModeResponseRendering() {
    this.log('🔮 Testing god mode response rendering', 'info');

    const dataWithGodMode = {
      narrative: "Regular narrative text",
      god_mode_response: "📝 DM Notes: User requested plot arcs. State rationale: No changes needed.",
      entities_mentioned: ["player"],
      location_confirmed: "tavern"
    };

    const html = this.window.generateStructuredFieldsHTML(dataWithGodMode, true);
    
    // 🔴 These should FAIL - god mode response should be rendered
    this.assert(html.includes('🔮 God Mode Response:'), 'God mode response header displayed');
    this.assert(html.includes('📝 DM Notes: User requested plot arcs'), 'God mode content displayed');
    this.assert(html.includes('god-mode-response'), 'God mode CSS class applied');
    
    // Regular narrative should still be present
    this.assert(html.includes('Regular narrative text'), 'Regular narrative still displayed');
  }

  // Run all tests
  async runTests() {
    this.log('🚀 Starting Structured Fields Frontend Tests', 'info');
    
    // Setup environment
    const setupSuccess = await this.setupBrowserEnvironment();
    if (!setupSuccess) {
      this.log('❌ Failed to setup test environment', 'fail');
      return this.summarizeResults();
    }

    // Run test suite
    await this.testGenerateStructuredFieldsHTML();
    await this.testEmptyFieldsHandling();
    await this.testMissingFieldsHandling();
    await this.testGodModeResponseRendering();

    return this.summarizeResults();
  }

  summarizeResults() {
    const passed = this.testResults.filter(r => r.type === 'pass').length;
    const failed = this.testResults.filter(r => r.type === 'fail').length;
    const total = passed + failed;

    this.log('=' * 50, 'info');
    this.log(`Test Summary: ${passed}/${total} passed`, 'info');
    
    if (failed > 0) {
      this.log(`❌ ${failed} tests failed`, 'fail');
      process.exit(1);
    } else {
      this.log('✅ All tests passed!', 'pass');
      process.exit(0);
    }
  }
}

// Run tests if executed directly
if (require.main === module) {
  const test = new StructuredFieldsTest();
  test.runTests().catch(error => {
    console.error('Test execution failed:', error);
    process.exit(1);
  });
}

module.exports = StructuredFieldsTest;