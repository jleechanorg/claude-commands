# Testing Structure Summary

## Directory Organization

### testing_ui/ (Real Browser Automation Only)
- **Purpose**: REAL browser automation using Playwright
- **Technology**: Playwright, Selenium
- **What it does**: Launches actual browsers, clicks real buttons, fills real forms
- **Commands**:
  - `/testui` - Browser tests with mock APIs (free)
  - `/testuif` - Browser tests with REAL APIs (costs money)
- **Files**:
  - `test_campaign_creation_browser.py` - Real browser test for campaign creation
  - `test_real_browser.py` - Main browser automation suite
  - `run_all_browser_tests.py` - Runner for all browser tests

### testing_http/ (HTTP Request Testing)
- **Purpose**: Direct HTTP API testing
- **Technology**: requests library
- **What it does**: Makes HTTP requests to test endpoints directly
- **Commands**:
  - `/testhttp` - HTTP tests with mock APIs (free)
  - `/testhttpf` - HTTP tests with REAL APIs (costs money)
- **Files**:
  - All former "browser simulation" tests
  - `testing_full/` - Tests with real Firebase/Gemini APIs
  - `run_all_http_tests.py` - Runner for all HTTP tests

## Key Changes Made

1. **Added HARD RULE to CLAUDE.md**:
   - Section: "Browser vs HTTP Testing (🚨 HARD RULE)"
   - Clear distinction between testing_ui/ and testing_http/
   - Explicit prohibition of HTTP simulation in browser tests

2. **Reorganized all test files**:
   - Moved HTTP-based tests from testing_ui/ to testing_http/
   - Created proper Playwright browser tests in testing_ui/
   - Updated test runners to reflect new structure

3. **Redefined commands for clarity**:
   - `/testui` - Real browser tests with mock APIs (free)
   - `/testuif` - Real browser tests with REAL APIs (costs money)
   - `/testhttp` - HTTP tests with mock APIs (free)
   - `/testhttpf` - HTTP tests with REAL APIs (costs money)
   - `/testi` - Legacy HTTP integration tests

## How to Run Tests

### Browser Tests (Playwright)
```bash
# Install Playwright first
pip install playwright
playwright install chromium

# Run browser tests with mock APIs (free)
python3 mvp_site/main.py testui

# Run browser tests with REAL APIs (costs money!)
python3 mvp_site/main.py testuif
```

### HTTP Tests
```bash
# Run HTTP tests with mock APIs (free)
python3 mvp_site/main.py testhttp

# Run HTTP tests with REAL APIs (costs money!)
python3 mvp_site/main.py testhttpf
```

## Important Notes

1. **Never mix approaches**: Browser tests use Playwright, HTTP tests use requests
2. **testing_ui/ is for visual testing**: Real browsers, real UI interactions
3. **testing_http/ is for API testing**: Direct endpoint testing, faster but less realistic
4. **Both have their place**: Use browser tests for user journeys, HTTP tests for API contracts
