# Scratchpad: JSON Bug Display Issue - Comprehensive Debugging Plan

## Current Branch: json_fix_v3
**Created**: 2025-07-08
**Purpose**: Isolate where raw JSON is being surfaced to users in the display pipeline

## Summary of Issue

From tmp/json_bug_v3.txt logs:
- User sees: `Scene #2: {` followed by raw JSON content starting with `"narrative": "[Mode: STORY MODE]...`
- Server logs show JSON detection at multiple points but the JSON still reaches the frontend
- The bug is: Raw JSON from Gemini API is being displayed directly to users instead of just the narrative text

## Key Observations from Logs

1. **Backend detects the issue** (multiple error logs):
   - Line 265: `JSON_BUG_PARSE_RAW_JSON_INPUT: Input is already raw JSON!`
   - Line 346: `JSON_BUG_DETECTED_IN_GEMINI_SERVICE_CONTINUE: response_text contains JSON!`
   - Line 354: `JSON_BUG_DETECTED_IN_GEMINI_RESPONSE_CREATE: narrative_text contains JSON!`
   - Line 364: `JSON_BUG_DETECTED_IN_ADD_STORY_ENTRY: Saving JSON to Firestore!`

2. **Despite detection, JSON reaches frontend**:
   - The frontend displays: `Scene #2: {` with raw JSON
   - This means the detection isn't preventing the JSON from being saved/sent

## Debugging Plan - Layer by Layer

### Phase 1: Frontend Display Layer (HTML/JavaScript)
**Goal**: Determine if frontend is adding "Scene #" prefix and how it handles the response

1. **Check where "Scene #" prefix is added**:
   - Add console log in app.js `displayMessage()` or similar function:
     ```javascript
     console.log('[DEBUG] displayMessage raw input:', message);
     console.log('[DEBUG] displayMessage type:', typeof message);
     ```
   - Add log before any HTML construction:
     ```javascript
     console.log('[DEBUG] Before HTML construction, text content:', textContent);
     ```

2. **Check API response handling**:
   - In api.js `sendInteraction()` or similar:
     ```javascript
     console.log('[DEBUG] Raw API response:', response);
     console.log('[DEBUG] Response.text:', response.text);
     console.log('[DEBUG] Is JSON?:', response.text.trim().startsWith('{'));
     ```

3. **Check if there's JSON parsing happening**:
   - Look for any `JSON.parse()` calls that might be failing
   - Add try-catch around potential JSON operations:
     ```javascript
     try {
         // existing code
     } catch (e) {
         console.error('[DEBUG] JSON parse error:', e, 'for text:', text);
     }
     ```

### Phase 2: API Response Layer (main.py routes)
**Goal**: Check what exactly is being sent from Flask to frontend

1. **In `/api/campaigns/<id>/interaction` route**:
   - Before returning response:
     ```python
     logger.error(f"🔍 FINAL_RESPONSE_TO_FRONTEND type: {type(gemini_response.text)}")
     logger.error(f"🔍 FINAL_RESPONSE_TO_FRONTEND content: {gemini_response.text[:200]}...")
     logger.error(f"🔍 FINAL_RESPONSE_TO_FRONTEND starts with brace: {gemini_response.text.strip().startswith('{')}")
     ```

2. **Check response transformation**:
   - Log the exact JSON being sent:
     ```python
     response_dict = {
         'text': gemini_response.text,
         'mode': mode,
         # ... other fields
     }
     logger.error(f"🔍 RESPONSE_DICT text field: {response_dict['text'][:200]}...")
     ```

### Phase 3: Gemini Service Layer (gemini_service.py)
**Goal**: Understand why JSON detection isn't preventing the issue

1. **In `continue_story()` after detection**:
   - Check what happens after JSON is detected:
     ```python
     if response_text.strip().startswith('{'):
         logger.error("🔍 JSON_DETECTED - raw response_text")
         logger.error(f"🔍 What is structured_response? {type(structured_response)}")
         logger.error(f"🔍 Does structured_response have narrative? {hasattr(structured_response, 'narrative')}")
         # What actually gets returned?
         logger.error(f"🔍 ACTUAL_RETURN_VALUE: {response_text[:200]}...")
     ```

2. **Check extraction logic**:
   - When JSON is detected, what should happen?
   - Is there supposed to be extraction of just the narrative field?
   ```python
   if raw_response.strip().startswith('{'):
       logger.error("🔍 Attempting to extract narrative from JSON")
       # Is this extraction happening?
   ```

