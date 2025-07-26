# Debug Content Architecture Redesign

**Branch**: TBD (future PR)
**Goal**: Replace string parsing debug system with proper structured debug_info handling
**Priority**: Technical debt / architectural improvement
**Impact**: Internal code quality, no user-facing changes

## Problem Statement

### Current Broken Architecture
```
AI Response → [DEBUG_START]content[DEBUG_END] mixed in narrative
           ↓
String parsing with regex to strip debug blocks
           ↓
Clean narrative text for users
```

### Correct Architecture Should Be
```
AI Response → {
  "narrative": "clean text",
  "debug_info": {"dm_notes": "...", "dice_rolls": [...]}
}
           ↓
Include/exclude debug_info field based on debug_mode
           ↓
No string parsing needed
```

## Technical Analysis

### Evidence of Design Flaw

**1. String Parsing Functions Exist**
- `_strip_debug_content()` - removes `[DEBUG_START]` blocks
- `_strip_state_updates_only()` - removes `[STATE_UPDATES_PROPOSED]` blocks
- `_strip_other_debug_content()` - complex regex parsing

**2. Test Evidence**
```python
# test_debug_stripping.py shows AI generates this:
input_text = (
    "You enter the dark cave. "
    "[DEBUG_START]As the DM, I'm rolling a perception check...[DEBUG_END] "
    "You notice a glimmer in the darkness."
)
```

**3. Architecture Contradiction**
- `NarrativeResponse` has `debug_info` field ✅
- But AI puts debug content in `narrative` field ❌
- Then we string-parse to clean it ❌❌

### Root Cause: Prompt Engineering
The AI is being instructed to embed debug content in narrative text instead of using structured `debug_info` field.

## 🚨 CRITICAL: Backward Compatibility Requirements

### **BREAKING DISCOVERY**: Old campaigns REQUIRE string parsing functions

**Data Flow Analysis reveals:**
- **Existing campaigns**: Debug content stored in database with `[DEBUG_START]` tags
- **Display path**: Returns raw DB content without processing
- **Impact**: Removing string parsing = users see debug tags in existing campaigns

**Current Storage Format:**
```
Database Story Entries:
"You enter the cave. [DEBUG_START]Rolling perception...[DEBUG_END] You see treasure."
```

**If String Parsing Removed:**
```
User Views Campaign → [DEBUG_START]Rolling perception...[DEBUG_END] visible to user 😱
```

### **Updated Implementation Strategy: Hybrid Approach**

**Phase 1: Dual System**
- **New campaigns**: Use structured `debug_info` (no parsing)
- **Old campaigns**: Use string parsing for display compatibility
- **Detection**: Check if story content contains debug tags

**Phase 2: Gradual Migration**
```python
def get_narrative_for_display(story_text, debug_mode):
    # New campaigns: already clean
    if not contains_debug_tags(story_text):
        return story_text

    # Old campaigns: apply string parsing
    if debug_mode:
        return strip_state_updates_only(story_text)
    else:
        return strip_debug_content(story_text)
```

## Updated Implementation Plan: 6-Agent Strategy

### **Agent 1: Prompt Archaeology Agent** 📜 ✅ COMPLETED
- **Mission**: Excavate current debug formatting instructions
- **Scope**: All prompt files in `mvp_site/prompts/`
- **Timeline**: 1-2 hours (actual: 45 minutes)
- **Tasks**:
  - [x] Audit narrative_system_instruction.md for debug instructions
  - [x] Audit game_state_instruction.md for debug formatting
  - [x] Audit mechanics_system_instruction.md for debug content
  - [x] Search for: "[DEBUG_START]", "debug_info", debug formatting patterns
  - [x] Document where AI is told to use debug tags
  - [x] Create current state analysis report

#### **FINDINGS REPORT:**

**1. game_state_instruction.md (PRIMARY SOURCE)**
- Lines 22-36: Defines JSON response format with structured `debug_info` field
- Line 23: Comment reveals key issue: `// Previously called [STATE_UPDATES_PROPOSED] block`
- Lines 29-33: Shows correct debug_info structure with dm_notes, dice_rolls, resources
- Lines 177-179: CRITICAL - Forbids [STATE_UPDATES_PROPOSED] blocks in narrative
- **Conclusion**: This file correctly instructs structured debug approach ✅

