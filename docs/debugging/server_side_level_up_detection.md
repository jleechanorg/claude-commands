# Server-Side Level-Up Detection Fix

**Branch:** claude/debug-rewards-agent-dX7Ku
**Date:** 2025-12-30
**Issue:** Level-up not triggered when XP awarded outside rewards pipeline

## Root Cause

The RewardsAgent only triggers when specific state conditions exist:
- `combat_phase == "ended"` with `combat_summary`
- `encounter_completed == true` with `encounter_summary`
- Explicit `rewards_pending` flag

When XP is awarded via God Mode or narrative milestones, these conditions are NOT set,
so RewardsAgent never runs and level-up is not offered to the player.

**Evidence from Undertale campaign (`docs/debugging/Undertale (2).txt`):**
- Line 1391: Player had 6,206 XP
- Line 1539: After killing Toriel, XP increased to 8,006 (narratively)
- Line 1542: Player had to manually ask in God Mode: "shouldn't I be level 5 now?"
- Level 5 threshold is 6,500 XP - player was 1,500+ XP over threshold but never offered level-up

## Fix Implemented

Added `_check_and_set_level_up_pending()` function in `world_logic.py:462-539`:

1. **Runs for ALL modes** - not just combat/rewards mode
2. **Compares stored level vs XP-calculated level** using `level_from_xp()`
3. **Sets `rewards_pending`** with `level_up_available=True` when level-up is available
4. **Triggers RewardsAgent** on the next action to offer the level-up

### Code Location

```python
# world_logic.py:462-539
def _check_and_set_level_up_pending(
    state_dict: dict[str, Any], original_state_dict: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Server-side level-up detection: Set rewards_pending when XP crosses level threshold.
    ...
    """
```

### Hook Points

The function is called in three locations:
1. `world_logic.py:685-688` - After rewards processing in `_process_rewards_followup`
2. `world_logic.py:700-703` - In else branch of `_process_rewards_followup`
3. `world_logic.py:1540-1542` - Main processing loop for ALL modes

## Merge Conflict Resolution

### Conflict 1: `_process_rewards_followup` (lines 684-696)

**HEAD (this branch):** Added `_check_and_set_level_up_pending()` call
**origin/main:** Changed `validate_and_correct_state()` to return tuple with `return_corrections=True`

**Resolution:** Keep BOTH changes:
- Keep `_check_and_set_level_up_pending()` call (level-up detection)
- Adopt `return_corrections=True` pattern from main

### Conflict 2: Main processing loop (lines 1541-1556)

**HEAD (this branch):** Added `_check_and_set_level_up_pending()` call with shorter comment
**origin/main:** Different formatting and no level-up detection

**Resolution:** Keep BOTH:
- Keep `_check_and_set_level_up_pending()` call (level-up detection)
- Adopt improved comment from remote: "Check for level-up in ALL modes where original_state_dict is available"
- Adopt multi-line parameter formatting from remote

### Conflict 3: Comment and formatting (lines 1578-1599)

**HEAD:** Single-line comment, single-line parameters
**origin/remote:** Multi-line comment (more descriptive), multi-line parameters

**Resolution:** Adopt remote's improved formatting:
- More descriptive comment explaining why original_state_dict is needed
- Multi-line parameter style for readability

## Test Verification

```python
# Test case: Undertale scenario reproduction
original_state = {
    "player_character_data": {
        "level": 4,
        "experience": {"current": 6206}
    }
}
updated_state = {
    "player_character_data": {
        "level": 4,  # Still stored as 4 (the bug!)
        "experience": {"current": 8006}  # But XP is now 8006
    }
}

result = _check_and_set_level_up_pending(updated_state, original_state)
# Result: rewards_pending set with level_up_available=True, new_level=5
```

## Decision Rationale

All logic from both branches was kept because:
1. Level-up detection (this branch) fixes a real user-facing bug
2. `return_corrections` pattern (main) provides system warnings visibility
3. Both features are orthogonal and work together correctly
4. Improved comments from remote make the code more maintainable
