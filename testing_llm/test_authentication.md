# Test: Google OAuth Authentication End-to-End Flow

> **Execution Command:** `/testllm` - LLM-Driven Test Execution Command  
> **Protocol Notice:** This is an executable test that must be run via the `/testllm` workflow with full agent orchestration.

## Test ID
test-authentication-oauth-e2e

## Status
- [ ] RED (failing) - Authentication flow not tested
- [ ] GREEN (passing) - OAuth integration working
- [ ] REFACTORED

## Description
Validates that React V2 frontend successfully authenticates users through Google OAuth, handles authentication state correctly, and integrates properly with the backend API without errors.

## Pre-conditions
- React V2 development server running on `http://localhost:3002`
- Flask backend server running on `http://localhost:5005`
- Google OAuth credentials available in home directory
- Firebase authentication configured
- Playwright MCP configured with headless mode disabled for OAuth popup

## Test Environment Setup

### Google Credentials
```bash
# Expected credentials location
~/.config/worldarchitect-ai/google-credentials.json
# OR
~/google-credentials.json

# Contains:
{
  "email": "<YOUR_TEST_EMAIL>",
  "password": "<YOUR_TEST_PASSWORD>"
}

# Alternative: Use environment variables (recommended)
export TEST_EMAIL="your-test-email@gmail.com"
export TEST_PASSWORD="your-test-password"
```

### Server Startup Validation
Before running tests, verify both servers are healthy:
```bash
# Backend health check
curl -f http://localhost:5005/ && echo "✅ Backend ready"

# Frontend health check
curl -f http://localhost:3002/ && echo "✅ Frontend ready"
```

## Test Matrix

This test validates 4 critical authentication scenarios:

| Test Case | Initial State | Action | Expected State | Expected Destination |
|-----------|---------------|--------|----------------|---------------------|
| **Case 1** | Logged Out | Load Homepage | Show auth UI | Landing page with sign-in button |
| **Case 2** | Logged Out | Click Campaign Button | Trigger OAuth | Google OAuth popup |
| **Case 3** | OAuth Popup | Complete Login | Authenticated | Return to campaigns page |
| **Case 4** | Authenticated | Page Reload | Persist State | Remain authenticated |

## Test Steps

### Test Case 1: Initial Unauthenticated State
1. **Navigate**: `http://localhost:3002/`
2. **Verify Unauthenticated UI**:
   - Header shows no user information (no placeholder text)
   - Button text: "✨ Create Your First Campaign ✨" (no lock icon, no "Sign In &")
   - Button is enabled and clickable
3. **Console Verification**:
   - ✅ No Firebase authentication errors
   - ✅ No undefined user state errors
   - ✅ Clean initial authentication state

### Test Case 2: OAuth Flow Initiation
1. **Action**: Click "✨ Create Your First Campaign ✨" button
2. **Expected Behavior**:
   - Google OAuth popup window opens
   - Popup URL contains `accounts.google.com`
   - Original page remains in background
3. **Backend Log Verification**:
   - ❌ No premature API calls before authentication
   - ✅ No authentication errors in Flask logs
4. **Console Verification**:
   - ✅ OAuth flow initiation logged
   - ❌ No JavaScript errors during popup launch

### Test Case 3: Complete Google OAuth Authentication
1. **In OAuth Popup**:
   - Enter Google credentials from home directory file or environment variables
   - Complete 2FA if required
   - Grant permissions to WorldArchitect.AI
2. **After OAuth Success**:
   - Popup closes automatically
   - User returns to main application
   - **CRITICAL: Expected Destination**: Campaigns page (URL should be `http://localhost:3002/campaigns` or similar)
3. **Post-Login Page Validation**:
   - **URL Verification**: Current page URL contains `/campaigns` or campaign-related path
   - **Page Content**: Campaigns page elements are visible (not landing page elements)
   - **Navigation State**: User is correctly redirected from landing to campaigns
   - **Page Load Complete**: All campaigns page assets loaded without errors
4. **Authentication State Verification**:
   - Header shows authenticated user info (name, email, avatar from Google account)
   - Button text changes appropriately for authenticated users
   - No placeholder text visible anywhere in UI
   - User authentication state is `authenticated: true`
