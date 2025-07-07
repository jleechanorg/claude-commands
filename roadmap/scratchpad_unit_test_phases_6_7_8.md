# Unit Test Coverage Improvement - Phases 6, 7, and 8

## Overview
Continue systematic unit test coverage improvement focusing on the three most critical files with significant coverage gaps.

### Current State (After Phases 3-5)
- **Overall Coverage**: 68% (16,869 statements, 5,388 missing)
- **Phase 3**: ✅ main.py error handling (10 tests) - PR #409
- **Phase 4**: ✅ firestore_service.py MissionHandler (34 tests) - PR #411
- **Phase 5**: ✅ firestore_service.py state helpers (30 tests) - PR #413

### Target Files for Next Phases
1. **gemini_service.py**: 65% → 85% (221 statements missing)
2. **firestore_service.py**: 61% → 80% (99 statements missing)
3. **main.py**: 73% → 85% (159 statements missing)

---

## Phase 6: gemini_service.py (65% → 85%)

**Current**: 632 statements, 221 missing
**Target**: Add ~150 statements coverage
**Priority**: CRITICAL - Core AI service

### Analysis of Missing Coverage

#### 1. Error Handling & Retry Logic (Lines ~150-250)
- **Missing**: Exception handling in API calls
- **Missing**: Retry mechanism with exponential backoff
- **Missing**: Model fallback logic (Gemini 2.5 → 1.5)
- **Test Cases**: 
  - API timeout scenarios
  - Rate limit errors
  - Invalid API key
  - Network failures
  - Model-specific errors

#### 2. Response Validation & Parsing (Lines ~350-450)
- **Missing**: Malformed response handling
- **Missing**: JSON parsing error recovery
- **Missing**: Schema validation failures
- **Test Cases**:
  - Empty responses
  - Partial JSON responses
  - Missing required fields
  - Type mismatches
  - Oversized responses

#### 3. Token Management (Lines ~500-600)
- **Missing**: Token counting edge cases
- **Missing**: Context window management
- **Missing**: Token limit exceeded handling
- **Test Cases**:
  - Very long prompts
  - Unicode/emoji token counting
  - Context truncation logic
  - Token estimation accuracy

#### 4. Campaign & Character Generation (Lines ~700-900)
- **Missing**: Edge cases in generation logic
- **Missing**: Validation of generated content
- **Missing**: Error recovery during generation
- **Test Cases**:
  - Invalid character names
  - Banned content filtering
  - Generation timeout handling
  - Partial generation recovery

### Phase 6 Implementation Plan

#### Milestone 6.1: Error Handling & Retry Tests (25 tests)
```python
test_gemini_error_handling.py:
- test_api_timeout_retry
- test_rate_limit_exponential_backoff
- test_invalid_api_key_handling
- test_network_failure_recovery
- test_model_fallback_sequence
- test_max_retry_exceeded
- test_partial_response_error
```

#### Milestone 6.2: Response Validation Tests (20 tests)
```python
test_gemini_response_validation.py:
- test_malformed_json_recovery
- test_missing_required_fields
- test_type_validation_errors
- test_oversized_response_handling
- test_empty_response_handling
- test_schema_validation_failures
```

#### Milestone 6.3: Token Management Tests (15 tests)
```python
test_gemini_token_management.py:
- test_unicode_token_counting
- test_context_window_limits
- test_prompt_truncation_logic
- test_token_estimation_accuracy
- test_multi_turn_context_management
```

#### Milestone 6.4: Generation Logic Tests (20 tests)
```python
test_gemini_generation.py:
- test_character_name_validation
- test_banned_content_filtering
- test_generation_timeout_handling
- test_campaign_world_building
- test_narrative_consistency_checks
```

---

## Phase 7: firestore_service.py (61% → 80%)

**Current**: 254 statements, 99 missing (after Phases 4-5)
**Target**: Add ~50 statements coverage
**Priority**: CRITICAL - Database operations

### Analysis of Remaining Missing Coverage

#### 1. Database Operation Error Handling (Lines ~300-400)
- **Missing**: Connection failure handling
- **Missing**: Transaction rollback scenarios
- **Missing**: Concurrent access conflicts
- **Test Cases**:
  - Database connection timeouts
  - Transaction conflicts
  - Document size limits
  - Collection query errors

