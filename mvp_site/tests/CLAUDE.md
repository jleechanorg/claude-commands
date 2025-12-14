# MVP Site Testing Architecture

This document inherits from the root project documentation. Please refer to `../../CLAUDE.md` for project-wide conventions and guidelines.

## Overview
The `mvp_site/tests/` directory contains a comprehensive testing suite with 197 Python test files implementing unit, integration, and security tests. The testing infrastructure follows a mock-first approach with Firebase service simulations and CI-ready execution patterns.

## Test Categories

### Integration Tests
End-to-end workflow and service interaction testing:
- `test_integration.py` - Full application flow testing with real API endpoints
- `test_api_integration.py` - REST API endpoint integration validation
- `test_firebase_integration.py` - Firestore database operation workflows
- `test_auth_integration.py` - Authentication flow validation
- `test_campaign_integration.py` - Campaign creation and management workflows

### Unit Tests
Core business logic and component testing:
- `test_models.py` - Data model validation and serialization
- `test_utils.py` - Utility function testing
- `test_handlers.py` - Request handler logic validation
- `test_validators.py` - Input and data validation functions
- `test_services.py` - Service layer business logic

### Security Tests
Defensive security and permission validation:
- `test_security.py` - Access control and input sanitization
- `test_auth_security.py` - Authentication boundary testing
- `test_data_security.py` - Data exposure and validation security
- `test_xss_protection.py` - Cross-site scripting prevention

## Mock Infrastructure
Testing infrastructure uses comprehensive service mocking for isolated testing:

### Authentication Mocks
- `fake_auth.py` - Simulated Firebase Authentication service with user management
- `mock_user_service.py` - User registration and profile management simulation
- `test_auth_middleware.py` - Authentication pipeline and middleware testing

### Database Mocks
- `fake_firestore.py` - Complete Firestore database operation mocks with collections
- `fake_gemini.py` - Gemini AI service mocking for prompt testing
- `mock_data_store.py` - Data persistence layer simulation with state management

### External Service Mocks
- `mock_email_service.py` - Email delivery and notification simulation
- `fake_storage.py` - Cloud storage service mocks for file operations
- `mock_firebase_admin.py` - Firebase Admin SDK simulation for system operations

## Testing Patterns

### Mock-First Development
All tests utilize mock services before hitting real infrastructure:
```python
# Example pattern from test_integration.py
from tests.fake_firestore import MockFirestore
from tests.fake_auth import MockAuth

def test_user_registration():
    with patch('services.firestore_service', MockFirestore()):
        with patch('services.auth_service', MockAuth()):
            # Test logic with mocked dependencies
            response = client.post('/api/register', json=test_data)
            assert response.status_code == 200
```

### CI Simulation Environment
Tests run in isolated CI environments by default:
- `conftest.py` - pytest configuration and fixtures for test setup
- `test_runner.py` - Test execution coordination and reporting
- Environment variables control mock behavior and test mode selection
- Automatic CI simulation prevents external dependency failures

### Comprehensive Coverage
Testing targets 95%+ code coverage with systematic validation:
- `test_coverage_validation.py` - Coverage reporting and gap analysis
- Path-specific test files for edge case coverage
- Security boundary testing for all public endpoints
- Mock service behavior validation against real service contracts

## Execution Guidelines

### Local Testing (Recommended Patterns)
```bash
# Run all tests from project root
TESTING=true vpython mvp_site/tests/test_integration.py

# Run specific test categories
TESTING=true vpython mvp_site/tests/test_security.py
TESTING=true vpython mvp_site/tests/test_models.py

# Run with coverage reporting
./run_tests.sh --coverage
```

### CI Testing (Automated Environment)
```bash
# Default CI simulation mode
./run_tests.sh                           # Runs with CI simulation

# Explicit CI simulation
./run_tests.sh --ci-sim                  # Force CI environment simulation

# Local mode (full environment)
./run_tests.sh --no-ci-sim              # Disable CI simulation
```

### Mock Mode Testing
```bash
# UI testing with mock backend
./run_ui_tests.sh mock                  # Playwright tests with mocked APIs

# Full integration with real services
./run_ui_tests.sh real                  # Playwright tests with live backend
```

## Test Infrastructure Components

### Core Testing Utilities
Located in testing support files:
- `test_client_factory.py` - Flask test client configuration
- `test_data_generators.py` - Dynamic test data generation
- `assertion_helpers.py` - Custom assertion utilities for complex validations

### Mock Service Validation
- `mock_service_contracts.py` - Ensures mock services match real service behavior
- `mock_data_integrity.py` - Validates mock data consistency and realism
- `mock_performance_simulation.py` - Simulates realistic service response times

### Security Testing Framework
- `security_test_base.py` - Base class for security testing patterns
- `auth_boundary_testing.py` - Authentication and authorization boundary validation
- `input_sanitization_tests.py` - Comprehensive input validation and XSS prevention

## No Silent Test Skipping Policy

**CRITICAL RULE:** Tests must NEVER silently skip or short-circuit based on environment variables.

### The Three Valid Test States

Every test must exist in exactly ONE of these states:

| State | Behavior | Example |
|-------|----------|---------|
| **RUN** | Test executes with real or mocked dependencies | Normal test execution |
| **FAIL LOUDLY** | Test raises clear error explaining why it cannot run | `pytest.fail("Requires /special/path - see README")` |
| **MOCK** | Test uses mock/fake services when `TESTING=true` | `FakeFirestore`, `FakeLLMResponse` |

### Forbidden Patterns

These patterns create silent failures and are **BANNED**:

