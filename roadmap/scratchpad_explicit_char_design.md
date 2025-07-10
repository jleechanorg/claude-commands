# Scratchpad: Explicit Character Design UI

**Branch**: explicit_char_design  
**Goal**: Replace single prompt textarea with separate character and setting inputs  
**Date**: 2025-01-10

## Current State

✅ **COMPLETED**: Successfully implemented character and setting separation!

**Before**: Users entered everything in one big textarea:
- "Play as Astarion who ascended in BG3 in Baldur's Gate setting"
- LLM had to parse what's character vs setting
- Often failed to recognize character specifications

**After**: Clean separation with two input boxes:
- Character Input: "Astarion who ascended in BG3"
- Setting Input: "Baldur's Gate"
- Backend constructs: "Character: Astarion who ascended in BG3\nSetting: Baldur's Gate"

## Proposed Solution

### UI Changes
Replace current textarea with two separate input boxes:

**Character Input Box:**
- Label: "Character you want to play"
- Placeholder: "Random character (auto-generate)"
- Input type: text or textarea (single line preferred)
- Examples: "Astarion who ascended in BG3", "A brave knight", "Random"

**Setting Input Box:**
- Label: "Setting/world for your adventure"  
- Placeholder: "Random fantasy D&D world (auto-generate)"
- Input type: text or textarea (single line preferred)
- Examples: "Baldur's Gate", "Modern day New York", "Random"

### Backend Changes
- Add `character` and `setting` parameters to `/api/campaigns` endpoint
- Update prompt construction to handle separate inputs
- Modify CHARACTER_DESIGN_REMINDER to work with explicit character input
- Update mechanics instructions to handle separate character/setting

### Logic Rules
1. **Both empty**: Generate random character + random setting
2. **Character only**: Use specified character + random setting
3. **Setting only**: Generate random character + specified setting  
4. **Both specified**: Use both as specified

## Implementation Plan

### Phase 1: Frontend (TDD)
1. **Test**: Form collects character and setting inputs separately
2. **Test**: Sends character/setting as separate params to backend
3. **Test**: Handles empty inputs gracefully
4. **Implement**: Update HTML form structure
5. **Implement**: Update JavaScript form submission logic

### Phase 2: Backend (TDD)
1. **Test**: Endpoint accepts character/setting parameters
2. **Test**: Processes empty inputs as "random"
3. **Test**: Constructs prompts with separate character/setting
4. **Test**: CHARACTER_DESIGN_REMINDER works with explicit character
5. **Implement**: Update main.py endpoint
6. **Implement**: Update gemini_service.py prompt construction
7. **Implement**: Update constants.py reminder logic

### Phase 3: Integration Testing
1. **Test**: End-to-end flow from UI to LLM response
2. **Test**: Character design properly recognizes specified characters
3. **Test**: Setting properly influences world generation
4. **Test**: Random generation works when inputs are empty

## File Changes Required

### Frontend Files
- `mvp_site/static/index.html` - Update form structure
- `mvp_site/static/app.js` - Update form submission logic
- `mvp_site/static/js/campaign-wizard.js` - Update wizard if needed

### Backend Files
- `mvp_site/main.py` - Update `/api/campaigns` endpoint
- `mvp_site/gemini_service.py` - Update prompt construction
- `mvp_site/constants.py` - Update CHARACTER_DESIGN_REMINDER
- `mvp_site/prompts/mechanics_system_instruction.md` - Update instructions

## Test Cases

### Frontend Tests ✅ COMPLETED
- [x] Form collects character input
- [x] Form collects setting input  
- [x] Empty inputs handled correctly
- [x] Form submission sends correct parameters
- [x] Old textarea properly removed

### Backend Tests ✅ COMPLETED
- [x] Endpoint accepts new parameters
- [x] Empty character becomes "random character"
- [x] Empty setting becomes "random setting"
- [x] Specified inputs are preserved
- [x] Prompt construction works correctly
- [x] Backward compatibility maintained

### Integration Tests 🔄 IN PROGRESS
- [ ] End-to-end character specification works
- [ ] End-to-end setting specification works  
- [ ] Random generation works for empty inputs
- [ ] LLM properly recognizes explicit character input
- [ ] CHARACTER_DESIGN_REMINDER adapts to specified character

## Next Steps

### ✅ COMPLETED
1. ✅ **Frontend Implementation**: TDD approach - HTML/JS changes with comprehensive tests
2. ✅ **Backend Implementation**: TDD approach - API endpoint changes with comprehensive tests  
3. ✅ **Character Design System Updates**: Enhanced CHARACTER_DESIGN_REMINDER and mechanics instructions

### 🔄 CURRENT STATUS
**PR Comments Need Resolution**: Core implementation complete, but PR #474 has critical feedback requiring fixes.

### ⚠️ PR COMMENT RESOLUTION STATUS

