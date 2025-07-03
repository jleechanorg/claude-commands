# Diagnostic edit to test file system access.
import os
import io
import uuid
import re
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth
import traceback
import document_generator
import logging
from game_state import GameState, MigrationStatus
from debug_mode_parser import DebugModeParser
import constants
import json
import collections
from firestore_service import update_state_with_changes, json_default_serializer, _truncate_log_json

# --- Service Imports ---
import gemini_service
import firestore_service

# --- CONSTANTS ---
# API Configuration
CORS_RESOURCES = {r"/api/*": {"origins": "*"}}

# Request Headers
HEADER_AUTH = 'Authorization'
HEADER_TEST_BYPASS = 'X-Test-Bypass-Auth'
HEADER_TEST_USER_ID = 'X-Test-User-ID'

# Request/Response Data Keys (specific to main.py)
KEY_PROMPT = 'prompt'
KEY_SELECTED_PROMPTS = 'selected_prompts'
KEY_USER_INPUT = 'input'
KEY_CAMPAIGN_ID = 'campaign_id'
KEY_SUCCESS = 'success'
KEY_ERROR = 'error'
KEY_TRACEBACK = 'traceback'
KEY_MESSAGE = 'message'
KEY_CAMPAIGN = 'campaign'
KEY_STORY = 'story'
KEY_DETAILS = 'details'
KEY_RESPONSE = 'response'

# Roles & Modes
DEFAULT_TEST_USER = 'test-user'

# --- END CONSTANTS ---


class StateHelper:
    """
    Helper class for state-related operations.
    Consolidates debug content stripping and state cleanup functions.
    """
    
    @staticmethod
    def strip_debug_content(text):
        """
        Strip debug content from AI response text while preserving the rest.
        Removes content between debug tags: [DEBUG_START/END], [DEBUG_ROLL_START/END], [DEBUG_STATE_START/END]
        Also removes [STATE_UPDATES_PROPOSED] blocks which are internal state management.
        
        Args:
            text: The raw text containing debug content
            
        Returns:
            str: Text with debug content removed
        """
        return strip_debug_content(text)
    
    @staticmethod
    def strip_state_updates_only(text):
        """
        Strip only [STATE_UPDATES_PROPOSED] blocks while preserving other debug content.
        Used when user has debug mode enabled but we still want to hide internal state updates.
        
        Args:
            text: The raw text containing state updates
            
        Returns:
            str: Text with state updates removed
        """
        return strip_state_updates_only(text)
    
    @staticmethod
    def strip_other_debug_content(text):
        """
        Strip all debug content EXCEPT [STATE_UPDATES_PROPOSED] blocks.
        Used for extracting state updates while removing other debug information.
        
        Args:
            text: The raw text containing debug content
            
        Returns:
            str: Text with only state updates remaining
        """
        return strip_other_debug_content(text)
    
    @staticmethod
    def apply_automatic_combat_cleanup(state_dict, proposed_changes):
        """
        Automatically clean up combat state when combat ends.
        
        Args:
            state_dict: Current game state dictionary
            proposed_changes: Proposed state changes
            
        Returns:
            dict: Updated state dictionary with combat cleanup applied
        """
        return apply_automatic_combat_cleanup(state_dict, proposed_changes)
    
    @staticmethod
    def cleanup_legacy_state(state_dict):
        """
        Clean up legacy state issues like __DELETE__ tokens and str() conversions.
        
        Args:
            state_dict: Game state dictionary to clean
            
        Returns:
            tuple: (cleaned_dict, was_cleaned, num_cleaned)
        """
        return _cleanup_legacy_state(state_dict)


def _prepare_game_state(user_id, campaign_id):
    """
    Load and prepare game state, including legacy cleanup.
    
    Args:
        user_id: User ID
        campaign_id: Campaign ID
        
    Returns:
        tuple: (current_game_state, was_cleaned, num_cleaned)
    """
    current_game_state_doc = firestore_service.get_campaign_game_state(user_id, campaign_id)
    
    # Ensure current_game_state is always a valid GameState object
    if current_game_state_doc:
        current_game_state = GameState.from_dict(current_game_state_doc.to_dict())
    else:
        current_game_state = GameState()
    
    # Perform cleanup on a dictionary copy
    cleaned_state_dict, was_cleaned, num_cleaned = StateHelper.cleanup_legacy_state(current_game_state.to_dict())
    if was_cleaned:
        # If cleaned, update the main object from the cleaned dictionary
        current_game_state = GameState.from_dict(cleaned_state_dict)
        firestore_service.update_campaign_game_state(user_id, campaign_id, current_game_state.to_dict())
        logging.info(f"Legacy state cleanup complete. Removed {num_cleaned} entries.")
    
    return current_game_state, was_cleaned, num_cleaned


