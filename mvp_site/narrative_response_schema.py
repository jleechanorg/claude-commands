# ruff: noqa: PLR0911,PLR0912,PLR0915
"""
Simplified structured narrative generation schemas
Based on Milestone 0.4 Combined approach implementation (without pydantic dependency)
"""

import copy
import hashlib
import json
import os
import re
from typing import Any

from mvp_site import logging_util

# Planning block extraction from narrative is deprecated - blocks should only come from JSON

# Minimum narrative length threshold for "suspiciously short" detection
# A valid narrative should typically be at least ~100 characters
MIN_NARRATIVE_LENGTH = 100

# Precompiled regex patterns for markdown code block extraction
# NOTE: Limited recovery for "Extra data" errors (valid JSON + trailing text) has been restored.
# Only markdown extraction patterns remain for extracting JSON from code blocks.
JSON_MARKDOWN_PATTERN = re.compile(r"```json\s*\n?(.*?)\n?```", re.DOTALL)
GENERIC_MARKDOWN_PATTERN = re.compile(r"```\s*\n?(.*?)\n?```", re.DOTALL)

# Planning block detection is handled via brace matching in
# `_remove_planning_json_blocks`; regex explorations are intentionally omitted
# to keep the implementation single-sourced.
# Quick check just verifies both required keys exist (order-independent).


def _log_json_parse_error(
    error: json.JSONDecodeError,
    json_content: str,
    logger_func: Any = logging_util.error,
    *,
    include_recovery_message: bool = False,
    base_message_prefix: str = "Failed to parse JSON response",
) -> None:
    """
    Log JSON parsing errors with security-conscious content handling.

    By default, logs a hash of the content to avoid leaking sensitive data.
    Full content logging is only enabled when LOG_JSON_ERRORS_FULL env var is set.

    Args:
        error: The JSONDecodeError exception
        json_content: The malformed JSON content
        logger_func: Logger function to use (default: logging_util.error)
        include_recovery_message: Whether to include recovery message (default: False)
        base_message_prefix: Custom prefix for the error message (default: "Failed to parse JSON response")
    """
    error_pos = getattr(error, "pos", None)
    log_full_content = os.getenv("LOG_JSON_ERRORS_FULL", "false").lower() == "true"

    # Compute content hash for safe logging
    content_hash = hashlib.sha256(json_content.encode("utf-8")).hexdigest()[:16]

    # Build error message
    base_msg = f"{base_message_prefix}: {error}"

    if error_pos is not None:
        # Show context around error position (if full logging enabled)
        start = max(0, error_pos - 500)
        end = min(len(json_content), error_pos + 500)
        context = json_content[start:end] if log_full_content else None

        if log_full_content and context:
            logger_func(
                f"{base_msg} "
                f"Error at position {error_pos}. "
                f"JSON context (chars {start}-{end}): {context[:1000]} "
                f"[Content hash: {content_hash}]"
            )
        else:
            logger_func(
                f"{base_msg} "
                f"Error at position {error_pos}. "
                f"Content hash: {content_hash} "
                f"(Set LOG_JSON_ERRORS_FULL=true to log full content)"
            )
    # No position available - log hash or truncated content
    elif log_full_content:
        logger_func(
            f"{base_msg} "
            f"Full JSON content (first 2000 chars): {json_content[:2000]} "
            f"[Content hash: {content_hash}]"
        )
    else:
        logger_func(
            f"{base_msg} "
            f"Content hash: {content_hash} "
            f"(Set LOG_JSON_ERRORS_FULL=true to log full content)"
        )

    # Log recovery message if requested
    if include_recovery_message:
        logger_func(
            "JSON recovery functionality has been removed - invalid JSON will fail completely."
        )


# Shared boolean coercion helper so validation and sanitization use consistent
# handling for truthy/falsey inputs.
def _coerce_bool(value: Any, *, context: str | None = None) -> bool:
    if isinstance(value, bool):
        return value

    coerced: bool
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            coerced = True
        elif normalized in {"false", "no", "0", ""}:
            coerced = False
        else:
            # Default to False for unknown strings to avoid accidental True
            # e.g., "unknown", "undefined", "null" should be False, not True
            coerced = False
            if context:
                logging_util.warning(
                    f"{context}: Unrecognized boolean string '{value}' coerced to False"
                )
    elif isinstance(value, (int, float)):
        coerced = value != 0
    else:
        coerced = bool(value)

    if context and not isinstance(value, str):
        logging_util.warning(
            f"{context} coerced boolean from {type(value).__name__} value {value!r} to {coerced}"
        )

    return coerced


# Mixed language detection - CJK (Chinese/Japanese/Korean) characters
# These can appear due to LLM training data leakage
CJK_PATTERN = re.compile(
    r"[\u4e00-\u9fff"  # CJK Unified Ideographs (Chinese)
    r"\u3040-\u309f"  # Hiragana (Japanese)
    r"\u30a0-\u30ff"  # Katakana (Japanese)
    r"\uac00-\ud7af"  # Hangul Syllables (Korean)
    r"\u3400-\u4dbf"  # CJK Unified Ideographs Extension A
    r"\U00020000-\U0002a6df"  # CJK Unified Ideographs Extension B
    r"]+"
)


MAX_PLANNING_JSON_BLOCK_CHARS = 50000


# =============================================================================
# PLANNING BLOCK SCHEMA - Single Source of Truth
# =============================================================================
# This is the canonical schema for planning blocks. All validation, prompts,
# and documentation should reference this constant.
#
# Two types of planning blocks use this schema:
# - Think Mode: Explicit THINK: prefix, time frozen (microsecond only)
# - Story Choices: Every story response, time advances normally
#
# The schema is the same; only time handling differs based on mode.
# =============================================================================

# NOTE: "story mode" refers to the UI's Character (narrative) mode controlled by the
# `char-mode` radio button. The switch flag keeps the existing name for backward
# compatibility while documenting the mapping to Character mode.
CHOICE_SCHEMA = {
    "text": str,  # Display name for the choice (REQUIRED)
    "description": str,  # What this choice entails (REQUIRED)
    "pros": list,  # Advantages (optional, list[str]; primitives may be coerced to str) - for frontend display; always at choice level
    "cons": list,  # Risks/disadvantages (optional, list[str]; primitives may be coerced to str) - for frontend display; always at choice level
    "confidence": str,  # "high" | "medium" | "low" (optional) - for frontend display; always at choice level
    "risk_level": str,  # "safe" | "low" | "medium" | "high" (REQUIRED)
    "analysis": dict,  # Additional non-display metadata (optional). For parallel execution: delegation_targets (list), personal_focus (str), coordination_dc (int)
    "switch_to_story_mode": bool,  # If true, selecting this choice switches UI to Character/story mode (optional)
}

PLANNING_BLOCK_SCHEMA = {
    # Plan quality (Think Mode only - based on INT/WIS roll vs DC)
    "plan_quality": {
        "stat_used": str,  # "Intelligence" or "Wisdom"
        "stat_value": int,  # Character's stat value
        "modifier": str,  # e.g., "+2"
        "roll_result": int,  # Dice roll result (1d20 + modifier)
        "dc": int,  # Difficulty Class for this planning check
        "dc_category": str,  # DC category name (e.g., "Complicated Planning")
        "dc_reasoning": str,  # Why this DC was chosen
        "success": bool,  # Whether roll >= DC
        "margin": int,  # How much above/below DC (positive = success)
        "quality_tier": str,  # "Confused" | "Muddled" | "Incomplete" | "Competent" | "Sharp" | "Brilliant" | "Masterful"
        "effect": str,  # Description of quality effect
    },
    # Core fields
    "thinking": str,  # Internal monologue analyzing the situation (REQUIRED for Think Mode)
    "context": str,  # Optional context/background (optional)
    # Situation assessment (optional - for detailed Think Mode analysis)
    "situation_assessment": {
        "current_state": str,  # Where you are and what's happening
        "key_factors": list,  # List of important factors (strings)
        "constraints": list,  # List of constraints (strings)
        "resources_available": list,  # List of available resources (strings)
    },
    # Choices - the core decision points (REQUIRED)
    "choices": {
        # Choice keys should be snake_case, may have god: or think: prefix
        # "<choice_key>": CHOICE_SCHEMA
        # Note: See planning_protocol.md for ordering rules (parallel execution must be last)
    },
    # Analysis (optional - for detailed Think Mode analysis)
    "analysis": {
        "recommended_approach": str,  # Which choice key is recommended
        "reasoning": str,  # Why this approach is recommended
        "contingency": str,  # Backup plan if primary fails
    },
}

# Valid risk levels for choices
VALID_RISK_LEVELS = {"safe", "low", "medium", "high"}

# Valid confidence levels for choices
VALID_CONFIDENCE_LEVELS = {"high", "medium", "low"}

# Valid quality tiers for plan_quality (matches think_mode_instruction.md)
# Now based on success/failure margin vs DC (not absolute roll values)
VALID_QUALITY_TIERS = {
    # FAILURE tiers (roll < DC)
    "Confused",  # Failed by 10+ (severe failure - dangerously wrong conclusions)
    "Muddled",  # Failed by 5-9 (significant failure)
    "Incomplete",  # Failed by 1-4 (minor failure)
    # SUCCESS tiers (roll >= DC)
    "Competent",  # Meet or beat DC by up to 4 (basic success)
    "Sharp",  # Beat DC by 5-9 (solid success)
    "Brilliant",  # Beat DC by 10-14 (excellent success)
    "Masterful",  # Beat DC by 15+ (critical success)
}

# =============================================================================
# SOCIAL HP CHALLENGE SCHEMA - Explicit JSON field for social skill challenges
# =============================================================================
# This schema defines the structured format for Social HP tracking.
# Previously this was embedded in narrative text and parsed via regex.
# Now it's an explicit JSON field for reliability.
#
# INPUT SCHEMA (What the LLM receives):
# - npc_data.<name>.tier - NPC tier (commoner/merchant/guard/noble/knight/lord/general/king/ancient/god/primordial)
# - npc_data.<name>.role - NPC role
# - npc_data.<name>.relationships.player.trust_level - Current trust level (-10 to +10)
#
# OUTPUT SCHEMA (What the LLM must return):
# - npc_tier - MUST be extracted from INPUT: npc_data.<name>.tier
# - social_hp_max - Calculated from npc_tier:
#   * commoner: 1-2
#   * merchant/guard: 2-3
#   * noble/knight: 3-5
#   * lord/general: 5-8
#   * king/ancient: 8-12
#   * god/primordial: 15+
#
# FIELD MAPPING:
# OUTPUT.npc_tier = extract from INPUT.npc_data.<name>.tier
# OUTPUT.social_hp_max = calculate from OUTPUT.npc_tier using ranges above
#
# Per roadmap/llm_schema_alignment_gaps.md - Priority 1 (Critical)

SOCIAL_HP_CHALLENGE_SCHEMA = {
    "npc_id": str,  # NPC identifier (optional, for state linking)
    "npc_name": str,  # Display name (REQUIRED)
    "objective": str,  # What player wants to achieve (REQUIRED)
    "request_severity": str,  # information | favor | submission
    "social_hp": int,  # Current Social HP remaining (REQUIRED)
    "social_hp_max": int,  # Maximum Social HP (REQUIRED)
    "successes": int,  # Current successes achieved
    "successes_needed": int,  # Required successes to win
    "status": str,  # RESISTING | WAVERING | YIELDING | SURRENDERED
    "resistance_shown": str,  # Resistance indicator text
    "skill_used": str,  # Persuasion | Deception | Intimidation | Insight
    "roll_result": int,  # This turn's roll result
    "roll_dc": int,  # DC for the skill check
    "social_hp_damage": int,  # Damage dealt this turn (0-2)
}

# Valid Social HP status values
VALID_SOCIAL_HP_STATUS = {"RESISTING", "WAVERING", "YIELDING", "SURRENDERED"}

# Valid request severity values
VALID_SOCIAL_HP_REQUEST_SEVERITY = {"information", "favor", "submission"}

# Valid social skills
VALID_SOCIAL_SKILLS = {"Persuasion", "Deception", "Intimidation", "Insight"}

# =============================================================================
# COMBAT STATE SCHEMA - Explicit validation for combat state
# =============================================================================
# This schema defines the structured format for combat state tracking.
# Per roadmap/llm_schema_alignment_gaps.md - Priority 1 (Critical)

COMBAT_PHASE_ENUM = {"initiating", "active", "ended", "fled"}

COMBAT_STATE_SCHEMA = {
    "in_combat": bool,
    "combat_session_id": str,  # Format: combat_<timestamp>_<4char>
    "combat_phase": str,  # Must be in COMBAT_PHASE_ENUM
    "current_round": int,
    "initiative_order": list,  # Array of {name, initiative, type}
    "combatants": dict,  # Dict of combatant data
    "combat_summary": dict,  # {rounds_fought, enemies_defeated, xp_awarded, loot_distributed}
    "rewards_processed": bool,
}

# =============================================================================
# REPUTATION SCHEMA - Explicit validation for reputation tracking
# =============================================================================
# Per roadmap/llm_schema_alignment_gaps.md - Priority 1 (Critical)

VALID_NOTORIETY_LEVELS = {
    "infamous",
    "notorious",
    "disreputable",
    "unknown",
    "known",
    "respected",
    "famous",
    "legendary",
}

VALID_STANDING_LEVELS = {
    "enemy",
    "hostile",
    "unfriendly",
    "neutral",
    "friendly",
    "trusted",
    "ally",
    "champion",
}

REPUTATION_PUBLIC_SCHEMA = {
    "score": int,  # Range: -100 to +100
    "titles": list,
    "known_deeds": list,
    "rumors": list,
    "notoriety_level": str,  # Must be in VALID_NOTORIETY_LEVELS
}

REPUTATION_PRIVATE_SCHEMA = {
    "score": int,  # Range: -10 to +10
    "standing": str,  # Must be in VALID_STANDING_LEVELS
    "known_deeds": list,
    "secret_knowledge": list,
    "trust_override": int | None,
}

# =============================================================================
# RELATIONSHIP SCHEMA - Explicit validation for relationship tracking
# =============================================================================
# Per roadmap/llm_schema_alignment_gaps.md - Priority 2 (High)

VALID_DISPOSITIONS = {
    "hostile",
    "antagonistic",
    "cold",
    "neutral",
    "friendly",
    "allied",  # Documented in game_state_instruction.md line 765
    "trusted",
    "devoted",
    "bonded",
}

RELATIONSHIP_SCHEMA = {
    "trust_level": int,  # Range: -10 to +10
    "disposition": str,  # Must be in VALID_DISPOSITIONS
    "history": list,  # Array of strings
    "debts": list,  # Array of strings
    "grievances": list,  # Array of strings
}

# =============================================================================
# WORLD TIME SCHEMA - Explicit validation for world time tracking
# =============================================================================
# Per roadmap/llm_schema_alignment_gaps.md - Priority 2 (High)

VALID_TIME_OF_DAY = {
    "Dawn",
    "Morning",
    "Midday",
    "Afternoon",
    "Evening",
    "Night",
    "Deep Night",
}

