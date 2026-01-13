# LLM Schema Alignment Gaps Analysis

**Date:** 2026-01-11
**Purpose:** Document gaps between state management instructions given to the LLM and the explicit JSON input/output schemas defined in `narrative_response_schema.py` and related instruction files.

## Executive Summary

This analysis identifies 15+ areas where the system instructions tell the LLM to manage state, but the corresponding JSON schemas are either:
1. **Not explicitly defined** in Python validation code
2. **Partially defined** without complete field specifications
3. **Documented in instructions** but not linked to input source fields

Per CLAUDE.md principle: "Document BOTH Input and Output Schemas" - when adding LLM-driven features, we must document what data the LLM receives AND what data the LLM must return, linking them explicitly.

---

## Gap Categories

### Category A: State Objects Described in Instructions but No Python Schema Validation

### Category B: Output Fields Without Explicit Input Source Documentation

### Category C: Validation Gaps (Partial Schema Coverage)

---

## Detailed Gap Analysis

### 1. Relationship Object Schema (Category A - Critical)

**Instructions Reference:** `relationship_instruction.md`, `game_state_instruction.md`

**What LLM is told to do:**
- Track `relationships.player.trust_level` (-10 to +10)
- Track `relationships.player.disposition` (hostile/antagonistic/cold/neutral/friendly/trusted/devoted/bonded)
- Track `relationships.player.history` (array of strings)
- Track `relationships.player.debts` (array of strings)
- Track `relationships.player.grievances` (array of strings)
- Update these in `state_updates.npc_data.<name>.relationships`

**What's in Python schema:**
- `NarrativeResponse._validate_state_updates()` does NOT validate relationship structure
- Only basic dict type checking; no field-level validation
- No validation for trust_level range (-10 to +10)
- No validation for disposition enum values

**Gap:** No explicit JSON schema for relationship objects

---

### 2. Reputation Object Schema (Category A - Critical)

**Instructions Reference:** `reputation_instruction.md`, `game_state_instruction.md`

**What LLM is told to do:**
- Track `custom_campaign_state.reputation.public` with:
  - `score` (-100 to +100)
  - `titles` (array)
  - `known_deeds` (array)
  - `rumors` (array)
  - `notoriety_level` (infamous/notorious/disreputable/unknown/known/respected/famous/legendary)
- Track `custom_campaign_state.reputation.private.<faction_id>` with:
  - `score` (-10 to +10)
  - `standing` (enemy/hostile/unfriendly/neutral/friendly/trusted/ally/champion)
  - `known_deeds` (array)
  - `secret_knowledge` (array)
  - `trust_override` (nullable int)

**What's in Python schema:**
- No validation for reputation structure in `narrative_response_schema.py`
- Not referenced in any Python validation code

**Gap:** Complete absence of reputation schema validation

---

### 3. Frozen Plans Schema (Category A - Medium)

**Instructions Reference:** `think_mode_instruction.md`, `planning_protocol.md`, `game_state_instruction.md`

**What LLM is told to do:**
- On failed planning check, add to `state_updates.frozen_plans`:
  ```json
  {
    "<plan_topic_key>": {
      "failed_at": "<current_world_time>",
      "freeze_until": "<world_time + freeze_duration>",
      "original_dc": 14,
      "freeze_hours": 4,
      "description": "planning the warehouse ambush"
    }
  }
  ```

**What's in Python schema:**
- Comment in `_validate_state_updates()` says "frozen_plans is LLM-enforced via prompts"
- No Python validation at all

**Gap:** frozen_plans structure not documented as formal schema

---

### 4. Combat State Schema (Category A - High)

**Instructions Reference:** `game_state_instruction.md`, `combat_system_instruction.md`

**What LLM is told to do:**
- Track `combat_state.in_combat` (boolean)
- Track `combat_state.combat_session_id` (string, format: `combat_<timestamp>_<4char>`)
- Track `combat_state.combat_phase` (initiating/active/ended/fled)
- Track `combat_state.current_round` (integer)
- Track `combat_state.initiative_order` (array of {name, initiative, type})
- Track `combat_state.combatants` (dict of {hp_current, hp_max, ac, type, cr, category, etc.})
- Track `combat_state.combat_summary` (rounds_fought, enemies_defeated, xp_awarded, loot_distributed)
- Track `combat_state.rewards_processed` (boolean)

