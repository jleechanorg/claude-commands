# Unit Test Coverage Improvement Plan - Detailed Milestones

## Overview
This scratchpad outlines a comprehensive plan to improve unit test coverage from the current 32% to 80%+ with specific milestones, deliverables, and success metrics.

## Current State Analysis (As of 2025-07-03)

### Coverage Baseline
- **Overall Coverage**: 32%
- **Key Files**:
  - `firestore_service.py`: 50% (needs +30%)
  - `gemini_service.py`: 27% (needs +53%)  
  - `game_state.py`: 15% (needs +65%)
  - `main.py`: <10% (needs +70%)

### Existing Test Infrastructure
- **Total Test Files**: 76 (excluding manual tests)
- **Existing Coverage**:
  - 39 tests already cover game_state functionality
  - 32 tests already cover gemini service
  - 23 tests already cover firestore service
- **Test Framework**: pytest with pytest-cov
- **CI/CD**: GitHub Actions with coverage reporting
- **Testing Tools Available**: pytest-mock, responses, freezegun
- **Environment**: TESTING=true for faster AI models

## Milestone Plan

### Milestone 1: Foundation & Quick Wins (Week 1)
**Target Coverage: 32% → 45% (+13%)**

#### Deliverables
1. **Enhance Existing Mock Infrastructure**
   - [ ] Review and consolidate existing mocks in 76 test files
   - [ ] Create centralized `tests/fixtures/` directory
   - [ ] Extract reusable patterns from existing tests
   - [ ] Standardize mock usage across all tests
   - [ ] Update `conftest.py` with shared fixtures

2. **Fill Coverage Gaps in Tested Files**
   - [ ] Identify untested methods in already-tested modules
   - [ ] Add tests for error paths in existing test files
   - [ ] Test edge cases not covered by existing tests
   - [ ] Focus on increasing coverage in files already at 20-40%

3. **Documentation**
   - [ ] Document existing test patterns
   - [ ] Create testing best practices from current tests
   - [ ] Add coverage tracking dashboard

#### Success Metrics
- Existing tests refactored to use shared fixtures
- 10-15 new test methods added to existing files
- Coverage increased to 45%
- No increase in test execution time

### Milestone 2: Core Business Logic (Week 2-3)
**Target Coverage: 45% → 65% (+20%)**

#### Deliverables
1. **Enhance GameState Coverage (39 existing tests)**
   - [ ] Review gaps in existing game_state tests
   - [ ] Add missing tests for untested methods
   - [ ] Test complex state merge scenarios
   - [ ] Test all error conditions and edge cases
   - [ ] Improve existing tests with better assertions
   - [ ] Focus on the 85% uncovered code in game_state.py

2. **Complete Entity Management Coverage**
   - [ ] Build on existing entity tests
   - [ ] Test entity relationship management
   - [ ] Test bulk entity operations
   - [ ] Test entity state consistency
   - [ ] Add parametrized tests for all entity types

3. **Combat System Enhancement**
   - [ ] Extend existing combat tests
   - [ ] Test combat with multiple participants
   - [ ] Test special combat conditions
   - [ ] Test combat history tracking
   - [ ] Add integration tests for combat flow

#### Success Metrics
- `game_state.py` coverage: 15% → 70% (+55%)
- Build on existing 39 tests, add 20-30 new ones
- All critical paths have tests
- Reuse existing test infrastructure

### Milestone 3: Service Layer Testing (Week 4-5)
**Target Coverage: 65% → 75% (+10%)**

#### Deliverables
1. **Enhance Gemini Service Coverage (32 existing tests)**
   - [ ] Review gaps in existing gemini tests (73% uncovered)
   - [ ] Test PromptBuilder class thoroughly
   - [ ] Test all model cycling scenarios
   - [ ] Test rate limiting and quotas
   - [ ] Test streaming responses
   - [ ] Focus on untested helper methods

2. **Complete Firestore Coverage (23 existing tests)**
   - [ ] Review gaps in existing firestore tests (50% covered)
   - [ ] Test MissionHandler class completely
   - [ ] Test complex merge scenarios
   - [ ] Test batch operations
   - [ ] Test transaction rollbacks
   - [ ] Add tests for all error paths

3. **Service Integration Testing**
   - [ ] Build on existing integration patterns
   - [ ] Test cross-service data flow
   - [ ] Test failure cascades
   - [ ] Mock external dependencies consistently

#### Success Metrics
- `gemini_service.py`: 27% → 70% (+43%)
- `firestore_service.py`: 50% → 80% (+30%)
- Leverage existing 55 service tests
- Add 15-20 focused test methods

### Milestone 4: API & Routes (Week 6)
**Target Coverage: 75% → 82% (+7%)**

