# Planning Block Visual Verification Test

## Overview

The `test_planning_block_visual.py` test is designed to visually verify that planning blocks are rendered correctly in the browser, with proper HTML rendering and button display rather than raw JSON or text.

## What It Tests

1. **Normal Planning Blocks**: Verifies that planning blocks with choices render as proper HTML with clickable buttons
2. **Empty Planning Blocks**: Tests rendering when there are no choices available
3. **Special Characters**: Ensures proper HTML escaping for characters like `<>`, `&`, quotes, etc.
4. **Multiple Planning Blocks**: Verifies multiple planning blocks can be displayed on screen simultaneously
5. **Button Hover States**: Captures visual feedback when hovering over choice buttons
6. **Raw Content Detection**: Checks for any unrendered JSON or HTML in the output

## Running the Test

### Quick Run
```bash
./testing_ui/run_planning_block_visual_test.sh
```

### Manual Run
```bash
# Activate virtual environment
source venv/bin/activate

# Start test server (if not already running)
TESTING=true PORT=6006 python mvp_site/main.py serve &

# Run the test
TESTING=true python testing_ui/test_planning_block_visual.py
```

## Screenshots

The test saves screenshots to `/tmp/worldarchitectai/browser/planning_block_visual/`:

- `01_initial_page.png` - Initial page load
- `02_game_view.png` - Game view loaded
- `03_normal_planning_block.png` - Planning block with choice buttons
- `04_button_hover_state.png` - Button hover visual effect
- `05_multiple_planning_blocks.png` - Multiple blocks on screen
- `06_unescaped_content_block_*.png` - Any blocks with rendering issues
- `07_empty_planning_block.png` - Empty planning block (if found)
- `08_special_characters_response.png` - Response with special characters
- `09_final_full_page.png` - Final full page capture

## Test Requirements

- Python virtual environment activated
- Playwright installed in venv
- Test server running on port 6006
- Test mode URL parameters: `?test_mode=true&test_user_id=test-user-123`

## Success Criteria

✅ **PASS** if:
- Planning blocks render as structured HTML
- Choice buttons are visible and clickable
- No raw JSON strings like `"choices": [...]` visible
- No unescaped HTML tags in output
- Special characters properly escaped

❌ **FAIL** if:
- Raw JSON visible in planning blocks
- Buttons rendered as text (e.g., `<button>...</button>`)
- Unescaped special characters breaking layout
- JavaScript errors preventing rendering

## Debugging

If the test fails:

1. Check screenshots for visual issues
2. Look for error screenshots in the output directory
3. Run with a visible browser: Change `headless=True` to `headless=False` in the test
4. Check browser console for JavaScript errors
5. Verify the mock service is returning proper planning block data

## Related Files

- `mvp_site/static/js/game.js` - Frontend rendering logic
- `mvp_site/gemini_service.py` - Backend structured response generation
- `testing_ui/mock_services.py` - Mock service planning block generation
