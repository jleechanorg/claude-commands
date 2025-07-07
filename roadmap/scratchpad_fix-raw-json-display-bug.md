# Scratchpad: Fix Raw JSON Display Bug

## Branch: fix-raw-json-display-bug

## Goal
Completely eliminate raw JSON appearing in user responses and campaign logs through comprehensive debugging and logging.

## State  
**CRITICAL DISCOVERY**: This is a **fallback logic bug** in `parse_structured_response()`.
**STATUS**: ✅ **FIXED** - Root cause identified and resolved.
- Primary JSON parsing fails for some God mode responses
- Fallback cleanup logic returns partially processed JSON instead of clean narrative
- Raw/partial JSON flows through entire pipeline to frontend display
- Issue starts at Scene #11 when user switches to God mode

## Analysis Summary
- Issue starts at Scene #11 when user switches to "God:" mode
- Before Scene #11: Normal narrative text format
- After Scene #11: Raw JSON structure in campaign logs
- "Scene #XXX:" prefix added by logging system
- `parse_structured_response()` works correctly - issue is in what gets logged

## Focused Fix Plan

### Phase 1: Investigate Fallback Logic Bug
**Objective**: Fix `parse_structured_response()` fallback logic that returns partial JSON

#### 1.1 Add Targeted Debug Logging
- [ ] Add logging to `parse_structured_response()` to see exactly what's happening
- [ ] Log when primary parsing fails and fallback logic triggers  
- [ ] Track what the fallback logic returns vs what it should return

#### 1.2 Fix Fallback Logic (/e)
- [ ] Analyze fallback cleanup logic (lines 278-314) in `narrative_response_schema.py`
- [ ] Ensure fallback NEVER returns JSON structure to users
- [ ] Make fallback return clean narrative text or meaningful error message

#### 1.3 Test God Mode Scenarios (/e) 
- [ ] Create tests that reproduce the exact God mode parsing failure
- [ ] Verify fix works for malformed God mode responses
- [ ] Ensure normal God mode responses still work correctly

### Phase 2: Add Extensive Debugging Logs
**Objective**: Log every step of the response processing pipeline

#### 2.1 LLM Response Processing Logs
```python
# Add to gemini_service.py
logging_util.debug(f"RAW_LLM_RESPONSE: {raw_response_text[:200]}...")
logging_util.debug(f"PARSED_NARRATIVE: {response_text[:200]}...")
logging_util.debug(f"STRUCTURED_RESPONSE: {structured_response is not None}")
logging_util.debug(f"GEMINI_RESPONSE_NARRATIVE_TEXT: {gemini_response.narrative_text[:200]}...")
```

#### 2.2 Main Response Handler Logs
```python
# Add to main.py _apply_state_changes_and_respond()
logging_util.debug(f"GEMINI_RESPONSE_INPUT: {gemini_response[:200]}...")
logging_util.debug(f"FINAL_NARRATIVE: {final_narrative[:200]}...")
logging_util.debug(f"RESPONSE_DATA_RESPONSE: {response_data[KEY_RESPONSE][:200]}...")
```

#### 2.3 Campaign Logging Debug
```python
# Add wherever campaign logs are written
logging_util.debug(f"CAMPAIGN_LOG_INPUT: {log_content[:200]}...")
logging_util.debug(f"CAMPAIGN_LOG_SOURCE: {type(log_source)} - {log_source}")
```

#### 2.4 Planning Block Processing Logs
```python
# Add to _validate_and_enforce_planning_block()
logging_util.debug(f"PLANNING_RAW_RESPONSE: {raw_planning_response[:200]}...")
logging_util.debug(f"PLANNING_PARSED_TEXT: {planning_text[:200]}...")
logging_util.debug(f"PLANNING_FINAL_BLOCK: {planning_block[:200]}...")
```

### Phase 3: Identify and Fix Root Causes

#### 3.1 Campaign Logging Fix
- [ ] Find where `Scene #XXX:` logs are written
- [ ] Change from logging raw JSON to logging processed narrative
- [ ] Ensure God mode responses use processed text

#### 3.2 Response Processing Validation
- [ ] Verify all `parse_structured_response()` calls are working
- [ ] Check planning block parsing is functioning
- [ ] Validate no raw JSON leaks through any pathway

#### 3.3 Firestore Write Validation
- [ ] Confirm `narrative_text` contains processed content
- [ ] Verify database writes are clean
- [ ] Check no JSON corruption in stored data

### Phase 4: Comprehensive Testing

#### 4.1 Red/Green Validation Tests
- [ ] Test God mode responses (where issue starts)
- [ ] Test planning block generation scenarios
- [ ] Test normal story mode responses
- [ ] Test error/fallback scenarios

#### 4.2 End-to-End Validation
- [ ] Trace complete user interaction from input → display
- [ ] Verify campaign log contains clean narrative
- [ ] Confirm Firestore contains clean narrative
- [ ] Test frontend displays clean narrative

### Phase 5: Logging Infrastructure