### Phase 4: Firebase Service Layer (firebase_service.py)
**Goal**: Check what's being saved to Firestore

1. **In `add_story_entry()`**:
   - Log exactly what's being saved:
     ```python
     logger.error(f"🔍 SAVING_TO_FIRESTORE text: {gemini_response.text[:200]}...")
     logger.error(f"🔍 SAVING_TO_FIRESTORE is JSON: {gemini_response.text.strip().startswith('{')}")
     ```

### Phase 5: Data Retrieval Layer
**Goal**: Check if issue occurs during retrieval

1. **When fetching campaign data**:
   - In `get_campaign()` or similar:
     ```python
     for entry in story:
         logger.error(f"🔍 RETRIEVED_ENTRY text: {entry.get('text', '')[:100]}...")
         logger.error(f"🔍 RETRIEVED_ENTRY is JSON: {entry.get('text', '').strip().startswith('{')}")
     ```

## Data Flow and Schema at Each Layer

### Layer 1: Gemini API Raw Response
**What it returns**: Raw JSON string when in structured mode
```json
{
    "narrative": "[Mode: STORY MODE]\n[SESSION_HEADER]\nTimestamp: Year 11 New Peace...",
    "entities_mentioned": ["Ser Alderon Vance", "Alexiel"],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "player_character_data": { ... },
        "custom_campaign_state": { ... }
    },
    "debug_info": {
        "dm_notes": [...],
        "dice_rolls": [],
        "resources": "HD: 0/1, Lay on Hands: 0/5...",
        "state_rationale": "Updated character_creation progress..."
    }
}
```

**Expected by gemini_service.py**: Either:
- Plain text string (when not using structured generation)
- JSON object (when using structured generation)

### Layer 2: gemini_service.py Response
**What it SHOULD return**: GeminiResponse object with:
```python
GeminiResponse(
    text="[Mode: STORY MODE]\n[SESSION_HEADER]\n...",  # Just the narrative text
    raw_response="{...}",  # Full JSON for debugging
    mode="character",
    structured_response=NarrativeResponse(...),  # Parsed object
    model_used="gemini-2.5-flash"
)
```

**What it ACTUALLY returns** (based on logs):
```python
GeminiResponse(
    text='{\n    "narrative": "[Mode: STORY MODE]...',  # ERROR: Full JSON!
    raw_response='{\n    "narrative": "[Mode: STORY MODE]...',
    mode="character",
    structured_response=NarrativeResponse(...),
    model_used="gemini-2.5-flash"
)
```

### Layer 3: Firebase Service Operations

#### 3A: Firebase WRITE Operation (add_story_entry)

**Input Parameters**:
```python
# Called from main.py line 918
firestore_service.add_story_entry(
    user_id="abc123",
    campaign_id="6hxtUTnluAcZbxDasYkY",
    actor="gemini",
    text='{\n    "narrative": "[Mode: STORY MODE]...',  # ERROR: Full JSON!
    mode="character",
    metadata={...}
)
```

**What gets written to Firestore document**:
```python
# Collection: users/abc123/campaigns/6hxtUTnluAcZbxDasYkY/story
{
    'text': '{\n    "narrative": "[Mode: STORY MODE]...',  # ERROR: Saving JSON!
    'timestamp': server_timestamp(),
    'type': 'ai',  # Based on actor == 'gemini'
    'mode': 'character',
    'sequence_id': 2,  # Auto-incremented
    'metadata': {
        'model_used': 'gemini-2.5-flash',
        'structured_generation': True,
        'token_usage': {...}
    }
}
```

**What SHOULD be written**:
```python
{
    'text': '[Mode: STORY MODE]\n[SESSION_HEADER]\n...',  # Just narrative text
    'timestamp': server_timestamp(),
    'type': 'ai',
    'mode': 'character',
    'sequence_id': 2,
    'metadata': {...}
}
```

#### 3B: Firebase READ Operation (get_campaign)

**When frontend requests campaign data**:
```python
# GET /api/campaigns/6hxtUTnluAcZbxDasYkY
campaign_data = firestore_service.get_campaign(user_id, campaign_id)
```

