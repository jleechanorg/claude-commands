# ruff: noqa: PLR0911,PLR0912,PLR0915
"""
Simplified structured narrative generation schemas
Based on Milestone 0.4 Combined approach implementation (without pydantic dependency)
"""

import json
import re
from typing import Any

from mvp_site import logging_util
from mvp_site.json_utils import parse_llm_json_response, unescape_json_string

# Planning block extraction from narrative is deprecated - blocks should only come from JSON

# Minimum narrative length threshold for "suspiciously short" detection
# A valid narrative should typically be at least ~100 characters
MIN_NARRATIVE_LENGTH = 100

# Precompiled regex patterns for better performance
JSON_MARKDOWN_PATTERN = re.compile(r"```json\s*\n?(.*?)\n?```", re.DOTALL)
GENERIC_MARKDOWN_PATTERN = re.compile(r"```\s*\n?(.*?)\n?```", re.DOTALL)
NARRATIVE_PATTERN = re.compile(r'"narrative"\s*:\s*"([^"]*(?:\\.[^"]*)*)"')

# JSON cleanup patterns
JSON_STRUCTURE_PATTERN = re.compile(r"[{}\[\]]")
JSON_KEY_QUOTES_PATTERN = re.compile(r'"([^"]+)":')
JSON_COMMA_SEPARATOR_PATTERN = re.compile(r'",\s*"')
WHITESPACE_PATTERN = re.compile(
    r"[^\S\r\n]+"
)  # Normalize spaces while preserving line breaks

# Planning block detection is handled via brace matching in
# `_remove_planning_json_blocks`; regex explorations are intentionally omitted
# to keep the implementation single-sourced.
# Quick check just verifies both required keys exist (order-independent).

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

