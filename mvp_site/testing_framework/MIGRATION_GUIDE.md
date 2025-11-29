# Real-Mode Testing Framework Migration Guide

This guide shows how to update existing tests to support dual-mode operation (mock and real services) using the Real-Mode Testing Framework.

## Quick Start

### Option 1: Minimal Changes (Recommended)

Add this single import to your existing test file:

```python
from testing_framework.integration_utils import DualModeTestMixin

class YourExistingTest(DualModeTestMixin, unittest.TestCase):
    # All existing test methods work unchanged
    def test_something(self):
        # Your existing test code here
        pass
```

### Option 2: Using Fixtures (For new tests)

```python
from testing_framework.fixtures import BaseTestCase

class YourNewTest(BaseTestCase):
    def test_something(self):
        # Access services via self.firestore, self.gemini, self.auth
        result = self.firestore.get_document('test/doc')
        assert result is not None
```

## Test Modes

The framework supports three modes controlled by the `TEST_MODE` environment variable:

- `TEST_MODE=mock` (default): Uses mock services
- `TEST_MODE=real`: Uses real services (costs money, requires API keys)
- `TEST_MODE=capture`: Uses real services with data capture for analysis

## Migration Patterns

### Pattern 1: Class-Level Migration

**Before:**
```python
class TestCharacterCreation(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_create_character(self):
        with patch('main.llm_service') as mock_gemini:
            mock_gemini.generate_character.return_value = {"name": "Test"}
            # test logic...
```

**After:**
```python
from testing_framework.integration_utils import DualModeTestMixin

class TestCharacterCreation(DualModeTestMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()  # Initializes dual-mode support
        self.app = create_app()
        self.client = self.app.test_client()

    def test_create_character(self):
        # Automatically works with mock or real services
        with smart_patch(llm_service=None):
            # In mock mode: uses framework mocks
            # In real mode: no patching, uses real services
            # test logic unchanged...
```

### Pattern 2: Method-Level Migration

**Before:**
```python
def test_api_call(self):
    with patch('main.firestore_service') as mock_fs:
        mock_fs.get_document.return_value = {'test': True}
        # test logic...
```

**After:**
```python
from testing_framework.integration_utils import dual_mode_test, smart_patch

@dual_mode_test
def test_api_call(self):
    with smart_patch(firestore_service=None):
        # Works with both mock and real services
        # test logic unchanged...
```

### Pattern 3: Gradual Migration

For tests that need gradual migration:

```python
from testing_framework.fixtures import get_test_client_for_mode

class ExistingTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

        # Add dual-mode support gradually
        self.services = get_test_client_for_mode()
        self.is_real = self.services['is_real']

    def tearDown(self):
        # Always cleanup
        if hasattr(self, 'services'):
            self.services['provider'].cleanup()

    def test_something(self):
        if self.is_real:
            # Real mode - no mocking
            self._run_test_logic()
        else:
            # Mock mode - use existing patches
            with patch('main.llm_service', self.services['gemini']):
                self._run_test_logic()
```

## Service Access Patterns

### Firestore

**Mock Mode:**
```python
# Mock Firestore that simulates document operations
firestore = self.test_firestore
doc_ref = firestore.collection('test').document('doc1')
doc_ref.set({'data': 'test'})
result = doc_ref.get()
```

**Real Mode:**
```python
# Real Firestore (same API, actual database)
firestore = self.test_firestore
doc_ref = firestore.collection('test_real').document('doc1')
doc_ref.set({'data': 'test'})
result = doc_ref.get()  # Actually calls Firebase
```

### Gemini

**Mock Mode:**
```python
# Mock Gemini that returns predefined responses
gemini = self.test_gemini
response = gemini.generate_content("test prompt")
# Returns structured mock response
```

**Real Mode:**
```python
# Real Gemini API (same call, actual API)
gemini = self.test_gemini
response = gemini.generate_content("test prompt")
# Actually calls Google Gemini API
```

## Safety Features

### Resource Limits

Real mode tests automatically include safety limits:

```python
class TestWithLimits(BaseTestCase):
    def test_expensive_operation(self):
        if self.is_real:
            # Limit API calls in real mode
            for i in range(3):  # Max 3 calls
                result = self.gemini.generate_content("prompt")
        else:
            # No limits in mock mode
            for i in range(100):
                result = self.gemini.generate_content("prompt")
```

### Automatic Cleanup

Resources are automatically cleaned up:

```python
def test_creates_data(self):
    # Framework automatically cleans up test data
    if self.is_real:
        # Uses unique collection names: test_data_1638123456
        collection = self.test_firestore.collection('test_data')
    else:
        # Uses simple names: test_data
        collection = self.test_firestore.collection('test_data')

    # Data is cleaned up automatically after test
```

### Test Isolation

Tests are isolated in real mode:

```python
class TestIsolation(BaseTestCase):
    def test_user_data(self):
        # Each test gets isolated environment
        if self.is_real:
            # Uses test-specific user ID: test_user_123_1638123456
            user_id = f"test_user_{self._testMethodName}_{int(time.time())}"
        else:
            # Uses simple ID: test_user_123
            user_id = "test_user_123"
```

## Decorators

### @skip_in_real_mode

Skip tests that don't work with real services:

```python
@skip_in_real_mode("Uses hardcoded test data")
def test_mock_only_scenario(self):
    # This test only runs in mock mode
    pass
```

### @real_mode_only

Skip tests that need real services:

```python
@real_mode_only("Tests actual API integration")
def test_real_integration(self):
    # This test only runs in real mode
    pass
```

## Running Tests

### Mock Mode (Default)
```bash
# All tests run with mock services
./run_tests.sh

# Specific test with mocks
python -m pytest test_character_setting_backend.py -v
```

### Real Mode
```bash
# All tests run with real services (requires API keys)
TEST_MODE=real ./run_tests.sh

# Specific test with real services
TEST_MODE=real python -m pytest test_character_setting_backend.py -v
```

### Capture Mode
```bash
# Run with real services and capture data for analysis
TEST_MODE=capture ./run_tests.sh
```

## Best Practices

### 1. Start with Minimal Changes

Use `DualModeTestMixin` for existing tests:

```python
class ExistingTest(DualModeTestMixin, unittest.TestCase):
    # No other changes needed initially
```

### 2. Use Smart Patching

Replace manual patches with `smart_patch`:

```python
# Instead of:
with patch('main.llm_service') as mock_gemini:
    # setup mock...

# Use:
with smart_patch(llm_service=None):
    # Works in both modes
```

### 3. Add Resource Limits

Protect against runaway costs in real mode:

```python
def test_bulk_operation(self):
    max_items = 3 if self.is_real else 100
    for i in range(max_items):
        # Process items...
```

### 4. Use Descriptive Test Names

Include mode information in test output:

```python
def test_character_creation(self):
    mode = "REAL" if self.is_real else "MOCK"
    print(f"Testing character creation with {mode} services")
```

## Common Issues

### Import Errors

If you get import errors:

```python
# Add this at the top of test files
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

### Mock Setup

The framework handles mock setup automatically. Remove manual mock configuration:

```python
# Remove this:
mock_response = MagicMock()
mock_response.text = "test response"
mock_gemini.generate.return_value = mock_response

# Framework handles this automatically
```

### Service Dependencies

Tests automatically get the right services:

```python
def test_service_integration(self):
    # These work in both modes
    firestore = self.test_firestore
    gemini = self.test_gemini
    auth = self.test_auth
```

## Validation

Test your migration:

```bash
# Validate framework setup
python -c "from testing_framework.integration_utils import validate_test_environment; validate_test_environment()"

# Run specific test in both modes
python -m pytest test_file.py::test_method -v
TEST_MODE=real python -m pytest test_file.py::test_method -v
```

## Examples

See these files for complete examples:

- `testing_framework/migration_examples.py` - Before/after patterns
- `test_character_setting_backend.py` - Updated real test
- `testing_framework/fixtures.py` - Pytest fixtures
- `testing_framework/integration_utils.py` - Helper utilities

## Support

For questions or issues with migration:

1. Check existing examples in `testing_framework/migration_examples.py`
2. Validate your environment with `validate_test_environment()`
3. Start with minimal changes using `DualModeTestMixin`
4. Gradually adopt more framework features as needed
