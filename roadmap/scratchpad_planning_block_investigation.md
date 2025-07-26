# Planning Block Investigation Scratchpad

## Overview
This document maps all planning_block handling across the WorldArchitect.AI codebase, separating JSON field handlers from narrative parsing logic.

## Subagent 1 Results: Backend Mapping

### JSON Field Constants
**File: constants.py:35**
Function: Module-level constant
Type: JSON field
Purpose: Defines the structured field key for planning blocks
Code snippet: `FIELD_PLANNING_BLOCK = 'planning_block'`

### Core JSON Response Schema
**File: narrative_response_schema.py:31**
Function: NarrativeResponse.__init__
Type: JSON field
Purpose: Defines planning_block as a structured field in the response schema
Code snippet: `planning_block: str = None,`

**File: narrative_response_schema.py:44**
Function: NarrativeResponse.__init__
Type: JSON field
Purpose: Initialize planning_block field with default empty string
Code snippet: `self.planning_block = planning_block or ""`

**File: narrative_response_schema.py:99**
Function: NarrativeResponse.to_dict
Type: JSON field
Purpose: Include planning_block in dictionary export
Code snippet: `"planning_block": self.planning_block,`

**File: narrative_response_schema.py:227**
Function: parse_structured_response
Type: JSON field
Purpose: Extract planning_block from parsed JSON data
Code snippet: `planning_block = parsed_data.get('planning_block', '')`

**File: narrative_response_schema.py:274**
Function: parse_structured_response
Type: JSON field
Purpose: Extract planning_block in fallback parsing
Code snippet: `planning_block = parsed_data.get('planning_block', '')`

**File: narrative_response_schema.py:283**
Function: parse_structured_response
Type: JSON field
Purpose: Include planning_block in known fields for NarrativeResponse
Code snippet: `'planning_block': planning_block`

### Response Object Properties
**File: gemini_response.py:78-82**
Function: GeminiResponse.planning_block (property)
Type: JSON field
Purpose: Property accessor for planning_block from structured response
Code snippet:
```python
@property
def planning_block(self) -> str:
    """Get planning block from structured response."""
    if self.structured_response and hasattr(self.structured_response, 'planning_block'):
        return self.structured_response.planning_block or ""
    return ""
```

### Narrative Parsing (Legacy/Deprecated)
**File: gemini_response.py:311**
Function: GeminiResponse._strip_all_debug_tags
Type: Narrative parsing
Purpose: Remove planning block sections from narrative text (deprecated pattern)
Code snippet: `text = re.sub(r'--- PLANNING BLOCK ---.*?$', '', text, flags=re.DOTALL)`

**File: gemini_response.py:334**
Function: GeminiResponse._detect_debug_tags_static
Type: Narrative parsing
Purpose: Detect if narrative contains planning block markers (deprecated)
Code snippet: `'planning_block': '--- PLANNING BLOCK ---' in text,`

### Planning Block Validation & Generation
**File: gemini_service.py:1031-1045**
Function: _validate_and_enforce_planning_block
Type: JSON field & generation
Purpose: Main function to validate planning blocks and generate if missing
Code snippet: Full function signature and docstring

**File: gemini_service.py:1063-1065**
Function: _validate_and_enforce_planning_block
Type: JSON field
Purpose: Check if planning_block exists in structured response
Code snippet:
```python
if structured_response and hasattr(structured_response, 'planning_block') and structured_response.planning_block and structured_response.planning_block.strip():
    logging_util.info("Planning block found in JSON structured response")
    return response_text
```

**File: gemini_service.py:1140-1149**
Function: _validate_and_enforce_planning_block
Type: JSON field
Purpose: Parse planning block generation response
Code snippet:
```python
planning_text, structured_planning_response = _parse_gemini_response(raw_planning_response, context="planning_block")
# If we got a structured response with planning_block field, use that
if (structured_planning_response and
    hasattr(structured_planning_response, 'planning_block') and
    structured_planning_response.planning_block):
    planning_block = structured_planning_response.planning_block
else:
    # Fall back to plain text
    planning_block = planning_text
```

**File: gemini_service.py:1164-1168**
Function: _validate_and_enforce_planning_block
Type: JSON field
Purpose: Update structured_response.planning_block with generated content
Code snippet:
```python
structured_response.planning_block = clean_planning_block
logging_util.info(f"Updated structured_response.planning_block with {len(clean_planning_block)} characters")
```

