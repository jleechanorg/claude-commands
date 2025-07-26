# UI Debug Mode Verification Plan

**Goal**: Prove that ALL structured response fields are properly displayed in the UI, with screenshots of each element.

## Expected UI Elements to Verify

Based on the sample JSON response, we need to verify these elements appear in the UI:

1. **Session Header** (`session_header`)
   - Should show: Timestamp, Location, Status, HP, XP, Gold, Resources, Conditions, etc.
   - Style: Gray background, monospace font, at top of response

2. **Narrative** (`narrative`)
   - The main story text
   - Should be in the middle with "Scene #X:" label

3. **Dice Rolls** (`dice_rolls`)
   - Should show as a bulleted list
   - Style: Green background with dice emoji 🎲

4. **Resources** (`resources`)
   - Quick summary of resources
   - Style: Yellow background with chart emoji 📊

5. **Planning Block** (`planning_block`)
   - "What would you like to do next?" with numbered options
   - Style: Blue background, at bottom of response

6. **Debug Info** (`debug_info`) - ONLY IN DEBUG MODE
   - DM notes and state rationale
   - Style: Gray background with debug icon 🔍

## Test Plan

### Phase 1: Setup
1. Start test server with `TESTING=true`
2. Create browser test file
3. Navigate with test mode URL parameters

### Phase 2: Campaign Creation
1. Create a new campaign with debug mode ENABLED
2. Verify initial story displays with session header

### Phase 3: Trigger Combat Response
1. Send input: "I attack the goblin with my sword"
2. Wait for AI response that should include ALL fields

### Phase 4: Screenshot Each Element
Take individual screenshots of:
1. Full response container
2. Session header section
3. Narrative section
4. Dice rolls section
5. Resources section
6. Planning block section
7. Debug info section

### Phase 5: Verification
1. Check each element exists in DOM
2. Verify correct CSS classes applied
3. Confirm content matches expected format
4. Save all screenshots with descriptive names

## Implementation Steps

### Step 1: Create Comprehensive Test File
```python
# test_ui_all_elements_debug.py
- Use Playwright to automate browser
- Create campaign with debug mode ON
- Send combat action to trigger all fields
- Take targeted screenshots
```

### Step 2: Element Selectors
```javascript
// Session Header
.story-entry .session-header

// Narrative (main text)
.story-entry > p

// Dice Rolls
.story-entry .dice-rolls

// Resources
.story-entry .resources

// Planning Block
.story-entry .planning-block

// Debug Info (only in debug mode)
.story-entry .debug-info
```

### Step 3: Verification Checklist
- [ ] Server started with TESTING=true
- [ ] Test URL includes ?test_mode=true
- [ ] Campaign created with debug mode enabled
- [ ] Combat action triggers full response
- [ ] Session header visible with character stats
- [ ] Narrative text displayed with proper label
- [ ] Dice rolls shown in green box with bullets
- [ ] Resources shown in yellow box
- [ ] Planning block shown in blue box at bottom
- [ ] Debug info shown in gray box (debug mode only)
- [ ] All screenshots saved

## Expected Results

Each screenshot should show:

1. **screenshot_1_full_response.png**
   - Complete story entry with all elements

2. **screenshot_2_session_header.png**
   - Gray box with character status info

3. **screenshot_3_narrative.png**
   - "Scene #X:" followed by story text

4. **screenshot_4_dice_rolls.png**
   - Green box with "🎲 Dice Rolls:" and bullet list

5. **screenshot_5_resources.png**
   - Yellow box with "📊 Resources:" and resource list

6. **screenshot_6_planning_block.png**
   - Blue box with "--- PLANNING BLOCK ---" and numbered options

7. **screenshot_7_debug_info.png**
   - Gray box with "🔍 Debug Info:" and JSON content

## Success Criteria

✅ All 6 main elements visible in normal mode
✅ Debug info additionally visible in debug mode
✅ Each element has distinct visual styling
✅ Content matches expected format from JSON
✅ Screenshots clearly show each element
✅ No JavaScript errors in console

## Test Code Structure

```python
def test_all_ui_elements_debug_mode():
    # 1. Setup and navigation
    # 2. Create debug mode campaign
    # 3. Send combat action
    # 4. Wait for response
    # 5. Take screenshots of each element
    # 6. Verify all elements present
    # 7. Save verification report
```

This plan ensures we thoroughly test and document that the UI properly displays ALL structured response fields, proving the fix works completely.
