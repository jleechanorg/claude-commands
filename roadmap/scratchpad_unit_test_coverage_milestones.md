# Unit Test Coverage Improvement Plan - Updated Milestones (January 2025)

## Overview
Updated comprehensive plan to improve unit test coverage from current 59% to 80%+ using new coverage infrastructure and accurate baseline data.

## Current State Analysis (January 2025)

### Coverage Infrastructure ✅ **COMPLETED**
- **New Coverage Tools**: `./coverage.sh` and `./run_tests.sh --coverage`
- **HTML Reports**: `/tmp/worldarchitectai/coverage/index.html`
- **Timing**: ~10 seconds total (6s tests + 4s report generation)
- **Protocol**: Coverage Analysis Protocol added to CLAUDE.md

### Accurate Coverage Baseline (From Full Test Suite)
- **Overall Coverage**: **59%** (16,023 statements, 6,542 missing)
- **Key Files**:
  - `main.py`: **33%** (599 statements, 404 missing) - **TOP PRIORITY**
  - `firestore_service.py`: **61%** (254 statements, 100 missing) - **MEDIUM PRIORITY**
  - `llm_service.py`: **65%** (632 statements, 221 missing) - **LOWER PRIORITY**
  - `game_state.py`: **91%** (182 statements, 17 missing) - **MINIMAL WORK**

### Test Infrastructure Status
- **Total Test Files**: 94+ unit test files
- **Test Fixtures**: PR #238 - Centralized fixtures ready for merge
- **Existing Coverage**: Much better than originally estimated
- **Framework**: Working unittest framework with proper mocking

## Revised Milestone Plan

### Milestone 1: main.py Coverage (Priority 1 - Week 1-2)
**Target Coverage: 33% → 65% (+32%)**

#### Current Gap Analysis
- **Missing**: 404 statements out of 599 total
- **High-Impact Areas**:
  - Route handlers: `/api/campaigns/*` endpoints (lines 242-413)
  - Authentication middleware (lines 145-161)
  - State update processing (lines 500-584)
  - Error handling utilities (lines 628-982)
  - God mode command parsing (lines 1041-1148)

#### Deliverables
1. **Route Handler Test Suite**
   - [ ] `test_main_routes.py` - Campaign CRUD endpoints
   - [ ] Test `/api/campaigns/create` with various inputs
   - [ ] Test `/api/campaigns/update` with state changes
   - [ ] Test `/api/campaigns/delete` with cleanup
   - [ ] Test error responses for invalid requests

2. **Authentication Testing**
   - [ ] `test_main_auth.py` - Authentication middleware
   - [ ] Test valid token scenarios
   - [ ] Test invalid/expired token handling
   - [ ] Test test bypass headers
   - [ ] Test authorization edge cases

3. **State Management Testing**
   - [ ] `test_main_state.py` - Core state operations
   - [ ] Test `update_campaign_state()` function
   - [ ] Test `process_user_input()` function
   - [ ] Test state synchronization scenarios
   - [ ] Test concurrent update handling

4. **Error Handling Testing**
   - [ ] `test_main_errors.py` - Error scenarios
   - [ ] Test malformed JSON requests
   - [ ] Test database connection failures
   - [ ] Test AI service failures
   - [ ] Test recovery mechanisms

#### Success Metrics
- **main.py coverage**: 33% → 65% (+32%)
- **Lines covered**: ~200 additional statements
- **Critical paths**: All major route handlers tested
- **Error coverage**: All error paths have tests

### Milestone 2: firestore_service.py Enhancement (Week 3)
**Target Coverage: 61% → 80% (+19%)**

#### Current Gap Analysis
- **Missing**: 100 statements out of 254 total
- **Focus Areas**:
  - Complex merge scenarios
  - Batch operations and transactions
  - Error handling and recovery
  - Concurrent update management

#### Deliverables
1. **Advanced Operations Testing**
   - [ ] Test batch write operations
   - [ ] Test transaction rollback scenarios
   - [ ] Test concurrent update conflicts
   - [ ] Test large state merge operations

2. **Error Scenario Testing**
   - [ ] Test connection failure recovery
   - [ ] Test quota exceeded handling
   - [ ] Test malformed data recovery
   - [ ] Test network timeout scenarios

#### Success Metrics
- **firestore_service.py coverage**: 61% → 80% (+19%)
- **Lines covered**: ~50 additional statements
- **Focus**: Critical data integrity paths

### Milestone 3: llm_service.py Polish (Week 4)
**Target Coverage: 65% → 75% (+10%)**

#### Current Gap Analysis
- **Missing**: 221 statements out of 632 total
- **Status**: Already well-covered, focus on edge cases
- **Focus Areas**:
  - Model cycling edge cases
  - Advanced error handling
  - Response validation failures

#### Deliverables
1. **Advanced Error Handling**
   - [ ] Test model cycling under load
   - [ ] Test rate limiting scenarios
   - [ ] Test malformed response handling
   - [ ] Test service degradation scenarios

#### Success Metrics
- **llm_service.py coverage**: 65% → 75% (+10%)
- **Lines covered**: ~60 additional statements
- **Focus**: Resilience and error recovery

### Milestone 4: game_state.py Completion (Week 5)
**Target Coverage: 91% → 95% (+4%)**