5. **Backend Integration Validation**:
   - API calls now include proper authentication headers (`Authorization: Bearer <token>`)
   - Backend logs show successful authenticated requests to campaigns endpoints
   - No 401 Unauthorized errors in server logs
   - Campaigns data loads successfully from backend API

### Test Case 4: Authentication Persistence
1. **Action**: Refresh the page (F5 or browser reload)
2. **Expected Behavior**:
   - User remains authenticated (no re-login required)
   - Authentication state persists across page reloads
   - Direct navigation to campaigns page works
3. **State Verification**:
   - Firebase auth state maintained
   - User token still valid
   - Backend API calls continue to work

## Backend Log Monitoring

### Real-Time Log Monitoring Protocol

**Continuous Log Monitoring During Test Execution**:
```bash
# Start log monitoring in separate terminal before test execution
tail -f /tmp/worldarchitect.ai/frontend_v2_v2/flask-server.log | grep -E "(ERROR|WARN|401|500|authentication|firebase|oauth)" --color=always

# Alternative: Monitor with timestamps
tail -f /tmp/worldarchitect.ai/frontend_v2_v2/flask-server.log | while read line; do echo "$(date '+%H:%M:%S') $line"; done | grep -E "(ERROR|WARN|401|500)"
```

### Authentication Flow Log Patterns

**Expected Successful Flow**:
```bash
# Phase 1: Pre-authentication (Expected: Minimal activity)
[INFO] Frontend assets served from React dev server
[INFO] Static file requests only (CSS, JS, images)
❌ Should NOT see API endpoints called before authentication

# Phase 2: OAuth initiation (Expected: Clean startup)
[INFO] OAuth redirect initiated
[DEBUG] Firebase auth state change: null -> pending
❌ Should NOT see Firebase token validation errors

# Phase 3: Post-authentication (Expected: Valid API calls)
[INFO] Firebase token received and validated
[INFO] GET /api/campaigns HTTP/1.1 200 OK
[INFO] Authorization: Bearer <firebase-token> validated
[INFO] X-User-ID: <authenticated-user-id> processed
✅ All API responses should be 200 OK
✅ No authentication failures

# Phase 4: Session persistence (Expected: Continued access)
[INFO] Token refresh completed successfully
[INFO] Persistent session maintained across reload
✅ Continued API access without re-authentication
```

**Critical Error Indicators to Watch For**:
```bash
# Authentication Failures (CRITICAL - Test should FAIL)
❌ "401 Unauthorized: Firebase token validation failed"
❌ "403 Forbidden: Invalid user permissions"
❌ "500 Internal Server Error: Authentication processing failed"
❌ "Firebase Admin SDK initialization error"
❌ "Token verification timeout"

# OAuth Flow Errors (CRITICAL - Test should FAIL)
❌ "CORS policy error during OAuth redirect"
❌ "OAuth popup blocked by browser security"
❌ "Firebase configuration missing or invalid"
❌ "Cross-origin request blocked"

# API Integration Errors (CRITICAL - Test should FAIL)
❌ "Missing Authorization header in authenticated request"
❌ "Firebase token expired and refresh failed"
❌ "Database connection error during authenticated operation"
❌ "User session not found or expired"

# Network/Infrastructure Errors (CRITICAL - Test should FAIL)
❌ "Connection refused to Firebase Authentication"
❌ "DNS resolution failed for accounts.google.com"
❌ "SSL certificate validation failed"
❌ "Request timeout during OAuth flow"
```

### Automated Log Analysis

**Log Parsing for Test Results**:
```bash
# Create log analysis function for test validation
analyze_auth_logs() {
    local log_file="/tmp/worldarchitect.ai/frontend_v2_v2/flask-server.log"
    local test_start_time=$(date '+%Y-%m-%d %H:%M:%S')

    echo "🔍 Analyzing authentication logs from $test_start_time..."

    # Count critical errors during test window
    local error_count=$(tail -n 100 "$log_file" | grep -c -E "(ERROR|401|500|CRITICAL)")
    local auth_success=$(tail -n 100 "$log_file" | grep -c "Firebase token.*validated")
    local api_success=$(tail -n 100 "$log_file" | grep -c "GET /api.*200 OK")

    # Report results
    echo "📊 Log Analysis Results:"
    echo "   Errors found: $error_count (should be 0)"
    echo "   Auth successes: $auth_success (should be >= 1)"
    echo "   API successes: $api_success (should be >= 1)"

    # Determine pass/fail
    if [ "$error_count" -eq 0 ] && [ "$auth_success" -ge 1 ] && [ "$api_success" -ge 1 ]; then
        echo "✅ Backend logs show successful authentication flow"
        return 0
    else
        echo "❌ Backend logs show authentication issues"
        return 1
    fi
}
```

