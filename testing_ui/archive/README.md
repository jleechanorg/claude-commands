# Browser Testing Directory (REAL Browsers Only!)

This directory contains REAL browser automation tests using Playwright.

## HARD RULE: NO HTTP SIMULATION

🚨 **CRITICAL**: This directory is for REAL BROWSER AUTOMATION ONLY!
- ✅ Use Playwright to control actual browsers
- ✅ Click real buttons, fill real forms, see real UI
- ❌ NO direct HTTP requests
- ❌ NO `requests` library
- ❌ NO API simulation

## Structure

- **Real Browser Tests**: Automate actual Chrome/Firefox browsers
- **Visual Tests**: Take screenshots, verify UI elements
- **User Journey Tests**: Complete end-to-end workflows as a real user would

## Key Difference from testing_http/

- **testing_ui/**: REAL browser automation (Playwright)
- **testing_http/**: Direct HTTP requests (requests library)

## Running Tests

### Browser Tests with Mock APIs (Safe, Free)
```bash
# From project root - run browser tests with mocked backend
python3 mvp_site/main.py testui

# Or directly
TESTING=true python3 testing_ui/run_all_browser_tests.py
```

### Browser Tests with Real APIs (DANGER: Costs Money!)
```bash
# From project root - run browser tests with real Firebase/Gemini
python3 mvp_site/main.py testuif

# Or directly with environment variable
TESTING=true REAL_APIS=true python3 testing_ui/run_all_browser_tests.py
```

## Test Files

### Current Browser Tests
- `test_campaign_creation_browser.py` - Campaign creation browser automation
- `test_campaign_creation_browser_v2.py` - Campaign creation v2 framework
- `test_continue_campaign_browser.py` - Campaign continuation automation
- `test_continue_campaign_browser_v2.py` - Campaign continuation v2 framework
- `test_god_mode_browser.py` - God mode UI automation
- `test_real_browser.py` - Main browser automation test suite
- `test_playwright_sample.py` - Playwright sample implementation
- `test_playwright_mock.py` - Playwright with mock APIs

### Legacy Files (for reference)
- `test_selenium_browser_legacy.py` - Legacy Selenium implementation
- `test_real_playwright_legacy.py` - Legacy Playwright test
- `test_final_real_browser_moved.py` - Moved from testing_http
- `test_real_browser_moved.py` - Moved from testing_http

### Test Runners
- `run_all_browser_tests.py` - Main browser test runner (supports mock/real APIs)
- `run_full_browser_tests.py` - Real API browser test runner with confirmation

### Supporting Infrastructure
- `browser_test_base.py` - Shared test framework for v2 tests
- `playwright_config.py` - Playwright configuration
- Various test documentation and analysis files

## Writing New Tests

Always use Playwright for browser automation:

```python
from playwright.sync_api import sync_playwright

def test_user_can_create_character():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set True for CI
        page = browser.new_page()

        # Navigate to the app
        page.goto("http://localhost:6006")

        # Click real buttons
        page.click("text=Create Character")

        # Fill real forms
        page.fill("#character-name", "Gandalf")

        # Assert real UI state
        assert page.is_visible("text=Character Created")

        browser.close()
```

## Important Notes

1. These tests use REAL browser automation
2. They test the FULL user experience, not just APIs
3. For HTTP/API testing, use `testing_http/` directory instead
4. Browser tests are slower but more realistic
5. Always verify UI elements are visible before interacting

## Test Coverage Summary

### Currently Implemented:
1. **Campaign Creation** (Full coverage)
   - Browser automation v1 ✅ (`test_campaign_creation_browser.py`)
   - Browser automation v2 ✅ (`test_campaign_creation_browser_v2.py`)

2. **Campaign Continuation** (Full coverage)
   - Browser automation v1 ✅ (`test_continue_campaign_browser.py`)
   - Browser automation v2 ✅ (`test_continue_campaign_browser_v2.py`)

3. **God Mode** (Partial coverage)
   - Browser automation ✅ (`test_god_mode_browser.py`)
   - Needs integration with v2 framework ⚠️

4. **General Browser Testing**
   - Main test suite ✅ (`test_real_browser.py`)
   - Playwright samples ✅ (`test_playwright_sample.py`, `test_playwright_mock.py`)

### Authentication:
- Test mode bypass implemented for both backend and frontend
- URL parameter: `?test_mode=true&test_user_id=<user-id>`
- Backend header: `X-Test-Bypass-Auth: true`

### Red/Green Testing:
All test infrastructure has been validated with red/green methodology to ensure proper failure detection.