def _handle_set_command(user_input, current_game_state, user_id, campaign_id):
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
    
    payload_str = user_input_stripped[len(GOD_MODE_SET_COMMAND):]
    logging.info(f"--- GOD_MODE_SET received for campaign {campaign_id} ---")
    logging.info(f"GOD_MODE_SET raw payload:\\n---\\n{payload_str}\\n---")
    
    proposed_changes = parse_set_command(payload_str)
    logging.info(f"GOD_MODE_SET parsed changes to be merged:\\n{_truncate_log_json(proposed_changes)}")
    
    if not proposed_changes:
        logging.warning(f"GOD_MODE_SET command resulted in no valid changes.")
        return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: "[System Message: The GOD_MODE_SET command was received, but contained no valid instructions or was empty.]"})
    
    current_state_dict_before_update = current_game_state.to_dict()
    logging.info(f"GOD_MODE_SET state BEFORE update:\\n{_truncate_log_json(current_state_dict_before_update)}")
    
    updated_state = update_state_with_changes(current_state_dict_before_update, proposed_changes)
    updated_state = StateHelper.apply_automatic_combat_cleanup(updated_state, proposed_changes)
    logging.info(f"GOD_MODE_SET state AFTER update:\\n{_truncate_log_json(updated_state)}")
    
    firestore_service.update_campaign_game_state(user_id, campaign_id, updated_state)
    
    # Log the formatted changes for both server and chat
    log_message_for_log = format_state_changes(proposed_changes, for_html=False)
    logging.info(f"GOD_MODE_SET changes applied for campaign {campaign_id}:\\n{log_message_for_log}")
    
    log_message_for_chat = format_state_changes(proposed_changes, for_html=True)
    
    logging.info(f"--- GOD_MODE_SET for campaign {campaign_id} complete ---")
    
    return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: f"[System Message]<br>{log_message_for_chat}"})


def _handle_ask_state_command(user_input, current_game_state, user_id, campaign_id):
    """
    Handle GOD_ASK_STATE command.
    
    Returns:
        Flask response or None if not ASK_STATE command
    """
    GOD_ASK_STATE_COMMAND = "GOD_ASK_STATE"
    
    if user_input.strip() != GOD_ASK_STATE_COMMAND:
        return None
    
    game_state_dict = current_game_state.to_dict()
    game_state_json = json.dumps(game_state_dict, indent=2, default=json_default_serializer)
    
    firestore_service.add_story_entry(user_id, campaign_id, constants.ACTOR_USER, user_input, constants.MODE_CHARACTER)
    
    response_text = f"```json\\n{game_state_json}\\n```"
    return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: response_text})


def _handle_update_state_command(user_input, user_id, campaign_id):
    """
    Handle GOD_MODE_UPDATE_STATE command.
    
    Returns:
        Flask response or None if not UPDATE_STATE command
    """
    GOD_MODE_UPDATE_STATE_COMMAND = "GOD_MODE_UPDATE_STATE:"
    
    if not user_input.strip().startswith(GOD_MODE_UPDATE_STATE_COMMAND):
        return None
    
    json_payload = user_input.strip()[len(GOD_MODE_UPDATE_STATE_COMMAND):]
    try:
        state_changes = json.loads(json_payload)
        if not isinstance(state_changes, dict):
            raise ValueError("Payload is not a JSON object.")
        
        # Fetch the current state as a dictionary
        current_game_state = firestore_service.get_campaign_game_state(user_id, campaign_id)
        if not current_game_state:
            return jsonify({KEY_ERROR: 'Game state not found for GOD_MODE_UPDATE_STATE'}), 404
        
        current_state_dict = current_game_state.to_dict()
        
        # Perform an update
        updated_state_dict = update_state_with_changes(current_state_dict, state_changes)
        updated_state_dict = StateHelper.apply_automatic_combat_cleanup(updated_state_dict, state_changes)
        
        # Convert back to GameState object after the update to validate
        final_game_state = GameState.from_dict(updated_state_dict)
        
        firestore_service.update_campaign_game_state(user_id, campaign_id, final_game_state.to_dict())
        
        log_message = format_state_changes(state_changes, for_html=False)
        return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: f"[System Message: The following state changes were applied via GOD MODE]\\n{log_message}"})
    
    except json.JSONDecodeError:
        return jsonify({KEY_ERROR: 'Invalid JSON payload for GOD_MODE_UPDATE_STATE command.'}), 400
    except ValueError as e:
        return jsonify({KEY_ERROR: f'Error in GOD_MODE_UPDATE_STATE payload: {e}'}), 400
    except Exception as e:
        return jsonify({KEY_ERROR: f'An unexpected error occurred during GOD_MODE_UPDATE_STATE: {e}'}), 500


