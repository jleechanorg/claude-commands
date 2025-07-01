# Prompt System Cleanup Plan

## Overview
This plan outlines a systematic approach to cleaning up the WorldArchitect.AI prompt system, addressing the 14 critical issues identified in the prompt conflicts analysis.

## Phase 1: Immediate Cleanup (No User Input Required)

### Milestone 1.1: ~~Remove Duplicate Personality Files~~ (Completed - No duplicates found)
**Timeline:** Immediate
**Complexity:** Low
**Dependencies:** None

**Result:** Investigation showed there are no duplicate files. The personalities directory correctly contains 32 files: 16 portrait files and 16 growth files (one of each per MBTI type).

### Milestone 1.2: ~~Fix Self-Contradictory Mission List Instructions~~ (Completed)
**Timeline:** 1 hour
**Complexity:** Low
**Dependencies:** None

**Completed Tasks:**
1. ✅ Edited `game_state_instruction.md` to remove the "TOLERATED BUT NOT RECOMMENDED" dictionary format
2. ✅ Enforced strict list-only format for `active_missions`
3. ✅ Updated examples to show only the correct list format
4. ✅ Added clear error example with "INVALID FORMAT" showing what NOT to do
5. ✅ Added explicit rules stating array format is required

### Milestone 1.3: ~~Consolidate Duplicate Calendar Definitions~~ (Completed)
**Timeline:** 2 hours
**Complexity:** Medium
**Dependencies:** None

**Completed Tasks:**
1. ✅ Moved complete calendar definitions to `game_state_instruction.md`
2. ✅ Removed duplicate calendar details from `narrative_system_instruction.md`
3. ✅ Added reference in narrative instruction pointing to game state's "World Time Management" section
4. ✅ Ensured time advancement references the `world_time` object in game state

### Milestone 1.4: Create Entity ID Format Standard
**Timeline:** 1 hour
**Complexity:** Low
**Dependencies:** None

**Tasks:**
1. Document single consistent entity ID format in `entity_schema_instruction.md`
2. Update all examples in `game_state_instruction.md` to match
3. Add validation examples showing correct vs incorrect formats
4. Remove any conflicting ID format examples

### Milestone 1.5: Consolidate Combat State Structure
**Timeline:** 3 hours
**Complexity:** High
**Dependencies:** None

**Tasks:**
1. Create unified combat state structure in `destiny_ruleset.md`
2. Remove combat state definitions from `game_state_instruction.md` and `mechanics_system_instruction.md`
3. Update both files to reference destiny ruleset for combat
4. Ensure combat flow follows single consistent pattern

## Phase 2: Structural Reorganization (No User Input Required)

### Milestone 2.1: Create Master Directive File
**Timeline:** 2 hours
**Complexity:** Medium
**Dependencies:** Milestone 1.5 complete

**Tasks:**
1. Create `master_directive.md` with:
   - Clear hierarchy of all prompt files
   - Precedence rules for conflicts
   - Loading order specification
   - Authority definitions for each file
2. Update all "PRIORITY #1" claims to reference master directive
3. Add version number for tracking changes

### Milestone 2.2: Consolidate Planning/Think Block Protocol
**Timeline:** 2 hours
**Complexity:** Medium
**Dependencies:** Milestone 2.1 complete

**Tasks:**
1. Move complete Think Block protocol to `narrative_system_instruction.md`
2. Update `mechanics_system_instruction.md` to reference narrative file
3. Remove any duplicate protocol definitions
4. Ensure single source of truth for planning blocks

### Milestone 2.3: Unify Leveling Tiers Definition
**Timeline:** 1 hour
**Complexity:** Low
**Dependencies:** None

**Tasks:**
1. Keep full definition in `mechanics_system_instruction.md`
2. Update `narrative_system_instruction.md` to reference mechanics
3. Remove duplicate tier descriptions
4. Add cross-reference notes

### Milestone 2.4: Optimize Personality File Loading
**Timeline:** 2 hours
**Complexity:** Medium
**Dependencies:** Milestone 1.1 complete