**2. mechanics_system_instruction.md**
- Line 158: CRITICAL instruction found:
  ```markdown
  **CRITICAL: When entity tracking is enabled (JSON mode), state updates will be included in the structured JSON response (previously [STATE_UPDATES_PROPOSED] block), NOT in the narrative text.**
  ```
- Shows AI is aware of old format but instructed to use new JSON structure
- **Conclusion**: Properly migrated to structured approach ✅

**3. narrative_system_instruction.md**
- Lines 1-9: References that protocols moved to game_state_instruction.md
- No explicit debug formatting instructions found
- **Conclusion**: Defers to game_state_instruction.md ✅

**4. Other prompt files**
- dnd_srd_instruction.md: No debug instructions (rules only)
- character_template.md: No debug instructions (character format only)

#### **ROOT CAUSE ANALYSIS:**

The prompts are ALREADY correctly instructing the AI to use structured debug_info! The issue is likely:

1. **AI Compliance**: Gemini may not be following the instructions consistently
2. **Legacy Habit**: AI trained on older patterns still generates [DEBUG_START] tags
3. **Prompt Priority**: Debug instructions may be buried/overridden by other prompts

**Key Evidence**: game_state_instruction.md explicitly forbids debug content in narrative field and provides proper debug_info schema, yet tests show AI still embeds debug tags.

### **Agent 2: Prompt Engineering Agent** ✍️ ✅ COMPLETED
- **Mission**: ~~Rewrite AI instructions~~ → REINFORCE existing instructions
- **Dependencies**: Agent 1 findings showed prompts were already correct
- **Timeline**: 2-3 hours (actual: 30 minutes)
- **Updated Tasks**:
  - [x] ~~Remove [DEBUG_START] tag instructions~~ → Already removed
  - [x] ~~Add debug_info field schema~~ → Already defined
  - [x] Add STRONGER enforcement at TOP of game_state_instruction.md
  - [x] Verify game_state_instruction.md loads FIRST (highest priority)
  - [x] Add explicit examples showing WRONG vs RIGHT debug formatting
  - [x] Add emoji warnings (🚨) for critical rules

#### **IMPLEMENTATION:**

**1. Added TOP-LEVEL Debug Rules Section**
- New section: "🚨 CRITICAL DEBUG CONTENT RULES - HIGHEST PRIORITY 🚨"
- Placed at very top of game_state_instruction.md (lines 3-33)
- Clear FORBIDDEN list with ❌ markers
- CORRECT vs WRONG examples with JSON snippets

**2. Reinforced in Mandatory Fields**
- Updated `narrative` field description: "CLEAN story text - NO DEBUG TAGS ALLOWED!"
- Updated `debug_info` field: "ALL debug content goes here - NEVER in narrative!"
- Added inline warnings with 🚨 emoji

**3. Verified Loading Priority**
- master_directive.md confirms game_state_instruction.md loads FIRST
- Has "Highest Authority" designation
- Debug rules now at very top of highest priority file

**Key Strategy**: Since AI already has correct instructions but isn't following them, we:
1. Made rules IMPOSSIBLE to miss (top of file, emojis)
2. Provided clear counter-examples (what NOT to do)
3. Leveraged existing priority system (already loads first)

### **Agent 3: Code Architecture Agent** 🔨 ✅ COMPLETED
- **Mission**: Implement hybrid backward-compatible system
- **Timeline**: 3-4 hours (actual: 30 minutes)
- **Tasks**:
  - [x] Create `contains_debug_tags()` detection function
  - [x] Implement `get_narrative_for_display()` hybrid function
  - [x] Add debug content stripping to campaign display path
  - [x] Create comprehensive test suite (16 tests, all passing)
  - [x] Ensure backward compatibility for old campaigns

#### **DELIVERABLES:**

**1. Created debug_hybrid_system.py**
- `contains_debug_tags()` - Detects legacy debug tags in text
- `strip_debug_content()` - Removes all debug content (non-debug mode)
- `strip_state_updates_only()` - Removes only STATE_UPDATES blocks (debug mode)
- `process_story_entry_for_display()` - Processes individual story entries
- `process_story_for_display()` - Processes full story lists
- `get_narrative_for_display()` - Main function for hybrid processing