### Main Application Integration
**File: main.py:361**
Function: add_interaction (within)
Type: JSON field
Purpose: Extract planning_block from structured response for API response
Code snippet: `response_data['planning_block'] = getattr(structured_response, 'planning_block', '')`

### Structured Fields Utilities
**File: structured_fields_utils.py:24**
Function: extract_structured_fields
Type: JSON field
Purpose: Extract planning_block from GeminiResponse object for consistent handling
Code snippet: `constants.FIELD_PLANNING_BLOCK: getattr(gemini_response_obj.structured_response, constants.FIELD_PLANNING_BLOCK, '') or '',`

### Key Findings Summary

1. **Primary Source**: Planning blocks are now exclusively handled via JSON fields, not narrative parsing
2. **JSON Field Name**: `planning_block` (defined in constants.py as `FIELD_PLANNING_BLOCK`)
3. **Response Path**:
   - Generated by Gemini → Parsed in `narrative_response_schema.py` → Stored in `NarrativeResponse.planning_block`
   - Accessed via `GeminiResponse.planning_block` property → Sent to frontend in API response
4. **Validation Logic**: `_validate_and_enforce_planning_block` checks JSON field first, generates if missing
5. **Legacy Support**: Narrative parsing patterns still exist but are deprecated and marked for removal

## Subagent 2 Results: Frontend Implementation

### JSON Field Handling in API Response
**File: app.js:221-224**
Function: generateStructuredFieldsHTML
Type: JSON field handling
Purpose: Check for planning_block field in fullData and render it
Code snippet:
```javascript
// Add planning block if present (always at the bottom)
if (fullData.planning_block) {
    const parsedPlanningBlock = parsePlanningBlocks(fullData.planning_block);
    html += `<div class="planning-block">${parsedPlanningBlock}</div>`;
}
```

### Main Narrative Parsing Function
**File: app.js:359-453**
Function: parsePlanningBlocks
Type: Narrative parsing (now applied to JSON field content)
Purpose: Parse planning block text content to extract choices and create interactive buttons
Key features:
- Parses numbered format: "1. **ActionName** - Description"
- Parses simple numbered format: "1. ActionName"
- Parses bracket format: "**[ActionName]:** Description"
- Creates HTML buttons with data attributes for each choice
- Adds "Custom Action" button as final option
- Returns HTML with choice buttons in `.planning-block-choices` div

### Story Entry Rendering
**File: app.js:259-319**
Function: appendToStory
Type: JSON field handling
Purpose: Main function that appends story entries and structured fields
Key points:
- Line 306: Calls generateStructuredFieldsHTML which includes planning_block rendering
- Lines 313-318: Adds click handlers to newly created choice buttons
- IMPORTANT: Line 298 comment shows that narrative parsing for planning blocks was REMOVED

### Choice Button Event Handling
**File: app.js:322-356**
Function: handleChoiceClick
Type: Event handling
Purpose: Handle clicks on planning block choice buttons
Features:
- Extracts choice text and ID from button data attributes
- Special handling for "Custom" choice (focuses input field)
- For predefined choices: disables all buttons and submits form automatically
- Sets choice text in user input field before submission

### Interaction Form Integration
**File: app.js:581**
Function: resumeCampaign (within appendToStory call)
Type: JSON field handling
Purpose: Pass full response data including planning_block to appendToStory
Code snippet: `appendToStory(entry.actor, entry.text, entry.mode, debugMode, entry.user_scene_number, entry);`

**File: app.js:721**
Function: interaction form submit handler
Type: JSON field handling
Purpose: Pass API response data including planning_block to appendToStory
Code snippet: `appendToStory('gemini', narrativeText, null, data.debug_mode || false, data.user_scene_number, data);`

### Button Re-enabling
**File: app.js:731-733, 738-740**
Function: interaction form submit handler
Type: Event handling
Purpose: Re-enable choice buttons after receiving new response or on error

### CSS Styling
**File: planning-blocks.css**
Type: UI styling
Purpose: Visual styling for planning block choice buttons
Key classes:
- `.planning-block-choices`: Container for buttons
- `.choice-button`: Individual button styling
- `.choice-button-custom`: Special styling for custom action button
- Theme-specific adjustments for dark, fantasy, and cyberpunk themes

