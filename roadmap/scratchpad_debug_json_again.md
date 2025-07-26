# Debug JSON Display Bug - Investigation Scratchpad

**Branch**: `luke_campaign_fixes`
**Issue**: Raw JSON still being displayed to users instead of parsed narrative content
**Context**: 90-95% used - critical for complex debugging

## Problem Statement

User is still seeing raw JSON output like this:
```json
{
    "narrative": "[Mode: STORY MODE]\n[CHARACTER CREATION - Step 2 of 7]\n\nExcellent choice!...",
    "entities_mentioned": ["Aerion Vance"],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "custom_campaign_state": {
            "character_creation": {
                "in_progress": true,
                "current_step": 2
            }
        }
    },
    "debug_info": {
        "dm_notes": ["Player chose AI character generation"],
        "dice_rolls": [],
        "resources": "HD: 1/1"
    }
}
```

**Expected**: Only the narrative content should display, not the full JSON structure.

## Investigation Completed

### 1. Red Test Created ✅
**File**: `mvp_site/tests/test_raw_json_display_bug_reproduction.py`

**Key Findings**:
- ✅ `parse_structured_response()` function works correctly
- ✅ When given raw JSON, it properly extracts just the narrative content
- ❌ **THE BUG**: Raw JSON is being displayed WITHOUT going through the parsing function

**Test Results**:
- `test_parse_structured_response_works_correctly()` - PASSES ✅
- `test_reproduce_actual_raw_json_display_bug()` - FAILS ❌ (RED test confirming bug)

### 2. Root Cause Identified
The issue is NOT in the parsing logic itself. The problem is that somewhere in the system, raw JSON responses are being displayed directly to users without calling `parse_structured_response()`.

## Major Work Completed This Session

### Entity Schema Consolidation ✅
- **REMOVED**: `entities_simple.py` (422 lines) - eliminated dual validation system
- **ENHANCED**: `entities_pydantic.py` - now single source of truth
- **FIXED**: `entity_tracking.py` - always uses Pydantic, removed environment switching
- **RESULT**: Simplified from dual validation to single robust Pydantic system

### Critical Bug Fixes ✅
1. **NPC Display Name Bug**: Fixed `create_from_game_state` to use "name" field instead of dictionary key
2. **HP Field Mapping Bug**: Added support for both "hp_current" and "hp" keys
3. **Gender Validation Bug**: Added model validator for NPC gender requirement
4. **Test Failures**: Fixed all 8 failing tests systematically (following new CLAUDE.md rule)

### Process Improvements ✅
- **Added to CLAUDE.md**: "NEVER DISMISS FAILING TESTS" rule - mandate systematic debugging
- **PR Description**: Updated to reflect fundamental architectural changes
- **Documentation**: Simplified verbose NPC field section
- **Function Signatures**: Fixed parameter naming consistency

### Files Modified This Session
- `mvp_site/schemas/entities_pydantic.py` - Major enhancements, bug fixes
- `mvp_site/entity_tracking.py` - Simplified to Pydantic-only
- `CLAUDE.md` - Added test failure handling rule
- `mvp_site/prompts/game_state_instruction.md` - Simplified NPC documentation
- Multiple test files - Fixed for Pydantic V2 compatibility
- **DELETED**: `entities_simple.py`, `tmp/luke_campaign_log.txt`

## Current Status: Raw JSON Bug

### What We Know ✅
1. **Parsing function works**: `parse_structured_response()` correctly extracts narrative
2. **Bug location**: Raw JSON bypass - not going through parsing
3. **User impact**: Full JSON structure displayed instead of clean narrative
4. **Test coverage**: Red test reproduces the exact issue

### What We Need ❌
1. **Find the display logic**: Where raw JSON is shown to users
2. **Identify bypass point**: Why parsing is being skipped
3. **Fix the routing**: Ensure all responses go through `parse_structured_response()`
4. **Green test**: Verify fix works end-to-end

## Next Steps (Fresh Context Recommended)

### Investigation Needed
1. **Search for response display logic** in gemini_service.py, main.py, API routes
2. **Find god mode response handling** - where JSON gets returned to frontend
3. **Trace the response path** from LLM → parsing → user display
4. **Check if god_mode_response field** is being handled correctly

### Files to Investigate
- `mvp_site/gemini_service.py` - Main LLM interaction logic
- `mvp_site/main.py` - Flask routes and response handling
- `mvp_site/api_routes.py` - API endpoints
- Frontend JavaScript - Response display logic

### Context Limitations
- **Current**: 90-95% context used
- **Recommendation**: Use subagents for complex multi-file debugging
- **Alternative**: Fresh context session focused solely on JSON display bug

## Test Files Created
- ✅ `test_raw_json_display_bug_reproduction.py` - Red test confirming bug exists

## Branch Status
- **Branch**: `luke_campaign_fixes`
- **PR**: #351 - https://github.com/jleechan2015/worldarchitect.ai/pull/351
- **Status**: All architectural changes complete, JSON bug remains
- **Tests**: All original failing tests fixed, new red test for JSON bug added

## Todos Status
1. ✅ Create red test to reproduce raw JSON display bug
2. ❌ Identify where raw JSON is displayed instead of parsed (NEEDS FRESH CONTEXT)

---
*Session completed with successful red test creation and bug reproduction confirmation*
