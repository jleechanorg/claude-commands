# Browser Test Limitations

## Current Status

Browser tests with Playwright are working and can take real screenshots, but there's a limitation:

**The frontend requires Google Sign-In authentication that cannot be bypassed with test headers.**

## Why This Happens

1. The `X-Test-Bypass-Auth` headers only work for API endpoints, not the initial page load
2. The frontend uses Firebase Auth with Google Sign-In in the browser
3. There's no test mode in the frontend code to skip authentication

## What Works

- ✅ Playwright can launch browsers
- ✅ Real screenshots are captured
- ✅ API endpoints accept test bypass headers
- ❌ Frontend UI requires real Google authentication

## Solutions

1. **Add Frontend Test Mode**: Modify `auth.js` to check for a test mode flag and skip Firebase auth
2. **Use API Tests**: Use `/testhttp` for testing functionality via API endpoints
3. **Mock Auth**: Implement a mock authentication flow for testing
4. **Test After Login**: Manually sign in once and save the session for tests

## Current Workaround

For now, use:
- `/testhttp` - For API functionality testing (works with test headers)
- `/testui` - For browser automation (requires manual sign-in)

The test infrastructure is ready; the application just needs a frontend test mode.