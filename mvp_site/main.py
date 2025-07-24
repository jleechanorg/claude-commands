"""
WorldArchitect.AI - Main Flask Application

This is the primary Flask application entry point for WorldArchitect.AI, an AI-powered
tabletop RPG platform that serves as a digital D&D 5e Game Master.

Architecture:
- Flask web server with CORS support
- Firebase authentication and Firestore database
- Gemini AI service integration for story generation
- Real-time game state management
- Document export functionality
- Debug mode and god-mode commands for testing

Key Components:
- Campaign management (create, read, update, delete)
- Interactive story generation with user input
- Game state synchronization and validation
- Export campaigns to PDF/DOCX/TXT formats
- Authentication and authorization
- Test command runners for UI and HTTP testing

Dependencies:
- Flask: Web framework
- Firebase: Authentication and database
- Gemini AI: Story generation and game logic
- Bootstrap: Frontend CSS framework
- Various custom services for game logic
"""

# Standard library imports
import argparse
import collections
import json
import logging
import os
import random
import subprocess
import sys
import traceback
import uuid
from functools import wraps
from typing import Dict, List, Optional, Any, Union, Tuple, Callable

import constants
from custom_types import ApiResponse, CampaignData, UserId, CampaignId

# Local service imports
import document_generator

# Firebase imports
import firebase_admin
import logging_util
from debug_mode_parser import DebugModeParser
from firebase_admin import auth

# Flask and web imports
from flask import Flask, jsonify, request, send_file, send_from_directory, Response, Request
from flask_cors import CORS
from token_utils import log_with_tokens

from firestore_service import (
    _truncate_log_json,
    json_default_serializer,
    update_state_with_changes,
)
from game_state import GameState
from debug_hybrid_system import process_story_for_display

# Service imports that may be conditionally used
import gemini_service as real_gemini_service
import firestore_service as real_firestore_service
from mocks import mock_gemini_service_wrapper
from mocks import mock_firestore_service_wrapper
import structured_fields_utils

# --- Service Selection Logic ---
# Granular mock control - check individual service mock flags
use_mock_gemini = os.environ.get("USE_MOCK_GEMINI", "").lower() in ["true", "1", "yes"]
use_mock_firebase = os.environ.get("USE_MOCK_FIREBASE", "").lower() in [
    "true",
    "1",
    "yes",
]

# Legacy support - USE_MOCKS sets both if individual flags not set
if os.environ.get("USE_MOCKS", "").lower() in ["true", "1", "yes"]:
    # Only apply USE_MOCKS if individual flags aren't explicitly set
    if "USE_MOCK_GEMINI" not in os.environ:
        use_mock_gemini = True
    if "USE_MOCK_FIREBASE" not in os.environ:
        use_mock_firebase = True

# Choose which service to use based on flags
if use_mock_gemini:
    gemini_service = mock_gemini_service_wrapper
else:
    gemini_service = real_gemini_service

# Choose which firestore service to use based on flags  
if use_mock_firebase:
    firestore_service = mock_firestore_service_wrapper
else:
    firestore_service = real_firestore_service

# --- CONSTANTS ---
# API Configuration
CORS_RESOURCES = {r"/api/*": {"origins": "*"}}

# Request Headers
HEADER_AUTH = "Authorization"
HEADER_TEST_BYPASS = "X-Test-Bypass-Auth"
HEADER_TEST_USER_ID = "X-Test-User-ID"

# Logging Configuration
LOG_DIRECTORY = "/tmp/worldarchitectai_logs"

# Request/Response Data Keys (specific to main.py)
KEY_PROMPT = "prompt"
KEY_SELECTED_PROMPTS = "selected_prompts"
KEY_USER_INPUT = "input"
KEY_CAMPAIGN_ID = "campaign_id"
KEY_SUCCESS = "success"
KEY_ERROR = "error"
KEY_TRACEBACK = "traceback"
KEY_MESSAGE = "message"
KEY_CAMPAIGN = "campaign"
KEY_STORY = "story"
KEY_DETAILS = "details"
KEY_RESPONSE = "response"

# Roles & Modes
DEFAULT_TEST_USER = "test-user"

# Campaign Generation Constants
RANDOM_CHARACTERS = [
    "A brave warrior seeking to prove their worth in battle",
    "A cunning rogue with a mysterious past and hidden agenda",
    "A wise wizard devoted to uncovering ancient magical secrets",
    "A noble paladin sworn to protect the innocent from evil",
    "A skilled ranger who knows the wilderness like no other",
    "A charismatic bard who weaves magic through music and stories",
    "A devout cleric blessed with divine power to heal and smite",
    "A fierce barbarian driven by primal instincts and tribal honor",
    "A stealthy monk trained in martial arts and inner discipline",
    "A nature-loving druid who can shapeshift and command beasts",
]

RANDOM_SETTINGS = [
    "The bustling city of Waterdeep, where intrigue and adventure await around every corner",
    "The mystical Feywild, a realm where magic runs wild and reality bends to emotion",
    "The treacherous Underdark, a vast network of caverns filled with dangerous creatures",
    "The frozen lands of Icewind Dale, where survival means everything in the harsh tundra",
    "The desert kingdom of Calimshan, where genies and merchants rule with equal power",
    "The pirate-infested Sword Coast, where gold and glory are won by blade and cunning",
    "The haunted moors of Barovia, trapped in eternal mist and ruled by dark powers",
    "The floating city of Sharn, where magic and technology create vertical neighborhoods",
    "The jungle continent of Chult, where ancient ruins hide deadly secrets and treasures",
    "The war-torn kingdom of Cyre, struggling to rebuild after magical devastation",
]


# --- END CONSTANTS ---


def _prepare_game_state(user_id: UserId, campaign_id: CampaignId) -> Tuple[GameState, bool, int]:
    """
    Load and prepare game state, including legacy cleanup.

    This function handles the initialization and cleanup of game state data from Firestore.
    It performs automatic migration of legacy state structures and returns a clean GameState object.

    Key Responsibilities:
    - Fetches game state from Firestore
    - Ensures valid GameState object initialization
    - Performs legacy state cleanup (removes deprecated fields)
    - Updates Firestore with cleaned state if necessary
    - Logs cleanup operations for debugging

    Args:
        user_id: Firebase user ID
        campaign_id: Campaign identifier from Firestore

    Returns:
        tuple: (current_game_state, was_cleaned, num_cleaned)
            - current_game_state: GameState object ready for use
            - was_cleaned: boolean indicating if cleanup was performed
            - num_cleaned: integer count of cleaned entries
    """
    current_game_state_doc = firestore_service.get_campaign_game_state(
        user_id, campaign_id
    )

    # Ensure current_game_state is always a valid GameState object
    if current_game_state_doc:
        current_game_state = GameState.from_dict(current_game_state_doc.to_dict())
    else:
        current_game_state = GameState()

    # Perform cleanup on a dictionary copy
    cleaned_state_dict, was_cleaned, num_cleaned = _cleanup_legacy_state(
        current_game_state.to_dict()
    )
    if was_cleaned:
        # If cleaned, update the main object from the cleaned dictionary
        current_game_state = GameState.from_dict(cleaned_state_dict)
        firestore_service.update_campaign_game_state(
            user_id, campaign_id, current_game_state.to_dict()
        )
        logging_util.info(
            f"Legacy state cleanup complete. Removed {num_cleaned} entries."
        )

    return current_game_state, was_cleaned, num_cleaned