**What Firebase returns**:
```python
{
    'id': '6hxtUTnluAcZbxDasYkY',
    'title': 'Dragon Knight',
    'premise': 'A brave knight in a land of dragons...',
    'story': [
        {
            'sequence_id': 1,
            'text': '[CHARACTER CREATION - Step 1 of 7]...',  # Good entry
            'type': 'ai',
            'mode': 'god',
            'timestamp': {...}
        },
        {
            'sequence_id': 2,
            'text': '{\n    "narrative": "[Mode: STORY MODE]...',  # ERROR: JSON!
            'type': 'ai',
            'mode': 'character',
            'timestamp': {...}
        }
    ],
    'game_state': {...}
}
```

**Frontend receives in story array**:
```javascript
// story[1] contains:
{
    sequence_id: 2,
    text: '{\n    "narrative": "[Mode: STORY MODE]...',  // Raw JSON string
    type: 'ai',
    mode: 'character'
}
```

### Layer 4: main.py API Response
**What it returns to frontend**:
```json
{
    "text": "{\n    \"narrative\": \"[Mode: STORY MODE]...",
    "mode": "character",
    "state_updates": {...},
    "sequence_id": 2
}
```

**What frontend expects**:
```json
{
    "text": "[Mode: STORY MODE]\n[SESSION_HEADER]\n...",
    "mode": "character",
    "state_updates": {...},
    "sequence_id": 2
}
```

### Layer 5: JavaScript Frontend Display
**What it receives**: The API response above
**What it does**:
1. Takes the `text` field
2. Adds "Scene #X: " prefix based on sequence_id
3. Displays in message div

**Result**: User sees:
```
Scene #2: {
    "narrative": "[Mode: STORY MODE]...
```

## Detailed Logging Plan with Expected vs Actual

### Gemini Service Logging
```python
# In gemini_service.py continue_story()
logger.error("🔍 GEMINI_RAW_RESPONSE type: %s", type(raw_response))
logger.error("🔍 GEMINI_RAW_RESPONSE first 100 chars: %s", raw_response[:100])
logger.error("🔍 GEMINI_RAW_RESPONSE is JSON: %s", raw_response.strip().startswith('{'))

# After parsing
logger.error("🔍 STRUCTURED_RESPONSE type: %s", type(structured_response))
logger.error("🔍 STRUCTURED_RESPONSE has narrative: %s", hasattr(structured_response, 'narrative'))
if hasattr(structured_response, 'narrative'):
    logger.error("🔍 STRUCTURED_RESPONSE.narrative first 100 chars: %s", structured_response.narrative[:100])

# Before returning
logger.error("🔍 GEMINI_RESPONSE.text first 100 chars: %s", response_text[:100])
logger.error("🔍 GEMINI_RESPONSE.text is JSON: %s", response_text.strip().startswith('{'))
logger.error("🔍 EXPECTED: Plain narrative text")
logger.error("🔍 ACTUAL: %s", "JSON" if response_text.strip().startswith('{') else "Plain text")
```

### Firebase Service Logging

#### Write Operation Logging
```python
# In firestore_service.py add_story_entry()
def add_story_entry(user_id, campaign_id, actor, text, mode=None, metadata=None):
    logger.error("🔍 FIREBASE_WRITE_INPUT parameters:")
    logger.error("🔍   - actor: %s", actor)
    logger.error("🔍   - text type: %s", type(text))
    logger.error("🔍   - text length: %s", len(text))
    logger.error("🔍   - text first 200 chars: %s", text[:200])
    logger.error("🔍   - text is JSON: %s", text.strip().startswith('{'))
    logger.error("🔍   - mode: %s", mode)

    # Before writing to Firestore
    story_entry = {
        'text': text,
        'timestamp': server_timestamp(),
        'type': 'ai' if actor == 'gemini' else 'user',
        'mode': mode,
        'sequence_id': next_sequence_id,
        'metadata': metadata
    }

    logger.error("🔍 FIREBASE_WRITE_DOCUMENT being saved:")
    logger.error("🔍   - text field first 200 chars: %s", story_entry['text'][:200])
    logger.error("🔍   - text field is JSON: %s", story_entry['text'].strip().startswith('{'))
    logger.error("🔍   - type: %s", story_entry['type'])
    logger.error("🔍   - sequence_id: %s", story_entry['sequence_id'])

    logger.error("🔍 EXPECTED text format: '[Mode: STORY MODE]\\n[SESSION_HEADER]\\n...'")
    logger.error("🔍 ACTUAL text format: %s", "JSON object" if text.strip().startswith('{') else "Plain narrative text")
```

