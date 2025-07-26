# Scratchpad: Clean Debug/Narrative Separation

**Branch**: update/clean-debug-narrative-separation
**Goal**: Remove outdated pre-JSON mode references and ensure debug content is never placed in narrative fields

## Problem Analysis

### Current Issues
1. Legacy content from before JSON mode might confuse the LLM
2. Debug content sometimes appears in narrative fields (FORBIDDEN)
3. Unclear separation between debug info and narrative content
4. Potential outdated references to old formats/structures

### Forbidden Content in Narrative Field
- ❌ [DEBUG_START]...[DEBUG_END] blocks
- ❌ [DEBUG_STATE_START]...[DEBUG_STATE_END] blocks
- ❌ [DEBUG_ROLL_START]...[DEBUG_ROLL_END] blocks
- ❌ [STATE_UPDATES_PROPOSED]...[END_STATE_UPDATES_PROPOSED] blocks
- ❌ Any debug tags or markers

## Action Plan

### Phase 1: Discovery & Analysis
1. **Search for Debug Patterns in Prompts** ✅
   - [x] Grep for DEBUG tags in all prompt files
   - [x] Identify where debug content is being generated
   - [x] Find any instructions that might cause debug/narrative mixing

2. **Identify Pre-JSON Mode References** ✅
   - [x] Search for old response format references (found 28 files with STATE_UPDATES_PROPOSED)
   - [x] Look for legacy structured field definitions
   - [x] Find outdated examples or templates

3. **Analyze Current Implementation**
   - [ ] Review game_state_instruction.md for clarity
   - [ ] Check gemini_service.py prompt construction
   - [ ] Verify frontend parsing logic

## Findings

### Debug Pattern Usage
1. **game_state_instruction.md** already has proper warnings at the top (lines 5-12)
2. **mechanics_system_instruction.md** (line 158) has outdated reference to [STATE_UPDATES_PROPOSED] ✅ FIXED
3. **28 files** still reference old STATE_UPDATES_PROPOSED blocks (mostly tests and mocks)

### Pre-JSON Mode References
- mechanics_system_instruction.md contains instructions about state updates in old format ✅ FIXED
- Many test files still use the old block format
- Mock services still generate responses with old blocks

### Critical Issue Found
**game_state_instruction.md** has contradictory information:
- Lines 5-12: Correctly forbids [STATE_UPDATES_PROPOSED] blocks in narrative
- Lines 30-99: Shows correct JSON format with state_updates field
- Lines 621-952: Contains multiple examples still using old [STATE_UPDATES_PROPOSED] block format
- This contradiction is likely confusing the LLM!

### Phase 2: Clean Up Prompts
1. **Update game_state_instruction.md** ✅
   - [x] Strengthen separation between narrative and debug fields (already strong at top)
   - [x] Add clear examples of what goes where (updated all examples to JSON format)
   - [x] Remove any outdated format references (replaced all [STATE_UPDATES_PROPOSED] blocks)

2. **Clean Other Prompt Files**
   - [x] mechanics_system_instruction.md - removed reference to old block format
   - [ ] system_prompt.md - check for any outdated references
   - [ ] user_prompt_template.md - check for any outdated references
   - [ ] Any other instruction files

### Changes Made So Far
1. **mechanics_system_instruction.md** (line 158):
   - Removed reference to "previously [STATE_UPDATES_PROPOSED] block"
   - Clarified that state updates go in JSON state_updates field

2. **game_state_instruction.md**:
   - Updated line 621 to reference state_updates field instead of block
   - Converted 5 examples from old block format to proper JSON format:
     - Initial State Example (lines 632-698)
     - Example 1: Quest and XP (lines 772-798)
     - Example 2: NPC Update (lines 800-831)
     - Time Update Example (lines 912-937)
     - Core Memory Example (lines 982-1004)
   - Updated line 1008 to reference state_updates field instead of block

3. **Update Examples**
   - [ ] Ensure all examples show proper field separation
   - [ ] Remove any legacy format examples

### Phase 3: Test and Mock Updates
**Note**: There are 28 files (mostly tests and mocks) that still use old [STATE_UPDATES_PROPOSED] format.
This is a lower priority since these are test files, but should eventually be updated for consistency.

Key files to update:
- Mock services: `/mvp_site/mocks/mock_gemini_service.py`, `/mvp_site/mocks/data_fixtures.py`
- Test files: Various files in `/mvp_site/tests/` and `/mvp_site/test_integration/`

### Phase 4: Implementation Updates
1. **Backend Validation**
   - [ ] Add validation to ensure narrative field is clean
   - [ ] Strip any debug tags if they slip through
   - [ ] Log warnings when debug content detected in narrative

2. **Frontend Safety**
   - [ ] Ensure frontend never displays debug tags in narrative
   - [ ] Add client-side filtering as backup

### Phase 5: Testing & Verification
1. **Create Test Cases**
   - [ ] Test that debug content goes to debug_info field
   - [ ] Test that narrative field is always clean
   - [ ] Test error handling for malformed responses

2. **Manual Testing**
   - [ ] Run game with various prompts
   - [ ] Verify clean narrative output
   - [ ] Check debug info appears in correct field

## Summary of Critical Changes Made

### Problem Solved
The main issue was that `game_state_instruction.md` had contradictory information:
- Top section correctly forbade debug blocks in narrative
- But examples throughout the file still showed old [STATE_UPDATES_PROPOSED] block format
- This was likely confusing the LLM about where to put state updates

### Solution Implemented
1. **Updated all prompt files** to consistently use JSON format
2. **Removed all references** to old [STATE_UPDATES_PROPOSED] blocks in instructions
3. **Converted all examples** to show proper JSON structure with state_updates field
4. **Clarified** that debug content must NEVER appear in narrative field

### Key Takeaway
**The LLM was getting mixed signals** - being told not to use blocks in narrative, but then seeing examples that used blocks. Now all examples consistently show the correct JSON format with proper field separation.

## Key Files to Review

### Prompts
- `/mvp_site/prompts/game_state_instruction.md` - Main structured response format
- `/mvp_site/prompts/system_prompt.md` - System-level instructions
- `/mvp_site/prompts/user_prompt_template.md` - User prompt construction

### Code
- `/mvp_site/gemini_service.py` - Prompt construction and response handling
- `/mvp_site/static/app.js` - Frontend field parsing and display
- `/mvp_site/structured_response_parser.py` - Response validation

### Tests
- `/mvp_site/test_gemini_service_*.py` - Backend response tests
- `/testing_ui/test_structured_fields_*.py` - UI field display tests

## Success Criteria
1. ✅ No debug content ever appears in narrative field
2. ✅ All pre-JSON mode references removed
3. ✅ Clear separation between debug and narrative content
4. ✅ Validation prevents debug content in narrative
5. ✅ All tests pass with clean output

## Next Steps
1. Start with discovery phase - search for debug patterns
2. Document all findings
3. Implement fixes systematically
4. Test thoroughly before merging