def _handle_set_command(user_input: str, current_game_state: GameState, user_id: UserId, campaign_id: CampaignId) -> Optional[Response]:
    """
    Handle GOD_MODE_SET command.

    Args:
        user_input: User input string
        current_game_state: Current GameState object
        user_id: User ID
        campaign_id: Campaign ID

    Returns:
        Flask response or None if not a SET command
    """
    GOD_MODE_SET_COMMAND = "GOD_MODE_SET:"
    user_input_stripped = user_input.strip()

    if not user_input_stripped.startswith(GOD_MODE_SET_COMMAND):
        return None

    payload_str = user_input_stripped[len(GOD_MODE_SET_COMMAND) :]
    logging_util.info(f"--- GOD_MODE_SET received for campaign {campaign_id} ---")
    logging_util.info(f"GOD_MODE_SET raw payload:\\n---\\n{payload_str}\\n---")

    proposed_changes = parse_set_command(payload_str)
    logging_util.info(
        f"GOD_MODE_SET parsed changes to be merged:\\n{_truncate_log_json(proposed_changes)}"
    )

    if not proposed_changes:
        logging_util.warning("GOD_MODE_SET command resulted in no valid changes.")
        return jsonify(
            {
                KEY_SUCCESS: True,
                KEY_RESPONSE: "[System Message: The GOD_MODE_SET command was received, but contained no valid instructions or was empty.]",
            }
        )

    current_state_dict_before_update = current_game_state.to_dict()
    logging_util.info(
        f"GOD_MODE_SET state BEFORE update:\\n{_truncate_log_json(current_state_dict_before_update)}"
    )

    updated_state = update_state_with_changes(
        current_state_dict_before_update, proposed_changes
    )
    updated_state = apply_automatic_combat_cleanup(updated_state, proposed_changes)
    logging_util.info(
        f"GOD_MODE_SET state AFTER update:\\n{_truncate_log_json(updated_state)}"
    )

    firestore_service.update_campaign_game_state(user_id, campaign_id, updated_state)

    # Log the formatted changes for both server and chat
    log_message_for_log = format_state_changes(proposed_changes, for_html=False)
    logging_util.info(
        f"GOD_MODE_SET changes applied for campaign {campaign_id}:\\n{log_message_for_log}"
    )

    log_message_for_chat = format_state_changes(proposed_changes, for_html=True)

    logging_util.info(f"--- GOD_MODE_SET for campaign {campaign_id} complete ---")

    return jsonify(
        {KEY_SUCCESS: True, KEY_RESPONSE: f"[System Message]<br>{log_message_for_chat}"}
    )


def _handle_ask_state_command(user_input: str, current_game_state: GameState, user_id: UserId, campaign_id: CampaignId) -> Optional[Response]:
    """
    Handle GOD_ASK_STATE command.

    Returns:
        Flask response or None if not ASK_STATE command
    """
    GOD_ASK_STATE_COMMAND = "GOD_ASK_STATE"

    if user_input.strip() != GOD_ASK_STATE_COMMAND:
        return None

    game_state_dict = current_game_state.to_dict()
    game_state_json = json.dumps(
        game_state_dict, indent=2, default=json_default_serializer
    )

    firestore_service.add_story_entry(
        user_id, campaign_id, constants.ACTOR_USER, user_input, constants.MODE_CHARACTER
    )

    response_text = f"```json\\n{game_state_json}\\n```"
    return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: response_text})


def _handle_update_state_command(user_input: str, user_id: UserId, campaign_id: CampaignId) -> Optional[Response]:
    """
    Handle GOD_MODE_UPDATE_STATE command.

    Returns:
        Flask response or None if not UPDATE_STATE command
    """
    GOD_MODE_UPDATE_STATE_COMMAND = "GOD_MODE_UPDATE_STATE:"

    if not user_input.strip().startswith(GOD_MODE_UPDATE_STATE_COMMAND):
        return None

    json_payload = user_input.strip()[len(GOD_MODE_UPDATE_STATE_COMMAND) :]
    try:
        state_changes = json.loads(json_payload)
        if not isinstance(state_changes, dict):
            raise ValueError("Payload is not a JSON object.")

        # Fetch the current state as a dictionary
        current_game_state = firestore_service.get_campaign_game_state(
            user_id, campaign_id
        )
        if not current_game_state:
            return jsonify(
                {KEY_ERROR: "Game state not found for GOD_MODE_UPDATE_STATE"}
            ), 404

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

        firestore_service.update_campaign_game_state(
            user_id, campaign_id, final_game_state.to_dict()
        )

        log_message = format_state_changes(state_changes, for_html=False)
        return jsonify(
            {
                KEY_SUCCESS: True,
                KEY_RESPONSE: f"[System Message: The following state changes were applied via GOD MODE]\\n{log_message}",
            }
        )

    except json.JSONDecodeError:
        return jsonify(
            {KEY_ERROR: "Invalid JSON payload for GOD_MODE_UPDATE_STATE command."}
        ), 400
    except ValueError as e:
        return jsonify({KEY_ERROR: f"Error in GOD_MODE_UPDATE_STATE payload: {e}"}), 400
    except Exception as e:
        return jsonify(
            {
                KEY_ERROR: f"An unexpected error occurred during GOD_MODE_UPDATE_STATE: {e}"
            }
        ), 500


