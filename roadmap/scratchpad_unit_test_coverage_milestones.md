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
- **Total Test Files**: 78
- **Test Framework**: pytest with pytest-cov
- **CI/CD**: GitHub Actions with coverage reporting
- **Testing Tools Available**: pytest-mock, responses, freezegun
- **Environment**: TESTING=true for faster AI models

## Milestone Plan

### Milestone 1: Foundation & Quick Wins (Week 1)
**Target Coverage: 32% → 45% (+13%)**

#### Deliverables
1. **Mock Infrastructure Setup**
   - [ ] Create `tests/fixtures/` directory structure
   - [ ] Implement `firebase_fixtures.py` with reusable Firestore mocks
   - [ ] Implement `gemini_fixtures.py` with API response mocks
   - [ ] Implement `flask_fixtures.py` for app context mocks
   - [ ] Create `conftest.py` with shared pytest fixtures

2. **Low-Hanging Fruit Tests**
   - [ ] Test all constant definitions and enums
   - [ ] Test utility functions without dependencies
   - [ ] Test data validation functions
   - [ ] Test error handling paths

3. **Documentation**
   - [ ] Create `tests/README.md` with testing guidelines
   - [ ] Document mock usage patterns
   - [ ] Add coverage badge to main README

#### Success Metrics
- All mock fixtures working and documented
- 15+ new test files created
- Coverage increased to 45%
- CI pipeline remains under 5 minutes

### Milestone 2: Core Business Logic (Week 2-3)
**Target Coverage: 45% → 65% (+20%)**

#### Deliverables
1. **GameState Module (Priority: Critical)**
   - [ ] Test `GameState.from_dict()` with 20+ state variations
   - [ ] Test `GameState.to_dict()` round-trip serialization
   - [ ] Test all entity management methods
   - [ ] Test combat system state transitions
   - [ ] Test mission tracking logic
   - [ ] Test state migration scenarios

2. **Entity Management Tests**
   - [ ] Test entity creation and validation
   - [ ] Test entity removal (`__DELETE__` token)
   - [ ] Test companion state management
   - [ ] Test NPC state persistence
   - [ ] Test entity location tracking

3. **Combat System Tests**
   - [ ] Test combat initialization
   - [ ] Test turn order calculation
   - [ ] Test damage application
   - [ ] Test combat cleanup logic
   - [ ] Test combat state persistence

#### Success Metrics
- `game_state.py` coverage > 70%
- All critical paths have tests
- No flaky tests introduced
- 30+ new test files

### Milestone 3: Service Layer Testing (Week 4-5)
**Target Coverage: 65% → 75% (+10%)**

#### Deliverables
1. **Gemini Service Tests**
   - [ ] Test prompt building logic
   - [ ] Test model selection and fallback
   - [ ] Test token counting and budgets
   - [ ] Test response parsing
   - [ ] Test error handling and retries
   - [ ] Test debug mode integration

2. **Firestore Service Tests**
   - [ ] Test document CRUD operations
   - [ ] Test state merging logic
   - [ ] Test transaction handling
   - [ ] Test query operations
   - [ ] Test error recovery
   - [ ] Test data migrations

3. **Integration Points**
   - [ ] Test service interactions
   - [ ] Test state synchronization
   - [ ] Test concurrent access patterns

#### Success Metrics
- `gemini_service.py` coverage > 70%
- `firestore_service.py` coverage > 80%
- All API calls properly mocked
- Test execution time < 3 minutes

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