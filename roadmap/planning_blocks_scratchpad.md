# Planning Blocks Issue Scratchpad

## Problem
Looking at the campaign output, I can see that planning blocks are missing. The AI is directly generating story content without showing the planning phase that should precede it.

## Expected Behavior
Based on the game flow, there should be planning blocks before story generation that show:
1. Campaign initialization planning
2. Character creation planning
3. Story beat planning

## Current Output Analysis
The campaign shows:
- Direct story output without preceding planning blocks
- Character creation steps are working correctly
- State updates are being proposed correctly
- But no PLANNING: blocks are visible

## Hypothesis
The planning blocks might be:
1. Not being generated at all
2. Being generated but not displayed
3. Being skipped due to a configuration issue
4. Missing from the prompts/mechanics

## Investigation Areas
1. Check campaign initialization mechanics ✓
2. Review story generation prompts ✓
3. Look for planning-related prompts/mechanics ✓
4. Check if planning is toggled off somewhere ✓

## Findings
1. Planning blocks ARE defined in narrative_system_instruction.md
2. The instructions ARE being loaded correctly when narrative is selected
3. The critical instruction states: "🔥 CRITICAL: EVERY STORY MODE RESPONSE MUST END WITH A PLANNING BLOCK! 🔥"
4. No configuration disables planning blocks - they should always appear
5. The AI (Gemini) is not following the instructions properly

## Root Cause
The issue is NOT with the code or loading - it's with AI compliance. The AI is receiving the instructions but not following them consistently.

## Possible Solutions
1. Add explicit enforcement in the prompt builder ✓
2. Move planning block instructions earlier in the prompt order
3. Add a reminder at the end of each user prompt ✓
4. Validate AI responses and re-prompt if planning blocks are missing ✓

## Implementation
Implemented a comprehensive fix with the following components:

### 1. Planning Block Validation Function
- Added `_validate_and_enforce_planning_block()` in gemini_service.py
- Automatically detects missing planning blocks and adds them
- Context-aware: adds deep think blocks for think/plan keywords

### 2. Integration Points
- Modified `continue_story()` to validate all story mode responses
- Enhanced `_get_current_turn_prompt()` to add explicit reminders
- Added `build_continuation_reminder()` to PromptBuilder for system instructions

### 3. Testing
- Created comprehensive test suite in tests/test_planning_block_enforcement.py
- Tests various scenarios including existing blocks, missing blocks, think commands

### 4. Key Features
- Automatic enforcement if AI forgets
- Context-aware planning blocks
- Non-intrusive for existing blocks
- Consistent formatting

## Additional Issue: Character Creation State Tracking

### Problem
During character creation, when user selects "1" for background choice, the AI:
- Does not acknowledge the selection ("You have chosen Knight of the Imperium...")
- Does not update state to include `"background": "Knight of the Imperium"`
- Does not progress to next step (Step 7)
- Simply repeats the same Step 6 prompt

### Expected Behavior
According to mechanics_system_instruction.md line 176: "Single numeric inputs during these steps are selections, not story commands!"

The AI should:
1. Acknowledge the choice: "You have chosen Knight of the Imperium..."
2. Update STATE_UPDATES_PROPOSED to include the background selection
3. Progress to the next character creation step
4. Provide feedback about what it did with the input

### Possible Solutions
1. **Add explicit character creation input handling**
   - Create specific prompt reminders for processing numeric selections
   - Emphasize that numeric inputs map to the numbered options presented

2. **Enhance character creation state tracking**
   - Add validation to ensure selections are saved before progressing
   - Create clearer examples of how to update state with each selection

3. **Add character creation context to prompts**
   - Detect when in character creation mode
   - Add specific instructions for handling selections vs story commands

4. **Create character creation tests**
   - Test that numeric inputs update state correctly
   - Verify progression through all 7 steps
   - Ensure all selections are tracked (race, class, background, etc.)

