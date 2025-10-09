# Python Modules: schemas

> Auto-generated overview of module docstrings and public APIs. Enhance descriptions as needed.
> Last updated: 2025-10-08

## `schemas/defensive_numeric_converter.py`

**Role:** Defensive numeric field converter that handles 'unknown' and invalid values

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class DefensiveNumericConverter` – Handles conversion of numeric fields with fallback defaults for unknown/invalid values. When invalid values are encountered, logs warnings and uses safe defaults. (Status: Keep).
  - `convert_value` – Convert a value to integer with defensive handling of unknown/invalid values. Args: key: The field name value: The value to potentially convert Returns: The value converted to int with appropriate defaults for unknown/invalid values (Status: Keep).
  - `convert_dict` – Recursively convert all numeric fields in a dictionary with defensive handling. Args: data: Dictionary to process Returns: Dictionary with numeric fields converted to integers with safe defaults (Status: Keep).

---

## `schemas/entities_pydantic.py`

**Role:** Pydantic schema models for entity tracking in Milestone 0.4 Uses sequence ID format: {type}_{name}_{sequence}

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `sanitize_entity_name_for_id` – Sanitize a name to create a valid entity ID component. Converts special characters to underscores to ensure compatibility with entity ID validation patterns. Args: name: Raw entity name (e.g., "Cazador's Spawn") Returns: Sanitized name suitable for entity ID (e.g., "cazadors_spawn") (Status: Keep).
- `class EntityType` – Entity type enumeration (Status: Keep).
- `class EntityStatus` – Common entity statuses (Status: Keep).
- `class Visibility` – Entity visibility states (Status: Keep).
- `class Stats` – D&D-style character stats with defensive conversion (Status: Keep).
  - `convert_strength` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `convert_dexterity` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `convert_constitution` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `convert_intelligence` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `convert_wisdom` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `convert_charisma` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `get_modifier` – Calculate D&D 5e ability modifier: (ability - 10) // 2 (Status: Keep).
- `class HealthStatus` – Health and condition tracking with defensive conversion (Status: Keep).
  - `convert_hp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `convert_hp_max` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `convert_temp_hp` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `hp_not_exceed_max` – No docstring present; review implementation to confirm behavior. (Status: Keep).
- `class Location` – Location entity model (Status: Keep).
- `class Character` – Comprehensive character model with narrative consistency and D&D 5e support (Status: Keep).
  - `convert_level` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `validate_gender` – Validate gender field for narrative consistency (permissive for LLM creativity) (Status: Keep).
  - `validate_age` – Validate age field for narrative consistency (Status: Keep).
  - `validate_mbti` – Validate personality field (accepts MBTI or creative descriptions) (Status: Keep).
  - `validate_alignment` – Validate alignment field (accepts D&D or creative alignments) (Status: Keep).
  - `validate_entity_type` – No docstring present; review implementation to confirm behavior. (Status: Keep).
  - `validate_npc_gender_required` – Ensure NPCs have gender field for narrative consistency (Status: Keep).
- `class PlayerCharacter` – Player character specific model (Status: Keep).
- `class NPC` – NPC specific model (Status: Keep).
- `class CombatState` – Combat tracking model (Status: Keep).
  - `validate_participants` – No docstring present; review implementation to confirm behavior. (Status: Keep).
- `class SceneManifest` – Complete scene state for validation (Status: Keep).
  - `validate_present_entities` – Ensure all present entities exist in the scene (Status: Keep).
  - `get_expected_entities` – Get list of entities that should be mentioned in narrative (Status: Keep).
  - `to_prompt_format` – Convert to structured format for prompt injection (Status: Keep).
  - `to_json_schema` – Generate JSON schema for structured output (Status: Keep).
- `create_from_game_state` – Create a SceneManifest from legacy game state format (Status: Keep).

---