CHOICE_SCHEMA = {
    "text": str,  # Display name for the choice (REQUIRED)
    "description": str,  # What this choice entails (REQUIRED)
    "pros": list,  # Advantages of this choice (optional, list of strings)
    "cons": list,  # Risks/disadvantages (optional, list of strings)
    "confidence": str,  # "high" | "medium" | "low" (optional)
    "risk_level": str,  # "safe" | "low" | "medium" | "high" (REQUIRED)
    "analysis": dict,  # Additional analysis data (optional)
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


def _coerce_bool(value: Any) -> bool | None:
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
        entities_mentioned: list[str] = None,
        location_confirmed: str = "Unknown",
        turn_summary: str = None,
        state_updates: dict[str, Any] = None,
        debug_info: dict[str, Any] = None,
        god_mode_response: str = None,
        directives: dict[str, Any] = None,  # God mode: {add: [...], drop: [...]}
        session_header: str = None,
        planning_block: dict[str, Any] | None = None,
        dice_rolls: list[str] = None,
        dice_audit_events: list[dict[str, Any]] | None = None,
        resources: str = None,
        **kwargs,
    ):
        # Core required fields
        self.narrative = self._validate_narrative(narrative)
        self.entities_mentioned = self._validate_entities(entities_mentioned or [])
        self.location_confirmed = location_confirmed or "Unknown"
        self.turn_summary = turn_summary
        self.state_updates = self._validate_state_updates(state_updates)
        self.debug_info = self._validate_debug_info(debug_info)
        self.god_mode_response = god_mode_response
        self.directives = (
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

        # Store any extra fields that Gemini might include (shouldn't be any now)
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
        """
        if state_updates is None:
            return {}

        if not isinstance(state_updates, dict):
            logging_util.warning(
                f"Invalid state_updates type: {type(state_updates).__name__}, expected dict. Using empty dict instead."
            )
            return {}

        # Pass through state_updates with minimal validation
        # frozen_plans enforcement is handled by LLM prompts, not Python code
        return dict(state_updates)

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

        def _coerce_bool(value: Any) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in ("true", "yes", "1")
            return bool(value)

        validated: dict[str, Any] = {
            "source": str(rewards_box.get("source", "")).strip(),
            "xp_gained": _coerce_number(rewards_box.get("xp_gained", 0)),
            "current_xp": _coerce_number(rewards_box.get("current_xp", 0)),
            "next_level_xp": _coerce_number(rewards_box.get("next_level_xp", 0)),
            "progress_percent": _coerce_number(rewards_box.get("progress_percent", 0)),
            "level_up_available": _coerce_bool(
                rewards_box.get("level_up_available", False)
            ),
            "gold": _coerce_number(rewards_box.get("gold", 0)),
        }

        loot = rewards_box.get("loot", [])
        if not isinstance(loot, list):
            loot = [str(loot)] if loot is not None else []
        validated["loot"] = [str(item).strip() for item in loot if str(item).strip()]

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
        validated = {}

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
            provided_success = _coerce_bool(plan_quality.get("success"))
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

        validated_choices = {}
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

            validated_choice = {}

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

        def sanitize_string(value: str) -> str:
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

        sanitized = {}

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
        sanitized_choices = {}
        for choice_key, choice_data in planning_block.get("choices", {}).items():
            sanitized_choice = {}
            sanitized_choice["text"] = sanitize_string(choice_data.get("text", ""))
            sanitized_choice["description"] = sanitize_string(
                choice_data.get("description", "")
            )
            sanitized_choice["risk_level"] = choice_data.get("risk_level", "low")

            # Keep analysis if present (but sanitize strings within it)
            if "analysis" in choice_data:
                analysis = choice_data["analysis"]
                if isinstance(analysis, dict):
                    sanitized_analysis = {}
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

            sanitized_choices[choice_key] = sanitized_choice

        sanitized["choices"] = sanitized_choices

        return sanitized

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
                            "discovered_turn": 4,  # when player learned
                            "discovery_condition": "rumors from ferrymen or scouting the marsh",
                            "player_impact": "increases undead activity near routes east of the marsh",
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
    Parse structured response and check for JSON bug issues.
    """
    """
    Parse structured JSON response from LLM

    Returns:
        tuple: (narrative_text, parsed_response_or_none)
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

    # Use the robust parser on the extracted content
    parsed_data, was_incomplete = parse_llm_json_response(json_content)

    if was_incomplete:
        narrative_len = len(parsed_data.get("narrative", "")) if parsed_data else 0
        token_count = narrative_len // 4  # Rough estimate
        logging_util.info(
            f"Recovered from incomplete JSON response. Narrative length: {narrative_len} characters (~{token_count} tokens)"
        )
        # Warn if narrative is suspiciously short after recovery
        if narrative_len < MIN_NARRATIVE_LENGTH and narrative_len > 0:
            logging_util.warning(
                f"⚠️ SUSPICIOUSLY_SHORT_NARRATIVE: Narrative is only {narrative_len} chars "
                f"(min expected: {MIN_NARRATIVE_LENGTH}). This may indicate truncation due to "
                "malformed JSON with unescaped quotes. Consider reprompting."
            )

    # Create NarrativeResponse from parsed data

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
                    validated_response.god_mode_response, validated_response.narrative
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
                fallback_response = NarrativeResponse(**known_fields, **extra_fields)
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

    # Additional mitigation: Try to extract narrative from raw JSON-like text
    # This handles cases where JSON wasn't properly parsed but contains "narrative": "..."
    narrative_match = NARRATIVE_PATTERN.search(response_text)

    if narrative_match:
        extracted_narrative = narrative_match.group(1)
        # Properly unescape JSON string escapes
        extracted_narrative = unescape_json_string(extracted_narrative)
        logging_util.info("Extracted narrative from JSON-like text pattern")

        fallback_response = NarrativeResponse(
            narrative=extracted_narrative,
            entities_mentioned=[],
            location_confirmed="Unknown",
        )
        return fallback_response.narrative, fallback_response

    # Final fallback: Clean up raw text for display
    # Remove JSON-like structures and format for readability
    cleaned_text = response_text

    # Safer approach: Only clean if it's clearly malformed JSON
    # Check multiple indicators to avoid corrupting valid narrative text
    is_likely_json = (
        "{" in cleaned_text
        and '"' in cleaned_text
        and (
            cleaned_text.strip().startswith("{") or cleaned_text.strip().startswith('"')
        )
        and (cleaned_text.strip().endswith("}") or cleaned_text.strip().endswith('"'))
        and cleaned_text.count('"') >= 4  # At least 2 key-value pairs
    )

    if is_likely_json:
        # Apply cleanup only to confirmed JSON-like text
        # First, try to extract just the narrative value if possible
        if '"narrative"' in cleaned_text:
            # Try to extract narrative value safely
            narrative_match = NARRATIVE_PATTERN.search(cleaned_text)
            if narrative_match:
                cleaned_text = narrative_match.group(1)
                # Unescape JSON string escapes
                cleaned_text = (
                    cleaned_text.replace("\\n", "\n")
                    .replace('\\"', '"')
                    .replace("\\\\", "\\")
                )
                logging_util.info("Extracted narrative from JSON structure")
            else:
                # Fallback to aggressive cleanup only as last resort
                cleaned_text = JSON_STRUCTURE_PATTERN.sub(
                    "", cleaned_text
                )  # Remove braces and brackets
                cleaned_text = JSON_KEY_QUOTES_PATTERN.sub(
                    r"\1:", cleaned_text
                )  # Remove quotes from keys
                cleaned_text = JSON_COMMA_SEPARATOR_PATTERN.sub(
                    ". ", cleaned_text
                )  # Replace JSON comma separators
                cleaned_text = cleaned_text.replace(
                    "\\n", "\n"
                )  # Convert \n to actual newlines
                cleaned_text = cleaned_text.replace('\\"', '"')  # Unescape quotes
                cleaned_text = cleaned_text.replace(
                    "\\\\", "\\"
                )  # Unescape backslashes
                cleaned_text = WHITESPACE_PATTERN.sub(
                    " ", cleaned_text
                )  # Normalize spaces while preserving line breaks
                cleaned_text = cleaned_text.strip()
                logging_util.warning("Applied aggressive cleanup to malformed JSON")
        else:
            # No narrative field found, apply minimal cleanup
            cleaned_text = (
                cleaned_text.replace("\\n", "\n")
                .replace('\\"', '"')
                .replace("\\\\", "\\")
            )
            logging_util.warning(
                "Applied minimal cleanup to JSON-like text without narrative field"
            )

    # Final fallback response

    fallback_response = NarrativeResponse(
        narrative=cleaned_text, entities_mentioned=[], location_confirmed="Unknown"
    )

    # Final check for JSON artifacts in returned text
    if '"narrative":' in cleaned_text or '"god_mode_response":' in cleaned_text:
        # Try to extract narrative value one more time with more aggressive pattern
        narrative_match = NARRATIVE_PATTERN.search(cleaned_text)
        if narrative_match:
            cleaned_text = narrative_match.group(1)
            # Unescape JSON string escapes
            cleaned_text = (
                cleaned_text.replace("\\n", "\n")
                .replace('\\"', '"')
                .replace("\\\\", "\\")
            )
        else:
            # Final aggressive cleanup
            cleaned_text = JSON_STRUCTURE_PATTERN.sub(
                "", cleaned_text
            )  # Remove braces and brackets
            cleaned_text = JSON_KEY_QUOTES_PATTERN.sub(
                r"\1:", cleaned_text
            )  # Remove quotes from keys
            cleaned_text = JSON_COMMA_SEPARATOR_PATTERN.sub(
                ". ", cleaned_text
            )  # Replace JSON comma separators
            cleaned_text = cleaned_text.replace(
                "\\n", "\n"
            )  # Convert \n to actual newlines
            cleaned_text = cleaned_text.replace('\\"', '"')  # Unescape quotes
            cleaned_text = cleaned_text.replace("\\\\", "\\")  # Unescape backslashes
            cleaned_text = WHITESPACE_PATTERN.sub(" ", cleaned_text)  # Normalize spaces
            cleaned_text = cleaned_text.strip()

        # Update the fallback response with cleaned text
        fallback_response = NarrativeResponse(
            narrative=cleaned_text, entities_mentioned=[], location_confirmed="Unknown"
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
