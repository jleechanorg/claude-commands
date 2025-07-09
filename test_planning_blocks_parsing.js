#!/usr/bin/env node
/**
 * Test script to demonstrate planning block parsing functionality
 */

// The parsePlanningBlocks function from app.js
const parsePlanningBlocks = (text) => {
    // Pattern to match choice format: **[ActionWord_Number]:** Description
    const choicePattern = /\*\*\[([^\]]+)\]:\*\*\s*([^*\n]+(?:\n(?!\*\*\[)[^\n]*)*)/g;
    
    // Find all choices in the text
    const choices = [];
    let match;
    while ((match = choicePattern.exec(text)) !== null) {
        choices.push({
            id: match[1],
            fullText: match[0],
            description: match[2].trim()
        });
    }
    
    // If we found choices, create a planning block section
    if (choices.length > 0) {
        // Find where the choices start in the text
        const firstChoiceIndex = text.indexOf(choices[0].fullText);
        const narrativeText = text.substring(0, firstChoiceIndex).trim();
        
        // Create the choice buttons HTML
        let choicesHtml = '<div class="planning-block-choices">';
        choices.forEach(choice => {
            // Escape the choice text for HTML attribute
            const escapedText = `${choice.id}: ${choice.description}`.replace(/"/g, '&quot;');
            choicesHtml += `
                <button class="choice-button" data-choice-id="${choice.id}" data-choice-text="${escapedText}">
                    <span class="choice-id">[${choice.id}]</span>
                    <span class="choice-description">${choice.description}</span>
                </button>
            `;
        });
        choicesHtml += '</div>';
        
        // Return narrative text followed by choice buttons
        return {
            narrative: narrativeText,
            choicesHtml: choicesHtml,
            choices: choices
        };
    }
    
    // No choices found, return text as-is
    return {
        narrative: text,
        choicesHtml: '',
        choices: []
    };
};

// Test cases
console.log("🧪 Testing Planning Block Parsing\n");

// Test 1: Standard planning block
console.log("Test 1: Standard Planning Block");
console.log("================================");
const test1 = `The goblin chieftain snarls at your approach, his yellowed tusks gleaming in the torchlight. 
His warriors shift nervously, hands on their crude weapons. 

**What do you do?**

**[Action_1]:** Draw your sword and charge the chieftain directly, hoping to end this quickly.

**[Continue_1]:** Try to negotiate with the chieftain, offering gold for safe passage.

**[Explore_2]:** Look for an alternate route around the goblin encampment.`;

const result1 = parsePlanningBlocks(test1);
console.log("Narrative:", result1.narrative.substring(0, 50) + "...");
console.log("Choices found:", result1.choices.length);
result1.choices.forEach(choice => {
    console.log(`  - [${choice.id}]: ${choice.description.substring(0, 40)}...`);
});
console.log("\n");

// Test 2: Deep think block with pros/cons
console.log("Test 2: Deep Think Block with Pros/Cons");
console.log("=======================================");
const test2 = `You stand at a moral crossroads. The village elder offers you a substantial reward to retrieve a stolen artifact, 
but you've discovered the "thief" is actually the artifact's rightful owner.

**[Option_1]:** Return the artifact to the elder and claim your reward.
- *Pros:* Substantial gold reward, favor with the village, completed quest
- *Cons:* Moral compromise, potential karma loss, perpetuating injustice

**[Option_2]:** Side with the rightful owner and protect them from the elder.
- *Pros:* Moral integrity maintained, potential new ally, hidden quest line
- *Cons:* Village hostility, loss of reward, powerful enemy made

**[Option_3]:** Attempt to broker a compromise between both parties.
- *Pros:* Potential peaceful resolution, maintain neutrality, wisdom gain
- *Cons:* May satisfy neither party, reduced rewards, complex negotiations`;

const result2 = parsePlanningBlocks(test2);
console.log("Choices found:", result2.choices.length);
result2.choices.forEach(choice => {
    console.log(`  - [${choice.id}]: ${choice.description.substring(0, 40)}...`);
});
console.log("\n");

// Test 3: Special characters
console.log("Test 3: Special Characters Handling");
console.log("===================================");
const test3 = `The merchant grins widely as you approach his stall.

**[Talk_1]:** Say "Hello there, friend!" to the stranger.

**[Examine_1]:** Look at the merchant's "special" wares.

**[Leave_1]:** Walk away from the merchant's stall.`;

const result3 = parsePlanningBlocks(test3);
console.log("Choices with special characters:");
result3.choices.forEach(choice => {
    const escapedText = `${choice.id}: ${choice.description}`.replace(/"/g, '&quot;');
    console.log(`  - Original: ${choice.id}: ${choice.description}`);
    console.log(`    Escaped: ${escapedText}`);
});
console.log("\n");

// Test 4: No planning block
console.log("Test 4: Text Without Planning Block");
console.log("===================================");
const test4 = `You enter the tavern and the warmth of the fireplace washes over you. 
The barkeep nods in your direction while wiping down a mug. 
Several patrons are scattered throughout the common room, engaged in quiet conversation.`;

const result4 = parsePlanningBlocks(test4);
console.log("Choices found:", result4.choices.length);
console.log("Text returned as-is:", result4.narrative.substring(0, 50) + "...");

console.log("\n✅ All parsing tests completed!");