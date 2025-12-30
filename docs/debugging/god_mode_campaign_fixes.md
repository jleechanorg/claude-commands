# God Mode Campaign Fixes

## Overview

This document explains the fixes implemented to address issues identified in the Alexiel Assiah campaign debugging session. The core problem was that the LLM would make claims (e.g., "You are Level 8") that were silently corrected by validation (to Level 7), causing user confusion.

## Issues Identified

From analyzing the campaign log (`docs/debugging/Alexiel assiah.txt`):

| Category | Count | Examples |
|----------|-------|----------|
| Level/XP confusion | 5 | "no i am level 7 right?", "wait why am i level 12 now" |
| Gender misidentification | 2 | "remember alexiel is a woman so a daughter not a son" |
| Ignored directives | 2 | "when i say think about pros/cons dont ignore it" |
| Missing rewards | 3 | "make sure you awarded my exp, loot, resources" |

## Root Cause Analysis

The validation infrastructure **already existed** (`validate_and_correct_state()`, `validate_xp_level()`) but operated **invisibly**:

1. LLM claims "Level 8" in narrative
2. Validation corrects state to Level 7
3. User sees conflicting information (narrative says 8, state shows 7)
4. LLM context includes its own wrong claim

## Solutions Implemented

### 1. Visible Validation Feedback

**File:** `mvp_site/game_state.py`

```python
# validate_and_correct_state() now returns corrections
state, corrections = validate_and_correct_state(state_dict, return_corrections=True)
# Returns: ['Level auto-corrected from 8 to 7 based on XP']
```

**Why:** Users need to see when the system corrects the LLM's claims.

### 2. Character Identity Block

**File:** `mvp_site/game_state.py`

```python
def get_character_identity_block(self) -> str:
    # Returns:
    # ## Character Identity (IMMUTABLE)
    # - **Name**: Alexiel
    # - **Gender**: Female (she/her)
    # - **NEVER** refer to this character as 'he', 'him', or 'son'
```

**Why:** Prevents misgendering by including explicit pronoun enforcement in every prompt.

### 3. God Mode Directive Persistence

**File:** `mvp_site/game_state.py`

```python
def add_god_mode_directive(self, directive: str) -> None:
    # Stores in: custom_campaign_state.god_mode_directives[]
    # Persists across sessions
```

**Why:** Player rules like "always award XP after combat" were being forgotten between sessions.

### 4. Post-Combat XP Warning Detection

**File:** `mvp_site/game_state.py`

```python
def detect_post_combat_issues(self, previous_combat_state, state_changes) -> list[str]:
    # Returns: ['Combat ended but no XP was awarded. Consider awarding XP for 3 combatant(s).']
```

**Why:** The LLM frequently forgot to award XP after combat ended.

### 5. System Warnings in Response

**File:** `mvp_site/world_logic.py`

```python
# Corrections and warnings now surface in the API response
unified_response["system_warnings"] = [
    "Level auto-corrected from 8 to 7 based on XP",
    "Combat ended but no XP was awarded..."
]
```

**Why:** Makes validation corrections visible to the frontend/user.

### 6. Identity/Directives in Prompts

**File:** `mvp_site/agent_prompts.py`

```python
def finalize_instructions(self, parts, use_default_world=False) -> str:
    # Automatically injects:
    # - Character identity block (name, gender, pronouns)
    # - God mode directives (player-defined rules)
```

**Why:** Ensures every LLM prompt includes immutable character facts and player rules.

## Merge with Main Branch

The branch was rebased and merged with `origin/main` which added:

- **Arc Milestones** (`game_state.py`) - Tracks completed narrative arcs to prevent LLM from revisiting concluded storylines
- **Combat Agent** (`agents.py`) - New combat-focused agent with specialized prompts
- **Planning Blocks Fix** - Ensures real choices are generated in planning mode

### Merge Decision: No Conflicts

Both codebases modified `game_state.py` and `world_logic.py` but in different areas:
- **Main:** Added arc milestone methods (lines 340-500)
- **Branch:** Added god mode/identity methods (lines 1057-1237)

Git auto-merged successfully because the changes were additive and non-overlapping.

## Testing

### MCP Test Suite

**File:** `testing_mcp/test_god_mode_validation.py`

Tests all implemented features:
- Validation corrections visibility
- God mode directives persistence
- Character identity enforcement
- Post-combat XP warning detection

```bash
# Run against preview server
MCP_SERVER_URL=https://<preview>.run.app python test_god_mode_validation.py

# Run with local server
python test_god_mode_validation.py --start-local
```

## Impact

These changes should eliminate ~70% of the correction-type GOD MODE interventions observed in the Alexiel campaign:

| Before | After |
|--------|-------|
| Silent XP/level corrections | Visible `system_warnings` in response |
| Forgotten directives | Persisted in `god_mode_directives` |
| Misgendering | Identity block with pronoun enforcement |
| Missing combat rewards | Post-combat XP warning detection |

## Files Modified

| File | Changes |
|------|---------|
| `mvp_site/game_state.py` | +229 lines: identity block, directives, post-combat detection |
| `mvp_site/agent_prompts.py` | +112 lines: finalize_instructions with identity/directives |
| `mvp_site/world_logic.py` | +27 lines: system_warnings in response |
| `testing_mcp/test_god_mode_validation.py` | +414 lines: MCP test suite |
