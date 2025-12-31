"""
Unified API Layer for WorldArchitect.AI

This module provides consistent JSON interfaces for both Flask and MCP server usage,
extracting shared business logic and standardizing input/output formats.

Architecture:
- Unified functions handle the core game logic
- Consistent JSON input/output structures
- Centralized error handling and response formatting
- Support for both user_id extraction (Flask auth) and explicit parameters (MCP)

Concurrency:
- Async functions use asyncio.to_thread() for blocking I/O operations
- This prevents blocking the shared event loop during Gemini/Firestore calls
- Critical for allowing concurrent requests (e.g., loading campaigns while actions process)
"""

# ruff: noqa: E402, PLR0911, PLR0912, PLR0915, UP038

import asyncio
import collections
import copy
import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

# Apply clock skew patch BEFORE importing Firebase to handle time-ahead issues
from mvp_site.clock_skew_credentials import apply_clock_skew_patch

apply_clock_skew_patch()

import firebase_admin
from firebase_admin import credentials

# WorldArchitect imports
from mvp_site import (
    constants,
    document_generator,
    firestore_service,
    llm_service,
    logging_util,
    preventive_guards,
    structured_fields_utils,
    world_time,
)
from mvp_site.custom_types import CampaignId, UserId
from mvp_site.debug_hybrid_system import clean_json_artifacts, process_story_for_display
from mvp_site.firestore_service import (
    _truncate_log_json,
    get_user_settings,
    update_state_with_changes,
)
from mvp_site.game_state import GameState, validate_and_correct_state
from mvp_site.agent_prompts import extract_llm_instruction_hints
from mvp_site.prompt_utils import _build_campaign_prompt as _build_campaign_prompt_impl
from mvp_site.serialization import json_default_serializer

# Initialize Firebase if not already initialized (testing mode removed)
# WORLDAI_* vars take precedence for WorldArchitect.AI repo-specific config
try:
    firebase_admin.get_app()
except ValueError:
    try:
        worldai_creds_path = os.getenv("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS")
        if worldai_creds_path:
            worldai_creds_path = os.path.expanduser(worldai_creds_path)
            if os.path.exists(worldai_creds_path):
                logging_util.info(
                    f"Using WORLDAI credentials from {worldai_creds_path}"
                )
                firebase_admin.initialize_app(
                    credentials.Certificate(worldai_creds_path)
                )
            else:
                firebase_admin.initialize_app()
        else:
            firebase_admin.initialize_app()
        logging_util.info("Firebase initialized successfully in world_logic.py")
    except Exception as e:
        logging_util.critical(f"Failed to initialize Firebase: {e}")
        raise

# --- Constants ---
KEY_ERROR = "error"
KEY_SUCCESS = "success"
KEY_CAMPAIGN_ID = "campaign_id"
KEY_PROMPT = "prompt"

# Random constants moved to prompt_utils.py to avoid duplication
KEY_SELECTED_PROMPTS = "selected_prompts"
KEY_USER_INPUT = "user_input"
KEY_RESPONSE = "response"
KEY_TRACEBACK = "traceback"

# Temporal validation constants
# DISABLED: Set to 0 to prevent multiple LLM calls for temporal correction
# Previously was 2, but this causes 3 LLM calls total when time goes backward
MAX_TEMPORAL_CORRECTION_ATTEMPTS = 0  # Max retries before accepting response

_extract_world_time_from_response = world_time.extract_world_time_from_response
_check_temporal_violation = world_time.check_temporal_violation
_apply_timestamp_to_world_time = world_time.apply_timestamp_to_world_time
_format_world_time_for_prompt = world_time.format_world_time_for_prompt


def _extract_xp_from_player_data(pc_data: dict[str, Any]) -> int:
    """Extract XP value from player_character_data dict.

    Handles int, float, and string formats (including commas like "2,700").
    Returns 0 if XP cannot be parsed or is not present.

    Args:
        pc_data: Player character data dictionary

    Returns:
        Integer XP value, or 0 if not found/parseable
    """
    if not isinstance(pc_data, dict):
        return 0

    def _parse_numeric(val: Any) -> int:
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str):
            # Remove commas and whitespace, then try to parse
            cleaned = val.replace(",", "").replace(" ", "").strip()
            if not cleaned:
                return 0
            try:
                return int(float(cleaned))
            except (ValueError, TypeError):
                return 0
        return 0

    exp = pc_data.get("experience")
    if isinstance(exp, dict):
        return _parse_numeric(exp.get("current", 0))
    if exp is not None:
        return _parse_numeric(exp)
    xp = pc_data.get("xp")
    if xp is None:
        xp = pc_data.get("xp_current")
    if xp is not None:
        return _parse_numeric(xp)
    return 0


def _annotate_entry(entry: dict[str, Any], turn: int, scene: int) -> None:
    """Add turn/scene to a dict entry if not already present."""
    if "turn_generated" not in entry:
        entry["turn_generated"] = turn
        entry["scene_generated"] = scene


def annotate_world_events_with_turn_scene(
    game_state_dict: dict[str, Any],
    player_turn: int,
) -> dict[str, Any]:
    """Annotate living world entries with turn and scene numbers.

    Adds turn_generated and scene_generated to living world entries for UI display.

    NOTE: This function intentionally checks both nested and top-level locations.
    Living world data can appear in different locations based on LLM schema version:
    1. Under world_events.X (nested) - older schema
    2. At top level: rumors, faction_updates, etc. (direct) - newer schema

    These are DIFFERENT data structures, not duplicates. Even if the same object
    existed in both (by reference), annotation is idempotent (same turn/scene values).

    Args:
        game_state_dict: The game state dictionary to annotate
        player_turn: Player turn number (matches LLM cadence, not story entry count)

    Returns:
        The annotated game state dictionary
    """
    turn = player_turn
    # Each scene spans 2 player turns (e.g., turns 1-2 = scene 1, turns 3-4 = scene 2)
    TURNS_PER_SCENE = 2
    scene = (player_turn + 1) // TURNS_PER_SCENE

    def annotate_list(items: Any) -> None:
        """Annotate a list of dict entries."""
        if not isinstance(items, list):
            return
        for item in items:
            if isinstance(item, dict):
                _annotate_entry(item, turn, scene)

    def annotate_dict_values(container: Any) -> None:
        """Annotate all dict values in a container."""
        if not isinstance(container, dict):
            return
        for value in container.values():
            if isinstance(value, dict):
                _annotate_entry(value, turn, scene)

    def annotate_single(entry: Any) -> None:
        """Annotate a single dict entry."""
        if isinstance(entry, dict):
            _annotate_entry(entry, turn, scene)

    # 1. Annotate world_events.background_events (nested under world_events)
    world_events = game_state_dict.get("world_events")
    if isinstance(world_events, dict):
        annotate_list(world_events.get("background_events"))
        # Also check for nested versions (some schemas nest everything under world_events)
        annotate_list(world_events.get("rumors"))
        annotate_dict_values(world_events.get("faction_updates"))
        annotate_dict_values(world_events.get("time_events"))
        annotate_single(world_events.get("complications"))
        annotate_single(world_events.get("scene_event"))

    # 2. Annotate top-level living world fields (per schema, these are direct on state_updates)
    annotate_list(game_state_dict.get("rumors"))
    annotate_dict_values(game_state_dict.get("faction_updates"))
    annotate_dict_values(game_state_dict.get("time_events"))
    annotate_single(game_state_dict.get("complications"))
    annotate_single(game_state_dict.get("scene_event"))

    return game_state_dict


def _build_temporal_correction_prompt(
    original_user_input: str,
    old_time: dict[str, Any],
    new_time: dict[str, Any],
    old_location: str | None,
    new_location: str | None,
) -> str:
    """Build correction prompt when temporal violation detected.

    This prompts the LLM to regenerate the ENTIRE response with correct context.
    """
    old_time_str = _format_world_time_for_prompt(old_time)
    new_time_str = _format_world_time_for_prompt(new_time)
    old_loc = old_location or "Unknown location"
    new_loc = new_location or "Unknown location"

    return f"""⚠️ TEMPORAL VIOLATION - FULL REGENERATION REQUIRED

Your previous response was REJECTED because time went BACKWARD:
- CORRECT current state: {old_time_str} at {old_loc}
- YOUR invalid output: {new_time_str} at {new_loc}

🚨 CRITICAL ERROR: You appear to have lost track of the story timeline.

## ROOT CAUSE ANALYSIS
You likely focused on OLDER entries in the TIMELINE LOG instead of the MOST RECENT ones.
This caused you to generate a response for a scene that already happened in the past.

## MANDATORY CORRECTION INSTRUCTIONS

1. **FOCUS ON THE LATEST ENTRIES**: Look at the LAST 2-3 entries in the TIMELINE LOG.
   These represent where the story CURRENTLY is, not where it was earlier.

2. **IDENTIFY THE CURRENT SCENE**: The player is currently at:
   - Time: {old_time_str}
   - Location: {old_loc}
   - This is where you must CONTINUE from.

3. **GENERATE THE NEXT ENTRY**: Your response must continue the story forward.
   - Time MUST be AFTER {old_time_str} (move forward, even if just by minutes)
   - Location should logically follow from {old_loc}
   - Do NOT jump back to earlier scenes or locations

4. **IGNORE YOUR PREVIOUS ATTEMPT**: Your output of "{new_time_str} at {new_loc}" was WRONG.
   Do not use that as a reference.

## PLAYER ACTION TO RESPOND TO:
{original_user_input}

Generate a NEW response that is the NEXT logical entry in the timeline, continuing from the CURRENT state."""


def _build_temporal_warning_message(
    temporal_correction_attempts: int,
) -> str | None:
    """Build user-facing temporal warning text based on attempts taken."""

    if temporal_correction_attempts <= 0:
        return None

    # Always surface a warning once at least one correction was attempted.
    # When MAX_TEMPORAL_CORRECTION_ATTEMPTS is 0 (corrections disabled), we still
    # emit a warning and treat the effective max as at least one attempt so the
    # message doesn't silently disappear.
    effective_max_attempts = max(1, MAX_TEMPORAL_CORRECTION_ATTEMPTS)

    if temporal_correction_attempts > effective_max_attempts:
        return (
            f"⚠️ TEMPORAL CORRECTION EXCEEDED: The AI repeatedly generated responses that jumped "
            f"backward in time. After {temporal_correction_attempts} failed correction attempts "
            f"(configured max {MAX_TEMPORAL_CORRECTION_ATTEMPTS}), the system accepted the response "
            f"to avoid infinite loops. Timeline consistency may be compromised."
        )

    return (
        f"⚠️ TEMPORAL CORRECTION: The AI initially generated a response that jumped "
        f"backward in time. {temporal_correction_attempts} correction(s) were required "
        f"to fix the timeline continuity."
    )


def truncate_game_state_for_logging(
    game_state_dict: dict[str, Any], max_lines: int = 20
) -> str:
    """
    Truncates a game state dictionary for logging to improve readability.
    Uses the enhanced _truncate_log_json function from firestore_service.
    """
    return _truncate_log_json(
        game_state_dict, max_lines=max_lines, json_serializer=json_default_serializer
    )


def _has_rewards_narrative(narrative: str | None) -> bool:
    """Heuristic check for user-visible rewards in narrative text."""
    if not narrative:
        return False

    narrative_lower = narrative.lower()
    indicators = (
        "reward",
        "rewards",
        "xp",
        "experience",
        "level up",
        "level-up",
        "levelup",
        "loot",
        "gold",
        "treasure",
        "awarded",
        "gained",
        "victory",
    )
    if any(indicator in narrative_lower for indicator in indicators):
        return True

    # Common box markers used by RewardsAgent (format may vary)
    return "══" in narrative or "──" in narrative