def _handle_legacy_migration(current_game_state, campaign_id, story_context, user_id):
    """
    Handle one-time legacy migration for campaigns.
    
    Args:
        current_game_state: Current GameState object
        campaign_id: Campaign ID
        story_context: Story context list
        user_id: User ID
        
    Returns:
        GameState: Updated game state object
    """
    logging.info(f"Evaluating campaign {campaign_id} for legacy migration. Current status: {current_game_state.migration_status.value}")
    
    if current_game_state.migration_status != MigrationStatus.NOT_CHECKED:
        logging.info(f"-> Status is {current_game_state.migration_status.value}. Skipping scan.")
        return current_game_state
    
    logging.info(f"-> Status is NOT_CHECKED. Performing scan.")
    
    # The story context here still has datetime objects, which is fine for the parser
    if story_context:
        legacy_state_dict = gemini_service.create_game_state_from_legacy_story(story_context)
    else:
        legacy_state_dict = None
    
    if legacy_state_dict:
        logging.info(f"-> SUCCESS: Found and parsed legacy state for campaign {campaign_id}. Migrating.")
        # Check if we already have a GameState object
        if isinstance(legacy_state_dict, GameState):
            legacy_game_state = legacy_state_dict
        else:
            # If not, create one from the dictionary
            legacy_game_state = GameState.from_dict(legacy_state_dict)
        
        legacy_game_state.migration_status = MigrationStatus.MIGRATED
        
        # Save the newly migrated state to Firestore
        firestore_service.update_campaign_game_state(user_id, campaign_id, legacy_game_state.to_dict())
        return legacy_game_state
    else:
        logging.info(f"-> FAILED: No legacy state found for campaign {campaign_id}. Marking as checked.")
        # Mark as checked and update Firestore so we don't check again
        current_game_state.migration_status = MigrationStatus.NO_LEGACY_DATA
        firestore_service.update_campaign_game_state(user_id, campaign_id, current_game_state.to_dict())
        return current_game_state


def _apply_state_changes_and_respond(proposed_changes, current_game_state, gemini_response, 
                                   mode, story_context, campaign_id, user_id):
    """
    Apply state changes from AI response and prepare final response.
    
    Args:
        proposed_changes: Proposed state changes dict
        current_game_state: Current GameState object
        gemini_response: Full AI response text
        mode: Game mode
        story_context: Story context list
        campaign_id: Campaign ID
        user_id: User ID
        
    Returns:
        Flask response
    """
    # Store the full response with debug content for database and AI context
    full_response_with_debug = gemini_response
    
    # Conditionally strip debug content based on debug mode
    if hasattr(current_game_state, 'debug_mode') and current_game_state.debug_mode:
        # User has debug mode enabled - show ALL debug content
        final_response = full_response_with_debug
    else:
        # User has debug mode disabled - strip ALL debug content
        final_response = StateHelper.strip_debug_content(full_response_with_debug)
    
    if proposed_changes:
        # Track last story mode sequence ID
        if mode == constants.MODE_CHARACTER:
            # The new sequence ID will be the length of the old context plus the two new entries
            last_story_id = len(story_context) + 2
            story_id_update = {
                "custom_campaign_state": {
                    "last_story_mode_sequence_id": last_story_id
                }
            }
            # Merge this update with the changes from the LLM
            proposed_changes = update_state_with_changes(story_id_update, proposed_changes)
        
        # Enhanced logging for normal gameplay
        logging.info(f"AI proposed changes for campaign {campaign_id}:\\n{_truncate_log_json(proposed_changes)}")
        
        log_message = format_state_changes(proposed_changes, for_html=False)
        logging.info(f"Applying formatted state changes for campaign {campaign_id}:\\n{log_message}")
        
        # Update state with changes
        updated_state_dict = update_state_with_changes(current_game_state.to_dict(), proposed_changes)
        updated_state_dict = StateHelper.apply_automatic_combat_cleanup(updated_state_dict, proposed_changes)
        
        logging.info(f"New complete game state for campaign {campaign_id}:\\n{truncate_game_state_for_logging(updated_state_dict)}")
        
        firestore_service.update_campaign_game_state(user_id, campaign_id, updated_state_dict)
    
    # Include debug mode status in response
    return jsonify({
        KEY_SUCCESS: True, 
        KEY_RESPONSE: final_response,
        'debug_mode': current_game_state.debug_mode if hasattr(current_game_state, 'debug_mode') else True
    })


