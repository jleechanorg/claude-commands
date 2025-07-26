/**
 * Unit tests for frontend JSON planning block processing.
 * Tests the new parsePlanningBlocks function with structured JSON input.
 *
 * RED PHASE: These tests will FAIL initially and drive the frontend implementation.
 */

// Mock planning block data for testing
const mockPlanningBlockJson = {
    thinking: "The player approaches a mysterious door. Multiple options available.",
    context: "The door appears ancient and might be trapped.",
    choices: {
        examine_door: {
            text: "Examine Door",
            description: "Look carefully for traps or mechanisms",
            risk_level: "low"
        },
        open_directly: {
            text: "Open Directly",
            description: "Push the door open immediately",
            risk_level: "medium"
        },
        search_for_key: {
            text: "Search for Key",
            description: "Look around for a key or alternative entrance",
            risk_level: "safe"
        },
        cast_unlock_spell: {
            text: "Cast Unlock Spell",
            description: "Use magic to bypass the lock",
            risk_level: "high"
        }
    }
};

const mockEmptyChoicesPlanningBlock = {
    thinking: "The player rests and considers their options.",
    context: "This is a narrative moment with no immediate choices.",
    choices: {}
};

const mockXssPlanningBlock = {
    thinking: "Testing XSS prevention in choice text",
    choices: {
        xss_test: {
            text: "<script>alert('xss')</script>Examine Door",
            description: "Look for traps & mechanisms < > \" '",
            risk_level: "low"
        }
    }
};

const mockUnicodePlanningBlock = {
    thinking: "Testing unicode support 🧙‍♂️✨",
    choices: {
        magic_spell: {
            text: "Cast Spell 🔮",
            description: "Use magical powers ✨ to open the door 🚪",
            risk_level: "medium"
        },
        chinese_option: {
            text: "检查门",  // "Examine door" in Chinese
            description: "仔细查看是否有陷阱",  // "Look carefully for traps"
            risk_level: "low"
        }
    }
};