#### 2. Complex State Merging (Lines ~450-550)
- **Missing**: Deep nested merge conflicts
- **Missing**: Array merge strategies
- **Missing**: Circular reference handling
- **Test Cases**:
  - Conflicting nested updates
  - Array append vs overwrite
  - Circular reference detection
  - Type mismatch resolution

#### 3. Batch Operations (Lines ~600-700)
- **Missing**: Batch write failures
- **Missing**: Partial batch success
- **Missing**: Batch size limits
- **Test Cases**:
  - Batch operation rollback
  - Partial batch failure recovery
  - Batch size optimization
  - Concurrent batch conflicts

### Phase 7 Implementation Plan

#### Milestone 7.1: Database Error Handling Tests (15 tests)
```python
test_firestore_database_errors.py:
- test_connection_timeout_recovery
- test_transaction_conflict_resolution
- test_document_size_limit_handling
- test_collection_query_errors
- test_auth_token_expiry
- test_network_interruption_handling
- test_quota_exceeded_errors
- test_invalid_field_path_errors
- test_permission_denied_handling
- test_resource_exhausted_errors
- test_deadline_exceeded_recovery
- test_already_exists_conflict
- test_not_found_document_handling
- test_failed_precondition_errors
- test_aborted_transaction_retry
```

#### Milestone 7.2: Complex State Merging Tests (20 tests)
```python
test_firestore_complex_merging.py:
- test_deep_nested_conflicts
- test_array_merge_strategies
- test_circular_reference_prevention
- test_type_coercion_rules
- test_null_vs_undefined_handling
- test_timestamp_conflict_resolution
- test_numeric_precision_handling
- test_unicode_field_merging
- test_binary_data_conflicts
- test_reference_field_merging
- test_geopoint_merge_logic
- test_map_field_deep_merge
- test_array_union_operations
- test_array_remove_operations
- test_increment_field_conflicts
- test_server_timestamp_merging
- test_field_mask_application
- test_transform_operation_order
- test_compound_write_atomicity
- test_optimistic_concurrency_control
```

#### Milestone 7.3: Batch Operation Tests (15 tests)
```python
test_firestore_batch_operations.py:
- test_batch_write_rollback
- test_partial_batch_recovery
- test_batch_size_optimization
- test_concurrent_batch_handling
- test_batch_retry_logic
- test_batch_commit_failure
- test_max_batch_size_enforcement
- test_batch_precondition_checks
- test_cross_collection_batch
- test_batch_delete_operations
- test_batch_update_validation
- test_batch_create_conflicts
- test_batch_field_transforms
- test_batch_transaction_isolation
- test_batch_operation_ordering
```

---

## Phase 8: main.py (73% → 85%)

**Current**: 599 statements, 159 missing (after Phase 3)
**Target**: Add ~75 statements coverage
**Priority**: HIGH - API endpoints

### Analysis of Remaining Missing Coverage

#### 1. Complex Route Handlers (Lines ~800-1000)
- **Missing**: Campaign state update edge cases
- **Missing**: File upload/download errors
- **Missing**: Websocket connection handling
- **Test Cases**:
  - Large state update handling
  - File upload size limits
  - Concurrent request handling
  - Session timeout scenarios

#### 2. Authentication Edge Cases (Lines ~650-750)
- **Missing**: Token refresh scenarios
- **Missing**: Multi-device authentication
- **Missing**: Permission validation
- **Test Cases**:
  - Expired token refresh
  - Concurrent session handling
  - Role-based access control
  - Cross-origin authentication

#### 3. Request Validation (Lines ~1100-1300)
- **Missing**: Complex input validation
- **Missing**: SQL injection prevention
- **Missing**: XSS prevention
- **Test Cases**:
  - Malformed request bodies
  - Injection attack prevention
  - Request size limits
  - Rate limiting logic

### Phase 8 Implementation Plan

#### Milestone 8.1: Route Handler Edge Cases (25 tests)
```python
test_main_route_edge_cases.py:
- test_large_state_update_handling
- test_file_upload_limits
- test_concurrent_campaign_updates
- test_session_timeout_handling
- test_websocket_disconnection
```

#### Milestone 8.2: Authentication Tests (25 tests)
```python
test_main_authentication_advanced.py:
- test_token_refresh_flow
- test_multi_device_sessions
- test_permission_validation
- test_cross_origin_auth
- test_auth_rate_limiting
```

