# Plan to Fix Remaining Tests and Resolve Conflicts

## Current Situation
- 7 tests are failing due to moved functions (StateHelper and strip functions moved from main.py to gemini_response.py)
- Need to check for GitHub merge conflicts
- User will be away for 7 hours

## Step-by-Step Plan

### 1. Check for Merge Conflicts
- Use `gh pr view 424 --json mergeable,mergeStateStatus` to check PR status
- If conflicts exist, pull latest main and resolve

### 2. Fix Remaining Test Imports
The following tests need fixing:
- test_debug_logging.py
- test_main.py
- test_main_god_mode.py
- test_debug_mode_e2e.py
- test_main_routes_comprehensive.py
- test_debug_mode.py
- test_main_auth_state_phase2.py

### 3. Import Fix Strategy
For each test file:

#### Option A: Direct Import Replacement
```python
# OLD:
from main import StateHelper, strip_debug_content

# NEW:
from gemini_response import GeminiResponse

# Create wrapper for compatibility
class StateHelper:
    @staticmethod
    def strip_debug_content(text):
        return GeminiResponse._strip_debug_content(text)
    
    @staticmethod
    def strip_state_updates_only(text):
        return GeminiResponse._strip_state_updates_only(text)

# Or direct function wrappers
strip_debug_content = GeminiResponse._strip_debug_content
strip_state_updates_only = GeminiResponse._strip_state_updates_only
```

#### Option B: Mock the Functions in Tests
For tests that are specifically testing main.py integration, we might need to mock these functions instead of importing them.

### 4. Special Considerations

#### test_main.py and test_main_routes_comprehensive.py
These likely test the Flask routes and might need special handling since they test the integration layer.

#### test_debug_mode_e2e.py
End-to-end test might need to test the actual flow through main.py, so we need to ensure the test still validates the correct behavior.

### 5. Verification Steps
1. Run each test individually to verify it passes
2. Run full test suite
3. Check that no new issues were introduced
4. Verify the fix maintains the test's original intent

### 6. Final Steps
1. Commit all fixes
2. Push to GitHub
3. Verify CI passes
4. Leave summary for user

## Implementation Order
1. Check and resolve any merge conflicts first
2. Fix test_debug_logging.py (likely straightforward)
3. Fix test_main_auth_state_phase2.py (we saw the specific error)
4. Fix test_debug_mode.py and test_debug_mode_e2e.py (related tests)
5. Fix test_main.py, test_main_god_mode.py, test_main_routes_comprehensive.py (integration tests, need careful handling)

## Risk Mitigation
- Make small, incremental changes
- Test each fix individually before moving to the next
- Keep original test intent intact
- If a test is testing main.py behavior specifically, ensure the test still validates that behavior even with the moved functions