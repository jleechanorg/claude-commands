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

## Proposed Solution

### Phase 1: Analysis
- [ ] Audit all prompt files for debug formatting instructions
- [ ] Find where AI is told to use `[DEBUG_START]` tags
- [ ] Document current debug content types and usage

### Phase 2: Prompt Engineering
- [ ] Update prompts to use structured `debug_info` field
- [ ] Remove instructions for `[DEBUG_START]` style tags
- [ ] Define clear schema for debug_info content

### Phase 3: Code Changes  
- [ ] Remove `_strip_debug_content()` functions
- [ ] Update `get_narrative_text()` to just return narrative (no parsing)
- [ ] Add `get_debug_info()` method for structured debug access
- [ ] Update tests to expect clean narrative + structured debug

### Phase 4: Integration Testing
- [ ] Test with real AI responses
- [ ] Verify debug content appears in `debug_info` field
- [ ] Confirm narrative is clean without parsing

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

## Timeline Estimate

- **Analysis**: 1-2 hours
- **Prompt Engineering**: 4-6 hours (iteration required)
- **Code Changes**: 2-3 hours  
- **Testing**: 3-4 hours
- **Total**: ~10-15 hours of focused work

## Notes

- This is **technical debt**, not urgent bug fix
- Current system works, just architecturally backwards  
- Good candidate for dedicated PR with proper testing
- Should be done when not under delivery pressure