def strip_debug_content(text):
    """
    Strip debug content from AI response text while preserving the rest.
    Removes content between debug tags: [DEBUG_START/END], [DEBUG_ROLL_START/END], [DEBUG_STATE_START/END]
    Also removes [STATE_UPDATES_PROPOSED] blocks which are internal state management.
    
    Args:
        text (str): The full AI response with debug content
        
    Returns:
        str: The response with debug content removed
    """
    if not text:
        return text
        
    # Use regex for proper pattern matching - same patterns as frontend
    processed_text = re.sub(r'\[DEBUG_START\][\s\S]*?\[DEBUG_END\]', '', text)
    processed_text = re.sub(r'\[DEBUG_STATE_START\][\s\S]*?\[DEBUG_STATE_END\]', '', processed_text)
    processed_text = re.sub(r'\[DEBUG_ROLL_START\][\s\S]*?\[DEBUG_ROLL_END\]', '', processed_text)
    # Also strip STATE_UPDATES_PROPOSED blocks which are internal state management
    processed_text = re.sub(r'\[STATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]', '', processed_text)
    # Handle malformed STATE_UPDATES_PROPOSED blocks (missing opening characters)
    processed_text = re.sub(r'S?TATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]', '', processed_text)
    
    return processed_text


def strip_state_updates_only(text):
    """
    Strip only STATE_UPDATES_PROPOSED blocks from text, preserving all other debug content.
    This ensures that internal state management blocks are never shown to users, even in debug mode.
    
    Args:
        text (str): The full AI response text
        
    Returns:
        str: The response with STATE_UPDATES_PROPOSED blocks removed
    """
    if not text:
        return text
    
    # Remove only STATE_UPDATES_PROPOSED blocks - these should never be shown to users
    processed_text = re.sub(r'\[STATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]', '', text)
    # Also handle malformed blocks where the opening characters might be missing
    processed_text = re.sub(r'S?TATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]', '', processed_text)
    return processed_text


def strip_other_debug_content(text):
    """
    Strip all debug content EXCEPT STATE_UPDATES_PROPOSED blocks from text.
    Used when debug mode is disabled to hide DM commentary and dice rolls.
    
    Args:
        text (str): The full AI response text
        
    Returns:
        str: The response with debug content (except state updates) removed
    """
    if not text:
        return text
    
    # Strip debug content but NOT STATE_UPDATES_PROPOSED (already handled separately)
    processed_text = re.sub(r'\[DEBUG_START\][\s\S]*?\[DEBUG_END\]', '', text)
    processed_text = re.sub(r'\[DEBUG_STATE_START\][\s\S]*?\[DEBUG_STATE_END\]', '', processed_text)
    processed_text = re.sub(r'\[DEBUG_ROLL_START\][\s\S]*?\[DEBUG_ROLL_END\]', '', processed_text)
    
    return processed_text


def _handle_debug_mode_command(user_input, mode, current_game_state, user_id, campaign_id):
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
    current_debug_state = getattr(current_game_state, 'debug_mode', False)
    
    if debug_command == 'enable':
        new_debug_state = True
    else:  # disable
        new_debug_state = False
    
    # Only update if state actually changes
    if current_debug_state != new_debug_state:
        current_game_state.debug_mode = new_debug_state
        firestore_service.update_campaign_game_state(user_id, campaign_id, current_game_state.to_dict())
        logging.info(f"Debug mode {'enabled' if new_debug_state else 'disabled'} for campaign {campaign_id}")
    
    # Get appropriate message
    message = DebugModeParser.get_state_update_message(debug_command, new_debug_state)
    
    # Log the user input for history
    firestore_service.add_story_entry(user_id, campaign_id, constants.ACTOR_USER, user_input, mode)
    
    return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: message, 'debug_mode': new_debug_state})

def truncate_game_state_for_logging(game_state_dict, max_lines=20):
    """
    Truncates a game state dictionary for logging to improve readability.
    Only shows the first max_lines lines of the JSON representation.
    """
    json_str = json.dumps(game_state_dict, indent=2, default=json_default_serializer)
    lines = json_str.split('\n')
    
    if len(lines) <= max_lines:
        return json_str
    
    truncated_lines = lines[:max_lines]
    truncated_lines.append(f"... (truncated, showing {max_lines}/{len(lines)} lines)")
    return '\n'.join(truncated_lines)

def apply_automatic_combat_cleanup(updated_state_dict: dict, proposed_changes: dict) -> dict:
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
        logging.error("COMBAT CLEANUP ERROR: GameState.from_dict returned None, returning original state")
        return updated_state_dict
    
    # Check if we have combatants data to potentially clean up
    combatants = temp_game_state.combat_state.get("combatants", {})
    if not combatants:
        logging.info("COMBAT CLEANUP CHECK: No combatants found, skipping cleanup")
        return updated_state_dict
    
    # CRITICAL FIX: Always attempt cleanup if combatants exist
    # This handles ALL cases:
    # 1. Combat ongoing with new defeats
    # 2. Combat ending with pre-existing defeats
    # 3. State updates without explicit combat_state changes but with defeated enemies
    logging.info(f"COMBAT CLEANUP CHECK: Found {len(combatants)} combatants, scanning for defeated enemies...")
    
    # Perform cleanup - this always runs regardless of proposed_changes content
    defeated_enemies = temp_game_state.cleanup_defeated_enemies()
    if defeated_enemies:
        logging.info(f"AUTOMATIC CLEANUP: Defeated enemies removed: {defeated_enemies}")
        # Return the updated state dict from the game state that had cleanup applied
        return temp_game_state.to_dict()
    else:
        logging.info("AUTOMATIC CLEANUP: No defeated enemies found to clean up")
        # Return the original state since no cleanup was needed
        return updated_state_dict