**What's in Python schema:**
- No explicit combat_state schema in `narrative_response_schema.py`
- Not validated beyond basic dict checks

**Gap:** Complex combat_state not validated despite being critical for game mechanics

---

### 5. Encounter State Schema (Category C - Medium)

**Instructions Reference:** `game_state_instruction.md`, `narrative_system_instruction.md`

**What LLM is told to do:**
- Track `encounter_state.encounter_active` (boolean)
- Track `encounter_state.encounter_id` (string, format: `enc_<timestamp>_<type>_###`)
- Track `encounter_state.encounter_type` (heist/social/stealth/puzzle/quest/narrative_victory)
- Track `encounter_state.difficulty` (easy/medium/hard/deadly)
- Track `encounter_state.encounter_completed` (boolean)
- Track `encounter_state.encounter_summary` with xp_awarded, outcome, method
- Track `encounter_state.rewards_processed` (boolean)

**What's in Python schema:**
- No explicit encounter_state schema
- encounter_type enum not validated

**Gap:** encounter_type valid values not validated

---

### 6. Arc Milestones Schema (Category A - Low)

**Instructions Reference:** `game_state_instruction.md`

**What LLM is told to do:**
- Track `custom_campaign_state.arc_milestones.<arc_key>`:
  - `status` (in_progress/completed)
  - `phase` (string)
  - `progress` (0-100)
  - `updated_at` or `completed_at` (ISO timestamp)

**What's in Python schema:**
- Not referenced or validated

**Gap:** Arc milestone tracking not formally specified

---

### 7. World Time Schema (Category A - High)

**Instructions Reference:** `game_state_instruction.md`

**What LLM is told to do:**
- Output `world_data.world_time` with ALL fields:
  - `year` (integer)
  - `month` (string/integer)
  - `day` (integer, 1-31)
  - `hour` (integer, 0-23)
  - `minute` (integer, 0-59)
  - `second` (integer, 0-59)
  - `microsecond` (integer, 0-999999)
  - `time_of_day` (Dawn/Morning/Midday/Afternoon/Evening/Night/Deep Night)

**What's in Python schema:**
- Not validated in `narrative_response_schema.py`
- Only mentioned in instructions

**Gap:** Critical temporal data structure not validated

---

### 8. Social HP Challenge Input→Output Mapping (Category B - Critical)

**Instructions Reference:** `game_state_instruction.md`, `narrative_system_instruction.md`

**What LLM RECEIVES (Input):**
- `npc_data.<name>.tier` - NPC tier (commoner/merchant/guard/noble/knight/lord/general/king/ancient/god/primordial)
- `npc_data.<name>.role` - NPC role
- `npc_data.<name>.relationships.player.trust_level`

**What LLM OUTPUTS:**
- `social_hp_challenge.npc_tier` - MUST be extracted from input `npc_data.<name>.tier`
- `social_hp_challenge.social_hp_max` - Calculated from npc_tier

**Current Documentation Gap:**
- `SOCIAL_HP_CHALLENGE_SCHEMA` in `narrative_response_schema.py` defines OUTPUT fields
- But INPUT source (`npc_data.tier`) is only mentioned in game_state_instruction.md
- No explicit link: "OUTPUT.npc_tier = extract from INPUT.npc_data.tier"

**Gap:** Input-to-output field mapping not explicitly documented in schema

---

### 9. Session Header Format (Category A - Medium)

**Instructions Reference:** `game_state_instruction.md`

**What LLM is told to do:**
```
[SESSION_HEADER]
Timestamp: [Year] [Era], [Month] [Day], [Time]
Location: [Current Location Name]
Status: Lvl [X] [Class] | HP: [current]/[max] (Temp: [temp]) | XP: [current]/[needed] | Gold: [X]gp
Conditions: [Active conditions] | Exhaustion: [0-6] | Inspiration: [Yes/No]
```

**What's in Python schema:**
- `session_header` is just validated as a string
- No format validation

**Gap:** Session header format not formally specified as parseable structure

---

### 10. Debug Info Meta Schema (Category A - Low)

**Instructions Reference:** `game_state_instruction.md`

