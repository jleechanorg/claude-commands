# Testing UI Reusable Patterns Report

## Executive Summary

This report documents reusable patterns extracted from the `mvp_site/testing_ui/` folder for use in Frontend v2 development. The patterns cover authentication bypass, mock data generation, browser automation, and API simulation approaches.

## 1. Authentication Bypass Patterns

### 1.1 Test Mode URL Parameters
The primary authentication bypass method uses URL parameters to enable test mode:

```python
# Basic test mode URL
test_url = "http://localhost:8081?test_mode=true&test_user_id=test-user-123"

# Navigate with test mode
page.goto(test_url)

# Wait for test mode initialization
page.wait_for_function("window.testAuthBypass !== undefined", timeout=5000)
```

### 1.2 Test Mode Headers for API Requests
When test mode is active, the frontend automatically adds headers:

```javascript
// Frontend behavior (from README_TEST_MODE.md)
// api.js adds these headers when window.testAuthBypass is set:
headers['X-Test-Bypass-Auth'] = 'true';
headers['X-Test-User-ID'] = window.testAuthBypass.userId;
```

### 1.3 HTTP Test Headers
For HTTP-based tests, headers can be set directly:

```python
headers = {
    "X-Test-Bypass-Auth": "true",
    "X-Test-User-ID": "test-user-123",
    "Content-Type": "application/json"
}
```

## 2. Mock Data Generation Patterns

### 2.1 Campaign Creation via API
Creating campaigns through API to bypass UI issues:

```python
def create_campaign_via_api():
    """Create a campaign using the API with test headers."""
    url = "http://localhost:8081/api/campaigns"
    headers = {
        "Content-Type": "application/json",
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": "ui-debug-test",
    }
    data = {
        "title": "Debug Mode UI Test",
        "prompt": "A brave warrior enters a goblin cave",
        "genre": "Fantasy",
        "tone": "Epic",
        "selected_prompts": ["game_state_instruction.md"],
        "character_name": "Test Fighter",
        "character_background": "A warrior testing the UI",
        "debug_mode": True,  # Enable debug mode
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        result = response.json()
        return result.get("campaign_id")
```

### 2.2 Structured Field Mock Data
From `structured_fields_fixtures.py`, comprehensive mock responses:

```python
# Complete response with all 10 required fields
FULL_STRUCTURED_RESPONSE = {
    "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Ches 20, 10:00\nLocation: Goblin Cave",
    "resources": "HD: 3/5 | Second Wind: 1/1 | Action Surge: 1/1",
    "narrative": "You swing your sword in a mighty arc...",
    "planning_block": {
        "thinking": "The player has wounded one goblin...",
        "context": "The cave is dimly lit...",
        "choices": {
            "press_attack": {
                "text": "Press the Attack",
                "description": "Continue attacking...",
                "risk_level": "medium"
            }
        }
    },
    "dice_rolls": [
        "Attack Roll: 1d20+7 = 15+7 = 22 (Hit!)",
        "Damage Roll: 1d8+4 = 6+4 = 10 slashing damage"
    ],
    "god_mode_response": "",
    "entities_mentioned": ["goblin", "goblin chieftain"],
    "location_confirmed": "Goblin Cave - Main Chamber",
    "state_updates": {},
    "debug_info": {
        "dm_notes": ["Player made a successful attack"],
        "state_rationale": "Updated NPC HP values"
    }
}
```

### 2.3 Sample Game State Data
From `data_fixtures.py`:

```python
SAMPLE_GAME_STATE = {
    "game_state_version": 1,
    "player_character_data": {
        "name": "Sir Kaelan the Adamant",
        "hp_current": 85,
        "hp_max": 100,
        "level": 3,
        "experience": 2750,
        "gold": 150,
        "mbti": "ENFJ",
        "alignment": "Lawful Good"
    },
    "world_data": {
        "current_location_name": "Ancient Tavern",
        "weather": "Misty evening",
        "world_time": {"hour": 18, "minute": 30}
    },
    "npc_data": {
        "innkeeper": {
            "name": "Gareth the Wise",
            "relationship": "Friendly",
            "mbti": "ISFJ"
        }
    }
}
```