## Console Error Monitoring

→ See `testing_llm/console_monitor.md` for shared console error monitoring implementation

**Authentication-Specific Error Patterns**:
```javascript
const authErrorPatterns = [
    'firebase', 'authentication', 'oauth', '401',
    'token', 'CORS', 'Network Error'
];

// Use shared monitoring with authentication patterns
window.getAuthenticationErrors = function() {
    return window.getCriticalErrors(authErrorPatterns);
};
```

### Expected Clean Console (No Errors)

**Acceptable Informational Messages**:
```javascript
// React Development Environment
✅ "Download the React DevTools for a better development experience"
✅ "React DevTools extension detected"

// Firebase SDK Normal Operation
✅ "Firebase SDK initialized successfully"
✅ "Firebase auth state changed: null -> {user}"
✅ "Firebase auth state changed: {user} -> null"

// OAuth Process Normal Flow
✅ "OAuth flow initiated"
✅ "Google OAuth popup opened"
✅ "Firebase authentication completed"
✅ "User token received and stored"

// API Integration Success
✅ "API request sent with authentication header"
✅ "Campaign data loaded successfully"
```

**CRITICAL ERRORS (Test MUST FAIL if present)**:
```javascript
// Firebase Configuration Errors
❌ "firebase is not defined"
❌ "Firebase configuration object is missing"
❌ "Firebase app initialization failed"
❌ "FirebaseError: Firebase Configuration"

// Authentication Flow Errors
❌ "Failed to load resource: the server responded with a status of 401"
❌ "Unauthorized: Firebase token validation failed"
❌ "Authentication required but no user logged in"
❌ "Firebase auth state error"

// OAuth Integration Errors
❌ "Cross-Origin-Opener-Policy policy would block the window.close call"
❌ "OAuth popup blocked by browser"
❌ "Google OAuth configuration invalid"
❌ "Failed to complete OAuth flow"

// Network and API Errors
❌ "Network Error during authentication"
❌ "CORS policy: No 'Access-Control-Allow-Origin' header"
❌ "fetch() failed during authentication"
❌ "XMLHttpRequest error during OAuth"

// React Component Errors
❌ "Warning: Can't perform a React state update on an unmounted component"
❌ "Uncaught TypeError: Cannot read property 'user' of undefined"
❌ "React Hook useAuth was called outside of an AuthProvider"
❌ "Unhandled Promise rejection"

// Token Management Errors
❌ "Token refresh failed"
❌ "Invalid token format"
❌ "Token validation error"
❌ "JWT token expired and refresh unsuccessful"
```

### Console Error Analysis

Use the shared console monitoring orchestrator with authentication-specific patterns:

```javascript
// Authentication test validation
function validateAuthConsoleErrors(testCaseName) {
    return validateConsoleErrors(testCaseName, authErrorPatterns);
}
```

**Note**: The `validateConsoleErrors` and `resetConsoleErrorLog` functions are provided by the shared orchestrator in `testing_llm/console_monitor.md`.

### OAuth-Specific Console Monitoring

**During OAuth Flow - Expected Messages**:
```javascript
// Normal OAuth Process
✅ "OAuth popup window opened successfully"
✅ "Google accounts.google.com loaded in popup"
✅ "Firebase auth state change detected"
✅ "OAuth flow completed successfully"
✅ "User token received from Firebase"
✅ "Popup window closed after successful authentication"

// Token Management
✅ "Firebase token stored in local storage"
✅ "Authentication headers added to API requests"
✅ "Token validation successful"
```