**What LLM is told to do:**
- Output `debug_info.meta.needs_detailed_instructions` array
- Valid values: `["relationships", "reputation"]` (more to come)

**What's in Python schema:**
- `debug_info` validated as dict only
- No validation for `meta.needs_detailed_instructions` structure or valid values

**Gap:** Meta instruction request mechanism not validated

---

### 11. Time Pressure System Schema (Category A - Low)

**Instructions Reference:** `game_state_instruction.md`

**What LLM is told to do:**
- Track `time_sensitive_events` (dict by event_id)
- Track `time_pressure_warnings` (subtle_given, clear_given, urgent_given, last_warning_day)
- Track `npc_agendas` (dict by npc_id)
- Track `world_resources` (dict by resource_id)

**What's in Python schema:**
- None of these are referenced or validated

**Gap:** Time pressure system not formally specified

---

### 12. Directives Schema (Category C - Medium)

**Instructions Reference:** `god_mode_instruction.md`

**What LLM is told to do:**
- Output `directives.add` (array of strings)
- Output `directives.drop` (array of strings)

**What's in Python schema:**
- `NarrativeResponse` has `directives` attribute initialized to `{}`
- No explicit validation for add/drop structure

**Gap:** Directives add/drop arrays not validated

---

### 13. Equipment Slot Enum (Category C - Medium)

**Instructions Reference:** `game_state_instruction.md`

**What LLM is told to do:**
- Valid slots: `head`, `body`, `armor`, `cloak`, `hands`, `feet`, `neck`, `ring_1`, `ring_2`, `belt`, `shield`, `main_hand`, `off_hand`, `instrument`, `weapons` (array), `backpack` (array)
- Forbidden mappings: `weapon_main`→`main_hand`, `boots`→`feet`, etc.

**What's in Python schema:**
- No equipment slot validation
- No forbidden slot name checking

**Gap:** Equipment slot enum not enforced

---

### 14. Dice Audit Events Enhanced Fields (Category C - Low)

**Instructions Reference:** `game_state_instruction.md`

**What LLM is told to do (for skill checks and saving throws):**
- Include `dc` (integer)
- Include `dc_reasoning` (string) - proves DC was set BEFORE roll
- Include `success` (boolean)

**What's in Python schema:**
- `_validate_dice_audit_events()` is permissive ("Keep permissive")
- No validation for dc, dc_reasoning, success fields

**Gap:** Audit trail fields not formally required

---

### 15. Planning Block Input-Aware Fields (Category B - Medium)

**Instructions Reference:** `think_mode_instruction.md`, `planning_protocol.md`

**What LLM RECEIVES (Input for Think Mode):**
- Character's `attributes.intelligence` and `attributes.wisdom`
- Current `world_time.microsecond`
- Existing `frozen_plans` state

**What LLM OUTPUTS:**
- `planning_block.plan_quality.stat_value` - from input attributes
- `planning_block.plan_quality.modifier` - calculated from stat_value
- `state_updates.world_data.world_time.microsecond` - current + 1

**Gap:** Input fields that inform plan_quality not explicitly documented

---

## Recommendations

### Milestone 1: Core Schema Foundations (~1 week)

**Goal:** Establish critical schemas that affect core gameplay mechanics.

#### Step 1: Document Social HP Input→Output Mapping (0.5 days)
⬜ Map `npc_tier` extraction from `npc_data.tier` in schema documentation
⬜ Add explicit INPUT schema section to `SOCIAL_HP_CHALLENGE_SCHEMA` docstring
⬜ Document `social_hp_max` calculation formula based on tier
⬜ Add validation comment linking input source to output field
⬜ Update `game_state_instruction.md` with explicit field mapping
⬜ Add test case verifying tier extraction from npc_data
⬜ Document tier enum values in schema comments
⬜ Verify existing LLM instructions reference correct input path