def _has_rewards_context(
    state_dict: dict[str, Any], original_state_dict: dict[str, Any] | None = None
) -> bool:
    """Detect whether the current state suggests rewards should be visible."""
    combat_state = state_dict.get("combat_state", {}) or {}
    encounter_state = state_dict.get("encounter_state", {}) or {}
    rewards_pending = state_dict.get("rewards_pending") or {}

    if combat_state.get("combat_summary"):
        return True

    encounter_summary = encounter_state.get("encounter_summary")
    if isinstance(encounter_summary, dict) and encounter_summary:
        return True

    if rewards_pending:
        return True

    if original_state_dict is not None:
        # Use "or {}" to handle None values safely
        # (dict.get returns None when key exists with None value, not the default)
        current_xp = (
            (state_dict.get("player_character_data") or {}).get("experience") or {}
        ).get("current", 0)
        original_xp = (
            (original_state_dict.get("player_character_data") or {}).get("experience")
            or {}
        ).get("current", 0)
        if current_xp > original_xp:
            return True

    return False


def _enforce_rewards_processed_flag(
    state_dict: dict[str, Any], original_state_dict: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Server-side enforcement: Ensure rewards_processed is set when rewards were processed.

    This is a safety net for when the LLM doesn't follow the prompt to set this flag.
    The flag is critical to prevent RewardsAgent from triggering again on the next action.

    Sets rewards_processed=True when:
    1. Combat just ended (combat_phase="ended" and combat_summary exists)
    2. Encounter completed (encounter_completed=True and encounter_summary exists)
    3. XP increased from the previous state (with active combat or encounter)

    Args:
        state_dict: The game state dict after updates are applied
        original_state_dict: Optional original state before the update (for XP comparison)

    Returns:
        The game state dict with rewards_processed enforced
    """
    combat_state = state_dict.get("combat_state", {}) or {}
    encounter_state = state_dict.get("encounter_state", {}) or {}

    # Check combat rewards condition
    combat_phase = combat_state.get("combat_phase", "")
    combat_summary = combat_state.get("combat_summary")
    combat_rewards_processed = combat_state.get("rewards_processed", False)

    if (
        combat_phase in constants.COMBAT_FINISHED_PHASES
        and combat_summary
        and not combat_rewards_processed
    ):
        logging_util.info(
            "🏆 SERVER_ENFORCEMENT: Setting combat_state.rewards_processed=True "
            f"(combat_phase={combat_phase}, combat_summary exists)"
        )
        if "combat_state" not in state_dict:
            state_dict["combat_state"] = {}
        state_dict["combat_state"]["rewards_processed"] = True

    # Check encounter rewards condition
    # CRITICAL: Must require encounter_completed to match RewardsAgent trigger condition
    # (agents.py:798). Otherwise rewards get marked processed before RewardsAgent runs.
    encounter_completed = encounter_state.get("encounter_completed", False)
    encounter_summary = encounter_state.get("encounter_summary")
    encounter_rewards_processed = encounter_state.get("rewards_processed", False)

    if (
        encounter_completed
        and isinstance(encounter_summary, dict)
        and encounter_summary.get("xp_awarded") is not None
        and not encounter_rewards_processed
    ):
        logging_util.info(
            "🏆 SERVER_ENFORCEMENT: Setting encounter_state.rewards_processed=True "
            f"(encounter_completed={encounter_completed}, xp_awarded={encounter_summary.get('xp_awarded')})"
        )
        if "encounter_state" not in state_dict:
            state_dict["encounter_state"] = {}
        state_dict["encounter_state"]["rewards_processed"] = True

    # Check XP increase condition (fallback when LLM doesn't set summary structures)
    # Only trigger if combat/encounter context exists and XP increased
    if original_state_dict is not None:
        # Get XP values - use "or {}" to handle None values safely
        # (dict.get returns None when key exists with None value, not the default)
        current_xp = (
            (state_dict.get("player_character_data") or {}).get("experience") or {}
        ).get("current", 0)
        original_xp = (
            (original_state_dict.get("player_character_data") or {}).get("experience")
            or {}
        ).get("current", 0)

        # Detect XP increase
        xp_increased = current_xp > original_xp
        xp_gain = current_xp - original_xp if xp_increased else 0

        # Check if rewards_processed is set anywhere
        any_rewards_processed = (
            combat_state.get("rewards_processed", False)
            or encounter_state.get("rewards_processed", False)
        )

        # If XP increased but no rewards_processed flag is set, try to set it
        if xp_increased and not any_rewards_processed:
            # Check for combat context (even if ended without summary)
            combat_phase = combat_state.get("combat_phase", "")
            has_combat_context = combat_phase in constants.COMBAT_FINISHED_PHASES

            # Check for encounter context
            encounter_completed = encounter_state.get("encounter_completed", False)
            has_encounter_active = encounter_state.get("encounter_active", False)
            has_encounter_context = encounter_completed or has_encounter_active

            if has_combat_context:
                logging_util.info(
                    "🏆 SERVER_ENFORCEMENT: Setting combat_state.rewards_processed=True "
                    f"(XP increased by {xp_gain}: {original_xp} → {current_xp}, combat_phase={combat_phase})"
                )
                if "combat_state" not in state_dict:
                    state_dict["combat_state"] = {}
                state_dict["combat_state"]["rewards_processed"] = True
            elif has_encounter_context:
                logging_util.info(
                    "🏆 SERVER_ENFORCEMENT: Setting encounter_state.rewards_processed=True "
                    f"(XP increased by {xp_gain}: {original_xp} → {current_xp}, encounter context present)"
                )
                if "encounter_state" not in state_dict:
                    state_dict["encounter_state"] = {}
                state_dict["encounter_state"]["rewards_processed"] = True

    return state_dict


async def _process_rewards_followup(
    mode: str,
    llm_response_obj: Any,
    updated_game_state_dict: dict[str, Any],
    current_state_as_dict: dict[str, Any],
    original_world_time: dict[str, Any] | None,
    story_context: list[dict[str, Any]],
    selected_prompts: list[str],
    use_default_world: bool,
    user_id: str,
    prevention_extras: dict[str, Any],
) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    """
    Process rewards follow-up if needed after primary action.

    This function checks if RewardsAgent needs to run as a follow-up to ensure
    user-visible rewards output. It prevents double invocation by checking if
    rewards_box already exists in the response.

    Args:
        mode: The original action mode (MODE_CHARACTER, MODE_COMBAT, etc.)
        llm_response_obj: The primary LLM response object
        updated_game_state_dict: Current game state dict after primary updates
        current_state_as_dict: Original state dict before the action
        original_world_time: Original world time for validation
        story_context: Story context for LLM calls
        selected_prompts: Selected prompts for LLM calls
        use_default_world: Whether using default world
        user_id: User ID for LLM calls
        prevention_extras: Dict to accumulate prevention extras

    Returns:
        Tuple of (updated_game_state_dict, llm_response_obj, prevention_extras)
    """
    # Check if RewardsAgent already ran (rewards_box in response = no follow-up needed)
    # This prevents double agent invocation when get_agent_for_input() selected RewardsAgent
    rewards_already_in_response = (
        hasattr(llm_response_obj, "structured_response")
        and llm_response_obj.structured_response is not None
        and getattr(llm_response_obj.structured_response, "rewards_box", None)
        is not None
    )

    if mode == constants.MODE_REWARDS or rewards_already_in_response:
        return updated_game_state_dict, llm_response_obj, prevention_extras

    post_update_state = GameState.from_dict(updated_game_state_dict)
    rewards_visible = _has_rewards_narrative(llm_response_obj.narrative_text)
    rewards_expected = _has_rewards_context(
        updated_game_state_dict, original_state_dict=current_state_as_dict
    )
    rewards_pending = post_update_state.has_pending_rewards() if post_update_state else False

    if not post_update_state or not (rewards_pending or (rewards_expected and not rewards_visible)):
        return updated_game_state_dict, llm_response_obj, prevention_extras

    logging_util.info(
        "🏆 REWARDS_FOLLOWUP: Invoking RewardsAgent "
        f"(pending={rewards_pending}, visible={rewards_visible}, expected={rewards_expected})"
    )

    rewards_response_obj = await asyncio.to_thread(
        llm_service.continue_story,
        "continue",  # neutral prompt for rewards mode
        constants.MODE_REWARDS,
        story_context,
        post_update_state,
        selected_prompts,
        use_default_world,
        user_id,
    )

    rewards_state_changes, rewards_prevention_extras = (
        preventive_guards.enforce_preventive_guards(
            post_update_state, rewards_response_obj, constants.MODE_REWARDS
        )
    )

    if rewards_pending:
        # Apply preventive guards and update state with rewards response
        rewards_state_changes = _apply_timestamp_to_world_time(rewards_state_changes)
        rewards_state_changes = world_time.ensure_progressive_world_time(
            rewards_state_changes, is_god_mode=False
        )
        rewards_new_world_time = (
            rewards_state_changes.get("world_data", {}) or {}
        ).get("world_time")

        updated_game_state_dict = update_state_with_changes(
            updated_game_state_dict, rewards_state_changes
        )
        updated_game_state_dict = validate_game_state_updates(
            updated_game_state_dict,
            new_time=rewards_new_world_time,
            original_time=original_world_time,
        )
        updated_game_state_dict = _enforce_rewards_processed_flag(
            updated_game_state_dict,
            original_state_dict=current_state_as_dict,
        )
        updated_game_state_dict, rewards_corrections = validate_and_correct_state(
            updated_game_state_dict,
            previous_world_time=original_world_time,
            return_corrections=True,
        )
        # Store rewards corrections so they reach system_warnings in main flow
        if rewards_corrections:
            prevention_extras.setdefault("rewards_corrections", []).extend(rewards_corrections)
    else:
        # Rewards already applied; avoid double-awarding state changes.
        updated_game_state_dict = _enforce_rewards_processed_flag(
            updated_game_state_dict,
            original_state_dict=current_state_as_dict,
        )

    # Merge prevention extras for response visibility
    prevention_extras.update(rewards_prevention_extras)

    # Append rewards narrative to original narrative for user visibility
    primary_text = llm_response_obj.narrative_text or ""
    rewards_text = rewards_response_obj.narrative_text or ""
    if rewards_text:
        combined = f"{primary_text}\n\n{rewards_text}" if primary_text else rewards_text
        llm_response_obj.narrative_text = combined

    # Merge structured response from rewards follow-up (critical: rewards_box)
    rewards_structured = getattr(rewards_response_obj, "structured_response", None)
    if rewards_structured:
        primary_structured = getattr(llm_response_obj, "structured_response", None)
        if primary_structured is None:
            # No original structured response, use rewards response
            llm_response_obj.structured_response = rewards_structured
        else:
            # Merge rewards_box from rewards response into primary
            if hasattr(rewards_structured, "rewards_box") and rewards_structured.rewards_box:
                primary_structured.rewards_box = rewards_structured.rewards_box
                logging_util.info(
                    f"🏆 REWARDS_FOLLOWUP: Merged rewards_box into response "
                    f"(xp={rewards_structured.rewards_box.get('xp_gained', 'N/A')})"
                )

    return updated_game_state_dict, llm_response_obj, prevention_extras


def validate_game_state_updates(
    updated_state_dict: dict[str, Any],
    new_time: dict[str, Any] | None = None,
    original_time: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Validate and auto-correct game state updates.

    Applies XP/level validation and time monotonicity checks to the state dict.
    This should be called after update_state_with_changes() but before
    persisting to Firestore.

    Args:
        updated_state_dict: The game state dict after updates are applied
        new_time: Optional new world_time to validate for monotonicity
        original_time: Optional original world_time from before the update.
            Required for accurate time monotonicity checking since
            updated_state_dict already has new_time merged in.

    Returns:
        The validated (and potentially corrected) state dict

    Validation Applied:
        1. XP/Level consistency: Ensures level matches XP thresholds (D&D 5e)
        2. Missing level persistence: Computes and saves level if absent
        3. Type coercion: Handles string values from JSON/LLM responses
        4. Time monotonicity: Warns if time goes backward (if new_time provided)
    """
    # Create temporary GameState for validation
    temp_state = GameState.from_dict(updated_state_dict)
    if temp_state is None:
        logging_util.warning(
            "validate_game_state_updates: Could not create GameState, skipping validation"
        )
        return updated_state_dict

    # Validate XP/Level consistency (auto-corrects mismatches)
    xp_result = temp_state.validate_xp_level(strict=False)
    if xp_result.get("corrected"):
        logging_util.info(
            f"XP/Level validation corrected: expected_level={xp_result.get('expected_level')}, "
            f"provided_level={xp_result.get('provided_level')}"
        )
    if xp_result.get("computed_level"):
        logging_util.info(
            f"XP/Level validation computed missing level: {xp_result.get('computed_level')}"
        )

    # Validate time monotonicity if new_time is provided
    # Use original_time for comparison if provided, otherwise compare against
    # temp_state (which already has new_time merged, so it would compare to itself)
    if new_time and original_time is not None:
        # Temporarily set the original time for accurate comparison
        if temp_state.world_data:
            saved_time = temp_state.world_data.get("world_time")
            temp_state.world_data["world_time"] = original_time
            time_result = temp_state.validate_time_monotonicity(new_time, strict=False)
            # Restore the new time after validation
            temp_state.world_data["world_time"] = saved_time
            if time_result.get("warning"):
                logging_util.warning(
                    f"Time validation warning: {time_result.get('message')}"
                )
    elif new_time:
        # Fallback: compare against current state (may be inaccurate if already merged)
        time_result = temp_state.validate_time_monotonicity(new_time, strict=False)
        if time_result.get("warning"):
            logging_util.warning(
                f"Time validation warning: {time_result.get('message')}"
            )

    # Return the validated state dict (includes any corrections made)
    return temp_state.to_dict()


def _prepare_game_state(
    user_id: UserId, campaign_id: CampaignId
) -> tuple[GameState, bool, int]:
    """
    Load and prepare game state, including legacy cleanup.
    Extracted from main.py to maintain exact functionality.
    """
    current_game_state_doc = firestore_service.get_campaign_game_state(
        user_id, campaign_id
    )

    if current_game_state_doc:
        current_game_state = GameState.from_dict(current_game_state_doc.to_dict())
        if current_game_state is None:
            logging_util.warning(
                "PREPARE_GAME_STATE: GameState.from_dict returned None, using default state"
            )
            current_game_state = GameState(user_id=user_id)
    else:
        current_game_state = GameState(user_id=user_id)

    # Perform cleanup on a dictionary copy
    cleaned_state_dict, was_cleaned, num_cleaned = _cleanup_legacy_state(
        current_game_state.to_dict()
    )

    # Archive finished combat to history and clear active state at action START
    # This prevents stale combat_summary from being seen by LLM on next action
    # while allowing the previous action's response to include combat_summary
    #
    # IMPORTANT: Only clean if rewards_processed=True, otherwise RewardsAgent
    # needs to trigger first to display the rewards box and process XP/loot.
    combat_state = cleaned_state_dict.get("combat_state", {})
    # Use centralized constant for combat finished phases
    combat_phase = combat_state.get("combat_phase", "")
    rewards_processed = combat_state.get("rewards_processed", False)

    if (
        not combat_state.get("in_combat", True)
        and combat_phase in constants.COMBAT_FINISHED_PHASES
        and combat_state.get("combat_summary")
    ):
        if not rewards_processed:
            # Keep combat state intact for RewardsAgent to trigger
            logging_util.info(
                f"Combat ended but rewards_processed=False, keeping combat_summary for RewardsAgent. "
                f"xp_awarded={combat_state['combat_summary'].get('xp_awarded')}"
            )
        else:
            # Rewards already processed, safe to archive and clean
            combat_history = combat_state.get("combat_history", [])
            archived_entry = {
                **combat_state["combat_summary"],
                "session_id": combat_state.get("combat_session_id"),
                "archived_at": datetime.now(timezone.utc).isoformat(),
            }
            combat_history.append(archived_entry)

            logging_util.info(
                f"Archived finished combat to history: session_id={combat_state.get('combat_session_id')}, "
                f"xp_awarded={combat_state['combat_summary'].get('xp_awarded')}"
            )

            # Clear active combat state for clean LLM context
            combat_state["combat_history"] = combat_history
            combat_state["combat_summary"] = None
            combat_state["combat_phase"] = "idle"
            combat_state["combat_session_id"] = None
            combat_state["combatants"] = {}
            combat_state["initiative_order"] = []
            combat_state["current_round"] = None
            combat_state["rewards_processed"] = False  # Reset for next combat
            cleaned_state_dict["combat_state"] = combat_state
            was_cleaned = True

            # Persist the cleaned state immediately so LLM sees clean context
            firestore_service.update_campaign_game_state(
                user_id, campaign_id, cleaned_state_dict
            )

    if was_cleaned:
        # Ensure user_id is preserved in cleaned state
        cleaned_state_dict["user_id"] = user_id
        current_game_state = GameState.from_dict(cleaned_state_dict)
        if current_game_state is None:
            logging_util.error(
                "PREPARE_GAME_STATE: GameState.from_dict returned None after cleanup, using default state"
            )
            current_game_state = GameState(user_id=user_id)
        firestore_service.update_campaign_game_state(
            user_id, campaign_id, current_game_state.to_dict()
        )
        logging_util.info(
            f"Cleaned {num_cleaned} legacy state entries for campaign {campaign_id}"
        )

    return current_game_state, was_cleaned, num_cleaned


def _cleanup_legacy_state(
    state_dict: dict[str, Any],
) -> tuple[dict[str, Any], bool, int]:
    """
    Clean up legacy fields from game state.
    Extracted from main.py to maintain compatibility.
    """
    cleaned_dict = state_dict.copy()
    was_cleaned = False
    num_cleaned = 0

    # Define legacy fields that should be removed
    legacy_fields = [
        "party_data",  # Old party system
        "legacy_prompt_data",  # Old prompt format
        "deprecated_settings",  # Old settings format
    ]

    # Remove legacy fields
    for field in legacy_fields:
        if field in cleaned_dict:
            del cleaned_dict[field]
            was_cleaned = True
            num_cleaned += 1

    return cleaned_dict, was_cleaned, num_cleaned


def _get_player_character_data(game_state: Any) -> dict[str, Any]:
    """Safely extract player character data from game state objects or dicts."""

    if isinstance(game_state, dict):
        return game_state.get("player_character_data", {}) or {}

    if hasattr(game_state, "player_character_data"):
        return game_state.player_character_data or {}

    return {}


def _enrich_session_header_with_progress(
    session_header: str | None, game_state: Any
) -> str:
    """Ensure XP and gold are present in the session header for the UI."""

    session_header = session_header or ""

    player_data = _get_player_character_data(game_state)
    xp_current = player_data.get("xp_current")
    xp_next_level = player_data.get("xp_next_level")
    gold_amount = player_data.get("gold")

    contains_xp = re.search(r"\b(XP|experience)\b", session_header, flags=re.IGNORECASE)
    contains_gold = re.search(r"\b(Gold|gp)\b", session_header, flags=re.IGNORECASE)

    remove_prefixes: tuple[str, ...] = ()
    additions: list[str] = []
    if xp_current is not None and not contains_xp:
        xp_text = (
            f"XP: {xp_current}/{xp_next_level}"
            if xp_next_level is not None and xp_next_level != ""
            else f"XP: {xp_current}"
        )
        additions.append(xp_text)
        remove_prefixes += ("xp:", "experience:")

    if gold_amount is not None and not contains_gold:
        additions.append(f"Gold: {gold_amount}gp")
        remove_prefixes += ("gold:", "gp:")

    if not additions:
        return session_header

    def _remove_resource_tokens(tokens: list[str]) -> list[str]:
        if not remove_prefixes:
            return tokens

        return [
            token
            for token in tokens
            if token and not token.lower().strip().startswith(remove_prefixes)
        ]

    lines = session_header.splitlines()
    for idx, line in enumerate(lines):
        if line.strip().startswith("Status:"):
            prefix, _, remainder = line.partition("Status:")
            status_tokens = [part.strip() for part in remainder.split("|")]
            status_tokens = _remove_resource_tokens(status_tokens)
            merged_tokens = [token for token in status_tokens if token]
            merged_tokens.extend(additions)
            lines[idx] = f"{prefix}Status: {' | '.join(merged_tokens)}"
            return "\n".join(lines)

    if lines:
        separator = " | " if lines[-1].strip() else ""
        lines[-1] = f"{lines[-1]}{separator}{' | '.join(additions)}"
    else:
        lines.append(" | ".join(additions))

    return "\n".join(lines)


def _ensure_session_header_resources(
    structured_fields: dict[str, Any], game_state: Any
) -> dict[str, Any]:
    """
    Enriches session header with XP and gold from game state if these values exist in
    player_character_data but are not already present in the session header text.
    """

    if not structured_fields:
        return structured_fields

    session_header = structured_fields.get(constants.FIELD_SESSION_HEADER, "")
    enriched_header = _enrich_session_header_with_progress(session_header, game_state)

    if enriched_header == session_header:
        return structured_fields

    updated_fields = structured_fields.copy()
    updated_fields[constants.FIELD_SESSION_HEADER] = enriched_header
    return updated_fields


def _strip_game_state_fields(
    story_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Strip game state information from story entries when debug mode is OFF.
    Extracted from main.py to maintain compatibility.
    """
    if not story_entries:
        return story_entries

    # Fields to strip when debug mode is OFF
    game_state_fields = {
        "entities_mentioned",
        "entities",
        "state_updates",
        "debug_info",
    }

    stripped_story = []
    for entry in story_entries:
        # Create a copy without the game state fields
        stripped_entry = {
            key: value for key, value in entry.items() if key not in game_state_fields
        }
        stripped_story.append(stripped_entry)

    return stripped_story


# Helper function moved to prompt_utils.py to eliminate duplication


def _build_campaign_prompt(
    character: str, setting: str, description: str, old_prompt: str
) -> str:
    """
    Build campaign prompt from parameters.
    Unified logic from main.py and world_logic.py.
    """
    # Use the extracted implementation from prompt_utils.py
    return _build_campaign_prompt_impl(character, setting, description, old_prompt)


def _handle_debug_mode_command(
    user_input: str,
    current_game_state: GameState,
    user_id: UserId,
    campaign_id: CampaignId,
) -> dict[str, Any] | None:
    """
    Handle debug mode commands.
    Simplified version for unified API.

    Note: Processes debug commands regardless of debug_mode setting,
    but filters output based on debug_mode in the response.
    """

    user_input_stripped = user_input.strip()

    # Check if debug mode is enabled for filtering responses
    debug_mode_enabled = (
        hasattr(current_game_state, "debug_mode") and current_game_state.debug_mode
    )

    debug_disabled_response = {
        KEY_SUCCESS: True,
        KEY_RESPONSE: "Debug mode is not enabled",
    }

    try:
        # GOD_ASK_STATE
        if user_input_stripped == "GOD_ASK_STATE":
            if not debug_mode_enabled:
                return debug_disabled_response
            return _handle_ask_state_command(
                user_input, current_game_state, user_id, campaign_id
            )

        # GOD_MODE_SET
        if user_input_stripped.startswith("GOD_MODE_SET:"):
            if not debug_mode_enabled:
                return debug_disabled_response
            return _handle_set_command(
                user_input, current_game_state, user_id, campaign_id
            )

        # GOD_MODE_UPDATE_STATE
        if user_input_stripped.startswith("GOD_MODE_UPDATE_STATE:"):
            if not debug_mode_enabled:
                return debug_disabled_response
            return _handle_update_state_command(user_input, user_id, campaign_id)

    except Exception as e:
        logging_util.error(f"Debug command failed: {e}")
        return {KEY_ERROR: f"Debug command failed: {str(e)}"}

    return None


# --- Unified API Functions ---


async def create_campaign_unified(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    Unified campaign creation logic for both Flask and MCP.

    Uses asyncio.to_thread() for blocking I/O operations to prevent blocking
    the shared event loop.

    Args:
        request_data: Dictionary containing:
            - user_id: User ID
            - title: Campaign title
            - character: Character description (optional)
            - setting: Setting description (optional)
            - description: Campaign description (optional)
            - prompt: Legacy prompt format (optional)
            - selected_prompts: List of selected prompts (optional)
            - custom_options: List of custom options (optional)

    Returns:
        Dictionary with success/error status and campaign data
    """
    try:
        # Extract parameters
        user_id = request_data.get("user_id")
        title = request_data.get("title")
        character = request_data.get("character", "")
        setting = request_data.get("setting", "")
        description = request_data.get("description", "")
        old_prompt = request_data.get("prompt", "")
        selected_prompts = request_data.get("selected_prompts", [])
        custom_options = request_data.get("custom_options", [])

        # Validate required fields
        if not user_id:
            return {KEY_ERROR: "User ID is required"}
        if not title:
            return {KEY_ERROR: "Title is required"}

        # Build campaign prompt
        try:
            prompt = _build_campaign_prompt(character, setting, description, old_prompt)
        except ValueError as e:
            return {KEY_ERROR: str(e)}

        # Always use D&D system
        attribute_system = constants.ATTRIBUTE_SYSTEM_DND

        # Get user settings to apply debug mode during campaign creation (blocking I/O)
        user_settings = await asyncio.to_thread(get_user_settings, user_id)
        debug_mode = (
            user_settings.get("debug_mode", constants.DEFAULT_DEBUG_MODE)
            if user_settings
            else constants.DEFAULT_DEBUG_MODE
        )

        # Create initial game state with user's debug mode preference
        initial_game_state = GameState(
            user_id=user_id,
            custom_campaign_state={"attribute_system": attribute_system},
            debug_mode=debug_mode,
        ).to_dict()

        generate_companions = "companions" in custom_options
        use_default_world = "defaultWorld" in custom_options

        # Generate opening story using LLM (CRITICAL: blocking I/O - 10-30+ seconds!)
        try:
            opening_story_response = await asyncio.to_thread(
                llm_service.get_initial_story,
                prompt,
                user_id,
                selected_prompts,
                generate_companions,
                use_default_world,
            )
        except llm_service.LLMRequestError as e:
            logging_util.error(f"LLM request failed during campaign creation: {e}")
            status_code = getattr(e, "status_code", None) or 422
            return create_error_response(str(e), status_code)

        # Extract structured fields
        opening_story_structured_fields = _ensure_session_header_resources(
            structured_fields_utils.extract_structured_fields(opening_story_response),
            initial_game_state,
        )

        # Create campaign in Firestore (blocking I/O - run in thread)
        campaign_id = await asyncio.to_thread(
            firestore_service.create_campaign,
            user_id,
            title,
            prompt,
            opening_story_response.narrative_text,
            initial_game_state,
            selected_prompts,
            use_default_world,
            opening_story_structured_fields,
        )

        return {
            KEY_SUCCESS: True,
            KEY_CAMPAIGN_ID: campaign_id,
            "title": title,
            "opening_story": opening_story_response.narrative_text,
            "game_state": initial_game_state,
            "attribute_system": attribute_system,
        }

    except Exception as e:
        logging_util.error(f"Campaign creation failed: {e}")
        return {KEY_ERROR: f"Failed to create campaign: {str(e)}"}


async def process_action_unified(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    Unified story processing logic for both Flask and MCP.

    Uses asyncio.to_thread() for blocking I/O operations to prevent blocking
    the shared event loop. This allows concurrent requests (e.g., loading a
    campaign while an action is being processed).

    Args:
        request_data: Dictionary containing:
            - user_id: User ID
            - campaign_id: Campaign ID
            - user_input: User action/input
            - mode: Interaction mode (optional, defaults to 'character')

    Returns:
        Dictionary with success/error status and story response
    """
    campaign_id = request_data.get("campaign_id")
    logging_util.set_campaign_id(campaign_id)
    try:
        # Extract parameters
        user_id = request_data.get("user_id")
        user_input = request_data.get("user_input")
        mode = request_data.get("mode", constants.MODE_CHARACTER)

        # Validate required fields
        if not user_id:
            return {KEY_ERROR: "User ID is required"}
        if not campaign_id:
            return {KEY_ERROR: "Campaign ID is required"}
        if user_input is None:
            return {KEY_ERROR: "User input is required"}

        # Load and prepare game state (blocking I/O - run in thread)
        current_game_state, was_cleaned, num_cleaned = await asyncio.to_thread(
            _prepare_game_state, user_id, campaign_id
        )

        # Apply user settings to game state (blocking I/O - run in thread)
        user_settings = await asyncio.to_thread(get_user_settings, user_id)
        if user_settings and "debug_mode" in user_settings:
            current_game_state.debug_mode = user_settings["debug_mode"]

        # Handle debug mode commands (may contain blocking I/O)
        debug_response = await asyncio.to_thread(
            _handle_debug_mode_command,
            user_input,
            current_game_state,
            user_id,
            campaign_id,
        )
        if debug_response:
            return debug_response

        # Get story context for Gemini (blocking I/O - run in thread)
        campaign_data, story_context = await asyncio.to_thread(
            firestore_service.get_campaign_by_id, user_id, campaign_id
        )
        if not campaign_data:
            return {KEY_ERROR: "Campaign not found", "status_code": 404}

        story_context = story_context or []

        # Get campaign settings
        selected_prompts = campaign_data.get("selected_prompts", [])
        use_default_world = campaign_data.get("use_default_world", False)

        # Extract current world_time and location for temporal validation
        # CRITICAL: world_data can be None or non-dict in existing saves - normalize to {} first
        world_data = getattr(current_game_state, "world_data", None)
        if not isinstance(world_data, dict):
            world_data = {}
        old_world_time = world_data.get("world_time")
        old_location = world_data.get("current_location_name")

        # Process regular game action with LLM (CRITICAL: blocking I/O - 10-30+ seconds!)
        # This is the most important call to run in a thread to prevent blocking
        # TEMPORAL VALIDATION LOOP: Retry if LLM generates backward time
        # EXCEPTION: GOD MODE commands can intentionally move time backward
        is_god_mode = user_input.strip().upper().startswith("GOD MODE:")
        original_user_input = user_input  # Preserve for Firestore
        llm_input = user_input  # Separate variable for LLM calls
        temporal_correction_attempts = 0
        llm_response_obj = None
        new_world_time: dict[str, Any] | None = None

        while temporal_correction_attempts <= MAX_TEMPORAL_CORRECTION_ATTEMPTS:
            try:
                llm_response_obj = await asyncio.to_thread(
                    llm_service.continue_story,
                    llm_input,  # Use llm_input, NOT user_input
                    mode,
                    story_context,
                    current_game_state,
                    selected_prompts,
                    use_default_world,
                    user_id,  # Pass user_id to enable user model preference selection
                )
            except llm_service.LLMRequestError as e:
                logging_util.error(f"LLM request failed during story continuation: {e}")
                status_code = getattr(e, "status_code", None) or 422
                return create_error_response(str(e), status_code)

            # Check for temporal violation (time going backward)
            # EXCEPTION: Skip validation for GOD MODE (backward time is intentional)
            new_world_time = _extract_world_time_from_response(llm_response_obj)

            if is_god_mode or not _check_temporal_violation(
                old_world_time, new_world_time
            ):
                # No violation - time is moving forward (or GOD MODE allows backward), accept response
                if is_god_mode and _check_temporal_violation(
                    old_world_time, new_world_time
                ):
                    logging_util.info(
                        f"⏪ GOD_MODE: Allowing backward time travel from "
                        f"{_format_world_time_for_prompt(old_world_time)} to "
                        f"{_format_world_time_for_prompt(new_world_time)}"
                    )
                elif temporal_correction_attempts > 0:
                    logging_util.info(
                        f"✅ TEMPORAL_CORRECTION: Response accepted after {temporal_correction_attempts} correction(s)"
                    )
                break

            # Temporal violation detected!
            temporal_correction_attempts += 1

            if temporal_correction_attempts > MAX_TEMPORAL_CORRECTION_ATTEMPTS:
                # Max retries exceeded - log warning and accept the response anyway
                # NOTE: Correction FAILED - we're accepting a bad response, not a successful fix
                logging_util.warning(
                    f"❌ TEMPORAL_CORRECTION_FAILED: Max correction attempts ({MAX_TEMPORAL_CORRECTION_ATTEMPTS}) exceeded. "
                    f"Giving up and accepting response with backward time: {_format_world_time_for_prompt(new_world_time)} "
                    f"< {_format_world_time_for_prompt(old_world_time)}"
                )
                break

            # Extract new location for error message
            new_state_updates = (
                llm_response_obj.get_state_updates()
                if hasattr(llm_response_obj, "get_state_updates")
                else {}
            )
            new_location = new_state_updates.get("world_data", {}).get(
                "current_location_name", old_location
            )

            # Log the violation and retry
            logging_util.warning(
                f"🚨 TEMPORAL_VIOLATION (attempt {temporal_correction_attempts}/{MAX_TEMPORAL_CORRECTION_ATTEMPTS}): "
                f"Time went backward from {_format_world_time_for_prompt(old_world_time)} to "
                f"{_format_world_time_for_prompt(new_world_time)}. Requesting regeneration."
            )

            # Build correction prompt for next LLM call (does NOT overwrite user_input)
            llm_input = _build_temporal_correction_prompt(
                original_user_input,
                old_world_time,
                new_world_time,
                old_location,
                new_location,
            )

        # Convert LLMResponse to dict format for compatibility
        # Apply preventive guards to enforce continuity safeguards
        state_changes, prevention_extras = preventive_guards.enforce_preventive_guards(
            current_game_state, llm_response_obj, mode
        )

        # Allow LLMs to return a single timestamp string while we maintain the
        # structured world_time object expected by the engine.
        state_changes = _apply_timestamp_to_world_time(state_changes)

        # Normalize any world_time values without inventing new timestamps; the
        # LLM remains responsible for choosing timeline values.
        state_changes = world_time.ensure_progressive_world_time(
            state_changes,
            is_god_mode=is_god_mode,
        )
        new_world_time = state_changes.get("world_data", {}).get("world_time")

        # Add temporal violation error as god_mode_response for user-facing display
        # Note: new_world_time is already extracted in the temporal validation loop above
        temporal_violation_detected = _check_temporal_violation(
            old_world_time, new_world_time
        )

        if temporal_violation_detected and not is_god_mode:
            old_time_str = _format_world_time_for_prompt(old_world_time)
            new_time_str = _format_world_time_for_prompt(new_world_time)
            dice_retry_llm_call = bool(
                getattr(llm_response_obj, "processing_metadata", {}).get(
                    "dice_retry_llm_call"
                )
            )

            # User-facing error message as god_mode_response
            god_mode_response = (
                f"⚠️ **TEMPORAL ANOMALY DETECTED**\n\n"
                f"The AI generated a response where time moved backward:\n"
                f"- **Previous time:** {old_time_str}\n"
                f"- **Response time:** {new_time_str}\n\n"
                f"This may indicate the AI lost track of the story timeline. "
                f"The response was accepted but timeline consistency may be affected."
            )
            if dice_retry_llm_call:
                god_mode_response += (
                    "\n\n**Dice Retry Notice**\n"
                    "A dice integrity retry triggered an additional model call before this response. "
                    "If anything seems inconsistent, you can retry the action."
                )

            prevention_extras["god_mode_response"] = god_mode_response

            logging_util.warning(
                f"⚠️ TEMPORAL_VIOLATION surfaced to user: {new_time_str} < {old_time_str}"
            )

            prevention_extras["temporal_correction_warning"] = prevention_extras[
                "god_mode_response"
            ]
            prevention_extras["temporal_correction_attempts"] = 1

        # Add temporal correction warning if corrections were needed (legacy path when retries enabled)
        elif temporal_correction_attempts > 0:
            temporal_warning = _build_temporal_warning_message(
                temporal_correction_attempts
            )
            if temporal_correction_attempts > MAX_TEMPORAL_CORRECTION_ATTEMPTS:
                logging_util.warning(
                    f"⚠️ TEMPORAL_WARNING (exceeded): {temporal_correction_attempts} attempts, max was {MAX_TEMPORAL_CORRECTION_ATTEMPTS}"
                )
            else:
                logging_util.info(
                    f"✅ TEMPORAL_WARNING added to response: {temporal_correction_attempts} correction(s) fixed the issue"
                )

            prevention_extras["temporal_correction_warning"] = temporal_warning
            prevention_extras["temporal_correction_attempts"] = (
                temporal_correction_attempts
            )

        # Extract LLM-requested instruction hints for next turn
        # The LLM can signal it needs detailed sections (e.g., relationships, reputation)
        # via debug_info.meta.needs_detailed_instructions in its response
        llm_debug_info = llm_response_obj.get_debug_info() if hasattr(llm_response_obj, "get_debug_info") else {}
        # Wrap in dict as extract_llm_instruction_hints expects {"debug_info": {...}}
        instruction_hints = extract_llm_instruction_hints({"debug_info": llm_debug_info})
        # Always update pending_instruction_hints - either with new hints or empty list to clear
        # This ensures hints are consumed on the next turn and don't persist indefinitely
        state_changes["pending_instruction_hints"] = instruction_hints
        if instruction_hints:
            logging_util.info(
                f"📋 DYNAMIC_PROMPTS: LLM requested detailed sections for next turn: {instruction_hints}"
            )

        response = {
            "story": llm_response_obj.narrative_text,
            "state_changes": state_changes,
        }

        # Capture original time before update for accurate monotonicity validation
        # Note: current_game_state is a GameState instance (has to_dict() method)
        current_state_as_dict = current_game_state.to_dict()
        # Use `or {}` to handle both missing and explicitly-null world_data
        # CRITICAL: Deep-copy to prevent mutation by update_state_with_changes
        original_world_time = copy.deepcopy(
            (current_state_as_dict.get("world_data") or {}).get("world_time")
        )

        # Capture previous combat state for post-combat warning detection
        previous_combat_state = copy.deepcopy(current_state_as_dict.get("combat_state", {}))

        # Update game state with changes
        updated_game_state_dict = update_state_with_changes(
            current_state_as_dict, response.get("state_changes", {})
        )

        # Apply automatic combat cleanup (sync defeated enemies between combat_state and npc_data)
        # Named NPCs are preserved and marked dead for continuity, while generic enemies are deleted
        updated_game_state_dict = apply_automatic_combat_cleanup(
            updated_game_state_dict, response.get("state_changes", {})
        )

        # Validate and auto-correct XP/level and time consistency
        # Use `or {}` to handle both missing and explicitly-null world_data in state_changes
        new_world_time = (
            response.get("state_changes", {}).get("world_data") or {}
        ).get("world_time")
        # SERVER-SIDE ENFORCEMENT: Apply for any mode that can award XP/rewards
        # This ensures rewards_processed is set when combat ends, encounters complete, etc.
        # Pass original state for XP comparison (detects XP increases even without summary structures)
        if mode in (constants.MODE_REWARDS, constants.MODE_COMBAT, constants.MODE_CHARACTER):
            updated_game_state_dict = _enforce_rewards_processed_flag(
                updated_game_state_dict, original_state_dict=current_state_as_dict
            )

        # Validate and auto-correct state before persistence, capturing any corrections made
        updated_game_state_dict, state_corrections = validate_and_correct_state(
            updated_game_state_dict, previous_world_time=original_world_time, return_corrections=True
        )

        # If rewards are now pending but we did NOT run RewardsAgent, run it once
        # to ensure user-visible rewards output.
        # NOTE: This must happen BEFORE post-combat detection to avoid false-positive
        # "no XP awarded" warnings when RewardsAgent awards XP in the followup.
        try:
            updated_game_state_dict, llm_response_obj, prevention_extras = (
                await _process_rewards_followup(
                    mode=mode,
                    llm_response_obj=llm_response_obj,
                    updated_game_state_dict=updated_game_state_dict,
                    current_state_as_dict=current_state_as_dict,
                    original_world_time=original_world_time,
                    story_context=story_context,
                    selected_prompts=selected_prompts,
                    use_default_world=use_default_world,
                    user_id=user_id,
                    prevention_extras=prevention_extras,
                )
            )
        except Exception as e:
            logging_util.warning(f"⚠️ REWARDS_FOLLOWUP failed: {e}")

        # Re-validate state after rewards followup to capture any additional corrections
        # This ensures corrections from RewardsAgent state changes are surfaced to user
        updated_game_state_dict, followup_corrections = validate_and_correct_state(
            updated_game_state_dict, previous_world_time=original_world_time, return_corrections=True
        )
        # Merge corrections (deduplicate since some may overlap)
        all_corrections = state_corrections + [c for c in followup_corrections if c not in state_corrections]

        # Detect post-combat issues AFTER rewards followup to avoid false positives
        # when RewardsAgent awards XP during the followup
        updated_game_state_obj = GameState.from_dict(updated_game_state_dict)
        post_combat_warnings = []
        if updated_game_state_obj:
            # Compare final state against original to detect if XP was ever awarded
            final_pc = updated_game_state_dict.get("player_character_data", {})
            original_pc = current_state_as_dict.get("player_character_data", {})
            final_xp = _extract_xp_from_player_data(final_pc)
            original_xp = _extract_xp_from_player_data(original_pc)

            # Only warn if XP didn't increase at all (including from rewards followup)
            xp_increased = final_xp > original_xp
            if not xp_increased:
                post_combat_warnings = updated_game_state_obj.detect_post_combat_issues(
                    previous_combat_state, response.get("state_changes", {})
                )

        # Combine all system warnings (including any from rewards followup)
        rewards_corrections = prevention_extras.get("rewards_corrections", [])
        system_warnings = all_corrections + rewards_corrections + post_combat_warnings

        # Increment player turn counter for non-GOD mode actions
        if not is_god_mode:
            current_turn = updated_game_state_dict.get("player_turn", 0)
            updated_game_state_dict["player_turn"] = current_turn + 1
        else:
            # GOD MODE: Process directives from LLM response
            # The GodModeAgent analyzes the user's message and returns directives
            # Format: {"directives": {"add": ["rule1", ...], "drop": ["rule2", ...]}}
            early_structured = structured_fields_utils.extract_structured_fields(
                llm_response_obj
            )
            llm_directives = early_structured.get("directives", {})
            if not isinstance(llm_directives, dict):
                llm_directives = {}

            def _normalize_directive_list(value: Any) -> list[str]:
                if value is None:
                    return []
                if isinstance(value, str):
                    return [value] if value.strip() else []
                if isinstance(value, dict):
                    rule = value.get("rule")
                    return [rule] if isinstance(rule, str) and rule.strip() else []
                if isinstance(value, list):
                    normalized: list[str] = []
                    for item in value:
                        if isinstance(item, str):
                            if item.strip():
                                normalized.append(item)
                        elif isinstance(item, dict):
                            rule = item.get("rule")
                            if isinstance(rule, str) and rule.strip():
                                normalized.append(rule)
                    return normalized
                return []

            directives_to_add = _normalize_directive_list(llm_directives.get("add"))
            directives_to_drop = _normalize_directive_list(llm_directives.get("drop"))

            ccs = updated_game_state_dict.setdefault("custom_campaign_state", {}) or {}
            directives_list = ccs.setdefault("god_mode_directives", [])

            # Process directives to drop (remove matching rules)
            if directives_to_drop:
                drop_lower = [d.strip().lower() for d in directives_to_drop if d]
                original_count = len(directives_list)

                def _get_rule_lower(d: Any) -> str:
                    """Safely extract and lowercase a rule, handling None values."""
                    if isinstance(d, dict):
                        rule = d.get("rule")
                        return (rule.strip().lower() if isinstance(rule, str) else "")
                    return str(d).strip().lower() if d else ""

                directives_list[:] = [
                    d for d in directives_list
                    if _get_rule_lower(d) not in drop_lower
                ]
                dropped_count = original_count - len(directives_list)
                if dropped_count > 0:
                    logging_util.info(f"GOD MODE: Dropped {dropped_count} directives")

            # Process directives to add (avoid duplicates, case-insensitive)
            for new_rule in directives_to_add:
                if not new_rule or not isinstance(new_rule, str):
                    continue
                # Strip whitespace from new rule
                new_rule_clean = new_rule.strip()
                if not new_rule_clean:
                    continue
                # Case-insensitive duplicate check
                existing_rules_lower = [
                    (d.get("rule", "").strip().lower() if isinstance(d, dict) else str(d).strip().lower())
                    for d in directives_list
                    if (isinstance(d, dict) and d.get("rule")) or (not isinstance(d, dict) and d)
                ]
                if new_rule_clean.lower() not in existing_rules_lower:
                    directives_list.append({
                        "rule": new_rule_clean,
                        "added": datetime.now(timezone.utc).isoformat(),
                    })
                    logging_util.info(f"GOD MODE DIRECTIVE ADDED: {new_rule_clean}")

        # Annotate world_events entries with turn/scene numbers for UI display
        player_turn = updated_game_state_dict.get("player_turn", 1)
        updated_game_state_dict = annotate_world_events_with_turn_scene(
            updated_game_state_dict, player_turn
        )

        # Update in Firestore (blocking I/O - run in thread)
        await asyncio.to_thread(
            firestore_service.update_campaign_game_state,
            user_id,
            campaign_id,
            updated_game_state_dict,
        )

        # Save story entries to Firestore (blocking I/O - run in thread)
        # First save the user input
        await asyncio.to_thread(
            firestore_service.add_story_entry,
            user_id,
            campaign_id,
            constants.ACTOR_USER,
            user_input,
            mode,
        )

        # Then save the AI response with structured fields if available
        ai_response_text = llm_response_obj.narrative_text

        # Extract structured fields from AI response for storage
        structured_fields = _ensure_session_header_resources(
            structured_fields_utils.extract_structured_fields(llm_response_obj),
            updated_game_state_dict,
        )
        structured_fields.update(prevention_extras)

        # Annotate THIS TURN's world_events (from LLM response) with turn/scene numbers
        # NOTE: We annotate structured_fields directly, NOT game_state.world_events
        # game_state.world_events is CUMULATIVE (contains all historical events)
        # structured_fields.world_events contains only THIS TURN's new events
        # BUG FIX: Previously copied cumulative game_state.world_events causing duplicates
        llm_world_events = structured_fields.get("world_events")
        if not llm_world_events:
            # Check state_updates for world_events
            llm_world_events = structured_fields.get("state_updates", {}).get(
                "world_events"
            )

        if llm_world_events and isinstance(llm_world_events, dict):
            # Annotate the LLM response's world_events with current turn/scene
            annotate_world_events_with_turn_scene(
                {"world_events": llm_world_events}, player_turn
            )
            # Ensure it's in structured_fields for storage
            structured_fields["world_events"] = llm_world_events
            if "state_updates" in structured_fields:
                structured_fields["state_updates"]["world_events"] = llm_world_events

        await asyncio.to_thread(
            firestore_service.add_story_entry,
            user_id,
            campaign_id,
            constants.ACTOR_GEMINI,
            ai_response_text,
            None,  # mode
            structured_fields,  # structured_fields
        )

        # Get debug mode for narrative text processing
        debug_mode = (
            current_game_state.debug_mode
            if hasattr(current_game_state, "debug_mode")
            else False
        )

        # Extract narrative text with proper debug mode handling
        if hasattr(llm_response_obj, "get_narrative_text"):
            final_narrative = llm_response_obj.get_narrative_text(debug_mode=debug_mode)
        else:
            final_narrative = llm_response_obj.narrative_text

        # Note: With "text" field fix, empty narratives should now be properly handled
        # by the translation layer without needing fallback messages

        # Calculate sequence_id (critical missing field)
        # AI response should be next sequential number after user input
        # User input gets len(story_context) + 1, AI response gets len(story_context) + 2
        sequence_id = len(story_context) + 2

        # Calculate user_scene_number: count of AI responses (includes GOD mode)
        # This is different from player_turn which skips GOD mode
        user_scene_number = (
            sum(1 for entry in story_context if entry.get("actor") == "gemini") + 1
        )

        # Extract structured fields from LLM response (critical missing fields)
        structured_response = getattr(llm_response_obj, "structured_response", None)

        # Process story for display (convert narrative text to story entries format)
        # Use "text" field to match translation layer expectations in main.py
        story_entries = [{"text": final_narrative}]
        processed_story = process_story_for_display(story_entries, debug_mode)

        # Build comprehensive response with all frontend-required fields
        unified_response = {
            KEY_SUCCESS: True,
            "story": processed_story,
            "narrative": final_narrative,  # Add for frontend compatibility
            "response": final_narrative,  # Fallback for older frontend versions
            "game_state": updated_game_state_dict,
            "mode": mode,
            "user_input": user_input,
            "state_cleaned": was_cleaned,
            "entries_cleaned": num_cleaned,
            # CRITICAL: Add missing structured fields that frontend expects
            "sequence_id": sequence_id,
            "user_scene_number": user_scene_number,  # Scene number for current AI response: count of existing Gemini responses + 1
            "debug_mode": debug_mode,  # Add debug_mode for test compatibility
        }

        # Include state fields only when debug mode is enabled (shows MORE info)
        if debug_mode:
            unified_response["state_updates"] = response.get("state_changes", {})

        # Add structured response fields if available
        if structured_response:
            # entities_mentioned only in debug mode
            if debug_mode and hasattr(structured_response, "entities_mentioned"):
                unified_response["entities_mentioned"] = (
                    structured_response.entities_mentioned
                )
            if hasattr(structured_response, "location_confirmed"):
                unified_response["location_confirmed"] = (
                    structured_response.location_confirmed
                )
            if hasattr(structured_response, "session_header"):
                unified_response["session_header"] = structured_response.session_header
            if hasattr(structured_response, "planning_block"):
                unified_response["planning_block"] = structured_response.planning_block
            if hasattr(structured_response, "dice_rolls"):
                unified_response["dice_rolls"] = structured_response.dice_rolls
            if hasattr(structured_response, "dice_audit_events"):
                unified_response["dice_audit_events"] = (
                    structured_response.dice_audit_events
                )
            if hasattr(structured_response, "resources"):
                unified_response["resources"] = structured_response.resources
            if hasattr(structured_response, "rewards_box"):
                unified_response["rewards_box"] = structured_response.rewards_box
            # debug_info only in debug mode
            if debug_mode and hasattr(structured_response, "debug_info"):
                unified_response["debug_info"] = structured_response.debug_info
            # God mode response (when applicable)
            if (
                hasattr(structured_response, "god_mode_response")
                and structured_response.god_mode_response
            ):
                unified_response["god_mode_response"] = (
                    structured_response.god_mode_response
                )

        capture_evidence = os.getenv("CAPTURE_EVIDENCE", "").lower() == "true"
        if capture_evidence:
            metadata = getattr(llm_response_obj, "processing_metadata", {}) or {}
            llm_provider = metadata.get("llm_provider") or getattr(
                llm_response_obj, "provider", None
            )
            llm_model = metadata.get("llm_model") or getattr(
                llm_response_obj, "model", None
            )
            if llm_provider:
                unified_response["llm_provider"] = llm_provider
            if llm_model:
                unified_response["llm_model"] = llm_model
            if "dice_strategy" in metadata:
                unified_response["dice_strategy"] = metadata["dice_strategy"]
            if "raw_response_text" in metadata:
                unified_response["raw_llm_response"] = metadata["raw_response_text"]
            if "tool_results" in metadata:
                unified_response["tool_results"] = metadata["tool_results"]
            if "tool_requests_executed" in metadata:
                unified_response["tool_requests_executed"] = metadata[
                    "tool_requests_executed"
                ]
            # Add equipment_display if present (deterministic extraction from game_state)
            if "equipment_display" in metadata:
                unified_response["equipment_display"] = metadata["equipment_display"]

        # Always check for equipment_display even outside capture_evidence mode
        metadata = getattr(llm_response_obj, "processing_metadata", {}) or {}
        if (
            "equipment_display" in metadata
            and "equipment_display" not in unified_response
        ):
            unified_response["equipment_display"] = metadata["equipment_display"]

        if prevention_extras.get("god_mode_response"):
            # Prefer synthesized god mode responses from preventive guards when present
            # because they fill gaps left by the model.
            unified_response["god_mode_response"] = prevention_extras[
                "god_mode_response"
            ]

        # Add temporal correction warning to response if present
        if prevention_extras.get("temporal_correction_warning"):
            unified_response["temporal_correction_warning"] = prevention_extras[
                "temporal_correction_warning"
            ]
            unified_response["temporal_correction_attempts"] = prevention_extras.get(
                "temporal_correction_attempts", 0
            )

        # Add system warnings from validation corrections and post-combat checks
        if system_warnings:
            unified_response["system_warnings"] = system_warnings
            # Log warnings for visibility
            for warning in system_warnings:
                logging_util.warning(f"SYSTEM WARNING: {warning}")

        # Track story mode sequence ID for character mode
        if mode == constants.MODE_CHARACTER:
            story_id_update = {
                "custom_campaign_state": {"last_story_mode_sequence_id": sequence_id}
            }
            # Merge this update with existing state changes from Gemini response
            current_state_changes = response.get("state_changes", {})
            merged_state_changes = update_state_with_changes(
                current_state_changes, story_id_update
            )

            # Include state fields only when debug mode is enabled (shows MORE info)
            if debug_mode:
                unified_response["state_updates"] = merged_state_changes

            # Also update the game state dict that was already saved
            final_game_state_dict = update_state_with_changes(
                updated_game_state_dict, story_id_update
            )
            # Validate the final state before persisting
            final_game_state_dict = validate_game_state_updates(final_game_state_dict)
            # Blocking I/O - run in thread
            await asyncio.to_thread(
                firestore_service.update_campaign_game_state,
                user_id,
                campaign_id,
                final_game_state_dict,
            )
            unified_response["game_state"] = final_game_state_dict

        return unified_response

    except ValidationError:
        # Re-raise ValidationError so mcp_api.py can apply god mode recovery
        raise
    except Exception as e:
        logging_util.error(f"Process action failed: {e}")
        return {KEY_ERROR: f"Failed to process action: {str(e)}"}
    finally:
        logging_util.set_campaign_id(None)


async def get_campaign_state_unified(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    Unified campaign state retrieval logic for both Flask and MCP.

    Uses asyncio.to_thread() for blocking I/O operations to prevent blocking
    the shared event loop.

    Args:
        request_data: Dictionary containing:
            - user_id: User ID
            - campaign_id: Campaign ID
            - include_story: Whether to include processed story (optional, default False)

    Returns:
        Dictionary with success/error status and campaign state
    """
    try:
        # Extract parameters
        user_id = request_data.get("user_id")
        campaign_id = request_data.get("campaign_id")
        include_story = request_data.get("include_story", False)

        # Validate required fields
        if not user_id:
            return {KEY_ERROR: "User ID is required"}
        if not campaign_id:
            return {KEY_ERROR: "Campaign ID is required"}

        # Get campaign metadata and story (blocking I/O - run in thread)
        campaign_data, story = await asyncio.to_thread(
            firestore_service.get_campaign_by_id, user_id, campaign_id
        )
        if not campaign_data:
            return {KEY_ERROR: "Campaign not found", "status_code": 404}

        # Clean JSON artifacts from campaign description if present
        if campaign_data and "description" in campaign_data:
            campaign_data["description"] = clean_json_artifacts(
                campaign_data["description"]
            )

        # Also clean other text fields that might have JSON artifacts
        text_fields_to_clean = ["prompt", "title"]
        for field in text_fields_to_clean:
            if (
                campaign_data
                and field in campaign_data
                and isinstance(campaign_data[field], str)
            ):
                campaign_data[field] = clean_json_artifacts(campaign_data[field])

        # Get game state and apply user settings (blocking I/O - run in thread)
        game_state, was_cleaned, num_cleaned = await asyncio.to_thread(
            _prepare_game_state, user_id, campaign_id
        )
        game_state_dict = game_state.to_dict()

        # Get debug mode from user settings and apply to game state (blocking I/O)
        user_settings = await asyncio.to_thread(get_user_settings, user_id)
        debug_mode = user_settings.get("debug_mode", False) if user_settings else False
        game_state_dict["debug_mode"] = debug_mode

        result = {
            KEY_SUCCESS: True,
            "campaign": campaign_data,
            "game_state": game_state_dict,
            "state_cleaned": was_cleaned,
            "entries_cleaned": num_cleaned,
        }

        # Include processed story if requested (for Flask route compatibility)
        if include_story and story:
            processed_story = process_story_for_display(story, debug_mode)

            # Strip game state fields when debug mode is OFF
            if not debug_mode:
                processed_story = _strip_game_state_fields(processed_story)

            result["story"] = processed_story

        return result

    except Exception as e:
        logging_util.error(f"Failed to get campaign state: {e}")
        return {KEY_ERROR: f"Failed to get campaign state: {str(e)}"}


async def update_campaign_unified(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    Unified campaign update logic for both Flask and MCP.

    Uses asyncio.to_thread() for blocking I/O operations to prevent blocking
    the shared event loop.

    Args:
        request_data: Dictionary containing:
            - user_id: User ID
            - campaign_id: Campaign ID
            - updates: Dictionary of updates to apply

    Returns:
        Dictionary with success/error status
    """
    try:
        # Extract parameters
        user_id = request_data.get("user_id")
        campaign_id = request_data.get("campaign_id")
        updates = request_data.get("updates", {})

        # Validate required fields
        if not user_id:
            return {KEY_ERROR: "User ID is required"}
        if not campaign_id:
            return {KEY_ERROR: "Campaign ID is required"}
        if not updates:
            return {KEY_ERROR: "Updates are required"}

        # Check if campaign exists (blocking I/O - run in thread)
        campaign_data, _ = await asyncio.to_thread(
            firestore_service.get_campaign_by_id, user_id, campaign_id
        )
        if not campaign_data:
            return {KEY_ERROR: "Campaign not found", "status_code": 404}

        # Apply updates (blocking I/O - run in thread)
        await asyncio.to_thread(
            firestore_service.update_campaign, user_id, campaign_id, updates
        )

        return {
            KEY_SUCCESS: True,
            "message": f"Campaign updated with {len(updates)} changes",
        }

    except Exception as e:
        logging_util.error(f"Failed to update campaign: {e}")
        return {KEY_ERROR: f"Failed to update campaign: {str(e)}"}


async def export_campaign_unified(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    Unified campaign export logic for both Flask and MCP.

    Uses asyncio.to_thread() for blocking I/O operations to prevent blocking
    the shared event loop.

    Args:
        request_data: Dictionary containing:
            - user_id: User ID
            - campaign_id: Campaign ID
            - format: Export format ('pdf', 'docx', 'txt')
            - filename: Optional filename

    Returns:
        Dictionary with success/error status and export info
    """
    try:
        # Extract parameters
        user_id = request_data.get("user_id")
        campaign_id = request_data.get("campaign_id")
        export_format = request_data.get("format", "pdf").lower()
        filename = request_data.get("filename")

        # Validate required fields
        if not user_id:
            return {KEY_ERROR: "User ID is required"}
        if not campaign_id:
            return {KEY_ERROR: "Campaign ID is required"}
        if export_format not in ["pdf", "docx", "txt"]:
            return {KEY_ERROR: "Format must be one of: pdf, docx, txt"}

        # Get campaign data and story (blocking I/O - run in thread)
        campaign_data, story_context = await asyncio.to_thread(
            firestore_service.get_campaign_by_id, user_id, campaign_id
        )
        if not campaign_data:
            return {KEY_ERROR: "Campaign not found", "status_code": 404}

        # Get campaign title
        campaign_title = campaign_data.get("title", "Untitled Campaign")

        # Generate file path
        temp_dir = os.path.join(tempfile.gettempdir(), "campaign_exports")
        os.makedirs(temp_dir, exist_ok=True)

        if filename:
            safe_file_path = os.path.join(temp_dir, filename)
        else:
            safe_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.{export_format}")

        # Convert story context to text format
        story_parts = []
        for entry in story_context:
            actor = entry.get("actor", "unknown")
            text = entry.get("text", "")
            mode = entry.get("mode")

            if actor == "gemini":
                label = "Game Master"
            else:
                label = "God Mode" if mode == "god" else "Player"
            story_parts.append(f"{label}:\n{text}")
        story_text = "\n\n".join(story_parts)

        # Generate export file
        try:
            if export_format == "pdf":
                await asyncio.to_thread(
                    document_generator.generate_pdf,
                    story_text,
                    safe_file_path,
                    campaign_title,
                )
            elif export_format == "docx":
                await asyncio.to_thread(
                    document_generator.generate_docx,
                    story_text,
                    safe_file_path,
                    campaign_title,
                )
            elif export_format == "txt":
                await asyncio.to_thread(
                    document_generator.generate_txt,
                    story_text,
                    safe_file_path,
                    campaign_title,
                )

            return {
                KEY_SUCCESS: True,
                "export_path": safe_file_path,
                "format": export_format,
                "campaign_title": campaign_title,
            }
        except Exception as e:
            logging_util.error(f"Document generation failed: {e}")
            return {KEY_ERROR: f"Document generation failed: {str(e)}"}

    except Exception as e:
        logging_util.error(f"Failed to export campaign: {e}")
        return {KEY_ERROR: f"Failed to export campaign: {str(e)}"}


def get_campaigns_for_user_list(user_id: UserId) -> list[dict[str, Any]]:
    """Get campaigns list for a user - synchronous version for tests."""
    return firestore_service.get_campaigns_for_user(user_id)


async def get_campaigns_list_unified(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    Unified campaigns list retrieval logic for both Flask and MCP.

    Args:
        request_data: Dictionary containing:
            - user_id: User ID
            - limit: Optional maximum number of campaigns to return
            - sort_by: Optional sort field ('created_at' or 'last_played')

    Returns:
        Dictionary with success/error status and campaigns list
    """
    try:
        # Extract parameters
        user_id = request_data.get("user_id")
        limit = request_data.get("limit")
        sort_by = request_data.get("sort_by", "last_played")

        # Validate required fields
        if not user_id:
            return {KEY_ERROR: "User ID is required"}

        # Validate limit parameter with proper error handling
        if limit is not None:
            try:
                limit = int(limit) if limit else None
            except (ValueError, TypeError):
                return {KEY_ERROR: "Invalid limit parameter - must be a valid integer"}

        # Validate sort_by parameter
        valid_sort_fields = ["created_at", "last_played"]
        if sort_by and sort_by not in valid_sort_fields:
            return {
                KEY_ERROR: f"Invalid sort_by parameter - must be one of: {', '.join(valid_sort_fields)}"
            }

        # Get campaigns with pagination and sorting (blocking I/O - run in thread)
        campaigns = await asyncio.to_thread(
            firestore_service.get_campaigns_for_user, user_id, limit, sort_by
        )

        # Clean JSON artifacts from campaign text fields
        if campaigns:
            text_fields_to_clean = ["description", "prompt", "title"]
            for campaign in campaigns:
                for field in text_fields_to_clean:
                    if field in campaign and isinstance(campaign[field], str):
                        campaign[field] = clean_json_artifacts(campaign[field])

        return {
            KEY_SUCCESS: True,
            "campaigns": campaigns,
        }

    except Exception as e:
        logging_util.error(f"Failed to get campaigns: {e}")
        return {KEY_ERROR: f"Failed to get campaigns: {str(e)}"}


def create_error_response(message: str, status_code: int = 400) -> dict[str, Any]:
    """
    Create standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code (for Flask compatibility)

    Returns:
        Standardized error response dictionary
    """
    return {
        KEY_ERROR: message,
        "status_code": status_code,
        KEY_SUCCESS: False,
    }


def create_success_response(data: dict[str, Any]) -> dict[str, Any]:
    """
    Create standardized success response.

    Args:
        data: Response data

    Returns:
        Standardized success response dictionary
    """
    response = {KEY_SUCCESS: True}
    response.update(data)
    return response


async def get_user_settings_unified(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    Unified user settings retrieval for both Flask and MCP.

    Uses asyncio.to_thread() for blocking I/O operations to prevent blocking
    the shared event loop.

    Args:
        request_data: Dictionary containing:
            - user_id: User ID

    Returns:
        Dictionary with user settings or default settings
    """
    try:
        user_id = request_data.get("user_id")
        if not user_id:
            return create_error_response("User ID is required")

        # Blocking I/O - run in thread
        settings = await asyncio.to_thread(get_user_settings, user_id)

        # Return default settings for new users or database errors
        if settings is None:
            settings = {
                "debug_mode": constants.DEFAULT_DEBUG_MODE,
                "gemini_model": constants.DEFAULT_GEMINI_MODEL,  # Default model (supports code_execution + JSON)
                "llm_provider": constants.DEFAULT_LLM_PROVIDER,
                "openrouter_model": constants.DEFAULT_OPENROUTER_MODEL,
                "cerebras_model": constants.DEFAULT_CEREBRAS_MODEL,
            }

        settings.setdefault("llm_provider", constants.DEFAULT_LLM_PROVIDER)
        settings.setdefault("gemini_model", constants.DEFAULT_GEMINI_MODEL)
        settings.setdefault("openrouter_model", constants.DEFAULT_OPENROUTER_MODEL)
        settings.setdefault("cerebras_model", constants.DEFAULT_CEREBRAS_MODEL)

        return create_success_response(settings)

    except Exception as e:
        logging_util.error(f"Failed to get user settings: {e}")
        return create_error_response(f"Failed to get user settings: {str(e)}")


async def update_user_settings_unified(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    Unified user settings update for both Flask and MCP.

    Uses asyncio.to_thread() for blocking I/O operations to prevent blocking
    the shared event loop.

    Args:
        request_data: Dictionary containing:
            - user_id: User ID
            - settings: Dictionary of settings to update

    Returns:
        Dictionary with success status and updated settings
    """
    try:
        user_id = request_data.get("user_id")
        settings_data = request_data.get("settings")

        if not user_id:
            return create_error_response("User ID is required")

        if not isinstance(settings_data, dict):
            return create_error_response("Invalid request format")

        if not settings_data:
            return create_error_response("No data provided")

        settings_to_update = {}

        # Validate provider selection
        if "llm_provider" in settings_data:
            provider = settings_data["llm_provider"]
            if provider not in constants.ALLOWED_LLM_PROVIDERS:
                return create_error_response("Invalid provider selection")
            settings_to_update["llm_provider"] = provider

        # Validate gemini_model if provided
        if "gemini_model" in settings_data:
            model = settings_data["gemini_model"]
            if not isinstance(model, str):
                return create_error_response("Invalid model selection")

            # Case-insensitive validation to prevent case manipulation attacks
            model_lower = model.lower()
            allowed_models = {
                m.lower()
                for m in (
                    constants.ALLOWED_GEMINI_MODELS + constants.PREMIUM_GEMINI_MODELS
                )
            }
            # Also allow legacy models that have a mapping
            allowed_models.update(
                k.lower() for k in constants.GEMINI_MODEL_MAPPING.keys()
            )
            if model_lower not in allowed_models:
                return create_error_response("Invalid model selection")
            settings_to_update["gemini_model"] = model

        if "openrouter_model" in settings_data:
            model = settings_data["openrouter_model"]
            if not isinstance(model, str):
                return create_error_response("Invalid model selection")

            allowed_openrouter = {
                m.lower() for m in constants.ALLOWED_OPENROUTER_MODELS
            }
            if model.lower() not in allowed_openrouter:
                return create_error_response("Invalid model selection")
            settings_to_update["openrouter_model"] = model

        if "cerebras_model" in settings_data:
            model = settings_data["cerebras_model"]
            if not isinstance(model, str):
                return create_error_response("Invalid model selection")

            allowed_cerebras = {m.lower() for m in constants.ALLOWED_CEREBRAS_MODELS}
            if model.lower() not in allowed_cerebras:
                return create_error_response("Invalid model selection")
            settings_to_update["cerebras_model"] = model

        # Validate debug_mode if provided
        if "debug_mode" in settings_data:
            debug_mode = settings_data["debug_mode"]
            if not isinstance(debug_mode, bool):
                return create_error_response("Invalid debug mode value")
            settings_to_update["debug_mode"] = debug_mode

        # Update settings if there are any valid changes (blocking I/O - run in thread)
        if settings_to_update:
            await asyncio.to_thread(
                firestore_service.update_user_settings, user_id, settings_to_update
            )
            logging_util.info(
                f"Updated user settings for {user_id}: {settings_to_update}"
            )

        # Get updated settings to return (blocking I/O - run in thread)
        updated_settings = await asyncio.to_thread(get_user_settings, user_id) or {}

        return create_success_response({"settings": updated_settings})

    except Exception as e:
        logging_util.error(f"Failed to update user settings: {e}")
        return create_error_response(f"Failed to update user settings: {str(e)}")


def apply_automatic_combat_cleanup(
    updated_state_dict: dict[str, Any], _proposed_changes: dict[str, Any]
) -> dict[str, Any]:
    """
    Automatically cleans up defeated enemies from combat state when combat updates are applied.

    This function should be called after any state update that modifies combat_state.
    It identifies defeated enemies (HP <= 0) and removes them from both combat_state
    and npc_data to maintain consistency.

    Args:
        updated_state_dict: The state dictionary after applying proposed changes
        proposed_changes: The original changes dict to check if combat_state was modified

    Returns:
        Updated state dictionary with defeated enemies cleaned up
    """
    # CRITICAL BUG FIX: Handle case where GameState.from_dict returns None
    temp_game_state = GameState.from_dict(updated_state_dict)
    if temp_game_state is None:
        logging_util.error(
            "COMBAT CLEANUP ERROR: GameState.from_dict returned None, returning original state"
        )
        return updated_state_dict

    # Check if we have combatants data to potentially clean up
    combatants = temp_game_state.combat_state.get("combatants", {})
    if not combatants:
        logging_util.info("COMBAT CLEANUP CHECK: No combatants found, skipping cleanup")
        return updated_state_dict

    # CRITICAL FIX: Always attempt cleanup if combatants exist
    # This handles ALL cases:
    # 1. Combat ongoing with new defeats
    # 2. Combat ending with pre-existing defeats
    # 3. State updates without explicit combat_state changes but with defeated enemies
    logging_util.info(
        f"COMBAT CLEANUP CHECK: Found {len(combatants)} combatants, scanning for defeated enemies..."
    )

    # Perform cleanup - this always runs regardless of proposed_changes content
    defeated_enemies = temp_game_state.cleanup_defeated_enemies()
    if defeated_enemies:
        logging_util.info(
            f"AUTOMATIC CLEANUP: Defeated enemies removed: {defeated_enemies}"
        )
        # Return the updated state dict from the game state that had cleanup applied
        return temp_game_state.to_dict()
    logging_util.info("AUTOMATIC CLEANUP: No defeated enemies found to clean up")
    # Return the original state since no cleanup was needed
    return updated_state_dict


def format_game_state_updates(updates: dict[str, Any], for_html: bool = False) -> str:
    """Formats a dictionary of game state updates into a readable string, counting the number of leaf-node changes."""
    if not updates:
        return "No state updates."

    log_lines: list[str] = []

    def recurse_items(d: dict[str, Any], prefix: str = "") -> None:
        for key, value in d.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                recurse_items(value, prefix=path)
            else:
                log_lines.append(f"{path}: {json.dumps(value)}")

    recurse_items(updates)

    count = len(log_lines)
    if count == 0:
        return "No effective state updates were made."

    header = f"Game state updated ({count} {'entry' if count == 1 else 'entries'}):"

    if for_html:
        # Create an HTML list for the chat response
        items_html = "".join([f"<li><code>{line}</code></li>" for line in log_lines])
        return f"{header}<ul>{items_html}</ul>"
    # Create a plain text list for server logs
    items_text = "\n".join([f"  - {line}" for line in log_lines])
    return f"{header}\n{items_text}"


def parse_set_command(payload_str: str) -> dict[str, Any]:
    """
    Parses a multi-line string of `key.path = value` into a nested
    dictionary of proposed changes. Handles multiple .append operations correctly.
    """
    proposed_changes: dict[str, Any] = {}
    append_ops: dict[str, list[Any]] = collections.defaultdict(list)

    for line_raw in payload_str.strip().splitlines():
        line = line_raw.strip()
        if not line or "=" not in line:
            continue

        key_path, value_str = line.split("=", 1)
        key_path = key_path.strip()
        value_str = value_str.strip()

        try:
            value = json.loads(value_str)
        except json.JSONDecodeError:
            logging_util.warning(
                f"Skipping line in SET command due to invalid JSON value: {line}"
            )
            continue

        # Handle .append operations
        if key_path.endswith(".append"):
            base_key = key_path[:-7]  # Remove '.append'
            append_ops[base_key].append(value)
        else:
            # Regular assignment
            keys = key_path.split(".")
            current = proposed_changes
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value

    # Process append operations
    for base_key, values in append_ops.items():
        keys = base_key.split(".")
        current = proposed_changes
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        final_key = keys[-1]
        if final_key not in current:
            current[final_key] = []
        elif not isinstance(current[final_key], list):
            current[final_key] = [current[final_key]]

        current[final_key].extend(values)

    return proposed_changes


def _handle_ask_state_command(
    user_input: str,
    current_game_state: GameState,
    user_id: UserId,
    campaign_id: CampaignId,
) -> dict[str, Any] | None:
    """
    Handle GOD_ASK_STATE command.

    Returns:
        Response dict or None if not ASK_STATE command
    """
    god_ask_state_command = "GOD_ASK_STATE"

    if user_input.strip() != god_ask_state_command:
        return None

    game_state_dict = current_game_state.to_dict()
    game_state_json = json.dumps(game_state_dict, indent=2, default=str)

    firestore_service.add_story_entry(
        user_id, campaign_id, constants.ACTOR_USER, user_input, constants.MODE_CHARACTER
    )

    response_text = f"```json\n{game_state_json}\n```"
    return {
        KEY_SUCCESS: True,
        KEY_RESPONSE: response_text,
        "game_state": game_state_dict,
    }


def _handle_set_command(
    user_input: str,
    current_game_state: GameState,
    user_id: UserId,
    campaign_id: CampaignId,
) -> dict[str, Any] | None:
    """
    Handle GOD_MODE_SET command.

    Args:
        user_input: User input string
        current_game_state: Current GameState object
        user_id: User ID
        campaign_id: Campaign ID

    Returns:
        Response dict or None if not a SET command
    """
    god_mode_set_command = "GOD_MODE_SET:"
    user_input_stripped = user_input.strip()

    if not user_input_stripped.startswith(god_mode_set_command):
        return None

    payload_str = user_input_stripped[len(god_mode_set_command) :]
    logging_util.info(f"--- GOD_MODE_SET received for campaign {campaign_id} ---")
    logging_util.info(f"GOD_MODE_SET raw payload:\n---\n{payload_str}\n---")

    proposed_changes = parse_set_command(payload_str)
    # Enhanced logging with proper truncation
    logging_util.info(
        f"GOD_MODE_SET parsed changes to be merged:\n{_truncate_log_json(proposed_changes, json_serializer=json_default_serializer)}"
    )

    if not proposed_changes:
        logging_util.warning("GOD_MODE_SET command resulted in no valid changes.")
        return {
            KEY_SUCCESS: True,
            KEY_RESPONSE: "[System Message: The GOD_MODE_SET command was received, but contained no valid instructions or was empty.]",
        }

    current_state_dict_before_update = current_game_state.to_dict()
    logging_util.info(
        f"GOD_MODE_SET state BEFORE update: {current_state_dict_before_update}"
    )

    # Capture original time before update for accurate monotonicity validation
    # Note: current_game_state is a GameState instance, use dict version
    # Use `or {}` to handle both missing and explicitly-null world_data
    # CRITICAL: Deep-copy to prevent mutation by update_state_with_changes
    original_world_time = copy.deepcopy(
        (current_state_dict_before_update.get("world_data") or {}).get("world_time")
    )

    updated_state = update_state_with_changes(
        current_state_dict_before_update, proposed_changes
    )
    updated_state = apply_automatic_combat_cleanup(updated_state, proposed_changes)

    # Validate XP/level and time consistency before persisting
    # Use `or {}` to handle both missing and explicitly-null world_data
    new_world_time = (proposed_changes.get("world_data") or {}).get("world_time")
    updated_state = validate_game_state_updates(
        updated_state, new_time=new_world_time, original_time=original_world_time
    )

    logging_util.info(
        f"GOD_MODE_SET state AFTER update:\n{_truncate_log_json(updated_state, json_serializer=json_default_serializer)}"
    )

    # Validate and auto-correct state before persistence
    updated_state = validate_and_correct_state(
        updated_state, previous_world_time=original_world_time
    )

    firestore_service.update_campaign_game_state(user_id, campaign_id, updated_state)

    # Log the formatted changes for both server and chat
    log_message_for_log = format_game_state_updates(proposed_changes, for_html=False)
    logging_util.info(
        f"GOD_MODE_SET changes applied for campaign {campaign_id}:\n{log_message_for_log}"
    )

    log_message_for_chat = format_game_state_updates(proposed_changes, for_html=True)

    logging_util.info(f"--- GOD_MODE_SET for campaign {campaign_id} complete ---")

    return {
        KEY_SUCCESS: True,
        KEY_RESPONSE: f"[System Message]<br>{log_message_for_chat}",
    }


def _handle_update_state_command(
    user_input: str, user_id: UserId, campaign_id: CampaignId
) -> dict[str, Any] | None:
    """
    Handle GOD_MODE_UPDATE_STATE command.

    Returns:
        Response dict or None if not UPDATE_STATE command
    """
    god_mode_update_state_command = "GOD_MODE_UPDATE_STATE:"

    if not user_input.strip().startswith(god_mode_update_state_command):
        return None

    json_payload = user_input.strip()[len(god_mode_update_state_command) :]
    try:
        state_changes = json.loads(json_payload)
        if not isinstance(state_changes, dict):
            raise ValueError("Payload is not a JSON object.")

        # Fetch the current state as a dictionary
        current_game_state = firestore_service.get_campaign_game_state(
            user_id, campaign_id
        )
        if not current_game_state:
            return create_error_response(
                "Game state not found for GOD_MODE_UPDATE_STATE", 404
            )

        current_state_dict = current_game_state.to_dict()
        previous_combat_state = copy.deepcopy(current_state_dict.get("combat_state", {}))

        # Capture original time before update for accurate monotonicity validation
        # Note: current_game_state is a GameState instance, use dict version
        # Use `or {}` to handle both missing and explicitly-null world_data
        # CRITICAL: Deep-copy to prevent mutation by update_state_with_changes
        original_world_time = copy.deepcopy(
            (current_state_dict.get("world_data") or {}).get("world_time")
        )

        # Perform an update
        updated_state_dict = update_state_with_changes(
            current_state_dict, state_changes
        )
        updated_state_dict = apply_automatic_combat_cleanup(
            updated_state_dict, state_changes
        )

        # Convert to GameState object for validation
        final_game_state = GameState.from_dict(updated_state_dict)
        if final_game_state is None:
            logging_util.error(
                "PROCESS_ACTION: GameState.from_dict returned None after update; rejecting GOD_MODE_UPDATE_STATE"
            )
            return create_error_response(
                "Unable to reconstruct game state after applying changes.", 500
            )

        # Validate and auto-correct state before persistence
        # Surface corrections to user so they see what was actually applied
        validated_state_dict, corrections = validate_and_correct_state(
            final_game_state.to_dict(),
            previous_world_time=original_world_time,
            return_corrections=True,
        )

        # Detect post-combat warnings for GOD_MODE_UPDATE_STATE (no rewards followup here)
        # Uses shared _extract_xp_from_player_data helper to avoid duplication with unified flow
        post_combat_warnings: list[str] = []
        try:
            updated_game_state_obj = GameState.from_dict(validated_state_dict)
            if updated_game_state_obj:
                final_xp = _extract_xp_from_player_data(
                    validated_state_dict.get("player_character_data", {})
                )
                original_xp = _extract_xp_from_player_data(
                    current_state_dict.get("player_character_data", {})
                )
                if final_xp <= original_xp:
                    post_combat_warnings = updated_game_state_obj.detect_post_combat_issues(
                        previous_combat_state, state_changes
                    )
        except Exception as e:
            logging_util.warning(f"POST_COMBAT warning detection failed: {e}")

        system_warnings = corrections + post_combat_warnings

        firestore_service.update_campaign_game_state(
            user_id, campaign_id, validated_state_dict
        )

        log_message = format_game_state_updates(state_changes, for_html=False)

        # Build response with corrections if any were applied
        response_parts = [
            "[System Message: The following state changes were applied via GOD MODE]",
            log_message,
        ]
        if corrections:
            response_parts.append("\n[Auto-Corrections Applied]")
            for correction in corrections:
                response_parts.append(f"  - {correction}")
        if post_combat_warnings:
            response_parts.append("\n[System Warnings]")
            for warning in post_combat_warnings:
                response_parts.append(f"  - {warning}")

        response_payload = {
            KEY_SUCCESS: True,
            KEY_RESPONSE: "\n".join(response_parts),
        }
        if system_warnings:
            response_payload["system_warnings"] = system_warnings

        return response_payload

    except json.JSONDecodeError:
        return create_error_response(
            "Invalid JSON payload for GOD_MODE_UPDATE_STATE command.", 400
        )
    except ValueError as e:
        return create_error_response(
            f"Error in GOD_MODE_UPDATE_STATE payload: {e}", 400
        )
    except Exception as e:
        return create_error_response(
            f"An unexpected error occurred during GOD_MODE_UPDATE_STATE: {e}", 500
        )