#### Milestone 8.3: Security & Validation Tests (25 tests)
```python
test_main_security_validation.py:
- test_sql_injection_prevention
- test_xss_prevention
- test_request_size_limits
- test_rate_limiting_enforcement
- test_input_sanitization
```

---

## Success Metrics

### Phase 6 (gemini_service.py)
- **Target**: 65% → 85% coverage
- **Tests**: ~80 new tests
- **Focus**: Error handling, response validation, token management
- **Timeline**: 4-6 hours

### Phase 7 (firestore_service.py)
- **Target**: 61% → 80% coverage
- **Tests**: ~50 new tests
- **Focus**: Database errors, complex merging, batch operations
- **Timeline**: 3-4 hours

### Phase 8 (main.py)
- **Target**: 73% → 85% coverage
- **Tests**: ~75 new tests
- **Focus**: Route handlers, authentication, security
- **Timeline**: 4-5 hours

### Overall Goals
- **Total Coverage**: 68% → 80%+
- **New Tests**: ~205 tests across 3 phases
- **Risk Reduction**: Cover all critical error paths
- **Timeline**: 11-15 hours total

---

## Implementation Strategy

### General Approach
1. **Start with Phase 6** (gemini_service.py) - Largest impact
2. **Mock extensively** - Avoid real API calls
3. **Focus on error paths** - These are usually missing
4. **Test edge cases** - Boundary conditions, null values
5. **Verify async behavior** - Concurrent operations

### Testing Patterns
- Use consistent test file naming
- Group related tests in classes
- Mock at appropriate levels
- Test both success and failure paths
- Include integration scenarios

### Quality Checklist
- [ ] All tests pass independently
- [ ] No hardcoded values
- [ ] Proper cleanup in tearDown
- [ ] Meaningful test names
- [ ] Good assertion messages
- [ ] Documented complex scenarios

---

## Next Actions

1. **Create Phase 6 branch**: `feature/gemini-service-tests-phase6`
2. **Start with Milestone 6.1**: Error handling tests
3. **Run coverage after each milestone** to track progress
4. **Create PR after each phase** for easier review

---

## Subagent Execution Strategy

### PR Update Protocol
1. Create PR immediately after branch creation
2. Push commits after EACH milestone completion (every 5-10 tests)
3. Use descriptive commit messages: "Add gemini error handling tests (5/25)"
4. If subagent freezes, work is preserved in PR
5. Main agent can continue from last commit

### Phase 6 Subagent Prompts

#### Subagent 1: Gemini Error Handling Tests
```
TASK: Create error handling tests for gemini_service.py
BRANCH: feature/gemini-service-tests-phase6
FILE: mvp_site/test_gemini_error_handling.py

CONTEXT:
- Testing mvp_site/gemini_service.py error handling
- Current coverage: 65%, targeting 85%
- Focus on lines ~150-250 in gemini_service.py

TESTS TO IMPLEMENT (commit after each group):

Group 1 - API Errors (commit after completion):
1. test_api_timeout_with_retry - Mock timeout, verify 3 retries
2. test_api_timeout_exhausted - Mock persistent timeout, verify failure
3. test_connection_error_recovery - Mock ConnectionError, verify retry

Group 2 - Rate Limiting (commit after completion):
4. test_rate_limit_exponential_backoff - Mock 429, verify 1s, 2s, 4s delays
5. test_rate_limit_recovery - Mock 429 then success, verify recovery

Group 3 - Auth Errors (commit after completion):
6. test_invalid_api_key_handling - Mock 403, verify proper error message
7. test_expired_token_handling - Mock auth expiry, verify re-auth attempt

Group 4 - Model Fallback (commit after completion):
8. test_model_2_5_to_1_5_fallback - Mock 2.5 failure, verify 1.5 usage
9. test_all_models_fail - Mock all failures, verify final error

Group 5 - Response Errors (commit after completion):
10. test_partial_response_handling - Mock incomplete JSON, verify error
11. test_empty_response_handling - Mock empty body, verify error
12. test_malformed_response_recovery - Mock bad JSON, verify parsing error

REQUIREMENTS:
- Import and examine existing test_gemini_service.py for patterns
- Mock google.genai.Client to avoid real API calls
- Each test must be isolated and runnable independently
- Use unittest.TestCase as base class
- Include proper setUp/tearDown methods

COMMIT STRATEGY:
After each group (3-4 tests), run tests and commit:
git add mvp_site/test_gemini_error_handling.py
git commit -m "Add gemini error handling tests: [group name] (X/12 tests)"
git push origin feature/gemini-service-tests-phase6

IF BLOCKED: Report specific issue and stop. Do not simulate.
```