def _apply_state_changes_and_respond(
    proposed_changes: Optional[Dict[str, Any]],
    current_game_state: GameState,
    gemini_response_obj: Any,  # GeminiResponse type from gemini_service
    structured_response: Optional[Any],  # NarrativeResponse type from gemini_service
    mode: str,
    story_context: List[Dict[str, Any]],
    campaign_id: CampaignId,
    user_id: UserId,
) -> Response:
    """
    Apply state changes from AI response and prepare final response.

    Args:
        proposed_changes: Proposed state changes dict
        current_game_state: Current GameState object
        gemini_response_obj: Processed narrative text object
        structured_response: Parsed NarrativeResponse object or None
        mode: Game mode
        story_context: Story context list
        campaign_id: Campaign ID
        user_id: User ID

    Returns:
        Flask response with JSON structure

    Note: This function handles two types of debug content:
        1. Legacy debug tags embedded in narrative text - shown/hidden based on debug_mode
        2. Structured debug_info field - always included when present (frontend decides display)
    """
    # Check if debug mode is enabled
    debug_mode_enabled = (
        hasattr(current_game_state, "debug_mode") and current_game_state.debug_mode
    )

    # Get narrative text with debug content handled based on debug mode
    # GeminiResponse now handles debug content stripping internally
    if hasattr(gemini_response_obj, "get_narrative_text"):
        final_narrative = gemini_response_obj.get_narrative_text(
            debug_mode=debug_mode_enabled
        )
    else:
        # Fallback for string responses (shouldn't happen with current code)
        final_narrative = gemini_response_obj

    # Build response data structure
    response_data = {
        KEY_SUCCESS: True,
        KEY_RESPONSE: final_narrative,  # Keep for backward compatibility
        "narrative": final_narrative,  # Add narrative field per schema
        "debug_mode": debug_mode_enabled,
        "sequence_id": len(story_context) + 2,
    }

    # Always include structured response fields that consumers rely on
    if structured_response:
        # State updates are critical for game state progression
        if (
            hasattr(structured_response, "state_updates")
            and structured_response.state_updates
        ):
            response_data["state_updates"] = structured_response.state_updates

        # Entity tracking fields used by frontend
        response_data["entities_mentioned"] = getattr(
            structured_response, "entities_mentioned", []
        )
        response_data["location_confirmed"] = getattr(
            structured_response, "location_confirmed", "Unknown"
        )

        # Always include new always-visible fields
        response_data["session_header"] = getattr(
            structured_response, "session_header", ""
        )
        response_data["planning_block"] = getattr(
            structured_response, "planning_block", ""
        )
        response_data["dice_rolls"] = getattr(structured_response, "dice_rolls", [])
        response_data["resources"] = getattr(structured_response, "resources", "")

        # Include god_mode_response when in god mode
        if mode == constants.MODE_GOD and hasattr(
            structured_response, "god_mode_response"
        ):
            response_data[constants.FIELD_GOD_MODE_RESPONSE] = (
                structured_response.god_mode_response
            )

        # Always include structured debug_info (separate from legacy debug tags)
        # Frontend will use debug_mode flag to decide whether to display debug_info
        response_data["debug_info"] = getattr(structured_response, "debug_info", {})

    if proposed_changes:
        # Track last story mode sequence ID
        if mode == constants.MODE_CHARACTER:
            # The new sequence ID will be the length of the old context plus the two new entries
            last_story_id = len(story_context) + 2
            story_id_update = {
                "custom_campaign_state": {"last_story_mode_sequence_id": last_story_id}
            }
            # Merge this update with the changes from the LLM
            proposed_changes = update_state_with_changes(
                story_id_update, proposed_changes
            )

        # Enhanced logging for normal gameplay
        logging_util.info(
            f"AI proposed changes for campaign {campaign_id}:\\n{_truncate_log_json(proposed_changes)}"
        )

        log_message = format_state_changes(proposed_changes, for_html=False)
        logging_util.info(
            f"Applying formatted state changes for campaign {campaign_id}:\\n{log_message}"
        )

        # Update state with changes
        updated_state_dict = update_state_with_changes(
            current_game_state.to_dict(), proposed_changes
        )
        updated_state_dict = apply_automatic_combat_cleanup(
            updated_state_dict, proposed_changes
        )

        logging_util.info(
            f"New complete game state for campaign {campaign_id}:\\n{truncate_game_state_for_logging(updated_state_dict)}"
        )

        firestore_service.update_campaign_game_state(
            user_id, campaign_id, updated_state_dict
        )

    # Calculate user_scene_number by counting AI responses in story_context
    # Plus 1 for the new AI response we're about to add
    user_scene_number = (
        sum(1 for entry in story_context if entry.get("actor") == "gemini") + 1
    )

    # Add user_scene_number to response_data
    response_data["user_scene_number"] = user_scene_number

    return jsonify(response_data)


def _handle_debug_mode_command(
    user_input: str, mode: str, current_game_state: GameState, user_id: UserId, campaign_id: CampaignId
) -> Optional[Response]:
    """
    Handle debug mode command parsing and state updates.

    Args:
        user_input: The user's input text
        mode: Current interaction mode ('god' or 'character')
        current_game_state: The current GameState object
        user_id: The user's ID
        campaign_id: The campaign's ID

    Returns:
        Flask response if this is a debug command, None otherwise
    """
    debug_command, should_update = DebugModeParser.parse_debug_command(user_input, mode)
    if not debug_command:
        return None

    # Update state based on command
    current_debug_state = getattr(current_game_state, "debug_mode", False)

    if debug_command == "enable":
        new_debug_state = True
    else:  # disable
        new_debug_state = False

    # Only update if state actually changes
    if current_debug_state != new_debug_state:
        current_game_state.debug_mode = new_debug_state
        firestore_service.update_campaign_game_state(
            user_id, campaign_id, current_game_state.to_dict()
        )
        logging_util.info(
            f"Debug mode {'enabled' if new_debug_state else 'disabled'} for campaign {campaign_id}"
        )

    # Get appropriate message
    message = DebugModeParser.get_state_update_message(debug_command, new_debug_state)

    # Log the user input for history
    firestore_service.add_story_entry(
        user_id, campaign_id, constants.ACTOR_USER, user_input, mode
    )

    return jsonify(
        {KEY_SUCCESS: True, KEY_RESPONSE: message, "debug_mode": new_debug_state}
    )


def truncate_game_state_for_logging(game_state_dict: Dict[str, Any], max_lines: int = 20) -> str:
    """
    Truncates a game state dictionary for logging to improve readability.
    Only shows the first max_lines lines of the JSON representation.
    """
    json_str = json.dumps(game_state_dict, indent=2, default=json_default_serializer)
    lines = json_str.split("\n")

    if len(lines) <= max_lines:
        return json_str

    truncated_lines = lines[:max_lines]
    truncated_lines.append(f"... (truncated, showing {max_lines}/{len(lines)} lines)")
    return "\n".join(truncated_lines)


def apply_automatic_combat_cleanup(
    updated_state_dict: Dict[str, Any], proposed_changes: Dict[str, Any]
) -> Dict[str, Any]:
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