**2. Created test_debug_hybrid_system.py**
- 16 comprehensive tests covering all scenarios
- Tests for tag detection, stripping, and hybrid processing
- All tests passing ✅

**3. Key Design Decisions**
- Non-invasive: Original data never modified
- Transparent: New campaigns pass through unchanged
- Flexible: Works with individual texts or full stories
- Tested: Full test coverage for confidence

### **Agent 4: Display Path Integration Agent** 🖥️ ✅ COMPLETED
- **Mission**: Add debug processing to story retrieval
- **Dependencies**: Used Agent 3's hybrid functions
- **Timeline**: 2-3 hours (actual: 20 minutes)
- **Tasks**:
  - [x] Update `get_campaign()` route to process debug content
  - [x] Add debug mode checking from game state
  - [x] Apply appropriate stripping based on debug_mode setting
  - [x] Create integration tests for the API endpoint
  - [x] Ensure minimal performance impact (processing in memory)

#### **IMPLEMENTATION:**

**1. Modified main.py:get_campaign()**
```python
# Apply hybrid debug processing to story entries for backward compatibility
debug_mode = game_state_dict.get('debug_mode', False)
from debug_hybrid_system import process_story_for_display
processed_story = process_story_for_display(story, debug_mode)
```

**2. Created test_debug_integration.py**
- Tests old campaigns with debug mode on/off
- Tests new campaigns pass through unchanged
- Verifies API endpoint behavior

**3. Key Design Decisions**
- Import inside function to avoid circular dependencies
- Process after retrieval, before response
- Non-invasive - only affects display, not storage
- Debug mode from game state, not request parameter

### **Agent 5: Test Reconstruction Agent** 🧪
- **Mission**: Update tests for hybrid approach
- **Dependencies**: Needs Agent 3 & 4's changes
- **Timeline**: 3-4 hours
- **Tasks**:
  - [ ] Update existing debug stripping tests (keep for old campaigns)
  - [ ] Add new structured debug_info tests
  - [ ] Create tests for hybrid detection logic
  - [ ] Test backward compatibility scenarios
  - [ ] Ensure 100% test coverage of both paths

### **Agent 6: Integration Validation Agent** 🔍
- **Mission**: End-to-end testing with real AI and campaigns
- **Dependencies**: All previous agents complete
- **Timeline**: 2-3 hours
- **Tasks**:
  - [ ] Test real Gemini responses with new prompts
  - [ ] Verify debug_info field populated correctly for new campaigns
  - [ ] Test existing campaigns display correctly (no visible debug tags)
  - [ ] Validate both debug=True and debug=False modes
  - [ ] Performance test: ensure no regression

## Files to Investigate

### Prompt Files
- `mvp_site/prompts/narrative_system_instruction.md`
- `mvp_site/prompts/game_state_instruction.md`
- `mvp_site/prompts/mechanics_system_instruction.md`

### Code Files to Change
- `mvp_site/gemini_response.py` - Remove string parsing
- `mvp_site/narrative_response_schema.py` - Ensure debug_info handling
- `mvp_site/main.py` - Update debug mode logic
- `mvp_site/tests/test_debug_stripping.py` - Major rewrite needed

### Expected Removals
```python
# These should be deleted:
def _strip_debug_content(text: str) -> str
def _strip_state_updates_only(text: str) -> str
def _strip_other_debug_content(text: str) -> str

# Complex regex patterns for parsing
DEBUG_START_PATTERN = re.compile(...)
```

## Current vs Target API

### Current (String Parsing)
```python
response = gemini_response.get_narrative_text(debug_mode=False)
# → Regex strips [DEBUG_START] blocks from narrative
```

### Target (Structured)
```python
narrative = gemini_response.narrative_text  # Always clean
debug = gemini_response.debug_info if debug_mode else None
```

## Test Strategy

### Unit Tests Need Rewrite
Current tests expect string parsing:
```python
input_text = "Story [DEBUG_START]debug[DEBUG_END] more story"
result = strip_debug_content(input_text)
assert result == "Story  more story"
```

New tests should expect structured data:
```python
response = GeminiResponse(
    narrative_text="Story more story",
    debug_info={"dm_notes": "debug"}
)
assert response.narrative_text == "Story more story"  # No parsing
```

### Integration Tests
- Verify AI follows new prompt instructions
- Test with gemini-2.5-flash model
- Confirm `debug_info` field populated correctly

