#!/usr/bin/env node
/**
 * Test the updated planning block parsing with actual game format
 */

// Updated parsePlanningBlocks function
const parsePlanningBlocks = (text) => {
    // Pattern to match choice format: **[ActionWord_Number]:** Description OR numbered format: 1. **Action:** Description
    const bracketPattern = /\*\*\[([^\]]+)\]:\*\*\s*([^*\n]+(?:\n(?!\*\*\[)[^\n]*)*)/g;
    const numberedPattern = /^\d+\.\s*\*\*([^:]+):\*\*\s*(.+?)(?=^\d+\.|$)/gm;
    
    // Find all choices in the text
    const choices = [];
    let match;
    
    // First try bracket pattern: **[Action_1]:** Description
    while ((match = bracketPattern.exec(text)) !== null) {
        choices.push({
            id: match[1],
            fullText: match[0],
            description: match[2].trim()
        });
    }
    
    // If no bracket pattern found, try numbered pattern: 1. **Action:** Description
    if (choices.length === 0) {
        while ((match = numberedPattern.exec(text)) !== null) {
            choices.push({
                id: match[1].trim(),
                fullText: match[0],
                description: match[2].trim()
            });
        }
    }
    
    return choices;
};

// Test with actual game format from screenshot
const actualGameText = `He notices a city guard standing nearby, a stalwart figure in polished steel armor. His posture is attentive, his gaze sweeping across the crowd. A wave of thoughts washes over him: Should he enter the city and start exploring? Should he speak with this guard to learn more about the city? Or should he find shelter first and assess his plan?

He decides to follow his instincts, choosing to explore first. After a moment, he strides confidently toward the gates, his footsteps echoing on the cobblestones.

--- PLANNING BLOCK ---
What will you do?
1. **Enter Porthaven:** Step through the city gates and begin exploring the city's bustling streets and alleyways.
2. **Talk to the Guard:** Approach the guard and inquire about safe places to stay, and any immediate dangers to be aware of.
3. **Find an Inn:** Head directly towards the closest inn to find lodging and rest before venturing into the city's unknown corners.
4. **Other:** Describe another action you'd like to take.`;

console.log("🧪 Testing with actual game format\n");
console.log("Input text includes planning block in numbered format");

const choices = parsePlanningBlocks(actualGameText);
console.log(`\nFound ${choices.length} choices:`);
choices.forEach((choice, i) => {
    console.log(`${i+1}. ID: "${choice.id}"`);
    console.log(`   Description: "${choice.description}"`);
    console.log(`   Full text: "${choice.fullText.substring(0, 50)}..."`);
});

// Test if planning block section can be identified
const planningBlockIndex = actualGameText.indexOf('--- PLANNING BLOCK ---');
if (planningBlockIndex >= 0) {
    console.log(`\n✅ Planning block marker found at position ${planningBlockIndex}`);
}