def _cleanup_legacy_state(state_dict: dict) -> tuple[dict, bool, int]:
    """
    Removes legacy data structures from a game state dictionary.
    Specifically, it removes top-level keys with '.' in them and the old 'world_time' key.
    Returns the cleaned dictionary, a boolean indicating if changes were made, and the number of keys removed.
    """
    keys_to_delete = [key for key in state_dict.keys() if '.' in key]
    if 'world_time' in state_dict:
        keys_to_delete.append('world_time')
    
    num_deleted = len(keys_to_delete)

    if not keys_to_delete:
        return state_dict, False, 0

    logging.info(f"Performing one-time cleanup. Deleting {num_deleted} legacy keys: {keys_to_delete}")
    cleaned_state = state_dict.copy()
    for key in keys_to_delete:
        if key in cleaned_state:
             del cleaned_state[key]
    
    return cleaned_state, True, num_deleted

def format_state_changes(changes: dict, for_html: bool = False) -> str:
    """Formats a dictionary of state changes into a readable string, counting the number of leaf-node changes."""
    if not changes:
        return "No state changes."

    log_lines = []

    def recurse_items(d, prefix=""):
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
    else:
        # Create a plain text list for server logs
        items_text = "\\n".join([f"  - {line}" for line in log_lines])
        return f"{header}\\n{items_text}"

def parse_set_command(payload_str: str) -> dict:
    """
    Parses a multi-line string of `key.path = value` into a nested
    dictionary of proposed changes. Handles multiple .append operations correctly.
    """
    proposed_changes = {}
    append_ops = collections.defaultdict(list)

    for line in payload_str.strip().splitlines():
        line = line.strip()
        if not line or '=' not in line:
            continue
        
        key_path, value_str = line.split('=', 1)
        key_path = key_path.strip()
        value_str = value_str.strip()

        try:
            value = json.loads(value_str)
        except json.JSONDecodeError:
            logging.warning(f"Skipping line in SET command due to invalid JSON value: {line}")
            continue
        
        if key_path.endswith('.append'):
            base_key = key_path[:-len('.append')]
            append_ops[base_key].append(value)
            continue

        keys = key_path.split('.')
        d = proposed_changes
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
        
    for base_key, values_to_append in append_ops.items():
        keys = base_key.split('.')
        d = proposed_changes
        for key in keys:
            d = d.setdefault(key, {})
        d['append'] = values_to_append

    return proposed_changes

