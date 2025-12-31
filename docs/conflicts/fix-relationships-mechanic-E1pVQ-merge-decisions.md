# Merge Conflict Resolution: fix-relationships-mechanic-E1pVQ

**Date:** 2025-12-29
**Branch:** `claude/fix-relationships-mechanic-E1pVQ`
**PR:** #2578

## Complete Conflict Resolution Summary

### 1. `.beads/*` files (5 files)
**Decision:** TAKE MAIN
**Rationale:** Tracking files, more recent state from main preferred

### 2. `.claude/skills/evidence-standards.md`
**Decision:** TAKE MAIN
**Rationale:** Infrastructure documentation, no feature-specific content

### 3. `mvp_site/agent_prompts.py`
**Conflict:** PATH_MAP - RELATIONSHIP/REPUTATION vs LIVING_WORLD
**Decision:** KEEP ALL THREE
```python
PROMPT_TYPE_RELATIONSHIP: constants.RELATIONSHIP_INSTRUCTION_PATH,
PROMPT_TYPE_REPUTATION: constants.REPUTATION_INSTRUCTION_PATH,
PROMPT_TYPE_LIVING_WORLD: constants.LIVING_WORLD_INSTRUCTION_PATH,
```
**Rationale:** All are separate prompt types with no overlap

### 4. `mvp_site/constants.py`
**Conflict:** Prompt type constants and paths
**Decision:** KEEP ALL
- PROMPT_TYPE_RELATIONSHIP, PROMPT_TYPE_REPUTATION (ours)
- PROMPT_TYPE_LIVING_WORLD, LIVING_WORLD_TURN_INTERVAL (main)
**Rationale:** Complementary constants for different features

### 5. `mvp_site/game_state.py`
**Conflict:** New methods from main
**Decision:** KEEP MAIN's additions
- `get_encounter_state()` - non-combat encounters
- `get_rewards_pending()` - pending rewards tracking
- `has_pending_rewards()` - rewards state check
**Rationale:** New functionality for non-combat XP system

### 6. `mvp_site/llm_service.py`
**Conflicts:**
- Debug info capture
- Turn number calculation

**Decision:**
- Debug info: COMBINED BOTH approaches
  ```python
  debug_info["system_instruction_files"] = get_loaded_instruction_files()  # lightweight
  debug_info["system_instruction_char_count"] = len(system_instruction_final)
  debug_info["system_instruction_text"] = system_instruction_final[:max_chars]  # detailed
  ```
- Turn number: TAKE MAIN (`(len(truncated_story_context) // 2) + 1`)

**Rationale:** Both debug approaches valuable; main's turn calculation aligns with player turn pairs

### 7. `mvp_site/prompts/game_state_instruction.md`
**Conflicts:**
- ESSENTIALS section
- Non-combat encounter schema
- State update rules

**Decision:** KEEP ALL
- Added: Non-combat encounter schema (heists, social, stealth)
- Kept: Relationship updates mandate
- Kept: Arc milestones section

**Rationale:** All sections govern different game mechanics

### 8. `mvp_site/prompts/narrative_system_instruction.md`
**Conflict:** ESSENTIALS comment block removed in main
**Decision:** KEEP EXPANDED ESSENTIALS
```markdown
<!-- ESSENTIALS (token-constrained mode)
- 🔗 RELATIONSHIPS: CHECK trust_level BEFORE NPC interactions...
- 📢 REPUTATION: Public + Private per-faction tracking...
- 🏆 REWARDS: encounter_state requirements...
- ⚠️ MANDATORY XP ON NARRATIVE KILLS...
/ESSENTIALS -->
```
**Rationale:** Core feature of PR #2578, enriched with main's XP requirements

### 9. Test files (7 files)
**Decision:** TAKE MAIN
**Rationale:** Infrastructure/formatting changes, no feature-specific tests affected

## Features Combined After Merge

| Feature | Source | Status |
|---------|--------|--------|
| Relationship mechanics | PR #2578 | ✅ Preserved |
| Reputation system | PR #2578 | ✅ Preserved |
| Living World system | main | ✅ Added |
| Non-combat encounters | main | ✅ Added |
| Encounter XP rewards | main | ✅ Added |
| Arc milestones | main | ✅ Added |
| Combined debug info | both | ✅ Combined |

## Verification

- All features coexist without conflict
- No overlapping state fields
- Complementary game mechanics
- Debug info captures both lightweight and detailed evidence
