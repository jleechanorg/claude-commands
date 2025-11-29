# JSON Mode Architecture Cleanup - Scratchpad

**Branch**: To be created
**Goal**: Remove legacy text pattern matching and enforce consistent JSON-first architecture
**Priority**: Medium - Technical debt cleanup

## Problem Statement

Current codebase has architectural inconsistency between modern JSON mode responses and legacy text pattern matching:

### Issue Identified
- **File**: `mvp_site/llm_service.py:1044`
- **Problem**: `re.search(r"\[CHARACTER CREATION", response_text, re.IGNORECASE)` checks for old-style text markers
- **Modern Approach**: Should use JSON response fields and structured data instead

### Legacy vs Modern Patterns
- ❌ **Legacy**: `if re.search(r"\[CHARACTER CREATION", response_text)`
- ✅ **Modern**: Check JSON fields, game state, or structured response data

## Files to Clean Up

### Primary Target
- `mvp_site/llm_service.py`
  - Line 1044: Remove regex pattern check in `_validate_and_enforce_planning_block()`
  - Replace with proper JSON-based character creation state detection

### Related Areas to Review
- Character creation state management
- Planning block enforcement logic
- JSON response structure validation
- Game state tracking for character creation mode

## Implementation Plan

### 1. Analysis Phase
- [ ] Map all text pattern matching usage in llm_service.py
- [ ] Identify proper JSON fields for character creation state
- [ ] Review existing character creation tests
- [ ] Document current character creation flow

### 2. Replacement Strategy
- [ ] Define JSON-based character creation detection
- [ ] Update `_validate_and_enforce_planning_block()` function
- [ ] Remove `re.search(r"\[CHARACTER CREATION")` pattern
- [ ] Add proper structured state checking

### 3. Testing
- [ ] Update existing tests for new JSON-based approach
- [ ] Verify character creation flow still works
- [ ] Test planning block enforcement without regex
- [ ] Ensure no regression in character creation UX

### 4. Cleanup
- [ ] Remove unused text pattern constants if any
- [ ] Update documentation to reflect JSON-first approach
- [ ] Verify no other legacy text pattern dependencies

## Benefits

1. **Architectural Consistency**: Pure JSON mode without text pattern mixing
2. **Maintainability**: Easier to extend and modify structured responses
3. **Performance**: No regex scanning of response text
4. **Reliability**: Structured data is more reliable than text pattern matching
5. **Future-Proof**: Supports complex character creation workflows

## Notes

- Discovered during Copilot comment evaluation on PR #474
- User correctly identified this as architectural inconsistency
- Should be part of broader JSON mode standardization effort
- Low risk change - isolated to planning block enforcement logic

## Related Issues

- Planning block enforcement could be simplified with pure JSON approach
- Character creation state management needs better structure
- Consider standardizing all AI response state detection via JSON fields

## Status Update

**Current PR**: #474 (explicit_char_design branch)
**Remaining User Comments to Address**:

### 1. main.py fallback logic ✅ **RESOLVED**
- **Comment**: "This should work for all 4 cases: both provided, only one provided, both not provided"
- **Status**: ✅ **FIXED** - Lines 658-687 now handle all combinations properly:
  - Uses new fields if ANY of character/setting/description provided
  - Falls back to old_prompt if available
  - Returns error if neither format provided
  - Provides defaults for missing character/setting fields

### 2. Design vs Creation terminology ⚠️ **PARTIAL**
- **Comment**: "substitute the word design vs creation since creation sounds like a brand new char"
- **Status**: ⚠️ **NEEDS AUDIT** - Some places updated, need comprehensive search

### 3. Delete old one-page wizard 🔄 **PENDING**
- **Comment**: "is this the old onepager wizard? I wanna fully delete that one"
- **Status**: 🔄 **CLEANUP NEEDED** - Old wizard code removal

### 4. Backward compatibility decision ❓ **USER CHOICE**
- **Comment**: "Do we need to handle old prompt?"
- **Status**: ❓ **DECISION NEEDED** - Currently kept for compatibility

### 5. Extract helper method 🔄 **REFACTORING**
- **Comment**: "extract this code into helper method"
- **Status**: 🔄 **CODE ORGANIZATION** - Prompt construction should be extracted

### 6. Dragon Knight prompt length ✅ **RESOLVED**
- **Comment**: "Also it should be longer. See this PR."
- **Status**: ✅ **DONE** - PR #478 Dragon Knight narrative integrated

---

**Created**: 2025-07-10
**Updated**: 2025-07-10
**Context**: PR #474 Copilot comment evaluation revealed legacy regex usage
**Next Steps**: Address remaining user comments + JSON cleanup