**OAuth Error Indicators (CRITICAL)**:
```javascript
// Popup Handling Errors
❌ "Popup window blocked by browser security settings"
❌ "Failed to open OAuth popup window"
❌ "Popup window closed without completing authentication"
❌ "Cross-origin communication failed with popup"

// OAuth Configuration Errors
❌ "Invalid OAuth client configuration"
❌ "OAuth redirect URI mismatch"
❌ "Google OAuth service unavailable"
❌ "OAuth scope permissions denied"

// Token Processing Errors
❌ "Failed to exchange OAuth code for token"
❌ "Token validation failed after OAuth completion"
❌ "Firebase token creation failed"
❌ "OAuth flow completed but user not authenticated"
```

### Console Monitoring Protocol

**Test Execution Console Monitoring**:
```javascript
// Execute at start of authentication test
1. Initialize console error capture
2. Reset error log for clean slate
3. Begin monitoring authentication-specific errors

// Execute during each test case
1. Check console for new errors before proceeding
2. Validate no authentication errors occurred
3. Log any unexpected errors for analysis

// Execute at end of each test case
1. Run validateConsoleErrors() function
2. Report pass/fail based on error analysis
3. Reset error log for next test case

// Execute at end of full test suite
1. Generate comprehensive error report
2. Identify patterns in console errors
3. Mark overall test pass/fail based on critical errors
```

## Success Criteria Matrix

| Test Case | Authentication State | UI Elements | API Integration | Console Status |
|-----------|---------------------|-------------|-----------------|----------------|
| **Case 1** | Unauthenticated | Clean UI, no placeholders | No API calls | No errors |
| **Case 2** | OAuth in progress | Popup visible | No premature calls | OAuth logs only |
| **Case 3** | Newly authenticated | User info displayed | Successful API calls | No errors |
| **Case 4** | Persistent auth | State maintained | Continued API access | No errors |

**Overall PASS Criteria (ALL must be satisfied)**:
- ✅ Complete OAuth flow without JavaScript errors in console
- ✅ User successfully authenticated and **lands specifically on campaigns page**
- ✅ **URL after login is campaigns page** (not landing page or other location)
- ✅ **Campaigns page content loads completely** with all expected UI elements
- ✅ Authentication state persists across page reloads
- ✅ Backend API integration works with valid authentication tokens
- ✅ No 401 Unauthorized errors in backend logs during or after authentication
- ✅ Clean console with zero authentication-related errors
- ✅ UI correctly reflects authenticated user state throughout entire flow
- ✅ **Backend logs show no errors** during authentication process
- ✅ **All API calls succeed** with proper authentication headers

**CRITICAL FAIL Indicators (ANY of these fails the test)**:
- ❌ OAuth popup fails to open or complete authentication process
- ❌ JavaScript console errors during authentication flow
- ❌ **User not redirected to campaigns page after successful login**
- ❌ **User lands on wrong page** (landing page, error page, or blank page)
- ❌ Backend API calls fail with 401 errors after authentication
- ❌ Authentication state not preserved on page reload
- ❌ Firebase token validation errors in backend logs
- ❌ UI shows placeholder text or incorrect authentication state
- ❌ **Backend errors logged** during authentication process
- ❌ **Console errors related to authentication, OAuth, or Firebase**
- ❌ Campaigns page fails to load or displays errors after authentication
- ❌ Network errors during OAuth flow or subsequent API calls

## Implementation Notes

### OAuth Popup Handling
```javascript
// Playwright MCP configuration for OAuth testing
// Note: Headless mode must be disabled for OAuth popup interaction
const browserConfig = {
  headless: false,  // Required for OAuth popup
  args: [
    '--disable-web-security',  // May be needed for localhost OAuth
    '--disable-features=VizDisplayCompositor'
  ]
};
```

### Credential Management
```bash
# Option 1: Credential file structure (NOT RECOMMENDED - use environment variables instead)
# ~/.config/worldarchitect-ai/google-credentials.json
{
  "email": "<YOUR_TEST_EMAIL>",
  "password": "<YOUR_TEST_PASSWORD>",
  "backup_codes": ["<CODE1>", "<CODE2>"]  # Optional for 2FA
}

# Option 2: Environment variables (RECOMMENDED)
export TEST_EMAIL="your-test-email@gmail.com"
export TEST_PASSWORD="your-test-password"
export TEST_BACKUP_CODES="code1,code2"  # Optional for 2FA
```