def _cleanup_legacy_state(state_dict: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, int]:
    """
    Removes legacy data structures from a game state dictionary.
    Specifically, it removes top-level keys with '.' in them and the old 'world_time' key.
    Returns the cleaned dictionary, a boolean indicating if changes were made, and the number of keys removed.
    """
    keys_to_delete = [key for key in state_dict if "." in key]
    if "world_time" in state_dict:
        keys_to_delete.append("world_time")

    num_deleted = len(keys_to_delete)

    if not keys_to_delete:
        return state_dict, False, 0

    logging_util.info(
        f"Performing one-time cleanup. Deleting {num_deleted} legacy keys: {keys_to_delete}"
    )
    cleaned_state = state_dict.copy()
    for key in keys_to_delete:
        if key in cleaned_state:
            del cleaned_state[key]

    return cleaned_state, True, num_deleted


def format_state_changes(changes: Dict[str, Any], for_html: bool = False) -> str:
    """Formats a dictionary of state changes into a readable string, counting the number of leaf-node changes."""
    if not changes:
        return "No state changes."

    log_lines: List[str] = []

    def recurse_items(d: Dict[str, Any], prefix: str = "") -> None:
        for key, value in d.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                recurse_items(value, prefix=path)
            else:
                log_lines.append(f"{path}: {json.dumps(value)}")

    recurse_items(changes)

    count = len(log_lines)
    if count == 0:
        return "No effective state changes were made."

    header = f"Game state updated ({count} {'entry' if count == 1 else 'entries'}):"

    if for_html:
        # Create an HTML list for the chat response
        items_html = "".join([f"<li><code>{line}</code></li>" for line in log_lines])
        return f"{header}<ul>{items_html}</ul>"
    # Create a plain text list for server logs
    items_text = "\\n".join([f"  - {line}" for line in log_lines])
    return f"{header}\\n{items_text}"


def parse_set_command(payload_str: str) -> Dict[str, Any]:
    """
    Parses a multi-line string of `key.path = value` into a nested
    dictionary of proposed changes. Handles multiple .append operations correctly.
    """
    proposed_changes: Dict[str, Any] = {}
    append_ops: Dict[str, List[Any]] = collections.defaultdict(list)

    for line in payload_str.strip().splitlines():
        line = line.strip()
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

        if key_path.endswith(".append"):
            base_key = key_path[: -len(".append")]
            append_ops[base_key].append(value)
            continue

        keys = key_path.split(".")
        d = proposed_changes
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value

    for base_key, values_to_append in append_ops.items():
        keys = base_key.split(".")
        d = proposed_changes
        for key in keys:
            d = d.setdefault(key, {})
        d["append"] = values_to_append

    return proposed_changes


def _build_campaign_prompt(character: Optional[str], setting: Optional[str], description: Optional[str], old_prompt: Optional[str]) -> str:
    """
    Build campaign prompt from character, setting, and description parameters.

    This function handles all combinations of character, setting, and description inputs:
    - Provided inputs are used as-is
    - Empty/None inputs are replaced with randomly generated content
    - Backward compatibility with old_prompt format is maintained

    Args:
        character: Character description or None/empty
        setting: Setting description or None/empty
        description: Campaign description or None/empty
        old_prompt: Legacy prompt format for backward compatibility

    Returns:
        Constructed campaign prompt with proper character/setting/description format
    """

    # Normalize inputs: convert None to empty string and strip whitespace
    character = (character or "").strip()
    setting = (setting or "").strip()
    description = (description or "").strip()
    old_prompt = (old_prompt or "").strip()

    # Build new format prompt - use provided fields or generate random content
    prompt_parts = []

    # Character: use provided or generate random
    if character:
        prompt_parts.append(f"Character: {character}")
    else:
        prompt_parts.append(f"Character: {random.choice(RANDOM_CHARACTERS)}")

    # Setting: use provided or generate random
    if setting:
        prompt_parts.append(f"Setting: {setting}")
    else:
        prompt_parts.append(f"Setting: {random.choice(RANDOM_SETTINGS)}")

    # Description: only include if provided
    if description:
        prompt_parts.append(f"Campaign Description: {description}")

    # Backward compatibility: use old_prompt only if no new format fields provided
    if not character and not setting and not description and old_prompt:
        return old_prompt

    return "\n".join(prompt_parts)


