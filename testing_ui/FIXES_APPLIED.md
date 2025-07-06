# Browser Test Fixes Applied

## Summary of 500 Error Debugging

The 500 errors were caused by field name mismatches between the browser tests and the API:

### 1. Field Name Mismatch
- **Problem**: Tests were sending `"text"` field but API expects `"input"` field (defined by `KEY_USER_INPUT = 'input'` in main.py:36)
- **Fix**: Updated all test files to use `"input"` instead of `"text"` in story interaction payloads

### 2. API Endpoint Issues  
- **Problem**: Tests were using incorrect endpoints like `/campaigns` and `/story`
- **Fix**: Updated to correct endpoints:
  - `/api/campaigns` for campaign creation
  - `/api/campaigns/{id}/interaction` for story interactions

### 3. Response Field Names
- **Problem**: Tests expected `campaignId` but API returns `campaign_id`
- **Fix**: Updated all campaign ID extraction to use `campaign.get('campaign_id')`
- **Fix**: Campaign list uses `id` field, updated to `camp.get('id')`

### 4. Status Code Handling
- **Problem**: Tests expected 200 for campaign creation but API returns 201
- **Fix**: Updated all campaign creation checks to accept both 200 and 201

### 5. Authentication Headers
- **Problem**: Tests needed authentication bypass headers for test server
- **Fix**: All tests now use `get_test_session()` from test_config.py which adds:
  - `X-Test-Bypass-Auth: true`
  - `X-Test-User-ID: test-user`

## Files Modified

1. `test_continue_campaign.py` - Fixed field names and endpoints
2. `test_god_mode.py` - Fixed field names and endpoints  
3. `test_multiple_turns.py` - Fixed field names and endpoints
4. `test_character_creation.py` - Fixed field names and added auth
5. `test_export_download.py` - Fixed field names and added auth
6. `test_error_cases.py` - Added auth headers
7. `test_settings_theme.py` - Added auth headers
8. `test_http_browser_simulation.py` - Fixed field names and endpoints

## Test Runner Created

- Created `run_all_browser_tests.py` to run all tests sequentially
- Added `/testui` command to main.py for easy test execution
- Usage: `python3 mvp_site/main.py testui`

All browser tests are now passing successfully!