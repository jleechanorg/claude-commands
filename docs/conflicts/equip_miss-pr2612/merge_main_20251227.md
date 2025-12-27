# Merge Conflict Resolution: main → equip_miss

**Date**: 2025-12-27
**PR**: #2612
**Commit**: 85c0f0e54

## Conflicts Resolved

### 1. mvp_site/llm_service.py (Line 3319)
**Conflict**: Combat state access method
- HEAD: `combat_state_raw = getattr(current_game_state, "combat_state", None)`
- main: `is_combat_or_complex = current_game_state.is_in_combat()`

**Resolution**: Keep main's `is_in_combat()` helper - cleaner API, removes manual dict extraction

**Risk**: Low - both achieve same result, main's is DRYer

### 2. combat_system_instruction.md (Lines 91, 120, 522)
**Conflict**: Initiative order schema format
- HEAD: `{"id": "pc_kira_001", "name": "Kira (PC)", "initiative": 18}`
- main: `{"name": "pc_kira_001", "initiative": 18}`

**Resolution**: Keep main's simplified schema - `name` field IS the string_id

**Risk**: Low - documentation only, aligns with string-id entity system

### 3. game_state_instruction.md (Line 611)
**Conflict**: Same initiative_order schema difference

**Resolution**: Keep main's version for consistency

**Risk**: Low - documentation only

### 4. test_arc_completion_real_e2e.py (Lines 188, 267, 294)
**Conflict**: Arc milestone extraction method
- HEAD: `extract_arc_milestones(game_state)` helper
- main: Inline `.get()` chains

**Resolution**: Keep HEAD's helper function - exists in file, cleaner code

**Risk**: Low - both equivalent functionality