## 3. Browser Automation Patterns (Playwright)

### 3.1 Basic Browser Test Setup
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    try:
        # Navigate with test mode
        page.goto("http://localhost:8081?test_mode=true&test_user_id=test-123")

        # Wait for test mode
        page.wait_for_function("window.testAuthBypass !== undefined")

        # Should bypass auth and go to dashboard
        page.wait_for_selector("#campaign-list", timeout=10000)

    finally:
        browser.close()
```

### 3.2 Campaign Creation Wizard Navigation
From `test_ui_with_test_mode.py`:

```python
# Create new campaign through wizard
page.click("button:has-text('Create New Campaign')")

# Fill campaign form
page.fill("#campaign-title", "UI Structure Test")
page.fill("#campaign-genre", "Fantasy")
page.fill("#campaign-tone", "Epic")
page.fill("#character-name", "Test Hero")
page.fill("#character-background", "Testing the UI display")

# Submit
page.click("button:has-text('Create Campaign')")

# Wait for story view
page.wait_for_selector("#story-content", timeout=10000)
```

### 3.3 Advanced Wizard Testing (5-step process)
From `wizard_test_instructions.md`:

```python
# Step 1: Test wizard-setting-input field
setting_input = page.locator("#wizard-setting-input")
placeholder = setting_input.get_attribute("placeholder")
print(f"Setting placeholder: {placeholder}")

# Test campaign type switching
page.click("#wizard-customCampaign")
page.wait_for_timeout(500)

# Navigate through steps
next_btn = page.locator("#wizard-next")
next_btn.click()

# Step 4: Launch
launch_btn = page.locator("#launch-campaign")
```

### 3.4 Element Visibility Testing
```python
# Check for UI elements in story entries
story_entries = page.locator(".story-entry").all()
if story_entries:
    last_entry = story_entries[-1]

    # Check structured fields
    session_header = last_entry.locator(".session-header")
    if session_header.count() > 0 and session_header.is_visible():
        print("✓ SESSION HEADER found")

    planning_block = last_entry.locator(".planning-block")
    if planning_block.count() > 0 and planning_block.is_visible():
        print("✓ PLANNING BLOCK found")
```

### 3.5 Mobile Responsive Testing
From `test_mobile_responsive.py`:

```python
# Test different viewport sizes
viewports = [
    {"width": 320, "height": 568, "name": "Small Mobile"},
    {"width": 375, "height": 667, "name": "iPhone"},
    {"width": 768, "height": 1024, "name": "Tablet"},
    {"width": 1024, "height": 768, "name": "Desktop"}
]

for viewport in viewports:
    page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
    page.wait_for_timeout(1000)  # Allow layout to settle

    # Check element styles
    choice_id_style = page.locator(".choice-id").first.evaluate("""
        element => {
            const style = window.getComputedStyle(element);
            return {
                fontSize: style.fontSize,
                fontWeight: style.fontWeight,
                color: style.color
            };
        }
    """)
```

## 4. API Response Monitoring

### 4.1 Intercepting API Responses
```python
# Log API responses
def log_response(response):
    if "/api/campaigns/" in response.url and response.status == 200:
        try:
            data = response.json()
            if "session_header" in data or "planning_block" in data:
                print(f"📡 API Response fields: {list(data.keys())}")
                if "session_header" in data:
                    print(f"   session_header: {data['session_header'][:100]}...")
        except:
            pass

page.on("response", log_response)
```

## 5. Screenshot Patterns

### 5.1 Organized Screenshot Capture
```python
# Create screenshots directory
screenshots_dir = "ui_verification_screenshots"
os.makedirs(screenshots_dir, exist_ok=True)

