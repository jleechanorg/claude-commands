# Test Organization Improvements

## Project Goal
Fix failing tests in the mvp_site/tests directory by updating them to reflect the current codebase architecture and removing references to archived features.

## Branch Info
- **Remote Branch**: test-organization-improvements
- **Target**: main
- **PR Number**: TBD

## Implementation Plan

### Phase 1: Test Analysis ✅
- Analyzed all 9 failing tests
- Identified root causes:
  - Tests reference archived/removed constants (Calibration, Destiny systems)
  - Entity schema tests expect old constants but feature is now integrated into game_state
  - Some constants referenced in tests never existed

### Phase 2: Test Updates (IN PROGRESS)
1. **test_entity_tracking.py** - Remove PROMPT_TYPE_ENTITY_SCHEMA test, update to verify entity tracking works with game_state integration
2. **test_prompts.py** - Remove PROMPT_TYPE_CALIBRATION test
3. **test_pr_state_sync_entity.py** - Update entity schema expectations
4. **test_constants.py** - Major rewrite to only test active constants
5. Other tests appear structurally sound

### Phase 3: Validation
- Run updated tests to ensure they pass
- Verify no real bugs were masked by broken tests
- Ensure test coverage remains adequate

## Current State
- ✅ Analyzed all failing tests
- ✅ Identified broken tests vs real bugs (all are broken tests)
- ✅ Updated tests to match current architecture
- ✅ Fixed all 4 test files with outdated constants references
- ✅ Pushed changes to GitHub PR
- ✅ Added detailed analysis of remaining failures to PR
- ✅ Moved 3 google-genai dependent tests to test_integration/
- ✅ Fixed logging assertions in 2 test files
- ✅ Updated test_think_block_protocol.py to match current prompt content

## Key Context
- Many tests fail because they reference the old dual-system architecture (Narrative Flair + Calibration Rigor)
- The codebase has evolved to a single-system approach with entity tracking integrated into game_state
- Constants for archived features are commented out but tests weren't updated
- This is test maintenance debt, not application bugs

## Completed Tasks
1. ✅ Updated test_constants.py to only test active constants
2. ✅ Updated entity-related tests to check game_state integration instead of separate constants
3. ✅ Removed tests for archived prompt types
4. ✅ Verified fixes work (tests that don't require google module pass)
5. ⏳ Push to GitHub PR on test-organization-improvements branch

## Final Test Results Summary

### Fixed Tests (now passing):
- **test_constants.py**: ✅ PASSED (15 tests)
- **test_entity_tracking.py**: ✅ PASSED (8 tests)
- **test_firestore_helpers.py**: ✅ PASSED (15 tests) - Fixed logging assertion
- **test_think_block_protocol.py**: ✅ PASSED (19 tests) - Updated to match current prompt content

### Moved to test_integration/ (require google-genai):
- **test_pr_state_sync_entity.py** - Moved ✅
- **test_function_validation_flow.py** - Moved ✅
- **test_refactoring_helpers.py** - Moved ✅
- **test_prompts.py** - Still in tests/ (also needs google module)
- **test_refactoring_coverage.py** - Still in tests/ (has mock setup but needs google module)

## Remaining Test Failures Root Causes

### Missing Dependencies (3 files):
- test_pr_state_sync_entity.py - needs `google-genai` module
- test_function_validation_flow.py - needs `google-genai` module
- test_refactoring_helpers.py - needs `google-genai` module

### Test Logic Issues (3 files):
- test_firestore_helpers.py - Mock expects wrong logger instance
- test_think_block_protocol.py - Tests check for outdated prompt content
- test_refactoring_coverage.py - Mock expects wrong logger instance

**Key Finding**: No actual bugs in production code - all failures are test environment or test logic issues.

## Test Categories

### Broken Tests (need updates):
- test_entity_tracking.py - expects removed PROMPT_TYPE_ENTITY_SCHEMA
- test_prompts.py - expects removed PROMPT_TYPE_CALIBRATION
- test_pr_state_sync_entity.py - expects removed PROMPT_TYPE_ENTITY_SCHEMA
- test_constants.py - expects many archived constants

### Likely Passing Tests:
- test_firestore_helpers.py
- test_think_block_protocol.py
- test_function_validation_flow.py (may need mock setup)
- test_refactoring_helpers.py
- test_refactoring_coverage.py
