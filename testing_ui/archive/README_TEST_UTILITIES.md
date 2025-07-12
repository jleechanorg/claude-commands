# UI Test Utilities Guide

This directory contains several utility modules to reduce code duplication and standardize UI testing patterns.

## Available Utilities

### 1. `screenshot_utils.py`
**Purpose**: Standardized screenshot handling
- `take_screenshot(page, test_name, description)` - Take and save screenshots to `/tmp/worldarchitectai/browser/`
- `get_screenshot_path(test_name, description)` - Get standardized paths
- `cleanup_old_screenshots(test_name)` - Remove old screenshots

### 2. `test_ui_util.py`
**Purpose**: Core browser test utilities
- `setup_browser()` - Standard browser configuration
- `navigate_to_page()` - Navigation with test mode parameters
- `enable_console_logging()` - Console output capture
- `capture_api_request()` - API request interception
- `fill_wizard_step1()` - Campaign wizard helpers
- `run_ui_test()` - Test execution wrapper

### 3. `test_data_utils.py`
**Purpose**: Test data and mock server utilities
- `MockAPIServer` - Context manager for mock API server
- `generate_test_campaign()` - Create test campaign data
- `generate_mock_structured_response()` - Create mock API responses
- `DEFAULT_TEST_CAMPAIGNS` - Common test campaign data
- `TEST_USERS` - Standard test user configurations

### 4. `test_ui_helpers.py`
**Purpose**: Additional UI interaction helpers
- `wait_and_click()` - Click with error handling
- `try_multiple_selectors()` - Try multiple selectors until one works
- `verify_view_active()` - Check if a view is active
- `fill_form_field()` - Fill forms with verification
- `extract_structured_fields()` - Extract common response fields
- `wait_for_text_to_appear()` - Wait for specific text

### 5. `browser_test_base.py` 
**Purpose**: Base class for browser tests (for tests that extend BrowserTestBase)
- `BrowserTestBase` - Base class with setup/teardown
- `FlaskServerManager` - Manages test server lifecycle
- Built-in screenshot handling
- Test mode activation
- Console error tracking

**Note**: The functionality from `browser_test_helpers.py` has been merged into:
- `screenshot_utils.py` - Enhanced screenshot capabilities with element selection
- `test_ui_helpers.py` - Added `navigate_to_test_game()` and `capture_structured_fields_sequence()`
- `test_data_utils.py` - Added `create_test_campaign()` function

## Usage Examples

### Basic UI Test with Utilities
```python
from test_ui_util import run_ui_test, navigate_to_page, fill_wizard_step1
from screenshot_utils import take_screenshot

def my_test(page, test_name):
    # Navigate with test mode
    navigate_to_page(page, "new-campaign", port=6008)
    
    # Take screenshot
    take_screenshot(page, test_name, "initial_state")
    
    # Fill wizard
    fill_wizard_step1(page, "Test Campaign", "custom", 
                     "Test Character", "Test Setting")
    
    # ... rest of test

# Run the test
run_ui_test(my_test, "my_campaign_test")
```

### Mock API Test
```python
from test_data_utils import MockAPIServer, generate_test_campaign

with MockAPIServer(port=8086) as server:
    # Set custom response
    server.set_response("/api/custom", {"result": "success"})
    
    # Run test against mock server
    # ...
    
    # Check what requests were made
    print(f"Requests made: {server.requests}")
```

### Using Base Class
```python
from browser_test_base import BrowserTestBase

class MyTest(BrowserTestBase):
    def __init__(self):
        super().__init__("My Test Name")
    
    def run_test(self, page):
        # Your test logic here
        self.take_screenshot(page, "test_screenshot")
        return True

# Execute
test = MyTest()
test.execute()
```

## Best Practices

1. **Use utilities instead of duplicating code** - Don't reimplement browser setup, use the utilities
2. **Consistent screenshot naming** - Use the screenshot utilities for consistent paths
3. **Mock when possible** - Use MockAPIServer for faster, more reliable tests
4. **Leverage helpers** - Use wait_and_click, try_multiple_selectors, etc. for robust tests
5. **Extend base class** - For complex tests, extend BrowserTestBase

## Migration Guide

To update existing tests:

1. Replace manual browser setup with `setup_browser()` or extend `BrowserTestBase`
2. Replace hardcoded screenshot paths with `take_screenshot()`
3. Replace manual navigation with `navigate_to_page()`
4. Use `MockAPIServer` instead of manual HTTP servers
5. Use helper functions for common operations