WORLD_TIME_SCHEMA = {
    "year": int,
    "month": str | int,
    "day": int,  # Range: 1-31
    "hour": int,  # Range: 0-23
    "minute": int,  # Range: 0-59
    "second": int,  # Range: 0-59
    "microsecond": int,  # Range: 0-999999
    "time_of_day": str,  # Must be in VALID_TIME_OF_DAY
}

# =============================================================================
# ENCOUNTER STATE SCHEMA - Explicit validation for encounter tracking
# =============================================================================
# Per roadmap/llm_schema_alignment_gaps.md - Priority 2 (High)

VALID_ENCOUNTER_TYPES = {
    "heist",
    "social",
    "stealth",
    "puzzle",
    "quest",
    "narrative_victory",
}

VALID_ENCOUNTER_DIFFICULTIES = {"easy", "medium", "hard", "deadly"}

ENCOUNTER_STATE_SCHEMA = {
    "encounter_active": bool,
    "encounter_id": str,  # Format: enc_<timestamp>_<type>_###
    "encounter_type": str,  # Must be in VALID_ENCOUNTER_TYPES
    "difficulty": str,  # Must be in VALID_ENCOUNTER_DIFFICULTIES
    "encounter_completed": bool,
    "encounter_summary": dict,  # {xp_awarded, outcome, method}
    "rewards_processed": bool,
}

# =============================================================================
# FROZEN PLANS SCHEMA - Explicit validation for frozen plans tracking
# =============================================================================
# Per roadmap/llm_schema_alignment_gaps.md - Priority 3 (Medium)
# Note: frozen_plans is LLM-enforced via prompts, but we document structure

FROZEN_PLANS_SCHEMA = {
    "<plan_topic_key>": {
        "failed_at": str,  # ISO timestamp or world_time string
        "freeze_until": str,  # ISO timestamp or world_time string
        "original_dc": int,
        "freeze_hours": int,
        "description": str,
    }
}

# =============================================================================
# DIRECTIVES SCHEMA - Explicit validation for god mode directives
# =============================================================================
# Per roadmap/llm_schema_alignment_gaps.md - Priority 3 (Medium)

DIRECTIVES_SCHEMA = {
    "add": list,  # Array of strings
    "drop": list,  # Array of strings
}

# =============================================================================
# EQUIPMENT SLOT ENUM - Valid equipment slot names
# =============================================================================
# Per roadmap/llm_schema_alignment_gaps.md - Priority 3 (Medium)

VALID_EQUIPMENT_SLOTS = {
    "head",
    "body",
    "armor",
    "cloak",
    "hands",
    "feet",
    "neck",
    "ring_1",
    "ring_2",
    "belt",
    "shield",
    "main_hand",
    "off_hand",
    "instrument",
    "weapons",  # Array slot
    "backpack",  # Array slot
}

# Forbidden slot name mappings (should be normalized)
FORBIDDEN_SLOT_MAPPINGS = {
    "weapon_main": "main_hand",
    "boots": "feet",
}

# =============================================================================
# ARC MILESTONES SCHEMA - Explicit validation for arc milestone tracking
# =============================================================================
# Per roadmap/llm_schema_alignment_gaps.md - Priority 4 (Low)

VALID_ARC_MILESTONE_STATUS = {"in_progress", "completed"}

ARC_MILESTONE_SCHEMA = {
    "status": str,  # Must be in VALID_ARC_MILESTONE_STATUS
    "phase": str,
    "progress": int,  # Range: 0-100
    "updated_at": str | None,  # ISO timestamp
    "completed_at": str | None,  # ISO timestamp
}

# =============================================================================
# TIME PRESSURE SYSTEM SCHEMA - Explicit validation for time pressure tracking
# =============================================================================
# Per roadmap/llm_schema_alignment_gaps.md - Priority 4 (Low)

TIME_PRESSURE_WARNINGS_SCHEMA = {
    "subtle_given": bool,
    "clear_given": bool,
    "urgent_given": bool,
    "last_warning_day": int,
}

# =============================================================================
# RESOURCES SCHEMA - Explicit validation for resources tracking
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 1 (Critical)

RESOURCES_SCHEMA = {
    "gold": int,  # >= 0
    "hit_dice": dict,  # {used: int (0-total), total: int (>= 0)}
    "spell_slots": dict,  # {level_X: {current: int (0-max), max: int (>= 0)}}
    "class_features": dict,  # Class-specific resources (varies by class)
    "consumables": dict,  # Consumable items
}

# =============================================================================
# SPELL SLOTS SCHEMA - Explicit validation for spell slot tracking
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 1 (Critical)

VALID_SPELL_SLOT_LEVELS = {
    "level_1",
    "level_2",
    "level_3",
    "level_4",
    "level_5",
    "level_6",
    "level_7",
    "level_8",
    "level_9",
}

SPELL_SLOTS_SCHEMA = {
    "<level_X>": {
        "used": int,  # Range: 0 to max (alias: "current" also accepted)
        "current": int,  # Range: 0 to max (deprecated, use "used")
        "max": int,  # Range: >= 0
    }
}

# =============================================================================
# CLASS FEATURES SCHEMA - Explicit validation for class-specific resources
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 1 (Critical)

VALID_CLASS_FEATURES = {
    "bardic_inspiration",
    "ki_points",
    "rage",
    "channel_divinity",
    "lay_on_hands",
    "sorcery_points",
    "wild_shape",
}

CLASS_FEATURES_SCHEMA = {
    "<feature_name>": {
        "used": int,  # Range: 0 to max (alias: "current" also accepted)
        "current": int,  # Range: 0 to max (deprecated, use "used")
        "max": int,  # Range: >= 0
    }
}

# =============================================================================
# ATTRIBUTES SCHEMA - Explicit validation for attributes tracking
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 2 (High)

# Support both abbreviated (STR, DEX, etc.) and full names (strength, dexterity, etc.)
VALID_ATTRIBUTE_NAMES_ABBREV = {"STR", "DEX", "CON", "INT", "WIS", "CHA"}
VALID_ATTRIBUTE_NAMES_FULL = {"strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"}
VALID_ATTRIBUTE_NAMES = VALID_ATTRIBUTE_NAMES_ABBREV | VALID_ATTRIBUTE_NAMES_FULL

# Mapping between formats for validation
ATTRIBUTE_NAME_MAPPING = {
    "STR": "strength",
    "DEX": "dexterity",
    "CON": "constitution",
    "INT": "intelligence",
    "WIS": "wisdom",
    "CHA": "charisma",
    "strength": "STR",
    "dexterity": "DEX",
    "constitution": "CON",
    "intelligence": "INT",
    "wisdom": "WIS",
    "charisma": "CHA",
}

ATTRIBUTES_SCHEMA = {
    "base_attributes": dict,  # {STR: int (1-30), DEX: int (1-30), ...}
    "attributes": dict,  # {STR: int (1-30), DEX: int (1-30), ...}
}

# =============================================================================
# EXPERIENCE SCHEMA - Explicit validation for experience tracking
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 2 (High)

EXPERIENCE_SCHEMA = {
    "current": int,  # >= 0
    "needed_for_next_level": int,  # >= current
}

# =============================================================================
# DEATH SAVES SCHEMA - Explicit validation for death saves tracking
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 2 (High)

DEATH_SAVES_SCHEMA = {
    "successes": int,  # Range: 0-3
    "failures": int,  # Range: 0-3
}

# =============================================================================
# SPELLS KNOWN SCHEMA - Explicit validation for spells known tracking
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 2 (High)

SPELLS_KNOWN_SCHEMA = {
    "name": str,  # Required
    "level": int,  # Range: 0-9
    # Optional: school, casting_time, range, components, duration
}

# =============================================================================
# STATUS CONDITIONS SCHEMA - Explicit validation for status conditions tracking
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 3 (Medium)

# Common D&D 5e status conditions (from SRD)
VALID_STATUS_CONDITIONS = {
    "Blinded",
    "Charmed",
    "Deafened",
    "Exhaustion",
    "Frightened",
    "Grappled",
    "Incapacitated",
    "Invisible",
    "Paralyzed",
    "Petrified",
    "Poisoned",
    "Prone",
    "Restrained",
    "Stunned",
    "Unconscious",
}

STATUS_CONDITIONS_SCHEMA = list  # Array of strings

# =============================================================================
# ACTIVE EFFECTS SCHEMA - Explicit validation for active effects tracking
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 3 (Medium)

ACTIVE_EFFECTS_SCHEMA = list  # Array of strings describing persistent buffs/effects

# =============================================================================
# COMBAT STATS SCHEMA - Explicit validation for combat stats tracking
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 3 (Medium)

COMBAT_STATS_SCHEMA = {
    "initiative": int,
    "speed": int,  # >= 0
    "passive_perception": int,  # >= 0
}

# =============================================================================
# ITEM SCHEMAS - Explicit validation for equipment items
# =============================================================================
# Per roadmap/schema_validation_gaps_resources_spells.md - Priority 3 (Medium)

VALID_DAMAGE_TYPES = {
    "acid",
    "bludgeoning",
    "cold",
    "fire",
    "force",
    "lightning",
    "necrotic",
    "piercing",
    "poison",
    "psychic",
    "radiant",
    "slashing",
    "thunder",
}

VALID_ARMOR_TYPES = {"light", "medium", "heavy"}

WEAPON_SCHEMA = {
    "name": str,
    "type": str,  # Must be "weapon"
    "damage": str,  # Dice notation (e.g., "1d8")
    "damage_type": str,  # Must be in VALID_DAMAGE_TYPES
    "properties": list,  # Optional
    "bonus": int,  # Optional
    "weight": int | float,  # Optional
    "value_gp": int | float,  # Optional
}

ARMOR_SCHEMA = {
    "name": str,
    "type": str,  # Must be "armor"
    "armor_class": int,  # Range: 1-30
    "armor_type": str,  # Must be in VALID_ARMOR_TYPES
    "stealth_disadvantage": bool,  # Optional
    "strength_requirement": int,  # Optional
    "weight": int | float,  # Optional
    "value_gp": int | float,  # Optional
}


def _validate_combat_state(combat_state: dict[str, Any]) -> list[str]:
    """Validate combat_state structure. Returns list of error messages (empty if valid)."""
    errors = []

    if "combat_phase" in combat_state:
        phase = combat_state["combat_phase"]
        # Type check before set membership to avoid TypeError on unhashable types (list/dict)
        if not isinstance(phase, str) or phase not in COMBAT_PHASE_ENUM:
            errors.append(
                f"Invalid combat_phase '{phase}', must be one of {COMBAT_PHASE_ENUM}"
            )

    if "combat_session_id" in combat_state:
        session_id = combat_state["combat_session_id"]
        if not isinstance(session_id, str):
            errors.append("combat_session_id must be a string")
        elif not session_id.startswith("combat_"):
            errors.append(
                f"combat_session_id must start with 'combat_', got '{session_id}'"
            )
        else:
            # Validate format: combat_<timestamp>_<4char>
            # Timestamp should be numeric, suffix should be 4 alphanumeric characters
            pattern = r"^combat_\d+_[a-zA-Z0-9]{4}$"
            if not re.match(pattern, session_id):
                errors.append(
                    f"combat_session_id must match format 'combat_<timestamp>_<4char>', got '{session_id}'"
                )

    return errors


def _validate_reputation(reputation: dict[str, Any]) -> list[str]:
    """Validate reputation structure. Returns list of error messages (empty if valid)."""
    errors = []

    if "public" in reputation:
        public = reputation["public"]
        if isinstance(public, dict):
            if "score" in public:
                score = public["score"]
                # Strict type checking: must be int, not float (e.g., 50.0 is rejected)
                if not isinstance(score, int) or score < -100 or score > 100:
                    errors.append(
                        f"Public reputation score must be an integer between -100 and +100, got {score}"
                    )

            if "notoriety_level" in public:
                level = public["notoriety_level"]
                # Type check before set membership to avoid TypeError on unhashable types (list/dict)
                if not isinstance(level, str) or level not in VALID_NOTORIETY_LEVELS:
                    errors.append(
                        f"Invalid notoriety_level '{level}', must be one of {VALID_NOTORIETY_LEVELS}"
                    )

    if "private" in reputation:
        private = reputation["private"]
        if isinstance(private, dict):
            for faction_id, faction_data in private.items():
                if isinstance(faction_data, dict):
                    if "score" in faction_data:
                        score = faction_data["score"]
                        # Strict type checking: must be int, not float (e.g., 5.0 is rejected)
                        if not isinstance(score, int) or score < -10 or score > 10:
                            errors.append(
                                f"Private reputation score for {faction_id} must be an integer between -10 and +10, got {score}"
                            )

                    if "standing" in faction_data:
                        standing = faction_data["standing"]
                        # Type check before set membership to avoid TypeError on unhashable types (list/dict)
                        if (
                            not isinstance(standing, str)
                            or standing not in VALID_STANDING_LEVELS
                        ):
                            errors.append(
                                f"Invalid standing '{standing}' for {faction_id}, must be one of {VALID_STANDING_LEVELS}"
                            )

    return errors


def _validate_relationship(relationship: dict[str, Any]) -> list[str]:
    """Validate relationship structure. Returns list of error messages (empty if valid)."""
    errors = []

    if "trust_level" in relationship:
        trust_level = relationship["trust_level"]
        # Strict type checking: must be int, not float (e.g., 5.0 is rejected)
        if not isinstance(trust_level, int) or trust_level < -10 or trust_level > 10:
            errors.append(
                f"trust_level must be an integer between -10 and +10, got {trust_level}"
            )

    if "disposition" in relationship:
        disposition = relationship["disposition"]
        # Type check before set membership to avoid TypeError on unhashable types (list/dict)
        if not isinstance(disposition, str) or disposition not in VALID_DISPOSITIONS:
            errors.append(
                f"Invalid disposition '{disposition}', must be one of {VALID_DISPOSITIONS}"
            )

    return errors