def create_app():
    app = Flask(__name__, static_folder='static')
    CORS(app, resources=CORS_RESOURCES)

    if not firebase_admin._apps:
        firebase_admin.initialize_app()

    def check_token(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if app.config.get('TESTING') and request.headers.get(HEADER_TEST_BYPASS) == 'true':
                kwargs['user_id'] = request.headers.get(HEADER_TEST_USER_ID, DEFAULT_TEST_USER)
                return f(*args, **kwargs)
            if not request.headers.get(HEADER_AUTH): return jsonify({KEY_MESSAGE: 'No token provided'}), 401
            try:
                id_token = request.headers[HEADER_AUTH].split(' ').pop()
                decoded_token = auth.verify_id_token(id_token)
                kwargs['user_id'] = decoded_token['uid']
            except Exception as e:
                return jsonify({KEY_SUCCESS: False, KEY_ERROR: f"Auth failed: {e}", KEY_TRACEBACK: traceback.format_exc()}), 401
            return f(*args, **kwargs)
        return wrap

    # --- API Routes ---
    @app.route('/api/campaigns', methods=['GET'])
    @check_token
    def get_campaigns(user_id):
        # --- RESTORED TRY-EXCEPT BLOCK ---
        try:
            return jsonify(firestore_service.get_campaigns_for_user(user_id))
        except Exception as e:
            return jsonify({KEY_SUCCESS: False, KEY_ERROR: str(e), KEY_TRACEBACK: traceback.format_exc()}), 500
        # --- END RESTORED BLOCK ---

    @app.route('/api/campaigns/<campaign_id>', methods=['GET'])
    @check_token
    def get_campaign(user_id, campaign_id):
        # --- RESTORED TRY-EXCEPT BLOCK ---
        try:
            campaign, story = firestore_service.get_campaign_by_id(user_id, campaign_id)
            if not campaign: return jsonify({KEY_ERROR: 'Campaign not found'}), 404
            
            # Include game state for debug mode status
            game_state = firestore_service.get_campaign_game_state(user_id, campaign_id)
            game_state_dict = game_state.to_dict() if game_state else {}
            
            return jsonify({KEY_CAMPAIGN: campaign, KEY_STORY: story, 'game_state': game_state_dict})
        except Exception as e:
            return jsonify({KEY_SUCCESS: False, KEY_ERROR: str(e), KEY_TRACEBACK: traceback.format_exc()}), 500
        # --- END RESTORED BLOCK ---

    @app.route('/api/campaigns', methods=['POST'])
    @check_token
    def create_campaign_route(user_id):
        data = request.get_json()
        prompt, title = data.get(KEY_PROMPT), data.get(constants.KEY_TITLE)
        selected_prompts = data.get(KEY_SELECTED_PROMPTS, [])
        custom_options = data.get('custom_options', [])
        
        # Debug logging
        app.logger.info(f"Received custom_options: {custom_options}")
        
        # Always use D&D system (Destiny system removed)
        attribute_system = constants.ATTRIBUTE_SYSTEM_DND
        
        app.logger.info(f"Selected attribute_system: {attribute_system}")
        
        # Create initial game state with attribute system
        initial_game_state = GameState(
            custom_campaign_state={'attribute_system': attribute_system}
        ).to_dict()

        generate_companions = 'companions' in custom_options
        use_default_world = 'defaultWorld' in custom_options
        
        opening_story = gemini_service.get_initial_story(
            prompt, 
            selected_prompts=selected_prompts,
            generate_companions=generate_companions,
            use_default_world=use_default_world
        )
        
        campaign_id = firestore_service.create_campaign(
            user_id, title, prompt, opening_story, initial_game_state, selected_prompts, use_default_world
        )
        
        return jsonify({KEY_SUCCESS: True, KEY_CAMPAIGN_ID: campaign_id}), 201
        
    @app.route('/api/campaigns/<campaign_id>', methods=['PATCH'])
    @check_token
    def update_campaign(user_id, campaign_id):
        data = request.get_json()
        new_title = data.get(constants.KEY_TITLE)
        if not new_title:
            return jsonify({KEY_ERROR: 'New title is required'}), 400
        
        try:
            firestore_service.update_campaign_title(user_id, campaign_id, new_title)
            return jsonify({KEY_SUCCESS: True, KEY_MESSAGE: 'Campaign title updated successfully.'})
        except Exception as e:
            traceback.print_exc()
            return jsonify({KEY_ERROR: 'Failed to update campaign', KEY_DETAILS: str(e)}), 500

    @app.route('/api/campaigns/<campaign_id>/interaction', methods=['POST'])
    @check_token
    def handle_interaction(user_id, campaign_id):
        data = request.get_json()
        user_input, mode = data.get(KEY_USER_INPUT), data.get(constants.KEY_MODE, constants.MODE_CHARACTER)
        
        # --- Special command handling ---
        GOD_MODE_SET_COMMAND = "GOD_MODE_SET:"
        GOD_ASK_STATE_COMMAND = "GOD_ASK_STATE"
        GOD_MODE_UPDATE_STATE_COMMAND = "GOD_MODE_UPDATE_STATE:"

        user_input_stripped = user_input.strip()

        # --- Game State Loading and Legacy Cleanup ---
        current_game_state, was_cleaned, num_cleaned = _prepare_game_state(user_id, campaign_id)
        game_state_dict = current_game_state.to_dict()

        # --- Debug Mode Command Parsing (BEFORE other commands) ---
        debug_response = _handle_debug_mode_command(user_input, mode, current_game_state, user_id, campaign_id)
        if debug_response:
            return debug_response
        
        # --- Retroactive MBTI Assignment Logging ---
        game_state_dict = current_game_state.to_dict()
        pc_data = game_state_dict.get('player_character_data', {})
        if constants.KEY_MBTI not in pc_data:
            pc_name = pc_data.get('name', 'Player Character')
            logging.info(f"RETROACTIVE_ASSIGNMENT: Character '{pc_name}' is missing an MBTI type. The AI will be prompted to assign one.")

        npc_data = game_state_dict.get('npc_data', {})
        for npc_id, npc_info in npc_data.items():
            # Defensive programming: ensure npc_info is a dictionary
            if not isinstance(npc_info, dict):
                logging.warning(f"NPC data for '{npc_id}' is not a dictionary: {type(npc_info)}. Skipping MBTI check.")
                continue
                
            if constants.KEY_MBTI not in npc_info:
                npc_name = npc_info.get('name', npc_id)
                logging.info(f"RETROACTIVE_ASSIGNMENT: NPC '{npc_name}' is missing an MBTI type. The AI will be prompted to assign one.")
        # --- END Retroactive MBTI ---

        # Handle SET command
        set_response = _handle_set_command(user_input, current_game_state, user_id, campaign_id)
        if set_response:
            return set_response

        # --- Debug Mode Command Parsing (BEFORE other commands) ---
        debug_response = _handle_debug_mode_command(user_input, mode, current_game_state, user_id, campaign_id)
        if debug_response:
            return debug_response
        
        # Handle ASK_STATE command
        ask_state_response = _handle_ask_state_command(user_input, current_game_state, user_id, campaign_id)
        if ask_state_response:
            return ask_state_response

        # Handle UPDATE_STATE command
        update_state_response = _handle_update_state_command(user_input, user_id, campaign_id)
        if update_state_response:
            return update_state_response

        # Fetch campaign metadata and story context
        campaign, story_context = firestore_service.get_campaign_by_id(user_id, campaign_id)
        if not campaign: return jsonify({KEY_ERROR: 'Campaign not found'}), 404
        
        # --- ONE-TIME LEGACY MIGRATION ---
        current_game_state = _handle_legacy_migration(current_game_state, campaign_id, story_context, user_id)

        # 2. Add user's action to the story log
        firestore_service.add_story_entry(user_id, campaign_id, constants.ACTOR_USER, user_input, mode)
        
        # 3. Process: Get AI response, passing in the current state
        selected_prompts = campaign.get(KEY_SELECTED_PROMPTS, [])
        use_default_world = campaign.get('use_default_world', False)
        gemini_response = gemini_service.continue_story(user_input, mode, story_context, current_game_state, selected_prompts, use_default_world)
        
        # 3a. Verify debug content generation for monitoring
        debug_tags_found = {
            'dm_notes': '[DEBUG_START]' in gemini_response,
            'dice_rolls': '[DEBUG_ROLL_START]' in gemini_response,
            'state_changes': '[DEBUG_STATE_START]' in gemini_response
        }
        
        if not any(debug_tags_found.values()):
            logging.warning(f"AI response missing debug content for campaign {campaign_id}")
            logging.warning(f"Debug tags found: {debug_tags_found}")
            logging.warning(f"Response length: {len(gemini_response)} chars")
        else:
            # Log which debug content types were included
            logging.info(f"Debug content generated for campaign {campaign_id}: {debug_tags_found}")
        
        # 4. Write: Add AI response to story log and update state
        firestore_service.add_story_entry(user_id, campaign_id, constants.ACTOR_GEMINI, gemini_response)

        # 5. Parse and apply state changes from AI response
        proposed_changes = gemini_service.parse_llm_response_for_state_changes(gemini_response)
        
        # --- NEW: Post-response checkpoint validation ---
        if proposed_changes:
            # Apply changes to a temporary state copy for validation
            temp_state_dict = current_game_state.to_dict()
            updated_temp_state = update_state_with_changes(temp_state_dict, proposed_changes)
            temp_game_state = GameState.from_dict(updated_temp_state)
            
            # Validate the new response against the updated state
            post_update_discrepancies = temp_game_state.validate_checkpoint_consistency(gemini_response)
            
            if post_update_discrepancies:
                logging.warning(f"POST_UPDATE_VALIDATION: AI response created {len(post_update_discrepancies)} new discrepancies:")
                for i, discrepancy in enumerate(post_update_discrepancies, 1):
                    logging.warning(f"  {i}. {discrepancy}")
        
        # Apply state changes and return response
        return _apply_state_changes_and_respond(proposed_changes, current_game_state, gemini_response, 
                                              mode, story_context, campaign_id, user_id)


    @app.route('/api/campaigns/<campaign_id>/export', methods=['GET'])
    @check_token
    def export_campaign(user_id, campaign_id):
        try:
            export_format = request.args.get('format', 'txt').lower()
            
            campaign_data, story_log = firestore_service.get_campaign_by_id(user_id, campaign_id)
            if not campaign_data:
                return jsonify({KEY_ERROR: 'Campaign not found'}), 404

            campaign_title = campaign_data.get('title', 'Untitled Campaign')
            desired_download_name = f"{campaign_title}.{export_format}"

            temp_dir = '/tmp/campaign_exports'
            os.makedirs(temp_dir, exist_ok=True)
            safe_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.{export_format}")
            
            story_parts = []
            for entry in story_log:
                actor = entry.get(constants.KEY_ACTOR, document_generator.UNKNOWN_ACTOR)
                text = entry.get(constants.KEY_TEXT, '')
                mode = entry.get(constants.KEY_MODE)
                if actor == constants.ACTOR_GEMINI:
                    label = document_generator.LABEL_GEMINI
                else:
                    label = document_generator.LABEL_GOD if mode == constants.MODE_GOD else document_generator.LABEL_USER
                story_parts.append(f"{label}:\\n{text}")
            story_text = "\\n\\n".join(story_parts)
            
            if export_format == 'pdf':
                document_generator.generate_pdf(story_text, safe_file_path, campaign_title)
            elif export_format == 'docx':
                document_generator.generate_docx(story_text, safe_file_path, campaign_title)
            elif export_format == 'txt':
                document_generator.generate_txt(story_text, safe_file_path, campaign_title)
            else:
                return jsonify({KEY_ERROR: f"Unsupported format: {export_format}"}), 400

            if os.path.exists(safe_file_path):
                logging.info(f"Exporting file '{safe_file_path}' with download_name='{desired_download_name}'")
                
                # Use the standard send_file call, which should now work correctly
                # with the fixed JavaScript client.
                response = send_file(
                    safe_file_path,
                    download_name=desired_download_name,
                    as_attachment=True
                )

                @response.call_on_close
                def cleanup():
                    try:
                        os.remove(safe_file_path)
                        logging.info(f"Cleaned up temporary file: {safe_file_path}")
                    except Exception as e:
                        logging.error(f"Error cleaning up file {safe_file_path}: {e}")

                return response
            else:
                return jsonify({KEY_ERROR: 'Failed to create export file.'}), 500

        except Exception as e:
            logging.error(f"Export failed: {e}")
            traceback.print_exc()
            return jsonify({KEY_ERROR: 'An unexpected error occurred during export.', KEY_DETAILS: str(e)}), 500


    # --- Frontend Serving ---
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    return app

def run_god_command(campaign_id, user_id, action, command_string=None):
    """Runs a GOD_MODE command directly against Firestore."""
    # We need to initialize the app to get the context for Firestore
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
        
    if action == 'ask':
        print(f"Fetching current state for campaign: {campaign_id}")
        current_game_state = firestore_service.get_campaign_game_state(user_id, campaign_id)
        if not current_game_state:
            print("No game state found for this campaign.")
            return
        
        # Pretty-print the JSON to the console
        state_json = json.dumps(current_game_state.to_dict(), indent=2, default=json_default_serializer)
        print(state_json)
        return

    elif action == 'set':
        if not command_string:
            print("Error: The 'set' action requires a --command_string.")
            return

        if not command_string.strip().startswith("GOD_MODE_SET:"):
            print("Error: Command string must start with GOD_MODE_SET:")
            return

        payload_str = command_string.strip()[len("GOD_MODE_SET:"):].strip()
        proposed_changes = parse_set_command(payload_str)
        
        if not proposed_changes:
            print("Command contained no valid changes.")
            return

        print(f"Applying changes to campaign: {campaign_id}")
        
        current_game_state_doc = firestore_service.get_campaign_game_state(user_id, campaign_id)
        current_state_dict = current_game_state_doc.to_dict() if current_game_state_doc else GameState().to_dict()

        updated_state = update_state_with_changes(current_state_dict, proposed_changes)
        updated_state = apply_automatic_combat_cleanup(updated_state, proposed_changes)
        firestore_service.update_campaign_game_state(user_id, campaign_id, updated_state)
        
        log_message = format_state_changes(proposed_changes, for_html=False)
        print(f"Update successful:\\n{log_message}")

    else:
        print(f"Error: Unknown god-command action '{action}'. Use 'set' or 'ask'.")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="World Architect AI Server & Tools")
    parser.add_argument('command', nargs='?', default='serve', help="Command to run ('serve' or 'god-command')")
    
    # Manual parsing for god-command to handle multi-line strings
    if len(sys.argv) > 1 and sys.argv[1] == 'god-command':
        parser.add_argument('action', choices=['set', 'ask'], help="The action to perform ('set' or 'ask')")
        parser.add_argument('--campaign_id', required=True, help="Campaign ID for the god-command")
        parser.add_argument('--user_id', required=True, help="User ID who owns the campaign")
        parser.add_argument('--command_string', help="The full GOD_MODE_SET command string (required for 'set')")
        
        args, unknown = parser.parse_known_args(sys.argv[2:])
        
        if args.action == 'set' and not args.command_string:
             # Manually reconstruct the command string if it was not passed with the flag
            try:
                command_string_index = sys.argv.index('--command_string')
                args.command_string = " ".join(sys.argv[command_string_index + 1:])
            except (ValueError, IndexError):
                 parser.error("--command_string is required for the 'set' action.")

        run_god_command(args.campaign_id, args.user_id, args.action, args.command_string)

    else:
        # Standard server execution
        args = parser.parse_args()
        if args.command == 'serve':
            app = create_app()
            port = int(os.environ.get('PORT', 8080))
            print(f"Development server running: http://localhost:{port}")
            app.run(host='0.0.0.0', port=port, debug=True)
        else:
            parser.error(f"Unknown command: {args.command}")
