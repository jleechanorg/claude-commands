# Browser Test Mode Authentication Bypass

This document explains how browser tests bypass authentication in WorldArchitect.AI.

## Overview

Browser tests cannot set custom HTTP headers like API tests can. Instead, WorldArchitect.AI uses URL parameters to enable test mode authentication bypass.

## How It Works

### 1. Server Setup
Start the server with testing mode enabled:
```bash
TESTING_AUTH_BYPASS=true PORT=8081 python main.py serve
```

The `TESTING_AUTH_BYPASS=true` environment variable enables the test bypass in the backend.

### 2. Browser Navigation
Navigate to the app with test mode parameters:
```
http://localhost:8081?test_mode=true&test_user_id=test-user-123
```

Parameters:
- `test_mode=true` - Enables test authentication bypass
- `test_user_id=test-user-123` - Sets the test user ID (optional, defaults to 'test-user')

### 3. Frontend Behavior

When the page loads with `?test_mode=true`:

1. **auth.js** detects the parameter and:
   - Sets `window.testAuthBypass = { enabled: true, userId: 'test-user-123' }`
   - Skips Firebase initialization
   - Dispatches 'testModeReady' event

2. **api.js** checks `window.testAuthBypass` and:
   - Adds `X-Test-Bypass-Auth: true` header to all API requests
   - Adds `X-Test-User-ID: test-user-123` header
   - Skips Firebase token retrieval

3. **app.js** in `handleRouteChange()`:
   - Checks `window.testAuthBypass.enabled`
   - Skips authentication checks
   - Goes directly to dashboard

### 4. Backend Validation

The backend `@check_token` decorator:
- Checks if `app.config['TESTING']` is True
- Looks for `X-Test-Bypass-Auth: true` header
- Uses the `X-Test-User-ID` value instead of Firebase auth

## Example Playwright Test

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    # Navigate with test mode
    page.goto("http://localhost:8081?test_mode=true&test_user_id=test-123")

    # Wait for test mode to initialize
    page.wait_for_function("window.testAuthBypass !== undefined")

    # Should be on dashboard, not sign-in page
    page.wait_for_selector("#dashboard")

    # All API calls will now work without authentication
```

## Browser Test Helper Library

A standardized helper library (`testing_ui/browser_test_helpers.py`) provides common browser test operations:

### Features

- **Standardized authentication bypass** with `navigate_with_test_auth()`
- **5-step campaign creation wizard** navigation with navbar overlay workarounds
- **Debug utilities** for analyzing element visibility and CSS states
- **Screenshot capture** at each wizard step
- **JavaScript workarounds** for form elements hidden by navbar

### Usage

```python
from testing_ui.browser_test_helpers import BrowserTestHelper

# Initialize helper
helper = BrowserTestHelper(page, "http://localhost:8088")

# Navigate with test auth
helper.navigate_with_test_auth()
helper.wait_for_auth_bypass()

# Create a campaign (handles 5-step wizard)
success = helper.create_test_campaign(
    campaign_title="My Test Campaign",
    debug_mode=True  # Enables screenshots and detailed logging
)

# Take screenshots
helper.take_screenshot("test_state")

# Debug element issues
helper.debug_element_state("#campaign-title", "Campaign Title Field")
```

### Campaign Creation Wizard Steps

The helper navigates through all 5 steps:
1. **Basics** - Campaign title and settings
2. **AI Style** - AI behavior preferences
3. **Options** - Game options
4. **Launch** - Begin adventure button
5. **Campaign View** - Wait for game to load

### Common Issues Resolved

1. **Navbar Overlay**: JavaScript direct value setting when elements are covered
2. **Duplicate Buttons**: Specific selectors for launch button (#launch-campaign)
3. **Form Visibility**: Scroll and wait strategies for hidden elements
4. **Wizard Navigation**: Proper step-by-step progression with waits

## Security Notes

- Test mode ONLY works when server is started with `TESTING_AUTH_BYPASS=true`
- In production, the URL parameters are ignored
- The backend still validates the test bypass header
- This ensures test mode cannot be accidentally enabled in production

## Common Issues

1. **Still seeing sign-in page?**
   - Check server was started with `TESTING_AUTH_BYPASS=true`
   - Verify URL has `?test_mode=true`
   - Check browser console for errors

2. **API calls failing?**
   - Ensure `window.testAuthBypass` is set (check console)
   - Verify test headers are being sent (check Network tab)

3. **Test user not persisting?**
   - Each test should use a unique test_user_id
   - Data is still saved to Firestore under the test user

## Files Involved

- `main.py` - Backend test bypass in `@check_token` decorator
- `static/auth.js` - Frontend test mode detection
- `static/api.js` - API request header injection
- `static/app.js` - Route handling bypass
