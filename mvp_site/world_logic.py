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
import json
import os
import re
import tempfile
import uuid
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
    structured_fields_utils,
)
from mvp_site.custom_types import CampaignId, UserId
from mvp_site.debug_hybrid_system import clean_json_artifacts, process_story_for_display
from mvp_site.firestore_service import (
    _truncate_log_json,
    get_user_settings,
    update_state_with_changes,
)
from mvp_site.game_state import GameState
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
MAX_TEMPORAL_CORRECTION_ATTEMPTS = 2  # Max retries before accepting response


def _world_time_to_comparable(world_time: dict[str, Any] | None) -> tuple[int, ...]:
    """Convert world_time dict to comparable tuple (year, month_num, day, hour, min, sec, microsec).

    Returns tuple that can be compared with < > operators.
    Missing fields default to 0.
    """
    if not world_time or not isinstance(world_time, dict):
        return (0, 0, 0, 0, 0, 0, 0)

    # Month name to number mapping for Forgotten Realms calendar
    month_map = {
        "hammer": 1, "alturiak": 2, "ches": 3, "tarsakh": 4,
        "mirtul": 5, "kythorn": 6, "flamerule": 7, "eleasis": 8,
        "eleint": 9, "marpenoth": 10, "uktar": 11, "nightal": 12,
        # Common abbreviations
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    year = world_time.get("year", 0)
    month = world_time.get("month", 0)
    if isinstance(month, str):
        month = month_map.get(month.lower(), 0)
    day = world_time.get("day", 0)
    hour = world_time.get("hour", 0)
    minute = world_time.get("minute", 0)
    second = world_time.get("second", 0)
    microsecond = world_time.get("microsecond", 0)

    return (year, month, day, hour, minute, second, microsecond)


def _extract_world_time_from_response(llm_response: Any) -> dict[str, Any] | None:
    """Extract world_time from LLM response state_updates."""
    try:
        state_updates = llm_response.get_state_updates() if hasattr(llm_response, "get_state_updates") else {}
        world_data = state_updates.get("world_data", {})
        return world_data.get("world_time")
    except Exception:
        return None


def _check_temporal_violation(
    old_time: dict[str, Any] | None,
    new_time: dict[str, Any] | None,
) -> bool:
    """Check if new_time is backward from old_time (violation).

    Returns True if violation detected, False if OK.
    """
    if not old_time or not new_time:
        return False  # Can't validate without both times

    old_tuple = _world_time_to_comparable(old_time)
    new_tuple = _world_time_to_comparable(new_time)

    # Violation if new time is less than or equal to old time
    # (equal is also a violation - time should always advance)
    return new_tuple <= old_tuple


def _format_world_time_for_prompt(world_time: dict[str, Any] | None) -> str:
    """Format world_time dict for human-readable prompt display."""
    if not world_time:
        return "Unknown"

    year = world_time.get("year", "????")
    month = world_time.get("month", "??")
    day = world_time.get("day", "??")
    hour = world_time.get("hour", 0)
    minute = world_time.get("minute", 0)
    time_of_day = world_time.get("time_of_day", "")

    time_str = f"{hour:02d}:{minute:02d}"
    if time_of_day:
        time_str = f"{time_of_day} ({time_str})"

    return f"{year} DR, {month} {day}, {time_str}"


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

    correction = f"""⚠️ TEMPORAL VIOLATION - FULL REGENERATION REQUIRED

Your previous response was REJECTED because time went BACKWARD:
- CORRECT current state: {old_time_str} at {old_loc}
- YOUR invalid output: {new_time_str} at {new_loc}

The TEMPORAL CONSISTENCY PROTOCOL requires time to ALWAYS move FORWARD.
Your response appears to have lost track of the story context.

MANDATORY REGENERATION INSTRUCTIONS:
1. Continue from the CORRECT context: {old_time_str} at {old_loc}
2. Time in your response MUST be AFTER {old_time_str}
3. Location should continue logically from {old_loc}
4. Do NOT reference {new_loc} if that was incorrect

Original player action to respond to:
{original_user_input}

Generate a NEW response that properly continues the story with correct temporal progression."""

    return correction


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

    contains_xp = re.search(
        r"\b(XP|experience)\b", session_header, flags=re.IGNORECASE
    )
    contains_gold = re.search(
        r"\b(Gold|gp)\b", session_header, flags=re.IGNORECASE
    )

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
        opening_story_response = await asyncio.to_thread(
            llm_service.get_initial_story,
            prompt,
            user_id,
            selected_prompts,
            generate_companions,
            use_default_world,
        )

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
    try:
        # Extract parameters
        user_id = request_data.get("user_id")
        campaign_id = request_data.get("campaign_id")
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

        # Get campaign settings
        selected_prompts = campaign_data.get("selected_prompts", [])
        use_default_world = campaign_data.get("use_default_world", False)

        # Extract current world_time and location for temporal validation
        old_world_time = current_game_state.world_data.get("world_time") if hasattr(current_game_state, "world_data") else None
        old_location = current_game_state.world_data.get("current_location") if hasattr(current_game_state, "world_data") else None

        # Process regular game action with LLM (CRITICAL: blocking I/O - 10-30+ seconds!)
        # This is the most important call to run in a thread to prevent blocking
        # TEMPORAL VALIDATION LOOP: Retry if LLM generates backward time
        original_user_input = user_input
        temporal_correction_attempts = 0
        llm_response_obj = None

        while temporal_correction_attempts <= MAX_TEMPORAL_CORRECTION_ATTEMPTS:
            llm_response_obj = await asyncio.to_thread(
                llm_service.continue_story,
                user_input,
                mode,
                story_context,
                current_game_state,
                selected_prompts,
                use_default_world,
                user_id,  # Pass user_id to enable user model preference selection
            )

            # Check for temporal violation (time going backward)
            new_world_time = _extract_world_time_from_response(llm_response_obj)

            if not _check_temporal_violation(old_world_time, new_world_time):
                # No violation - time is moving forward, accept response
                if temporal_correction_attempts > 0:
                    logging_util.info(
                        f"✅ TEMPORAL_CORRECTION: Response accepted after {temporal_correction_attempts} correction(s)"
                    )
                break

            # Temporal violation detected!
            temporal_correction_attempts += 1

            if temporal_correction_attempts > MAX_TEMPORAL_CORRECTION_ATTEMPTS:
                # Max retries exceeded - log warning and accept the response anyway
                logging_util.warning(
                    f"⚠️ TEMPORAL_VIOLATION: Max correction attempts ({MAX_TEMPORAL_CORRECTION_ATTEMPTS}) exceeded. "
                    f"Accepting response with backward time: {_format_world_time_for_prompt(new_world_time)} "
                    f"< {_format_world_time_for_prompt(old_world_time)}"
                )
                break

            # Extract new location for error message
            new_state_updates = llm_response_obj.get_state_updates() if hasattr(llm_response_obj, "get_state_updates") else {}
            new_location = new_state_updates.get("world_data", {}).get("current_location", old_location)

            # Log the violation and retry
            logging_util.warning(
                f"🚨 TEMPORAL_VIOLATION (attempt {temporal_correction_attempts}/{MAX_TEMPORAL_CORRECTION_ATTEMPTS}): "
                f"Time went backward from {_format_world_time_for_prompt(old_world_time)} to "
                f"{_format_world_time_for_prompt(new_world_time)}. Requesting regeneration."
            )

            # Build correction prompt and retry
            user_input = _build_temporal_correction_prompt(
                original_user_input,
                old_world_time,
                new_world_time,
                old_location,
                new_location,
            )

        # Convert LLMResponse to dict format for compatibility
        response = {
            "story": llm_response_obj.narrative_text,
            "state_changes": llm_response_obj.get_state_updates(),
        }

        # Update game state with changes
        updated_game_state_dict = update_state_with_changes(
            current_game_state.to_dict(), response.get("state_changes", {})
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

        # Process story for display (convert narrative text to story entries format)
        # Use "text" field to match translation layer expectations in main.py
        story_entries = [{"text": final_narrative}]
        processed_story = process_story_for_display(story_entries, debug_mode)

        # Calculate sequence_id (critical missing field)
        # AI response should be next sequential number after user input
        # User input gets len(story_context) + 1, AI response gets len(story_context) + 2
        sequence_id = len(story_context) + 2

        # Calculate user_scene_number for this AI response (critical missing field)
        # Count existing gemini responses in story_context
        user_scene_number = (
            sum(1 for entry in story_context if entry.get("actor") == "gemini") + 1
        )

        # Extract structured fields from LLM response (critical missing fields)
        structured_response = getattr(llm_response_obj, "structured_response", None)

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
            if hasattr(structured_response, "resources"):
                unified_response["resources"] = structured_response.resources
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
            allowed_models = {m.lower() for m in constants.ALLOWED_GEMINI_MODELS}
            if model_lower not in allowed_models:
                return create_error_response("Invalid model selection")
            settings_to_update["gemini_model"] = model

        if "openrouter_model" in settings_data:
            model = settings_data["openrouter_model"]
            if not isinstance(model, str):
                return create_error_response("Invalid model selection")

            allowed_openrouter = {m.lower() for m in constants.ALLOWED_OPENROUTER_MODELS}
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

    updated_state = update_state_with_changes(
        current_state_dict_before_update, proposed_changes
    )
    updated_state = apply_automatic_combat_cleanup(updated_state, proposed_changes)
    logging_util.info(
        f"GOD_MODE_SET state AFTER update:\n{_truncate_log_json(updated_state, json_serializer=json_default_serializer)}"
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

        # Perform an update
        updated_state_dict = update_state_with_changes(
            current_state_dict, state_changes
        )
        updated_state_dict = apply_automatic_combat_cleanup(
            updated_state_dict, state_changes
        )

        # Convert back to GameState object after the update to validate
        final_game_state = GameState.from_dict(updated_state_dict)
        if final_game_state is None:
            logging_util.error(
                "PROCESS_ACTION: GameState.from_dict returned None after update; rejecting GOD_MODE_UPDATE_STATE"
            )
            return create_error_response(
                "Unable to reconstruct game state after applying changes.", 500
            )

        firestore_service.update_campaign_game_state(
            user_id, campaign_id, final_game_state.to_dict()
        )

        log_message = format_game_state_updates(state_changes, for_html=False)
        return {
            KEY_SUCCESS: True,
            KEY_RESPONSE: f"[System Message: The following state changes were applied via GOD MODE]\n{log_message}",
        }

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