// Test runner function
function runPlanningBlockJsonTests() {
    const results = [];

    console.log('🧪 Running Frontend Planning Block JSON Tests');
    console.log('=' .repeat(60));

    // Test 1: JSON object processing
    try {
        console.log('Test 1: JSON object processing...');
        const result = parsePlanningBlocks(mockPlanningBlockJson);

        if (typeof result !== 'string') {
            throw new Error('parsePlanningBlocks should return a string');
        }

        if (!result.includes('planning-block-choices')) {
            throw new Error('Result should contain planning-block-choices div');
        }

        if (!result.includes('examine_door')) {
            throw new Error('Result should contain examine_door choice');
        }

        if (!result.includes('Examine Door')) {
            throw new Error('Result should contain "Examine Door" text');
        }

        if (!result.includes('Look carefully for traps')) {
            throw new Error('Result should contain choice description');
        }

        console.log('✅ Test 1 PASSED');
        results.push({ name: 'JSON object processing', passed: true });
    } catch (error) {
        console.log(`❌ Test 1 FAILED: ${error.message}`);
        results.push({ name: 'JSON object processing', passed: false, error: error.message });
    }

    // Test 2: Choice button attributes
    try {
        console.log('Test 2: Choice button attributes...');
        const result = parsePlanningBlocks(mockPlanningBlockJson);

        if (!result.includes('data-choice-id="examine_door"')) {
            throw new Error('Should contain data-choice-id attribute for examine_door');
        }

        if (!result.includes('data-choice-text="')) {
            throw new Error('Should contain data-choice-text attribute');
        }

        if (!result.includes('class="choice-button"')) {
            throw new Error('Should contain choice-button class');
        }

        console.log('✅ Test 2 PASSED');
        results.push({ name: 'Choice button attributes', passed: true });
    } catch (error) {
        console.log(`❌ Test 2 FAILED: ${error.message}`);
        results.push({ name: 'Choice button attributes', passed: false, error: error.message });
    }

    // Test 3: Empty choices handling
    try {
        console.log('Test 3: Empty choices handling...');
        const result = parsePlanningBlocks(mockEmptyChoicesPlanningBlock);

        // Should return thinking text but no choice buttons
        if (!result.includes('The player rests')) {
            throw new Error('Should include thinking text');
        }

        if (result.includes('choice-button')) {
            throw new Error('Should not contain choice buttons for empty choices');
        }

        console.log('✅ Test 3 PASSED');
        results.push({ name: 'Empty choices handling', passed: true });
    } catch (error) {
        console.log(`❌ Test 3 FAILED: ${error.message}`);
        results.push({ name: 'Empty choices handling', passed: false, error: error.message });
    }

    // Test 4: XSS prevention
    try {
        console.log('Test 4: XSS prevention...');
        const result = parsePlanningBlocks(mockXssPlanningBlock);

        // Should not contain raw script tags
        if (result.includes('<script>')) {
            throw new Error('Should not contain raw script tags');
        }

        // Should escape HTML entities
        if (!result.includes('&lt;script&gt;') && !result.includes('&amp;lt;script&amp;gt;')) {
            throw new Error('Should contain escaped script tags');
        }

        console.log('✅ Test 4 PASSED');
        results.push({ name: 'XSS prevention', passed: true });
    } catch (error) {
        console.log(`❌ Test 4 FAILED: ${error.message}`);
        results.push({ name: 'XSS prevention', passed: false, error: error.message });
    }

    // Test 5: Unicode support
    try {
        console.log('Test 5: Unicode support...');
        const result = parsePlanningBlocks(mockUnicodePlanningBlock);

        if (!result.includes('🔮')) {
            throw new Error('Should preserve emoji characters');
        }

        if (!result.includes('检查门')) {
            throw new Error('Should preserve Chinese characters');
        }

        console.log('✅ Test 5 PASSED');
        results.push({ name: 'Unicode support', passed: true });
    } catch (error) {
        console.log(`❌ Test 5 FAILED: ${error.message}`);
        results.push({ name: 'Unicode support', passed: false, error: error.message });
    }

    // Test 6: Thinking text extraction
    try {
        console.log('Test 6: Thinking text extraction...');
        const result = parsePlanningBlocks(mockPlanningBlockJson);

        if (!result.includes('mysterious door')) {
            throw new Error('Should include thinking text content');
        }

        console.log('✅ Test 6 PASSED');
        results.push({ name: 'Thinking text extraction', passed: true });
    } catch (error) {
        console.log(`❌ Test 6 FAILED: ${error.message}`);
        results.push({ name: 'Thinking text extraction', passed: false, error: error.message });
    }

    // Test 7: Legacy string format compatibility
    try {
        console.log('Test 7: Legacy string format compatibility...');
        const legacyString = `What would you like to do?
1. **ExamineDoor** - Look at the door carefully
2. **OpenDirectly** - Push the door open`;

        const result = parsePlanningBlocks(legacyString);

        if (!result.includes('choice-button')) {
            throw new Error('Should still process legacy string format');
        }

        if (!result.includes('ExamineDoor')) {
            throw new Error('Should extract choice IDs from legacy format');
        }

        console.log('✅ Test 7 PASSED');
        results.push({ name: 'Legacy string format compatibility', passed: true });
    } catch (error) {
        console.log(`❌ Test 7 FAILED: ${error.message}`);
        results.push({ name: 'Legacy string format compatibility', passed: false, error: error.message });
    }

    // Summary
    console.log('\n' + '=' .repeat(60));
    console.log('TEST SUMMARY');
    console.log('=' .repeat(60));

    const passed = results.filter(r => r.passed).length;
    const failed = results.filter(r => !r.passed).length;

    console.log(`Total Tests: ${results.length}`);
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`Success Rate: ${(passed/results.length*100).toFixed(1)}%`);

    if (failed > 0) {
        console.log('\nFAILED TESTS:');
        results.filter(r => !r.passed).forEach(result => {
            console.log(`   ❌ ${result.name}: ${result.error}`);
        });
    }

    console.log('\n🧪 Frontend JSON Planning Block Tests Complete');

    return { passed, failed, results };
}

// Auto-run tests if parsePlanningBlocks function exists
if (typeof parsePlanningBlocks === 'function') {
    document.addEventListener('DOMContentLoaded', () => {
        // Add a small delay to ensure all JS is loaded
        setTimeout(runPlanningBlockJsonTests, 100);
    });
} else {
    console.warn('parsePlanningBlocks function not found - tests cannot run');
}
