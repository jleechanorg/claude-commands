# TASK-140: Hard Stop for Integrity Failures - Requirements & Implementation

## Task Overview
Implement hard stop mechanism for unrecoverable integrity failures when LLM doesn't generate state updates, with error display in debug mode and user-friendly messages in normal mode.

## Current Problem
- **Silent Failures**: When LLM fails to generate state updates, system proceeds silently
- **User Confusion**: Same options presented back to user without indication of failure
- **No Error Visibility**: Users don't know when integrity failures occur
- **Recovery Unclear**: No guidance on how to recover from failures

## Autonomous Implementation Requirements

### Phase 1: Integrity Failure Detection (45 min)
1. **State Update Validation Points:**
   - After every LLM call in `gemini_service.py`
   - Before processing LLM responses in game state logic
   - During JSON parsing and state updates
   
2. **Failure Detection Criteria:**
   - Missing `state_updates` field in LLM response
   - Empty or null state updates when expected
   - Malformed JSON that can't be parsed
   - Critical game state fields missing after update

3. **Detection Implementation:**
   ```python
   def validate_state_integrity(llm_response, expected_updates):
       if not llm_response.get('state_updates'):
           raise IntegrityFailureError("Missing state updates")
       # Additional validation logic
   ```

### Phase 2: Hard Stop Implementation (30 min)
1. **Exception Handling:**
   - Create `IntegrityFailureError` exception class
   - Catch failures at LLM response processing points
   - Halt game progression immediately on detection
   
2. **Error Context Collection:**
   - Capture full LLM request and response
   - Record game state before failure
   - Log user action that triggered failure
   - Generate unique error ID for tracking

3. **Graceful Stopping:**
   - Prevent further game actions
   - Preserve game state before failure
   - Clear any in-progress operations

### Phase 3: Error Display System (45 min)
1. **Debug Mode Error Display:**
   - Show full Python traceback in separate error modal
   - Display complete LLM request/response details
   - Include game state context and user action
   - Provide error ID for support reference

2. **Normal Mode User-Friendly Error:**
   - Simple message: "Game encountered an error and cannot continue"
   - Hide technical details from user
   - Provide general recovery guidance
   - Include error ID for reporting

3. **Error Modal/Display:**
   - Separate error section/modal (not inline in narrative)
   - Clear distinction between debug and normal mode
   - Professional error presentation

### Phase 4: Recovery Options (30 min)
1. **User Recovery Actions:**
   - **Retry**: Attempt the same action again
   - **Reload**: Refresh page to latest valid state
   - **Abort**: End session gracefully
   - **Report**: Submit error for investigation

2. **State Recovery:**
   - Revert to last known good game state
   - Clear any partial/corrupted updates
   - Reset UI to stable state

3. **Error Logging:**
   - Log all integrity failures for analysis
   - Include context for debugging
   - Track recovery success rates

## Implementation Strategy

### Files to Modify:
1. **`mvp_site/gemini_service.py`** - Add integrity validation after LLM calls
2. **`mvp_site/game_state.py`** - Add state update validation
3. **Frontend templates** - Add error display modal/section
4. **Error handling modules** - Create IntegrityFailureError class

### Error Detection Points:
```python
# After LLM call
response = call_gemini_api(prompt)
validate_state_integrity(response)

# Before state update
if not response.get('state_updates'):
    raise IntegrityFailureError("No state updates provided")

# During JSON processing
try:
    updates = json.loads(response['state_updates'])
except (KeyError, JSONDecodeError) as e:
    raise IntegrityFailureError(f"Invalid state updates: {e}")
```

### Error Display Logic:
```python
def handle_integrity_failure(error, debug_mode=False):
    if debug_mode:
        show_debug_error(error, traceback, llm_context)
    else:
        show_user_friendly_error(error.id, generic_message)
```

## Success Criteria
- [ ] All LLM response points have integrity validation
- [ ] System immediately halts on missing state updates
- [ ] Debug mode shows full traceback and LLM context
- [ ] Normal mode shows user-friendly error messages
- [ ] Error display appears in separate modal/section (not inline)
- [ ] Users can retry, reload, or abort on failure
- [ ] All integrity failures are logged for analysis
- [ ] Game state preserved at point of failure
- [ ] Recovery options work correctly

## Error Scenarios to Handle
1. **Missing state_updates field** - Most common failure
2. **Empty state_updates** - LLM provided field but no content
3. **Malformed JSON** - Invalid JSON structure
4. **Partial state corruption** - Some fields missing or invalid
5. **Network/API failures** - Connection issues during LLM call

## Dependencies
- Access to LLM response processing pipeline
- Frontend error display capabilities
- Logging system for error tracking
- Game state management functions

## Estimated Time: 2.5 hours
- Detection implementation: 45 minutes
- Hard stop mechanism: 30 minutes
- Error display system: 45 minutes
- Recovery options: 30 minutes
- Testing and validation: 20 minutes

## Testing Plan
1. **Simulate integrity failures** by modifying LLM responses
2. **Test debug mode** error display with full details
3. **Test normal mode** user-friendly error messages
4. **Verify recovery options** work correctly
5. **Confirm logging** captures all necessary context
6. **Test state preservation** during failures

## Expected Outcomes
1. **No more silent failures** - All integrity issues immediately visible
2. **Clear error communication** - Users understand when problems occur
3. **Debugging capability** - Full context available in debug mode
4. **Graceful degradation** - System fails safely with recovery options
5. **Better reliability** - Faster detection and resolution of integrity issues