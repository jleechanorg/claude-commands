# Code Execution JSON Parsing Fix - Verification

## Problem Identified from GCP Logs

### Error Pattern
From GCP logs for campaign `yxU6r6UuGFthtDvVsxSl` on server `mvp-site-app-s6`:

```
2026-01-16 02:11:51,833 - root - ERROR - 🔥🔴 campaign_id=yxU6r6UuGFthtDvVsxSl | 
Failed to parse JSON response: Expecting value: line 1 column 2 (char 1) 
Error at position 1. Content hash: 4e1cfb4ed18e114f
```

### Root Cause Analysis

1. **Code Execution Was Active**: Logs show:
   ```
   GEMINI_CODE_EXECUTION_PARTS[continue_story]: model=gemini-3-flash-preview 
   evidence={'code_execution_used': True, 'executable_code_parts': 1, 
   'code_execution_result_parts': 1, 'stdout': '[{"notation": "1d20+799"...}]\n', 
   'stdout_is_valid_json': True}
   ```

2. **Error Position Analysis**: 
   - Error: "Expecting value: line 1 column 2 (char 1)"
   - Position 1 means the **second character** was invalid
   - This suggests the response started with a single invalid character (likely whitespace or code output) before the JSON

3. **Pattern Observed**:
   - Code execution outputs valid JSON in `stdout` (dice rolls as arrays)
   - Main response text has artifacts (whitespace/code output) before the actual JSON object
   - Parser fails because it tries to parse from the start, hitting invalid characters

## Fix Implementation

### Code Changes
**File**: `mvp_site/narrative_response_schema.py`

Added code execution artifact removal logic in `parse_structured_response()`:

1. **Detects non-JSON prefixes**: Checks if response doesn't start with `{`
2. **Finds actual JSON start**: 
   - If array `[` comes first, finds the `{` that comes **after** the array closes
   - Otherwise finds the first `{` or `[`
3. **Removes prefix**: Strips everything before the JSON start character
4. **Logs removal**: Records how many characters were removed for debugging

### Test Coverage

**File**: `mvp_site/tests/test_code_execution_json_parsing.py`

Created comprehensive test suite with 10 test cases covering:
- ✅ Whitespace prefixes (newlines, tabs, spaces)
- ✅ Code execution stdout output before JSON
- ✅ Array output before JSON object (production scenario)
- ✅ Mixed code execution output
- ✅ Production error pattern reproduction
- ✅ Edge cases (carriage returns, markdown blocks)

**All 10 tests pass** ✅

## Verification Method

### 1. GCP Log Analysis
Used `gcloud logging read` to query production logs:

```bash
gcloud logging read \
  'resource.type=cloud_run_revision AND 
   resource.labels.service_name=mvp-site-app-s6 AND 
   textPayload=~"yxU6r6UuGFthtDvVsxSl" AND 
   textPayload=~"Expecting value"' \
  --limit=5
```

**Findings**:
- Multiple instances of "Expecting value: line 1 column 2 (char 1)" errors
- All occurred when code execution was active (`GEMINI_CODE_EXECUTION_PARTS`)
- Error position 1 indicates response started with invalid character before JSON

### 2. Error Pattern Matching
The error "Expecting value: line 1 column 2 (char 1)" specifically indicates:
- **Line 1**: First line of response
- **Column 2**: Second character position  
- **Char 1**: Character at index 1 (0-indexed)

This pattern matches responses that start with:
- Single whitespace character + JSON
- Single code output character + JSON
- Array output + newline + JSON object

### 3. Test Reproduction
Created tests that reproduce the exact error pattern:
- `test_code_execution_error_position_one`: Tests the specific "char 1" error
- `test_code_execution_production_scenario`: Tests realistic production scenario
- `test_code_execution_with_array_first`: Tests array-before-object pattern

All tests **pass** with the fix, confirming it handles the production error pattern.

## How to Verify Fix Works in Production

### Before Fix (Current State)
1. Check logs for campaign `yxU6r6UuGFthtDvVsxSl`:
   ```bash
   gcloud logging read \
     'resource.type=cloud_run_revision AND 
      resource.labels.service_name=mvp-site-app-s6 AND 
      textPayload=~"yxU6r6UuGFthtDvVsxSl" AND 
      textPayload=~"Invalid JSON"' \
     --limit=10
   ```
   **Expected**: Multiple "Invalid JSON response received" errors

### After Fix (Post-Deployment)
1. **Monitor for error reduction**:
   - Same query should show fewer/no "Invalid JSON" errors
   - Look for log message: "Removed code execution prefix (X chars) before JSON"

2. **Check for successful parsing**:
   ```bash
   gcloud logging read \
     'resource.type=cloud_run_revision AND 
      resource.labels.service_name=mvp-site-app-s6 AND 
      textPayload=~"yxU6r6UuGFthtDvVsxSl" AND 
      textPayload=~"Removed code execution prefix"' \
     --limit=10
   ```
   **Expected**: Log entries showing prefix removal and successful parsing

3. **Verify user experience**:
   - Campaign should no longer show "Invalid JSON response received" messages
   - Scenes should generate successfully even with code execution active

## Summary

✅ **Problem Verified**: GCP logs confirmed JSON parsing failures when code execution artifacts precede JSON  
✅ **Root Cause Identified**: Response text starts with invalid characters before actual JSON  
✅ **Fix Implemented**: Code execution artifact removal in `parse_structured_response()`  
✅ **Tests Created**: Comprehensive test suite with 10 passing tests  
✅ **Verification Plan**: GCP log monitoring strategy documented  

The fix addresses the production issue by removing code execution artifacts before JSON parsing, preventing "Expecting value: line 1 column 2 (char 1)" errors.