```python
# ❌ FORBIDDEN: Conditional early return
def test_api_integration():
    if not os.getenv("API_KEY"):
        return  # Silent skip - test appears to pass!

# ❌ FORBIDDEN: Module-level import that raises
try:
    import special_module
except ImportError:
    pass  # Test file may silently do nothing

# ❌ FORBIDDEN: Empty test body with conditional
def test_feature():
    if os.getenv("CI"):
        pass  # Does nothing in CI
```

### Required Patterns

```python
# ✅ CORRECT: Explicit skip with reason
@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="Requires GEMINI_API_KEY for live API testing"
)
def test_gemini_live_integration():
    # This test is visibly skipped with clear reason
    ...

# ✅ CORRECT: Mock when TESTING=true
def test_database_operation():
    # TESTING=true enables mock mode automatically
    with fake_firestore_context():
        result = db_service.query(...)
        assert result is not None

# ✅ CORRECT: Fail loudly if dependency missing
def test_requires_special_setup():
    if not os.path.exists("/special/path"):
        pytest.fail("Test requires /special/path - see README for setup")
```

### Test Collection Rules

1. **Test collection must NEVER fail** due to missing environment variables
2. All imports must be guarded or use conditional imports within test functions
3. Use `pytest.importorskip()` for optional dependencies
4. `TESTING=true` must enable mock mode for all external services

### Enforcement

- CI runs ALL tests - no silent exclusions
- Coverage reports should show tests as "skipped" (not "passed" with 0 assertions)
- Pre-commit hooks may validate test patterns when configured
- Code review should flag silent skip patterns for discussion

## Quality Standards and Compliance

### Test Coverage Requirements
- All new features require 100% test coverage
- Mock services must accurately simulate real service behavior
- Security tests are mandatory for all public endpoints
- Integration tests must validate complete user workflows

### Testing Best Practices
- Tests must be deterministic and repeatable
- Mock services should fail in realistic ways
- Test data must be isolated and not affect other tests
- Performance testing validates response time requirements

### CI/CD Integration
- All tests run automatically on pull requests
- Coverage reports generated for every commit
- Security tests block deployment if vulnerabilities detected
- Integration tests validate system behavior before release

## Common Testing Patterns

### Authentication Testing
```python
def test_protected_endpoint():
    # Test without authentication
    response = client.get('/api/protected')
    assert response.status_code == 401
    
    # Test with valid authentication
    with authenticated_user(test_user_id):
        response = client.get('/api/protected')
        assert response.status_code == 200
```

### Database Testing
```python
def test_campaign_creation():
    with fake_firestore_context():
        campaign_data = generate_test_campaign()
        result = campaign_service.create_campaign(campaign_data)
        assert result['success'] is True
        assert 'campaign_id' in result
```

## End-to-End Testing Philosophy

### Key Principle: Mock External APIs, Not Internal Logic

**CRITICAL:** When testing internal function logic (like `generate_content_with_tool_requests`), mock the **lowest-level API calls**, NOT the function you're testing. This ensures internal logic is exercised.

```python
# ❌ BAD: Mocking the entire function - internal logic NOT tested
with patch('provider.generate_content_with_tool_requests') as mock:
    mock.return_value = Mock(text='{"result": "test"}')
    # Bug in generate_content_with_tool_requests would NOT be caught!

# ✅ GOOD: Mock the low-level API call - internal logic IS tested
with patch('provider.generate_json_mode_content') as mock_api:
    # Phase 1: Return JSON response (may include tool_requests)
    mock_api.side_effect = [phase1_response, phase2_response]
    result = generate_content_with_tool_requests(...)
    # Now internal logic (parsing tool_requests, executing, Phase 2) is tested!
```

### Fake Implementations Over Mock Objects

From `README_END2END_TESTS.md`:
- Mock only **external APIs** (Firebase, Gemini API client)
- DON'T mock internal service functions
- Use `FakeLLMResponse` classes that return real Python data structures
- Avoids JSON serialization errors from `Mock()` objects

### Testing Multi-Phase Functions (JSON-First Architecture)

For functions with multiple phases (like JSON-first tool_requests):

1. **Mock the lowest-level API call** (e.g., `generate_json_mode_content`)
2. **Use `side_effect` for sequential responses** (Phase 1 JSON, Phase 2 with results)
3. **Verify intermediate data is passed correctly** between phases
4. **Check call arguments** to ensure history/context is preserved

```python
def test_tool_requests_passes_history_to_phase2():
    """Verify Phase 2 receives conversation history from Phase 1."""
    with patch('provider.generate_json_mode_content') as mock_api:
        # Phase 1: Return JSON with tool_requests
        phase1_response = create_json_response({
            "narrative": "Rolling...",
            "tool_requests": [{"tool": "roll_dice", "args": {"notation": "1d20"}}]
        })
        # Phase 2: Return final JSON (no tool_requests)
        phase2_response = create_json_response({"narrative": "You rolled 15!"})
        mock_api.side_effect = [phase1_response, phase2_response]

        result = generate_content_with_tool_requests(prompt, model, ...)

        # Verify Phase 2 was called with history including tool results
        phase2_call = mock_api.call_args_list[1]
        assert phase2_call.kwargs.get('prompt_contents') is not None  # History passed!
```

### Reference Files
- `fake_llm.py` - `FakeLLMResponse`, `FakePart` with `function_call` attribute
- `fake_firestore.py` - `FakeFirestoreClient`, `FakeFirestoreDocument`
- `README_END2END_TESTS.md` - Full philosophy documentation

See also: [../../CLAUDE.md](../../CLAUDE.md) for complete project protocols and development guidelines.