**✅ RESOLVED Issues (replied to on PR):**
1. **Logic Fix**: ✅ MOSTLY RESOLVED - 4-case logic works correctly in `_build_campaign_prompt()`
2. **Code Organization**: ✅ RESOLVED - Helper method `_build_campaign_prompt()` extracted and working
3. **Import Issues**: ✅ RESOLVED - `import re` properly placed at line 45 in gemini_service.py

**❌ REMAINING Issues - Need Action:**
1. **Terminology Audit**: Complete "creation" → "design" rename across files
   - `mechanics_system_instruction.md`: 18 instances 
   - `campaign-wizard.js`: 13 instances
   - `animation-helpers.js`, `enhanced-search.js`, `visual-validator.js`: 1-2 instances each
2. **Port Standardization**: Test files use inconsistent ports (6006, 6007, 6008, 8080, 5000)
3. **Architecture Decisions**: 
   - Remove old one-pager wizard if no longer needed
   - Decide on backward compatibility for old `prompt` parameter
4. **Accessibility**: Add aria-labels, screen reader support to form inputs

**Copilot Technical Debt:**
- Form validation improvements
- Screenshot utility filename sanitization  
- Documentation updates

### 🎯 REVISED SUBAGENT RESOLUTION PLAN

#### **Subagent A: Terminology & Consistency** (High Priority)
**Target**: Complete terminology standardization and code consistency  
**Tasks**:
1. **Terminology Audit**: Replace all "creation" → "design" in:
   - `mechanics_system_instruction.md` (18 instances)
   - `campaign-wizard.js` (13 instances)  
   - `animation-helpers.js`, `enhanced-search.js`, `visual-validator.js` (1-2 each)
2. **Port Standardization**: Centralize test port configuration to use consistent port (6006)
   - Update all test files to use standard port
   - Create shared config for test server URLs
3. **Documentation Updates**: Update comments and docstrings to reflect "design" terminology

**Testing Strategy**:
- Grep-based verification that no "creation" instances remain
- Test all standardized ports work correctly
- Validate terminology consistency across all files

#### **Subagent B: Architecture & Cleanup** (Medium Priority)
**Target**: Address remaining architectural decisions and cleanup
**Tasks**:
1. **Backward Compatibility Decision**: 
   - Evaluate if old `prompt` parameter is still needed
   - Either remove entirely or document as deprecated
2. **Old Wizard Investigation**: 
   - Identify what "old one-pager wizard" refers to
   - Remove if no longer needed
3. **Code Organization**: Review and clean up any remaining technical debt

**Testing Strategy**:
- API tests to verify parameter handling
- Integration tests for wizard functionality
- Regression testing for removed features

#### **Subagent C: Accessibility & UI Polish** (Low Priority)
**Target**: Improve user experience and accessibility
**Tasks**:
1. **Accessibility**: Add aria-labels, required field markers to character/setting inputs
2. **Form Validation**: Add proper client-side validation  
3. **Screenshot Utilities**: Improve filename sanitization (Copilot suggestion)
4. **Error Messages**: Improve user-facing error text

**Testing Strategy**:
- Accessibility validation with form inputs
- Screenshot generation testing with edge cases
- Form validation unit tests
- User experience testing

### ⏭️ REVISED EXECUTION SEQUENCE

**Phase 1: Terminology & Consistency** (Subagent A - 1-2 hours)
1. Complete "creation" → "design" terminology audit and fixes
2. Standardize test ports to consistent configuration
3. Update documentation and comments for consistency
4. Verify all terminology changes with grep validation

**Phase 2: Architecture Cleanup** (Subagent B - 1 hour)
1. Investigate and decide on backward compatibility for old `prompt` parameter
2. Identify and remove old wizard code if no longer needed
3. Clean up any remaining architectural technical debt
4. Document architectural decisions

**Phase 3: Accessibility & Polish** (Subagent C - 30 minutes)
1. Add accessibility attributes to form inputs
2. Improve form validation and error messages
3. Final testing and user experience validation
4. Address remaining Copilot suggestions

### 🧪 COMPREHENSIVE TEST STRATEGY

**Terminology Audit Matrix** (Subagent A):
```
| File | Instances Found | Priority | Status |
|------|----------------|----------|--------|
| mechanics_system_instruction.md | 18 | High | ❌ Fix |
| campaign-wizard.js | 13 | High | ❌ Fix |
| animation-helpers.js | 1 | Low | ❌ Fix |
| enhanced-search.js | 1 | Low | ❌ Fix |
| visual-validator.js | 2 | Low | ❌ Fix |
```

**Port Standardization Matrix** (Subagent A):
```
| Current Port | Usage | New Port | Status |
|-------------|-------|----------|--------|
| 6006 | Standard | 6006 | ✅ Keep |
| 6007 | Some tests | 6006 | ❌ Fix |
| 6008 | Some tests | 6006 | ❌ Fix |
| 8080 | Legacy tests | 6006 | ❌ Fix |
| 5000 | Old config | 6006 | ❌ Fix |
```

**Integration Test Coverage** (All Subagents):
- Terminology consistency verification
- Port standardization testing
- Architecture cleanup validation
- Accessibility compliance checks

### 🚀 SUBAGENT EXECUTION GUIDE