def _validate_world_time(world_time: dict[str, Any]) -> list[str]:
    """Validate world_time structure. Returns list of error messages (empty if valid).

    Validates 6 of 8 required fields (day, hour, minute, second, microsecond, time_of_day).
    Year and month are not validated as they have no range constraints (year: any int, month: str | int).
    """
    errors = []

    if "day" in world_time:
        day = world_time["day"]
        # Strict type checking: must be int, not float (e.g., 15.0 is rejected)
        if not isinstance(day, int) or day < 1 or day > 31:
            errors.append(f"day must be an integer between 1 and 31, got {day}")

    if "hour" in world_time:
        hour = world_time["hour"]
        # Strict type checking: must be int, not float (e.g., 10.0 is rejected)
        if not isinstance(hour, int) or hour < 0 or hour > 23:
            errors.append(f"hour must be an integer between 0 and 23, got {hour}")

    if "minute" in world_time:
        minute = world_time["minute"]
        # Strict type checking: must be int, not float (e.g., 30.0 is rejected)
        if not isinstance(minute, int) or minute < 0 or minute > 59:
            errors.append(f"minute must be an integer between 0 and 59, got {minute}")

    if "second" in world_time:
        second = world_time["second"]
        # Strict type checking: must be int, not float (e.g., 45.0 is rejected)
        if not isinstance(second, int) or second < 0 or second > 59:
            errors.append(f"second must be an integer between 0 and 59, got {second}")

    if "microsecond" in world_time:
        microsecond = world_time["microsecond"]
        # Strict type checking: must be int, not float (e.g., 123456.0 is rejected)
        if not isinstance(microsecond, int) or microsecond < 0 or microsecond > 999999:
            errors.append(
                f"microsecond must be an integer between 0 and 999999, got {microsecond}"
            )

    if "time_of_day" in world_time:
        time_of_day = world_time["time_of_day"]
        # Type check before set membership to avoid TypeError on unhashable types (list/dict)
        if not isinstance(time_of_day, str) or time_of_day not in VALID_TIME_OF_DAY:
            errors.append(
                f"Invalid time_of_day '{time_of_day}', must be one of {VALID_TIME_OF_DAY}"
            )

    return errors


def _validate_encounter_state(encounter_state: dict[str, Any]) -> list[str]:
    """Validate encounter_state structure. Returns list of error messages (empty if valid)."""
    errors = []

    if "encounter_type" in encounter_state:
        encounter_type = encounter_state["encounter_type"]
        # Type check before set membership to avoid TypeError on unhashable types (list/dict)
        if (
            not isinstance(encounter_type, str)
            or encounter_type not in VALID_ENCOUNTER_TYPES
        ):
            errors.append(
                f"Invalid encounter_type '{encounter_type}', must be one of {VALID_ENCOUNTER_TYPES}"
            )

    if "difficulty" in encounter_state:
        difficulty = encounter_state["difficulty"]
        # Type check before set membership to avoid TypeError on unhashable types (list/dict)
        if (
            not isinstance(difficulty, str)
            or difficulty not in VALID_ENCOUNTER_DIFFICULTIES
        ):
            errors.append(
                f"Invalid difficulty '{difficulty}', must be one of {VALID_ENCOUNTER_DIFFICULTIES}"
            )

    return errors


def _validate_frozen_plans(frozen_plans: dict[str, Any]) -> list[str]:
    """Validate frozen_plans structure. Returns list of error messages (empty if valid).

    Note: frozen_plans is LLM-enforced via prompts, but we validate structure for consistency.
    """
    errors = []

    if not isinstance(frozen_plans, dict):
        errors.append("frozen_plans must be a dict")
        return errors

    for plan_key, plan_data in frozen_plans.items():
        if not isinstance(plan_data, dict):
            errors.append(f"frozen_plans.{plan_key} must be a dict")
            continue

        # Validate required fields exist
        required_fields = [
            "failed_at",
            "freeze_until",
            "original_dc",
            "freeze_hours",
            "description",
        ]
        for field in required_fields:
            if field not in plan_data:
                errors.append(
                    f"frozen_plans.{plan_key} missing required field: {field}"
                )

        # Validate original_dc is integer
        if "original_dc" in plan_data and not isinstance(plan_data["original_dc"], int):
            errors.append(f"frozen_plans.{plan_key}.original_dc must be an integer")

        # Validate freeze_hours is integer
        if "freeze_hours" in plan_data and not isinstance(
            plan_data["freeze_hours"], int
        ):
            errors.append(f"frozen_plans.{plan_key}.freeze_hours must be an integer")

    return errors


def _validate_directives(directives: dict[str, Any]) -> list[str]:
    """Validate directives structure. Returns list of error messages (empty if valid)."""
    errors = []

    if "add" in directives:
        if not isinstance(directives["add"], list):
            errors.append("directives.add must be an array")
        elif not all(isinstance(item, str) for item in directives["add"]):
            errors.append("directives.add must be an array of strings")

    if "drop" in directives:
        if not isinstance(directives["drop"], list):
            errors.append("directives.drop must be an array")
        elif not all(isinstance(item, str) for item in directives["drop"]):
            errors.append("directives.drop must be an array of strings")

    return errors


def _validate_equipment_slots(equipment: dict[str, Any]) -> list[str]:
    """Validate equipment slot names. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(equipment, dict):
        errors.append("equipment must be a dict")
        return errors

    for slot_name in equipment:
        # Check for forbidden slot mappings
        if slot_name in FORBIDDEN_SLOT_MAPPINGS:
            errors.append(
                f"Invalid equipment slot '{slot_name}', use '{FORBIDDEN_SLOT_MAPPINGS[slot_name]}' instead"
            )
        # Check if slot is valid (allow array slots like weapons/backpack)
        elif slot_name not in VALID_EQUIPMENT_SLOTS:
            errors.append(
                f"Invalid equipment slot '{slot_name}', must be one of {VALID_EQUIPMENT_SLOTS}"
            )

    return errors


def _validate_arc_milestones(arc_milestones: dict[str, Any]) -> list[str]:
    """Validate arc_milestones structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(arc_milestones, dict):
        errors.append("arc_milestones must be a dict")
        return errors

    for arc_key, milestone_data in arc_milestones.items():
        if not isinstance(milestone_data, dict):
            errors.append(f"arc_milestones.{arc_key} must be a dict")
            continue

        # Validate status enum
        if "status" in milestone_data:
            status = milestone_data["status"]
            # Type check before set membership to avoid TypeError on unhashable types (list/dict)
            if not isinstance(status, str) or status not in VALID_ARC_MILESTONE_STATUS:
                errors.append(
                    f"arc_milestones.{arc_key}.status must be one of {VALID_ARC_MILESTONE_STATUS}, got '{status}'"
                )

        # Validate progress range (0-100)
        if "progress" in milestone_data:
            progress = milestone_data["progress"]
            # Strict type checking: must be int, not float (e.g., 45.0 is rejected)
            if not isinstance(progress, int) or progress < 0 or progress > 100:
                errors.append(
                    f"arc_milestones.{arc_key}.progress must be an integer between 0 and 100, got {progress}"
                )

    return errors


def _validate_time_pressure_warnings(
    time_pressure_warnings: dict[str, Any],
) -> list[str]:
    """Validate time_pressure_warnings structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(time_pressure_warnings, dict):
        errors.append("time_pressure_warnings must be a dict")
        return errors

    # Validate boolean fields
    for field in ["subtle_given", "clear_given", "urgent_given"]:
        if field in time_pressure_warnings:
            if not isinstance(time_pressure_warnings[field], bool):
                errors.append(f"time_pressure_warnings.{field} must be a boolean")

    # Validate last_warning_day is integer
    if "last_warning_day" in time_pressure_warnings:
        if not isinstance(time_pressure_warnings["last_warning_day"], int):
            errors.append("time_pressure_warnings.last_warning_day must be an integer")

    return errors


def _validate_resources(resources: dict[str, Any]) -> list[str]:
    """Validate resources structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(resources, dict):
        errors.append("resources must be a dict")
        return errors

    # Validate gold (must be int >= 0)
    if "gold" in resources:
        gold = resources["gold"]
        if gold is None:
            errors.append("resources.gold cannot be None")
        elif isinstance(gold, float) and gold.is_integer():
            # Allow whole number floats like 50.0
            pass  # Valid
        elif not isinstance(gold, int) or gold < 0:
            errors.append(f"resources.gold must be an integer >= 0, got {gold}")

    # Validate hit_dice structure
    if "hit_dice" in resources:
        hit_dice = resources["hit_dice"]
        if isinstance(hit_dice, dict):
            # Accept both "max" (actual game state) and "total" (legacy schema)
            used = hit_dice.get("used")
            # Preserve 0 values - only fall back to "total" if "max" is missing (not if it's 0)
            max_or_total = hit_dice.get("max") if "max" in hit_dice else hit_dice.get("total")

            if used is None:
                errors.append("resources.hit_dice.used cannot be None")
            elif isinstance(used, float) and used.is_integer():
                # Allow whole number floats
                pass
            elif not isinstance(used, int) or used < 0:
                errors.append(
                    f"resources.hit_dice.used must be an integer >= 0, got {used}"
                )

            if max_or_total is None:
                errors.append("resources.hit_dice.max/total cannot be None")
            elif isinstance(max_or_total, float) and max_or_total.is_integer():
                # Allow whole number floats
                pass
            elif not isinstance(max_or_total, int) or max_or_total < 0:
                errors.append(
                    f"resources.hit_dice.max/total must be an integer >= 0, got {max_or_total}"
                )

            # Validate used <= max/total
            if used is not None and max_or_total is not None:
                if (
                    isinstance(used, int)
                    and isinstance(max_or_total, int)
                    and used > max_or_total
                ):
                    errors.append(
                        f"resources.hit_dice.used ({used}) cannot exceed max/total ({max_or_total})"
                    )

            # Warn if both "max" and "total" are present (should use only one)
            if "max" in hit_dice and "total" in hit_dice:
                errors.append(
                    "resources.hit_dice has both 'max' and 'total' - use only 'max'"
                )

    # Validate consumables (can be dict or array)
    if "consumables" in resources:
        consumables = resources["consumables"]
        if consumables is not None and not isinstance(consumables, (dict, list)):
            errors.append(
                f"resources.consumables must be a dict or array, got {type(consumables).__name__}"
            )

    # Note: spell_slots and class_features are validated separately in _validate_state_updates()
    # to provide clearer error message prefixes (SPELL_SLOTS_VALIDATION vs RESOURCES_VALIDATION)

    return errors


def _validate_spell_slots(spell_slots: dict[str, Any]) -> list[str]:
    """Validate spell_slots structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(spell_slots, dict):
        errors.append("spell_slots must be a dict")
        return errors

    for level_key, level_data in spell_slots.items():
        # Validate level key format (level_1 through level_9)
        if level_key not in VALID_SPELL_SLOT_LEVELS:
            errors.append(
                f"Invalid spell slot level '{level_key}', must be one of {VALID_SPELL_SLOT_LEVELS}"
            )

        # Validate level data structure
        if isinstance(level_data, dict):
            # Accept both "used" (actual game state) and "current" (legacy schema)
            # Preserve 0 values - only fall back to "current" if "used" is missing (not if it's 0)
            used_value = level_data.get("used") if "used" in level_data else level_data.get("current")

            if used_value is not None:
                # Strict type checking: must be int, not float
                if not isinstance(used_value, int) or used_value < 0:
                    errors.append(
                        f"spell_slots.{level_key}.used/current must be an integer >= 0, got {used_value}"
                    )

            if "max" in level_data:
                max_slots = level_data["max"]
                # Strict type checking: must be int, not float
                if not isinstance(max_slots, int) or max_slots < 0:
                    errors.append(
                        f"spell_slots.{level_key}.max must be an integer >= 0, got {max_slots}"
                    )

            # Validate used/current <= max
            if used_value is not None and "max" in level_data:
                max_slots = level_data["max"]
                if (
                    isinstance(used_value, int)
                    and isinstance(max_slots, int)
                    and used_value > max_slots
                ):
                    errors.append(
                        f"spell_slots.{level_key}.used/current ({used_value}) cannot exceed max ({max_slots})"
                    )

            # Warn if both "used" and "current" are present (should use only one)
            if "used" in level_data and "current" in level_data:
                errors.append(
                    f"spell_slots.{level_key} has both 'used' and 'current' - use only 'used'"
                )

    return errors


def _validate_class_features(class_features: dict[str, Any]) -> list[str]:
    """Validate class_features structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(class_features, dict):
        errors.append("class_features must be a dict")
        return errors

    for feature_name, feature_data in class_features.items():
        # Validate feature data structure
        if isinstance(feature_data, dict):
            # Accept both "used" (actual game state) and "current" (legacy schema)
            # Preserve 0 values - only fall back to "current" if "used" is missing (not if it's 0)
            used_value = feature_data.get("used") if "used" in feature_data else feature_data.get("current")

            if used_value is not None:
                # Strict type checking: must be int, not float
                if not isinstance(used_value, int) or used_value < 0:
                    errors.append(
                        f"class_features.{feature_name}.used/current must be an integer >= 0, got {used_value}"
                    )

            if "max" in feature_data:
                max_value = feature_data["max"]
                # Strict type checking: must be int, not float
                if not isinstance(max_value, int) or max_value < 0:
                    errors.append(
                        f"class_features.{feature_name}.max must be an integer >= 0, got {max_value}"
                    )

            # Validate used/current <= max
            if used_value is not None and "max" in feature_data:
                max_value = feature_data["max"]
                if (
                    isinstance(used_value, int)
                    and isinstance(max_value, int)
                    and used_value > max_value
                ):
                    errors.append(
                        f"class_features.{feature_name}.used/current ({used_value}) cannot exceed max ({max_value})"
                    )

            # Warn if both "used" and "current" are present (should use only one)
            if "used" in feature_data and "current" in feature_data:
                errors.append(
                    f"class_features.{feature_name} has both 'used' and 'current' - use only 'used'"
                )

    return errors


def _validate_attributes(player_data: dict[str, Any]) -> list[str]:
    """Validate attributes structure. Returns list of error messages (empty if valid)."""
    errors = []

    base_attributes = player_data.get("base_attributes", {})
    attributes = player_data.get("attributes", {})

    if not isinstance(base_attributes, dict) or not isinstance(attributes, dict):
        return ["base_attributes and attributes must be dicts"]

    # Collect all attribute keys from both dicts to validate what's actually present
    all_attr_keys = set(base_attributes.keys()) | set(attributes.keys())

    # Validate each attribute stat that appears in either dict
    for stat_name in all_attr_keys:
        # Check if it's a valid attribute name (either abbreviated or full format)
        if stat_name not in VALID_ATTRIBUTE_NAMES:
            errors.append(
                f"Unknown attribute name '{stat_name}'. Valid names are: {sorted(VALID_ATTRIBUTE_NAMES_ABBREV)} or {sorted(VALID_ATTRIBUTE_NAMES_FULL)}"
            )
            continue

        base_value = base_attributes.get(stat_name)
        if base_value is not None:
            if isinstance(base_value, float) and base_value.is_integer():
                # Allow whole number floats
                pass
            elif not isinstance(base_value, int) or base_value < 1 or base_value > 30:
                errors.append(
                    f"base_attributes.{stat_name} must be an integer between 1 and 30, got {base_value}"
                )

        attr_value = attributes.get(stat_name)
        if attr_value is not None:
            if isinstance(attr_value, float) and attr_value.is_integer():
                # Allow whole number floats
                pass
            elif not isinstance(attr_value, int) or attr_value < 1 or attr_value > 30:
                errors.append(
                    f"attributes.{stat_name} must be an integer between 1 and 30, got {attr_value}"
                )

        # Validate attributes >= base_attributes (equipment can only add)
        if base_value is not None and attr_value is not None:
            if (
                isinstance(base_value, (int, float))
                and isinstance(attr_value, (int, float))
                and float(attr_value) < float(base_value)
            ):
                errors.append(
                    f"attributes.{stat_name} ({attr_value}) cannot be less than base_attributes.{stat_name} ({base_value})"
                )

    return errors


