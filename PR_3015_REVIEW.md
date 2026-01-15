# PR #3015 Review: Campaign Upgrade Agent

## Summary
This PR adds a comprehensive campaign tier progression system (mortal → divine → sovereign) with upgrade ceremonies. Overall, the implementation is solid, but there are several issues that should be addressed.

## 🔴 Critical Issues

### 1. **Potential Race Condition: Upgrade Type Stale State**
**Location:** `mvp_site/agents.py:1414-1415`

**Issue:** `CampaignUpgradeAgent.__init__` captures `_upgrade_type` at initialization time, but the upgrade availability could change between agent creation and when `build_system_instructions()` is called. If the upgrade type changes or becomes unavailable, the agent may load the wrong ceremony prompt.

**Impact:** Medium - Could lead to incorrect ceremony prompts being loaded

**Recommendation:**
```python
def build_system_instructions(self, ...):
    # Re-check upgrade type at instruction build time, not just at init
    upgrade_type = None
    if self.game_state:
        upgrade_type = self.game_state.get_pending_upgrade_type()
    
    if upgrade_type == "multiverse":
        # ...
```

### 2. **Missing Error Handling for Prompt File Loading**
**Location:** `mvp_site/agents.py:1451-1464`

**Issue:** `_load_instruction_file()` can raise `FileNotFoundError` or `ValueError` if prompt files are missing. The `CampaignUpgradeAgent.build_system_instructions()` method doesn't handle these exceptions, which could crash the entire request.

**Impact:** High - Could cause 500 errors if prompt files are missing

**Recommendation:** Add try/except around `_load_instruction_file()` calls with fallback behavior:
```python
try:
    parts.append(_load_instruction_file(constants.PROMPT_TYPE_DIVINE_ASCENSION))
except (FileNotFoundError, ValueError) as e:
    logging_util.error(f"Failed to load ascension prompt: {e}")
    # Fallback: add a generic upgrade instruction
    parts.append("# Campaign Upgrade Ceremony\n\nUpgrade ceremony in progress...")
```

### 3. **Redundant XP Calculation**
**Location:** `mvp_site/constants.py:705-725`

**Issue:** In `get_xp_for_level()`, when calculating for level >= 26, the function:
1. First calculates XP for levels 21-25 (lines 706-708)
2. Then recalculates XP at level 25 again (lines 713-715)
3. Uses the second calculation

This is inefficient and confusing, though not incorrect.

**Impact:** Low - Performance/readability issue

**Recommendation:** Use the already-calculated `xp` value:
```python
# Divine levels 26+: exponential formula
if level >= 26:
    # XP at level 25 was already calculated above
    xp_at_25 = xp  # Use the value we already have
    
    # Base XP to go from 25→26
    base_divine_xp = 27_000
    
    # Calculate cumulative XP for divine levels
    for lvl in range(26, level + 1):
        level_cost = int(base_divine_xp * (DIVINE_XP_GROWTH_RATE ** (lvl - 25)))
        xp += level_cost
```

## ⚠️ Medium Priority Issues

### 4. **Missing Validation: None Upgrade Type with Active Upgrade**
**Location:** `mvp_site/agents.py:1465-1470`

**Issue:** If `get_pending_upgrade_type()` returns `None` but `is_campaign_upgrade_available()` returns `True`, the agent will log a warning but continue with incomplete instructions. This could happen if there's a race condition or state inconsistency.

**Impact:** Medium - Could lead to confusing user experience

**Recommendation:** Add validation:
```python
if self._upgrade_type is None:
    if self.game_state and self.game_state.is_campaign_upgrade_available():
        logging_util.error(
            "CAMPAIGN_UPGRADE: Upgrade available but type not determined. "
            "This indicates a state inconsistency."
        )
    # Fallback gracefully
```

### 5. **Potential Integer Overflow in XP Calculation**
**Location:** `mvp_site/constants.py:724`

**Issue:** For very high levels (100+), the exponential XP calculation `base_divine_xp * (1.15 ** (lvl - 25))` could produce extremely large numbers. At level 100, this is ~7.3 billion XP, which is fine, but at level 200+ it could exceed Python's int limits or cause performance issues.

**Impact:** Low - Edge case, but should have a safety cap

**Recommendation:** Add a level cap or overflow check:
```python
# Safety cap for very high levels
if level > 200:
    logging_util.warning(f"Level {level} exceeds recommended maximum (200)")
    level = 200  # Cap at reasonable maximum
```

### 6. **Missing Type Validation in get_campaign_tier()**
**Location:** `mvp_site/game_state.py:1748-1752`

**Issue:** `get_campaign_tier()` returns whatever is in `custom_campaign_state["campaign_tier"]` without validating it's one of the expected constants. If an invalid value is stored (e.g., "invalid_tier"), it could cause issues downstream.

**Impact:** Medium - Could cause silent failures

**Recommendation:** Add validation:
```python
def get_campaign_tier(self) -> str:
    """Get the current campaign tier (mortal, divine, or sovereign)."""
    tier = self.custom_campaign_state.get(
        "campaign_tier", constants.CAMPAIGN_TIER_MORTAL
    )
    valid_tiers = {
        constants.CAMPAIGN_TIER_MORTAL,
        constants.CAMPAIGN_TIER_DIVINE,
        constants.CAMPAIGN_TIER_SOVEREIGN,
    }
    if tier not in valid_tiers:
        logging_util.warning(
            f"Invalid campaign_tier '{tier}', defaulting to mortal"
        )
        return constants.CAMPAIGN_TIER_MORTAL
    return tier
```

## ✅ Good Practices Observed

1. **Defensive Type Coercion:** Good use of try/except for converting string values to int in upgrade detection methods
2. **Logging:** Comprehensive logging throughout for debugging
3. **Documentation:** Well-documented methods with clear docstrings
4. **Test Coverage:** Tests updated to mock new methods
5. **Backward Compatibility:** New fields initialized with defaults in `__init__`

## 🔍 Minor Issues / Suggestions

### 7. **Inconsistent Error Messages**
The error message in `CampaignUpgradeAgent.build_system_instructions()` says "falling back to core instructions only" but doesn't explain why this happened or what the user should do.

### 8. **Performance: Repeated get_pending_upgrade_type() Calls**
In `get_agent_for_input()`, `CampaignUpgradeAgent.matches_game_state()` is called multiple times (lines 1571, 1638, 1647). Consider caching the result if performance becomes an issue.

### 9. **Magic Strings**
The upgrade types "divine" and "multiverse" are hardcoded strings. Consider using constants:
```python
UPGRADE_TYPE_DIVINE = "divine"
UPGRADE_TYPE_MULTIVERSE = "multiverse"
```

## 📋 Testing Recommendations

1. **Test missing prompt files:** Verify graceful degradation when prompt files don't exist
2. **Test race conditions:** Verify behavior when upgrade availability changes between agent init and instruction build
3. **Test invalid campaign_tier values:** Verify handling of corrupted state data
4. **Test XP overflow:** Verify behavior at very high levels (200+)

## Overall Assessment

**Status:** ⚠️ **Needs Fixes Before Merge**

The PR is well-structured and adds valuable functionality, but the critical issues (#1, #2) should be addressed before merging. The medium-priority issues (#4, #6) are also important for robustness.

**Recommendation:** Fix critical issues, then merge. Medium-priority issues can be addressed in follow-up PRs if needed.
