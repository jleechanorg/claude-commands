---
description: Browser-based login to a sample web app via Firebase Google OAuth using Chrome Superpowers MCP
type: reference
scope: reference
---

# Browser Login via MCP (Firebase Google OAuth)

This skill documents how to authenticate with a Firebase-backed web app in a real browser using Chrome Superpowers MCP or Playwright MCP for browser-based testing.

## Test Accounts

| Account | Purpose | Notes |
|---------|---------|-------|
| `<test-user@example.com>` | Secondary test account | Sample data available |
| `$USER@example.com` | Primary account (owner) | Full data set |

## Server URLs

| Environment | URL |
|-------------|-----|
| Deployed Dev | `https://your-project.example.com` |
| Local | `http://localhost:8081` |

## Chrome Superpowers MCP Login Flow

### Step 1: Navigate to the App

```python
# Navigate to deployed server
mcp__chrome-superpower__use_browser(
    action="navigate",
    payload="https://your-project.example.com"
)
```

### Step 2: Click Sign In with Google

```python
# Click the Google sign-in button
mcp__chrome-superpower__use_browser(
    action="click",
    selector="//button[contains(text(), 'Sign in with Google')]"
)
```

### Step 3: Complete OAuth in Popup

The Firebase OAuth popup will open. The MCP browser cannot track the popup window, but:
- If you've previously signed in with Google in the same browser profile, it may auto-complete
- Manual intervention may be needed to click your Google account
- After successful auth, the main page will show your email in the header

### Step 4: Verify Login Success

```python
# Extract page content to verify login
mcp__chrome-superpower__use_browser(
    action="extract",
    payload="text",
    selector="body"
)
```

**Success indicators:**
- Email address visible in header (e.g., `$USER@example.com`)
- Dashboard navigation and primary content visible
- Expected data for the signed-in user rendered without errors

### Step 5: Navigate to App Page

```python
# Navigate directly to a specific page
mcp__chrome-superpower__use_browser(
    action="navigate",
    payload="http://localhost:8081/your/path"
)
```

## Evidence Collection

### Screenshot Capture

```python
# Capture screenshot as evidence
mcp__chrome-superpower__use_browser(
    action="screenshot",
    payload="evidence-name.png"
)
```

Screenshots are saved to Chrome Superpowers temp directory:
`/var/folders/j0/.../chrome-session-*/XXX-action-timestamp/screenshot.png`

### Copy to Evidence Directory

```bash
# Create evidence directory
mkdir -p /tmp/browser-login-evidence/

# Copy screenshot
cp /path/to/chrome-session/*/screenshot.png /tmp/browser-login-evidence/
```

### OCR Validation

**Primary Method: Claude Code Native Vision**

Claude Code can directly read and analyze image files as a multimodal LLM:

```python
# Use the Read tool on PNG files - Claude sees the image directly
Read(file_path="/tmp/browser-login-evidence/screenshot.png")
# Claude will describe what it sees: user email, page content, UI state
```

**Secondary Method: Tesseract OCR (Cross-validation)**

```python
python3 - <<'PY'
from PIL import Image
import pytesseract

image_path = "/tmp/browser-login-evidence/screenshot.png"
img = Image.open(image_path)
text = pytesseract.image_to_string(img)

# Verify login success
if "$USER@example.com" in text or "<test-user@example.com>" in text:
    print("SUCCESS: User is logged in")

if "Dashboard" in text:
    print("SUCCESS: Dashboard page visible")

print("\n=== Full OCR Output ===")
print(text)
PY
```

## Example: Full Login Test

```python
# 1. Navigate
mcp__chrome-superpower__use_browser(action="navigate", payload="https://your-project.example.com")

# 2. Click Sign In
mcp__chrome-superpower__use_browser(action="click", selector="//button[contains(text(), 'Sign in with Google')]")

# 3. Wait for OAuth popup (manual intervention if needed)

# 4. Take screenshot
mcp__chrome-superpower__use_browser(action="screenshot", payload="login-test.png")

# 5. Extract and verify
mcp__chrome-superpower__use_browser(action="extract", payload="text", selector="body")
```

## Playwright MCP Alternative

If Chrome Superpowers is unavailable, use Playwright MCP:

```python
# Navigate
mcp__playwright-mcp__browser_navigate(url="https://your-project.example.com")

# Get snapshot
mcp__playwright-mcp__browser_snapshot()

# Click login button
mcp__playwright-mcp__browser_click(element="Sign in with Google button", ref="button-ref")

# Take screenshot
mcp__playwright-mcp__browser_take_screenshot()
```

## Troubleshooting

### Session Lost After Navigation

Firebase OAuth sessions may not persist across page navigations in MCP browsers.

**Solution**: Navigate to the target page directly after authentication completes, or use the same tab for all operations.

### OAuth Popup Not Completing

The MCP browser cannot interact with popup windows.

**Solution**: Use a browser profile that's already logged into Google, or manually complete the OAuth flow when the popup appears.

### "No token provided" Error

The API endpoint requires Firebase authentication.

**Solution**: Ensure you've completed the OAuth flow and the session is active. Check the header for your email address.

## Related Skills

- [browser-testing-ocr-validation.md](browser-testing-ocr-validation.md) - OCR validation for browser tests
- [chrome-superpowers-reference.md](chrome-superpowers-reference.md) - Chrome Superpowers MCP reference
- [playwright-mcp-manual-interaction.md](playwright-mcp-manual-interaction.md) - Playwright MCP manual interaction
