# Schema Validation Gaps: Resources, Spell Slots, and D&D 5e Structures

**Date:** 2026-01-11  
**Related Bead:** worktree_worker2-68v  
**Related PR:** #3470 (schema validation pattern)

## Executive Summary

Analysis of D&D SRD (`dnd_srd_instruction.md`) and game state documentation (`game_state_instruction.md`) reveals **12+ additional structures** that need Python schema validation beyond what PR #3470 addressed.

## Gap Categories

### Priority 1 (Critical - Core Gameplay)

#### 1. Resources Schema
**Location:** `player_character_data.resources`  
**Current State:** Only validated as string field, not structured object

**Structure:**
```json
{
  "gold": 0,
  "hit_dice": {"used": 0, "total": 0},
  "spell_slots": {},
  "class_features": {},
  "consumables": {}
}
```

**Required Validation:**
- `gold`: int (>= 0)
- `hit_dice`: dict with `used` (int, 0-total) and `total` (int, >= 0)
- `spell_slots`: dict (see SPELL_SLOTS_SCHEMA below)
- `class_features`: dict (see CLASS_FEATURES_SCHEMA below)
- `consumables`: dict/array

#### 2. Spell Slots Schema
**Location:** `player_character_data.resources.spell_slots`  
**Documentation:** `game_state_instruction.md` lines 1086-1177

**Structure:**
```json
{
  "level_1": {"current": 4, "max": 4},
  "level_2": {"current": 2, "max": 3},
  "level_3": {"current": 0, "max": 2}
}
```

**Required Validation:**
- Level keys: `level_1` through `level_9`
- Each level: `{current: int (0-max), max: int (>= 0)}`
- Constraint: `current <= max`, `current >= 0`

#### 3. Class Features Schema
**Location:** `player_character_data.resources.class_features`  
**Documentation:** `game_state_instruction.md` lines 1236-1443

**Class-Specific Resources:**
- `bardic_inspiration`: `{current: int, max: int}` (max = CHA mod, min 1)
- `ki_points`: `{current: int, max: int}` (max = monk level)
- `rage`: `{current: int, max: int}` (max scales with level: 2 at L1, 3 at L3, etc.)
- `channel_divinity`: `{current: int, max: int}` (max = 1-2 based on level)
- `lay_on_hands`: `{current: int, max: int}` (max = paladin level × 5)
- `sorcery_points`: `{current: int, max: int}` (max = sorcerer level)
- `wild_shape`: `{current: int, max: int}` (max = 2)

**Required Validation:**
- All class features: `current <= max`, `current >= 0`
- Max values should match class/level constraints (warn if exceeds expected)

### Priority 2 (High - State Integrity)

#### 4. Attributes Schema
**Location:** `player_character_data.base_attributes` and `player_character_data.attributes`  
**Documentation:** `game_state_instruction.md` lines 717-754

**Critical Relationship:**
```
attributes[stat] = base_attributes[stat] + sum(equipment bonuses)
```

**Required Validation:**
- `base_attributes`: dict with STR/DEX/CON/INT/WIS/CHA (int, 1-30)
- `attributes`: dict with same keys (int, 1-30)
- **Constraint:** `attributes[stat] >= base_attributes[stat]` (equipment can only add)
- **Math verification:** Warn if `attributes != base_attributes + equipment bonuses`

#### 5. Experience Schema
**Location:** `player_character_data.experience`  
**Documentation:** `game_state_instruction.md` line 795

**Structure:**
```json
{
  "current": 0,
  "needed_for_next_level": 300
}
```

**Required Validation:**
- `current`: int (>= 0)
- `needed_for_next_level`: int (>= current)
- Warn if `current > needed_for_next_level` (should trigger level up)

#### 6. Death Saves Schema
**Location:** `player_character_data.death_saves`  
**Documentation:** `game_state_instruction.md` line 803, D&D SRD

**Structure:**
```json
{
  "successes": 0,
  "failures": 0
}
```

**Required Validation:**
- `successes`: int (0-3)
- `failures`: int (0-3)
- **State logic:** If successes == 3: stabilized, if failures == 3: death

#### 7. Spells Known Schema
**Location:** `player_character_data.spells_known`  
**Documentation:** `game_state_instruction.md` lines 896-931

**Structure:**
```json
[
  {"name": "Charm Person", "level": 1},
  {"name": "Hypnotic Pattern", "level": 3, "school": "illusion", "casting_time": "1 action"}
]
```

**Required Validation:**
- Array of dicts
- Required fields: `name` (str), `level` (int, 0-9)
- Optional fields: `school`, `casting_time`, `range`, `components`, `duration`
- Warn if missing `name` or `level`

### Priority 3 (Medium - Data Quality)

#### 8. Status Conditions Schema
**Location:** `player_character_data.status_conditions`  
**Documentation:** `game_state_instruction.md` lines 843-845

