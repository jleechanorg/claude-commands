# Character Creation State Tracking Issue Scratchpad

## Problem Statement
During character creation, when a user selects a numbered option (e.g., "1" for background choice), the AI fails to:
1. Acknowledge the selection
2. Update the game state with the selection
3. Progress to the next character creation step
4. Provide feedback about what was selected

Instead, it repeats the same prompt without processing the input.

## Example from User Report
- User was at Step 6 (Background Selection) 
- Options presented: 1. Knight of the Imperium, 2. Wilds Warden, 3. Disgraced Noble
- User input: "1"
- Expected: AI acknowledges "You have chosen Knight of the Imperium..." and moves to Step 7
- Actual: AI repeated the exact same Step 6 prompt without saving the background

## Expected Behavior
According to `mechanics_system_instruction.md` line 176:
> "Single numeric inputs during these steps are selections, not story commands!"

The AI should:
1. Parse numeric input as a selection from the numbered list
2. Update STATE_UPDATES_PROPOSED to include the selection
3. Acknowledge what was chosen with flavor text
4. Progress to the next character creation step

## State Update Analysis
Current state (missing background):
```json
{
  "custom_campaign_state": {
    "character_creation": {
      "in_progress": true,
      "current_step": 6,
      "method_chosen": "custom_character",
      "selections": {
        "concept": "A knight who secretly communes with dragons.",
        "race": "Dragonborn",
        "class": "Dragon Ascendant",
        "attributes": { ... }
        // MISSING: "background": "Knight of the Imperium"
      }
    }
  }
}
```

Expected state after selection:
```json
{
  "custom_campaign_state": {
    "character_creation": {
      "in_progress": true,
      "current_step": 7,  // Should advance
      "method_chosen": "custom_character",
      "selections": {
        "concept": "A knight who secretly communes with dragons.",
        "race": "Dragonborn",
        "class": "Dragon Ascendant",
        "background": "Knight of the Imperium",  // Should be added
        "attributes": { ... }
      }
    }
  }
}
```

## Root Cause Hypotheses
1. **Input Processing Issue**: AI not recognizing numeric inputs as selections during character creation
2. **State Management**: AI not properly tracking which selections have been made
3. **Prompt Context**: AI losing context about being in character creation mode
4. **Instruction Priority**: Other instructions overriding the character creation numeric input rule

## Investigation Areas
1. Check how numeric inputs are processed differently in character creation vs story mode
2. Verify the prompt includes clear instructions about numeric selections
3. Test if the issue occurs at all character creation steps or just background
4. Check if the STATE_UPDATES_PROPOSED parsing is working correctly

## Potential Solutions

### Solution 1: Enhanced Character Creation Detection
Add explicit detection in continue_story to handle character creation mode:
```python
if current_game_state.custom_campaign_state.get('character_creation', {}).get('in_progress'):
    # Add special prompt handling for numeric inputs
```

### Solution 2: Clearer AI Instructions
Add more explicit instructions in the character creation prompt:
```
CRITICAL: During character creation, when the user provides a single number (1, 2, 3, etc.), 
this is ALWAYS a selection from the numbered options you just presented. You MUST:
1. Map the number to the corresponding option
2. Update the state with this selection
3. Acknowledge what was chosen
4. Move to the next step
```

### Solution 3: State Validation
Add validation to ensure selections are properly saved:
```python
def validate_character_creation_progress(old_state, new_state, user_input):
    # If numeric input provided, ensure a selection was added
    if user_input.strip().isdigit():
        # Verify state was updated with a new selection
```

### Solution 4: Character Creation Tests
Create comprehensive tests for the character creation flow:
- Test each step processes numeric inputs correctly
- Verify state updates include selections
- Ensure progression through all 7 steps
- Test edge cases (invalid numbers, text during creation)

## Next Steps
1. Create minimal reproduction test case
2. Add logging to trace how numeric inputs are processed
3. Review if other users have reported similar issues
4. Implement fix with appropriate solution
5. Add regression tests to prevent future issues