### Root Cause Analysis
The AI appears to be:
- Not recognizing numeric input as a selection during character creation
- Not mapping "1" to the first background option
- Missing the context that it should process and move forward
- Possibly treating the input as invalid and re-presenting options

## Critical Bug: Planning Blocks in God Mode

### Problem
User reported getting a planning block when replying "god mode", which should switch to MODE_GOD where planning blocks should NOT appear.

Worse, the planning block was from a completely different campaign:
- Mentioned "war council", "the Imperium", "your children, Cassian, Valerius, and Sariel"
- User was playing as "Sir Braddock" on a dragon hunt
- AI even acknowledged the error but still included the wrong block

### Issues Identified
1. **Planning blocks appearing in god mode** - Should only appear in MODE_CHARACTER
2. **Cross-campaign contamination** - Planning blocks from other campaigns bleeding through
3. **LLM context confusion** - AI generating planning blocks from wrong context

### Immediate Fix Needed
The planning block validation needs to check the mode AFTER processing the user input, not before:
```python
# Current (wrong): checks mode from previous state
if mode == constants.MODE_CHARACTER:
    response_text = _validate_and_enforce_planning_block(...)

# Should be: check if response indicates we're still in character mode
# Or better: don't generate planning blocks if user said "god mode"
```

### AI's Self-Analysis of the Bug
The AI provided 10 reasons for the contamination:
1. **Contextual Shift** - Wrong character context (Alexiel vs Sir Braddock)
2. **Instruction Fatigue** - Too many instructions causing bleed-through
3. **Template Over-application** - Grabbed wrong character's options
4. **Mis-weighted Tags** - Prioritized wrong character's progress
5. **Lack of Negative Constraints** - No filtering of irrelevant options
6. **Best Guess Fallback** - Defaulted to wrong character's options
7. **Over-Generalization** - High-level concerns vs immediate actions
8. **Internal State Contradiction** - Tier mismatch (Tier 3/4 vs Tier 1)
9. **Debug Trace Interference** - Processing overhead causing shifts
10. **Cached Response Collision** - Previous responses bleeding through

## Comprehensive Fix Plan

### 1. Mode Detection Fix
```python
def _validate_and_enforce_planning_block(response_text, user_input, game_state, chosen_model, system_instruction):
    # Check if user is switching to god/dm mode
    if any(phrase in user_input.lower() for phrase in ['god mode', 'dm mode', 'gm mode']):
        logging.info("User switching to god/dm mode - skipping planning block")
        return response_text

    # Check if AI response indicates mode switch
    if "[Mode: DM MODE]" in response_text or "[Mode: GOD MODE]" in response_text:
        logging.info("Response indicates mode switch - skipping planning block")
        return response_text

    # Existing character creation check...
    # Continue with planning block enforcement...
```

### 2. Context Isolation for Planning Blocks
When generating planning blocks, include ONLY current character context:
```python
planning_prompt = f"""
GENERATE PLANNING BLOCK FOR CURRENT CHARACTER ONLY:
Character: {game_state.player_character_data.get('name', 'Player Character')}
Current Location: {game_state.world_data.get('current_location_name', 'Unknown')}
Current Situation: {response_text[-500:]}

DO NOT reference other characters, campaigns, or unrelated narrative elements.
Focus ONLY on immediate tactical options for THIS character in THIS situation.
"""
```

### 3. Add Validation for Generated Planning Blocks
Check that generated planning blocks don't contain unrelated elements:
```python
def validate_planning_block_relevance(planning_block, game_state):
    # Check for character names not in current campaign
    # Check for locations not in current world_data
    # Check for narrative elements not in recent context
    pass
```

### 4. Test Cases Needed
- Test mode switching ("god mode" input)
- Test planning block isolation (no cross-campaign bleed)
- Test tier-appropriate options (Tier 1 vs Tier 4)
- Test context relevance validation