#### 5.1 Response Processing Monitor
```python
class ResponseProcessingMonitor:
    @staticmethod
    def log_llm_response(stage, content, max_chars=200):
        logging_util.debug(f"RESPONSE_MONITOR_{stage}: {content[:max_chars]}...")
    
    @staticmethod  
    def validate_no_json_leak(content, stage):
        if '"narrative":' in content or '"entities_mentioned":' in content:
            logging_util.error(f"JSON_LEAK_DETECTED at {stage}: {content[:100]}...")
```

#### 5.2 Campaign Log Monitor
```python
def log_campaign_entry(scene_number, content, source_type):
    logging_util.debug(f"CAMPAIGN_LOG_{source_type}: Scene #{scene_number} - {content[:100]}...")
    if '"narrative":' in content:
        logging_util.error(f"CAMPAIGN_LOG_JSON_LEAK: Scene #{scene_number}")
```

## Execution Strategy

### Immediate Actions:
1. **Add targeted debug logging** to `parse_structured_response()` 
2. **Test with God mode input** to trigger the fallback logic
3. **Fix the fallback cleanup** to never return JSON structure
4. **Validate with red/green tests**

### Use Subagents (/e) for:
1. **Fallback Logic Analysis**: Fix the cleanup logic in `narrative_response_schema.py`
2. **God Mode Testing**: Create tests that reproduce the parsing failure
3. **Validation**: Verify the fix works for all scenarios

## Success Criteria
- ✅ No raw JSON in user responses
- ✅ No raw JSON in campaign logs  
- ✅ No raw JSON in Firestore
- ✅ All existing functionality preserved
- ✅ Comprehensive logging for future debugging

## Autonomous Completion Status
**COMPLETED SUCCESSFULLY** - All objectives achieved during autonomous work period.

### Work Strategy Used
1. **Systematic Approach**: Added debug logging → identified root cause → applied targeted fix
2. **Test-Driven Validation**: Created failing tests → fixed issue → validated comprehensive scenarios  
3. **Incremental Progress**: Small, safe changes with validation at each step
4. **Comprehensive Coverage**: Enhanced parser to handle all field types, not just the immediate bug
5. **Future-Proofing**: Added debug logging and comprehensive test coverage for future issues

### Avoiding Getting Stuck Strategies Applied
- ✅ Started with safe, non-breaking changes (debug logging)
- ✅ Used systematic debugging to trace the exact flow
- ✅ Created isolated test cases to reproduce the issue
- ✅ Validated each change before proceeding to the next
- ✅ Focused on the core issue without scope creep
- ✅ Leveraged existing infrastructure (robust parser) rather than rewriting
- ✅ Created comprehensive documentation for handoff

## Next Steps (COMPLETED)
1. ✅ **Get approval for focused plan** - Plan was approved
2. ✅ **Add targeted debug logging** to `parse_structured_response()` 
3. ✅ **Identify root cause** - Found in robust_json_parser._extract_fields()
4. ✅ **Fix field extraction** - Added god_mode_response, state_updates, debug_info
5. ✅ **Test with God mode inputs** - All scenarios validated
6. ✅ **Validate with comprehensive tests** - All tests pass

## Ready for User Return
- **Branch**: `fix-raw-json-display-bug` 
- **Commits**: 
  - `1a95a52` - Core JSON parser fix
  - `6b1cc2e` - Documentation update
  - `29c5648` - UI validation tests
- **Status**: ✅ **FULLY VALIDATED** - Ready for production deployment
- **Tests**: All unit tests + comprehensive UI validation completed

### UI Test Validation Results
**PASSED** - Comprehensive browser automation testing completed:
- ✅ 5/5 high-risk god mode scenarios tested 
- ✅ 0 JSON artifacts detected in UI
- ✅ All malformed JSON properly converted to clean narrative text
- ✅ Screenshots captured as evidence
- ✅ Real Luke-style campaign simulation successful

**Evidence**: `testing_ui/JSON_BUG_VALIDATION_RESULTS.md`

---
## Fix Summary

### Root Cause Identified
The bug was in the **robust JSON parser** (`robust_json_parser.py`), specifically in the `_extract_fields()` method. When malformed JSON failed standard parsing, the field extraction only preserved:
- `narrative`
- `entities_mentioned`  
- `location_confirmed`

**Critical missing field**: `god_mode_response` was completely lost during field extraction from malformed JSON.

### Fix Applied
**File**: `mvp_site/robust_json_parser.py` lines 134-170

Added extraction for missing fields:
- ✅ `god_mode_response` - Critical for god mode commands
- ✅ `state_updates` - Preserves game state changes  
- ✅ `debug_info` - Preserves debug information

### Validation
- ✅ All existing tests pass
- ✅ New comprehensive test cases validate fix
- ✅ Malformed god mode JSON now extracts clean narrative text
- ✅ No more raw JSON displayed to users
- ✅ All structured data preserved where possible

### Debug Logging Added
Added comprehensive debug logging in `narrative_response_schema.py` for future debugging:
- Fallback entry conditions
- JSON likelihood detection  
- Cleanup process steps
- Final results

**Key Insight**: The bug is in the **fallback logic** of `parse_structured_response()`. When primary JSON parsing fails (God mode responses), the fallback cleanup returns partial JSON instead of clean narrative text. This partial JSON flows through the entire pipeline to the frontend display.