#### Read Operation Logging
```python
# In firestore_service.py get_campaign()
def get_campaign(user_id, campaign_id):
    # After fetching story documents
    for story_doc in story_docs:
        story_data = story_doc.to_dict()

        logger.error("🔍 FIREBASE_READ_STORY_ENTRY sequence_id=%s:", story_data.get('sequence_id'))
        logger.error("🔍   - text type: %s", type(story_data.get('text')))
        logger.error("🔍   - text first 200 chars: %s", story_data.get('text', '')[:200])
        logger.error("🔍   - text is JSON: %s", story_data.get('text', '').strip().startswith('{'))
        logger.error("🔍   - type: %s", story_data.get('type'))
        logger.error("🔍   - mode: %s", story_data.get('mode'))

        if story_data.get('text', '').strip().startswith('{'):
            logger.error("🔍 WARNING: Story entry %s contains raw JSON!", story_data.get('sequence_id'))

    # Before returning campaign data
    logger.error("🔍 FIREBASE_READ_RETURN total story entries: %s", len(story))
    logger.error("🔍 FIREBASE_READ_RETURN entries with JSON: %s",
                 sum(1 for s in story if s.get('text', '').strip().startswith('{')))
```

### Main.py API Logging
```python
# In interaction route
logger.error("🔍 API_RESPONSE text field first 100 chars: %s", gemini_response.text[:100])
logger.error("🔍 API_RESPONSE text field is JSON: %s", gemini_response.text.strip().startswith('{'))
logger.error("🔍 API_RESPONSE full structure: %s", {
    'text_type': type(gemini_response.text),
    'text_starts_with': gemini_response.text[:50],
    'mode': mode,
    'has_state_updates': bool(getattr(gemini_response, 'state_updates', None))
})
```

### Frontend JavaScript Logging
```javascript
// In api.js after receiving response
console.log('🔍 JS_API_RESPONSE full object:', response);
console.log('🔍 JS_API_RESPONSE.text type:', typeof response.text);
console.log('🔍 JS_API_RESPONSE.text first 100 chars:', response.text.substring(0, 100));
console.log('🔍 JS_API_RESPONSE.text is JSON:', response.text.trim().startsWith('{'));
console.log('🔍 EXPECTED: Plain text like "[Mode: STORY MODE]..."');
console.log('🔍 ACTUAL:', response.text.trim().startsWith('{') ? 'JSON object' : 'Plain text');

// In display function
console.log('🔍 DISPLAY_MESSAGE input:', message);
console.log('🔍 DISPLAY_MESSAGE adding Scene prefix to:', message.text?.substring(0, 50));
```

## Root Cause Hypothesis

Based on the logs, the most likely scenario:
1. Gemini returns raw JSON (which is detected)
2. The code detects this but doesn't extract the narrative field
3. The full JSON is saved to Firestore
4. Frontend receives and displays the raw JSON
5. Frontend adds "Scene #X: " prefix to whatever text it receives

## Critical Code Location

The bug is in `gemini_service.py` where it creates the GeminiResponse object. The flow is:

1. **gemini_service.py** creates GeminiResponse with `narrative_text` = full JSON string
2. **main.py** writes to Firebase using `firestore_service.add_story_entry(..., gemini_response_obj.narrative_text)`
3. **Firebase** stores the full JSON string
4. **Frontend** displays it with "Scene #" prefix

The fix needs to be in `gemini_service.py` where it should extract the narrative:
```python
# Current (buggy) behavior
if use_structured_generation:
    response_text = raw_response  # BUG: Using full JSON!

# Should be:
if use_structured_generation:
    if raw_response.strip().startswith('{'):
        parsed = json.loads(raw_response)
        response_text = parsed.get('narrative', raw_response)
    else:
        response_text = raw_response
```

## Key Finding: Writer to Firebase

**main.py writes to Firebase**, not gemini_service. The exact call is:
```python
# Line 918 in main.py
firestore_service.add_story_entry(user_id, campaign_id, constants.ACTOR_GEMINI, gemini_response_obj.narrative_text)
```

This means `gemini_response_obj.narrative_text` must contain ONLY the narrative text, not the full JSON.

## Fix Strategy (after debugging confirms location)

**If issue is in gemini_service.py**:
- When JSON is detected, extract the `narrative` field before returning
- Ensure only the narrative text is returned, not the full JSON

**If issue is in frontend**:
- Add JSON detection and parsing in JavaScript
- Extract narrative field if JSON is detected