### Test Execution Protocol

**Authentication Test Sequence**:
```bash
# 1. Start servers and verify health
./tools/localserver.sh
curl -f http://localhost:5005/ && curl -f http://localhost:3002/

# 2. Execute authentication test cases
mcp__playwright-mcp__browser_navigate --url="http://localhost:3002/"
# Execute Test Case 1: Verify unauthenticated state
# Execute Test Case 2: Click button, handle OAuth popup
# Execute Test Case 3: Complete authentication in popup
# Execute Test Case 4: Verify persistence on reload

# 3. Monitor logs throughout
tail -f /tmp/worldarchitect.ai/frontend_v2_v2/flask-server.log

# 4. Verify final state
# - User authenticated
# - No console errors
# - Backend API working
# - Campaigns page accessible
```

### Error Recovery Testing

**Additional Test Scenarios**:
1. **OAuth Cancellation**: User closes popup without completing login
2. **Network Interruption**: Connection lost during OAuth flow
3. **Token Expiration**: Long session with token refresh required
4. **Multiple Login Attempts**: Repeated authentication attempts

## Expected Results

**Complete Authentication Success Verification**:
- ✅ Google OAuth popup opens and accepts credentials from environment variables or secure credential file
- ✅ User successfully authenticated and **redirected specifically to campaigns page**
- ✅ **Post-login URL verification**: `http://localhost:3002/campaigns` or campaign-related path
- ✅ Header displays actual user information (name, email from Google account)
- ✅ Backend API calls include proper authentication headers (`Authorization: Bearer <token>`)
- ✅ **No authentication errors** in backend logs or browser console throughout process
- ✅ Authentication state persists across browser reloads on campaigns page
- ✅ Clean UI with no placeholder text or authentication artifacts

**Backend Log Success Verification**:
- ✅ Zero errors logged during OAuth initiation, completion, and subsequent API calls
- ✅ Firebase token validation successful in server logs
- ✅ Authenticated API endpoints return 200 OK responses
- ✅ No 401, 403, or 500 errors related to authentication process
- ✅ Campaigns data loading successful with authenticated requests

**Console Error Success Verification**:
- ✅ Zero JavaScript console errors related to authentication, OAuth, or Firebase
- ✅ No network errors during OAuth flow or subsequent API requests
- ✅ No React component errors related to authentication state management
- ✅ No CORS policy violations or popup blocking errors
- ✅ Clean console throughout entire authentication process

**Integration Verification**:
- ✅ Firebase authentication properly configured and working with Google OAuth
- ✅ React authentication state management functional with useAuth hook
- ✅ Backend API authentication token validation working correctly
- ✅ OAuth flow completes without CORS or security policy errors
- ✅ **User experience is seamless**: landing page → OAuth → campaigns page
- ✅ **Campaigns page fully functional** after authentication completion

**Final Validation Checklist**:
```bash
# 1. URL Validation
assertEquals(window.location.pathname, "/campaigns", "User should be on campaigns page after login")

# 2. Authentication State Validation
assertTrue(user.authenticated, "User should be authenticated after OAuth completion")
assertNotNull(user.email, "User email should be populated from Google account")
assertNotNull(user.displayName, "User name should be populated from Google account")

# 3. Backend Integration Validation
assertEquals(lastApiResponse.status, 200, "Authenticated API calls should succeed")
assertTrue(lastApiRequest.headers.includes("Authorization"), "API calls should include auth header")

# 4. Error Validation
assertEquals(consoleErrors.length, 0, "Console should have no authentication errors")
assertEquals(backendErrors.length, 0, "Backend should have no authentication errors")

# 5. Page Content Validation
assertTrue(isElementVisible("campaigns-list"), "Campaigns page content should be visible")
assertFalse(isElementVisible("sign-in-button"), "Sign-in elements should not be visible")
```

This comprehensive authentication test ensures the complete OAuth integration works correctly from initial page load through successful authentication, proper campaigns page redirection, and persistent session management with zero errors in backend logs or JavaScript console.