#### **Phase 1: Launch Subagent A (Core Logic)**
```bash
# Command: Task tool with specific directive
```
**Subagent A Instructions**:
```
You are Subagent A focusing on TERMINOLOGY & CONSISTENCY for PR #474.

CRITICAL TASKS:
1. TERMINOLOGY AUDIT: Replace all "creation" → "design" in files:
   - mechanics_system_instruction.md (18 instances found)
   - campaign-wizard.js (13 instances found) 
   - animation-helpers.js, enhanced-search.js, visual-validator.js (1-2 instances each)

2. PORT STANDARDIZATION: Unify test server ports to use 6006 consistently:
   - Find all hardcoded localhost URLs in testing_ui/ files
   - Replace 6007, 6008, 8080, 5000 with 6006
   - Create shared port configuration if possible

3. DOCUMENTATION: Update comments and docstrings to use "design" terminology

TESTING REQUIREMENTS:
- Run grep commands to verify 0 "creation" instances remain
- Test that all files use consistent port 6006
- Verify test suite still works with standardized ports

DELIVERY: Consistent terminology and port configuration across all files
```

#### **Phase 2: Launch Subagent B (Code Quality)**
```bash
# Command: Task tool with specific directive
```
**Subagent B Instructions**:
```
You are Subagent B focusing on ARCHITECTURE & CLEANUP for PR #474.

CRITICAL TASKS:
1. BACKWARD COMPATIBILITY DECISION: Evaluate old 'prompt' parameter handling:
   - Read current _build_campaign_prompt() method
   - Determine if old_prompt fallback is still needed
   - Either remove entirely or document as deprecated

2. OLD WIZARD INVESTIGATION: Find the "old one-pager wizard" referenced in comments:
   - Search for old wizard code in campaign-wizard.js  
   - Identify unused/legacy wizard components
   - Remove if no longer needed

3. ARCHITECTURE CLEANUP: Address any remaining technical debt from PR comments

TESTING REQUIREMENTS:
- Test API behavior with/without old prompt parameter
- Verify wizard functionality after cleanup
- Run regression tests for any removed features

DELIVERY: Clean architecture with clear decisions on deprecated features
```

#### **Phase 3: Launch Subagent C (Polish)**
```bash  
# Command: Task tool with specific directive
```
**Subagent C Instructions**:
```
You are Subagent C focusing on ACCESSIBILITY & UI POLISH for PR #474.

CRITICAL TASKS:
1. ADD aria-labels and accessibility attributes to character/setting inputs
2. IMPROVE screenshot utility filename sanitization
3. ADD proper form validation for character/setting inputs
4. ENHANCE error messages for better user experience

ACCESSIBILITY TARGETS:
- Add aria-required, aria-label attributes
- Ensure form inputs are properly associated with labels
- Add screen reader friendly error messages
- Test with accessibility tools if available

TESTING REQUIREMENTS:
- Validate accessibility attributes are present
- Test screenshot utility with various input strings
- Verify form validation works correctly
- Ensure error messages are user-friendly

DELIVERY: Accessible UI, robust utilities, better user experience
```

### 📋 EXECUTION CHECKLIST

**Before Starting:**
- [ ] Confirm current branch: `explicit_char_design`
- [ ] Verify PR #474 is current with latest commits
- [ ] Check test server is running on port 6006

**Phase 1 Completion Criteria:**
- [ ] All "creation" terminology replaced with "design" (grep verification shows 0 results)
- [ ] All test files use consistent port (6006) configuration  
- [ ] Documentation and comments updated with correct terminology
- [ ] Terminology consistency verified across all file types

**Phase 2 Completion Criteria:**
- [ ] Decision made on old `prompt` parameter (remove or deprecate)
- [ ] Old wizard code identified and removed if unused
- [ ] Architecture cleaned up and documented
- [ ] No remaining technical debt from original comments

**Phase 3 Completion Criteria:**
- [ ] Form inputs have proper aria-labels and accessibility attributes
- [ ] Client-side validation works correctly
- [ ] Error messages are user-friendly and clear
- [ ] Copilot suggestions addressed

**Final Validation:**
- [ ] All PR comments addressed with ✅ status
- [ ] Test suite passes 100% 
- [ ] Manual testing confirms functionality
- [ ] Ready for merge approval

## Summary

**🎯 GOAL ACHIEVED**: The system now clearly separates character and setting inputs, which should significantly improve the LLM's ability to recognize and work with user-specified characters like "Astarion who ascended in BG3".

**📊 PROGRESS**: 
- Frontend: ✅ Complete (HTML structure + JavaScript + Tests)
- Backend: ✅ Complete (API changes + Prompt construction + Tests)
- Integration: 🔄 Ready for testing

**🔗 PR**: https://github.com/jleechan2015/worldarchitect.ai/pull/157

## Notes

- This should significantly improve character recognition reliability
- Cleaner UX - users know exactly what goes where
- Backend can make smarter decisions with explicit inputs
- Still compatible with World of Assiah checkbox for rich lore