**If issue is systemic**:
- Add a sanitization layer that ensures only narrative text is saved/sent

## Key Questions to Answer

1. **Where is "Scene #" prefix added?** (Frontend likely)
2. **Is the backend returning raw JSON or attempting to extract narrative?**
3. **Is there a missing extraction step when JSON is detected?**
4. **Should the fix be in backend (extract before saving) or frontend (parse on display)?**

## Data Corruption Path Summary

The JSON corruption flows through the system as follows:

1. **Gemini API** → Returns proper JSON with narrative field
2. **gemini_service.py** → Creates GeminiResponse with `narrative_text = full JSON string` ❌
3. **main.py** → Calls `add_story_entry(..., gemini_response_obj.narrative_text)` passing JSON
4. **Firebase Write** → Saves `{'text': '{"narrative": "..."}'}` to Firestore
5. **Firebase Read** → Returns story entry with JSON in text field
6. **Frontend** → Displays "Scene #2: {" with raw JSON

**The corruption happens at step 2** - gemini_service should extract just the narrative.

## Firebase-Specific Verification

To confirm Firebase is just storing what it receives (not causing the issue):

```python
# Temporary debug in main.py before add_story_entry call
logger.error("🔍 MAIN.PY about to save to Firebase:")
logger.error("🔍   - gemini_response_obj.narrative_text type: %s", type(gemini_response_obj.narrative_text))
logger.error("🔍   - gemini_response_obj.narrative_text[:200]: %s", gemini_response_obj.narrative_text[:200])
logger.error("🔍   - is JSON: %s", gemini_response_obj.narrative_text.strip().startswith('{'))

# This will prove that main.py is already receiving JSON from gemini_service
```

## Browser Test Plan with Real APIs

### Test Strategy Using run_ui_tests.sh

Since I can run Playwright tests, here's a comprehensive plan to reproduce the JSON bug with real Gemini and Firebase:

#### 1. **Modify test_campaign_creation_browser.py**
Instead of creating a new test, modify the existing campaign creation test to:
- Create a campaign with the exact premise that triggers the bug
- Continue the campaign 5 times to ensure we hit the JSON issue
- Add extensive logging to capture API responses

#### 2. **Test Execution Plan**
```bash
# Run with REAL APIs (not mock mode)
./run_ui_tests.sh  # No 'mock' argument = real APIs

# Or run specific test directly
TESTING=true USE_MOCKS=false PORT=6006 vpython testing_ui/test_campaign_creation_browser.py
```

#### 3. **Modifications Needed**
```python
# In test_campaign_creation_browser.py, after campaign creation:

# Continue the campaign multiple times
for i in range(5):
    print(f"🔍 Interaction {i+1}: Attempting to trigger JSON bug")

    # Type "2" if this is the first interaction (character creation)
    if i == 0:
        page.fill("#userInput", "2")  # Choose AI character generation
    else:
        page.fill("#userInput", "continue")  # Just continue

    # Submit and wait
    page.press("#userInput", "Enter")
    time.sleep(5)  # Wait for AI response

    # Check for JSON in display
    story_entries = page.query_selector_all(".message-bubble")
    if story_entries:
        last_entry = story_entries[-1].inner_text()
        if "narrative" in last_entry and "{" in last_entry:
            print(f"🔍 JSON BUG DETECTED at interaction {i+1}!")
            print(f"🔍 Content: {last_entry[:200]}...")
            self.take_screenshot(page, f"json_bug_interaction_{i+1}")
```

#### 4. **Console Injection for API Monitoring**
Add this to the page initialization:
```javascript
page.add_init_script("""
    // Intercept and log all API responses
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        console.log('🔍 API_REQUEST:', args[0]);
        const response = await originalFetch.apply(window, args);
        const clone = response.clone();

        try {
            const data = await clone.json();
            console.log('🔍 API_RESPONSE:', {
                url: args[0],
                status: response.status,
                hasText: !!data.text,
                textIsJSON: data.text && data.text.trim().startsWith('{'),
                textPreview: data.text ? data.text.substring(0, 100) : null
            });

            if (data.text && data.text.trim().startsWith('{')) {
                console.error('🚨 JSON BUG: API returned JSON in text field!');
                console.error('Full text:', data.text);
            }
        } catch (e) {}

        return response;
    };
""")
```

#### 5. **Backend Logging Setup**
Before running the test, add these logs:

