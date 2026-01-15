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
from mvp_site.action_resolution_utils import add_action_resolution_to_response
from mvp_site.agent_prompts import (
    build_temporal_correction_prompt,
    build_temporal_warning_message,
    extract_llm_instruction_hints,
)
from mvp_site.custom_types import CampaignId, UserId
from mvp_site.debug_hybrid_system import clean_json_artifacts, process_story_for_display
from mvp_site.firestore_service import (
    _truncate_log_json,
    get_user_settings,
    update_state_with_changes,
)
from mvp_site.game_state import (
    GameState,
    coerce_int,
    level_from_xp,
    validate_and_correct_state,
    xp_needed_for_level,
)
from mvp_site.prompt_utils import _build_campaign_prompt as _build_campaign_prompt_impl
from mvp_site.serialization import json_default_serializer

# Initialize Firebase if not already initialized.
# In mock/test mode, missing credentials should not be fatal.
# WORLDAI_* vars take precedence for WorldArchitect.AI repo-specific config.
_MOCK_SERVICES_MODE = os.getenv("MOCK_SERVICES_MODE", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "y",
    "on",
}
_TEST_MODE = os.getenv("TEST_MODE", "mock").strip().lower()
_ALLOW_MISSING_FIREBASE = _MOCK_SERVICES_MODE or _TEST_MODE == "mock"