def setup_file_logging() -> None:
    """
    Configure file logging for current git branch.

    Creates branch-specific log files in /tmp/worldarchitectai_logs/{branch}.log
    and configures logging_util to write to both console and file.
    """
    # Create log directory
    os.makedirs(LOG_DIRECTORY, exist_ok=True)

    # Get current branch name
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=os.path.dirname(__file__),
            text=True,
        ).strip()
    except:
        branch = "unknown"

    # Configure file logging using standard logging module
    # Convert forward slashes to underscores for valid filename
    safe_branch = branch.replace("/", "_")
    log_file = os.path.join(LOG_DIRECTORY, f"{safe_branch}.log")

    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set up formatting
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set level
    root_logger.setLevel(logging.INFO)

    logging_util.info(f"File logging configured: {log_file}")


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    This function initializes the Flask application with all necessary configuration,
    middleware, and route handlers. It sets up CORS, authentication, database connections,
    and all API endpoints.

    Key Configuration:
    - Static file serving from 'static' folder
    - CORS enabled for all /api/* routes
    - Testing mode configuration from environment
    - Firebase Admin SDK initialization
    - Authentication decorator for protected routes
    - File logging to /tmp/worldarchitectai_logs/{branch}.log

    Routes Configured:
    - GET /api/campaigns - List user's campaigns
    - GET /api/campaigns/<id> - Get specific campaign
    - POST /api/campaigns - Create new campaign
    - PATCH /api/campaigns/<id> - Update campaign
    - POST /api/campaigns/<id>/interaction - Handle user interactions
    - GET /api/campaigns/<id>/export - Export campaign documents
    - /* - Frontend SPA fallback

    Returns:
        Configured Flask application instance
    """
    # Set up file logging before creating app
    setup_file_logging()

    app = Flask(__name__, static_folder=None)  # Disable default static serving
    CORS(app, resources=CORS_RESOURCES)
    
    # Cache busting route for testing - only activates with special header
    @app.route('/static/<path:filename>')
    def static_files_with_cache_busting(filename):
        """Serve static files with optional cache-busting for testing"""
        static_folder = os.path.join(os.path.dirname(__file__), 'static')
        response = send_from_directory(static_folder, filename)
        
        # Only disable cache if X-No-Cache header is present (for testing)
        if request.headers.get('X-No-Cache') and filename.endswith(('.js', '.css')):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response

    # Set TESTING config from environment
    if os.environ.get("TESTING", "").lower() in ["true", "1", "yes"]:
        app.config["TESTING"] = True

    # Store mock configuration in app config
    app.config["USE_MOCK_GEMINI"] = use_mock_gemini
    app.config["USE_MOCK_FIREBASE"] = use_mock_firebase
    app.config["USE_MOCKS"] = use_mock_gemini and use_mock_firebase  # Both mocked

    # Log mock configuration
    if use_mock_gemini or use_mock_firebase:
        mock_status = []
        if use_mock_gemini:
            mock_status.append("Gemini=MOCK")
        else:
            mock_status.append("Gemini=REAL")
        if use_mock_firebase:
            mock_status.append("Firebase=MOCK")
        else:
            mock_status.append("Firebase=REAL")
        logging_util.info(f"Service configuration: {', '.join(mock_status)}")

    # Initialize Firebase only if not using mock
    if not use_mock_firebase:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()

    def check_token(f: Callable[..., Response]) -> Callable[..., Response]:
        @wraps(f)
        def wrap(*args: Any, **kwargs: Any) -> Response:
            # Check for auth skip mode (for testing with real services)
            auth_skip_enabled = (
                app.config.get("TESTING") or os.getenv("AUTH_SKIP_MODE") == "true"
            )
            if (
                auth_skip_enabled
                and request.headers.get(HEADER_TEST_BYPASS, "").lower() == "true"
            ):
                kwargs["user_id"] = request.headers.get(
                    HEADER_TEST_USER_ID, DEFAULT_TEST_USER
                )
                return f(*args, **kwargs)
            if not request.headers.get(HEADER_AUTH):
                return jsonify({KEY_MESSAGE: "No token provided"}), 401
            try:
                id_token = request.headers[HEADER_AUTH].split(" ").pop()
                decoded_token = auth.verify_id_token(id_token)
                kwargs["user_id"] = decoded_token["uid"]
            except Exception as e:
                return jsonify(
                    {
                        KEY_SUCCESS: False,
                        KEY_ERROR: f"Auth failed: {e}",
                        KEY_TRACEBACK: traceback.format_exc(),
                    }
                ), 401
            return f(*args, **kwargs)

        return wrap

    # --- API Routes ---
    @app.route("/api/campaigns", methods=["GET"])
    @check_token
    def get_campaigns(user_id: UserId) -> Union[Response, Tuple[Response, int]]:
        # --- RESTORED TRY-EXCEPT BLOCK ---
        try:
            return jsonify(firestore_service.get_campaigns_for_user(user_id))
        except Exception as e:
            return jsonify(
                {
                    KEY_SUCCESS: False,
                    KEY_ERROR: str(e),
                    KEY_TRACEBACK: traceback.format_exc(),
                }
            ), 500
        # --- END RESTORED BLOCK ---

    @app.route("/api/campaigns/<campaign_id>", methods=["GET"])
    @check_token
    def get_campaign(user_id: UserId, campaign_id: CampaignId) -> Union[Response, Tuple[Response, int]]:
        # --- RESTORED TRY-EXCEPT BLOCK ---
        try:
            logging_util.info(
                f"🎮 LOADING GAME PAGE: user={user_id}, campaign={campaign_id}"
            )
            campaign, story = firestore_service.get_campaign_by_id(user_id, campaign_id)
            if not campaign:
                return jsonify({KEY_ERROR: "Campaign not found"}), 404

            # Include game state for debug mode status
            game_state = firestore_service.get_campaign_game_state(user_id, campaign_id)
            game_state_dict = game_state.to_dict() if game_state else {}

            # Apply hybrid debug processing to story entries for backward compatibility
            debug_mode = game_state_dict.get("debug_mode", False)
            processed_story = process_story_for_display(story, debug_mode)

            # Debug logging for structured fields
            logging_util.info(
                f"Campaign {campaign_id} story entries: {len(processed_story)}"
            )
            for i, entry in enumerate(processed_story[:3]):  # Log first 3 entries
                if entry.get("actor") == constants.ACTOR_GEMINI:
                    fields = [
                        k
                        for k in entry.keys()
                        if k not in ["text", "actor", "mode", "timestamp", "part"]
                    ]
                    logging_util.info(f"Entry {i} structured fields: {fields}")
                    if "god_mode_response" in entry:
                        logging_util.info(
                            f"  god_mode_response: {entry['god_mode_response'][:50]}..."
                        )
                    if "resources" in entry:
                        logging_util.info(f"  resources: {entry['resources']}")
                    if "dice_rolls" in entry:
                        logging_util.info(f"  dice_rolls: {entry['dice_rolls']}")

            return jsonify(
                {
                    KEY_CAMPAIGN: campaign,
                    KEY_STORY: processed_story,
                    "game_state": game_state_dict,
                }
            )
        except Exception as e:
            return jsonify(
                {
                    KEY_SUCCESS: False,
                    KEY_ERROR: str(e),
                    KEY_TRACEBACK: traceback.format_exc(),
                }
            ), 500
        # --- END RESTORED BLOCK ---

    @app.route("/api/campaigns", methods=["POST"])
    @check_token
    def create_campaign_route(user_id: UserId) -> Union[Response, Tuple[Response, int]]:
        data = request.get_json()

        # Handle both new (character/setting/description) and old (prompt) formats
        character = data.get("character", "")
        setting = data.get("setting", "")
        description = data.get("description", "")
        old_prompt = data.get(KEY_PROMPT, "")
        title = data.get(constants.KEY_TITLE)
        selected_prompts = data.get(KEY_SELECTED_PROMPTS, [])
        custom_options = data.get("custom_options", [])

        # Construct prompt from provided parameters
        try:
            prompt = _build_campaign_prompt(character, setting, description, old_prompt)
        except ValueError as e:
            return jsonify({KEY_ERROR: str(e)}), 400

        # Validate required fields
        if not title:
            return jsonify({KEY_ERROR: "Title is required"}), 400

        # Debug logging
        app.logger.info("Received campaign creation request:")
        app.logger.info(f"  Character: {character}")
        app.logger.info(f"  Setting: {setting}")
        app.logger.info(f"  Description: {description}")
        app.logger.info(f"  Custom options: {custom_options}")
        app.logger.info(f"  Selected prompts: {selected_prompts}")

        # Always use D&D system (Destiny system removed)
        attribute_system = constants.ATTRIBUTE_SYSTEM_DND

        app.logger.info(f"Selected attribute_system: {attribute_system}")

        # Create initial game state with attribute system
        initial_game_state = GameState(
            custom_campaign_state={"attribute_system": attribute_system}
        ).to_dict()

        generate_companions = "companions" in custom_options
        use_default_world = "defaultWorld" in custom_options

        try:
            opening_story_response = gemini_service.get_initial_story(
                prompt,
                selected_prompts=selected_prompts,
                generate_companions=generate_companions,
                use_default_world=use_default_world,
            )

            # Extract structured fields from opening story response
            opening_story_structured_fields = (
                structured_fields_utils.extract_structured_fields(
                    opening_story_response
                )
            )

            campaign_id = firestore_service.create_campaign(
                user_id,
                title,
                prompt,
                opening_story_response.narrative_text,
                initial_game_state,
                selected_prompts,
                use_default_world,
                opening_story_structured_fields,
            )

            return jsonify({KEY_SUCCESS: True, KEY_CAMPAIGN_ID: campaign_id}), 201
        except Exception as e:
            app.logger.error(f"Failed to create campaign: {e}")
            return jsonify({KEY_ERROR: f"Failed to create campaign: {str(e)}"}), 500

    @app.route("/api/campaigns/<campaign_id>", methods=["PATCH"])
    @check_token
    def update_campaign(user_id: UserId, campaign_id: CampaignId) -> Union[Response, Tuple[Response, int]]:
        data = request.get_json()
        new_title = data.get(constants.KEY_TITLE)
        if not new_title:
            return jsonify({KEY_ERROR: "New title is required"}), 400

        try:
            firestore_service.update_campaign_title(user_id, campaign_id, new_title)
            return jsonify(
                {KEY_SUCCESS: True, KEY_MESSAGE: "Campaign title updated successfully."}
            )
        except Exception as e:
            traceback.print_exc()
            return jsonify(
                {KEY_ERROR: "Failed to update campaign", KEY_DETAILS: str(e)}
            ), 500

    @app.route("/api/campaigns/<campaign_id>/interaction", methods=["POST"])
    @check_token
    def handle_interaction(user_id: UserId, campaign_id: CampaignId) -> Union[Response, Tuple[Response, int]]:
        try:
            data = request.get_json()
            user_input, mode = (
                data.get(KEY_USER_INPUT),
                data.get(constants.KEY_MODE, constants.MODE_CHARACTER),
            )

            # Validate user_input is provided
            if user_input is None:
                return jsonify({KEY_ERROR: "User input is required"}), 400

            # --- Special command handling ---
            GOD_MODE_SET_COMMAND = "GOD_MODE_SET:"
            GOD_ASK_STATE_COMMAND = "GOD_ASK_STATE"
            GOD_MODE_UPDATE_STATE_COMMAND = "GOD_MODE_UPDATE_STATE:"

            user_input_stripped = user_input.strip()

            # --- Game State Loading and Legacy Cleanup ---
            current_game_state, was_cleaned, num_cleaned = _prepare_game_state(
                user_id, campaign_id
            )
            game_state_dict = current_game_state.to_dict()

            # --- Debug Mode Command Parsing (BEFORE other commands) ---
            debug_response = _handle_debug_mode_command(
                user_input, mode, current_game_state, user_id, campaign_id
            )
            if debug_response:
                return debug_response

            # --- Retroactive MBTI Assignment Logging ---
            game_state_dict = current_game_state.to_dict()
            pc_data = game_state_dict.get("player_character_data", {})
            if constants.KEY_MBTI not in pc_data:
                pc_name = pc_data.get("name", "Player Character")
                logging_util.info(
                    f"RETROACTIVE_ASSIGNMENT: Character '{pc_name}' is missing an MBTI type. The AI will be prompted to assign one."
                )

            npc_data = game_state_dict.get("npc_data", {})
            for npc_id, npc_info in npc_data.items():
                # Defensive programming: ensure npc_info is a dictionary
                if not isinstance(npc_info, dict):
                    logging_util.warning(
                        f"NPC data for '{npc_id}' is not a dictionary: {type(npc_info)}. Skipping MBTI check."
                    )
                    continue

                if constants.KEY_MBTI not in npc_info:
                    npc_name = npc_info.get("name", npc_id)
                    logging_util.info(
                        f"RETROACTIVE_ASSIGNMENT: NPC '{npc_name}' is missing an MBTI type. The AI will be prompted to assign one."
                    )
            # --- END Retroactive MBTI ---

            # Handle SET command
            set_response = _handle_set_command(
                user_input, current_game_state, user_id, campaign_id
            )
            if set_response:
                return set_response

            # Handle ASK_STATE command
            ask_state_response = _handle_ask_state_command(
                user_input, current_game_state, user_id, campaign_id
            )
            if ask_state_response:
                return ask_state_response

            # Handle UPDATE_STATE command
            update_state_response = _handle_update_state_command(
                user_input, user_id, campaign_id
            )
            if update_state_response:
                return update_state_response

            # Fetch campaign metadata and story context
            campaign, story_context = firestore_service.get_campaign_by_id(
                user_id, campaign_id
            )
            if not campaign:
                return jsonify({KEY_ERROR: "Campaign not found"}), 404

            # 2. Add user's action to the story log
            logging_util.info(
                f"📝 ADDING USER STORY ENTRY: user={user_id}, campaign={campaign_id}, mode={mode}, input_length={len(user_input)}"
            )
            firestore_service.add_story_entry(
                user_id, campaign_id, constants.ACTOR_USER, user_input, mode
            )

            # 3. Process: Get AI response, passing in the current state
            selected_prompts = campaign.get(KEY_SELECTED_PROMPTS, [])
            use_default_world = campaign.get("use_default_world", False)
            gemini_response_obj = gemini_service.continue_story(
                user_input,
                mode,
                story_context,
                current_game_state,
                selected_prompts,
                use_default_world,
            )

            # 3a. Verify debug content generation for monitoring
            debug_tags_found = gemini_response_obj.debug_tags_present

            if not any(debug_tags_found.values()):
                logging_util.warning(
                    f"AI response missing debug content for campaign {campaign_id}"
                )
                logging_util.warning(f"Debug tags found: {debug_tags_found}")
                log_with_tokens(
                    "Response length", gemini_response_obj.narrative_text, logging_util
                )
            else:
                # Log which debug content types were included
                logging_util.info(
                    f"Debug content generated for campaign {campaign_id}: {debug_tags_found}"
                )

            # 4. Write: Add AI response to story log and update state
            # Extract structured fields from AI response for storage
            structured_fields = structured_fields_utils.extract_structured_fields(
                gemini_response_obj
            )
            logging_util.info(
                f"📝 ADDING AI STORY ENTRY: user={user_id}, campaign={campaign_id}, "
                f"narrative_length={len(gemini_response_obj.narrative_text)}, "
                f"structured_fields_count={len(structured_fields) if structured_fields else 0}"
            )
            firestore_service.add_story_entry(
                user_id,
                campaign_id,
                constants.ACTOR_GEMINI,
                gemini_response_obj.narrative_text,
                structured_fields=structured_fields,
            )

            # 5. Parse and apply state changes from AI response
            # JSON mode is the ONLY mode - state updates come exclusively from the structured response object.
            # No fallback parsing is performed.
            proposed_changes = gemini_response_obj.state_updates

            # --- NEW: Post-response checkpoint validation ---
            if proposed_changes:
                # Apply changes to a temporary state copy for validation
                temp_state_dict = current_game_state.to_dict()
                updated_temp_state = update_state_with_changes(
                    temp_state_dict, proposed_changes
                )
                temp_game_state = GameState.from_dict(updated_temp_state)

                # Validate the new response against the updated state
                post_update_discrepancies = (
                    temp_game_state.validate_checkpoint_consistency(
                        gemini_response_obj.narrative_text
                    )
                )

                if post_update_discrepancies:
                    logging_util.warning(
                        f"POST_UPDATE_VALIDATION: AI response created {len(post_update_discrepancies)} new discrepancies:"
                    )
                    for i, discrepancy in enumerate(post_update_discrepancies, 1):
                        logging_util.warning(f"  {i}. {discrepancy}")

            # Apply state changes and return response
            logging_util.info(
                f"✅ STORY INTERACTION COMPLETE: user={user_id}, campaign={campaign_id}, "
                f"mode={mode}, response_ready=True"
            )
            return _apply_state_changes_and_respond(
                proposed_changes,
                current_game_state,
                gemini_response_obj,
                gemini_response_obj.structured_response,
                mode,
                story_context,
                campaign_id,
                user_id,
            )

        except Exception as e:
            # Critical security fix: Never expose raw exceptions to frontend
            logging_util.error(
                f"Critical error in handle_interaction for campaign {campaign_id}: {e}"
            )
            logging_util.error(
                f"User input: {user_input if 'user_input' in locals() else 'N/A'}"
            )
            logging_util.error(traceback.format_exc())

            # Return sanitized error response that cannot leak JSON or internal details
            return jsonify(
                {
                    KEY_SUCCESS: False,
                    KEY_ERROR: "An error occurred processing your request.",
                    KEY_RESPONSE: "I encountered an issue and cannot continue at this time. Please try again, or contact support if the problem persists.",
                }
            ), 500

    @app.route("/api/campaigns/<campaign_id>/export", methods=["GET"])
    @check_token
    def export_campaign(user_id: UserId, campaign_id: CampaignId) -> Union[Response, Tuple[Response, int]]:
        try:
            export_format = request.args.get("format", "txt").lower()

            campaign_data, story_log = firestore_service.get_campaign_by_id(
                user_id, campaign_id
            )
            if not campaign_data:
                return jsonify({KEY_ERROR: "Campaign not found"}), 404

            campaign_title = campaign_data.get("title", "Untitled Campaign")
            desired_download_name = f"{campaign_title}.{export_format}"

            temp_dir = os.path.join("/tmp", "campaign_exports")
            os.makedirs(temp_dir, exist_ok=True)
            safe_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.{export_format}")

            story_parts = []
            for entry in story_log:
                actor = entry.get(constants.KEY_ACTOR, document_generator.UNKNOWN_ACTOR)
                text = entry.get(constants.KEY_TEXT, "")
                mode = entry.get(constants.KEY_MODE)
                if actor == constants.ACTOR_GEMINI:
                    label = document_generator.LABEL_GEMINI
                else:
                    label = (
                        document_generator.LABEL_GOD
                        if mode == constants.MODE_GOD
                        else document_generator.LABEL_USER
                    )
                story_parts.append(f"{label}:\\n{text}")
            story_text = "\\n\\n".join(story_parts)

            if export_format == "pdf":
                document_generator.generate_pdf(
                    story_text, safe_file_path, campaign_title
                )
            elif export_format == "docx":
                document_generator.generate_docx(
                    story_text, safe_file_path, campaign_title
                )
            elif export_format == "txt":
                document_generator.generate_txt(
                    story_text, safe_file_path, campaign_title
                )
            else:
                return jsonify({KEY_ERROR: f"Unsupported format: {export_format}"}), 400

            if os.path.exists(safe_file_path):
                logging_util.info(
                    f"Exporting file '{safe_file_path}' with download_name='{desired_download_name}'"
                )

                # Use the standard send_file call, which should now work correctly
                # with the fixed JavaScript client.
                response = send_file(
                    safe_file_path,
                    download_name=desired_download_name,
                    as_attachment=True,
                )

                @response.call_on_close
                def cleanup() -> None:
                    try:
                        os.remove(safe_file_path)
                        logging_util.info(
                            f"Cleaned up temporary file: {safe_file_path}"
                        )
                    except Exception as e:
                        logging_util.error(
                            f"Error cleaning up file {safe_file_path}: {e}"
                        )

                return response
            return jsonify({KEY_ERROR: "Failed to create export file."}), 500

        except Exception as e:
            logging_util.error(f"Export failed: {e}")
            traceback.print_exc()
            return jsonify(
                {
                    KEY_ERROR: "An unexpected error occurred during export.",
                    KEY_DETAILS: str(e),
                }
            ), 500

    # --- Frontend Serving ---
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str) -> Response:
        """Serve the frontend files. This is the fallback for any non-API routes."""
        static_folder = os.path.join(os.path.dirname(__file__), 'static')
        if path and os.path.exists(os.path.join(static_folder, path)):
            return send_from_directory(static_folder, path)
        return send_from_directory(static_folder, "index.html")

    # Fallback route for old cached frontend code calling /handle_interaction
    @app.route("/handle_interaction", methods=["POST"])
    def handle_interaction_fallback():
        """Fallback for cached frontend code calling old endpoint"""
        return jsonify({
            "error": "This endpoint has been moved. Please refresh your browser (Ctrl+Shift+R) to get the latest version.",
            "redirect_message": "Hard refresh required to clear browser cache",
            "status": "cache_issue"
        }), 410  # 410 Gone - indicates this endpoint no longer exists

    return app


def run_god_command(campaign_id: CampaignId, user_id: UserId, action: str, command_string: Optional[str] = None) -> None:
    """Runs a GOD_MODE command directly against Firestore."""
    # We need to initialize the app to get the context for Firestore
    if not firebase_admin._apps:
        firebase_admin.initialize_app()

    if action == "ask":
        logging_util.info(f"Fetching current state for campaign: {campaign_id}")
        current_game_state = firestore_service.get_campaign_game_state(
            user_id, campaign_id
        )
        if not current_game_state:
            logging_util.info("No game state found for this campaign.")
            return

        # Pretty-print the JSON to the console
        state_json = json.dumps(
            current_game_state.to_dict(), indent=2, default=json_default_serializer
        )
        logging_util.info(f"Current game state:\n{state_json}")
        return

    if action == "set":
        if not command_string:
            logging_util.error("The 'set' action requires a --command_string.")
            return

        if not command_string.strip().startswith("GOD_MODE_SET:"):
            logging_util.error("Command string must start with GOD_MODE_SET:")
            return

        payload_str = command_string.strip()[len("GOD_MODE_SET:") :].strip()
        proposed_changes = parse_set_command(payload_str)

        if not proposed_changes:
            logging_util.warning("Command contained no valid changes.")
            return

        logging_util.info(f"Applying changes to campaign: {campaign_id}")

        current_game_state_doc = firestore_service.get_campaign_game_state(
            user_id, campaign_id
        )
        current_state_dict = (
            current_game_state_doc.to_dict()
            if current_game_state_doc
            else GameState().to_dict()
        )

        updated_state = update_state_with_changes(current_state_dict, proposed_changes)
        updated_state = apply_automatic_combat_cleanup(updated_state, proposed_changes)
        firestore_service.update_campaign_game_state(
            user_id, campaign_id, updated_state
        )

        log_message = format_state_changes(proposed_changes, for_html=False)
        logging_util.info(f"Update successful:\n{log_message}")

    else:
        logging_util.error(
            f"Unknown god-command action '{action}'. Use 'set' or 'ask'."
        )


def run_test_command(command: str) -> None:
    """
    Run a test command.

    Args:
        command: The test command to run ('testui', 'testuif', 'testhttp', 'testhttpf')
    """
    if command == "testui":
        # Run browser tests with mock APIs
        test_runner = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "testing_ui",
            "run_all_browser_tests.py",
        )
        if os.path.exists(test_runner):
            logging_util.info(
                "🌐 Running WorldArchitect.AI Browser Tests (Mock APIs)..."
            )
            logging_util.info("   Using real browser automation with mocked backend")
            result = subprocess.run([sys.executable, test_runner], check=False)
            sys.exit(result.returncode)
        else:
            logging_util.error(f"Test runner not found: {test_runner}")
            sys.exit(1)

    elif command == "testuif":
        # Run browser tests with REAL APIs
        test_runner = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "testing_ui",
            "run_all_browser_tests.py",
        )
        if os.path.exists(test_runner):
            logging_util.info(
                "🌐 Running WorldArchitect.AI Browser Tests (REAL APIs)..."
            )
            logging_util.warning(
                "⚠️  WARNING: These tests use REAL APIs and cost money!"
            )
            env = os.environ.copy()
            env["REAL_APIS"] = "true"
            result = subprocess.run([sys.executable, test_runner], check=False, env=env)
            sys.exit(result.returncode)
        else:
            logging_util.error(f"Test runner not found: {test_runner}")
            sys.exit(1)

    elif command == "testhttp":
        # Run HTTP tests with mock APIs
        test_runner = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "testing_http",
            "run_all_http_tests.py",
        )
        if os.path.exists(test_runner):
            logging_util.info("🔗 Running WorldArchitect.AI HTTP Tests (Mock APIs)...")
            logging_util.info("   Using direct HTTP requests with mocked backend")
            result = subprocess.run([sys.executable, test_runner], check=False)
            sys.exit(result.returncode)
        else:
            logging_util.error(f"Test runner not found: {test_runner}")
            sys.exit(1)

    elif command == "testhttpf":
        # Run HTTP tests with REAL APIs
        test_runner = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "testing_http",
            "testing_full",
            "run_all_full_tests.py",
        )
        if os.path.exists(test_runner):
            logging_util.info("🔗 Running WorldArchitect.AI HTTP Tests (REAL APIs)...")
            logging_util.warning(
                "⚠️  WARNING: These tests use REAL APIs and cost money!"
            )
            result = subprocess.run([sys.executable, test_runner], check=False)
            sys.exit(result.returncode)
        else:
            logging_util.error(f"Full API test runner not found: {test_runner}")
            sys.exit(1)

    else:
        logging_util.error(f"Unknown test command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="World Architect AI Server & Tools")
    parser.add_argument(
        "command",
        nargs="?",
        default="serve",
        help="Command to run ('serve', 'god-command', 'testui', 'testuif', 'testhttp', or 'testhttpf')",
    )

    # Manual parsing for god-command to handle multi-line strings
    if len(sys.argv) > 1 and sys.argv[1] == "god-command":
        parser.add_argument(
            "action",
            choices=["set", "ask"],
            help="The action to perform ('set' or 'ask')",
        )
        parser.add_argument(
            "--campaign_id", required=True, help="Campaign ID for the god-command"
        )
        parser.add_argument(
            "--user_id", required=True, help="User ID who owns the campaign"
        )
        parser.add_argument(
            "--command_string",
            help="The full GOD_MODE_SET command string (required for 'set')",
        )

        args, unknown = parser.parse_known_args(sys.argv[2:])

        if args.action == "set" and not args.command_string:
            # Manually reconstruct the command string if it was not passed with the flag
            try:
                command_string_index = sys.argv.index("--command_string")
                args.command_string = " ".join(sys.argv[command_string_index + 1 :])
            except (ValueError, IndexError):
                parser.error("--command_string is required for the 'set' action.")

        run_god_command(
            args.campaign_id, args.user_id, args.action, args.command_string
        )

    elif len(sys.argv) > 1 and sys.argv[1] == "testui":
        run_test_command("testui")

    elif len(sys.argv) > 1 and sys.argv[1] == "testuif":
        run_test_command("testuif")

    elif len(sys.argv) > 1 and sys.argv[1] == "testhttp":
        run_test_command("testhttp")

    elif len(sys.argv) > 1 and sys.argv[1] == "testhttpf":
        run_test_command("testhttpf")

    else:
        # Standard server execution
        args = parser.parse_args()
        if args.command == "serve":
            app = create_app()
            port = int(os.environ.get("PORT", 8081))
            logging_util.info(f"Development server running: http://localhost:{port}")
            app.run(host="0.0.0.0", port=port, debug=True)
        elif args.command == "testui":
            run_test_command("testui")
        elif args.command == "testuif":
            run_test_command("testuif")
        elif args.command == "testhttp":
            run_test_command("testhttp")
        elif args.command == "testhttpf":
            run_test_command("testhttpf")
        else:
            parser.error(f"Unknown command: {args.command}")
