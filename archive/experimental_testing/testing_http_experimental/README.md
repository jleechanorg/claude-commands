# HTTP Testing Directory

This directory contains HTTP-based tests that make direct HTTP requests to the Flask server.

## Structure

- **Mock API Tests**: Use HTTP requests with mocked Firebase/Gemini responses (fast, free)
- **Full API Tests (`testing_full/`)**: Use HTTP requests with REAL Firebase/Gemini APIs (slow, costs money)

## Key Difference from testing_ui/

- **testing_http/**: Direct HTTP requests using `requests` library
- **testing_ui/**: Real browser automation using Playwright

## Running Tests

### HTTP Tests with Mock APIs (Safe, Free)
```bash
# From project root - run HTTP tests with mocked backend
python3 mvp_site/main.py testhttp

# Or directly
TESTING=true python3 testing_http/run_all_http_tests.py
```

### HTTP Tests with Real APIs (DANGER: Costs Money!)
```bash
# From project root - run HTTP tests with real Firebase/Gemini
python3 mvp_site/main.py testhttpf

# Or directly
cd testing_http/testing_full
python3 run_all_full_tests.py
```

## Test Files

### Current HTTP Tests
- `test_continue_campaign.py` - Tests campaign continuation flow via HTTP
- `test_character_creation.py` - Tests character creation via HTTP
- `test_god_mode.py` - Tests god mode interactions via HTTP
- `test_error_cases.py` - Tests error handling via HTTP
- `test_export_download.py` - Tests export functionality via HTTP
- `test_multiple_turns.py` - Tests multiple turn sequences via HTTP
- `test_settings_theme.py` - Tests settings/theme changes via HTTP
- `test_http_browser_simulation.py` - HTTP simulation tests
- `test_config.py` - Test configuration utilities

### Test Runner
- `run_all_http_tests.py` - Main HTTP test runner for mock APIs

### Full API Tests (testing_full/)
- `test_continue_campaign_full.py` - Campaign continuation with real APIs
- `test_god_mode_full.py` - God mode with real APIs
- `test_config_full.py` - Full API test configuration
- `run_all_full_tests.py` - Real API test runner with cost tracking

### Utility Files
- `show_homepage_ascii.py` - ASCII homepage display utility
- `visual_browser_proof.py` - Visual browser proof utility
- Various test scripts in `test_scripts/` subdirectory

## Important Notes

1. These tests use direct HTTP requests, NOT browser automation
2. They test the API endpoints directly, not the full user experience
3. For real browser testing, use `testing_ui/` directory instead