#### Deliverables
1. **Flask Route Tests**
   - [ ] Test all `/api/campaigns` endpoints
   - [ ] Test authentication middleware
   - [ ] Test error response formatting
   - [ ] Test CORS handling
   - [ ] Test request validation

2. **Command Handlers**
   - [ ] Test GOD mode commands
   - [ ] Test debug mode commands
   - [ ] Test state update commands
   - [ ] Test export functionality

3. **End-to-End Flows**
   - [ ] Test campaign creation flow
   - [ ] Test story progression flow
   - [ ] Test state persistence flow

#### Success Metrics
- `main.py` coverage > 70%
- All API endpoints tested
- Response contracts validated
- No integration test failures

### Milestone 5: Edge Cases & Polish (Week 7)
**Target Coverage: 82% → 85%+ (+3%)**

#### Deliverables
1. **Edge Case Coverage**
   - [ ] Test malformed input handling
   - [ ] Test boundary conditions
   - [ ] Test race conditions
   - [ ] Test resource exhaustion

2. **Performance Tests**
   - [ ] Test large state handling
   - [ ] Test context window limits
   - [ ] Test response time SLAs
   - [ ] Test memory usage

3. **Quality Improvements**
   - [ ] Add property-based tests
   - [ ] Add mutation testing
   - [ ] Improve test naming
   - [ ] Add test categories

#### Success Metrics
- Overall coverage > 85%
- All edge cases documented
- Performance benchmarks established
- Zero flaky tests

## Implementation Strategy

### Phase 1: Setup (Day 1-2)
1. Create test infrastructure directories
2. Implement core mock fixtures
3. Set up coverage reporting
4. Create initial test templates

### Phase 2: Parallel Development (Day 3-30)
1. Assign developers to specific modules
2. Daily coverage tracking
3. Weekly milestone reviews
4. Continuous integration updates

### Phase 3: Integration (Day 31-35)
1. Merge all test branches
2. Run full test suite
3. Fix any conflicts
4. Update documentation

### Tools & Best Practices

#### Required Tools
```bash
# Install test dependencies
pip install pytest-cov pytest-mock responses freezegun hypothesis pytest-benchmark
```

#### Testing Patterns
1. **Arrange-Act-Assert** pattern for all tests
2. **Given-When-Then** for integration tests
3. **One assertion per test** when possible
4. **Descriptive test names** that explain the scenario

#### Mock Strategy
```python
# Example mock pattern
@pytest.fixture
def mock_firestore():
    with patch('firestore_service.db') as mock_db:
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection
        yield mock_db

def test_save_game_state(mock_firestore):
    # Test implementation
```

## Success Criteria

### Technical Metrics
- [ ] Overall test coverage ≥ 85%
- [ ] Critical path coverage = 100%
- [ ] Test execution time < 5 minutes
- [ ] Zero flaky tests
- [ ] All tests pass in CI/CD

### Quality Metrics
- [ ] Clear test documentation
- [ ] Consistent naming conventions
- [ ] Reusable test fixtures
- [ ] Maintainable test code
- [ ] Good error messages

### Business Value
- [ ] Reduced bug escape rate
- [ ] Faster development cycles
- [ ] Improved code confidence
- [ ] Better refactoring safety
- [ ] Clearer system behavior

## Risk Mitigation

### Identified Risks
1. **External dependency mocking complexity**
   - Mitigation: Create comprehensive fixture library
   
2. **Test execution time increase**
   - Mitigation: Parallelize tests, use test categories

3. **Flaky test introduction**
   - Mitigation: No sleep statements, deterministic mocks

4. **Coverage gaming**
   - Mitigation: Focus on meaningful tests, not just lines

## Next Steps

1. Review and approve this plan
2. Create tracking tickets for each milestone
3. Assign team members to milestones
4. Set up daily coverage tracking
5. Schedule weekly review meetings

## Appendix: Coverage Commands

```bash
# Run tests with coverage
TESTING=true vpython -m pytest --cov=. --cov-report=html

# Run specific module tests
TESTING=true vpython -m pytest tests/test_game_state.py -v

# Generate coverage report
TESTING=true vpython -m pytest --cov=. --cov-report=term-missing

# Run tests in parallel
TESTING=true vpython -m pytest -n auto

# Run only unit tests (exclude integration)
TESTING=true vpython -m pytest -m "not integration"
```

---

**Created**: 2025-07-03
**Author**: AI Assistant
**Status**: Draft - Ready for Review

## Update Log

### 2025-07-03 - Excluded Manual Tests
- Updated `run_tests.sh` to exclude `./tests/manual_tests/*` from automatic test discovery
- Updated `.github/workflows/test.yml` to exclude manual_tests from CI/CD pipeline
- Ensures manual tests are not run automatically in local or CI environments
- Manual tests can still be run explicitly when needed