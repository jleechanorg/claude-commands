# Scratchpad: JSON Debug Red/Green Perspective

## Branch: json_debug_redgreen_perspective

## Goal
Debug the raw JSON display issue with a fresh perspective, following proper debugging protocols.

## Bug Report
User is seeing raw JSON in campaign logs. Example from UI:
```
Scene #2: {
    "narrative": "[Mode: STORY MODE]\n[CHARACTER CREATION - Step 2 of 7]...",
    "god_mode_response": "",
    "entities_mentioned": ["Mark Grayson", "Nolan"],
    ...
}
```

## Test Instructions

### Prerequisites
1. Ensure you have a working Python virtual environment
2. Playwright must be installed for browser tests
3. You need a test account or Firebase emulator

### Running the UI Test

#### Option 1: Using the test runner script (RECOMMENDED)
```bash
# From project root
./run_ui_tests.sh mock
```

This will:
- Activate virtual environment
- Verify Playwright installation
- Start test server on port 6006
- Run all UI tests with mock APIs
- Generate screenshots in `/tmp/worldarchitectai/browser/`

#### Option 2: Manual browser test
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Start test server
TESTING=true PORT=6006 python mvp_site/main.py serve &

# 3. Run specific test (if created)
TESTING=true python testing_ui/test_json_bug_scenario.py
```

#### Option 3: Manual testing in browser
1. Start the server as above
2. Navigate to http://localhost:6006
3. Create a new campaign with this exact prompt:
   ```
   Play as Nolan's son. He's offering you to join him. TV show invincible
   ```
4. Continue the story for 5 turns
5. Check if raw JSON appears in the story display

### What to Look For
1. Check the story display area for any JSON artifacts like:
   - `"narrative": "..."`
   - `"entities_mentioned": [...]`
   - Complete JSON structures
2. Note WHERE the "Scene #X:" prefix appears relative to any JSON
3. Use browser DevTools Network tab to inspect actual API responses

### Debugging Approach (MANDATORY)
Per CLAUDE.md debugging protocol:

1. **Trace Complete Data Flow**: Backend → API → Frontend → Display
   - Check actual API response in browser DevTools
   - Search for "Scene #" in both .py and .js files
   - Don't assume formatting comes from backend

2. **Question Assumptions**:
   - Is "Scene #2: {json}" one string or two parts?
   - Where is "Scene #" added - backend or frontend?
   - What does the raw API response actually contain?

3. **Verify Before Fixing**:
   - Add logging at multiple points
   - Test hypothesis with minimal changes
   - Never implement complex fixes based on assumptions

## Key Files to Check
- `mvp_site/static/app.js` - Frontend display logic
- `mvp_site/main.py` - API endpoints
- `mvp_site/gemini_service.py` - AI response processing
- `mvp_site/narrative_response_schema.py` - JSON parsing
- `mvp_site/firestore_service.py` - Database storage

## Status
- [ ] Fresh perspective analysis started
- [ ] Data flow traced end-to-end
- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Fix verified with tests