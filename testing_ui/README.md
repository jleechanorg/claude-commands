# Testing UI - Browser and Integration Testing

This directory contains browser-based testing infrastructure for WorldArchitect.AI, including HTTP-based browser simulation tests, test servers, and testing utilities.

## Directory Structure

```
testing_ui/
├── test_scripts/       # Standalone test scripts for various scenarios
├── test_servers/       # Specialized test servers with enhanced features
├── test_results/       # Test output and result files
├── http_captures/      # HTTP request/response captures (gitignored)
├── test_config.py      # Shared test configuration and auth headers
├── run_all_browser_tests.py  # Main test runner
└── test_*.py          # Main browser test files
```

## Main Test Files

### Core Browser Tests
- `test_continue_campaign.py` - Tests loading and continuing existing campaigns
- `test_multiple_turns.py` - Tests multiple gameplay turns in a session
- `test_god_mode.py` - Tests god mode commands and mode switching
- `test_character_creation.py` - Tests 7-step character creation flow
- `test_export_download.py` - Tests campaign export in various formats
- `test_settings_theme.py` - Tests UI settings and theme changes
- `test_error_cases.py` - Tests error handling and edge cases
- `test_http_browser_simulation.py` - Comprehensive HTTP simulation demo

### Testing Infrastructure
- `test_config.py` - Provides shared configuration, auth headers, and base URL
- `run_all_browser_tests.py` - Runs all browser tests sequentially
- `FIXES_APPLIED.md` - Documents fixes applied to resolve 500 errors

## Running Tests

### Individual Test
```bash
python3 testing_ui/test_continue_campaign.py
```

### All Browser Tests
```bash
# From project root
python3 mvp_site/main.py testui

# Or directly
python3 testing_ui/run_all_browser_tests.py
```

### With Test Server
Many tests require a test server running on port 8086:
```bash
python3 testing_ui/test_servers/monitored_test_server.py
```

## Authentication

Tests use header-based authentication bypass for the test environment:
- `X-Test-Bypass-Auth: true`
- `X-Test-User-ID: test-user`

This is configured automatically via `test_config.py`.

## Test Categories

### Functional Tests
- Campaign creation and management
- Story interaction and progression
- Character creation workflow
- Export functionality

### UI Tests
- Theme switching
- Settings persistence
- Error handling
- Browser simulation

### Integration Tests
- God mode commands
- Multiple turn sequences
- Campaign continuation
- Auth bypass verification

## Important Notes

1. **No Mocks**: These tests interact with real servers, not mocks
2. **Port 8086**: Default test server port (different from production 8080)
3. **Field Names**: API expects `input` field, not `text` 
4. **Status Codes**: Campaign creation returns 201, not 200
5. **Endpoints**: Use `/api/campaigns/{id}/interaction` for story interactions

## Subdirectories

- **test_scripts/** - Reusable test scripts for specific scenarios (combat, auth, etc.)
- **test_servers/** - Test servers with debugging, monitoring, and special features
- **test_results/** - Test outputs and reports (temporary, can be cleaned)
- **http_captures/** - HTTP request/response captures for debugging

See README files in each subdirectory for more details.