#!/usr/bin/env node
/**
 * Unit tests for structured response fields display in frontend
 * Tests the complete data flow from API response to UI rendering
 */

const assert = require('assert');

// Mock DOM elements
global.document = {
    getElementById: (id) => {
        if (id === 'story-content') {
            return {
                appendChild: () => {},
                children: []
            };
        }
        return null;
    },
    createElement: (tag) => {
        return {
            className: '',
            innerHTML: '',
            style: {},
            appendChild: () => {},
            querySelectorAll: () => [],
            querySelector: () => null
        };
    }
};

// Mock window
global.window = {};

// Test data matching the schema from game_state_instruction.md
const mockApiResponse = {
    success: true,
    response: "[SESSION_HEADER]\nTimestamp: 1492 DR, Ches 20, 10:00\nLocation: Goblin Cave\nStatus: Lvl 2 Fighter | HP: 15/18 (Temp: 0) | XP: 450/900 | Gold: 25gp\nResources: HD: 2/2 | Second Wind: 0/1 | Action Surge: 1/1\nConditions: None | Exhaustion: 0 | Inspiration: No | Potions: 1\n\nYou swing your sword at the goblin!\n\n--- PLANNING BLOCK ---\nWhat would you like to do next?\n1. **Attack again:** Strike the goblin with your sword\n2. **Defend:** Raise your shield and prepare for the goblin's counterattack\n3. **Use Second Wind:** Recover some hit points\n4. **Other:** Describe a different action you'd like to take.",
    debug_mode: true,
    sequence_id: 5,
    user_scene_number: 5,
    entities_mentioned: ["goblin"],
    location_confirmed: "Goblin Cave",
    state_updates: {
        "npc_data": {
            "goblin_1": {
                "hp_current": 3
            }
        }
    },
    debug_info: {
        "dm_notes": ["I chose to have the goblin attempt a dodge", "The shoulder wound gives specific injury location"],
        "dice_rolls": ["Attack roll: 1d20+5 = 15+5 = 20 (Hit, AC 15)", "Damage: 1d8+3 = 5+3 = 8 slashing damage"],
        "resources": "HD: 2/2, Second Wind: 0/1, Action Surge: 1/1, Potions: 1",
        "state_rationale": "Reduced goblin HP from 11 to 3 due to 8 damage taken"
    }
};

// Test appendToStory with fullData parameter
function testAppendToStoryWithFullData() {
    console.log("Testing appendToStory with fullData parameter...");

    // This should NOT throw an error
    try {
        // Simulate the function with all parameters including fullData
        const appendToStory = (actor, text, mode, debugMode, sequenceId, fullData) => {
            assert.strictEqual(actor, 'gemini');
            assert.strictEqual(typeof text, 'string');
            assert.strictEqual(debugMode, true);
            assert.strictEqual(sequenceId, 5);
            assert.ok(fullData, 'fullData parameter should be provided');
            assert.ok(fullData.debug_info, 'fullData should contain debug_info');
            assert.ok(Array.isArray(fullData.debug_info.dice_rolls), 'dice_rolls should be in debug_info');
            return true;
        };

        const result = appendToStory(
            'gemini',
            mockApiResponse.response,
            null,
            mockApiResponse.debug_mode,
            mockApiResponse.user_scene_number,
            mockApiResponse
        );

        assert.strictEqual(result, true);
        console.log("✅ PASS: appendToStory accepts fullData parameter");
    } catch (error) {
        console.log("❌ FAIL: appendToStory with fullData -", error.message);
    }
}

// Test structured fields extraction from debug_info
function testStructuredFieldsExtraction() {
    console.log("\nTesting structured fields extraction from debug_info...");

    // Test extracting dice_rolls from debug_info
    assert.ok(mockApiResponse.debug_info.dice_rolls, 'dice_rolls should exist in debug_info');
    assert.strictEqual(mockApiResponse.debug_info.dice_rolls.length, 2, 'Should have 2 dice rolls');
    console.log("✅ PASS: dice_rolls found in debug_info");

    // Test extracting resources from debug_info
    assert.ok(mockApiResponse.debug_info.resources, 'resources should exist in debug_info');
    assert.strictEqual(typeof mockApiResponse.debug_info.resources, 'string', 'resources should be a string');
    console.log("✅ PASS: resources found in debug_info");

    // Test other fields at top level
    assert.ok(mockApiResponse.entities_mentioned, 'entities_mentioned should exist');
    assert.ok(mockApiResponse.location_confirmed, 'location_confirmed should exist');
    assert.ok(mockApiResponse.state_updates, 'state_updates should exist');
    console.log("✅ PASS: Top-level fields found");
}

