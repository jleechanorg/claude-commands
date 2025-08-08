# Test: Visual Content Validation - End-to-End Data Flow

## Test ID
test-visual-content-validation-e2e

## Status
- [ ] RED (failing) - Content validation test to detect hardcoded content
- [ ] GREEN (passing) - Visual verification that displayed content matches user input
- [ ] REFACTORED

## Description
Validates that React V2 displays the actual user-created content instead of hardcoded content. This test specifically checks the end-to-end data flow: user input → API call → database storage → retrieval → UI display.

## Critical Learning Context
Previous testing focused only on API calls and navigation, missing the fact that game view displayed "Shadowheart" content instead of the created "Elara the Brave" character. This test ensures visual content validation.

## Pre-conditions
- React V2 development server running on `http://localhost:3002`
- Flask backend server running on `http://localhost:5005`
- **REAL PRODUCTION MODE**: NO test mode parameters
- User must be signed in with real Google account
- Playwright MCP configured with headless mode

## Test Case: Visual Content Validation

### Test Data
```json
{
  "campaign_title": "Visual Test Campaign",
  "character_name": "Zara the Mystic",
  "setting": "Crystal caves of Luminara where gemstones sing ancient melodies",
  "description": "A realm where music and magic intertwine through crystalline formations"
}
```

### Step 1: Create Campaign with Specific Content
1. **Navigate**: `http://localhost:3002`
2. **Sign In**: Complete real Google authentication
3. **Create Campaign**: Click "Create V2 Campaign"
4. **Step 1 - Basics**:
   - Select "Custom Campaign"
   - Enter title: "Visual Test Campaign"
   - Enter character: "Zara the Mystic"
   - Enter setting: "Crystal caves of Luminara where gemstones sing ancient melodies"
   - Click "Next"
5. **Step 2 - AI Style**:
   - Uncheck "Default Fantasy World" (custom setting)
   - Keep "Mechanical Precision" and "Starting Companions"
   - Click "Next"
6. **Step 3 - Launch**: Click "Begin Adventure!"

### Step 2: Visual Content Verification
7. **Wait for Campaign Creation**: Allow full campaign generation
8. **Navigate to Game View**: Should automatically redirect to `/campaigns/{id}`
9. **Visual Verification**: Take screenshot and verify content contains:
   - ✅ Character name "Zara the Mystic" appears in story
   - ✅ Setting references "Crystal caves of Luminara" or "gemstones"
   - ✅ No hardcoded character names (e.g., "Shadowheart", "Ser Arion")
   - ✅ No hardcoded settings (e.g., "Bastion of Eternal Radiance", "World of Assiah")

### Step 3: API Verification
10. **Check Flask Logs**: Verify both creation and retrieval calls
    ```bash
    # Should show both calls:
    POST /api/campaigns HTTP/1.1" 201
    GET /api/campaigns/{campaign_id} HTTP/1.1" 200
    ```

## Expected Results

### PASS Criteria (GREEN)
- ✅ Campaign creation API call successful
- ✅ Game view loads with campaign ID in URL
- ✅ **CRITICAL**: Story content contains "Zara the Mystic"
- ✅ **CRITICAL**: Story content references "Crystal caves" or "Luminara"
- ✅ **CRITICAL**: NO hardcoded character names present
- ✅ **CRITICAL**: Story matches user's custom input data

### FAIL Indicators (RED)
- ❌ Game view shows hardcoded characters (Shadowheart, Ser Arion, etc.)
- ❌ Game view shows hardcoded settings (Bastion, World of Assiah, etc.)
- ❌ Story content doesn't match user input
- ❌ No GET request to `/api/campaigns/{id}` in Flask logs
- ❌ Generic/template content instead of personalized story

## Visual Test Commands

```bash
# Execute with visual content verification
mcp__playwright-mcp__browser_navigate --url="http://localhost:3002"
# Create campaign with test data
# Take screenshot after creation
mcp__playwright-mcp__browser_take_screenshot --filename="visual-test-result.png"
# Verify screenshot contains expected content
```

### Content Verification Checklist
- [ ] Screenshot shows "Zara the Mystic" in story text
- [ ] Screenshot shows "Crystal caves" or "Luminara" references
- [ ] Screenshot shows NO "Shadowheart" or other hardcoded names
- [ ] Screenshot shows NO "Bastion of Eternal Radiance" or hardcoded settings
- [ ] Story content is unique and matches user input

## Flask Log Verification

### Required API Calls
```bash
# Campaign creation
POST /api/campaigns HTTP/1.1" 201

# Campaign retrieval (THIS IS CRITICAL)
GET /api/campaigns/{campaign_id} HTTP/1.1" 200
```

If GET request is missing, the game view is using hardcoded content!

## Bug Detection Pattern

**Symptom**: API integration works but wrong content displays
**Root Cause**: Game view component not fetching or not rendering real campaign data
**Fix Required**: Verify GamePlayView.tsx fetches and displays actual campaign content

This test specifically targets the gap between API integration success and content rendering success.