**In main.py** (line ~918):
```python
logger.error("🔍 MAIN.PY before add_story_entry:")
logger.error("🔍   narrative_text type: %s", type(gemini_response_obj.narrative_text))
logger.error("🔍   narrative_text[:200]: %s", gemini_response_obj.narrative_text[:200])
logger.error("🔍   is JSON: %s", gemini_response_obj.narrative_text.strip().startswith('{'))
```

**In gemini_service.py** (in continue_story):
```python
# Right before returning GeminiResponse
logger.error("🔍 GEMINI_SERVICE creating response:")
logger.error("🔍   response_text type: %s", type(response_text))
logger.error("🔍   response_text[:200]: %s", response_text[:200])
logger.error("🔍   response_text is JSON: %s", response_text.strip().startswith('{'))
```

**In firestore_service.py** (in add_story_entry):
```python
logger.error("🔍 FIRESTORE add_story_entry:")
logger.error("🔍   text param[:200]: %s", text[:200])
logger.error("🔍   text is JSON: %s", text.strip().startswith('{'))
```

#### 6. **Expected Output**
The test should:
1. Create a campaign successfully
2. On first interaction (typing "2"), trigger the JSON bug
3. Capture screenshots showing "Scene #2: {" with raw JSON
4. Log the exact JSON being passed through each layer
5. Confirm the bug happens between gemini_service and main.py

#### 7. **Data Collection**
After running, we'll have:
- Screenshots at each step
- Browser console logs showing API responses
- Server logs showing data flow through each layer
- Exact confirmation of where narrative extraction fails

## Complete Execution Plan - Risk-Free Implementation

### Pre-Flight Checklist

1. **Verify environment**:
   ```bash
   # Check we're on correct branch
   git branch --show-current  # Should show: json_fix_v3

   # Check virtual environment
   source venv/bin/activate
   which python  # Should show venv python

   # Verify Playwright is installed
   python -c "import playwright; print('✅ Playwright ready')"

   # Verify test server can start
   TESTING=true PORT=6006 vpython mvp_site/main.py serve &
   sleep 3
   curl http://localhost:6006 && echo "✅ Server works"
   kill %1
   ```

2. **Backup current code**:
   ```bash
   cp mvp_site/gemini_service.py mvp_site/gemini_service.py.backup
   cp mvp_site/main.py mvp_site/main.py.backup
   cp mvp_site/firestore_service.py mvp_site/firestore_service.py.backup
   ```

### Phase 1: Add Comprehensive Logging (10 min)

1. **Create a dedicated test that WILL reproduce the bug**:
   - Don't modify existing test, create new one for safety
   - Include explicit premise that triggers character creation
   - Add multiple verification points

2. **Add logging at ALL critical points**:
   - gemini_service.py: Log raw response AND processed response
   - main.py: Log before AND after getting narrative_text
   - firestore_service.py: Log input AND what gets saved
   - Add try-catch around logging to prevent crashes

3. **Add frontend detection**:
   - Inject console logging in browser
   - Take screenshots at each step
   - Save HTML content for analysis

### Phase 2: Red Test - Prove Bug Exists (15 min)

1. **Create red test that MUST fail**:
   ```python
   # test_json_bug_red.py
   def test_narrative_should_not_contain_json():
       # Create campaign, interact with "2"
       # Assert that response.text does NOT start with '{'
       # This WILL FAIL, proving bug exists
   ```

2. **Run and capture failure**:
   - Save test output showing failure
   - Take screenshot of JSON display
   - Log the exact JSON being shown

### Phase 3: Implement Fix (20 min)

1. **Fix location confirmed**: gemini_service.py

2. **Safe fix implementation**:
   ```python
   # In gemini_service.py, find where response_text is set
   # Add extraction logic:
   if use_structured_generation and raw_response.strip().startswith('{'):
       try:
           parsed = json.loads(raw_response)
           response_text = parsed.get('narrative', raw_response)
           logger.info("✅ Extracted narrative from JSON response")
       except json.JSONDecodeError:
           logger.error("Failed to parse JSON, using raw response")
           response_text = raw_response
   ```

3. **Add defensive checks**:
   - Validate narrative is a string
   - Add fallback if parsing fails
   - Log success/failure of extraction

### Phase 4: Green Test - Prove Fix Works (15 min)

1. **Run same test - should now PASS**:
   - No JSON in displayed text
   - Proper narrative shown
   - Screenshots prove fix