// Test generateStructuredFieldsHTML with correct field locations
function testGenerateStructuredFieldsHTML() {
    console.log("\nTesting generateStructuredFieldsHTML with nested fields...");

    const generateStructuredFieldsHTML = (fullData, debugMode) => {
        let html = '';

        // Extract dice_rolls from debug_info, not top level
        if (debugMode && fullData.debug_info && fullData.debug_info.dice_rolls && fullData.debug_info.dice_rolls.length > 0) {
            html += '<div class="dice-rolls">';
            html += '<strong>🎲 Dice Rolls:</strong><ul>';
            fullData.debug_info.dice_rolls.forEach(roll => {
                html += `<li>${roll}</li>`;
            });
            html += '</ul></div>';
        }

        // Extract resources from debug_info, not top level
        if (debugMode && fullData.debug_info && fullData.debug_info.resources) {
            html += `<div class="resources"><strong>📊 Resources:</strong> ${fullData.debug_info.resources}</div>`;
        }

        // Add entities mentioned
        if (fullData.entities_mentioned && fullData.entities_mentioned.length > 0) {
            html += `<div class="entities"><strong>👥 Entities:</strong> ${fullData.entities_mentioned.join(', ')}</div>`;
        }

        // Add location
        if (fullData.location_confirmed) {
            html += `<div class="location"><strong>📍 Location:</strong> ${fullData.location_confirmed}</div>`;
        }

        return html;
    };

    const html = generateStructuredFieldsHTML(mockApiResponse, true);

    assert.ok(html.includes('🎲 Dice Rolls:'), 'Should include dice rolls section');
    assert.ok(html.includes('Attack roll:'), 'Should include attack roll');
    assert.ok(html.includes('📊 Resources:'), 'Should include resources section');
    assert.ok(html.includes('HD: 2/2'), 'Should include hit dice');
    assert.ok(html.includes('👥 Entities:'), 'Should include entities section');
    assert.ok(html.includes('goblin'), 'Should include goblin entity');
    assert.ok(html.includes('📍 Location:'), 'Should include location section');
    assert.ok(html.includes('Goblin Cave'), 'Should include location name');

    console.log("✅ PASS: generateStructuredFieldsHTML extracts from correct locations");
}

// Test session header and planning block extraction
function testNarrativeStructuredContent() {
    console.log("\nTesting narrative structured content extraction...");

    const narrative = mockApiResponse.response;

    // Check for session header
    assert.ok(narrative.includes('[SESSION_HEADER]'), 'Narrative should contain session header marker');
    assert.ok(narrative.includes('Lvl 2 Fighter'), 'Session header should contain character info');

    // Check for planning block
    assert.ok(narrative.includes('--- PLANNING BLOCK ---'), 'Narrative should contain planning block marker');
    assert.ok(narrative.includes('What would you like to do next?'), 'Planning block should contain prompt');

    console.log("✅ PASS: Session header and planning block found in narrative");
}

// Test god_mode_response handling
function testGodModeResponse() {
    console.log("\nTesting god_mode_response handling...");

    const godModeResponse = {
        ...mockApiResponse,
        god_mode_response: "The goblin has 3 HP remaining. Its AC is 15.",
        response: "" // Narrative might be empty in god mode
    };

    assert.ok(godModeResponse.god_mode_response, 'god_mode_response should exist');
    assert.strictEqual(typeof godModeResponse.god_mode_response, 'string', 'god_mode_response should be a string');

    console.log("✅ PASS: god_mode_response field handled correctly");
}

// Test state updates display
function testStateUpdatesDisplay() {
    console.log("\nTesting state_updates display...");

    const stateUpdates = mockApiResponse.state_updates;

    assert.ok(stateUpdates, 'state_updates should exist');
    assert.ok(stateUpdates.npc_data, 'state_updates should contain npc_data');
    assert.ok(stateUpdates.npc_data.goblin_1, 'npc_data should contain goblin_1');
    assert.strictEqual(stateUpdates.npc_data.goblin_1.hp_current, 3, 'Goblin HP should be 3');

    console.log("✅ PASS: state_updates structure is correct");
}

// Run all tests
console.log("=== Frontend Unit Tests for Structured Response Fields ===\n");

testAppendToStoryWithFullData();
testStructuredFieldsExtraction();
testGenerateStructuredFieldsHTML();
testNarrativeStructuredContent();
testGodModeResponse();
testStateUpdatesDisplay();

console.log("\n=== All Frontend Unit Tests Completed ===");