#### Step 2: Add Combat State Schema (1 day)
⬜ Define `COMBAT_STATE_SCHEMA` dict with all required fields
⬜ Add `combat_phase` enum validation (initiating/active/ended/fled)
⬜ Validate `combat_session_id` format (combat_<timestamp>_<4char>)
⬜ Add `initiative_order` array structure validation
⬜ Add `combatants` dict structure validation (hp_current, hp_max, ac, type, cr)
⬜ Validate `combat_summary` structure (rounds_fought, enemies_defeated, xp_awarded)
⬜ Add `_validate_combat_state()` method to `NarrativeResponse`
⬜ Integrate validation into `_validate_state_updates()` chain
⬜ Write failing tests for combat_state validation (RED phase)
⬜ Implement minimal validation to pass tests (GREEN phase)
⬜ Add error messages for invalid combat_state fields
⬜ Document combat_state schema in instruction files

#### Step 3: Add Reputation Schema (1 day)
⬜ Define `REPUTATION_PUBLIC_SCHEMA` with score range (-100 to +100)
⬜ Define `REPUTATION_PRIVATE_SCHEMA` with score range (-10 to +10)
⬜ Add `notoriety_level` enum validation (infamous/notorious/disreputable/unknown/known/respected/famous/legendary)
⬜ Add `standing` enum validation (enemy/hostile/unfriendly/neutral/friendly/trusted/ally/champion)
⬜ Validate `titles`, `known_deeds`, `rumors` array structures
⬜ Validate `secret_knowledge` and `trust_override` fields
⬜ Add `_validate_reputation()` method to `NarrativeResponse`
⬜ Integrate reputation validation into state_updates chain
⬜ Write failing tests for public reputation validation
⬜ Write failing tests for private reputation validation
⬜ Implement validation to pass tests
⬜ Document reputation schema in `reputation_instruction.md`

#### Step 4: Integration and Testing (0.5 days)
⬜ Run full test suite to verify no regressions
⬜ Test end-to-end campaign flow with new validations
⬜ Update validation mode config (strict vs warn) for Priority 1 schemas
⬜ Document validation errors in user-facing logs
⬜ Verify LLM can still generate valid responses with new schemas

---

### Milestone 2: State Integrity Schemas (~1 week)

**Goal:** Add validation for schemas that maintain game state consistency.

#### Step 5: Add Relationship Schema (1 day)
⬜ Define `RELATIONSHIP_SCHEMA` with trust_level range (-10 to +10)
⬜ Add `disposition` enum validation (hostile/antagonistic/cold/neutral/friendly/trusted/devoted/bonded)
⬜ Validate `history` array structure (array of strings)
⬜ Validate `debts` and `grievances` array structures
⬜ Add `_validate_relationship()` method to `NarrativeResponse`
⬜ Integrate relationship validation into npc_data.relationships chain
⬜ Write failing tests for trust_level range validation
⬜ Write failing tests for disposition enum validation
⬜ Write failing tests for relationship array structures
⬜ Implement validation to pass tests
⬜ Document relationship schema in `relationship_instruction.md`
⬜ Add validation error messages for out-of-range trust_level

#### Step 6: Add World Time Schema (1 day)
⬜ Define `WORLD_TIME_SCHEMA` with all 8 required fields
⬜ Validate `year` (integer)
⬜ Validate `month` (string/integer)
⬜ Validate `day` (integer, 1-31)
⬜ Validate `hour` (integer, 0-23)
⬜ Validate `minute` (integer, 0-59)
⬜ Validate `second` (integer, 0-59)
⬜ Validate `microsecond` (integer, 0-999999)
⬜ Add `time_of_day` enum validation (Dawn/Morning/Midday/Afternoon/Evening/Night/Deep Night)
⬜ Add `_validate_world_time()` method to `NarrativeResponse`
⬜ Integrate world_time validation into world_data chain
⬜ Write failing tests for each field validation
⬜ Implement validation to pass tests
⬜ Document world_time schema in `game_state_instruction.md`