def _validate_experience(experience: dict[str, Any]) -> list[str]:
    """Validate experience structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(experience, dict):
        errors.append("experience must be a dict")
        return errors

    if "current" in experience:
        current = experience["current"]
        # Strict type checking: must be int, not float
        if not isinstance(current, int) or current < 0:
            errors.append(f"experience.current must be an integer >= 0, got {current}")

    if "needed_for_next_level" in experience:
        needed = experience["needed_for_next_level"]
        # Strict type checking: must be int, not float
        if not isinstance(needed, int) or needed < 0:
            errors.append(
                f"experience.needed_for_next_level must be an integer >= 0, got {needed}"
            )

    # Warn if current > needed_for_next_level (should trigger level up)
    if "current" in experience and "needed_for_next_level" in experience:
        current = experience["current"]
        needed = experience["needed_for_next_level"]
        if isinstance(current, int) and isinstance(needed, int) and current > needed:
            errors.append(
                f"experience.current ({current}) exceeds needed_for_next_level ({needed}) - level up should trigger"
            )

    return errors


def _validate_death_saves(death_saves: dict[str, Any]) -> list[str]:
    """Validate death_saves structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(death_saves, dict):
        errors.append("death_saves must be a dict")
        return errors

    if "successes" in death_saves:
        successes = death_saves["successes"]
        # Strict type checking: must be int, not float
        if not isinstance(successes, int) or successes < 0 or successes > 3:
            errors.append(
                f"death_saves.successes must be an integer between 0 and 3, got {successes}"
            )

    if "failures" in death_saves:
        failures = death_saves["failures"]
        # Strict type checking: must be int, not float
        if not isinstance(failures, int) or failures < 0 or failures > 3:
            errors.append(
                f"death_saves.failures must be an integer between 0 and 3, got {failures}"
            )

    return errors


def _validate_spells_known(spells_known: list[dict[str, Any]]) -> list[str]:
    """Validate spells_known array structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(spells_known, list):
        errors.append("spells_known must be an array")
        return errors

    for idx, spell in enumerate(spells_known):
        if not isinstance(spell, dict):
            errors.append(f"spells_known[{idx}] must be a dict")
            continue

        # Required: name field
        if (
            "name" not in spell
            or not isinstance(spell["name"], str)
            or not spell["name"].strip()
        ):
            errors.append(f"spells_known[{idx}] missing required 'name' field")

        # Required: level field
        if "level" in spell:
            level = spell["level"]
            # Strict type checking: must be int, not float
            if not isinstance(level, int) or level < 0 or level > 9:
                errors.append(
                    f"spells_known[{idx}].level must be an integer between 0 and 9, got {level}"
                )
        else:
            errors.append(f"spells_known[{idx}] missing required 'level' field")

    return errors


def _validate_status_conditions(status_conditions: Any) -> list[str]:
    """Validate status_conditions array structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(status_conditions, list):
        return ["status_conditions must be an array"]

    for idx, condition in enumerate(status_conditions):
        if not isinstance(condition, str):
            errors.append(f"status_conditions[{idx}] must be a string")
            continue

        # Warn on unknown conditions (but don't fail - allow custom conditions)
        condition_normalized = condition.strip()
        if condition_normalized and condition_normalized not in VALID_STATUS_CONDITIONS:
            # Log warning but don't add to errors (permissive validation)
            pass  # Could add warning here if needed

    return errors


