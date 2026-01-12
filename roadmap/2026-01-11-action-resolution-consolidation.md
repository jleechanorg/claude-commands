# Action Resolution Consolidation Plan

**Created:** 2026-01-11
**Bead:** `worktree_worker3-caz`
**Epic:** `worktree_worker3-l1s` (Unified Action Resolution System)
**Status:** ✅ COMPLETED (100%)

## Executive Summary

Consolidate Phases 2-4 of the Unified Action Resolution System into a **single PR** using a "Parallel Support" approach. This enables:
- Zero breaking changes
- Gradual LLM adoption
- Easy rollback if needed
- Measurable success before cleanup

## Background

Phase 1 (PR #3383) introduced `outcome_resolution` for reinterpretation scenarios. This plan consolidates the remaining phases:

| Original Phase | Scope | New Approach |
|----------------|-------|--------------|
| Phase 2 | Rename + expand | Combined PR |
| Phase 3 | Deprecate legacy | Combined PR |
| Phase 4 | Remove legacy | Future cleanup PR |

## Strategy: Parallel Support

### Core Principle
Keep legacy fields working while adding new `action_resolution` as the preferred alternative.

```
OLD (still works):           NEW (preferred):
{                            {
  "dice_rolls": [...],    →    "action_resolution": {
  "dice_audit_events": [...]     "mechanics": {
}                                   "rolls": [...],
                                    "audit_events": [...]
                                 }
                               }
                             }
```

### Why This Works
1. **Zero risk:** Legacy fields keep working
2. **Gradual adoption:** LLM can use either format
3. **Easy rollback:** Just ignore new field
4. **Measurable:** Track adoption before removing legacy

## Implementation Plan

### File Changes

| File | Changes | Lines |
|------|---------|-------|
| `narrative_response_schema.py` | Rename validation, add backward compat, add normalization | ~150 |
| `game_state_instruction.md` | Update schema, add DEPRECATED labels | ~50 |
| `master_directive.md` | Rename OUTCOME → ACTION RESOLUTION PROTOCOL | ~20 |
| `llm_response.py` | Add action_resolution property | ~30 |
| `test_action_resolution.py` | New tests for validation and backward compat | ~150 |
| **Total** | | **~400** |

### Key Code Changes

#### 1. Accept Both Field Names
```python
def __init__(self, ...,
             action_resolution=None,      # NEW: Primary name
             outcome_resolution=None,      # DEPRECATED: Backward compat
             ...):
    # Use 'is not None' to preserve empty dict {} precedence
    resolution = action_resolution if action_resolution is not None else outcome_resolution
    self.action_resolution = self._validate_action_resolution(resolution)
```

#### 2. Add Normalization Helper
```python
def get_unified_action_resolution(self):
    """Get action resolution, normalizing from legacy if needed."""
    if self.action_resolution:
        return self.action_resolution
    return self._normalize_legacy_to_action_resolution()

def _normalize_legacy_to_action_resolution(self):
    """Convert dice_rolls + dice_audit_events to action_resolution format."""
    if not self.dice_rolls:
        return {}
    return {
        "player_input": None,
        "interpreted_as": "action",
        "reinterpreted": False,
        "mechanics": {
            "rolls": [{"display": r} for r in self.dice_rolls],
            "audit_events": self.dice_audit_events or []
        },
        "audit_flags": ["normalized_from_legacy"]
    }
```

#### 3. Updated Schema
```json
{
  "action_resolution": {
    "player_input": "I attack the goblin",
    "interpreted_as": "melee_attack",
    "reinterpreted": false,
    "audit_flags": [],
    "mechanics": {
      "type": "attack_roll",
      "rolls": [
        {"purpose": "attack", "notation": "1d20+5", "result": 17, "dc": 13, "success": true}
      ]
    },
    "narrative_outcome": "Your blade finds its mark"
  }
}
```

## Rollout Plan

### Week 1: Deploy Combined PR
- Ship all changes together
- Both formats accepted
- Deprecation warnings logged (server-side only)

### Week 2-3: Monitor
- Track % of responses using action_resolution vs legacy
- Watch error rates
- Target: >80% action_resolution adoption

### Week 4: Cleanup PR
If adoption >80%:
- Remove legacy field support
- Update prompts (remove deprecated examples)
- Final schema cleanup

If adoption <80%:
- Investigate causes
- Extend timeline
- Consider prompt improvements

## Success Criteria

| Metric | Target |
|--------|--------|
| Zero errors from field rename | Required |
| All existing tests pass | Required |
| New tests pass | Required |
| action_resolution adoption | >80% in 2 weeks |
| Gameplay regression | None |

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| LLM ignores new field | Legacy fields still work |
| Frontend breaks | No frontend changes required |
| Performance regression | Normalization is O(1) |
| Token overhead | Optional for normal actions |
| Prompt confusion | Clear DEPRECATED labels |

## Dependencies

- **Depends on:** `worktree_worker3-38z` (Phase 1 - CLOSED)
- **Part of:** `worktree_worker3-l1s` (Epic - Unified Action Resolution)

## Future Work

After this PR stabilizes:
1. **Cleanup PR:** Remove legacy field support
2. **Analytics:** Add action resolution dashboards
3. **Frontend:** Optional UI for action resolution display