#### Step 7: Add Encounter State Schema (0.5 days)
⬜ Define `ENCOUNTER_STATE_SCHEMA` with encounter_type enum
⬜ Add `encounter_type` enum validation (heist/social/stealth/puzzle/quest/narrative_victory)
⬜ Validate `encounter_id` format (enc_<timestamp>_<type>_###)
⬜ Add `difficulty` enum validation (easy/medium/hard/deadly)
⬜ Validate `encounter_summary` structure (xp_awarded, outcome, method)
⬜ Add `_validate_encounter_state()` method to `NarrativeResponse`
⬜ Integrate encounter_state validation into state_updates chain
⬜ Write failing tests for encounter_type enum validation
⬜ Implement validation to pass tests
⬜ Document encounter_state schema in instruction files

#### Step 8: Integration and Testing (0.5 days)
⬜ Run full test suite to verify no regressions
⬜ Test state persistence with new validations
⬜ Update validation mode config for Priority 2 schemas
⬜ Verify backward compatibility with existing campaign data
⬜ Document any migration requirements for existing state

---

### Priority 3 (Medium - Affects Feature Completeness)
7. **Frozen Plans Schema** - Document structure even if LLM-enforced
8. **Directives Schema** - Add add/drop array validation
9. **Equipment Slot Enum** - Add valid slot validation
10. **Session Header Format** - Document parseable format

### Priority 4 (Low - Nice to Have)
11. Arc Milestones Schema
12. Time Pressure System Schema
13. Debug Info Meta Schema
14. Dice Audit Events Enhanced Fields

---

## Implementation Approach

Per CLAUDE.md:
> "Document BOTH Input and Output Schemas... Show how to extract input data for output fields"

Each gap should be addressed by:
1. **Input Schema Section** - What data does the LLM receive?
2. **Output Schema Section** - What data must the LLM return?
3. **Field Mapping** - Explicit links: "OUTPUT.field_x = extract from INPUT.field_y"
4. **Validation Code** - Python validation in `narrative_response_schema.py` (where applicable)

---

## TDD Implementation Protocol

Follow Red-Green-Refactor for each schema gap:

### Phase 1: RED - Write Failing Tests First

For each gap, create tests in `mvp_site/tests/test_narrative_response_schema.py` that:

```python
# Example: Testing Combat State Schema (Gap #4)
class TestCombatStateSchema(unittest.TestCase):
    """RED: Tests written BEFORE implementation."""

    def test_valid_combat_state_passes_validation(self):
        """Valid combat_state with all required fields should pass."""
        combat_state = {
            "in_combat": True,
            "combat_session_id": "combat_1704931200_a1b2",
            "combat_phase": "active",
            "current_round": 2,
            "initiative_order": [
                {"name": "Player", "initiative": 18, "type": "player"},
                {"name": "Goblin", "initiative": 12, "type": "enemy"}
            ],
            "combatants": {}
        }
        # This FAILS initially (no validation exists)
        result = validate_combat_state(combat_state)
        self.assertTrue(result.is_valid)

    def test_invalid_combat_phase_fails_validation(self):
        """Invalid combat_phase enum value should fail."""
        combat_state = {"combat_phase": "invalid_phase"}
        result = validate_combat_state(combat_state)
        self.assertFalse(result.is_valid)
        self.assertIn("combat_phase", result.errors)

    def test_trust_level_out_of_range_fails(self):
        """trust_level outside -10 to +10 should fail."""
        relationship = {"trust_level": 15}  # Invalid: > 10
        result = validate_relationship(relationship)
        self.assertFalse(result.is_valid)
```

### Phase 2: GREEN - Minimal Implementation

Add validation to `narrative_response_schema.py`:

```python
# Example: Minimal combat_state validation
COMBAT_PHASE_ENUM = ["initiating", "active", "ended", "fled"]

def validate_combat_state(combat_state: dict) -> ValidationResult:
    """Validate combat_state structure."""
    errors = []

    # Required fields
    if "in_combat" in combat_state:
        if not isinstance(combat_state["in_combat"], bool):
            errors.append("in_combat must be boolean")

    # Enum validation
    if "combat_phase" in combat_state:
        if combat_state["combat_phase"] not in COMBAT_PHASE_ENUM:
            errors.append(f"combat_phase must be one of {COMBAT_PHASE_ENUM}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

### Phase 3: REFACTOR - Integrate with NarrativeResponse

1. Add validation call in `NarrativeResponse._validate_state_updates()`
2. Decide on validation mode: `strict` (raise) vs `warn` (log only)
3. Add to existing validation chain

### TDD Execution Order

| Bead ID | Gap | Test File | Implementation File |
|---------|-----|-----------|---------------------|
| worktree_worker2-5jj | Combat State | `test_narrative_response_schema.py` | `narrative_response_schema.py` |
| worktree_worker2-oy4 | Reputation | `test_narrative_response_schema.py` | `narrative_response_schema.py` |
| worktree_worker2-g10 | Relationship | `test_narrative_response_schema.py` | `narrative_response_schema.py` |
| worktree_worker2-4j3 | Social HP Mapping | `test_game_state_instruction.py` | `game_state_instruction.md` |
| worktree_worker2-kg6 | World Time | `test_narrative_response_schema.py` | `narrative_response_schema.py` |
| worktree_worker2-ipj | Encounter State | `test_narrative_response_schema.py` | `narrative_response_schema.py` |

### All Beads Summary

**Epic:** `worktree_worker2-1gp` - LLM Schema Alignment (parent of all tasks below)

**Priority 1 (Critical):**
- `worktree_worker2-4j3` - Social HP Input→Output Mapping
- `worktree_worker2-5jj` - Combat State Schema
- `worktree_worker2-oy4` - Reputation Schema

**Priority 2 (High):**
- `worktree_worker2-g10` - Relationship Schema
- `worktree_worker2-kg6` - World Time Schema
- `worktree_worker2-ipj` - Encounter State Schema

**Priority 3 (Medium):**
- `worktree_worker2-uyf` - Frozen Plans Schema
- `worktree_worker2-tuq` - Directives Schema
- `worktree_worker2-6je` - Equipment Slot Enum

**Priority 4 (Low):**
- `worktree_worker2-otq` - Arc Milestones Schema
- `worktree_worker2-zk3` - Time Pressure System Schema

### Test Categories

1. **Schema Structure Tests** - Validate field presence and types
2. **Enum Validation Tests** - Validate allowed values
3. **Range Validation Tests** - Validate numeric ranges (trust_level, scores)
4. **Integration Tests** - End-to-end LLM response validation
5. **Regression Tests** - Ensure existing campaigns don't break

### Validation Strategy Decision

**Option A: Strict Mode (Recommended for Critical Gaps)**
- Raise `SchemaValidationError` on invalid data
- Prevents bad state from persisting
- Risk: May break existing flows if LLM varies output

**Option B: Warn Mode (Recommended for Medium/Low Gaps)**
- Log warning but allow processing to continue
- Captures issues without breaking gameplay
- Good for monitoring before strict enforcement

```python
# Configuration in narrative_response_schema.py
SCHEMA_VALIDATION_MODE = {
    "combat_state": "strict",      # Priority 1: Must be correct
    "reputation": "strict",        # Priority 1: Must be correct
    "relationship": "strict",      # Priority 2: Should be correct
    "frozen_plans": "warn",        # Priority 3: Nice to have
    "arc_milestones": "warn",      # Priority 4: Low priority
}

---

## Files Analyzed

### Instruction Files (What LLM is told)
- `mvp_site/prompts/game_state_instruction.md` (primary)
- `mvp_site/prompts/planning_protocol.md`
- `mvp_site/prompts/think_mode_instruction.md`
- `mvp_site/prompts/narrative_system_instruction.md`
- `mvp_site/prompts/relationship_instruction.md`
- `mvp_site/prompts/reputation_instruction.md`
- `mvp_site/prompts/god_mode_instruction.md`
- `mvp_site/prompts/rewards_system_instruction.md`

### Schema Files (What Python validates)
- `mvp_site/narrative_response_schema.py` (primary)
  - `PLANNING_BLOCK_SCHEMA`
  - `CHOICE_SCHEMA`
  - `SOCIAL_HP_CHALLENGE_SCHEMA`
  - `NarrativeResponse` class

---

## Appendix: Existing Well-Defined Schemas

These schemas ARE properly defined and validated:

1. **PLANNING_BLOCK_SCHEMA** - Canonical schema with plan_quality, thinking, choices
2. **CHOICE_SCHEMA** - text, description, pros, cons, confidence, risk_level, switch_to_story_mode
3. **SOCIAL_HP_CHALLENGE_SCHEMA** - All output fields defined (but input mapping gap exists)
4. **rewards_box** - source, xp_gained, current_xp, next_level_xp, progress_percent, level_up_available, loot, gold
5. **NarrativeResponse core fields** - narrative, entities_mentioned, location_confirmed, turn_summary, state_updates, debug_info, planning_block, dice_rolls, dice_audit_events, resources, social_hp_challenge, rewards_box