def _validate_active_effects(active_effects: Any) -> list[str]:
    """Validate active_effects array structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(active_effects, list):
        return ["active_effects must be an array"]

    for idx, effect in enumerate(active_effects):
        if not isinstance(effect, str):
            errors.append(f"active_effects[{idx}] must be a string")
            continue

        # Basic format validation: should describe effect and mechanical benefit
        if not effect.strip():
            errors.append(f"active_effects[{idx}] cannot be empty")

    return errors


def _validate_combat_stats(combat_stats: dict[str, Any]) -> list[str]:
    """Validate combat_stats structure. Returns list of error messages (empty if valid)."""
    errors = []

    if not isinstance(combat_stats, dict):
        return ["combat_stats must be a dict"]

    if "speed" in combat_stats:
        speed = combat_stats["speed"]
        # Strict type checking: must be int, not float
        if not isinstance(speed, int) or speed < 0:
            errors.append(f"combat_stats.speed must be an integer >= 0, got {speed}")

    if "passive_perception" in combat_stats:
        passive_perception = combat_stats["passive_perception"]
        # Strict type checking: must be int, not float
        if not isinstance(passive_perception, int) or passive_perception < 0:
            errors.append(
                f"combat_stats.passive_perception must be an integer >= 0, got {passive_perception}"
            )

    # initiative is optional and can be any int (no range constraint)

    return errors


def _validate_item(item: dict[str, Any], item_name: str = "item") -> list[str]:
    """Validate item structure (weapon, armor, or general item). Returns list of error messages."""
    errors = []

    if not isinstance(item, dict):
        return [f"{item_name} must be a dict"]

    item_type = item.get("type", "")

    # Warn on unknown/non-empty item types (but don't fail - allow custom types)
    if item_type and item_type not in ("weapon", "armor"):
        errors.append(
            f"{item_name}.type '{item_type}' is not a recognized type (expected 'weapon' or 'armor')"
        )

    # Validate weapon
    if item_type == "weapon":
        if "damage" in item:
            damage = item["damage"]
            if not isinstance(damage, str) or not damage.strip():
                errors.append(
                    f"{item_name}.damage must be a non-empty string (dice notation)"
                )

        if "damage_type" in item:
            damage_type = item["damage_type"]
            if (
                isinstance(damage_type, str)
                and damage_type.lower() not in VALID_DAMAGE_TYPES
            ):
                errors.append(
                    f"{item_name}.damage_type '{damage_type}' must be one of {VALID_DAMAGE_TYPES}"
                )

    # Validate armor
    elif item_type == "armor":
        if "armor_class" in item:
            ac = item["armor_class"]
            # Strict type checking: must be int, not float
            if not isinstance(ac, int) or ac < 1 or ac > 30:
                errors.append(
                    f"{item_name}.armor_class must be an integer between 1 and 30, got {ac}"
                )

        if "armor_type" in item:
            armor_type = item["armor_type"]
            if (
                isinstance(armor_type, str)
                and armor_type.lower() not in VALID_ARMOR_TYPES
            ):
                errors.append(
                    f"{item_name}.armor_type '{armor_type}' must be one of {VALID_ARMOR_TYPES}"
                )

    return errors


def _derive_quality_tier(success: bool, margin: int) -> str:
    """Derive a quality tier from success flag and margin using documented bands."""

    if success:
        if margin >= 15:
            return "Masterful"
        if margin >= 10:
            return "Brilliant"
        if margin >= 5:
            return "Sharp"
        return "Competent"

    failure_margin = abs(margin)
    if failure_margin >= 10:
        return "Confused"
    if failure_margin >= 5:
        return "Muddled"
    return "Incomplete"


def _coerce_bool_optional(value: Any) -> bool | None:
    """Best-effort conversion of arbitrary values to bool, returning None when unclear."""

    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None


def _freeze_duration_hours_from_dc(original_dc: int) -> int:
    """Map a DC value to its freeze duration in hours (game time)."""

    if original_dc >= 21:
        return 24
    if original_dc >= 17:
        return 8
    if original_dc >= 13:
        return 4
    if original_dc >= 9:
        return 2
    if original_dc >= 6:
        return 1
    return 1


def _strip_embedded_planning_json(text: str) -> str:
    """
    Strip embedded planning block JSON from narrative text.

    The LLM sometimes outputs planning block JSON directly in the narrative field.
    This JSON should be stripped because the planning_block is a separate structured field.

    Detects and removes JSON blocks that contain:
    - "thinking" key (GM reasoning)
    - "choices" key (player options)

    Args:
        text: The narrative text that may contain embedded JSON

    Returns:
        The narrative text with embedded planning JSON removed
    """
    if not text or not isinstance(text, str):
        return text

    # Quick check - if no planning block indicators, return as-is
    # Both keys must be present (order-independent check)
    if '"thinking"' not in text or '"choices"' not in text:
        return text

    cleaned = text

    # Try to find and remove embedded planning JSON using recursive brace matching
    # This is more robust than regex for deeply nested JSON
    cleaned, removed = _remove_planning_json_blocks(cleaned)

    # Clean up multiple consecutive newlines that might result from removal
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    if removed and cleaned != text:
        logging_util.info("Stripped embedded planning block JSON from narrative text")

    return cleaned


def _remove_planning_json_blocks(text: str) -> tuple[str, bool]:
    """
    Remove JSON blocks that look like planning blocks (have thinking and choices keys).

    Uses brace matching to handle arbitrarily nested JSON.
    """
    result = []
    i = 0
    text_len = len(text)

    removed = False

    while i < text_len:
        # Look for potential JSON object start
        if text[i] == "{":
            # Try to extract the full JSON object
            json_end = _find_matching_brace(text, i)
            if json_end != -1:
                json_block = text[i : json_end + 1]
                # Check if this looks like a planning block
                if _is_planning_block_json(json_block):
                    # Skip this JSON block (don't add to result)
                    removed = True
                    i = json_end + 1
                    continue

        result.append(text[i])
        i += 1

    return "".join(result), removed


def _find_matching_brace(text: str, start: int) -> int:
    """
    Find the index of the closing brace that matches the opening brace at start.

    Returns -1 if no matching brace is found.
    """
    if start >= len(text) or text[start] != "{":
        return -1

    depth = 0
    in_string = False
    escape_next = False
    i = start

    while i < len(text):
        char = text[i]

        if escape_next:
            escape_next = False
        elif char == "\\":
            escape_next = True
        elif char == '"':
            in_string = not in_string
        elif not in_string:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return i

        i += 1

    return -1  # No matching brace found


def _is_planning_block_json(json_text: str) -> bool:
    """
    Check if a JSON block looks like a planning block structure.

    Planning blocks have "thinking" and "choices" keys.
    """
    if len(json_text) > MAX_PLANNING_JSON_BLOCK_CHARS:
        return False

    # Quick string check first (faster than parsing)
    if '"thinking"' not in json_text or '"choices"' not in json_text:
        return False

    # Verify it's actually valid JSON with these keys
    try:
        parsed = json.loads(json_text)
        if isinstance(parsed, dict):
            has_thinking = "thinking" in parsed
            has_choices = "choices" in parsed
            return has_thinking and has_choices
    except json.JSONDecodeError:
        # If it looks like planning JSON but doesn't parse,
        # still remove it (it's likely malformed planning block)
        # Use a looser check
        return (
            '"thinking"' in json_text
            and '"choices"' in json_text
            and json_text.strip().startswith("{")
            and json_text.strip().endswith("}")
        )

    return False


def strip_mixed_language_characters(text: str) -> str:
    """
    Strip CJK (Chinese/Japanese/Korean) characters from text.

    These can appear due to LLM training data leakage and should be removed
    to maintain narrative consistency in English-language campaigns.

    Args:
        text: Input text that may contain mixed language characters

    Returns:
        Text with CJK characters removed
    """
    if not text:
        return text

    # Check if there are any CJK characters
    if CJK_PATTERN.search(text):
        original_len = len(text)
        cleaned = CJK_PATTERN.sub("", text)
        removed_count = original_len - len(cleaned)
        logging_util.warning(
            f"⚠️ MIXED_LANGUAGE_STRIPPED: Removed {removed_count} CJK characters from narrative. "
            f"This indicates LLM training data leakage."
        )
        # Clean up any double spaces left behind
        cleaned = re.sub(r"  +", " ", cleaned)
        return cleaned.strip()

    return text


class NarrativeResponse:
    """Schema for structured narrative generation response"""

    def __init__(
        self,
        narrative: str,
        entities_mentioned: list[str] | None = None,
        location_confirmed: str = "Unknown",
        turn_summary: str | None = None,
        state_updates: dict[str, Any] | None = None,
        debug_info: dict[str, Any] | None = None,
        god_mode_response: str | None = None,
        directives: dict[str, Any] | None = None,  # God mode: {add: [...], drop: [...]}
        session_header: str | None = None,
        planning_block: dict[str, Any] | None = None,
        dice_rolls: list[str] | None = None,
        dice_audit_events: list[dict[str, Any]] | None = None,
        resources: str | None = None,
        **kwargs: Any,
    ):
        # Core required fields
        self.narrative = self._validate_narrative(narrative)
        self.entities_mentioned = self._validate_entities(entities_mentioned or [])
        self.location_confirmed = location_confirmed or "Unknown"
        self.turn_summary = turn_summary
        self.state_updates = self._validate_state_updates(state_updates)
        self.debug_info = self._validate_debug_info(debug_info)
        self.god_mode_response = god_mode_response
        self.directives = self._validate_directives_field(
            directives or {}
        )  # God mode directives: {add: [...], drop: [...]}

        # New always-visible fields
        self.session_header = self._validate_string_field(
            session_header, "session_header"
        )
        self.planning_block = self._validate_planning_block(planning_block)
        self.dice_rolls = self._validate_list_field(dice_rolls, "dice_rolls")
        self.dice_audit_events = self._validate_dice_audit_events(dice_audit_events)
        self.resources = self._validate_string_field(resources, "resources")
        self.rewards_box = self._validate_rewards_box(kwargs.pop("rewards_box", None))
        self.social_hp_challenge = self._validate_social_hp_challenge(
            kwargs.pop("social_hp_challenge", None)
        )

        # Action Resolution & Backward Compatibility
        # ------------------------------------------
        # We accept both action_resolution (new) and outcome_resolution (legacy).

        action_resolution = kwargs.pop("action_resolution", None)
        outcome_resolution = kwargs.pop("outcome_resolution", None)

        # Track if either field is explicitly provided for normalization logic
        # This ensures get_unified_action_resolution() returns the validated data
        # even when only outcome_resolution (legacy) is provided
        self._action_resolution_provided = (
            action_resolution is not None or outcome_resolution is not None
        )

        # Determine which resolution to use (action_resolution takes precedence)
        if action_resolution is not None:
            resolution = action_resolution
        elif outcome_resolution is not None:
            logging_util.warning(
                "Legacy 'outcome_resolution' field received. Mapping to 'action_resolution'. "
                "Please update prompts to use 'action_resolution'."
            )
            resolution = outcome_resolution
        else:
            # Neither field provided - this will trigger a warning in _validate_action_resolution
            # Per system prompts, action_resolution is MANDATORY for all player actions
            resolution = None

        self.action_resolution = self._validate_action_resolution(resolution)

        # Store outcome_resolution for backward compatibility in to_dict()
        # Always use the validated version (self.action_resolution) to ensure consistency
        # This ensures both fields have the same validated, normalized data structure
        self.outcome_resolution = self.action_resolution

        # Store any extra fields that Gemini might include
        self.extra_fields = kwargs

    def _validate_narrative(self, narrative: str) -> str:
        """Validate narrative content, strip embedded JSON and mixed language characters"""
        if not isinstance(narrative, str):
            raise ValueError("Narrative must be a string")

        # Strip embedded planning block JSON from narrative
        cleaned = _strip_embedded_planning_json(narrative)

        # Strip any mixed language characters (CJK) that may have leaked from LLM training
        cleaned = strip_mixed_language_characters(cleaned)

        return cleaned.strip()

    def _validate_entities(self, entities: list[str]) -> list[str]:
        """Validate and clean entity list"""
        if not isinstance(entities, list):
            raise ValueError("Entities must be a list")

        return [str(entity).strip() for entity in entities if str(entity).strip()]

    def _validate_state_updates(self, state_updates: Any) -> dict[str, Any]:
        """Validate and clean state updates.

        Note: frozen_plans is LLM-enforced via prompts, not Python-validated.
        The LLM tracks freeze state and enforces re-think cooldowns based on
        the rules in think_mode_instruction.md and planning_protocol.md.

        Per roadmap/llm_schema_alignment_gaps.md, this method now validates:
        - combat_state (Priority 1)
        - reputation (Priority 1)
        - relationships (Priority 2)
        - world_time (Priority 2)
        - encounter_state (Priority 2)
        """
        if state_updates is None:
            return {}

        if not isinstance(state_updates, dict):
            logging_util.warning(
                f"Invalid state_updates type: {type(state_updates).__name__}, expected dict. Using empty dict instead."
            )
            return {}

        validated = dict(state_updates)

        # Validate combat_state (Priority 1)
        if "combat_state" in validated:
            combat_state = validated["combat_state"]
            if isinstance(combat_state, dict):
                try:
                    errors = _validate_combat_state(combat_state)
                    if errors:
                        for error in errors:
                            logging_util.warning(f"⚠️ COMBAT_STATE_VALIDATION: {error}")
                except Exception as e:
                    logging_util.error(f"⚠️ COMBAT_STATE_VALIDATION: Validation failed with exception: {e}")

        # Validate reputation (Priority 1)
        if "custom_campaign_state" in validated:
            custom_state = validated["custom_campaign_state"]
            if isinstance(custom_state, dict) and "reputation" in custom_state:
                reputation = custom_state["reputation"]
                if isinstance(reputation, dict):
                    try:
                        errors = _validate_reputation(reputation)
                        if errors:
                            for error in errors:
                                logging_util.warning(f"⚠️ REPUTATION_VALIDATION: {error}")
                    except Exception as e:
                        logging_util.error(f"⚠️ REPUTATION_VALIDATION: Validation failed with exception: {e}")

        # Validate relationships (Priority 2)
        if "npc_data" in validated:
            npc_data = validated["npc_data"]
            if isinstance(npc_data, dict):
                for npc_name, npc_info in npc_data.items():
                    if isinstance(npc_info, dict) and "relationships" in npc_info:
                        relationships = npc_info["relationships"]
                        if isinstance(relationships, dict):
                            for rel_name, relationship in relationships.items():
                                if isinstance(relationship, dict):
                                    try:
                                        errors = _validate_relationship(relationship)
                                        if errors:
                                            for error in errors:
                                                logging_util.warning(
                                                    f"⚠️ RELATIONSHIP_VALIDATION ({npc_name}.{rel_name}): {error}"
                                                )
                                    except Exception as e:
                                        logging_util.error(f"⚠️ RELATIONSHIP_VALIDATION ({npc_name}.{rel_name}): Validation failed with exception: {e}")

        # Validate world_time (Priority 2)
        if "world_data" in validated:
            world_data = validated["world_data"]
            if isinstance(world_data, dict) and "world_time" in world_data:
                world_time = world_data["world_time"]
                if isinstance(world_time, dict):
                    try:
                        errors = _validate_world_time(world_time)
                        if errors:
                            for error in errors:
                                logging_util.warning(f"⚠️ WORLD_TIME_VALIDATION: {error}")
                    except Exception as e:
                        logging_util.error(f"⚠️ WORLD_TIME_VALIDATION: Validation failed with exception: {e}")

        # Validate encounter_state (Priority 2)
        if "encounter_state" in validated:
            encounter_state = validated["encounter_state"]
            if isinstance(encounter_state, dict):
                try:
                    errors = _validate_encounter_state(encounter_state)
                    if errors:
                        for error in errors:
                            logging_util.warning(f"⚠️ ENCOUNTER_STATE_VALIDATION: {error}")
                except Exception as e:
                    logging_util.error(f"⚠️ ENCOUNTER_STATE_VALIDATION: Validation failed with exception: {e}")

        # Validate frozen_plans (Priority 3)
        if "frozen_plans" in validated:
            frozen_plans = validated["frozen_plans"]
            if isinstance(frozen_plans, dict):
                try:
                    errors = _validate_frozen_plans(frozen_plans)
                    if errors:
                        for error in errors:
                            logging_util.warning(f"⚠️ FROZEN_PLANS_VALIDATION: {error}")
                except Exception as e:
                    logging_util.error(f"⚠️ FROZEN_PLANS_VALIDATION: Validation failed with exception: {e}")

        # Validate equipment slots (Priority 3)
        if "player_character_data" in validated:
            player_data = validated["player_character_data"]
            if isinstance(player_data, dict) and "equipment" in player_data:
                equipment = player_data["equipment"]
                if isinstance(equipment, dict):
                    try:
                        errors = _validate_equipment_slots(equipment)
                        if errors:
                            for error in errors:
                                logging_util.warning(
                                    f"⚠️ EQUIPMENT_SLOT_VALIDATION: {error}"
                                )
                    except Exception as e:
                        logging_util.error(f"⚠️ EQUIPMENT_SLOT_VALIDATION: Validation failed with exception: {e}")

        # Validate resources (Priority 1)
        if "player_character_data" in validated:
            player_data = validated["player_character_data"]
            if isinstance(player_data, dict):
                # Validate resources structure (gold, hit_dice, consumables)
                if "resources" in player_data:
                    resources = player_data["resources"]
                    if isinstance(resources, dict):
                        # Validate resources structure (gold, hit_dice)
                        try:
                            errors = _validate_resources(resources)
                            if errors:
                                for error in errors:
                                    logging_util.warning(f"⚠️ RESOURCES_VALIDATION: {error}")
                        except Exception as e:
                            logging_util.error(f"⚠️ RESOURCES_VALIDATION: Validation failed with exception: {e}")

                        # Validate spell_slots separately (for clearer error messages)
                        if "spell_slots" in resources:
                            spell_slots = resources["spell_slots"]
                            if isinstance(spell_slots, dict):
                                try:
                                    spell_slot_errors = _validate_spell_slots(spell_slots)
                                    if spell_slot_errors:
                                        for error in spell_slot_errors:
                                            logging_util.warning(
                                                f"⚠️ SPELL_SLOTS_VALIDATION: {error}"
                                            )
                                except Exception as e:
                                    logging_util.error(f"⚠️ SPELL_SLOTS_VALIDATION: Validation failed with exception: {e}")

                        # Validate class_features separately (for clearer error messages)
                        if "class_features" in resources:
                            class_features = resources["class_features"]
                            if isinstance(class_features, dict):
                                try:
                                    class_feature_errors = _validate_class_features(
                                        class_features
                                    )
                                    if class_feature_errors:
                                        for error in class_feature_errors:
                                            logging_util.warning(
                                                f"⚠️ CLASS_FEATURES_VALIDATION: {error}"
                                            )
                                except Exception as e:
                                    logging_util.error(f"⚠️ CLASS_FEATURES_VALIDATION: Validation failed with exception: {e}")

                # Validate attributes (Priority 2)
                if "base_attributes" in player_data or "attributes" in player_data:
                    try:
                        attribute_errors = _validate_attributes(player_data)
                        if attribute_errors:
                            for error in attribute_errors:
                                logging_util.warning(f"⚠️ ATTRIBUTES_VALIDATION: {error}")
                    except Exception as e:
                        logging_util.error(f"⚠️ ATTRIBUTES_VALIDATION: Validation failed with exception: {e}")

                # Validate experience (Priority 2)
                if "experience" in player_data:
                    experience = player_data["experience"]
                    if isinstance(experience, dict):
                        try:
                            experience_errors = _validate_experience(experience)
                            if experience_errors:
                                for error in experience_errors:
                                    logging_util.warning(
                                        f"⚠️ EXPERIENCE_VALIDATION: {error}"
                                    )
                        except Exception as e:
                            logging_util.error(f"⚠️ EXPERIENCE_VALIDATION: Validation failed with exception: {e}")

                # Validate death_saves (Priority 2)
                if "death_saves" in player_data:
                    death_saves = player_data["death_saves"]
                    if isinstance(death_saves, dict):
                        try:
                            death_saves_errors = _validate_death_saves(death_saves)
                            if death_saves_errors:
                                for error in death_saves_errors:
                                    logging_util.warning(
                                        f"⚠️ DEATH_SAVES_VALIDATION: {error}"
                                    )
                        except Exception as e:
                            logging_util.error(f"⚠️ DEATH_SAVES_VALIDATION: Validation failed with exception: {e}")

                # Validate spells_known (Priority 2)
                if "spells_known" in player_data:
                    spells_known = player_data["spells_known"]
                    if isinstance(spells_known, list):
                        try:
                            spells_known_errors = _validate_spells_known(spells_known)
                            if spells_known_errors:
                                for error in spells_known_errors:
                                    logging_util.warning(
                                        f"⚠️ SPELLS_KNOWN_VALIDATION: {error}"
                                    )
                        except Exception as e:
                            logging_util.error(f"⚠️ SPELLS_KNOWN_VALIDATION: Validation failed with exception: {e}")

                # Validate status_conditions (Priority 3)
                if "status_conditions" in player_data:
                    status_conditions = player_data["status_conditions"]
                    try:
                        status_conditions_errors = _validate_status_conditions(
                            status_conditions
                        )
                        if status_conditions_errors:
                            for error in status_conditions_errors:
                                logging_util.warning(
                                    f"⚠️ STATUS_CONDITIONS_VALIDATION: {error}"
                                )
                    except Exception as e:
                        logging_util.error(f"⚠️ STATUS_CONDITIONS_VALIDATION: Validation failed with exception: {e}")

                # Validate active_effects (Priority 3)
                if "active_effects" in player_data:
                    active_effects = player_data["active_effects"]
                    try:
                        active_effects_errors = _validate_active_effects(active_effects)
                        if active_effects_errors:
                            for error in active_effects_errors:
                                logging_util.warning(
                                    f"⚠️ ACTIVE_EFFECTS_VALIDATION: {error}"
                                )
                    except Exception as e:
                        logging_util.error(f"⚠️ ACTIVE_EFFECTS_VALIDATION: Validation failed with exception: {e}")

                # Validate combat_stats (Priority 3)
                if "combat_stats" in player_data:
                    combat_stats = player_data["combat_stats"]
                    if isinstance(combat_stats, dict):
                        try:
                            combat_stats_errors = _validate_combat_stats(combat_stats)
                            if combat_stats_errors:
                                for error in combat_stats_errors:
                                    logging_util.warning(
                                        f"⚠️ COMBAT_STATS_VALIDATION: {error}"
                                    )
                        except Exception as e:
                            logging_util.error(f"⚠️ COMBAT_STATS_VALIDATION: Validation failed with exception: {e}")

                # Validate equipment items (Priority 3)
                if "equipment" in player_data:
                    equipment = player_data["equipment"]
                    if isinstance(equipment, dict):
                        # Validate each item in equipment slots
                        for slot_name, item in equipment.items():
                            if item is not None and isinstance(item, dict):
                                try:
                                    item_errors = _validate_item(
                                        item, f"equipment.{slot_name}"
                                    )
                                    if item_errors:
                                        for error in item_errors:
                                            logging_util.warning(
                                                f"⚠️ ITEM_VALIDATION: {error}"
                                            )
                                except Exception as e:
                                    logging_util.error(f"⚠️ ITEM_VALIDATION (equipment.{slot_name}): Validation failed with exception: {e}")
                            elif isinstance(item, list):
                                # Handle array slots (weapons, backpack)
                                for idx, sub_item in enumerate(item):
                                    if isinstance(sub_item, dict):
                                        try:
                                            item_errors = _validate_item(
                                                sub_item, f"equipment.{slot_name}[{idx}]"
                                            )
                                            if item_errors:
                                                for error in item_errors:
                                                    logging_util.warning(
                                                        f"⚠️ ITEM_VALIDATION: {error}"
                                                    )
                                        except Exception as e:
                                            logging_util.error(f"⚠️ ITEM_VALIDATION (equipment.{slot_name}[{idx}]): Validation failed with exception: {e}")

        # Validate arc_milestones (Priority 4)
        if "custom_campaign_state" in validated:
            custom_state = validated["custom_campaign_state"]
            if isinstance(custom_state, dict) and "arc_milestones" in custom_state:
                arc_milestones = custom_state["arc_milestones"]
                if isinstance(arc_milestones, dict):
                    try:
                        errors = _validate_arc_milestones(arc_milestones)
                        if errors:
                            for error in errors:
                                logging_util.warning(
                                    f"⚠️ ARC_MILESTONES_VALIDATION: {error}"
                                )
                    except Exception as e:
                        logging_util.error(f"⚠️ ARC_MILESTONES_VALIDATION: Validation failed with exception: {e}")

        # Validate time_pressure_warnings (Priority 4)
        if "time_pressure_warnings" in validated:
            time_pressure_warnings = validated["time_pressure_warnings"]
            if isinstance(time_pressure_warnings, dict):
                try:
                    errors = _validate_time_pressure_warnings(time_pressure_warnings)
                    if errors:
                        for error in errors:
                            logging_util.warning(f"⚠️ TIME_PRESSURE_VALIDATION: {error}")
                except Exception as e:
                    logging_util.error(f"⚠️ TIME_PRESSURE_VALIDATION: Validation failed with exception: {e}")

        return validated

    def _validate_debug_info(self, debug_info: Any) -> dict[str, Any]:
        """Validate and clean debug info"""
        if debug_info is None:
            return {}

        if not isinstance(debug_info, dict):
            logging_util.warning(
                f"Invalid debug_info type: {type(debug_info).__name__}, expected dict. Using empty dict instead."
            )
            return {}

        return debug_info

    def _validate_string_field(self, value: Any, field_name: str) -> str:
        """Validate a string field with null/type checking"""
        if value is None:
            return ""

        if not isinstance(value, str):
            logging_util.warning(
                f"Invalid {field_name} type: {type(value).__name__}, expected str. Converting to string."
            )
            try:
                return str(value)
            except Exception as e:
                logging_util.error(f"Failed to convert {field_name} to string: {e}")
                return ""

        return value

    def _validate_list_field(self, value: Any, field_name: str) -> list[str]:
        """Validate a list field with null/type checking"""
        if value is None:
            return []

        if not isinstance(value, list):
            logging_util.warning(
                f"Invalid {field_name} type: {type(value).__name__}, expected list. Using empty list."
            )
            return []

        # Convert all items to strings
        validated_list = []
        for item in value:
            if item is not None:
                try:
                    # Handle dice_rolls dict format from Think Mode
                    if isinstance(item, dict) and field_name == "dice_rolls":
                        formatted = self._format_dice_roll_object(item)
                        validated_list.append(formatted)
                    else:
                        validated_list.append(str(item))
                except Exception as e:
                    logging_util.warning(
                        f"Failed to convert {field_name} item to string: {e}"
                    )

        return validated_list

    def _format_dice_roll_object(self, roll: dict) -> str:
        """Format a dice roll object into a human-readable string.

        Handles Think Mode dice roll format:
        {
            "type": "Intelligence Check (Planning)",
            "roll": "1d20+2",
            "result": 14,
            "dc": null,
            "outcome": "Good - Sharp analysis"
        }

        Returns formatted string like:
        "Intelligence Check (Planning): 1d20+2 = 14 - Good - Sharp analysis"
        """
        roll_type = roll.get("type", "Roll")
        roll_dice = roll.get("roll", "")
        roll_result = roll.get("result", "?")
        roll_dc = roll.get("dc")
        roll_outcome = roll.get("outcome", "")

        # Build formatted string
        parts = [f"{roll_type}:"]

        if roll_dice:
            parts.append(f"{roll_dice} =")

        parts.append(str(roll_result))

        if roll_dc is not None:
            parts.append(f"vs DC {roll_dc}")

        if roll_outcome:
            parts.append(f"- {roll_outcome}")

        return " ".join(parts)

    def _validate_rewards_box(self, rewards_box: Any) -> dict[str, Any]:
        """Validate rewards_box structured field."""
        if rewards_box is None:
            return {}

        if not isinstance(rewards_box, dict):
            logging_util.warning(
                f"Invalid rewards_box type: {type(rewards_box).__name__}, expected dict. Using empty dict."
            )
            return {}

        def _coerce_number(value: Any, default: float = 0.0) -> float:
            if isinstance(value, (int, float)):
                return float(value)
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        validated: dict[str, Any] = {
            "source": str(rewards_box.get("source", "")).strip(),
            "xp_gained": _coerce_number(rewards_box.get("xp_gained", 0)),
            "current_xp": _coerce_number(rewards_box.get("current_xp", 0)),
            "next_level_xp": _coerce_number(rewards_box.get("next_level_xp", 0)),
            "progress_percent": _coerce_number(rewards_box.get("progress_percent", 0)),
            "level_up_available": _coerce_bool(
                rewards_box.get("level_up_available", False),
                context="rewards_box.level_up_available",
            ),
            "gold": _coerce_number(rewards_box.get("gold", 0)),
        }

        loot = rewards_box.get("loot", [])
        if not isinstance(loot, list):
            loot = [str(loot)] if loot is not None else []
        validated["loot"] = [str(item).strip() for item in loot if str(item).strip()]

        return validated

    def _validate_social_hp_challenge(self, social_hp_challenge: Any) -> dict[str, Any]:
        """Validate social_hp_challenge structured field for Social HP tracking."""
        if social_hp_challenge is None:
            return {}

        if not isinstance(social_hp_challenge, dict):
            logging_util.warning(
                f"Invalid social_hp_challenge type: {type(social_hp_challenge).__name__}, "
                "expected dict. Using empty dict."
            )
            return {}

        def _coerce_int(value: Any, default: int = 0) -> int:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        def _coerce_str(value: Any, default: str = "") -> str:
            if value is None:
                return default
            return str(value).strip()

        # Validate and coerce fields
        validated: dict[str, Any] = {}

        # String fields
        validated["npc_id"] = _coerce_str(social_hp_challenge.get("npc_id", ""))
        validated["npc_name"] = _coerce_str(social_hp_challenge.get("npc_name", ""))
        validated["npc_tier"] = _coerce_str(social_hp_challenge.get("npc_tier", ""))
        validated["objective"] = _coerce_str(social_hp_challenge.get("objective", ""))

        request_severity = _coerce_str(
            social_hp_challenge.get("request_severity", "information")
        ).lower()
        if request_severity not in VALID_SOCIAL_HP_REQUEST_SEVERITY:
            logging_util.warning(
                f"Invalid social_hp_challenge request_severity '{request_severity}', defaulting to information"
            )
            request_severity = "information"
        validated["request_severity"] = request_severity

        validated["resistance_shown"] = _coerce_str(
            social_hp_challenge.get("resistance_shown", "")
        )

        # Integer fields - HP tracking
        validated["social_hp"] = _coerce_int(social_hp_challenge.get("social_hp", 0))
        validated["social_hp_max"] = _coerce_int(
            social_hp_challenge.get("social_hp_max", 0)
        )
        validated["social_hp_damage"] = _coerce_int(
            social_hp_challenge.get("social_hp_damage", 0)
        )

        # Integer fields - Progress tracking
        validated["successes"] = _coerce_int(social_hp_challenge.get("successes", 0))
        validated["successes_needed"] = _coerce_int(
            social_hp_challenge.get("successes_needed", 5)
        )

        # Integer fields - Roll tracking
        validated["roll_result"] = _coerce_int(
            social_hp_challenge.get("roll_result", 0)
        )
        validated["roll_dc"] = _coerce_int(social_hp_challenge.get("roll_dc", 0))

        # Status field with validation
        status = _coerce_str(social_hp_challenge.get("status", "RESISTING")).upper()
        if status not in VALID_SOCIAL_HP_STATUS:
            logging_util.warning(
                f"Invalid social_hp_challenge status '{status}', defaulting to RESISTING"
            )
            status = "RESISTING"
        validated["status"] = status

        # Skill field with validation
        skill_used = _coerce_str(social_hp_challenge.get("skill_used", "Persuasion"))
        # Normalize case for comparison
        skill_normalized = skill_used.title()
        if skill_normalized not in VALID_SOCIAL_SKILLS:
            logging_util.warning(
                f"Invalid social_hp_challenge skill_used '{skill_used}', "
                "defaulting to Persuasion"
            )
            skill_normalized = "Persuasion"
        validated["skill_used"] = skill_normalized

        return validated

    def _validate_action_resolution(self, action_resolution: Any) -> dict[str, Any]:
        """Validate action_resolution structured field for audit trail.
        
        This field is MANDATORY for all player actions per system prompts.
        
        Hybrid enforcement:
        - Current (transition period): Warning when missing, returns {} fallback
        - Future (strict mode): Set ENFORCE_ACTION_RESOLUTION_STRICT=true to raise ValueError
        
        This allows gradual migration: warnings now, strict enforcement later.
        """
        if action_resolution is None:
            # Check for strict enforcement mode (future: enable after transition period)
            strict_mode = os.getenv("ENFORCE_ACTION_RESOLUTION_STRICT", "false").lower() == "true"

            if strict_mode:
                raise ValueError(
                    "action_resolution is REQUIRED for all player actions per system prompts. "
                    "LLM must include action_resolution with reinterpreted flag and mechanics. "
                    "Missing action_resolution violates audit trail requirements."
                )
            # Transition period: Warning only, allow {} fallback
            logging_util.warning(
                "action_resolution is missing from LLM response. "
                "This field is REQUIRED for all player actions per system prompts. "
                "LLM should include action_resolution with reinterpreted flag and mechanics. "
                "Using empty dict as fallback. "
                "Future: Set ENFORCE_ACTION_RESOLUTION_STRICT=true for strict enforcement."
            )
            return {}

        if not isinstance(action_resolution, dict):
            logging_util.warning(
                f"Invalid action_resolution type: {type(action_resolution).__name__}, "
                "expected dict. Using empty dict."
            )
            return {}

        # Use deep copy to avoid mutating nested structures (e.g., mechanics dict)
        # Schema is defined in game_state_instruction.md
        # Required fields: trigger, player_intent, original_input, resolution_type, mechanics, audit_flags
        validated = copy.deepcopy(action_resolution)

        # Ensure reinterpreted field defaults to False if not provided
        if "reinterpreted" not in validated:
            validated["reinterpreted"] = False

        # Validate required fields exist (warn but don't fail - downstream code may handle gracefully)
        required_fields = [
            "trigger",
            "player_intent",
            "original_input",
            "resolution_type",
            "mechanics",
            "audit_flags",
        ]
        missing_fields = [field for field in required_fields if field not in validated]
        if missing_fields:
            logging_util.warning(
                f"action_resolution missing required fields: {missing_fields}. "
                "Schema defined in game_state_instruction.md"
            )
        # Ensure audit_flags is a list (coerce non-list values, but preserve None/empty as empty list)
        if "audit_flags" not in validated or validated["audit_flags"] is None:
            validated["audit_flags"] = []
        elif not isinstance(validated["audit_flags"], list):
            # Coerce single values to list, but filter out falsy non-None values (0, "", False)
            if validated["audit_flags"]:
                validated["audit_flags"] = [validated["audit_flags"]]
            else:
                validated["audit_flags"] = []
        # Validate mechanics is a dict if present
        if "mechanics" in validated and validated["mechanics"] is not None:
            if not isinstance(validated["mechanics"], dict):
                logging_util.warning(
                    f"action_resolution.mechanics must be a dict, got {type(validated['mechanics']).__name__}"
                )
                validated["mechanics"] = {}
            elif "outcome" not in validated["mechanics"]:
                logging_util.warning(
                    "action_resolution.mechanics missing required 'outcome' field"
                )

        return validated

    def _validate_directives_field(self, directives: dict[str, Any]) -> dict[str, Any]:
        """Validate directives field structure."""
        if not isinstance(directives, dict):
            logging_util.warning(
                f"Invalid directives type: {type(directives).__name__}, expected dict. Using empty dict."
            )
            return {}

        validated = {}
        errors = _validate_directives(directives)
        if errors:
            for error in errors:
                logging_util.warning(f"⚠️ DIRECTIVES_VALIDATION: {error}")

        # Coerce add/drop to lists if they exist but aren't lists
        # Filter out None values to avoid converting None to string "None"
        if "add" in directives:
            if isinstance(directives["add"], list):
                validated["add"] = [
                    str(item) for item in directives["add"] if item is not None
                ]
            else:
                validated["add"] = [str(directives["add"])] if directives["add"] else []
        else:
            validated["add"] = []

        if "drop" in directives:
            if isinstance(directives["drop"], list):
                validated["drop"] = [
                    str(item) for item in directives["drop"] if item is not None
                ]
            else:
                validated["drop"] = (
                    [str(directives["drop"])] if directives["drop"] else []
                )
        else:
            validated["drop"] = []

        return validated


    def _validate_dice_audit_events(self, value: Any) -> list[dict[str, Any]]:
        """Validate dice_audit_events as a list of dicts.

        Keep permissive: events may include provider-specific evidence fields,
        and strict validation should not block gameplay.
        """
        if value is None:
            return []

        if not isinstance(value, list):
            logging_util.warning(
                f"Invalid dice_audit_events type: {type(value).__name__}, expected list. Using empty list."
            )
            return []

        events: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                events.append(item)
                continue
            logging_util.warning(
                f"Invalid dice_audit_events item type: {type(item).__name__}, expected dict. Skipping."
            )

        return events

    def _validate_planning_block(self, planning_block: Any) -> dict[str, Any]:
        """Validate planning block content - JSON ONLY format"""
        if planning_block is None:
            return {}

        # JSON format - ONLY supported format
        if isinstance(planning_block, dict):
            return self._validate_planning_block_json(planning_block)

        # String format - NO LONGER SUPPORTED
        if isinstance(planning_block, str):
            logging_util.error(
                f"❌ STRING PLANNING BLOCKS NO LONGER SUPPORTED: String planning blocks are deprecated. Only JSON format is allowed. Received: {planning_block[:100]}..."
            )
            return {}

        # Invalid type - reject
        logging_util.error(
            f"❌ INVALID PLANNING BLOCK TYPE: Expected dict (JSON object), got {type(planning_block).__name__}. Planning blocks must be JSON objects with 'thinking' and 'choices' fields."
        )
        return {}

    def _validate_planning_block_json(
        self, planning_block: dict[str, Any]
    ) -> dict[str, Any]:  # noqa: PLR0912
        """Validate JSON-format planning block structure"""
        validated: dict[str, Any] = {}

        # Validate thinking field
        thinking = planning_block.get("thinking", "")
        if not isinstance(thinking, str):
            thinking = str(thinking) if thinking is not None else ""
        validated["thinking"] = thinking

        # Validate optional context field
        context = planning_block.get("context", "")
        if not isinstance(context, str):
            context = str(context) if context is not None else ""
        validated["context"] = context

        # Validate plan_quality object (Think Mode only)
        plan_quality = planning_block.get("plan_quality")
        if plan_quality is not None and isinstance(plan_quality, dict):
            validated_pq: dict[str, Any] = {}

            # String fields
            for field in [
                "stat_used",
                "modifier",
                "dc_category",
                "dc_reasoning",
                "effect",
            ]:
                val = plan_quality.get(field, "")
                validated_pq[field] = str(val) if val is not None else ""

            # Integer fields
            for field in ["stat_value", "roll_result", "dc", "margin"]:
                val = plan_quality.get(field)
                if isinstance(val, int):
                    validated_pq[field] = val
                elif val is not None:
                    try:
                        validated_pq[field] = int(val)
                    except (ValueError, TypeError):
                        validated_pq[field] = 0
                else:
                    validated_pq[field] = 0

            expected_margin = validated_pq.get("roll_result", 0) - validated_pq.get(
                "dc", 0
            )
            actual_margin = validated_pq.get("margin", 0)
            if actual_margin != expected_margin:
                logging_util.warning(
                    f"plan_quality margin inconsistency: margin={actual_margin} but roll_result-dc={expected_margin}"
                )
                validated_pq["margin"] = expected_margin

            # Boolean field
            provided_success = _coerce_bool_optional(plan_quality.get("success"))
            derived_success = validated_pq.get("roll_result", 0) >= validated_pq.get(
                "dc", 0
            )
            if provided_success is not None:
                if provided_success != derived_success:
                    logging_util.warning(
                        f"plan_quality success inconsistency: success={provided_success} but "
                        f"roll_result({validated_pq.get('roll_result', 0)}) >= dc({validated_pq.get('dc', 0)}) is {derived_success}"
                    )
            else:
                logging_util.warning(
                    "plan_quality.success missing or invalid; deriving success from roll_result vs dc"
                )
            validated_pq["success"] = derived_success

            derived_quality_tier = _derive_quality_tier(
                validated_pq["success"], validated_pq.get("margin", 0)
            )
            quality_tier = plan_quality.get("quality_tier", "")
            if quality_tier in VALID_QUALITY_TIERS:
                if quality_tier != derived_quality_tier:
                    logging_util.warning(
                        "plan_quality quality_tier '%s' inconsistent with margin %s (expected '%s')",
                        quality_tier,
                        validated_pq.get("margin", 0),
                        derived_quality_tier,
                    )
                    validated_pq["quality_tier"] = derived_quality_tier
                else:
                    validated_pq["quality_tier"] = quality_tier
            else:
                validated_pq["quality_tier"] = derived_quality_tier
                if quality_tier:
                    logging_util.warning(
                        f"Invalid quality_tier '{quality_tier}', defaulting to '{derived_quality_tier}'"
                    )

            validated["plan_quality"] = validated_pq

        # Validate choices object
        choices = planning_block.get("choices", {})
        if not isinstance(choices, dict):
            logging_util.warning("Planning block choices must be a dict object")
            choices = {}

        validated_choices: dict[str, Any] = {}
        for choice_key, choice_data in choices.items():
            # Validate choice key format (snake_case, allowing god:/think: prefixes)
            if not re.match(r"^(god:|think:)?[a-zA-Z_][a-zA-Z0-9_]*$", choice_key):
                logging_util.warning(
                    f"Choice key '{choice_key}' is not a valid identifier, skipping"
                )
                continue

            # Validate choice data structure
            if not isinstance(choice_data, dict):
                logging_util.warning(
                    f"Choice '{choice_key}' data must be a dict, skipping"
                )
                continue

            validated_choice: dict[str, Any] = {}

            # Required: text field
            text = choice_data.get("text", "")
            if not isinstance(text, str):
                text = str(text) if text is not None else ""
            validated_choice["text"] = text

            # Required: description field
            description = choice_data.get("description", "")
            if not isinstance(description, str):
                description = str(description) if description is not None else ""
            validated_choice["description"] = description

            # Optional: risk_level field (validate against VALID_RISK_LEVELS)
            risk_level = choice_data.get("risk_level", "low")
            if risk_level not in VALID_RISK_LEVELS:
                risk_level = "low"
            validated_choice["risk_level"] = risk_level

            # Optional: analysis field (for deep think blocks)
            if "analysis" in choice_data:
                analysis = choice_data["analysis"]
                if isinstance(analysis, dict):
                    validated_choice["analysis"] = analysis

            # Optional: pros field (list of advantages)
            if "pros" in choice_data:
                pros = choice_data["pros"]
                if isinstance(pros, list):
                    validated_pros = []
                    for item in pros:
                        if isinstance(item, (str, int, float, bool)):
                            validated_pros.append(
                                item if isinstance(item, str) else str(item)
                            )
                        else:
                            logging_util.warning(
                                f"Skipping non-primitive pros item of type {type(item).__name__} "
                                f"for choice '{choice_key}'"
                            )
                    validated_choice["pros"] = validated_pros

            # Optional: cons field (list of disadvantages)
            if "cons" in choice_data:
                cons = choice_data["cons"]
                if isinstance(cons, list):
                    validated_cons = []
                    for item in cons:
                        if isinstance(item, (str, int, float, bool)):
                            validated_cons.append(
                                item if isinstance(item, str) else str(item)
                            )
                        else:
                            logging_util.warning(
                                f"Skipping non-primitive cons item of type {type(item).__name__} "
                                f"for choice '{choice_key}'"
                            )
                    validated_choice["cons"] = validated_cons

            # Optional: confidence field (high/medium/low)
            if "confidence" in choice_data:
                confidence = choice_data["confidence"]
                if (
                    isinstance(confidence, str)
                    and confidence in VALID_CONFIDENCE_LEVELS
                ):
                    validated_choice["confidence"] = confidence
                else:
                    logging_util.warning(
                        f"Choice '{choice_key}' has invalid confidence '{confidence}', "
                        "defaulting to 'medium'"
                    )
                    validated_choice["confidence"] = "medium"

            # Optional: switch_to_story_mode field (boolean)
            if "switch_to_story_mode" in choice_data:
                switch_value = choice_data["switch_to_story_mode"]
                validated_choice["switch_to_story_mode"] = _coerce_bool(
                    switch_value,
                    context=f"Choice '{choice_key}' switch_to_story_mode",
                )

            # Only add choice if it has both text and description
            if validated_choice["text"] and validated_choice["description"]:
                validated_choices[choice_key] = validated_choice
            else:
                logging_util.warning(
                    f"Choice '{choice_key}' missing required text or description, skipping"
                )

        validated["choices"] = validated_choices

        # Security check - sanitize any HTML/script content
        return self._sanitize_planning_block_content(validated)

    def _sanitize_planning_block_content(
        self, planning_block: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate planning block content - remove dangerous scripts but preserve normal text"""

        def sanitize_string(value: Any) -> str:
            """Remove dangerous script tags but preserve normal apostrophes and quotes"""
            if not isinstance(value, str):
                return str(value)

            # Only remove actual script tags and dangerous HTML
            # Don't escape normal apostrophes and quotes since frontend handles display
            dangerous_patterns = [
                r"<script[^>]*>.*?</script>",
                r"<iframe[^>]*>.*?</iframe>",
                r"<img[^>]*>",  # Remove all img tags (can have malicious attributes)
                r"javascript:",
                r"on\w+\s*=.*?[\s>]",  # event handlers like onclick= onerror=
            ]

            cleaned = value
            for pattern in dangerous_patterns:
                cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

            return cleaned

        sanitized: dict[str, Any] = {}

        # Sanitize thinking
        sanitized["thinking"] = sanitize_string(planning_block.get("thinking", ""))

        # Sanitize context
        if "context" in planning_block:
            sanitized["context"] = sanitize_string(planning_block["context"])

        # Preserve plan_quality but sanitize string subfields
        if "plan_quality" in planning_block and isinstance(
            planning_block.get("plan_quality"), dict
        ):
            sanitized_pq: dict[str, Any] = {}
            for key, value in planning_block["plan_quality"].items():
                if isinstance(value, str):
                    sanitized_pq[key] = sanitize_string(value)
                else:
                    sanitized_pq[key] = value
            sanitized["plan_quality"] = sanitized_pq

        # Sanitize choices
        sanitized_choices: dict[str, Any] = {}
        for choice_key, choice_data in planning_block.get("choices", {}).items():
            sanitized_choice: dict[str, Any] = {}
            sanitized_choice["text"] = sanitize_string(choice_data.get("text", ""))
            sanitized_choice["description"] = sanitize_string(
                choice_data.get("description", "")
            )
            sanitized_choice["risk_level"] = choice_data.get("risk_level", "low")

            # Keep analysis if present (but sanitize strings within it)
            if "analysis" in choice_data:
                analysis = choice_data["analysis"]
                if isinstance(analysis, dict):
                    sanitized_analysis: dict[str, Any] = {}
                    for key, value in analysis.items():
                        if isinstance(value, str):
                            sanitized_analysis[key] = sanitize_string(value)
                        elif isinstance(value, list):
                            sanitized_analysis[key] = [
                                sanitize_string(item) if isinstance(item, str) else item
                                for item in value
                            ]
                        else:
                            sanitized_analysis[key] = value
                    sanitized_choice["analysis"] = sanitized_analysis

            # Keep pros if present (sanitize each string in list)
            if "pros" in choice_data:
                pros = choice_data["pros"]
                if isinstance(pros, list):
                    sanitized_choice["pros"] = [
                        sanitize_string(item) if isinstance(item, str) else str(item)
                        for item in pros
                    ]

            # Keep cons if present (sanitize each string in list)
            if "cons" in choice_data:
                cons = choice_data["cons"]
                if isinstance(cons, list):
                    sanitized_choice["cons"] = [
                        sanitize_string(item) if isinstance(item, str) else str(item)
                        for item in cons
                    ]

            # Keep confidence if present (already validated), sanitize defensively
            if "confidence" in choice_data:
                sanitized_choice["confidence"] = sanitize_string(
                    choice_data["confidence"]
                )

            # Keep switch_to_story_mode if present (boolean, no sanitization needed)
            if "switch_to_story_mode" in choice_data:
                sanitized_choice["switch_to_story_mode"] = _coerce_bool(
                    choice_data["switch_to_story_mode"],
                    context=f"Sanitizing choice '{choice_key}' switch_to_story_mode",
                )

            sanitized_choices[choice_key] = sanitized_choice

        sanitized["choices"] = sanitized_choices

        return sanitized

    def get_unified_action_resolution(self) -> dict[str, Any]:
        """Get action resolution, normalizing from legacy if needed.
        
        Returns action_resolution if explicitly provided (including empty dict {}), otherwise normalizes from legacy fields
        (dice_rolls, dice_audit_events) if available.
        """
        # If action_resolution was explicitly provided (even if empty), use it
        # Otherwise, normalize from legacy fields if available
        if self._action_resolution_provided:
            return self.action_resolution
        return self._normalize_legacy_to_action_resolution()

    def _normalize_legacy_to_action_resolution(self) -> dict[str, Any]:
        """Convert dice_rolls + dice_audit_events to action_resolution format."""
        # Normalize if either dice_rolls or dice_audit_events exist
        if not self.dice_rolls and not self.dice_audit_events:
            return {}

        return {
            "player_input": None,  # Unknown from legacy
            "interpreted_as": "action",
            "reinterpreted": False,
            "mechanics": {
                "rolls": [{"display": r} for r in self.dice_rolls] if self.dice_rolls else [],
                "audit_events": self.dice_audit_events or [],
            },
            "audit_flags": ["normalized_from_legacy"],
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "narrative": self.narrative,
            "entities_mentioned": self.entities_mentioned,
            "location_confirmed": self.location_confirmed,
            "turn_summary": self.turn_summary,
            "state_updates": self.state_updates,
            "debug_info": self.debug_info,
            "session_header": self.session_header,
            "planning_block": self.planning_block,
            "dice_rolls": self.dice_rolls,
            "dice_audit_events": self.dice_audit_events,
            "resources": self.resources,
            "social_hp_challenge": self.social_hp_challenge,
            "action_resolution": self.action_resolution,
            "outcome_resolution": self.outcome_resolution,
        }

        # Include god_mode_response if present
        if self.god_mode_response:
            result["god_mode_response"] = self.god_mode_response

        return result