### Key Frontend Findings

1. **Data Flow**:
   - API response → `data.planning_block` → `generateStructuredFieldsHTML` → `parsePlanningBlocks` → HTML buttons

2. **Parsing Location**:
   - Planning blocks are parsed from the JSON field content, NOT from narrative text
   - The `parsePlanningBlocks` function operates on `fullData.planning_block` string

3. **Button Mechanics**:
   - Each button stores choice ID and full text in data attributes
   - Click handler automatically fills input and submits form
   - Buttons are disabled during API calls to prevent double submission

4. **Important Note**:
   - Comment at line 298 explicitly states planning block parsing from narrative was REMOVED
   - All planning block content now comes through the structured JSON field

## Subagent 3 Results: PR #502 Analysis

### PR Context
- The user mentioned PR #500, but based on git history and commit analysis, the actual planning block fixes were in PR #473
- PR #473: "Fix planning block choice buttons not working" (merged commit 41db2d0e)
- The PR/commit numbers in the user's request appear to be incorrect

### Key Changes Identified

#### 1. Frontend Fix - app.js (Commit 1d37f3d3)
**Purpose**: Fix planning block choice buttons not generating from JSON field
**Change**: Modified `generateStructuredFieldsHTML` to call `parsePlanningBlocks()` on the JSON field content
```javascript
// Before:
html += `<div class="planning-block">${fullData.planning_block}</div>`;

// After:
const parsedPlanningBlock = parsePlanningBlocks(fullData.planning_block);
html += `<div class="planning-block">${parsedPlanningBlock}</div>`;
```
**Impact**: This ensures the planning_block JSON field content is parsed to generate interactive choice buttons

#### 2. Test File - test_planning_block_json_first_fix.py
**Purpose**: Document and test the JSON-first architecture for planning blocks
**Key Test Cases**:
- `test_user_reported_issue`: Shows the problem where planning blocks appear in narrative text instead of JSON field
- `test_frontend_receives_correct_data`: Verifies API response structure with planning_block in JSON field only

**Critical Finding**: The test explicitly documents that:
- Planning blocks should ONLY come from the JSON field
- Narrative text should NOT contain planning block content
- Frontend should parse from `data.planning_block`, not from narrative text

#### 3. CSS Styling Updates (Commit d79e5459)
**Purpose**: Make planning block buttons more compact
**Changes**: Reduced padding, margins, font sizes, and border widths for a cleaner look

### Architecture Confirmation

The changes in PR #473 (not #500/502) actually SUPPORT the JSON-first architecture:

1. **JSON Field is Primary**: The fix ensures planning blocks come from `fullData.planning_block` (JSON field)
2. **Parsing Applied to JSON**: The `parsePlanningBlocks()` function now processes JSON field content, not narrative
3. **Test Validation**: Tests explicitly validate that planning blocks should NOT be in narrative text
4. **Frontend Comment**: app.js line 298 has a comment stating planning block parsing from narrative was REMOVED

### Files That Don't Exist
The following files mentioned in the user's request do not exist in the codebase:
- mvp_site/planning_block_extractor.py
- mvp_site/json_response_utils.py
- mvp_site/testing_ui/test_planning_block_buttons.py
- mvp_site/testing_ui/test_planning_blocks_display_simple.py

### Conclusion
PR #473 (not #500/502) actually strengthened the JSON-first architecture by:
1. Fixing the frontend to properly parse planning blocks from the JSON field
2. Adding tests that explicitly validate JSON-first behavior
3. Documenting that narrative text should NOT contain planning blocks

The changes do NOT contradict JSON-first architecture - they reinforce it.

## Subagent 3 Execution Results: Test Consolidation

### Test Files Analyzed
1. **test_planning_block_enforcement.py** - Tests narrative "--- PLANNING BLOCK ---" markers (DEPRECATED)
2. **test_planning_block_json_corruption_fix.py** - Tests JSON parsing (CONSOLIDATED)
3. **test_planning_block_json_first_fix.py** - Tests JSON-first architecture (CONSOLIDATED)
4. **test_planning_block_simplified.py** - Tests simplified prompts with narrative markers (DEPRECATED)
5. **test_planning_blocks_ui.py** - UI tests (KEEP)