#### Subagent 2: Gemini Response Validation Tests
```
TASK: Create response validation tests for gemini_service.py
BRANCH: feature/gemini-service-tests-phase6 (checkout existing)
FILE: mvp_site/test_gemini_response_validation.py

CONTEXT:
- Testing mvp_site/gemini_service.py response parsing
- Focus on lines ~350-450 in gemini_service.py
- Tests JSON parsing, schema validation, field validation

TESTS TO IMPLEMENT (commit after each group):

Group 1 - JSON Parsing (commit after completion):
1. test_valid_json_parsing - Mock valid response, verify parsing
2. test_invalid_json_recovery - Mock malformed JSON, verify error
3. test_partial_json_handling - Mock truncated JSON, verify error

Group 2 - Required Fields (commit after completion):
4. test_missing_content_field - Mock response without 'content'
5. test_missing_role_field - Mock response without 'role'
6. test_missing_parts_field - Mock response without 'parts'

Group 3 - Type Validation (commit after completion):
7. test_invalid_content_type - Mock content as number not string
8. test_invalid_parts_structure - Mock parts as string not list
9. test_null_values_handling - Mock null in required fields

Group 4 - Size Limits (commit after completion):
10. test_oversized_response - Mock 10MB response, verify handling
11. test_empty_content_handling - Mock empty content field
12. test_whitespace_only_content - Mock whitespace content

REQUIREMENTS:
- Study gemini_service.py response parsing logic first
- Mock at the HTTP response level
- Test both successful parsing and error cases
- Include edge cases like Unicode, emojis

COMMIT STRATEGY:
After each group, run tests and commit:
git add mvp_site/test_gemini_response_validation.py
git commit -m "Add gemini response validation: [group name] (X/12 tests)"
git push origin feature/gemini-service-tests-phase6

IF BLOCKED: Report specific issue and stop.
```

#### Subagent 3: Gemini Token Management Tests
```
TASK: Create token management tests for gemini_service.py
BRANCH: feature/gemini-service-tests-phase6 (checkout existing)
FILE: mvp_site/test_gemini_token_management.py

CONTEXT:
- Testing token counting and context management
- Focus on lines ~500-600 in gemini_service.py
- Critical for cost control and context limits

TESTS TO IMPLEMENT (commit after each group):

Group 1 - Token Counting (commit after completion):
1. test_basic_token_counting - Test ASCII text counting
2. test_unicode_token_counting - Test emoji, Chinese, Arabic
3. test_special_char_tokens - Test code, markdown, symbols

Group 2 - Context Limits (commit after completion):
4. test_context_window_8k - Mock 8k limit, verify truncation
5. test_context_window_32k - Mock 32k limit, verify handling
6. test_context_overflow_handling - Mock exceeded context

Group 3 - Multi-turn Context (commit after completion):
7. test_conversation_history_tracking - Mock multi-turn chat
8. test_context_pruning_strategy - Mock long conversation
9. test_system_prompt_preservation - Verify system prompt kept

Group 4 - Token Estimation (commit after completion):
10. test_prompt_token_estimation - Compare estimate vs actual
11. test_response_token_budgeting - Verify response limits
12. test_token_usage_reporting - Verify usage tracking

REQUIREMENTS:
- Understand token counting logic in gemini_service.py
- Mock the token counting API responses
- Test edge cases with different character sets
- Verify context management strategies

COMMIT STRATEGY:
After each group, run tests and commit:
git add mvp_site/test_gemini_token_management.py
git commit -m "Add token management tests: [group name] (X/12 tests)"
git push origin feature/gemini-service-tests-phase6

IF BLOCKED: Report specific issue and stop.
```

### Phase 7 Subagent Prompts