class EntityTrackingInstruction:
    """Schema for entity tracking instructions to be injected into prompts"""

    def __init__(
        self, scene_manifest: str, expected_entities: list[str], response_format: str
    ):
        self.scene_manifest = scene_manifest
        self.expected_entities = expected_entities
        self.response_format = response_format

    @classmethod
    def create_from_manifest(
        cls, manifest_text: str, expected_entities: list[str]
    ) -> "EntityTrackingInstruction":
        """Create entity tracking instruction from manifest"""
        response_format = {
            "narrative": "Your narrative text here...",
            "entities_mentioned": expected_entities,
            "location_confirmed": "The current location name",
            "state_updates": {
                "player_character_data": {"hp_current": "updated value if changed"},
                "npc_data": {"npc_name": {"status": "updated status"}},
                "world_data": {"current_location": "if moved"},
                "custom_campaign_state": {"any": "custom updates"},
                "world_events": {
                    "background_events": [
                        {
                            "actor": "Baroness Kess",
                            "action": "ordered her scouts to sabotage the bridge",
                            "location": "Northbridge Crossing",
                            "outcome": "bridge supports weakened, travel slowed",
                            "event_type": "immediate",
                            "status": "pending",  # pending|discovered|resolved
                            "player_aware": True,  # player can observe bridge damage
                            "discovery_condition": "locals report repairs needed; player notices delays",
                            "player_impact": "harder to move troops north next turn",
                        },
                        {
                            "actor": "Undertow Cult",
                            "action": "performed a midnight rite",
                            "location": "Shimmerfen Marsh",
                            "outcome": "ghostly lights seen, wards destabilizing",
                            "event_type": "immediate",
                            "status": "discovered",  # player learned of this
                            "player_aware": True,  # player heard rumors
                            "discovered_turn": 4,  # when player learned
                            "discovery_condition": "rumors from ferrymen or scouting the marsh",
                            "player_impact": "increases undead activity near routes east of the marsh",
                        },
                        {
                            "actor": "Lord Vance",
                            "action": "hired assassins to eliminate rival merchant",
                            "location": "Capital City, private estate",
                            "outcome": "contract signed, assassins en route",
                            "event_type": "long_term",
                            "status": "pending",
                            "player_aware": False,  # secret meeting, player cannot know
                            "discovery_condition": "merchant found dead or assassins intercepted",
                            "player_impact": "may affect trade relations if player involved with either party",
                        },
                    ],
                    # Actual turn number when these background events were generated.
                    "turn_generated": 3,
                },
                "faction_updates": {
                    "Iron Syndicate": {
                        "current_objective": "complete hidden tunnel to the docks",
                        "progress": "construction 75% complete",
                        "resource_change": "+2 shipments of illicit tools delivered",
                        "player_standing_change": "none yet (player unaware)",
                        "next_action": "bribe harbor master to ignore new night shipments",
                    }
                },
                "time_events": {
                    "Blood Moon Ritual": {
                        "time_remaining": "1 turn until completion",
                        "status": "ongoing",
                        "changes_this_turn": "cultists gathered final components",
                        "new_consequences": "summons a vengeful spirit if not interrupted",
                    }
                },
                "rumors": [
                    {
                        "content": "ferrymen say the marsh glows at night and patrols vanish",
                        "accuracy": "partial",
                        "source_type": "traveler",
                        "related_event": "Undertow Cult midnight rite",
                    }
                ],
                "npc_status_changes": {
                    "Captain Mara": {
                        "previous_state": "patrolling the harbor",
                        "new_state": "missing",
                        "reason": "abducted during the night raid",
                    }
                },
            },
        }

        response_format_str = json.dumps(response_format, indent=2)

        return cls(
            scene_manifest=manifest_text,
            expected_entities=expected_entities,
            response_format=response_format_str,
        )

    def to_prompt_injection(self) -> str:
        """Convert to prompt injection format"""
        entities_list = ", ".join(self.expected_entities)

        return f"""
{self.scene_manifest}

CRITICAL ENTITY TRACKING REQUIREMENT:
You MUST mention ALL characters listed in the manifest above in your narrative.
Required entities: {entities_list}

ENTITY TRACKING NOTES:
- Include ALL required entities ({entities_list}) in BOTH the narrative AND entities_mentioned array
- Set location_confirmed to match the current location from the manifest
- Update state_updates with any changes to entity status, health, or relationships
"""


