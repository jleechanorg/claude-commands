# TestServiceProvider Framework

A service abstraction layer that enables seamless switching between mock and real services for testing.

## Overview

This framework provides a unified interface for accessing services (Firestore, Gemini, Auth) in tests, allowing you to easily switch between mock services (for fast unit tests) and real services (for integration testing) without changing your test code.

## Quick Start

```python
from mvp_site.testing_framework import get_current_provider

def test_something():
    provider = get_current_provider()
    firestore = provider.get_firestore()
    gemini = provider.get_gemini()

    # Your test logic here - works with mock or real services
    campaigns = firestore.get_campaigns_for_user("test_user")
    response = gemini.generate_content("Test prompt")

    # Cleanup happens automatically
    provider.cleanup()
```

## Service Modes

### Mock Mode (Default)
```bash
# Uses fast in-memory mock services
export TEST_MODE=mock
```

### Real Mode
```bash
# Uses actual services with test isolation
export TEST_MODE=real
export TEST_GEMINI_API_KEY=your_api_key
export TEST_FIRESTORE_PROJECT=your_test_project
```

### Capture Mode
```bash
# Uses real services and can capture responses
export TEST_MODE=capture
export TEST_GEMINI_API_KEY=your_api_key
export TEST_FIRESTORE_PROJECT=your_test_project
```

## API Reference

### Service Provider Interface

All providers implement the `TestServiceProvider` interface:

```python
class TestServiceProvider(ABC):
    def get_firestore(self) -> Any: ...
    def get_gemini(self) -> Any: ...
    def get_auth(self) -> Any: ...
    def cleanup(self) -> None: ...

    @property
    def is_real_service(self) -> bool: ...
```

### Factory Functions

```python
from mvp_site.testing_framework import (
    get_service_provider,      # Create provider for specific mode
    get_current_provider,      # Get global provider instance
    set_service_provider,      # Set global provider
    reset_global_provider      # Reset global state
)

# Create specific provider
provider = get_service_provider('mock')  # or 'real', 'capture'

# Use global provider (recommended for most tests)
provider = get_current_provider()
```

## Configuration

### Real Service Configuration

Required environment variables for real mode:
- `TEST_GEMINI_API_KEY`: Your Gemini API key
- `TEST_FIRESTORE_PROJECT`: Test Firestore project ID (optional, defaults to 'worldarchitect-test')

### Test Isolation

Real services use test-specific collections:
- Original: `campaigns` → Test: `test_campaigns`
- Original: `game_states` → Test: `test_game_states`

All test data is automatically cleaned up after test execution.

## Directory Structure

```
mvp_site/testing_framework/
├── __init__.py                 # Main exports
├── service_provider.py         # Abstract interface
├── mock_provider.py           # Mock implementation
├── simple_mock_provider.py    # Fallback mock (no dependencies)
├── real_provider.py           # Real service implementation
├── factory.py                 # Provider factory
├── config.py                  # Configuration management
└── tests/                     # Unit tests
    ├── test_mock_provider.py
    ├── test_real_provider.py
    └── test_factory.py
```

## Testing the Framework

```bash
# Run framework validation
python3 test_framework_validation.py

# Run integration demo
python3 test_integration_demo.py

# Run simple component test
python3 simple_test.py
```

## Usage Patterns

### Basic Test Setup
```python
def setUp(self):
    self.provider = get_current_provider()

def tearDown(self):
    self.provider.cleanup()
```

### Mode-Specific Tests
```python
@unittest.skipIf(not get_current_provider().is_real_service, "Requires real services")
def test_real_api_integration(self):
    # Test that only runs with real services
    pass
```

### Service Switching
```python
def test_with_different_modes():
    # Test with mock
    mock_provider = get_service_provider('mock')
    # ... test logic

    # Test with real (if configured)
    if os.getenv('TEST_GEMINI_API_KEY'):
        real_provider = get_service_provider('real')
        # ... same test logic
```

## Implementation Notes

### Mock Provider Fallback

The framework includes a fallback mechanism for mock services:
- Primary: Uses existing `MockFirestoreClient` and `MockGeminiClient`
- Fallback: Uses `SimpleMockServiceProvider` if imports fail

This ensures the framework works even if there are dependency issues with the existing mock services.

### Test Data Cleanup

Real providers automatically track and cleanup test collections:
```python
provider = RealServiceProvider()
provider.track_test_collection('campaigns')  # Will cleanup test_campaigns
provider.cleanup()  # Deletes all tracked test data
```

### Error Handling

The framework validates configuration early:
```python
# Will raise ValueError if TEST_GEMINI_API_KEY is missing
provider = RealServiceProvider()
```

## Future Enhancements

- Integration with test runners (`./run_tests.sh --real`)
- Response capture and replay for deterministic testing
- Performance benchmarking between mock and real services
- Additional service providers (Auth, Storage, etc.)