**Tasks:**
1. Create personality loading instruction in master directive
2. Specify on-demand loading instead of bulk loading
3. Add personality type detection logic
4. Document when each personality file should be loaded

## Phase 3: Critical Fixes Requiring User Decisions

### Milestone 3.1: Resolve Character Attribute System Conflict
**Timeline:** 4 hours
**Complexity:** High
**Dependencies:** User decision required

**Decision Required:**
- Option A: Update Destiny ruleset to use D&D 6-attribute system (STR, DEX, CON, INT, WIS, CHA)
- Option B: Update character sheet template to use Destiny 5-aptitude system (Physique, Coordination, Health, Intelligence, Wisdom)
- Option C: Support both with clear separation and conversion rules

**Tasks (after decision):**
1. Update the chosen system consistently across all files
2. Remove or clearly mark the deprecated system
3. Add migration guide if needed
4. Update all examples to use consistent system

### Milestone 3.2: Implement Instruction Loading Order
**Timeline:** 3 hours
**Complexity:** High
**Dependencies:** Milestone 2.1 complete, User approval required

**Decision Required:**
- Approve new loading order as specified in master directive
- Confirm state management should load before narrative

**Tasks (after approval):**
1. Update code to load prompts in new order
2. Test loading order with sample campaigns
3. Document loading sequence in code
4. Add loading order validation

### Milestone 3.3: Implement DELETE Token Processing
**Timeline:** 4 hours
**Complexity:** High
**Dependencies:** User confirmation of implementation approach

**Decision Required:**
- Confirm `__DELETE__` token should remove entities completely
- Approve implementation approach
- Define edge cases (what if entity is referenced elsewhere?)

**Tasks (after decision):**
1. Verify code implementation matches prompt documentation
2. Add comprehensive DELETE token handling
3. Create test cases for deletion scenarios
4. Document deletion behavior clearly

## Phase 4: Long-term Optimization

### Milestone 4.1: Reduce Instruction Complexity
**Timeline:** 1 week
**Complexity:** Very High
**Dependencies:** All previous milestones complete

**Tasks:**
1. Analyze instruction usage patterns
2. Identify rarely-used instructions
3. Create modular instruction sets
4. Implement conditional loading based on campaign type
5. Reduce total instruction count from ~5000 to <3000 lines

### Milestone 4.2: Add Validation Layer
**Timeline:** 1 week
**Complexity:** Very High
**Dependencies:** Phase 3 complete

**Tasks:**
1. Create schema validation for all data structures
2. Implement pre-flight checks for state updates
3. Add type checking for critical fields
4. Create error reporting system
5. Implement recovery mechanisms for invalid data

## Implementation Order

### Immediate (Can do now):
1. Milestone 1.1: Remove Duplicate Personality Files
2. Milestone 1.2: Fix Mission List Instructions
3. Milestone 1.3: Consolidate Calendar Definitions
4. Milestone 1.4: Create Entity ID Standard
5. Milestone 1.5: Consolidate Combat State

### Next Phase (Can do without input):
6. Milestone 2.1: Create Master Directive
7. Milestone 2.2: Consolidate Think Block
8. Milestone 2.3: Unify Leveling Tiers
9. Milestone 2.4: Optimize Personality Loading

### Requires User Decision:
10. Milestone 3.1: Character Attributes (BLOCKING - need decision first)
11. Milestone 3.2: Loading Order (need approval)
12. Milestone 3.3: DELETE Token (need confirmation)

### Long-term:
13. Milestone 4.1: Reduce Complexity
14. Milestone 4.2: Add Validation

## Success Metrics
- Zero duplicate definitions across files
- Single source of truth for each system
- Clear precedence hierarchy
- Reduced instruction count by 40%
- No conflicting examples
- All cross-references accurate
- Validation catches 95% of data errors

## Risk Mitigation
- Create backups before each change
- Test each milestone in isolation
- Document all changes in git commits
- Keep rollback plan for each phase
- Monitor AI behavior after each change