def _combine_god_mode_and_narrative(
    god_mode_response: str, narrative: str | None
) -> str:
    """
    Helper function to handle god_mode_response and narrative fields.

    Rules:
    - If BOTH present: return only narrative (god_mode_response shown separately in structured fields)
    - If ONLY god_mode_response: return god_mode_response (also shown in structured fields)
    - If ONLY narrative: return narrative

    Args:
        god_mode_response: The god mode response text
        narrative: Optional narrative text

    Returns:
        Main story text for display
    """
    # If both are present, return only narrative (avoid duplication)
    if narrative and narrative.strip() and god_mode_response:
        return narrative
    # If only narrative, return it
    if narrative and narrative.strip():
        return narrative
    # If only god_mode_response, return it
    if god_mode_response:
        return god_mode_response
    # If neither, return empty string
    return ""


def parse_structured_response(
    response_text: str,
) -> tuple[str, NarrativeResponse]:  # noqa: PLR0911,PLR0912,PLR0915
    """
    Parse structured JSON response from LLM.

    NOTE: Regex-based JSON parsing and recovery have been removed per PR #3458.
    This function now uses standard json.loads() only. Invalid or malformed JSON
    responses will fail completely rather than attempting partial recovery.

    Behavior changes:
    - Truncated JSON responses will fail (no partial recovery)
    - Malformed JSON will fail (no regex-based extraction)
    - Text-wrapped JSON will fail (no boundary extraction)
    - Only valid JSON wrapped in markdown code blocks is supported

    Returns:
        tuple: (narrative_text, parsed_response)
    """

    def _apply_planning_fallback(
        narrative_value: str | None, planning_block: Any
    ) -> str:
        """Return narrative or minimal placeholder - DO NOT inject thinking text.

        The thinking text is rendered separately by the frontend via planning_block.
        Injecting it into narrative would cause double-rendering and pollute story history.
        """

        # Ensure narrative_value is a string
        if narrative_value is not None and not isinstance(narrative_value, str):
            try:
                narrative_value = str(narrative_value)
            except Exception:
                narrative_value = ""

        narrative_value = (narrative_value or "").strip()
        if narrative_value:
            return narrative_value

        # If narrative is empty but planning_block exists, return minimal placeholder
        # The frontend will render the planning_block.thinking separately
        if planning_block and isinstance(planning_block, dict):
            thinking_text = planning_block.get("thinking", "")
            if thinking_text and str(thinking_text).strip():
                # Return minimal placeholder - thinking is rendered via planning_block
                return "You pause to consider your options..."

        return narrative_value

    if not response_text:
        empty_response = NarrativeResponse(
            narrative="The story awaits your input...",  # Default narrative for empty response
            entities_mentioned=[],
            location_confirmed="Unknown",
        )
        return empty_response.narrative, empty_response

    # Check for system messages (e.g. refused content)
    if response_text.strip().startswith("[System Message:"):
        system_msg = response_text.strip()
        logging_util.warning(f"⚠️ Received system message instead of JSON: {system_msg}")

        # Create a valid NarrativeResponse wrapping the system message
        fallback_response = NarrativeResponse(
            narrative=system_msg,
            entities_mentioned=[],
            location_confirmed="Unknown",
            debug_info={"system_message": system_msg},
        )
        return fallback_response.narrative, fallback_response

    # First check if the JSON is wrapped in markdown code blocks
    json_content = response_text

    # Use precompiled pattern to match ```json ... ``` blocks
    match = JSON_MARKDOWN_PATTERN.search(response_text)

    if match:
        json_content = match.group(1).strip()
        logging_util.info("Extracted JSON from markdown code block")
    else:
        # Also try without the 'json' language identifier
        match = GENERIC_MARKDOWN_PATTERN.search(response_text)

        if match:
            content = match.group(1).strip()
            if content.startswith("{") and content.endswith("}"):
                json_content = content
                logging_util.info("Extracted JSON from generic code block")

    # Strategy: Handle code execution artifacts
    # When Gemini uses code execution, response may start with whitespace or code output
    # before the JSON. Find the first { (JSON object) to locate the actual JSON start.
    # We prefer { over [ because the response should be a JSON object, not an array.
    stripped = json_content.strip()
    if not stripped.startswith("{"):
        # Look for JSON object start character (prefer { over [)
        json_start = -1
        brace_pos = json_content.find("{")
        bracket_pos = json_content.find("[")

        # If array comes first, find the { that comes after the array closes
        if bracket_pos >= 0 and (brace_pos < 0 or bracket_pos < brace_pos):
            # Find the closing bracket for the array
            bracket_end = json_content.find("]", bracket_pos)
            if bracket_end >= 0:
                # Look for { after the array closes
                brace_after_array = json_content.find("{", bracket_end + 1)
                if brace_after_array >= 0:
                    json_start = brace_after_array
                else:
                    # No { after array, use array start as fallback
                    json_start = bracket_pos
            else:
                # Array not closed, use array start as fallback
                json_start = bracket_pos
        elif brace_pos >= 0:
            # { comes first or no array, use brace position
            json_start = brace_pos
        elif bracket_pos >= 0:
            # Only array exists, use it
            json_start = bracket_pos

        if json_start > 0:
            cleaned_json = json_content[json_start:].strip()
            logging_util.info(f"Removed code execution prefix ({json_start} chars) before JSON")
            json_content = cleaned_json

    # Parse JSON using standard json.loads()
    # Recovery logic: Handle various JSON errors with multiple recovery strategies
    recovery_attempted = False
    recovery_strategy = None
    parsed_data = None
    try:
        parsed_data = json.loads(json_content)
    except json.JSONDecodeError as e:
        error_msg = str(e)
        error_pos = getattr(e, "pos", None)

        # Strategy 1: Handle "Extra data" errors (valid JSON + trailing text)
        if "Extra data" in error_msg and error_pos is not None:
            recovery_attempted = True
            recovery_strategy = "extra_data_truncation"
            try:
                # Extract JSON up to the error position and strip trailing whitespace
                valid_json = json_content[:error_pos].rstrip()

                # Try parsing the truncated JSON
                parsed_data = json.loads(valid_json)
                extra_data_length = len(json_content) - error_pos
                logging_util.warning(
                    f"⚠️ JSON recovery (extra_data_truncation): Successfully parsed valid JSON portion "
                    f"(truncated at position {error_pos}, {extra_data_length} chars of extra data ignored). "
                    f"Original error: {error_msg}"
                )
            except (json.JSONDecodeError, ValueError):
                parsed_data = None
                # Keep recovery_strategy set to track which strategy was attempted

        # Strategy 2: Handle "Expecting value" errors (common with truncated/malformed responses)
        if parsed_data is None and "Expecting value" in error_msg:
            recovery_attempted = True
            recovery_strategy = "expecting_value_recovery"

            # Try to find the last complete JSON object/array
            # Look for the last closing brace/bracket
            last_brace = json_content.rfind("}")
            last_bracket = json_content.rfind("]")
            last_valid_pos = max(last_brace, last_bracket)

            if last_valid_pos > 0:
                try:
                    # Try parsing from start to last valid position
                    truncated_json = json_content[:last_valid_pos + 1]
                    parsed_data = json.loads(truncated_json)
                    logging_util.warning(
                        f"⚠️ JSON recovery (expecting_value_recovery): Successfully parsed JSON "
                        f"by truncating at last valid brace/bracket (position {last_valid_pos}). "
                        f"Original error: {error_msg}"
                    )
                except (json.JSONDecodeError, ValueError):
                    parsed_data = None
                    # Keep recovery_strategy set to track which strategy was attempted

        # Strategy 3: Try stripping common prefixes/suffixes that might cause issues
        if parsed_data is None and error_pos is not None:
            recovery_attempted = True
            recovery_strategy = "prefix_suffix_stripping"

            # Try removing leading/trailing whitespace and common markdown artifacts
            cleaned_json = json_content.strip()

            # Remove common markdown code block artifacts if present
            if cleaned_json.startswith("```"):
                # Find the first newline after ```
                first_newline = cleaned_json.find("\n")
                if first_newline > 0:
                    cleaned_json = cleaned_json[first_newline + 1:]

            if cleaned_json.endswith("```"):
                cleaned_json = cleaned_json[:-3].rstrip()

            # Try parsing cleaned JSON
            try:
                parsed_data = json.loads(cleaned_json)
                logging_util.warning(
                    f"⚠️ JSON recovery (prefix_suffix_stripping): Successfully parsed JSON "
                    f"after removing markdown artifacts. Original error: {error_msg}"
                )
            except (json.JSONDecodeError, ValueError):
                parsed_data = None
                # Keep recovery_strategy set to track which strategy was attempted

        # If all recovery strategies failed, log the error
        if parsed_data is None:
            if recovery_attempted:
                logging_util.warning(
                    f"⚠️ JSON recovery attempted ({recovery_strategy}) but failed. "
                    f"Falling back to error response. Original error: {error_msg}"
                )
            _log_json_parse_error(e, json_content, include_recovery_message=False)

    # Create NarrativeResponse from parsed data

    if parsed_data:
        # Ensure parsed_data is a dict, not a list (e.g., dice roll results)
        if not isinstance(parsed_data, dict):
            logging_util.error(
                f"Invalid JSON response format: expected dict, got {type(parsed_data).__name__}. "
                f"Response may be a list (e.g., dice roll result) instead of a structured response."
            )
            parsed_data = None

        if parsed_data:
            try:
                # Planning blocks should only come from JSON field, not extracted from narrative
                narrative = parsed_data.get("narrative", "")
                planning_block = parsed_data.get("planning_block", "")

                validated_response = NarrativeResponse(**parsed_data)
                # If god_mode_response is present, return both god mode response and narrative
                if (
                    hasattr(validated_response, "god_mode_response")
                    and validated_response.god_mode_response
                ):
                    combined_response = _combine_god_mode_and_narrative(
                        validated_response.god_mode_response,
                        validated_response.narrative,
                    )
                    validated_response.narrative = _apply_planning_fallback(
                        validated_response.narrative, validated_response.planning_block
                    )
                    return combined_response, validated_response

                validated_response.narrative = _apply_planning_fallback(
                    validated_response.narrative, validated_response.planning_block
                )
                return validated_response.narrative, validated_response

            except (ValueError, TypeError):
                # NarrativeResponse creation failed
                # Check for god_mode_response first
                god_mode_response = parsed_data.get("god_mode_response")
                if god_mode_response:
                    # For god mode, combine god_mode_response with narrative if both exist
                    narrative = parsed_data.get("narrative")
                    # Handle null narrative
                    if narrative is None:
                        narrative = ""
                    entities_value = parsed_data.get("entities_mentioned", [])
                    if not isinstance(entities_value, list):
                        entities_value = []

                    fallback_narrative = _apply_planning_fallback(
                        narrative, parsed_data.get("planning_block")
                    )

                    known_fields = {
                        "narrative": fallback_narrative,
                        "god_mode_response": god_mode_response,
                        "entities_mentioned": entities_value,
                        "location_confirmed": parsed_data.get("location_confirmed")
                        or "Unknown",
                        "state_updates": parsed_data.get("state_updates", {}),
                        "debug_info": parsed_data.get("debug_info", {}),
                    }
                    # Pass any other fields as kwargs
                    extra_fields = {
                        k: v for k, v in parsed_data.items() if k not in known_fields
                    }
                    fallback_response = NarrativeResponse(
                        **known_fields, **extra_fields
                    )
                    combined_response = _combine_god_mode_and_narrative(
                        god_mode_response, fallback_response.narrative
                    )
                    return combined_response, fallback_response

                # Return the narrative if we at least got that
                narrative = parsed_data.get("narrative")
                # Handle null or missing narrative - use empty string instead of raw JSON
                if narrative is None:
                    narrative = ""

                # Planning blocks should only come from JSON field
                planning_block = parsed_data.get("planning_block", "")

            fallback_narrative = _apply_planning_fallback(narrative, planning_block)

            # Extract only the fields we know about, let **kwargs handle the rest
            entities_value = parsed_data.get("entities_mentioned", [])
            if not isinstance(entities_value, list):
                entities_value = []

            known_fields = {
                "narrative": fallback_narrative,  # Use fallback_narrative with planning fallback applied
                "entities_mentioned": entities_value,  # Use validated entities_value
                "location_confirmed": parsed_data.get("location_confirmed")
                or "Unknown",
                "state_updates": parsed_data.get("state_updates", {}),
                "debug_info": parsed_data.get("debug_info", {}),
                "planning_block": planning_block,
            }
            # Pass any other fields as kwargs
            extra_fields = {
                k: v
                for k, v in parsed_data.items()
                if k not in known_fields and k != "planning_block"
            }
            fallback_response = NarrativeResponse(**known_fields, **extra_fields)
            return (
                fallback_response.narrative,
                fallback_response,
            )  # Return cleaned narrative from response

    # JSON parsing failed - return error response
    # NOTE: Multiple recovery strategies are attempted (extra_data_truncation, expecting_value_recovery, prefix_suffix_stripping).
    # If all recovery strategies fail, we return an error response to avoid silent data corruption.
    if recovery_attempted and parsed_data is None:
        error_detail = f"Recovery was attempted ({recovery_strategy}) but failed."
    elif not recovery_attempted:
        error_detail = "No recovery attempted - error type not recoverable."
    else:
        error_detail = None  # Recovery succeeded, parsed_data should be set

    if parsed_data is None:
        logging_util.error(
            f"Failed to parse JSON response - returning error message. {error_detail}"
        )
    fallback_response = NarrativeResponse(
        narrative="Invalid JSON response received. Please try again.",
        entities_mentioned=[],
        location_confirmed="Unknown",
    )
    return fallback_response.narrative, fallback_response