# Capture different states
page.screenshot(path=f"{screenshots_dir}/01_initial_campaign.png", full_page=True)

# Element-specific screenshots
session_header.screenshot(path=f"{screenshots_dir}/03_session_header.png")
planning_block.screenshot(path=f"{screenshots_dir}/07_planning_block.png")
```

## 6. Reusable Test Utilities

### 6.1 Test Mode Navigation Helper
```python
def navigate_with_test_auth(page, base_url, user_id="test-user"):
    """Navigate to app with test authentication bypass."""
    test_url = f"{base_url}?test_mode=true&test_user_id={user_id}"
    page.goto(test_url)
    page.wait_for_function("window.testAuthBypass !== undefined", timeout=5000)
    page.wait_for_selector("#campaign-list", timeout=10000)
    return test_url
```

### 6.2 Campaign Creation Helper
```python
def create_test_campaign(page, title="Test Campaign", debug_mode=False):
    """Create a campaign through the UI."""
    page.click("button:has-text('Create New Campaign')")

    # Fill form
    page.fill("#campaign-title", title)
    page.fill("#character-name", "Test Character")

    if debug_mode:
        # Enable debug mode if checkbox exists
        if page.locator("#debug-mode-checkbox").count() > 0:
            page.check("#debug-mode-checkbox")

    page.click("button:has-text('Create Campaign')")
    page.wait_for_selector("#story-content", timeout=15000)
```

### 6.3 Element State Debugging
```python
def debug_element_state(page, selector, element_name):
    """Debug why an element might not be interactable."""
    element = page.locator(selector)

    if element.count() == 0:
        print(f"❌ {element_name}: Not found in DOM")
        return

    is_visible = element.is_visible()
    is_enabled = element.is_enabled()
    bounding_box = element.bounding_box()

    print(f"\n🔍 {element_name} Debug Info:")
    print(f"   Visible: {is_visible}")
    print(f"   Enabled: {is_enabled}")
    print(f"   Bounding Box: {bounding_box}")

    if bounding_box:
        print(f"   Position: ({bounding_box['x']}, {bounding_box['y']})")
        print(f"   Size: {bounding_box['width']}x{bounding_box['height']}")
```

## 7. Frontend v2 Integration Recommendations

### 7.1 Test Mode Implementation
1. Implement URL parameter detection in Frontend v2:
   ```typescript
   const urlParams = new URLSearchParams(window.location.search);
   if (urlParams.get('test_mode') === 'true') {
     window.testAuthBypass = {
       enabled: true,
       userId: urlParams.get('test_user_id') || 'test-user'
     };
   }
   ```

2. Add test headers to API service:
   ```typescript
   if (window.testAuthBypass?.enabled) {
     headers['X-Test-Bypass-Auth'] = 'true';
     headers['X-Test-User-ID'] = window.testAuthBypass.userId;
   }
   ```

### 7.2 Mock Data Service
Create a mock data service using the patterns from fixtures:
```typescript
export const mockData = {
  campaigns: [/* Use SAMPLE_CAMPAIGN pattern */],
  gameStates: [/* Use SAMPLE_GAME_STATE pattern */],
  structuredResponses: [/* Use FULL_STRUCTURED_RESPONSE pattern */]
};
```

### 7.3 Playwright Test Suite
Structure tests following the established patterns:
- Authentication bypass tests
- Campaign creation flow tests
- Game view interaction tests
- Mobile responsive tests
- API response validation tests

### 7.4 Visual Regression Testing
Use the screenshot patterns for visual regression:
- Capture key UI states
- Compare against baseline images
- Flag visual changes in PRs

## Conclusion

These patterns provide a solid foundation for implementing comprehensive testing in Frontend v2. The key strengths are:
- Simple authentication bypass mechanism
- Realistic mock data structures
- Proven browser automation patterns
- Mobile testing capabilities
- API response validation

By adopting these patterns, Frontend v2 can have robust testing from day one.
