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

### **Agent 1: Prompt Archaeology Agent** 📜
- **Mission**: Excavate current debug formatting instructions
- **Scope**: All prompt files in `mvp_site/prompts/`
- **Timeline**: 1-2 hours
- **Tasks**:
  - [ ] Audit narrative_system_instruction.md for debug instructions
  - [ ] Audit game_state_instruction.md for debug formatting
  - [ ] Audit mechanics_system_instruction.md for debug content
  - [ ] Search for: "[DEBUG_START]", "debug_info", debug formatting patterns
  - [ ] Document where AI is told to use debug tags
  - [ ] Create current state analysis report

### **Agent 2: Prompt Engineering Agent** ✍️
- **Mission**: Rewrite AI instructions for structured debug
- **Dependencies**: Needs Agent 1's findings
- **Timeline**: 4-6 hours
- **Tasks**:
  - [ ] Remove [DEBUG_START] tag instructions from prompts
  - [ ] Add debug_info field schema definitions
  - [ ] Define structured debug content types (dm_notes, dice_rolls, etc.)
  - [ ] Test prompt changes with sample scenarios
  - [ ] Validate AI follows new structured instructions

### **Agent 3: Code Architecture Agent** 🔨
- **Mission**: Implement hybrid backward-compatible system
- **Timeline**: 3-4 hours
- **Tasks**:
  - [ ] Create `contains_debug_tags()` detection function
  - [ ] Implement `get_narrative_for_display()` hybrid function
  - [ ] Add debug content stripping to campaign display path
  - [ ] Update `get_narrative_text()` for new campaigns
  - [ ] Ensure backward compatibility for old campaigns

### **Agent 4: Display Path Integration Agent** 🖥️
- **Mission**: Add debug processing to story retrieval
- **Dependencies**: Needs Agent 3's hybrid functions
- **Timeline**: 2-3 hours
- **Tasks**:
  - [ ] Update `get_campaign_by_id()` to process debug content
  - [ ] Add debug mode checking to story display
  - [ ] Apply appropriate stripping based on campaign settings
  - [ ] Test with existing campaigns containing debug content
  - [ ] Ensure no performance impact on story display

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

## Notes

- This is **technical debt**, not urgent bug fix
- Current system works, just architecturally backwards  
- Good candidate for dedicated PR with proper testing
- Should be done when not under delivery pressure