### Actions Taken
1. Created `test_planning_block_json.py` - Consolidated JSON handling tests from:
   - test_planning_block_json_first_fix.py
   - test_planning_block_json_corruption_fix.py

2. Removed original files after consolidation

3. Identified deprecated tests that need removal:
   - test_planning_block_enforcement.py (tests narrative markers)
   - test_planning_block_simplified.py (tests narrative generation)

### Test Coverage Status
- ✅ JSON field handling: Fully covered in test_planning_block_json.py
- ✅ UI rendering: Covered in test_planning_blocks_ui.py
- ❌ Narrative parsing: Deprecated tests to be removed
- ✅ Edge cases: Added empty/null handling tests

### Next Steps
1. Remove test_planning_block_enforcement.py (all narrative marker tests)
2. Remove test_planning_block_simplified.py (deprecated prompt tests)
3. Update any remaining tests that check for narrative markers
4. Run test suite to verify coverage

## Subagent 5 Execution Results: Final Verification

### Test Results
- ✅ All planning block tests passing after fixes
- ✅ test_planning_block_json.py - 7 tests OK
- ✅ test_planning_block_robustness.py - 10 tests OK
- ✅ test_planning_blocks_ui.py - 4 tests OK

### Codebase Search Results
- ❌ No "PLANNING BLOCK" markers found in production code
- ✅ Only references are in documentation/scratchpad files
- ✅ All prompts updated to use JSON-only approach
- ✅ Frontend uses only JSON field (no narrative parsing)

### Complete Change Summary

#### Files Removed (6 files)
1. mvp_site/gemini_response.py - Removed planning block regex patterns
2. mvp_site/prompts/game_state_instruction.md - Removed narrative markers
3. mvp_site/tests/test_planning_block_enforcement.py - Deprecated tests
4. mvp_site/tests/test_planning_block_json_first_fix.py - Consolidated
5. mvp_site/tests/test_planning_block_json_corruption_fix.py - Consolidated
6. mvp_site/tests/test_planning_block_simplified.py - Deprecated tests

#### Files Added (2 files)
1. mvp_site/tests/test_planning_block_json.py - Consolidated JSON tests
2. mvp_site/tests/test_planning_block_robustness.py - Edge case tests

#### Files Modified (4 files)
1. mvp_site/narrative_response_schema.py - Added validation methods
2. mvp_site/static/app.js - Enhanced error handling
3. mvp_site/static/css/planning-blocks.css - Added error styles
4. roadmap/scratchpad_planning_block_investigation.md - Documentation

### Architecture Summary
The system now implements pure JSON-first architecture:
- Planning blocks ONLY come from `planning_block` JSON field
- No narrative text parsing for planning blocks
- Robust edge case handling throughout
- Clear separation of concerns

## Subagent 4 Results: Comprehensive Analysis & Recommendations

### 1. Complete Codepath Inventory

#### JSON Field Codepaths (PRIMARY - IN USE)
1. **Backend Generation → Storage**:
   - Gemini API generates response with planning_block in JSON
   - `narrative_response_schema.py:parse_structured_response()` extracts from JSON
   - Stored in `NarrativeResponse.planning_block` field
   - Accessed via `GeminiResponse.planning_block` property

2. **Backend Validation & Generation**:
   - `gemini_service.py:_validate_and_enforce_planning_block()` checks JSON field
   - If missing, generates planning block and updates JSON field
   - Updates `structured_response.planning_block` directly

3. **API Response Path**:
   - `main.py:361` extracts planning_block from structured response
   - `structured_fields_utils.py:24` provides consistent extraction utility
   - Sent to frontend as `response_data['planning_block']`

4. **Frontend Display Path**:
   - API response → `data.planning_block`
   - `app.js:generateStructuredFieldsHTML()` checks for field
   - `app.js:parsePlanningBlocks()` parses content into interactive buttons
   - Rendered in `.planning-block` div with choice buttons

#### Narrative Parsing Codepaths (DEPRECATED - TO BE REMOVED)
1. **Backend Stripping**:
   - `gemini_response.py:_strip_all_debug_tags()` - removes planning block markers from narrative
   - `gemini_response.py:_detect_debug_tags_static()` - detects planning block markers

2. **Frontend Parsing**:
   - ALREADY REMOVED per comment at app.js:298
   - `parsePlanningBlocks()` now only operates on JSON field content