#### Subagent 4: Firestore Database Error Tests
```
TASK: Create database error handling tests
BRANCH: feature/firestore-tests-phase7 (create new)
FILE: mvp_site/test_firestore_database_errors.py

CONTEXT:
- Testing mvp_site/firestore_service.py error scenarios
- Focus on connection, transaction, and query errors
- Must handle async operations properly

TESTS TO IMPLEMENT (commit after each group):

Group 1 - Connection Errors (commit after completion):
1. test_connection_timeout - Mock firestore timeout
2. test_connection_refused - Mock network failure
3. test_auth_token_expiry - Mock expired credentials

Group 2 - Transaction Errors (commit after completion):
4. test_transaction_conflict - Mock concurrent modification
5. test_transaction_rollback - Mock failed transaction
6. test_deadlock_detection - Mock transaction deadlock

Group 3 - Query Errors (commit after completion):
7. test_invalid_query_syntax - Mock bad query
8. test_query_timeout - Mock slow query timeout
9. test_query_size_limit - Mock result too large

Group 4 - Document Errors (commit after completion):
10. test_document_not_found - Mock missing doc
11. test_document_size_limit - Mock oversized doc
12. test_invalid_document_id - Mock bad doc ID

PR SETUP:
1. Create branch and PR immediately
2. Push after each group completion
3. Update PR description with progress

IF BLOCKED: Report and stop.
```

### Coordination Checklist

1. [ ] Create all branches upfront
2. [ ] Create PRs immediately (empty)
3. [ ] Launch subagents in parallel
4. [ ] Monitor PR updates every 30 mins
5. [ ] Merge completed milestones
6. [ ] Run coverage after each merge
7. [ ] Adjust strategy based on results

### Recovery Protocol

If subagent freezes:
1. Check PR for last commit
2. Pull latest changes
3. Continue from last test completed
4. Or assign remaining tests to new subagent

---

## EXECUTION STATUS UPDATE - 2025-01-07 02:05 AM

### Phase 6 Progress
- **PR #416**: https://github.com/jleechan2015/worldarchitect.ai/pull/416
- **Branch**: feature/gemini-service-tests-phase6
- **Completed**:
  - ✅ Milestone 6.1: Error handling tests (12 tests) - test_gemini_error_handling.py
  - ✅ Milestone 6.2: Response validation tests (12 tests) - test_gemini_response_validation.py
  - ✅ Milestone 6.3: Token management tests (12 tests) - test_gemini_token_management.py
  - 🔄 Milestone 6.4: Generation logic tests (IN PROGRESS) - test_gemini_generation.py created

### Critical Import Pattern for Tests
```python
# ALL test files MUST use this import pattern:
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set dummy API key before importing gemini_service
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_TESTING"

import gemini_service
# Import other modules without mvp_site prefix
```

### Remaining Work - 8 Hour Execution Plan

#### Hour 1-2: Complete Phase 6
1. Fix test_gemini_generation.py imports
2. Adjust tests to match actual gemini_service.py functions:
   - `get_initial_story()` instead of generate_character_details
   - `continue_story()` for narrative generation
3. Run all Phase 6 tests
4. Push final commit
5. Run coverage check
6. Update PR #416 description with results

#### Hour 2-4: Execute Phase 7
- **PR #417**: https://github.com/jleechan2015/worldarchitect.ai/pull/417  
- **Branch**: feature/firestore-tests-phase7
- Launch 2 subagents:
  - Subagent 5: Milestone 7.1 + 7.2 (Database errors + Complex merging)
  - Subagent 6: Complete Milestone 7.3 (Batch operations)

#### Hour 4-6: Execute Phase 8
- Create new branch: feature/main-tests-phase8
- Launch 3 subagents:
  - Subagent 7: Milestone 8.1 (Route handlers)
  - Subagent 8: Milestone 8.2 (Authentication)
  - Subagent 9: Milestone 8.3 (Security/Validation)

#### Hour 6-7: Integration & Coverage
1. Merge all PRs to main
2. Run full test suite: `./run_tests.sh`
3. Generate coverage report: `./coverage.sh`
4. Document final coverage percentages

#### Hour 7-8: Cleanup & Documentation
1. Update roadmap with completion status
2. Create summary PR with all achievements
3. Archive scratchpad

---

## COMPACT SUBAGENT PROMPTS - PHASE 7 COMPLETION

### Subagent 5: Firestore Database Errors + Complex Merging
```
TASK: Create database error and complex merging tests
BRANCH: feature/firestore-tests-phase7 (checkout existing)
FILES: 
- mvp_site/test_firestore_database_errors.py
- mvp_site/test_firestore_complex_merging.py

CRITICAL IMPORT PATTERN:
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
import firestore_service

MILESTONE 7.1 - Database Errors (15 tests):
- Connection timeouts/failures
- Transaction conflicts/rollbacks  
- Query errors and limits
- Document-level errors
- Mock google.cloud.firestore appropriately

MILESTONE 7.2 - Complex Merging (20 tests):
- Deep nested merge conflicts
- Array merge strategies
- Circular reference prevention
- Type coercion and null handling
- Test merge_game_state() and update_game_state()

COMMIT AFTER EACH MILESTONE:
git add mvp_site/test_firestore_*.py
git commit -m "Add firestore [milestone] tests (X/35 total)"
git push origin feature/firestore-tests-phase7
```