def is_mock_services_mode() -> bool:
    """Check if mock services mode is enabled.

    Evaluated at runtime to support dynamic environment changes in tests.
    """
    return os.getenv("MOCK_SERVICES_MODE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }

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
        if _ALLOW_MISSING_FIREBASE:
            logging_util.warning(
                "Failed to initialize Firebase in mock/test mode; continuing without Firebase: %s",
                e,
            )
        else:
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
    turns_per_scene = 2
    scene = (player_turn + 1) // turns_per_scene

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


# Temporal correction prompts centralized in agent_prompts.py
# Use build_temporal_correction_prompt() and build_temporal_warning_message()


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
        # Use robust XP extractor to handle multiple field formats
        player_data = state_dict.get("player_character_data") or {}
        original_player_data = original_state_dict.get("player_character_data") or {}

        current_xp = _extract_xp_robust(player_data)
        original_xp = _extract_xp_robust(original_player_data)
        if current_xp > original_xp:
            return True

    return False


def _detect_rewards_discrepancy(
    state_dict: dict[str, Any],
    original_state_dict: dict[str, Any] | None = None,
    warnings_out: list[str] | None = None,
) -> list[str]:
    """

    Detect rewards state discrepancies for LLM self-correction.

    Instead of server-side enforcement (which undermines LLM decision-making),
    this function detects discrepancies and returns correction messages that
    will be injected into the next LLM prompt via `system_corrections`.

    This follows the "LLM Decides, Server Detects" principle - we inform the LLM
    of issues and let it fix them in the next inference.

    Detects discrepancies when:
    1. Combat just ended (combat_phase in COMBAT_FINISHED_PHASES and combat_summary exists)
       but rewards_processed=False
    2. Encounter completed (encounter_completed=True and encounter_summary exists)
       but rewards_processed=False
    3. XP increased from the previous state but rewards_processed=False
    Also emits warnings when XP increases while rewards_processed=True (possible double-processing).

    Args:
        state_dict: The game state dict after updates are applied
        original_state_dict: Optional original state before the update (for XP comparison)
        warnings_out: Optional list to append non-blocking warning messages

    Returns:
        List of discrepancy messages to inject into next prompt's system_corrections

    """
    discrepancies: list[str] = []
    combat_state = state_dict.get("combat_state", {}) or {}
    encounter_state = state_dict.get("encounter_state", {}) or {}

    # Check 1: Combat just ended with summary but rewards_processed=False
    combat_phase = combat_state.get("combat_phase", "")
    combat_summary = combat_state.get("combat_summary")
    combat_rewards_processed = combat_state.get("rewards_processed", False)

    if (
        combat_phase in constants.COMBAT_FINISHED_PHASES
        and combat_summary
        and not combat_rewards_processed
    ):
        logging_util.warning(
            "🏆 REWARDS_DISCREPANCY: combat_phase=%s, combat_summary exists, "
            "but rewards_processed=False",
            combat_phase,
        )
        discrepancies.append(
            f"REWARDS_STATE_ERROR: Combat ended (phase={combat_phase}) with summary, "
            "but rewards_processed=False. You MUST set combat_state.rewards_processed=true."
        )

    # Check 2: Encounter completed with summary but rewards_processed=False
    encounter_completed = encounter_state.get("encounter_completed", False)
    encounter_summary = encounter_state.get("encounter_summary")
    encounter_rewards_processed = encounter_state.get("rewards_processed", False)

    if encounter_completed and encounter_summary and not encounter_rewards_processed:
        logging_util.warning(
            "🏆 REWARDS_DISCREPANCY: encounter_completed=True, encounter_summary exists, "
            "but rewards_processed=False"
        )
        discrepancies.append(
            "REWARDS_STATE_ERROR: Encounter completed with summary, "
            "but rewards_processed=False. You MUST set encounter_state.rewards_processed=true."
        )

    # Check 3: XP increased during combat; flag whether rewards_processed is set
    if original_state_dict and combat_phase in constants.COMBAT_FINISHED_PHASES:
        player_data = state_dict.get("player_character_data") or {}
        original_player_data = original_state_dict.get("player_character_data") or {}
        original_combat_state = original_state_dict.get("combat_state") or {}
        original_combat_rewards_processed = original_combat_state.get(
            "rewards_processed", False
        )

        current_xp = _extract_xp_robust(player_data)
        original_xp = _extract_xp_robust(original_player_data)

        if current_xp > original_xp:
            if not combat_rewards_processed:
                logging_util.warning(
                    "🏆 REWARDS_DISCREPANCY: XP increased (%d -> %d) during combat_phase=%s, "
                    "but rewards_processed=False",
                    original_xp,
                    current_xp,
                    combat_phase,
                )
                discrepancies.append(
                    f"REWARDS_STATE_ERROR: XP increased ({original_xp} -> {current_xp}) during "
                    f"combat_phase={combat_phase}, but rewards_processed=False. "
                    "You MUST set combat_state.rewards_processed=true."
                )
            elif original_combat_rewards_processed:
                warning = (
                    "REWARDS_STATE_WARNING: XP increased "
                    f"({original_xp} -> {current_xp}) during combat_phase={combat_phase}, "
                    "but rewards_processed=True. Ensure rewards are not being double-processed."
                )
                logging_util.warning(
                    "🏆 REWARDS_DISCREPANCY: XP increased (%d -> %d) even though "
                    "rewards_processed=True during combat_phase=%s; investigate potential "
                    "double-processing",
                    original_xp,
                    current_xp,
                    combat_phase,
                )
                if warnings_out is not None:
                    warnings_out.append(warning)

    return discrepancies


REWARD_CORRECTION_PREFIX = "REWARDS_STATE_ERROR"


def _is_reward_correction(message: Any) -> bool:
    """Return True for reward-related system correction strings."""
    return isinstance(message, str) and message.startswith(REWARD_CORRECTION_PREFIX)


def _filter_reward_corrections(corrections: list[Any] | None) -> list[str]:
    """Filter to reward-related system correction strings."""
    if not corrections:
        return []
    return [message for message in corrections if _is_reward_correction(message)]


def _normalize_system_corrections(value: Any) -> list[str]:
    """Coerce arbitrary pending corrections to a clean list[str] (drop non-strings)."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item)
        return out
    return []


def _extract_xp_robust(player_data: dict[str, Any]) -> int:
    """Extract XP from player_character_data, handling multiple field formats.

    Tries in order:
    1. experience.current (canonical format)
    2. xp (flat format)
    3. xp_current (flat variant)

    Also handles comma-formatted strings like "1,500".

    Args:
        player_data: The player_character_data dict

    Returns:
        XP as integer, or 0 if not found
    """
    # Try canonical format first
    experience = player_data.get("experience") or {}
    xp_raw = experience.get("current")

    # Try flat formats if canonical not found
    if xp_raw is None:
        xp_raw = player_data.get("xp") or player_data.get("xp_current")

    # Handle comma-formatted strings (e.g., "1,500" -> 1500)
    if isinstance(xp_raw, str):
        xp_raw = xp_raw.replace(",", "")

    return coerce_int(xp_raw, 0)


def _check_and_set_level_up_pending(
    state_dict: dict[str, Any], original_state_dict: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Server-side level-up detection: Set rewards_pending when XP now supports a higher level.

    This ensures level-up is offered to the player even when XP is awarded outside
    the normal rewards pipeline (e.g., God Mode, narrative milestones) or when a
    previous level-up was missed. Comparison uses the original state (pre-update)
    to avoid relying on validation that may auto-correct the stored level.

    The LLM receives rewards_pending in game state context and generates level-up
    rewards boxes per rewards_system_instruction.md when level_up_available=True.

    Args:
        state_dict: The game state dict after updates are applied
        original_state_dict: Original state before the update (for XP comparison)

    Returns:
        The game state dict with rewards_pending set if level-up is available
    """
    if original_state_dict is None:
        return state_dict

    # Get current and original XP using robust extractor
    player_data = state_dict.get("player_character_data") or {}
    current_xp = _extract_xp_robust(player_data)

    original_player_data = original_state_dict.get("player_character_data") or {}
    original_xp = _extract_xp_robust(original_player_data)

    # Get stored level from ORIGINAL state (before validation auto-correction)
    # This ensures we detect level-ups even when validation already corrected the level
    # in the current state. Falls back to current state's level if original not available.
    original_level = coerce_int(original_player_data.get("level"), None)
    current_level = coerce_int(player_data.get("level"), 1)
    stored_level = original_level if original_level is not None else current_level

    # Calculate what level SHOULD be based on XP
    expected_level = level_from_xp(current_xp)

    # If expected level is NOT higher than stored level, NO level-up needed
    if expected_level <= stored_level:
        # CRITICAL: Clear stale level-up notifications if:
        # 1. Player actually leveled up (stored_level >= pending new_level), OR
        # 2. XP dropped below the threshold for the pending level-up
        existing_rewards = state_dict.get("rewards_pending") or {}
        if existing_rewards.get("level_up_available") is True:
            existing_new_level = coerce_int(
                existing_rewards.get("new_level"), default=0
            )
            # Get XP threshold for the pending level-up
            xp_threshold_for_pending = xp_needed_for_level(existing_new_level)
            if stored_level >= existing_new_level:
                # Player reached or exceeded the pending level → clear the notification
                logging_util.info(
                    f"📈 LEVEL_UP_CHECK: Clearing stale level-up notification "
                    f"(stored_level={stored_level} >= pending new_level={existing_new_level})"
                )
                state_dict.pop("rewards_pending", None)
            elif current_xp < xp_threshold_for_pending:
                # XP dropped below threshold for pending level-up → clear stale notification
                logging_util.info(
                    f"📈 LEVEL_UP_CHECK: Clearing stale level-up notification "
                    f"(XP {current_xp} < threshold {xp_threshold_for_pending} for level {existing_new_level})"
                )
                state_dict.pop("rewards_pending", None)
        return state_dict

    # Check if rewards_pending already exists and handles this level-up
    existing_rewards = state_dict.get("rewards_pending") or {}
    if existing_rewards.get("level_up_available") is True:
        existing_new_level = coerce_int(
            existing_rewards.get("new_level"), default=stored_level
        )
        if expected_level <= existing_new_level:
            # Already have an equal-or-higher pending level-up; avoid resetting flags
            logging_util.debug(
                "📈 LEVEL_UP_CHECK: existing level_up_available covers current level"
            )
            return state_dict

        # XP has pushed the player to a higher level than the pending notification;
        # refresh rewards_pending to surface the higher target level.
        logging_util.info(
            "📈 LEVEL_UP_CHECK: Upgrading pending level-up notification "
            f"from {existing_new_level} to {expected_level}"
        )

    # Set rewards_pending to trigger RewardsAgent (either new or upgraded)
    xp_delta = current_xp - original_xp
    logging_util.info(
        f"📈 LEVEL_UP_CHECK: Level-up available! "
        f"XP {original_xp} → {current_xp} ({'+' if xp_delta >= 0 else ''}{xp_delta}), "
        f"stored_level={stored_level}, expected_level={expected_level}. "
        f"Setting rewards_pending.level_up_available=True"
    )

    existing_rewards = state_dict.get("rewards_pending") or {}

    # CRITICAL FIX: Don't resurrect already-processed rewards
    # If existing rewards were already processed, clear them before merging new level-up
    if existing_rewards.get("processed") is True:
        # Old rewards already processed - start fresh for this level-up
        merged_items = []
        preserved_xp = 0
        preserved_gold = 0
    else:
        # Old rewards not yet processed - merge them with this level-up
        merged_items = list(existing_rewards.get("items") or [])
        preserved_xp = existing_rewards.get("xp", 0)
        preserved_gold = existing_rewards.get("gold", 0)

    new_source_id = f"level_up_{stored_level}_to_{expected_level}"

    state_dict["rewards_pending"] = {
        "source": "level_up",
        # Always align source_id with the current target level (upgrade-safe)
        "source_id": new_source_id,
        # XP has already been applied to state; preserve any existing rewards XP (if not processed)
        "xp": preserved_xp,
        "gold": preserved_gold,
        "items": merged_items,
        "level_up_available": True,
        "new_level": expected_level,
        # Always reset processed to False so RewardsAgent prompts for the higher level
        "processed": False,
    }

    return state_dict


async def _process_rewards_followup(
    mode: str,
    llm_response_obj: Any,
    updated_game_state_dict: dict[str, Any],
    original_state_as_dict: dict[str, Any],
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
        original_state_as_dict: Original state dict before the action
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

    rewards_warnings: list[str] = []

    post_update_state = GameState.from_dict(updated_game_state_dict)
    rewards_visible = _has_rewards_narrative(llm_response_obj.narrative_text)
    rewards_expected = _has_rewards_context(
        updated_game_state_dict, original_state_dict=original_state_as_dict
    )
    rewards_pending = (
        post_update_state.has_pending_rewards() if post_update_state else False
    )

    if not post_update_state or not (
        rewards_pending or (rewards_expected and not rewards_visible)
    ):
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
        # Detect rewards discrepancies (will be injected into next prompt)
        rewards_discrepancies = _detect_rewards_discrepancy(
            updated_game_state_dict,
            original_state_dict=original_state_as_dict,
            warnings_out=rewards_warnings,
        )
        if rewards_discrepancies:
            prevention_extras.setdefault("system_corrections", []).extend(
                rewards_discrepancies
            )
        if rewards_warnings:
            prevention_extras.setdefault("system_warnings", []).extend(rewards_warnings)
        # Check for level-up after rewards processing
        updated_game_state_dict = _check_and_set_level_up_pending(
            updated_game_state_dict,
            original_state_dict=original_state_as_dict,
        )
        updated_game_state_dict, rewards_corrections = validate_and_correct_state(
            updated_game_state_dict,
            previous_world_time=original_world_time,
            return_corrections=True,
        )
        # Store rewards corrections so they reach system_warnings in main flow
        if rewards_corrections:
            prevention_extras.setdefault("rewards_corrections", []).extend(
                rewards_corrections
            )
    else:
        # Rewards already applied; detect any discrepancies for next prompt
        rewards_discrepancies = _detect_rewards_discrepancy(
            updated_game_state_dict,
            original_state_dict=original_state_as_dict,
            warnings_out=rewards_warnings,
        )
        if rewards_discrepancies:
            prevention_extras.setdefault("system_corrections", []).extend(
                rewards_discrepancies
            )
        if rewards_warnings:
            prevention_extras.setdefault("system_warnings", []).extend(rewards_warnings)
        # Check for level-up in case XP was awarded in this follow-up
        updated_game_state_dict = _check_and_set_level_up_pending(
            updated_game_state_dict,
            original_state_dict=original_state_as_dict,
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
        # Merge rewards_box from rewards response into primary
        elif (
            hasattr(rewards_structured, "rewards_box")
            and rewards_structured.rewards_box
        ):
            primary_structured.rewards_box = rewards_structured.rewards_box
            logging_util.info(
                f"🏆 REWARDS_FOLLOWUP: Merged rewards_box into response "
                f"(xp={rewards_structured.rewards_box.get('xp_gained', 'N/A')})"
            )

    return updated_game_state_dict, llm_response_obj, prevention_extras


def _inject_levelup_choices_if_needed(
    planning_block: dict[str, Any] | str | None,
    game_state_dict: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Server-side enforcement of level-up choices in planning_block.

    When rewards_pending.level_up_available=true, the LLM SHOULD include
    level_up_now and continue_adventuring choices. However, the LLM sometimes
    prioritizes narrative/tactical choices, especially during active gameplay.

    This function ensures users ALWAYS have clickable level-up buttons when
    level-up is available, preventing the "text shown but no buttons" failure mode.

    Args:
        planning_block: The planning_block from LLM response (dict, JSON string, or None)
        game_state_dict: Current game state dict to check for level_up_available

    Returns:
        The planning_block dict with level-up choices injected if needed,
        or None if input was None and no injection needed.
    """
    # Check if level-up is available
    rewards_pending = game_state_dict.get("rewards_pending") or {}
    if not rewards_pending.get("level_up_available"):
        # No level-up available - return as-is
        if isinstance(planning_block, str):
            try:
                return json.loads(planning_block) if planning_block.strip() else None
            except (json.JSONDecodeError, TypeError):
                return None
        return planning_block

    # Level-up is available - ensure choices are present
    new_level = rewards_pending.get("new_level", "?")
    player_data = game_state_dict.get("player_character_data") or {}
    player_class = player_data.get("class", "Character")

    # Parse planning_block if it's a string
    if isinstance(planning_block, str):
        try:
            planning_block = (
                json.loads(planning_block) if planning_block.strip() else {}
            )
        except (json.JSONDecodeError, TypeError):
            planning_block = {}
    elif planning_block is None:
        planning_block = {}

    # Ensure choices dict exists
    if "choices" not in planning_block or not isinstance(
        planning_block.get("choices"), dict
    ):
        planning_block["choices"] = {}

    choices = planning_block["choices"]

    # Check if level-up choices are already present (exact IDs required by protocol)
    has_level_up_now = "level_up_now" in choices
    has_continue_adventuring = "continue_adventuring" in choices

    if has_level_up_now and has_continue_adventuring:
        # Already has the required choices - no injection needed
        return planning_block

    # Inject missing level-up choices
    logging_util.info(
        f"📈 SERVER_LEVELUP_INJECTION: Injecting level-up choices for level {new_level} "
        f"(had level_up_now={has_level_up_now}, continue_adventuring={has_continue_adventuring})"
    )

    if not has_level_up_now:
        choices["level_up_now"] = {
            "text": f"Level Up to Level {new_level}",
            "description": f"Apply level {new_level} {player_class} benefits immediately",
            "risk_level": "safe",
        }

    if not has_continue_adventuring:
        choices["continue_adventuring"] = {
            "text": "Continue Adventuring",
            "description": "Level up later and continue the story",
            "risk_level": "safe",
        }

    # Add thinking if not present
    if "thinking" not in planning_block:
        planning_block["thinking"] = (
            f"Level-up to {new_level} is available. "
            "The player can level up now or continue adventuring."
        )

    return planning_block


def _inject_levelup_narrative_if_needed(
    narrative: str | None,
    planning_block: dict[str, Any] | None,
    game_state_dict: dict[str, Any],
) -> str:
    """
    Ensure level-up prompt/options/benefits are visible in narrative text.

    This prevents the "choices only in planning_block" failure mode where the
    UI might not render structured choices, leaving the player unaware of the
    available level-up and its benefits.
    """
    narrative_text = narrative or ""
    rewards_pending = game_state_dict.get("rewards_pending") or {}
    if not rewards_pending.get("level_up_available"):
        return narrative_text

    new_level = rewards_pending.get("new_level", "?")
    player_data = game_state_dict.get("player_character_data") or {}
    current_level = player_data.get("level", "?")
    lower = narrative_text.lower()

    banner_present = "level up available!" in lower
    prompt_present = "would you like to level up" in lower
    immediate_present = (
        "level up immediately" in lower
        or "level up now" in lower
        or "level up to level" in lower
    )
    later_present = (
        "continue adventuring" in lower
        or "continue your journey" in lower
        or "continue the adventure" in lower
    )
    continue_difference_present = ("continue" in lower or "continuing" in lower) and (
        "defer" in lower
        or "later" in lower
        or "remain level" in lower
        or "stay level" in lower
    )
    benefit_keywords = (
        "gain",
        "unlock",
        "bonus",
        "increase",
        "extra",
        "improve",
        "add",
        "advantage",
        "feature",
        "proficiency",
        "hp",
        "hit points",
    )
    benefits_present = any(k in lower for k in benefit_keywords)

    if (
        banner_present
        and prompt_present
        and immediate_present
        and later_present
        and benefits_present
        and continue_difference_present
    ):
        return narrative_text

    lines: list[str] = []
    if not banner_present:
        lines.append(
            f"**LEVEL UP AVAILABLE!** You have earned enough experience to reach Level {new_level}!"
        )

    if not benefits_present:
        benefit_text = None
        if isinstance(planning_block, dict):
            choices = planning_block.get("choices", {})
            if isinstance(choices, dict):
                level_up_choice = choices.get("level_up_now", {})
                if isinstance(level_up_choice, dict):
                    description = level_up_choice.get("description")
                    if isinstance(description, str) and description.strip():
                        benefit_text = description.strip()
        if not benefit_text:
            benefit_text = (
                "Gain new class features, increased proficiency, and more HP."
            )
        lines.append(f"Benefits: {benefit_text}")

    if not prompt_present:
        lines.append("Would you like to level up now?")

    if not (immediate_present and later_present):
        lines.append("Options: 1. Level up immediately  2. Continue adventuring")

    if not continue_difference_present:
        lines.append(
            f"If you continue adventuring, you remain Level {current_level} and defer these benefits until you choose to level up."
        )

    if not lines:
        return narrative_text

    separator = "\n\n" if narrative_text.strip() else ""
    injected_block = "\n".join(lines)
    return f"{narrative_text}{separator}{injected_block}"


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
                "archived_at": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
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
            # Clear reward-related pending_system_corrections - they've been consumed by the LLM
            # which fixed the issue (evidenced by rewards_processed=True)
            pending_corrections = _normalize_system_corrections(
                cleaned_state_dict.get("pending_system_corrections")
            )

            remaining_corrections = [
                message
                for message in pending_corrections
                if not _is_reward_correction(message)
            ]
            if remaining_corrections:
                cleaned_state_dict["pending_system_corrections"] = remaining_corrections
            else:
                cleaned_state_dict.pop("pending_system_corrections", None)
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


def _prepare_game_state_with_user_settings(
    user_id: UserId, campaign_id: CampaignId
) -> tuple[GameState, bool, int, dict[str, Any] | None]:
    """
    Prepare game state and fetch user settings in the same worker thread.

    This reduces thread scheduling overhead in hot paths that already need to
    load game state, while keeping all blocking calls off the event loop.
    """
    current_game_state, was_cleaned, num_cleaned = _prepare_game_state(
        user_id, campaign_id
    )
    user_settings = get_user_settings(user_id)
    if not isinstance(user_settings, dict):
        user_settings = None
    return current_game_state, was_cleaned, num_cleaned, user_settings


def _persist_turn_to_firestore(
    user_id: UserId,
    campaign_id: CampaignId,
    *,
    mode: str,
    user_input: str,
    ai_response_text: str,
    structured_fields: dict[str, Any],
    updated_game_state_dict: dict[str, Any],
) -> None:
    """
    Persist a completed turn (state + story entries) in a single worker thread.

    This reduces asyncio.to_thread() scheduling overhead in hot paths while
    keeping all Firestore I/O off the event loop.
    """
    firestore_service.update_campaign_game_state(
        user_id, campaign_id, updated_game_state_dict
    )
    firestore_service.add_story_entry(
        user_id,
        campaign_id,
        constants.ACTOR_USER,
        user_input,
        mode,
    )
    firestore_service.add_story_entry(
        user_id,
        campaign_id,
        constants.ACTOR_GEMINI,
        ai_response_text,
        None,  # mode
        structured_fields,  # structured_fields
    )


def _update_campaign_game_state(
    user_id: UserId, campaign_id: CampaignId, state_dict: dict[str, Any]
) -> None:
    firestore_service.update_campaign_game_state(user_id, campaign_id, state_dict)


def _load_campaign_and_continue_story(
    user_id: UserId,
    campaign_id: CampaignId,
    *,
    llm_input: str,
    mode: str,
    current_game_state: GameState,
    include_raw_llm_payloads: bool,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], Any]:
    """Fetch campaign data/story context and run continue_story in one thread."""
    campaign_data, story_context = firestore_service.get_campaign_by_id(
        user_id, campaign_id
    )
    if not campaign_data:
        return None, [], None

    story_context = story_context or []
    selected_prompts = campaign_data.get("selected_prompts", [])
    use_default_world = campaign_data.get("use_default_world", False)
    llm_response_obj = llm_service.continue_story(
        llm_input,
        mode,
        story_context,
        current_game_state,
        selected_prompts,
        use_default_world,
        user_id,
        include_raw_llm_payloads,
    )
    return campaign_data, story_context, llm_response_obj


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


def _parse_god_mode_data_string(god_mode_data: str) -> dict[str, Any] | None:
    """
    Parse god_mode_data string format into god_mode dict format.

    String format: "Character: X | Setting: Y | Description: Z"
    Dict format: {"character": {...}, "setting": "...", "description": "..."}

    Args:
        god_mode_data: String in format "Character: X | Setting: Y | Description: Z"

    Returns:
        Dict with god_mode structure, or None if parsing fails
    """
    if not god_mode_data or not isinstance(god_mode_data, str):
        return None

    try:
        # Split by " | " to get Character, Setting, Description parts
        parts = [p.strip() for p in god_mode_data.split(" | ")]

        parsed = {}
        character_str = ""
        setting_str = ""
        description_str = ""

        for part in parts:
            if part.startswith("Character:"):
                character_str = part.replace("Character:", "").strip()
            elif part.startswith("Setting:"):
                setting_str = part.replace("Setting:", "").strip()
            elif part.startswith("Description:"):
                description_str = part.replace("Description:", "").strip()

        # If description contains the full text, use it
        if description_str:
            parsed["description"] = description_str

        if setting_str:
            parsed["setting"] = setting_str

        # Extract character info from character_str and description
        # Look for character details in the description (name, class, level, stats, etc.)
        character_dict = {}

        # Extract character name from character_str (first part before any additional info)
        if character_str:
            # Character string might be just "Ser Arion" or "Ser Arion val Valerion"
            character_dict["name"] = character_str.split(",")[0].strip()

        # Parse description for character details
        # The description contains markdown-formatted character info
        full_text = god_mode_data.lower()

        # Extract name from **Name:** pattern (more reliable than character_str)
        name_match = re.search(r"\*\*name:\*\*\s*([^\n*]+)", full_text, re.IGNORECASE)
        if name_match:
            character_dict["name"] = name_match.group(1).strip()
        elif character_str:
            character_dict["name"] = character_str.split(",")[0].strip()

        # Extract class (look for "Level X Class" or "**Class:** Level X Class" pattern)
        class_match = re.search(r"\*\*class:\*\*\s*level\s+(\d+)\s+(\w+)", full_text, re.IGNORECASE)
        if not class_match:
            class_match = re.search(r"level\s+(\d+)\s+(\w+)", full_text, re.IGNORECASE)
        if class_match:
            character_dict["level"] = int(class_match.group(1))
            # Extract class name (might have parenthetical like "Paladin (Oath of the Crown)")
            class_name = class_match.group(2).strip()
            # Remove parenthetical if present
            class_name = re.sub(r"\s*\([^)]+\)", "", class_name)
            character_dict["class"] = class_name.capitalize()

        # Extract race if mentioned
        race_match = re.search(r"\*\*race:\*\*\s*([^\n*]+)", full_text, re.IGNORECASE)
        if not race_match:
            race_match = re.search(r"race[:\s]+(\w+)", full_text, re.IGNORECASE)
        if race_match:
            race_name = race_match.group(1).strip()
            # Remove markdown formatting
            race_name = re.sub(r"\*\*", "", race_name)
            character_dict["race"] = race_name.capitalize()

        # Extract background if mentioned
        background_match = re.search(r"\*\*background:\*\*\s*([^\n*]+)", full_text, re.IGNORECASE)
        if background_match:
            bg_name = background_match.group(1).strip()
            # Remove markdown formatting
            bg_name = re.sub(r"\*\*", "", bg_name)
            character_dict["background"] = bg_name

        # Extract stats if mentioned (Str X, Con Y, Cha Z pattern)
        # Look for "**Stats:** Str X, Con Y, Cha Z" or "Stats: Str X, Con Y, Cha Z"
        stats_match = re.search(r"\*\*stats?:\*\*\s*(?:str|strength)\s+(\d+)[,\s|]+(?:con|constitution)\s+(\d+)[,\s|]+(?:cha|charisma)\s+(\d+)", full_text, re.IGNORECASE)
        if not stats_match:
            stats_match = re.search(r"stats?[:\s]+(?:str|strength)\s+(\d+)[,\s|]+(?:con|constitution)\s+(\d+)[,\s|]+(?:cha|charisma)\s+(\d+)", full_text, re.IGNORECASE)
        if stats_match:
            character_dict["base_attributes"] = {
                "strength": int(stats_match.group(1)),
                "constitution": int(stats_match.group(2)),
                "charisma": int(stats_match.group(3)),
            }
            character_dict["attributes"] = character_dict["base_attributes"].copy()

        # Extract HP if mentioned
        hp_match = re.search(r"\*\*hp:\*\*\s*(\d+)", full_text, re.IGNORECASE)
        if not hp_match:
            hp_match = re.search(r"hp[:\s]+(\d+)", full_text, re.IGNORECASE)
        if hp_match:
            hp_value = int(hp_match.group(1))
            character_dict["hp_max"] = hp_value
            character_dict["hp_current"] = hp_value

        # Extract AC if mentioned
        ac_match = re.search(r"\*\*ac:\*\*\s*(\d+)", full_text, re.IGNORECASE)
        if not ac_match:
            ac_match = re.search(r"ac[:\s]+(\d+)", full_text, re.IGNORECASE)
        if ac_match:
            character_dict["ac"] = int(ac_match.group(1))

        # Only create god_mode dict if we found character info
        if character_dict:
            parsed["character"] = character_dict
            return parsed

        # If no character info found but we have character string, create minimal character
        if character_str:
            parsed["character"] = {"name": character_str}
            return parsed

        # Return parsed dict if we have setting or description, even without character
        # This prevents user-provided campaign settings from being lost
        if parsed.get("setting") or parsed.get("description"):
            return parsed

        return None

    except Exception as e:
        logging_util.warning(f"Failed to parse god_mode_data string: {e}")
        return None


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
        god_mode = request_data.get("god_mode")
        god_mode_data = request_data.get("god_mode_data")

        # Parse god_mode_data (string format) into god_mode (dict format) if needed
        # Real users send god_mode_data as string: "Character: X | Setting: Y | Description: Z"
        # Code expects god_mode as dict: {"character": {...}, "setting": "...", "description": "..."}
        if not god_mode and god_mode_data and isinstance(god_mode_data, str):
            logging_util.info("Parsing god_mode_data string format into god_mode dict")
            god_mode = _parse_god_mode_data_string(god_mode_data)
            if god_mode:
                logging_util.info(f"Parsed god_mode_data: character={god_mode.get('character', {}).get('name', 'Unknown')}")
                # Extract character/setting/description from parsed god_mode for prompt building
                if not character and god_mode.get("character", {}).get("name"):
                    character = god_mode["character"]["name"]
                if not setting and god_mode.get("setting"):
                    setting = god_mode["setting"]
                if not description and god_mode.get("description"):
                    description = god_mode["description"]

        # Validate required fields
        if not user_id:
            return {KEY_ERROR: "User ID is required"}
        if not title:
            return {KEY_ERROR: "Title is required"}

        # Build campaign prompt (may generate random values if character/setting are empty)
        try:
            prompt = _build_campaign_prompt(character, setting, description, old_prompt)
        except ValueError as e:
            return {KEY_ERROR: str(e)}

        # CRITICAL FIX: Extract character/setting from prompt if they were randomly generated
        # When user leaves fields blank, _build_campaign_prompt generates random values
        # We need to extract those values to build god_mode
        if not character or not setting:
            # Parse prompt to extract character/setting (format: "Character: X | Setting: Y")
            import re
            char_match = re.search(r"Character:\s*([^|]+)", prompt)
            setting_match = re.search(r"Setting:\s*([^|]+)", prompt)
            if char_match:
                character = char_match.group(1).strip()
                logging_util.info(f"Extracted character from prompt: {character}")
            if setting_match:
                setting = setting_match.group(1).strip()
                logging_util.info(f"Extracted setting from prompt: {setting}")

        # ALSO: Build god_mode dict from separate character/setting/description fields (frontend format)
        # Frontend sends character/setting/description as separate fields, not god_mode_data string
        # This also handles randomly generated values from _build_campaign_prompt
        if not god_mode and (character or setting or description):
            logging_util.info("Building god_mode dict from separate character/setting/description fields")
            god_mode = {}
            if setting:
                god_mode["setting"] = setting
            if description:
                god_mode["description"] = description
            if character:
                # Build minimal character dict - LLM will interpret the string
                # We just need god_mode["character"] to be a dict so is_god_mode_with_character is True
                character_dict = {}
                if isinstance(character, str):
                    # Store the full character string - LLM will interpret it
                    # This could be "Ser Arion", "A devout cleric...", "Level 1 Fighter", etc.
                    character_dict["name"] = character.strip()
                    # If description exists, combine it (LLM sees full context)
                    if description:
                        character_dict["description"] = description.strip()
                elif isinstance(character, dict):
                    character_dict = character
                if character_dict:
                    god_mode["character"] = character_dict
                    logging_util.info(f"Built god_mode from separate fields: character={character_dict.get('name', 'Unknown')}")

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
        # ALWAYS start in character creation mode, even if God Mode includes character data
        # Extract God Mode character template if provided
        player_character_data = {}
        character_creation_stage = "concept"  # Default stage

        # Initialize entity tracking with player character if provided
        entity_tracking = {}
        if god_mode and isinstance(god_mode, dict):
            god_mode_character = god_mode.get("character")
            if god_mode_character and isinstance(god_mode_character, dict):
                # Populate player_character_data with template fields
                player_character_data = god_mode_character.copy()
                # Set stage to "review" since character data is pre-populated
                character_creation_stage = "review"
                player_name = player_character_data.get("name")
                logging_util.info(
                    f"God Mode character template detected: {player_name or 'Unknown'}"
                )

                # CHAR-9ss fix: Initialize starting equipment based on class/background
                # Use (get() or "") to handle None values that bypass default
                character_class = (player_character_data.get("class") or "").lower()
                background = (player_character_data.get("background") or "").lower()

                # Basic starting equipment by class (D&D 5e SRD)
                class_equipment = {
                    "wizard": [
                        "Spellbook",
                        "Component pouch",
                        "Quarterstaff",
                        "Scholar's pack"
                    ],
                    "fighter": [
                        "Chain mail",
                        "Longsword",
                        "Shield",
                        "Dungeoneer's pack",
                        "Javelin (2)"
                    ],
                    "rogue": [
                        "Leather armor",
                        "Shortsword (2)",
                        "Dagger",
                        "Thieves' tools",
                        "Burglar's pack"
                    ],
                    "cleric": [
                        "Chain mail",
                        "Mace",
                        "Shield",
                        "Holy symbol",
                        "Priest's pack"
                    ],
                }

                # Get starting equipment for this class
                equipment = []
                for class_name, items in class_equipment.items():
                    if class_name in character_class:
                        equipment.extend(items)
                        break

                # Add background-specific items
                if "sage" in background:
                    equipment.extend(["Ink (1 ounce bottle)", "Quill", "Small knife", "Letter from dead colleague"])
                elif "soldier" in background:
                    equipment.extend(["Insignia of rank", "Trophy from fallen enemy", "Dice set"])
                elif "criminal" in background:
                    equipment.extend(["Crowbar", "Dark common clothes", "Pouch (15gp)"])

                # Add basic adventuring gear
                equipment.extend([
                    "Backpack",
                    "Bedroll",
                    "Mess kit",
                    "Tinderbox",
                    "Torch (10)",
                    "Rations (10 days)",
                    "Waterskin",
                    "Rope (50 feet)",
                    "Coin pouch (10gp)"
                ])

                # Initialize inventory in player_character_data
                if equipment and "inventory" not in player_character_data:
                    player_character_data["inventory"] = equipment
                    logging_util.info(
                        f"✅ Initialized {len(equipment)} starting items for {character_class}"
                    )

                # Add player character to active_entities for entity tracking
                if player_name:
                    entity_tracking = {
                        "active_entities": [player_name],
                        "present_entities": []
                    }
                    logging_util.info(
                        f"✅ Added '{player_name}' to active_entities (God Mode character)"
                    )

        # Extract companions from god_mode if present
        npc_data_from_god_mode = {}
        if god_mode and isinstance(god_mode, dict) and "companions" in god_mode:
            companions_dict = god_mode.get("companions", {})
            if isinstance(companions_dict, dict):
                # CRITICAL: Ensure all companions have relationship="companion" field
                # so they're detected by build_companion_instruction() filter
                npc_data_from_god_mode = {}
                for name, npc in companions_dict.items():
                    if isinstance(npc, dict):
                        npc_copy = npc.copy()
                        npc_copy["relationship"] = "companion"  # Required for companion detection
                        npc_data_from_god_mode[name] = npc_copy
                logging_util.info(
                    f"🎭 GOD MODE: Found {len(npc_data_from_god_mode)} companions in god_mode: {list(npc_data_from_god_mode.keys())}"
                )

        initial_game_state = GameState(
            user_id=user_id,
            custom_campaign_state={
                "attribute_system": attribute_system,
                "character_creation_in_progress": True,
                "character_creation_stage": character_creation_stage,
            },
            player_character_data=player_character_data,
            entity_tracking=entity_tracking,
            debug_mode=debug_mode,
            npc_data=npc_data_from_god_mode,  # Pass directly - GameState handles empty dict default
        ).to_dict()

        # Verify companions are in the state dict
        if npc_data_from_god_mode:
            state_npc_data = initial_game_state.get("npc_data", {})
            if not isinstance(state_npc_data, dict):
                state_npc_data = {}
            # Merge companions into state (in case GameState didn't preserve them)
            state_npc_data.update(npc_data_from_god_mode)
            initial_game_state["npc_data"] = state_npc_data
            logging_util.info(
                f"🎭 GOD MODE: Verified {len(state_npc_data)} companions in initial_game_state: {list(state_npc_data.keys())}"
            )

        generate_companions = "companions" in custom_options
        use_default_world = "defaultWorld" in custom_options

        # CRITICAL UX FIX: For God Mode campaigns with pre-populated characters,
        # generate character creation narrative IMMEDIATELY so user can review.
        # Only skip for empty character creation (user will build from scratch).
        is_god_mode_with_character = (
            god_mode
            and isinstance(god_mode, dict)
            and god_mode.get("character")
            and isinstance(god_mode.get("character"), dict)
        )

        # DEBUG LOGGING: Track why placeholder might be shown
        logging_util.info("🔍 CHARACTER CREATION DECISION:")
        logging_util.info(f"  character_creation_in_progress: {initial_game_state['custom_campaign_state']['character_creation_in_progress']}")
        logging_util.info(f"  god_mode exists: {god_mode is not None}")
        logging_util.info(f"  god_mode type: {type(god_mode)}")
        logging_util.info(f"  god_mode value: {god_mode}")
        if god_mode:
            logging_util.info(f"  god_mode.get('character'): {god_mode.get('character')}")
            logging_util.info(f"  character is dict: {isinstance(god_mode.get('character'), dict) if god_mode.get('character') else False}")
        logging_util.info(f"  is_god_mode_with_character: {is_god_mode_with_character}")

        if initial_game_state["custom_campaign_state"]["character_creation_in_progress"] and not is_god_mode_with_character:
            # Empty character creation - skip opening story, let user build character in Turn 1
            logging_util.info(
                "Skipping opening story generation - empty character creation mode active"
            )
            opening_story_text = "[Character Creation Mode - Story begins after character is complete]"
            # Keep Firestore structured field payload shape consistent, even when
            # we skip opening story generation.
            opening_story_structured_fields = {
                constants.FIELD_SESSION_HEADER: "",
                constants.FIELD_PLANNING_BLOCK: {},
                constants.FIELD_DICE_ROLLS: [],
                constants.FIELD_DICE_AUDIT_EVENTS: [],
                constants.FIELD_RESOURCES: {},
                constants.FIELD_DEBUG_INFO: {},
                constants.FIELD_GOD_MODE_RESPONSE: "",
                constants.FIELD_DIRECTIVES: {},
            }
        else:
            # Generate opening story using LLM (CRITICAL: blocking I/O - 10-30+ seconds!)
            # For God Mode campaigns with character data, use CharacterCreationAgent
            # For regular campaigns, use StoryModeAgent
            # CRITICAL: If companions are in initial_game_state (from god_mode), ensure generate_companions is True
            # so the LLM knows to include them in the narrative
            if npc_data_from_god_mode and not generate_companions:
                generate_companions = True
                logging_util.info(
                    f"🎭 GOD MODE: Enabling generate_companions=True because {len(npc_data_from_god_mode)} companions found in god_mode"
                )

            try:
                opening_story_response = await asyncio.to_thread(
                    llm_service.get_initial_story,
                    prompt,
                    user_id,
                    selected_prompts,
                    generate_companions,
                    use_default_world,
                    use_character_creation_agent=is_god_mode_with_character,  # Use CharacterCreationAgent for God Mode with character
                    initial_npc_data=npc_data_from_god_mode if npc_data_from_god_mode else None,  # Pass companions from god_mode
                )
            except llm_service.LLMRequestError as e:
                logging_util.error(f"LLM request failed during campaign creation: {e}")
                status_code = getattr(e, "status_code", None) or 422
                return create_error_response(str(e), status_code)

            opening_story_text = opening_story_response.narrative_text

            # Extract structured fields
            fields = structured_fields_utils.extract_structured_fields(opening_story_response)

            # Ensure planning_block is a dict (prevent string "empty" values from extraction)
            if constants.FIELD_PLANNING_BLOCK in fields:
                if not isinstance(fields[constants.FIELD_PLANNING_BLOCK], dict):
                    fields[constants.FIELD_PLANNING_BLOCK] = {}
            else:
                fields[constants.FIELD_PLANNING_BLOCK] = {}

            opening_story_structured_fields = _ensure_session_header_resources(
                fields,
                initial_game_state,
            )

        # Create campaign in Firestore (blocking I/O - run in thread)
        campaign_id = await asyncio.to_thread(
            firestore_service.create_campaign,
            user_id,
            title,
            prompt,
            opening_story_text,
            initial_game_state,
            selected_prompts,
            use_default_world,
            opening_story_structured_fields,
        )

        return {
            KEY_SUCCESS: True,
            KEY_CAMPAIGN_ID: campaign_id,
            "title": title,
            "opening_story": opening_story_text,
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

    def _is_god_mode_return_to_story(text: str, mode: str | None = None) -> bool:
        """Check if text is a return-to-story command from god mode.

        Works with both:
        1. "GOD MODE: return to story" prefix (any mode)
        2. "return to story" without prefix (when mode='god')
        """
        if not isinstance(text, str):
            return False
        stripped = text.strip()

        # Check if we have the GOD MODE: prefix
        has_prefix = stripped.upper().startswith("GOD MODE:")

        # If we have the prefix, extract remainder; otherwise use full text
        if has_prefix:
            remainder = stripped[len("GOD MODE:") :].strip().lower()
        elif mode and mode.lower() == constants.MODE_GOD:
            # No prefix but we're in god mode via parameter - check full text
            remainder = stripped.lower()
        else:
            # No prefix and not in god mode - not a return command
            return False

        remainder = remainder.rstrip(".! ")
        tokens = [t for t in remainder.split() if t]
        if not tokens:
            return False
        # Allow polite suffixes like "please"/"now" but prevent matching unrelated commands.
        suffix_ok = {"please", "now"}
        if tokens[:3] == ["return", "to", "story"]:
            return all(t in suffix_ok for t in tokens[3:])
        if tokens[:4] == ["return", "to", "story", "mode"]:
            return all(t in suffix_ok for t in tokens[4:])
        if tokens[:3] == ["exit", "god", "mode"]:
            return all(t in suffix_ok for t in tokens[3:])
        if tokens[:3] == ["return", "to", "game"]:
            return all(t in suffix_ok for t in tokens[3:])
        if tokens[:2] == ["resume", "story"]:
            return all(t in suffix_ok for t in tokens[2:])
        return False

    campaign_id = request_data.get("campaign_id")
    logging_util.set_campaign_id(campaign_id)
    try:
        # Extract parameters
        user_id = request_data.get("user_id")
        user_input = request_data.get("user_input")
        mode = request_data.get("mode", constants.MODE_CHARACTER)
        include_raw_llm_payloads = bool(
            request_data.get("include_raw_llm_payloads", False)
        )

        # Validate required fields
        if not user_id:
            return {KEY_ERROR: "User ID is required"}
        if not campaign_id:
            return {KEY_ERROR: "Campaign ID is required"}
        if user_input is None:
            return {KEY_ERROR: "User input is required"}

        # Preserve raw input for Firestore + temporal correction prompts
        original_user_input = user_input

        # If this is a GOD MODE return command, treat as story mode transition.
        # Supports both "GOD MODE: return to story" prefix and plain "return to story" when mode='god'
        if _is_god_mode_return_to_story(user_input, mode):
            user_input = "Return to story."
            mode = constants.MODE_CHARACTER

        # Load and prepare game state + user settings.
        #
        # In mock services mode, Firestore is in-memory and non-blocking, so
        # running directly avoids thread scheduling overhead that can make
        # concurrency tests flaky.
        if is_mock_services_mode():
            (
                current_game_state,
                was_cleaned,
                num_cleaned,
                user_settings,
            ) = _prepare_game_state_with_user_settings(user_id, campaign_id)
        else:
            (
                current_game_state,
                was_cleaned,
                num_cleaned,
                user_settings,
            ) = await asyncio.to_thread(
                _prepare_game_state_with_user_settings, user_id, campaign_id
            )
        if user_settings and "debug_mode" in user_settings:
            current_game_state.debug_mode = user_settings["debug_mode"]

        # Handle debug mode commands (only when applicable; avoids unnecessary
        # thread scheduling overhead for normal gameplay).
        user_input_stripped = user_input.strip()
        if (
            user_input_stripped == "GOD_ASK_STATE"
            or user_input_stripped.startswith(("GOD_MODE_SET:", "GOD_MODE_UPDATE_STATE:"))
        ):
            debug_response = await asyncio.to_thread(
                _handle_debug_mode_command,
                user_input,
                current_game_state,
                user_id,
                campaign_id,
            )
            if debug_response:
                return debug_response

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
        #
        # NOTE: is_god_mode and is_think_mode are determined by agent selection inside
        # llm_service.continue_story. The LLMResponse returns agent_mode as the single
        # source of truth. We set these AFTER the LLM call based on llm_response_obj.agent_mode.
        llm_input = user_input  # Separate variable for LLM calls
        temporal_correction_attempts = 0
        llm_response_obj = None
        new_world_time: dict[str, Any] | None = None

        while temporal_correction_attempts <= MAX_TEMPORAL_CORRECTION_ATTEMPTS:
            try:
                # Always reload campaign_data and story_context from Firestore for each request.
                # This ensures:
                # 1. story_context includes the latest story entries (including previous commands)
                # 2. campaign_data reflects any changes (selected_prompts, use_default_world, etc.)
                #
                # No caching is needed because:
                # - MAX_TEMPORAL_CORRECTION_ATTEMPTS = 0 (loop only runs once per request)
                # - Campaign data is just one document read (cheap)
                # - Story context must be fresh (includes latest entries)
                # - Caching adds complexity and risk of stale data bugs
                (
                    campaign_data,
                    story_context,
                    llm_response_obj,
                ) = await asyncio.to_thread(
                    _load_campaign_and_continue_story,
                    user_id,
                    campaign_id,
                    llm_input=llm_input,
                    mode=mode,
                    current_game_state=current_game_state,
                    include_raw_llm_payloads=include_raw_llm_payloads,
                )
                if not campaign_data or llm_response_obj is None:
                    return {
                        KEY_ERROR: "Campaign not found",
                        "status_code": 404,
                    }
                selected_prompts = campaign_data.get("selected_prompts", [])
                use_default_world = campaign_data.get("use_default_world", False)
            except llm_service.LLMRequestError as e:
                logging_util.error(f"LLM request failed during story continuation: {e}")
                status_code = getattr(e, "status_code", None) or 422
                return create_error_response(str(e), status_code)

            # Get mode from LLM response - agent selection is the single source of truth
            # This replaces duplicate is_god_mode/is_think_mode detection
            is_god_mode = llm_response_obj.agent_mode == constants.MODE_GOD
            is_think_mode = llm_response_obj.agent_mode == constants.MODE_THINK

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
            llm_input = build_temporal_correction_prompt(
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

        # Surface critical LLM response-quality issues to users (and logs) without retries.
        llm_metadata = getattr(llm_response_obj, "processing_metadata", {}) or {}
        llm_missing_fields = llm_metadata.get("llm_missing_fields", [])
        if isinstance(llm_missing_fields, list) and llm_missing_fields:
            warnings_out = prevention_extras.setdefault("system_warnings", [])
            if "dice_integrity" in llm_missing_fields:
                warnings_out.append(
                    "Dice integrity warning: dice output could not be verified. Consider retrying this action."
                )
            if "dice_rolls" in llm_missing_fields:
                warnings_out.append(
                    "Dice rolls missing for an action that required them. Consider retrying this action."
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
            # User-facing error message as god_mode_response
            god_mode_response = (
                f"⚠️ **TEMPORAL ANOMALY DETECTED**\n\n"
                f"The AI generated a response where time moved backward:\n"
                f"- **Previous time:** {old_time_str}\n"
                f"- **Response time:** {new_time_str}\n\n"
                f"This may indicate the AI lost track of the story timeline. "
                f"The response was accepted but timeline consistency may be affected."
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
            temporal_warning = build_temporal_warning_message(
                temporal_correction_attempts,
                max_attempts=MAX_TEMPORAL_CORRECTION_ATTEMPTS,
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
        get_debug_info = getattr(llm_response_obj, "get_debug_info", None)
        llm_debug_info = get_debug_info() if callable(get_debug_info) else {}
        if not isinstance(llm_debug_info, dict):
            llm_debug_info = {}
        # Wrap in dict as extract_llm_instruction_hints expects {"debug_info": {...}}
        instruction_hints = extract_llm_instruction_hints(
            {"debug_info": llm_debug_info}
        )
        pending_instruction_hints = instruction_hints
        if pending_instruction_hints:
            logging_util.info(
                f"📋 DYNAMIC_PROMPTS: LLM requested detailed sections for next turn: {pending_instruction_hints}"
            )

        response = {
            "story": llm_response_obj.narrative_text,
            "state_changes": state_changes,
        }

        # Capture original time before update for accurate monotonicity validation
        # Note: current_game_state is a GameState instance (has to_dict() method)
        # Preserve an immutable snapshot for XP/level comparisons
        original_state_for_level_check = copy.deepcopy(current_game_state.to_dict())
        # Work on a deep copy so in-place mutations do not affect the original snapshot
        current_state_as_dict = copy.deepcopy(original_state_for_level_check)
        # Use `or {}` to handle both missing and explicitly-null world_data
        # CRITICAL: Deep-copy to prevent mutation by update_state_with_changes
        original_world_time = copy.deepcopy(
            (original_state_for_level_check.get("world_data") or {}).get("world_time")
        )

        # Capture previous combat state for post-combat warning detection
        previous_combat_state = copy.deepcopy(
            original_state_for_level_check.get("combat_state", {})
        )

        # Clear old pending_system_corrections BEFORE merge
        # These were already consumed by llm_service (sent to LLM in this turn)
        # Any NEW corrections from the LLM's state_updates will be preserved by the merge
        current_state_as_dict.pop("pending_system_corrections", None)

        # Only include pending_instruction_hints in state_changes when we have new
        # hints to store OR when we need to clear existing hints from prior turns.
        if pending_instruction_hints or original_state_for_level_check.get(
            "pending_instruction_hints"
        ):
            state_changes["pending_instruction_hints"] = pending_instruction_hints

        # Update game state with changes
        # SAFETY: In Think Mode, only allow microsecond time advancement - block all other state changes
        # This prevents LLM hallucinations from accidentally modifying HP, inventory, etc.
        state_changes_to_apply = response.get("state_changes", {})
        if is_think_mode:
            # Filter to only allow world_time.microsecond updates
            # Handle BOTH nested dict format AND dotted key format from LLM
            allowed_changes = {}

            # Format 1: Nested dict - {"world_data": {"world_time": {"microsecond": value}}}
            if "world_data" in state_changes_to_apply:
                world_data = state_changes_to_apply.get("world_data", {})
                if world_data and "world_time" in world_data:
                    world_time_changes = world_data.get("world_time", {})
                    if world_time_changes and "microsecond" in world_time_changes:
                        allowed_changes = {
                            "world_data": {
                                "world_time": {
                                    "microsecond": world_time_changes["microsecond"]
                                }
                            }
                        }

            # Format 2: Dotted key - {"world_data.world_time.microsecond": value}
            dotted_key = "world_data.world_time.microsecond"
            if dotted_key in state_changes_to_apply:
                # Convert to nested format for consistency with update_state_with_changes
                allowed_changes = {
                    "world_data": {
                        "world_time": {
                            "microsecond": state_changes_to_apply[dotted_key]
                        }
                    }
                }

            state_changes_to_apply = allowed_changes
            if response.get("state_changes", {}) != allowed_changes:
                logging_util.info(
                    "🧠 THINK_MODE_SAFETY: Blocked non-time state changes in Think Mode"
                )

        if state_changes_to_apply:
            updated_game_state_dict = update_state_with_changes(
                current_state_as_dict, state_changes_to_apply
            )
        else:
            updated_game_state_dict = current_state_as_dict

        # Track player character in active_entities once name is known, to support
        # entity validation and reduce hallucinations in subsequent turns.
        current_custom_state = current_state_as_dict.get("custom_campaign_state") or {}
        if not isinstance(current_custom_state, dict):
            current_custom_state = {}

        custom_state = updated_game_state_dict.get("custom_campaign_state") or {}
        if not isinstance(custom_state, dict):
            custom_state = {}

        was_creating = current_custom_state.get("character_creation_in_progress", False)
        stage = custom_state.get("character_creation_stage")
        is_completed = bool(custom_state.get("character_creation_completed")) or (
            stage == "complete"
        )
        flag_cleared = not bool(custom_state.get("character_creation_in_progress", True))

        logging_util.debug(
            f"🔍 Entity tracking check: was_creating={was_creating}, is_completed={is_completed}, flag_cleared={flag_cleared}"
        )

        player_data = updated_game_state_dict.get("player_character_data") or {}
        if not isinstance(player_data, dict):
            player_data = {}

        player_name = player_data.get("name")
        should_track_player = False
        if was_creating and flag_cleared and is_completed:
            # Character creation just completed.
            should_track_player = True
        elif was_creating and stage in ("review", "level_up", "complete"):
            # God Mode templates and later phases have stable character identity.
            should_track_player = True
        elif (not was_creating) and player_name:
            # Story mode or other modes: ensure player is tracked if present.
            should_track_player = True

        if should_track_player and player_name:
            entity_tracking = updated_game_state_dict.get("entity_tracking")
            if not isinstance(entity_tracking, dict):
                entity_tracking = {}
                updated_game_state_dict["entity_tracking"] = entity_tracking

            active_entities = entity_tracking.get("active_entities")
            if not isinstance(active_entities, list):
                active_entities = []
                entity_tracking["active_entities"] = active_entities

            # Add player character if not already present
            if player_name not in active_entities:
                active_entities.append(player_name)
                logging_util.info(
                    f"✅ Added player character '{player_name}' to active_entities"
                )

        # Apply automatic combat cleanup (sync defeated enemies between combat_state and npc_data)
        # Named NPCs are preserved and marked dead for continuity, while generic enemies are deleted.
        # Think Mode freezes state, so skip cleanup to avoid side effects.
        if not is_think_mode:
            updated_game_state_dict = apply_automatic_combat_cleanup(
                updated_game_state_dict, response.get("state_changes", {})
            )
        else:
            logging_util.info(
                "🧠 THINK_MODE_SAFETY: Skipping combat cleanup in Think Mode"
            )

        # Validate and auto-correct XP/level and time consistency
        # Use `or {}` to handle both missing and explicitly-null world_data in state_changes
        new_world_time = (
            response.get("state_changes", {}).get("world_data") or {}
        ).get("world_time")
        # DISCREPANCY DETECTION: Detect rewards state errors for LLM self-correction
        # Instead of server-side enforcement, we inform the LLM of issues via system_corrections
        # The LLM will fix them in the next inference (LLM Decides, Server Detects principle)
        if mode in (
            constants.MODE_REWARDS,
            constants.MODE_COMBAT,
            constants.MODE_CHARACTER,
        ):
            rewards_warnings: list[str] = []
            rewards_discrepancies = _detect_rewards_discrepancy(
                updated_game_state_dict,
                original_state_dict=original_state_for_level_check,
                warnings_out=rewards_warnings,
            )
            if rewards_discrepancies:
                prevention_extras.setdefault("system_corrections", []).extend(
                    rewards_discrepancies
                )
            if rewards_warnings:
                prevention_extras.setdefault("system_warnings", []).extend(
                    rewards_warnings
                )

        # SERVER-SIDE LEVEL-UP DETECTION: Check for level-up in ALL modes where
        # original_state_dict is available for XP comparison. This ensures
        # level-up is offered even when XP is awarded outside rewards pipeline
        # (e.g., God Mode, narrative milestones, manual XP grants)
        updated_game_state_dict = _check_and_set_level_up_pending(
            updated_game_state_dict, original_state_dict=original_state_for_level_check
        )

        # Validate and auto-correct state before persistence, capturing any corrections made
        updated_game_state_dict, state_corrections = validate_and_correct_state(
            updated_game_state_dict,
            previous_world_time=original_world_time,
            return_corrections=True,
        )

        # If rewards are now pending but we did NOT run RewardsAgent, run it once
        # to ensure user-visible rewards output.
        # NOTE: This must happen BEFORE post-combat detection to avoid false-positive
        # "no XP awarded" warnings when RewardsAgent awards XP in the followup.
        try:
            (
                updated_game_state_dict,
                llm_response_obj,
                prevention_extras,
            ) = await _process_rewards_followup(
                mode=mode,
                llm_response_obj=llm_response_obj,
                updated_game_state_dict=updated_game_state_dict,
                original_state_as_dict=original_state_for_level_check,
                original_world_time=original_world_time,
                story_context=story_context,
                selected_prompts=selected_prompts,
                use_default_world=use_default_world,
                user_id=user_id,
                prevention_extras=prevention_extras,
            )
        except Exception as e:
            logging_util.warning(f"⚠️ REWARDS_FOLLOWUP failed: {e}")

        # Re-validate state after rewards followup to capture any additional corrections
        # This ensures corrections from RewardsAgent state changes are surfaced to user
        updated_game_state_dict, followup_corrections = validate_and_correct_state(
            updated_game_state_dict,
            previous_world_time=original_world_time,
            return_corrections=True,
        )
        # Merge corrections (deduplicate since some may overlap)
        all_corrections = state_corrections + [
            c for c in followup_corrections if c not in state_corrections
        ]

        # Detect post-combat issues AFTER rewards followup to avoid false positives
        # when RewardsAgent awards XP during the followup
        updated_game_state_obj = GameState.from_dict(updated_game_state_dict)
        post_combat_warnings = []
        if updated_game_state_obj:
            # Compare final state against original to detect if XP was ever awarded
            final_pc = updated_game_state_dict.get("player_character_data", {})
            # Use the preserved pre-update snapshot for XP comparison to avoid
            # false negatives when update_state_with_changes mutates the current
            # state dict in-place.
            original_pc = original_state_for_level_check.get(
                "player_character_data", {}
            )
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
        extra_warnings = prevention_extras.get("system_warnings", [])
        
        # Extract system_warnings from LLM response debug_info (e.g., missing planning block, missing fields)
        llm_system_warnings = []
        if llm_response_obj and llm_response_obj.structured_response:
            debug_info = llm_response_obj.structured_response.debug_info
            if isinstance(debug_info, dict):
                llm_warnings = debug_info.get("system_warnings", [])
                if isinstance(llm_warnings, list):
                    llm_system_warnings = llm_warnings
        
        system_warnings = (
            all_corrections + rewards_corrections + post_combat_warnings + extra_warnings + llm_system_warnings
        )

        # Deduplicate warnings while preserving order
        if system_warnings:
            system_warnings = list(dict.fromkeys(system_warnings))

        # Increment player turn counter for non-GOD mode actions (but keep Think Mode frozen)
        if not is_god_mode and not is_think_mode:
            current_turn = updated_game_state_dict.get("player_turn", 0)
            updated_game_state_dict["player_turn"] = current_turn + 1
        elif is_god_mode:
            # GOD MODE: Process directives from LLM response
            # The GodModeAgent analyzes the user's message and returns directives
            # Format: {"directives": {"add": ["rule1", ...], "drop": ["rule2", ...]}}  # noqa: ERA001
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

            # Ensure god_mode_directives is a list (handle legacy dict format)
            if not isinstance(directives_list, list):
                logging_util.warning(
                    f"god_mode_directives was {type(directives_list).__name__}, converting to list"
                )
                directives_list = []
                ccs["god_mode_directives"] = directives_list

            # Process directives to drop (remove matching rules)
            if directives_to_drop:
                drop_lower = [d.strip().lower() for d in directives_to_drop if d]
                original_count = len(directives_list)

                def _get_rule_lower(d: Any) -> str:
                    """Safely extract and lowercase a rule, handling None values."""
                    if isinstance(d, dict):
                        rule = d.get("rule")
                        return rule.strip().lower() if isinstance(rule, str) else ""
                    return str(d).strip().lower() if d else ""

                directives_list[:] = [
                    d for d in directives_list if _get_rule_lower(d) not in drop_lower
                ]
                dropped_count = original_count - len(directives_list)
                if dropped_count > 0:
                    logging_util.info(f"GOD MODE: Dropped {dropped_count} directives")

            def _should_reject_directive(rule: str) -> bool:
                """
                Filter out directives that should not be saved.

                IMPORTANT: We only reject directives that are STATE VALUES or ONE-TIME EVENTS.
                BEHAVIORAL RULES (like "always apply Guidance", "always use advantage") MUST be kept.

                Reject:
                - State values that change: "Level is X", "HP is Y", "Gold is Z"
                - One-time events: "You just killed X", "You defeated Y"
                - Formatting: "Always include X in header" (handled by system prompts)

                Keep:
                - Behavioral rules: "Always apply Guidance", "Always use Enhance Ability"
                - Persistent mechanics: "Apply advantage to Stealth", "Always use Foresight"
                - Ongoing effects: "Maintain X buff", "Track Y condition" (if behavioral)
                """
                rule_lower = rule.lower().strip()

                # AI sometimes prefixes directives with "Rule: "
                # We strip it for matching against our patterns
                if rule_lower.startswith("rule:"):
                    rule_lower = rule_lower[5:].strip()

                # Reject patterns: State values (numbers that change)
                # These are specific values, not behavioral rules
                state_value_patterns = [
                    "level is",  # "Level is 42" - specific value
                    "real level is",  # "Real Level is 15" - specific value
                    "hp is",  # "HP is 50" - specific value
                    "gold is",  # "Gold is 1000" - specific value
                    "xp is",  # "XP is 5000" - specific value
                    "experience is",  # "Experience is 5000" - specific value
                    "soul coin is",  # "Soul Coin is 25k" - specific value
                    "base spell save dc is",  # Calculated value
                    "effective charisma is",  # Calculated value
                ]

                # Reject patterns: One-time events (history, not ongoing rules)
                # These patterns are more specific to catch actual one-time events,
                # not behavioral rules like "Killed enemies should drop loot"
                one_time_patterns = [
                    "you just",  # "You just killed X"
                    "you just killed",  # More specific than just "killed"
                    "you just defeated",  # More specific than just "defeated"
                    "you just completed",  # More specific than just "completed"
                ]

                # Reject patterns: Formatting instructions (system-level, not game rules)
                formatting_patterns = [
                    "always include",  # "Always include XP in header"
                    "format",  # Formatting instructions
                ]

                # Check for state value patterns (must be exact value, not behavioral)
                # e.g., "Level is 42" is bad, but "Level affects X" might be OK
                for pattern in state_value_patterns:
                    if pattern in rule_lower:
                        # Additional check: if it's followed by a number or specific value, reject
                        # But if it's behavioral like "Level affects calculations", allow it
                        pattern_idx = rule_lower.find(pattern)
                        if pattern_idx != -1:
                            after_pattern = rule_lower[pattern_idx + len(pattern):].strip()
                            # If followed by a number or "=", it's a state value
                            if after_pattern and (after_pattern[0].isdigit() or after_pattern.startswith('=')):
                                return True

                # Check for one-time events (with additional context check)
                # Only reject if it's clearly a one-time event, not a behavioral rule
                for pattern in one_time_patterns:
                    if pattern in rule_lower:
                        pattern_idx = rule_lower.find(pattern)
                        if pattern_idx != -1:
                            # Get context from original rule to preserve capitalization for proper noun detection
                            # We find the pattern in rule_lower but apply the same offset to original rule
                            # This is safe since rule_lower has same length as rule
                            after_pattern_orig = rule[rule.lower().find(pattern) + len(pattern):].strip()
                            if after_pattern_orig:
                                behavioral_indicators = ["should", "grant", "affect", "provide", "give", "drop", "always"]
                                is_behavioral = any(indicator in after_pattern_orig.lower() for indicator in behavioral_indicators)
                                if not is_behavioral:
                                    # Check if it looks like a one-time event (specific entity/event)
                                    after_lower = after_pattern_orig.lower()
                                    if after_lower.startswith(("the ", "a ", "an ")) or after_pattern_orig[0].isupper():
                                        return True

                # Check for formatting instructions (with context validation)
                # Only reject if it's clearly formatting, not behavioral rules
                for pattern in formatting_patterns:
                    if pattern in rule_lower:
                        pattern_idx = rule_lower.find(pattern)
                        if pattern_idx != -1:
                            after_pattern = rule_lower[pattern_idx + len(pattern):].strip()
                            # Formatting patterns are usually about display/headers, not game mechanics
                            # If followed by formatting keywords, reject; otherwise allow behavioral rules
                            formatting_keywords = ["in header", "in title", "in display", "as text", "as string"]
                            is_formatting = any(keyword in after_pattern for keyword in formatting_keywords)
                            if is_formatting:
                                return True
                            # If it's about game mechanics (bonus, damage, effect), allow it
                            behavioral_keywords = ["bonus", "damage", "effect", "grant", "provide", "apply", "affect"]
                            if any(keyword in after_pattern for keyword in behavioral_keywords):
                                continue  # Don't reject - it's a behavioral rule
                            # If pattern is "format" alone without context, be more conservative
                            if pattern == "format" and len(after_pattern) < 10:
                                # Short "format" phrases are likely formatting instructions
                                return True

                # Allow everything else (behavioral rules, persistent mechanics, etc.)
                return False

            for new_rule in directives_to_add:
                if not new_rule or not isinstance(new_rule, str):
                    continue
                # Strip whitespace from new rule
                new_rule_clean = new_rule.strip()
                if not new_rule_clean:
                    continue

                # Filter out problematic directives (server-side validation)
                if _should_reject_directive(new_rule_clean):
                    logging_util.warning(
                        f"GOD MODE: Rejected problematic directive (should be in state_updates, not directives): {new_rule_clean[:100]}"
                    )
                    continue

                # Case-insensitive duplicate check
                existing_rules_lower = [
                    (
                        d.get("rule", "").strip().lower()
                        if isinstance(d, dict)
                        else str(d).strip().lower()
                    )
                    for d in directives_list
                    if (isinstance(d, dict) and d.get("rule"))
                    or (not isinstance(d, dict) and d)
                ]
                if new_rule_clean.lower() not in existing_rules_lower:
                    directives_list.append(
                        {
                            "rule": new_rule_clean,
                            "added": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
                        }
                    )
                    logging_util.info(f"GOD MODE DIRECTIVE ADDED: {new_rule_clean}")

        # Annotate world_events entries with turn/scene numbers for UI display
        player_turn = updated_game_state_dict.get("player_turn", 1)
        updated_game_state_dict = annotate_world_events_with_turn_scene(
            updated_game_state_dict, player_turn
        )

        # Capture any pending_system_corrections set by LLM (e.g. God Mode)
        # At this point, OLD corrections were already cleared earlier in the function
        # right before the state merge, so any present now are NEW from LLM state_updates.
        llm_pending_corrections_list = _normalize_system_corrections(
            updated_game_state_dict.pop("pending_system_corrections", None)
        )

        llm_reward_corrections = _filter_reward_corrections(
            llm_pending_corrections_list
        )
        llm_non_reward_corrections = [
            correction
            for correction in llm_pending_corrections_list
            if not _is_reward_correction(correction)
        ]

        # Combine with validator-generated corrections (reward-related only)
        validator_corrections_list = _normalize_system_corrections(
            prevention_extras.get("system_corrections")
        )

        reward_corrections = llm_reward_corrections + _filter_reward_corrections(
            validator_corrections_list
        )
        all_corrections = llm_non_reward_corrections + reward_corrections

        if all_corrections:
            # Deduplicate while preserving order
            # Note: all_corrections is guaranteed to be list[str] thanks to _normalize_system_corrections
            pending_corrections = list(dict.fromkeys(all_corrections))
            updated_game_state_dict["pending_system_corrections"] = pending_corrections
            logging_util.info(
                f"📋 Persisted {len(pending_corrections)} system_corrections "
                "to game_state.pending_system_corrections"
            )

        # Then save the AI response with structured fields if available
        ai_response_text = llm_response_obj.narrative_text

        # Extract structured fields from AI response for storage
        structured_fields = _ensure_session_header_resources(
            structured_fields_utils.extract_structured_fields(llm_response_obj),
            updated_game_state_dict,
        )
        structured_fields.update(prevention_extras)

        # Persist server-side level-up injections so stored story entries
        # reflect the same narrative/choices delivered to the user.
        if not is_god_mode:
            injected_planning_block = _inject_levelup_choices_if_needed(
                structured_fields.get("planning_block"),
                updated_game_state_dict,
            )
            if injected_planning_block is not None:
                structured_fields["planning_block"] = injected_planning_block

            injected_narrative = _inject_levelup_narrative_if_needed(
                ai_response_text,
                structured_fields.get("planning_block"),
                updated_game_state_dict,
            )
            if injected_narrative != ai_response_text:
                ai_response_text = injected_narrative
                llm_response_obj.narrative_text = injected_narrative

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

        # Persist state + story entries.
        if is_mock_services_mode():
            _persist_turn_to_firestore(
                user_id,
                campaign_id,
                mode=mode,
                user_input=user_input,
                ai_response_text=ai_response_text,
                structured_fields=structured_fields,
                updated_game_state_dict=updated_game_state_dict,
            )
        else:
            await asyncio.to_thread(
                _persist_turn_to_firestore,
                user_id,
                campaign_id,
                mode=mode,
                user_input=user_input,
                ai_response_text=ai_response_text,
                structured_fields=structured_fields,
                updated_game_state_dict=updated_game_state_dict,
            )

        # Get debug mode for narrative text processing
        debug_mode = (
            current_game_state.debug_mode
            if hasattr(current_game_state, "debug_mode")
            else False
        )

        # Extract narrative text with proper debug mode handling
        get_narrative_text = getattr(llm_response_obj, "get_narrative_text", None)
        if callable(get_narrative_text):
            final_narrative = get_narrative_text(debug_mode=debug_mode)
            if not isinstance(final_narrative, str):
                final_narrative = llm_response_obj.narrative_text
        else:
            final_narrative = llm_response_obj.narrative_text

        # Defensive check: ensure narrative is never None or empty
        if not final_narrative or not isinstance(final_narrative, str):
            logging_util.warning(
                f"⚠️ EMPTY_NARRATIVE in process_action_unified: narrative_text={final_narrative}, "
                f"type={type(final_narrative)}, has_structured_response={llm_response_obj.structured_response is not None}"
            )
            # Fallback to structured response narrative if available
            if llm_response_obj.structured_response and hasattr(llm_response_obj.structured_response, "narrative"):
                final_narrative = llm_response_obj.structured_response.narrative or "[Error: Empty narrative from LLM]"
            else:
                final_narrative = "[Error: Empty narrative from LLM]"

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

        # NOTE: Level-up handling is fully delegated to the LLM. The LLM receives
        # rewards_pending in game state context and should recognize level-up eligibility
        # to generate appropriate rewards boxes per rewards_system_instruction.md.

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
            # agent_mode: single source of truth for which agent was selected
            "agent_mode": getattr(llm_response_obj, "agent_mode", None),
        }

        if include_raw_llm_payloads:
            metadata = getattr(llm_response_obj, "processing_metadata", {}) or {}
            if "raw_request_payload" in metadata:
                unified_response["raw_request_payload"] = metadata[
                    "raw_request_payload"
                ]
            if "raw_response_text" in metadata:
                unified_response["raw_response_text"] = metadata["raw_response_text"]

        # Include state fields only when debug mode is enabled (shows MORE info)
        if debug_mode:
            unified_response["state_updates"] = response.get("state_changes") or {}
            # CRITICAL: Also include world_events from structured_fields for living world UI
            # world_events is stored in structured_fields but not in response.state_changes
            if structured_fields.get("world_events"):
                unified_response["world_events"] = structured_fields["world_events"]
                # Also merge into state_updates for frontend compatibility
                if not unified_response.get("state_updates"):
                    unified_response["state_updates"] = {}
                unified_response["state_updates"]["world_events"] = structured_fields[
                    "world_events"
                ]

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
            # Legacy dice_rolls/dice_audit_events - prefer extraction from action_resolution
            # but allow direct population for backward compatibility
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
            if hasattr(structured_response, "social_hp_challenge"):
                unified_response["social_hp_challenge"] = (
                    structured_response.social_hp_challenge
                )
            # Include action_resolution and outcome_resolution (backward compat)
            # Legacy dice_rolls/dice_audit_events fields; extraction from action_resolution takes precedence.
            add_action_resolution_to_response(structured_response, unified_response)
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

        # SERVER-SIDE LEVEL-UP CHOICE INJECTION
        # When level_up_available=true, ensure planning_block has required choices
        # This prevents the "text shown but no buttons" failure mode where users
        # see "LEVEL UP AVAILABLE!" but have no way to click to level up.
        # Skip injection in GOD MODE responses (god: choices required there).
        if not unified_response.get("god_mode_response"):
            injected_planning_block = _inject_levelup_choices_if_needed(
                unified_response.get("planning_block"),
                updated_game_state_dict,
            )
            if injected_planning_block is not None:
                unified_response["planning_block"] = injected_planning_block

            # SERVER-SIDE LEVEL-UP NARRATIVE INJECTION
            injected_narrative = _inject_levelup_narrative_if_needed(
                unified_response.get("narrative"),
                unified_response.get("planning_block"),
                updated_game_state_dict,
            )
            if injected_narrative != unified_response.get("narrative"):
                unified_response["narrative"] = injected_narrative
                unified_response["response"] = injected_narrative
                unified_response["story"] = process_story_for_display(
                    [{"text": injected_narrative}], debug_mode
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

        # Add system corrections for LLM self-correction in next inference
        # These are injected into the next prompt via system_corrections field
        # Filter to only reward-related corrections for persistence
        reward_system_corrections = _filter_reward_corrections(
            prevention_extras.get("system_corrections", [])
        )
        if reward_system_corrections:
            # Deduplicate while preserving order (same as we do for persistence)
            unified_response["system_corrections"] = list(
                dict.fromkeys(reward_system_corrections)
            )
            for correction in unified_response["system_corrections"]:
                logging_util.warning(f"SYSTEM CORRECTION QUEUED: {correction}")

        # Add system warnings from validation corrections and post-combat checks
        if system_warnings:
            unified_response["system_warnings"] = system_warnings
            for warning in system_warnings:
                logging_util.warning(f"SYSTEM WARNING: {warning}")

        # Track story mode sequence ID for character mode.
        #
        # NOTE: Skip in MOCK_SERVICES_MODE to keep tight concurrency tests stable
        # (mock Firestore is in-memory and this field isn't needed for those tests).
        # Read item_exploit_blocked from processing_metadata if item validation detected an exploit
        metadata = getattr(llm_response_obj, "processing_metadata", {}) or {}
        item_exploit_blocked = metadata.get("item_exploit_blocked", False)
        if (
            mode == constants.MODE_CHARACTER
            and not item_exploit_blocked
            and not is_mock_services_mode()
        ):
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
                # Re-merge world_events if present (may have been added earlier but overwritten)
                if structured_fields.get("world_events"):
                    unified_response["state_updates"]["world_events"] = (
                        structured_fields["world_events"]
                    )

            # Also update the game state dict that was already saved
            final_game_state_dict = update_state_with_changes(
                updated_game_state_dict, story_id_update
            )
            # Validate the final state before persisting
            final_game_state_dict = validate_game_state_updates(
                final_game_state_dict
            )

            await asyncio.to_thread(
                _update_campaign_game_state,
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

        # Fetch campaign metadata/story and game state concurrently (blocking I/O).
        (campaign_data, story), (
            game_state,
            was_cleaned,
            num_cleaned,
            user_settings,
        ) = await asyncio.gather(
            asyncio.to_thread(
                firestore_service.get_campaign_by_id, user_id, campaign_id
            ),
            asyncio.to_thread(
                _prepare_game_state_with_user_settings, user_id, campaign_id
            ),
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

        game_state_dict = game_state.to_dict()

        # Get debug mode from user settings and apply to game state (blocking I/O)
        debug_mode = (
            user_settings.get("debug_mode", False) if user_settings else False
        )
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

        # Convert story context to text format using enhanced formatting
        # This uses the same logic as the CLI download script for consistency
        story_text = document_generator.get_story_text_from_context_enhanced(
            story_context, include_scenes=True
        )

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
    campaigns, _, _ = firestore_service.get_campaigns_for_user(user_id)
    return campaigns


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

        # Get cursor for pagination
        start_after = request_data.get("start_after")

        # Get campaigns with pagination and sorting (blocking I/O - run in thread)
        # Include total count only on first page (when start_after is None)
        include_total = start_after is None
        campaigns, next_cursor, total_count = await asyncio.to_thread(
            firestore_service.get_campaigns_for_user, user_id, limit, sort_by, start_after, include_total
        )

        # Clean JSON artifacts from campaign text fields
        if campaigns:
            text_fields_to_clean = ["description", "prompt", "title"]
            for campaign in campaigns:
                for field in text_fields_to_clean:
                    if field in campaign and isinstance(campaign[field], str):
                        campaign[field] = clean_json_artifacts(campaign[field])

        result = {
            KEY_SUCCESS: True,
            "campaigns": campaigns,
        }

        # Include pagination info if there are more results
        if next_cursor:
            result["next_cursor"] = next_cursor
            result["has_more"] = True
        else:
            result["has_more"] = False

        # Include total count if available (only on first page)
        if total_count is not None:
            result["total_count"] = total_count

        return result

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
            allowed_models.update(k.lower() for k in constants.GEMINI_MODEL_MAPPING)
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
        logging_util.debug("COMBAT CLEANUP CHECK: No combatants found, skipping cleanup")
        return updated_state_dict

    # CRITICAL FIX: Always attempt cleanup if combatants exist
    # This handles ALL cases:
    # 1. Combat ongoing with new defeats
    # 2. Combat ending with pre-existing defeats
    # 3. State updates without explicit combat_state changes but with defeated enemies
    logging_util.debug(
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
    original_state_for_level_check = copy.deepcopy(current_state_dict_before_update)
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

    # SERVER-SIDE LEVEL-UP DETECTION for God Mode SET
    updated_state = _check_and_set_level_up_pending(
        updated_state, original_state_dict=original_state_for_level_check
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
        original_state_for_level_check = copy.deepcopy(current_state_dict)
        previous_combat_state = copy.deepcopy(
            current_state_dict.get("combat_state", {})
        )

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

        # SERVER-SIDE LEVEL-UP DETECTION for God Mode UPDATE_STATE
        validated_state_dict = _check_and_set_level_up_pending(
            validated_state_dict, original_state_dict=original_state_for_level_check
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
                    original_state_for_level_check.get("player_character_data", {})
                )
                if final_xp <= original_xp:
                    post_combat_warnings = (
                        updated_game_state_obj.detect_post_combat_issues(
                            previous_combat_state, state_changes
                        )
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

        # NOTE: Level-up handling is fully delegated to the LLM. The LLM receives
        # rewards_pending in game state context and should recognize level-up eligibility
        # to generate appropriate rewards boxes per rewards_system_instruction.md.

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
