# Prompt System Remaining Issues Plan

**Version:** 1.0
**Date:** 2025-01-01
**Status:** ACTIVE
**Previous Work:** Builds on PR #189 comprehensive prompt cleanup

## Overview

This plan addresses the remaining 4 of 14 identified issues from the comprehensive prompt cleanup initiative. The previous work (PR #189) successfully resolved 10 conflicts and established the dual attribute system foundation.

## Remaining Critical Issues

### 1. Loading Order Implementation ✅ **PARTIALLY COMPLETE**

**Status:** Core hierarchy implemented, needs optimization
**Impact:** Critical for instruction hierarchy effectiveness
**Complexity:** Low (remaining work)

#### Current State ✅
- Master directive loads first (IMPLEMENTED)
- Core hierarchy respected: master_directive → game_state → entity_schema
- Conditional prompts load in correct order
- New prompts (dual_system_reference, attribute_conversion) properly integrated

#### Current Loading Order (Verified)
```
✅ IMPLEMENTED ORDER:
1. master_directive          (CORRECT - overrides all)
2. game_state               (CORRECT - core state)
3. entity_schema            (CORRECT - data structures)
4. character_template       (CONDITIONAL - narrative selected)
5. character_sheet          (CONDITIONAL - mechanics selected)
6. narrative                (CONDITIONAL - user selected)
7. mechanics                (CONDITIONAL - user selected)
8. destiny_ruleset          (ALWAYS - system rules)
9. dual_system_reference    (ALWAYS - system guidance)
10. attribute_conversion    (ALWAYS - conversion rules)
```

#### Minor Optimizations Needed
```
ACTUAL vs IDEAL ORDER COMPARISON:
✅ master_directive (1st)     - PERFECT
✅ game_state (2nd)          - PERFECT
✅ entity_schema (3rd)       - PERFECT
❓ destiny_ruleset (8th)     - Currently loads 8th, should be 4th
❓ calibration (conditional)  - Missing from current implementation
❓ personality files         - Not currently loaded (on-demand system needed)
```

#### Remaining Implementation Tasks
- [ ] **Minor Reordering**
  - Move `destiny_ruleset` to load after `entity_schema` (position 4)
  - Add `calibration_instruction` to conditional loading when selected
  - Implement personality file on-demand loading system

- [ ] **Testing Requirements** ✅ **MOSTLY COMPLETE**
  - ✅ Verified instruction hierarchy in generated system text
  - ✅ Tested conditional prompt loading maintains order
  - ✅ Core prompts load in correct sequence
  - [ ] Test calibration prompt conditional loading
  - [ ] Validate personality file on-demand system

**Estimated Effort:** 0.5-1 day (minor adjustments)
**Risk:** Low (small tweaks to working system)

---

### 2. DELETE Token Processing Investigation 🔍 **HIGH PRIORITY**

**Status:** Needs investigation and potential fix
**Impact:** Critical for combat state consistency
**Complexity:** Medium

#### Current State
- AI instructions reference `__DELETE__` token for defeated enemies
- Partial implementation found in `firestore_service.py`
- Test file `test_delete_fix.py` exists showing expected behavior
- Unclear if current implementation handles all cases correctly

#### Implementation Tasks
- [ ] **Investigation Phase (1-2 hours)**
  - Run existing test: `python mvp_site/tests/test_delete_fix.py`
  - Trace through `firestore_service.py` `update_state_with_changes()` method
  - Verify if general `__DELETE__` token case is handled correctly
  - Test actual entity deletion in combat scenarios

- [ ] **Fix Implementation (if needed)**
  - Implement proper `__DELETE__` token processing if missing
  - Ensure defeated enemies are properly removed from state
  - Add comprehensive tests for edge cases

- [ ] **Validation**
  - Integration test with actual combat flow
  - Verify related data cleanup works correctly
  - Test malformed deletion token handling

**Estimated Effort:** 0.5-2 days (depending on findings)
**Risk:** Medium (data integrity impact)

---

### 3. Long-term: Instruction Complexity Reduction 📉 **MEDIUM PRIORITY**

**Status:** Future enhancement
**Impact:** Performance and maintainability
**Complexity:** High

#### Current State
- System instructions total 223k+ characters
- Risk of instruction fatigue for AI models
- Complex interdependencies between instruction files

#### Optimization Opportunities
```
Reduction Strategies:
1. Consolidate redundant information
2. Move detailed examples to separate reference files
3. Create tiered instruction system (core vs. advanced)
4. Implement dynamic instruction loading based on context
5. Use instruction templates with variable substitution
```

#### Implementation Tasks
- [ ] **Analysis Phase**
  - Audit all instruction files for redundancy
  - Identify most frequently used vs. edge-case instructions
  - Map instruction dependencies and conflicts
  - Measure current token usage impact

- [ ] **Optimization Phase**
  - Create instruction templates system
  - Implement context-aware instruction loading
  - Build instruction validation layer
  - Create instruction metrics and monitoring

**Estimated Effort:** 2-3 weeks
**Risk:** Low (incremental improvements)

---

### 4. Instruction Validation Layer 🛡️ **MEDIUM PRIORITY**

**Status:** Future enhancement
**Impact:** Quality assurance and consistency
**Complexity:** Medium

#### Current State
- No automated validation of instruction consistency
- Manual review required for instruction changes
- Risk of introducing conflicts during updates

#### Proposed Solution
```
Validation Components:
1. Instruction parser and analyzer
2. Conflict detection algorithms
3. Consistency checking rules
4. Automated testing for instruction changes
5. Instruction change impact analysis
```

#### Implementation Tasks
- [ ] **Parser Development**
  - Build instruction file parser
  - Extract key concepts, rules, and examples
  - Create instruction dependency graph
  - Implement conflict detection logic

- [ ] **Integration**
  - Add validation to CI/CD pipeline
  - Create instruction change review tools
  - Build metrics dashboard for instruction quality
  - Implement automated conflict resolution suggestions

**Estimated Effort:** 1-2 weeks
**Risk:** Low (quality improvement tool)

---

## Implementation Timeline

### Phase 1: Critical Fixes (Week 1)
- **Days 1-2:** Minor loading order optimizations (calibration prompt, destiny_ruleset reordering)
- **Days 3-4:** DELETE token investigation and fix implementation
- **Day 5:** Integration testing and validation

### Phase 2: Long-term Improvements (Month 2-3)
- **Month 2:** Instruction complexity reduction analysis and planning
- **Month 3:** Validation layer development and integration

## Success Metrics

### Phase 1 Success Criteria
- [ ] Minor loading order optimizations completed (calibration, destiny_ruleset positioning)
- [ ] DELETE token processing verified and working correctly
- [ ] Defeated enemies properly removed from game state
- [ ] All existing tests pass
- [ ] No state corruption from deletion operations

### Phase 2 Success Criteria
- [ ] System instruction size reduced by 20-30%
- [ ] Instruction loading time improved
- [ ] Automated validation catches 90%+ of instruction conflicts
- [ ] CI/CD pipeline prevents instruction regressions

## Risk Mitigation

### High-Risk Areas
1. **Loading Order Changes**
   - Risk: Breaking existing prompt functionality
   - Mitigation: Comprehensive testing, gradual rollout, rollback plan

2. **DELETE Token Implementation**
   - Risk: Data corruption or unintended deletions
   - Mitigation: Extensive unit testing, sandbox validation, backup strategies

### Monitoring and Validation
- Automated tests for all instruction loading scenarios
- Performance monitoring for instruction processing time
- User feedback collection for AI behavior changes
- Rollback procedures for each phase

## Dependencies

### External Dependencies
- No external API changes required
- No new service dependencies

### Internal Dependencies
- Stable test suite (all tests must pass)
- Code review approval for loading order changes
- Stakeholder approval for instruction complexity changes

## Communication Plan

### Stakeholders
- Development team: Technical implementation details
- QA team: Testing strategies and validation requirements
- Product team: User impact and behavior changes

### Progress Reporting
- Weekly progress updates during Phase 1
- Monthly reports during Phase 2
- Issue tracking via GitHub issues/project board

---

## Notes

This plan builds directly on the successful foundation established in PR #189. The remaining issues are primarily implementation and optimization tasks rather than fundamental design problems.

**Key Principle:** Maintain backward compatibility while systematically addressing each remaining issue with proper testing and validation.