### 2. Classification Table

| Component | Main Branch Status | PR #473 Changes | Classification |
|-----------|-------------------|-----------------|----------------|
| **Backend Schema** | ✅ JSON field defined | No changes | JSON Field |
| **Response Parsing** | ✅ Extracts from JSON | No changes | JSON Field |
| **Validation Logic** | ✅ Checks JSON first | No changes | JSON Field |
| **API Response** | ✅ Sends JSON field | No changes | JSON Field |
| **Frontend Display** | ❌ Bug: Not parsing | ✅ Fixed: Now parses | JSON Field |
| **Narrative Stripping** | ⚠️ Still present | No changes | Narrative (Deprecated) |
| **Narrative Detection** | ⚠️ Still present | No changes | Narrative (Deprecated) |

### 3. PR #500 Assessment (Actually PR #473)

**Finding**: The user referenced PR #500, but the actual planning block fixes were in PR #473.

**PR #473 Impact**:
- ✅ **SUPPORTS** JSON-first architecture
- ✅ Fixed bug where JSON field content wasn't being parsed into buttons
- ✅ Added tests that validate JSON-first behavior
- ❌ Does NOT add narrative parsing - actually reinforces JSON approach

**Is PR #473 needed?**
- YES - It's already merged and was critical to fix the button generation bug
- The fix ensures planning blocks from JSON fields are properly displayed

**Value provided**:
- Makes planning block choices actually clickable (they were broken before)
- Validates the JSON-first architecture with comprehensive tests
- Documents the expected behavior clearly

### 4. Recommendations

#### A. Safe Removal Opportunities
1. **Remove deprecated narrative parsing functions**:
   ```python
   # gemini_response.py
   - _strip_all_debug_tags() - line 311 regex for planning blocks
   - _detect_debug_tags_static() - line 334 detection logic
   ```

2. **Clean up narrative markers**:
   - Remove any prompts that instruct Gemini to add "--- PLANNING BLOCK ---" markers
   - Update documentation to reflect JSON-only approach

#### B. Ensure JSON Path Completeness
1. **Validation improvements**:
   - Add unit tests for `_validate_and_enforce_planning_block()`
   - Test edge cases: empty planning blocks, malformed JSON, etc.

2. **Error handling**:
   - Ensure frontend gracefully handles missing planning_block field
   - Add logging for planning block generation failures

#### C. Missing JSON Handling
1. **Frontend robustness**:
   - Add null checks before calling `parsePlanningBlocks()`
   - Handle case where planning_block exists but is empty string

2. **Backend consistency**:
   - Ensure all response paths include planning_block field (even if empty)
   - Standardize empty vs null handling

#### D. Code Cleanup Opportunities
1. **Remove dead code**:
   - Narrative parsing functions in gemini_response.py
   - Any prompt templates with planning block markers

2. **Consolidate logic**:
   - Move planning block parsing to a dedicated module
   - Create shared constants for planning block formats

### 5. Risk Assessment

#### What could break if we remove narrative parsing?
1. **Low Risk**: Frontend already doesn't use narrative parsing (removed per comment)
2. **Medium Risk**: If any legacy prompts still generate narrative markers, they'd appear in output
3. **Mitigation**: Search all prompt templates for "PLANNING BLOCK" before removal

#### Required Tests Before Removal
1. **Integration tests**:
   - Verify planning blocks work end-to-end with JSON field only
   - Test with various planning block formats

2. **Regression tests**:
   - Ensure no narrative text contains planning block markers
   - Verify `_strip_all_debug_tags()` isn't used for other purposes

3. **UI tests**:
   - Confirm choice buttons generate correctly
   - Test button click functionality

### 6. Executive Summary

**Current State**: Planning blocks use JSON-first architecture with some legacy narrative code
**PR #473 Impact**: Fixed critical bug and reinforced JSON approach (NOT contradictory)
**Action Items**:
1. ✅ Keep PR #473 - it's essential and already merged
2. 🧹 Remove deprecated narrative parsing code
3. 🔧 Add robustness to JSON handling
4. 📝 Update documentation to reflect JSON-only approach

**Conclusion**: The system is correctly designed for JSON-first planning blocks. PR #473 fixed a bug in that system rather than adding narrative parsing. The narrative parsing code is legacy and can be safely removed after proper testing.
