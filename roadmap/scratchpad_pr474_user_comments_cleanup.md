# PR #474 User Comments Cleanup - Execution Plan

**Branch**: explicit_char_design (continue on current branch)  
**Goal**: Address all remaining user comments from PR #474  
**Priority**: High - Complete PR review feedback  

## User Comments Status

### ✅ **RESOLVED**
1. **main.py fallback logic** - Lines 658-687 now handle all 4 cases properly
2. **Dragon Knight prompt length** - PR #478 integration completed

### 🔄 **PENDING EXECUTION**
3. **Design vs Creation terminology** - Need comprehensive audit
4. **Delete old one-page wizard** - Remove deprecated code
5. **Extract helper method** - Refactor prompt construction
6. **Backward compatibility decision** - Analyze and recommend

## Execution Plan

### **Phase 1: User Comment Resolution**

#### Task 1: Terminology Audit (30 min)
**Objective**: Replace "creation" with "design" terminology consistently

**Steps**:
1. Search all files for "creation" references:
   ```bash
   grep -r "creation" mvp_site/ --include="*.py" --include="*.js" --include="*.md"
   ```
2. Review each occurrence and categorize:
   - Character creation → character design  
   - Campaign creation → keep (refers to creating campaigns, not characters)
   - Other contexts → evaluate case by case
3. Update files systematically:
   - Constants and variable names
   - Comments and documentation
   - User-facing text and prompts
4. **Files likely to update**:
   - `constants.py` - Already has `CHARACTER_DESIGN_REMINDER`
   - `prompts/mechanics_system_instruction.md` - User specifically mentioned
   - Any remaining references in comments/docs

#### Task 2: Code Refactoring (45 min)
**Objective**: Extract prompt construction and remove old wizard

**Subtask 2a: Extract Helper Method (20 min)**
- Extract lines 656-687 from `create_campaign_route()` into:
  ```python
  def _build_campaign_prompt(character, setting, description, campaign_type, old_prompt):
      """Build campaign prompt from new fields or fallback to old format."""
  ```
- Keep exact same logic, just move to separate function
- Update `create_campaign_route()` to call helper method

**Subtask 2b: Remove Old One-Page Wizard (25 min)**
- Locate old wizard code in `campaign-wizard.js` around line 233
- Identify what constitutes "old onepager wizard"
- Remove deprecated code sections
- Ensure no references remain
- Test wizard still functions properly

#### Task 3: Backward Compatibility Analysis (15 min)  
**Objective**: Provide recommendation on old prompt handling

**Analysis Steps**:
1. Search codebase for usage of old `prompt` field:
   ```bash
   grep -r "KEY_PROMPT\|'prompt'" mvp_site/ --include="*.py"
   ```
2. Check if any existing campaigns/tests depend on old format
3. Evaluate risk/benefit of removal
4. **Recommendation Options**:
   - **Keep**: Low risk, maintains compatibility
   - **Remove**: Cleaner code, forces new format adoption
   - **Deprecate**: Keep with warning, plan future removal

### **Phase 2: JSON Architecture Cleanup**

#### Task 4: Remove Legacy Regex (30 min)
**Objective**: Replace text pattern matching with JSON-based detection

**Target**: `mvp_site/gemini_service.py:1044`
```python
# Current (legacy):
if re.search(r"\[CHARACTER CREATION", response_text, re.IGNORECASE):

# Replace with JSON-based approach:
# Check game state, response structure, or mode instead of text patterns
```

**Implementation**:
1. Analyze when character creation state should skip planning blocks
2. Design JSON-based detection method
3. Replace regex check with structured approach
4. Update related logic

#### Task 5: Testing & Validation (30 min)
**Objective**: Ensure no regressions from cleanup

**Test Areas**:
1. Character creation flow works properly
2. Campaign wizard functions correctly  
3. Prompt construction handles all cases
4. Planning block enforcement works
5. No broken references or imports

**Commands**:
```bash
# Run relevant tests
TESTING=true python mvp_site/tests/test_character_extraction_regex_bug.py
./run_tests.sh
```

## File Impact Assessment

### **High Impact** (Major changes)
- `mvp_site/main.py` - Extract helper method
- `mvp_site/static/js/campaign-wizard.js` - Remove old wizard
- `mvp_site/gemini_service.py` - Remove regex pattern

### **Medium Impact** (Content updates)  
- `mvp_site/prompts/mechanics_system_instruction.md` - Terminology
- `mvp_site/constants.py` - Variable names if needed

### **Low Impact** (Documentation/comments)
- Various files with "creation" → "design" terminology updates

## Success Criteria

1. ✅ All user comments addressed or resolved
2. ✅ No functional regressions in character creation
3. ✅ Campaign wizard works without old code
4. ✅ Prompt construction properly extracted
5. ✅ JSON-first architecture without legacy patterns
6. ✅ Consistent "design" terminology throughout

## Risk Mitigation

- **Low Risk**: Most changes are refactoring/cleanup
- **Test Coverage**: Existing tests will catch regressions  
- **Isolated Changes**: Each task can be done independently
- **Rollback Plan**: Git commits for each task allow selective revert

---

**Total Estimated Time**: 2.5 hours  
**Branch Strategy**: Continue on explicit_char_design  
**Next Step**: User approval before execution