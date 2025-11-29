# Test Coverage Improvement Plan

## Current State (2025-07-02)
- Overall coverage: 32%
- firestore_service.py: 50%
- llm_service.py: 27%
- game_state.py: 15%

## Goal
Achieve 80%+ test coverage across core modules while maintaining pragmatic testing practices.

## Phase 1: Mock External Dependencies (Priority: High)
**Target: +15% coverage**

### 1.1 Create Comprehensive Mock Fixtures
- [ ] Create `tests/mocks/firebase_mocks.py` with reusable Firebase mocks
- [ ] Create `tests/mocks/gemini_mocks.py` with Gemini API response mocks
- [ ] Create `tests/mocks/flask_mocks.py` for Flask app context

### 1.2 Test Firebase Operations
- [ ] Test `save_game_state()` with mocked Firestore
- [ ] Test `get_campaign_game_state()` with various document states
- [ ] Test `create_campaign()` with mock document creation
- [ ] Test error handling for Firebase failures

### 1.3 Test Gemini API Calls
- [ ] Test `_call_llm_api()` with mocked responses
- [ ] Test token counting and budget management
- [ ] Test model fallback behavior
- [ ] Test error handling for API failures

## Phase 2: Increase game_state.py Coverage (Priority: High)
**Target: +30% coverage**

### 2.1 Core GameState Operations
- [ ] Test `from_dict()` with various state structures
- [ ] Test `to_dict()` serialization completeness
- [ ] Test state migrations and version handling
- [ ] Test entity ID generation

### 2.2 Combat System
- [ ] Test combat initialization
- [ ] Test turn order management
- [ ] Test damage calculation
- [ ] Test combat state cleanup

### 2.3 Entity Management
- [ ] Test NPC creation and updates
- [ ] Test entity removal (`__DELETE__` token)
- [ ] Test companion management
- [ ] Test entity state persistence

## Phase 3: Integration Test Improvements (Priority: Medium)
**Target: +10% coverage**

### 3.1 Create Test Fixtures
- [ ] Create standard test campaigns
- [ ] Create mock LLM response fixtures
- [ ] Create state transition fixtures

### 3.2 End-to-End Flows
- [ ] Test complete campaign creation flow
- [ ] Test multi-turn story progression
- [ ] Test state consistency across turns
- [ ] Test debug mode functionality

## Phase 4: API Route Testing (Priority: Medium)
**Target: +8% coverage**

### 4.1 main.py Route Tests
- [ ] Test `/api/campaigns` endpoints with Flask test client
- [ ] Test authentication middleware
- [ ] Test error responses
- [ ] Test CORS handling

### 4.2 Helper Function Tests
- [ ] Test `_handle_ask_state_command()`
- [ ] Test `_handle_update_state_command()`
- [ ] Test `_handle_legacy_migration()`
- [ ] Test `_apply_state_changes_and_respond()`

## Phase 5: Edge Cases and Error Paths (Priority: Low)
**Target: +5% coverage**

### 5.1 Error Handling
- [ ] Test malformed JSON handling
- [ ] Test missing required fields
- [ ] Test type mismatches
- [ ] Test boundary conditions

### 5.2 Performance Tests
- [ ] Test large state handling
- [ ] Test context truncation
- [ ] Test concurrent access patterns

## Implementation Strategy

### Quick Wins (Week 1)
1. Create mock fixtures for Firebase and Gemini
2. Add tests for all public methods in game_state.py
3. Test error paths in existing code

### Medium Effort (Week 2-3)
1. Build comprehensive integration tests
2. Add Flask route testing with test client
3. Test complex state transitions

### Long Term (Month 2)
1. Add performance benchmarks
2. Create property-based tests for state operations
3. Add mutation testing to verify test quality

## Success Metrics
- [ ] 80%+ overall test coverage
- [ ] All critical paths have tests
- [ ] CI/CD runs full test suite in < 5 minutes
- [ ] No flaky tests
- [ ] Clear documentation for running tests

## Tools and Infrastructure
- **Coverage.py**: Track Python code coverage
- **pytest-cov**: Better pytest integration
- **pytest-mock**: Simplified mocking
- **responses**: Mock HTTP requests
- **freezegun**: Mock time-based operations

## Notes
- Prioritize testing business logic over boilerplate
- Focus on behavior, not implementation
- Keep tests fast and deterministic
- Use dependency injection to improve testability