def create_generic_json_instruction() -> str:
    """
    Create generic JSON response format instruction when no entity tracking is needed
    (e.g., during character creation, campaign initialization, or scenes without entities)
    """
    # The JSON format is now defined in game_state_instruction.md which is always loaded
    # This function returns empty string since the format is already specified
    return ""


def create_structured_prompt_injection(
    manifest_text: str, expected_entities: list[str] | None
) -> str:
    """
    Create structured prompt injection for JSON response format

    Args:
        manifest_text: Formatted scene manifest (can be empty)
        expected_entities: List of entities that must be mentioned (can be empty)

    Returns:
        Formatted prompt injection string
    """
    expected_entities = expected_entities or []

    if expected_entities:
        # Use full entity tracking instruction when entities are present
        instruction = EntityTrackingInstruction.create_from_manifest(
            manifest_text, expected_entities
        )
        return instruction.to_prompt_injection()
    # Use generic JSON response format when no entities (e.g., character creation)
    return create_generic_json_instruction()


def validate_entity_coverage(
    response: NarrativeResponse, expected_entities: list[str]
) -> dict[str, Any]:
    """
    Validate that the structured response covers all expected entities

    Returns:
        Dict with validation results
    """
    mentioned_entities = {entity.lower() for entity in response.entities_mentioned}
    expected_entities_lower = {entity.lower() for entity in expected_entities}

    missing_entities = expected_entities_lower - mentioned_entities
    extra_entities = mentioned_entities - expected_entities_lower

    # Also check narrative text for entity mentions (backup validation)
    narrative_lower = response.narrative.lower()
    narrative_mentions = set()
    for entity in expected_entities:
        if entity.lower() in narrative_lower:
            narrative_mentions.add(entity.lower())

    actually_missing = expected_entities_lower - narrative_mentions

    return {
        "schema_valid": len(missing_entities) == 0,
        "narrative_valid": len(actually_missing) == 0,
        "missing_from_schema": list(missing_entities),
        "missing_from_narrative": list(actually_missing),
        "extra_entities": list(extra_entities),
        "coverage_rate": len(narrative_mentions) / len(expected_entities)
        if expected_entities
        else 1.0,
        "entities_mentioned_count": len(response.entities_mentioned),
        "expected_entities_count": len(expected_entities),
    }