#### Current Gap Analysis
- **Missing**: Only 17 statements out of 182 total
- **Status**: Excellent coverage already
- **Focus Areas**: Remaining edge cases and error conditions

#### Deliverables
1. **Edge Case Completion**
   - [ ] Test boundary value conditions
   - [ ] Test error state recovery
   - [ ] Test invalid input validation
   - [ ] Test performance edge cases

#### Success Metrics
- **game_state.py coverage**: 91% → 95% (+4%)
- **Lines covered**: ~8 additional statements
- **Status**: Completion and polish

## Implementation Strategy

### Phase 1: Foundation (Week 1)
1. **Merge Test Fixtures** (PR #238)
   - ✅ Centralized mocking infrastructure ready
   - ✅ BaseTestCase classes available
   - ✅ Mock service patterns established

2. **Begin main.py Testing**
   - Start with route handlers (highest impact)
   - Use existing test patterns as templates
   - Focus on business logic paths

### Phase 2: Core Development (Weeks 2-4)
1. **Complete main.py testing** (33% → 65%)
2. **Enhance firestore_service.py** (61% → 80%)
3. **Polish llm_service.py** (65% → 75%)

### Phase 3: Completion (Week 5)
1. **Complete game_state.py** (91% → 95%)
2. **Integration validation**
3. **Documentation updates**

## Tools & Commands

### Coverage Analysis
```bash
# Primary coverage analysis (use this for all coverage work)
./coverage.sh                    # Unit tests with HTML report (default)
./coverage.sh --integration      # Include integration tests
./coverage.sh --no-html          # Text report only

# Alternative using existing test runner
./run_tests.sh --coverage        # Use existing runner with coverage

# View results
open /tmp/worldarchitectai/coverage/index.html
```

### Test Development
```bash
# Run all tests (fast, parallel)
./run_tests.sh

# Run specific test file
TESTING=true vpython mvp_site/tests/test_main.py

# Run from mvp_site directory
cd mvp_site && source ../venv/bin/activate
TESTING=true python tests/test_main_routes.py
```

### Coverage Tracking Progress
```bash
# Track progress on key files
./coverage.sh --no-html | grep -E "(main\.py|firestore_service\.py|llm_service\.py|game_state\.py)"

# Full coverage summary
./coverage.sh --no-html | tail -10
```

## Success Criteria

### Quantitative Goals (4-5 weeks)
- **Overall Coverage**: 59% → 80% (+21%)
- **main.py**: 33% → 65% (+32%) ⭐ **PRIMARY TARGET**
- **firestore_service.py**: 61% → 80% (+19%)
- **llm_service.py**: 65% → 75% (+10%)
- **game_state.py**: 91% → 95% (+4%)

### Qualitative Goals
- All critical business logic paths tested
- Comprehensive error handling validation
- Integration with centralized test fixtures
- Maintainable test documentation
- Fast test execution (<30 seconds for full suite)

## Risk Mitigation

### Technical Risks
1. **Coverage Tool Issues**: ✅ Infrastructure validated and working
2. **Test Execution Speed**: Coverage mode ~10s, normal mode <5s
3. **Mock Complexity**: ✅ Centralized fixtures reduce complexity
4. **Integration Conflicts**: Focus on unit tests only

### Scope Risks
1. **Time Overrun**: Prioritize main.py first (highest impact)
2. **Coverage Gaming**: Focus on meaningful business logic
3. **Maintenance Burden**: Use existing patterns and fixtures

## Current Status

### ✅ Completed
- **Coverage Infrastructure**: Tools working and documented
- **Baseline Analysis**: Accurate coverage data obtained
- **Priority Assessment**: main.py identified as top priority
- **Test Fixtures**: PR #238 ready for merge

### 🔄 In Progress
- **Planning**: Detailed implementation strategy complete
- **TASK-074 Review**: Coverage assessment complete

### ⭐ Next Actions
1. **Merge PR #238**: Test fixtures infrastructure
2. **Begin Milestone 1**: main.py route handler testing
3. **Use new coverage tools**: `./coverage.sh` for progress tracking

## Dependencies

### External Dependencies
- **PR #238**: Test fixtures (ready for merge)
- **Coverage Infrastructure**: ✅ Working (PR #388)

### Internal Dependencies
- **Test Environment**: ✅ TESTING=true setup working
- **Mock Services**: ✅ Patterns established
- **CI/CD**: Ready for coverage integration

## Archive History

### Previous Milestones (Pre-January 2025)
- **Milestone 1**: ✅ Test fixtures and infrastructure (completed)
- **Milestone 2**: ✅ GameState testing enhancement (completed)
- **Coverage Assessment**: ✅ Comprehensive analysis (completed)

### Updated Approach (January 2025)
- **Focus Shift**: main.py identified as highest priority (was lowest)
- **Better Baseline**: 59% overall vs 32% previously estimated
- **Tool Integration**: New coverage infrastructure integrated
- **Realistic Timeline**: 4-5 weeks vs 7 weeks previously

---

**Updated**: 2025-01-07
**Status**: Ready for Implementation
**Next Milestone**: Milestone 1 (main.py coverage 33% → 65%)
**Coverage Tool**: `./coverage.sh` (verified working)
**Priority**: main.py > firestore_service.py > llm_service.py > game_state.py