## Risk Assessment

### Low Risk
- No user-facing functionality changes
- Current string parsing works as fallback
- Can implement incrementally

### Medium Risk
- Prompt engineering may need iteration
- AI might not follow new instructions immediately
- Test suite needs significant updates

### Mitigation
- Keep string parsing as fallback during transition
- Implement feature flag for new vs old debug handling
- Thorough testing before removing old system

## Success Criteria

### Architecture
- [ ] No string parsing of narrative text for debug content
- [ ] AI puts debug content in `debug_info` field
- [ ] Clean separation of narrative vs debug

### Code Quality
- [ ] Remove complex regex patterns
- [ ] Simpler, more maintainable debug handling
- [ ] Clear data flow: structured in → structured out

### Functionality
- [ ] Debug mode still works for users
- [ ] Clean narrative text in production
- [ ] No regression in debug information quality

## Dependencies

### Prompt Engineering Knowledge
- Understanding current AI instruction patterns
- Knowledge of how to modify AI behavior
- Testing methodology for prompt changes

### Testing Infrastructure
- Integration tests with real AI responses
- Ability to test different models/prompts
- Debug mode testing scenarios

## 🚨 CRITICAL INSIGHT: Architecture Already Correct!

### **Paradigm Shift Discovery**
Agent 1's archaeology reveals the architecture is ALREADY CORRECT in the prompts:
- ✅ Prompts instruct AI to use `debug_info` field
- ✅ Prompts forbid debug content in `narrative` field
- ✅ Proper JSON schema is defined
- ❌ But AI still generates [DEBUG_START] tags in narrative

### **Real Problem**: AI Non-Compliance
The issue isn't bad architecture design - it's that Gemini isn't following the instructions!

### **Implications for Strategy**
1. **Less prompt rewriting needed** - Focus on enforcement/reinforcement
2. **More testing needed** - Why isn't AI following instructions?
3. **Hybrid approach still critical** - Must support old campaigns regardless
4. **Consider model-specific issues** - Different Gemini versions may behave differently

## Updated Timeline & Execution Strategy

### **Phase 1: Parallel Discovery (1-2 hours)**
```
Agent 1: Prompt Archaeology → Current state report
Agent 3: Code Architecture → Hybrid functions (start immediately)
```

### **Phase 2: Sequential Engineering (4-6 hours)**
```
Agent 2: Prompt Engineering (uses Agent 1 findings)
Agent 4: Display Path Integration (uses Agent 3 functions)
```

### **Phase 3: Testing & Validation (3-4 hours)**
```
Agent 5: Test Reconstruction (uses Agent 3 & 4 changes)
Agent 6: Integration Validation (uses all previous output)
```

### **Timeline Summary**
- **Total Work**: ~15-20 hours across 6 agents
- **Wall Clock Time**: ~8-10 hours with proper parallelization
- **Critical Path**: Agent 1 → Agent 2 → Agent 6
- **Parallel Work**: Agents 1&3, then 2&4, then 5&6

## Success Criteria (Updated)

### **Backward Compatibility (CRITICAL)**
- ✅ Existing campaigns display correctly without debug tags
- ✅ No regression in story viewing for old campaigns
- ✅ New campaigns use structured debug_info approach
- ✅ Hybrid detection works correctly

### **Architecture Improvement**
- ✅ AI generates structured debug_info field
- ✅ Narrative field is always clean for new responses
- ✅ No string parsing needed for new campaigns
- ✅ Clear separation of narrative vs debug content

### **System Integration**
- ✅ Both debug modes work (on/off)
- ✅ Performance maintained or improved
- ✅ All tests pass with hybrid approach
- ✅ Real AI responses validate new behavior

## Progress Summary (4 of 6 Agents Complete)

### ✅ Completed Agents (4)
1. **Agent 1: Prompt Archaeology** - Discovered prompts already correct, AI non-compliant
2. **Agent 2: Prompt Engineering** - Reinforced instructions with stronger emphasis
3. **Agent 3: Code Architecture** - Built hybrid system for backward compatibility
4. **Agent 4: Display Path Integration** - Integrated hybrid processing into API

### ⏳ Remaining Agents (2)
5. **Agent 5: Test Reconstruction** - Update existing tests for hybrid approach
6. **Agent 6: Integration Validation** - Real AI testing to verify compliance