**Structure:** Array of strings (Poisoned, Frightened, Prone, etc.)

**Required Validation:**
- Array of strings
- Should reference D&D 5e SRD valid conditions (warn on unknown)

#### 9. Active Effects Schema
**Location:** `player_character_data.active_effects`  
**Documentation:** `game_state_instruction.md` lines 808-841

**Structure:** Array of strings describing persistent buffs/effects

**Required Validation:**
- Array of strings
- Format validation (should describe effect and mechanical benefit)

#### 10. Combat Stats Schema
**Location:** `player_character_data.combat_stats`  
**Documentation:** `game_state_instruction.md` line 802

**Structure:**
```json
{
  "initiative": 0,
  "speed": 30,
  "passive_perception": 10
}
```

**Required Validation:**
- `initiative`: int
- `speed`: int (>= 0)
- `passive_perception`: int (>= 0)

#### 11. Item Schemas (Weapons, Armor, Consumables)
**Location:** `player_character_data.equipment`  
**Documentation:** `game_state_instruction.md` lines 847-894

**Weapon Schema:**
```json
{
  "name": "Longsword +1",
  "type": "weapon",
  "damage": "1d8",
  "damage_type": "slashing",
  "properties": ["versatile (1d10)"],
  "bonus": 1,
  "weight": 3,
  "value_gp": 1015
}
```

**Armor Schema:**
```json
{
  "name": "Chain Mail",
  "type": "armor",
  "armor_class": 16,
  "armor_type": "heavy",
  "stealth_disadvantage": true,
  "strength_requirement": 13,
  "weight": 55,
  "value_gp": 75
}
```

**Required Validation:**
- Weapon: validate `type: "weapon"`, `damage` format, `damage_type` enum
- Armor: validate `type: "armor"`, `armor_class` range (1-30), `armor_type` enum
- General items: validate `type`, `effect`, `charges`, `weight`, `value_gp`

## Implementation Priority

**Phase 1 (Critical):**
1. RESOURCES_SCHEMA (gold, hit_dice, spell_slots, class_features, consumables)
2. SPELL_SLOTS_SCHEMA
3. CLASS_FEATURES_SCHEMA

**Phase 2 (High):**
4. ATTRIBUTES_SCHEMA (base_attributes vs attributes relationship)
5. EXPERIENCE_SCHEMA
6. DEATH_SAVES_SCHEMA
7. SPELLS_KNOWN_SCHEMA

**Phase 3 (Medium):**
8. STATUS_CONDITIONS_SCHEMA
9. ACTIVE_EFFECTS_SCHEMA
10. COMBAT_STATS_SCHEMA
11. ITEM_SCHEMAS (weapons, armor, consumables)

## Implementation Pattern (from PR #3470)

1. **Define Schema Constants:**
   ```python
   RESOURCES_SCHEMA = {
       "gold": int,  # >= 0
       "hit_dice": dict,  # {used: int, total: int}
       "spell_slots": dict,  # {level_X: {current, max}}
       "class_features": dict,
       "consumables": dict,
   }
   ```

2. **Create Validation Functions:**
   ```python
   def _validate_resources(resources: dict[str, Any]) -> list[str]:
       """Validate resources structure. Returns list of error messages."""
       errors = []
       # Validation logic
       return errors
   ```

3. **Integrate into `_validate_state_updates()`:**
   ```python
   if "player_character_data" in validated:
       player_data = validated["player_character_data"]
       if isinstance(player_data, dict) and "resources" in player_data:
           resources = player_data["resources"]
           if isinstance(resources, dict):
               errors = _validate_resources(resources)
               if errors:
                   for error in errors:
                       logging_util.warning(f"⚠️ RESOURCES_VALIDATION: {error}")
   ```

4. **Add Test Coverage:**
   - Valid data passes
   - Invalid data logs warnings
   - Edge cases (None, wrong types, out of range)

5. **Document INPUT/OUTPUT Schemas:**
   - Add INPUT schema section (what LLM receives from game_state)
   - Add OUTPUT schema section (what LLM must return)
   - Document field mappings explicitly

## Related Work

- **PR #2716 (MERGED):** Added prompt-based validation protocol, no Python validation
- **PR #3470 (OPEN):** Added Python validation for combat_state, reputation, relationships, etc. - pattern to follow
- **PR #2385 (MERGED):** Centralized schema documentation, no new validation

## Next Steps

1. Create bead issue (✅ DONE: worktree_worker2-68v)
2. Implement Priority 1 schemas (resources, spell_slots, class_features)
3. Add comprehensive test coverage
4. Document INPUT/OUTPUT schemas in `game_state_instruction.md`
5. Integrate into `_validate_state_updates()` method
6. Repeat for Priority 2 and Priority 3 schemas