### Subagent 6: Firestore Batch Operations
```
TASK: Create batch operation tests
BRANCH: feature/firestore-tests-phase7 (checkout existing)
FILE: mvp_site/test_firestore_batch_operations.py

CRITICAL IMPORT PATTERN: [same as above]

MILESTONE 7.3 - Batch Operations (15 tests):
- test_batch_write_success
- test_batch_write_rollback_on_error
- test_partial_batch_failure_recovery
- test_batch_size_limit_500_docs
- test_concurrent_batch_conflicts
- test_batch_retry_logic
- test_batch_transaction_isolation
- test_batch_delete_operations
- test_mixed_batch_operations
- test_batch_with_subcollections

Focus on firestore_service.py batch methods.
Mock firestore batch operations carefully.

COMMIT STRATEGY: Every 5 tests
```

---

## COMPACT SUBAGENT PROMPTS - PHASE 8 COMPLETION

### Subagent 7: Route Handler Edge Cases
```
TASK: Create route handler tests for main.py
BRANCH: feature/main-tests-phase8 (create new from main)
FILE: mvp_site/test_main_route_edge_cases.py

IMPORT PATTERN:
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TESTING"] = "true"
from main import app
import json

MILESTONE 8.1 (25 tests):
Focus on Flask route edge cases:
- Large payload handling (>1MB)
- Concurrent request handling
- Session timeout scenarios
- File upload/download errors
- WebSocket disconnection
- CORS edge cases
- Rate limiting behavior

Use Flask test client:
self.client = app.test_client()

COMMIT: Every 5-7 tests
```

### Subagent 8: Authentication Advanced Tests
```
TASK: Create advanced auth tests for main.py
BRANCH: feature/main-tests-phase8 (checkout existing)
FILE: mvp_site/test_main_authentication_advanced.py

MILESTONE 8.2 (25 tests):
- Token refresh flows
- Multi-device sessions
- Permission validation (GM vs player)
- Cross-origin authentication
- OAuth edge cases
- Session hijacking prevention
- Expired token handling

Mock Firebase Auth appropriately.
Test decorators like @require_auth

COMMIT: Every 5-7 tests
```

### Subagent 9: Security & Validation Tests
```
TASK: Create security tests for main.py
BRANCH: feature/main-tests-phase8 (checkout existing)  
FILE: mvp_site/test_main_security_validation.py

MILESTONE 8.3 (25 tests):
- SQL injection attempts (even though using Firestore)
- XSS prevention in user inputs
- Request size limits
- Rate limiting enforcement
- Input sanitization
- CSRF protection
- Path traversal attempts
- JSON bomb protection

Test all user input endpoints.
Verify sanitization works.

COMMIT: Every 5-7 tests
```

---

## MASTER COORDINATION SCRIPT

```bash
#!/bin/bash
# Save as execute_all_phases.sh

echo "=== PHASE 6 COMPLETION ==="
cd /home/jleechan/projects/worldarchitect.ai/worktree_worker1
git checkout feature/gemini-service-tests-phase6
# Fix and run remaining tests
# ... (manual completion needed)

echo "=== PHASE 7 EXECUTION ==="
# Launch 2 subagents for Phase 7

echo "=== PHASE 8 EXECUTION ==="  
git checkout main
git pull origin main
git checkout -b feature/main-tests-phase8
git push -u origin feature/main-tests-phase8
# Create PR
# Launch 3 subagents for Phase 8

echo "=== COVERAGE CHECK ==="
git checkout main
# Merge all PRs first
./run_tests.sh
./coverage.sh

echo "=== FINAL REPORT ==="
# Generate summary
```

---

**Created**: 2025-01-07
**Last Updated**: 2025-01-07 02:05 AM
**Status**: Phase 6 at 90% (36/44 tests), Ready for Phase 7 & 8 execution
**Target**: Complete all phases with 80%+ coverage by 10:00 AM
