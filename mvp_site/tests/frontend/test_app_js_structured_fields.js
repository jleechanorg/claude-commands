#!/usr/bin/env node
/**
 * Tests for actual app.js implementation of structured fields
 */

const fs = require('fs');
const path = require('path');

// Read the actual app.js file
const appJsPath = path.join(__dirname, '../../static/app.js');
const appJsContent = fs.readFileSync(appJsPath, 'utf8');

console.log("=== Testing Actual app.js Implementation ===\n");

// Test 1: Check if generateStructuredFieldsHTML exists
const hasGenerateFunction = appJsContent.includes('const generateStructuredFieldsHTML');
console.log(`generateStructuredFieldsHTML function exists: ${hasGenerateFunction ? '✅ PASS' : '❌ FAIL'}`);

// Test 2: Check if appendToStory has fullData parameter
const appendToStoryRegex = /const appendToStory = \([^)]*fullData[^)]*\)/;
const hasFullDataParam = appendToStoryRegex.test(appJsContent);
console.log(`appendToStory has fullData parameter: ${hasFullDataParam ? '✅ PASS' : '❌ FAIL'}`);

// Test 3: Check if dice_rolls is extracted from debug_info
const diceRollsFromDebugInfo = appJsContent.includes('fullData.debug_info.dice_rolls');
console.log(`Extracts dice_rolls from debug_info: ${diceRollsFromDebugInfo ? '✅ PASS' : '❌ FAIL'}`);

// Test 4: Check if resources is extracted from debug_info
const resourcesFromDebugInfo = appJsContent.includes('fullData.debug_info.resources');
console.log(`Extracts resources from debug_info: ${resourcesFromDebugInfo ? '✅ PASS' : '❌ FAIL'}`);

// Test 5: Check if interaction handler passes full data
const interactionPassesData = /appendToStory\([^,]+,[^,]+,[^,]+,[^,]+,[^,]+,\s*data\)/.test(appJsContent);
console.log(`Interaction handler passes full data: ${interactionPassesData ? '✅ PASS' : '❌ FAIL'}`);

// Test 6: Check if story loading passes entry data
const storyLoadingPassesEntry = /appendToStory\([^,]+,[^,]+,[^,]+,[^,]+,[^,]+,\s*entry\)/.test(appJsContent);
console.log(`Story loading passes entry data: ${storyLoadingPassesEntry ? '✅ PASS' : '❌ FAIL'}`);

// Summary
const allTests = [
    hasGenerateFunction,
    hasFullDataParam,
    diceRollsFromDebugInfo,
    resourcesFromDebugInfo,
    interactionPassesData,
    storyLoadingPassesEntry
];

const passed = allTests.filter(t => t).length;
const total = allTests.length;

console.log(`\n=== Summary: ${passed}/${total} tests passed ===`);

if (passed < total) {
    console.log("\n❌ Implementation incomplete - some tests failed");
    process.exit(1);
} else {
    console.log("\n✅ All implementation tests passed!");
}