2. **Run comprehensive test suite**:
   ```bash
   # Ensure we didn't break anything
   ./run_tests.sh
   ```

### Phase 5: Integration Test with Browser (20 min)

1. **Full browser test with real APIs**:
   ```bash
   # This will use real Gemini and Firebase
   TESTING=true vpython testing_ui/test_json_bug_fixed.py
   ```

2. **Verify multiple scenarios**:
   - Character creation (option 2)
   - Normal story continuation
   - Combat scenarios
   - State updates still work

### Phase 6: Final Verification (10 min)

1. **Check all logs confirm fix**:
   - gemini_service extracts narrative
   - main.py receives plain text
   - firestore saves plain text
   - frontend displays correctly

2. **Create summary report**:
   ```markdown
   # JSON Bug Fix Summary
   - Bug: Raw JSON displayed to users
   - Root cause: gemini_service returning full JSON as narrative_text
   - Fix: Extract narrative field when structured generation returns JSON
   - Verification: Red test failed, green test passed
   - Screenshots: Before/after in /tmp/worldarchitectai/browser/
   ```

### Rollback Plan (if needed)

If anything goes wrong:
```bash
# Restore backups
cp mvp_site/gemini_service.py.backup mvp_site/gemini_service.py
cp mvp_site/main.py.backup mvp_site/main.py
cp mvp_site/firestore_service.py.backup mvp_site/firestore_service.py

# Check git diff
git diff
```

### Success Criteria

You'll return to:
1. ✅ Red test showing bug exists (failed as expected)
2. ✅ Fix implemented with proper extraction
3. ✅ Green test showing bug fixed (passed)
4. ✅ Browser screenshots proving fix works visually
5. ✅ All existing tests still passing
6. ✅ Comprehensive logs showing data flow
7. ✅ No JSON ever reaching the frontend

### Automation Script

Create `fix_json_bug.sh`:
```bash
#!/bin/bash
set -e  # Exit on error

echo "🚀 Starting JSON bug fix process..."

# Phase 1: Add logging
echo "📝 Phase 1: Adding logging..."
python add_json_logging.py

# Phase 2: Red test
echo "🔴 Phase 2: Running red test (expect failure)..."
TESTING=true vpython mvp_site/tests/test_json_bug_red.py || echo "✅ Red test failed as expected"

# Phase 3: Apply fix
echo "🔧 Phase 3: Applying fix..."
python apply_json_fix.py

# Phase 4: Green test
echo "🟢 Phase 4: Running green test (expect pass)..."
TESTING=true vpython mvp_site/tests/test_json_bug_green.py

# Phase 5: Browser test
echo "🌐 Phase 5: Running browser integration test..."
./run_ui_tests.sh test_json_bug_fixed.py

echo "✅ JSON bug fix complete!"
```

This plan is designed to run without intervention and handle edge cases gracefully.

## Resolution Summary

### Root Cause Identified
The bug occurred in `parse_structured_response()` in `narrative_response_schema.py`. When JSON parsing failed (due to malformed JSON), the function would fall through to a final fallback case that returned the raw input text unchanged. This raw JSON would then flow through the entire system and be displayed to users.

### Fix Implementation
Added defensive JSON detection and extraction in `_process_structured_response()` in `gemini_service.py`:
1. Detects when response_text starts with `{` (JSON indicator)
2. Attempts multiple extraction methods:
   - JSON parsing to extract 'narrative' field
   - Regex extraction as fallback
   - User-friendly error message as last resort
3. Ensures users NEVER see raw JSON, even with malformed responses

### Test Results
- ✅ RED test proved bug existed (would show JSON)
- ✅ GREEN test proves fix works (extracts narrative correctly)
- ✅ All existing tests still pass
- ✅ Multiple edge cases handled

### Code Changes
- `mvp_site/gemini_service.py`: Added JSON detection and extraction logic (lines 482-510)
- `mvp_site/main.py`: Added debug logging to trace data flow
- Added 6 new test files to verify fix comprehensively

### Verification
The fix has been tested with:
- Well-formed JSON (works correctly)
- Malformed JSON (now handled gracefully)
- Empty responses (returns error message)
- Various edge cases (all handled)

### GitHub
- Branch: json_fix_v3
- Commit: ba975b5
- Ready for PR: https://github.com/jleechan2015/worldarchitect.ai/pull/new/json_fix_v3