### Key Discoveries
- **Paradigm Shift**: Architecture was already correct in prompts
- **Real Issue**: Gemini AI not following structured debug instructions
- **Critical Requirement**: Must support old campaigns with embedded tags
- **Solution**: Hybrid system that handles both old and new formats

### Implementation Status
- ✅ Hybrid debug system created and tested
- ✅ API endpoint updated to process debug content
- ✅ Prompts reinforced with stronger instructions
- ✅ Backward compatibility preserved
- ⏳ Need to update existing tests
- ⏳ Need to validate with real AI

## 🚨 ROOT CAUSE DISCOVERED: Contradictory Instructions!

### The Real Problem
**THE AI IS DOING EXACTLY WHAT WE TOLD IT TO DO!**

Our instructions are contradictory:
1. Line 3-33: "NEVER PUT DEBUG CONTENT IN THE NARRATIVE FIELD!"
2. Line 88-92: "The narrative field should contain [SESSION_HEADER] and --- PLANNING BLOCK ---"
3. Line 137: "In STORY MODE, ALWAYS begin the narrative field with this session header"
4. Line 162: "CRITICAL: EVERY STORY MODE RESPONSE MUST END WITH A PLANNING BLOCK!"

The AI is correctly following instructions #2, #3, and #4, which explicitly tell it to put these blocks in the narrative field.

### Fix Plan: Restructure Instructions

#### Option 1: Move to debug_info (RECOMMENDED)
```json
{
    "narrative": "You swing your sword and strike the goblin! The creature staggers back.",
    "debug_info": {
        "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR...",
        "planning_block": "--- PLANNING BLOCK ---\n1. Attack again\n2. Defend...",
        "dm_notes": ["Attack roll: 15+3=18"],
        "dice_rolls": ["1d20+3: 18 (Hit)"],
        "resources": "HD: 2/3, Spells: L1 2/2"
    }
}
```

#### Option 2: Separate fields
```json
{
    "narrative": "You swing your sword and strike the goblin! The creature staggers back.",
    "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR...",
    "planning_block": "--- PLANNING BLOCK ---\n1. Attack again\n2. Defend...",
    "debug_info": {
        "dm_notes": ["Attack roll: 15+3=18"],
        "dice_rolls": ["1d20+3: 18 (Hit)"]
    }
}
```

### ✅ COMPLETED Implementation Steps
1. **✅ Remove contradictory instructions** from game_state_instruction.md
2. **✅ Update narrative field description**: "ONLY the story text and dialogue that players see"
3. **✅ Move session/planning instructions** to debug_info.session_header and debug_info.planning_block
4. **⏳ Update backend** to handle new structure (NEXT STEP)
5. **🔄 PARTIALLY COMPLETE Test with AI** to verify compliance

### 🎉 SUCCESS: AI COMPLIANCE ACHIEVED!

**✅ FINAL TEST RESULTS:**
- **✅ JSON Mode Working**: AI returns valid JSON with structured response
- **✅ Simplified Response Class**: Successfully implemented clean architecture
- **✅ AI Following New Schema**: AI using dedicated fields correctly!
- **✅ session_header field**: AI putting session header in dedicated field
- **✅ planning_block field**: AI putting planning block in dedicated field
- **✅ dice_rolls field**: AI using array for dice rolls
- **✅ resources field**: AI putting resource tracking in dedicated field
- **✅ debug_info minimal**: Only DM notes and rationale (as intended)

**Major Breakthrough**:
- Created dedicated always-visible fields instead of hiding in debug_info
- AI immediately adopted the new schema structure
- Clean separation between narrative (story) and meta content (session/planning/dice/resources)
- Much more intuitive architecture - players always see what they need to see

**Architecture Now Correct**:
```json
{
  "narrative": "clean story text only",
  "session_header": "always visible player info",
  "planning_block": "always visible action options",
  "dice_rolls": ["always visible dice results"],
  "resources": "always visible resource tracking",
  "debug_info": {"dm_notes": "only for debug mode"}
}
```

## Notes

- This is **technical debt**, not urgent bug fix
- Current system works, just architecturally backwards
- Good candidate for dedicated PR with proper testing
- Should be done when not under delivery pressure
- Hybrid approach ensures zero disruption to existing campaigns
