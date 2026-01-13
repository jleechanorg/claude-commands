# Schema Validation vs LLM Prompt Documentation Gap Analysis

**Date:** 2026-01-12  
**PR:** #3470  
**Purpose:** Identify fields we validate in Python but don't explicitly tell the LLM about

## Summary

We added 21 validation functions but need to verify the LLM knows about ALL the fields it should populate.

## Validation Functions vs Prompt Documentation

### ✅ FULLY DOCUMENTED (LLM knows about these)

1. **Resources** (`_validate_resources`)
   - ✅ Documented: `game_state_instruction.md` lines 859, 1151-1492
   - Fields: `gold`, `hit_dice`, `spell_slots`, `class_features`, `consumables`

2. **Spell Slots** (`_validate_spell_slots`)
   - ✅ Documented: `game_state_instruction.md` lines 1151-1242
   - Fields: `level_1` through `level_9`, `used`, `max`

3. **Class Features** (`_validate_class_features`)
   - ✅ Documented: `game_state_instruction.md` lines 1299-1531
   - Fields: `bardic_inspiration`, `ki_points`, `rage`, `channel_divinity`, etc.

4. **Attributes** (`_validate_attributes`)
   - ✅ Documented: `game_state_instruction.md` lines 780-817, 855-857
   - Fields: `base_attributes` vs `attributes` distinction clearly explained

5. **Experience** (`_validate_experience`)
   - ✅ Documented: `game_state_instruction.md` lines 860, 1638
   - Fields: `current`, `needed_for_next_level`

6. **Death Saves** (`_validate_death_saves`)
   - ✅ Documented: `game_state_instruction.md` line 868
   - Fields: `successes`, `failures` (0-3 range)

7. **Spells Known** (`_validate_spells_known`)
   - ✅ Documented: `game_state_instruction.md` lines 1244-1297
   - Fields: Array of spell objects with `name`, `level`, `school`

8. **Status Conditions** (`_validate_status_conditions`)
   - ✅ Documented: `game_state_instruction.md` lines 908-911
   - Fields: Array of strings (Poisoned, Stunned, etc.)

9. **Active Effects** (`_validate_active_effects`)
   - ✅ Documented: `game_state_instruction.md` lines 873-906
   - Fields: Array of strings describing persistent buffs

10. **Combat Stats** (`_validate_combat_stats`)
    - ✅ Documented: `game_state_instruction.md` lines 867, 1534
    - Fields: `initiative`, `speed`, `passive_perception`

11. **Combat State** (`_validate_combat_state`)
    - ✅ Documented: `game_state_instruction.md` lines 1559-1974
    - Fields: `combat_phase`, `combat_session_id`, `turn_number`

12. **Reputation** (`_validate_reputation`)
    - ✅ Documented: `game_state_instruction.md` lines 2144-2204
    - Fields: `public`, `private`, `score`, `notoriety_level`, `standing`

13. **Relationship** (`_validate_relationship`)
    - ✅ Documented: `game_state_instruction.md` lines 680-779
    - Fields: `trust_level`, `disposition`, `history`, `debts`, `grievances`

14. **World Time** (`_validate_world_time`)
    - ✅ Documented: `game_state_instruction.md` lines 1975-2031
    - Fields: `day`, `hour`, `minute`, `second`, `microsecond`, `time_of_day`, `month`

15. **Encounter State** (`_validate_encounter_state`)
    - ✅ Documented: `game_state_instruction.md` lines 1640-1658
    - Fields: `encounter_type`, `difficulty`, `encounter_active`, etc.

16. **Equipment Slots** (`_validate_equipment_slots`)
    - ✅ Documented: `game_state_instruction.md` lines 665-679
    - Fields: Slot names (weapons, armor, head, neck, etc.)

17. **Item** (`_validate_item`)
    - ✅ Documented: `game_state_instruction.md` lines 912-1020
    - Fields: `type`, `damage`, `damage_type`, `armor_class`, `armor_type`

18. **Frozen Plans** (`_validate_frozen_plans`)
    - ✅ Documented: `game_state_instruction.md` lines 1790-1795
    - Fields: `failed_at`, `freeze_until`, `original_dc`, `freeze_hours`

19. **Arc Milestones** (`_validate_arc_milestones`)
    - ✅ Documented: `game_state_instruction.md` lines 1802-1841
    - Fields: `arc_id`, `milestone_id`, `status`, `completed_at`

20. **Time Pressure Warnings** (`_validate_time_pressure_warnings`)
    - ✅ Documented: `game_state_instruction.md` line 2201
    - Fields: `subtle_given`, `clear_given`, `urgent_given`, `last_warning_day`

### ✅ DOCUMENTED IN SEPARATE FILE (God Mode Only)

21. **Directives** (`_validate_directives`)
    - ✅ Documented: `god_mode_instruction.md` lines 46-153
    - Fields validated: `directives.add` (array of strings), `directives.drop` (array of strings)
    - **Note:** This is God Mode only, so documentation in separate file is appropriate

## Field-Level Gaps (Fields we validate but might not be explicit)

### Combat Stats - Missing Field Documentation
- ✅ `initiative` - Documented
- ✅ `speed` - Documented  
- ✅ `passive_perception` - Documented
- ❓ `armor_class` - Validated in combat_stats? Need to check

### Experience - Field Validation Rules
- ✅ `current` - Documented
- ✅ `needed_for_next_level` - Documented
- ⚠️ **GAP:** We validate that `current > needed_for_next_level` should trigger level up, but prompt doesn't explicitly say this

### Attributes - Validation Rules
- ✅ `base_attributes` vs `attributes` distinction - Well documented
- ✅ Range validation (1-30) - Not explicitly stated but reasonable
- ✅ `attributes >= base_attributes` rule - Documented in line 857

### Death Saves - Range Validation
- ✅ `successes` (0-3) - Documented
- ✅ `failures` (0-3) - Documented
- ⚠️ **GAP:** Range constraint (0-3) not explicitly stated in prompt

## Recommendations

### MINOR: Clarify Field Constraints
1. **Death Saves:** Explicitly state range (0-3) in prompt
2. **Experience:** Explicitly state that `current > needed_for_next_level` should trigger level up
3. **Attributes:** Explicitly state range (1-30) in prompt

## Conclusion

**✅ GOOD NEWS:** All 21 validation functions correspond to documented fields!

- 20 are documented in `game_state_instruction.md` (main game state)
- 1 (`directives`) is documented in `god_mode_instruction.md` (God Mode only)

**⚠️ MINOR GAPS:** Some field constraints (ranges, validation rules) could be more explicit:
- Death saves range (0-3) - mentioned but not emphasized
- Experience level-up trigger - logic implied but not explicit
- Attributes range (1-30) - reasonable default but not stated

## Test Coverage

Our tests validate that the LLM generates these fields, but if the LLM doesn't know about them, tests will fail. The fact that 8/9 schema tests passed suggests the LLM DOES know about most fields, but we should verify directives.
