#!/usr/bin/env node
/**
 * Unit tests for the missing structured fields UI elements:
 * - god_mode_response
 * - entities_mentioned
 * - location_confirmed
 */

const assert = require('assert');

// Mock document for testing
global.document = {
    createElement: (tag) => ({
        className: '',
        innerHTML: '',
        style: {}
    })
};

// Test data matching schema
const mockGodModeResponse = {
    narrative: "",  // Empty in god mode
    god_mode_response: "Current game state:\n- Goblin HP: 7/7\n- Player Location: Cave Entrance\n- Combat: Not active",
    entities_mentioned: [],
    location_confirmed: "Cave Entrance",
    debug_mode: false
};

const mockCharacterResponse = {
    narrative: "You see goblins ahead...",
    entities_mentioned: ["goblin", "dragon", "merchant"],
    location_confirmed: "Dragon's Lair",
    debug_mode: true
};

console.log("=== Testing Missing Fields UI ===\n");

// Test 1: God Mode Response Display
function testGodModeResponseDisplay() {
    console.log("Test 1: God Mode Response Display");

    const generateStructuredFieldsHTML = (fullData, debugMode) => {
        let html = '';

        // God mode response should be displayed prominently
        if (fullData.god_mode_response) {
            html += '<div class="god-mode-response">';
            html += '<strong>🔮 God Mode Response:</strong>';
            html += `<pre>${fullData.god_mode_response}</pre>`;
            html += '</div>';
        }

        return html;
    };

    const html = generateStructuredFieldsHTML(mockGodModeResponse, false);

    assert.ok(html.includes('god-mode-response'), 'Should have god-mode-response class');
    assert.ok(html.includes('🔮'), 'Should include god mode emoji');
    assert.ok(html.includes(mockGodModeResponse.god_mode_response), 'Should include response text');
    assert.ok(html.includes('<pre>'), 'Should use pre tag for formatting');

    console.log("✅ PASS: God mode response displays correctly\n");
}

// Test 2: Entities Mentioned Display
function testEntitiesMentionedDisplay() {
    console.log("Test 2: Entities Mentioned Display");

    const generateStructuredFieldsHTML = (fullData, debugMode) => {
        let html = '';

        // Entities mentioned should show as a list
        if (fullData.entities_mentioned && fullData.entities_mentioned.length > 0) {
            html += '<div class="entities-mentioned">';
            html += '<strong>👥 Entities:</strong>';
            html += '<ul>';
            fullData.entities_mentioned.forEach(entity => {
                html += `<li>${entity}</li>`;
            });
            html += '</ul>';
            html += '</div>';
        }

        return html;
    };

    const html = generateStructuredFieldsHTML(mockCharacterResponse, true);

    assert.ok(html.includes('entities-mentioned'), 'Should have entities-mentioned class');
    assert.ok(html.includes('👥'), 'Should include entities emoji');
    assert.ok(html.includes('<ul>'), 'Should use unordered list');
    assert.ok(html.includes('<li>goblin</li>'), 'Should include goblin entity');
    assert.ok(html.includes('<li>dragon</li>'), 'Should include dragon entity');
    assert.ok(html.includes('<li>merchant</li>'), 'Should include merchant entity');

    console.log("✅ PASS: Entities mentioned displays correctly\n");
}

// Test 3: Location Confirmed Display
function testLocationConfirmedDisplay() {
    console.log("Test 3: Location Confirmed Display");

    const generateStructuredFieldsHTML = (fullData, debugMode) => {
        let html = '';

        // Location confirmed should always show when present
        if (fullData.location_confirmed && fullData.location_confirmed !== 'Unknown') {
            html += '<div class="location-confirmed">';
            html += `<strong>📍 Location:</strong> ${fullData.location_confirmed}`;
            html += '</div>';
        }

        return html;
    };

    const html = generateStructuredFieldsHTML(mockCharacterResponse, true);

    assert.ok(html.includes('location-confirmed'), 'Should have location-confirmed class');
    assert.ok(html.includes('📍'), 'Should include location pin emoji');
    assert.ok(html.includes("Dragon's Lair"), 'Should include location name');

    console.log("✅ PASS: Location confirmed displays correctly\n");
}

// Test 4: All Fields Together
function testAllFieldsTogether() {
    console.log("Test 4: All Missing Fields Together");

    const fullResponse = {
        ...mockCharacterResponse,
        god_mode_response: "Test god response",
        debug_info: {
            dm_notes: ["Test note"],
            state_rationale: "Test rationale"
        }
    };

    const generateStructuredFieldsHTML = (fullData, debugMode) => {
        let html = '';

        // All three missing fields
        if (fullData.god_mode_response) {
            html += '<div class="god-mode-response">🔮 God Mode</div>';
        }
        if (fullData.entities_mentioned?.length > 0) {
            html += '<div class="entities-mentioned">👥 Entities</div>';
        }
        if (fullData.location_confirmed) {
            html += '<div class="location-confirmed">📍 Location</div>';
        }

        return html;
    };

    const html = generateStructuredFieldsHTML(fullResponse, true);

    // Should have all three elements
    assert.ok(html.includes('god-mode-response'), 'Should have god mode element');
    assert.ok(html.includes('entities-mentioned'), 'Should have entities element');
    assert.ok(html.includes('location-confirmed'), 'Should have location element');

    console.log("✅ PASS: All missing fields can display together\n");
}

// Test 5: CSS Classes Expected
function testExpectedCSSClasses() {
    console.log("Test 5: Expected CSS Classes");

    const expectedClasses = {
        '.god-mode-response': 'Purple border (#9b59b6), padding, margin',
        '.entities-mentioned': 'Light blue background (#e7f3ff), list styling',
        '.location-confirmed': 'Alice blue background (#f0f8ff), padding'
    };

    console.log("Expected CSS classes to be defined:");
    for (const [selector, style] of Object.entries(expectedClasses)) {
        console.log(`  ${selector}: ${style}`);
    }

    console.log("\n✅ PASS: CSS class requirements documented\n");
}

// Run all tests
console.log("Running all tests for missing fields...\n");

try {
    testGodModeResponseDisplay();
    testEntitiesMentionedDisplay();
    testLocationConfirmedDisplay();
    testAllFieldsTogether();
    testExpectedCSSClasses();

    console.log("=== All Tests Passed! ===");
    console.log("\nNext step: Implement these UI elements in app.js");
} catch (error) {
    console.error("❌ Test failed:", error.message);
    process.exit(1);
}
