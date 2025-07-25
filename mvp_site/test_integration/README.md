# Integration Tests

This directory contains integration tests that require external dependencies or services:

- `test_integration.py` - Flask app integration tests
- `test_sariel_campaign_integration.py` - Campaign replay tests with Sariel data
- `test_campaign_timing_automated.py` - Browser automation tests using Selenium

These tests are:
- **Included** when running `run_tests.sh` locally
- **Excluded** when running `run_tests.sh --github-export` or with `GITHUB_EXPORT=true`

## Requirements

These tests require additional dependencies:
- Flask and related packages
- Selenium WebDriver for browser automation
- Chrome/Chromium browser for Selenium tests

## Running

From the mvp_site directory:
```bash
# Run all tests including integration
bash ../run_tests.sh

# Run tests excluding integration (for CI/export)
bash ../run_tests.sh --github-export
```
