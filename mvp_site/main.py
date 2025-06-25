# Diagnostic edit to test file system access.
import os
import io
import uuid
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth
import traceback
import document_generator
import logging
from game_state import GameState, MigrationStatus
import constants
import json
import collections
from firestore_service import update_state_with_changes, json_default_serializer

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
    # Create a temporary GameState object to use the cleanup method
    temp_game_state = GameState.from_dict(updated_state_dict)
    
    # Check if we have combatants data to potentially clean up
    combatants = temp_game_state.combat_state.get("combatants", {})
    if not combatants:
        logging.info("COMBAT CLEANUP CHECK: No combatants found, skipping cleanup")
        return updated_state_dict
    
    # CRITICAL FIX: Always attempt cleanup if combatants exist, regardless of in_combat status
    # This handles the case where combat is ending (in_combat becomes false) but defeated enemies still remain
    logging.info(f"COMBAT CLEANUP CHECK: Found {len(combatants)} combatants, checking for defeated enemies...")
    
    # Perform cleanup 
    defeated_enemies = temp_game_state.cleanup_defeated_enemies()
    if defeated_enemies:
        logging.info(f"AUTOMATIC CLEANUP: Defeated enemies removed: {defeated_enemies}")
        return temp_game_state.to_dict()
    else:
        logging.info("AUTOMATIC CLEANUP: No defeated enemies found to clean up")
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
            return jsonify({KEY_CAMPAIGN: campaign, KEY_STORY: story})
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
        
        # Create a blank initial game state.
        initial_game_state = GameState().to_dict()

        should_include_srd = constants.PROMPT_TYPE_MECHANICS in selected_prompts
        generate_companions = 'companions' in custom_options
        opening_story = gemini_service.get_initial_story(
            prompt, 
            selected_prompts=selected_prompts,
            include_srd=should_include_srd,
            generate_companions=generate_companions
        )
        
        campaign_id = firestore_service.create_campaign(
            user_id, title, prompt, opening_story, initial_game_state, selected_prompts
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
        current_game_state_doc = firestore_service.get_campaign_game_state(user_id, campaign_id)
        
        # This is the key fix: ensure current_game_state is always a valid GameState object.
        if current_game_state_doc:
            current_game_state = GameState.from_dict(current_game_state_doc.to_dict())
        else:
            current_game_state = GameState()
        
        game_state_dict = current_game_state.to_dict()

        # Perform cleanup on a dictionary copy
        cleaned_state_dict, was_cleaned, num_cleaned = _cleanup_legacy_state(current_game_state.to_dict())
        if was_cleaned:
            # If cleaned, update the main object from the cleaned dictionary
            current_game_state = GameState.from_dict(cleaned_state_dict)
            firestore_service.update_campaign_game_state(user_id, campaign_id, current_game_state.to_dict())
            logging.info(f"Legacy state cleanup complete. Removed {num_cleaned} entries.")
        # --- End cleanup ---

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

        if user_input_stripped.startswith(GOD_MODE_SET_COMMAND):
            payload_str = user_input_stripped[len(GOD_MODE_SET_COMMAND):]
            logging.info(f"--- GOD_MODE_SET received for campaign {campaign_id} ---")
            logging.info(f"GOD_MODE_SET raw payload:\\n---\\n{payload_str}\\n---")
            
            proposed_changes = parse_set_command(payload_str)
            logging.info(f"GOD_MODE_SET parsed changes to be merged:\\n{json.dumps(proposed_changes, indent=2, default=json_default_serializer)}")

            if not proposed_changes:
                logging.warning(f"GOD_MODE_SET command resulted in no valid changes.")
                return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: "[System Message: The GOD_MODE_SET command was received, but contained no valid instructions or was empty.]"})

            # The loaded current_game_state object is guaranteed to be valid here
            current_state_dict_before_update = current_game_state.to_dict()
            logging.info(f"GOD_MODE_SET state BEFORE update:\\n{json.dumps(current_state_dict_before_update, indent=2, default=json_default_serializer)}")
            
            updated_state = update_state_with_changes(current_state_dict_before_update, proposed_changes)
            updated_state = apply_automatic_combat_cleanup(updated_state, proposed_changes)
            logging.info(f"GOD_MODE_SET state AFTER update:\\n{json.dumps(updated_state, indent=2, default=json_default_serializer)}")
            
            firestore_service.update_campaign_game_state(user_id, campaign_id, updated_state)
            
            # --- Log the formatted changes for both server and chat ---
            log_message_for_log = format_state_changes(proposed_changes, for_html=False)
            logging.info(f"GOD_MODE_SET changes applied for campaign {campaign_id}:\\n{log_message_for_log}")
            
            log_message_for_chat = format_state_changes(proposed_changes, for_html=True)
            
            logging.info(f"--- GOD_MODE_SET for campaign {campaign_id} complete ---")

            return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: f"[System Message]<br>{log_message_for_chat}"})

        if user_input_stripped == GOD_ASK_STATE_COMMAND:
            # The loaded current_game_state object is guaranteed to be valid here
            game_state_json = json.dumps(current_game_state.to_dict(), indent=2, default=json_default_serializer)
            
            firestore_service.add_story_entry(user_id, campaign_id, constants.ACTOR_USER, user_input, mode)
            
            response_text = f"```json\\n{game_state_json}\\n```"
            return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: response_text})

        # Special command handling for direct state updates
        if user_input.strip().startswith(GOD_MODE_UPDATE_STATE_COMMAND):
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
                updated_state_dict = apply_automatic_combat_cleanup(updated_state_dict, state_changes)
                
                # Convert back to GameState object *after* the update to validate and use its methods
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

        # Fetch campaign metadata and story context
        campaign, story_context = firestore_service.get_campaign_by_id(user_id, campaign_id)
        if not campaign: return jsonify({KEY_ERROR: 'Campaign not found'}), 404
        
        # --- ONE-TIME LEGACY MIGRATION ---
        logging.info(f"Evaluating campaign {campaign_id} for legacy migration. Current status: {current_game_state.migration_status.value}")
        if current_game_state.migration_status == MigrationStatus.NOT_CHECKED:
            logging.info(f"-> Status is NOT_CHECKED. Performing scan.")
            # The story context here still has datetime objects, which is fine for the parser.
            if story_context:
                legacy_state_dict = gemini_service.create_game_state_from_legacy_story(story_context)
            else:
                legacy_state_dict = None
            
            if legacy_state_dict:
                logging.info(f"-> SUCCESS: Found and parsed legacy state for campaign {campaign_id}. Migrating.")
                # This is the fix. Check if we already have a GameState object.
                if isinstance(legacy_state_dict, GameState):
                    legacy_game_state = legacy_state_dict
                else:
                    # If not, create one from the dictionary.
                    legacy_game_state = GameState.from_dict(legacy_state_dict)
                
                legacy_game_state.migration_status = MigrationStatus.MIGRATED
                
                # Overwrite the current_game_state object and its dictionary representation
                current_game_state = legacy_game_state
                
                # Save the newly migrated state to Firestore.
                firestore_service.update_campaign_game_state(user_id, campaign_id, current_game_state.to_dict())
            else:
                logging.info(f"-> FAILED: No legacy state found for campaign {campaign_id}. Marking as checked.")
                # Mark as checked and update Firestore so we don't check again.
                current_game_state.migration_status = MigrationStatus.NO_LEGACY_DATA
                # Pass the full dict to ensure document creation on the first run.
                firestore_service.update_campaign_game_state(user_id, campaign_id, current_game_state.to_dict())
        else:
            logging.info(f"-> Status is {current_game_state.migration_status.value}. Skipping scan.")

        # 2. Add user's action to the story log
        firestore_service.add_story_entry(user_id, campaign_id, constants.ACTOR_USER, user_input, mode)
        
        # 3. Process: Get AI response, passing in the current state
        selected_prompts = campaign.get(KEY_SELECTED_PROMPTS, [])
        gemini_response = gemini_service.continue_story(user_input, mode, story_context, current_game_state, selected_prompts)
        
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
        
        # --- NEW: Append state changes to response for player ---
        final_response = gemini_response
        
        if proposed_changes:
            # --- NEW: Track last story mode sequence ID ---
            if mode == constants.MODE_CHARACTER:
                # The new sequence ID will be the length of the old context plus the two
                # new entries (user and AI).
                last_story_id = len(story_context) + 2
                story_id_update = {
                    "custom_campaign_state": {
                        "last_story_mode_sequence_id": last_story_id
                    }
                }
                # Merge this update with the changes from the LLM
                proposed_changes = update_state_with_changes(story_id_update, proposed_changes)

            # --- NEW: Enhanced Logging for normal gameplay ---
            logging.info(f"AI proposed changes for campaign {campaign_id}:\\n{json.dumps(proposed_changes, indent=2, default=json_default_serializer)}")

            log_message = format_state_changes(proposed_changes, for_html=False)
            logging.info(f"Applying formatted state changes for campaign {campaign_id}:\\n{log_message}")
            
            # --- FIX: UPDATE STATE WITH CHANGES ---
            updated_state_dict = update_state_with_changes(current_game_state.to_dict(), proposed_changes)
            updated_state_dict = apply_automatic_combat_cleanup(updated_state_dict, proposed_changes)

            logging.info(f"New complete game state for campaign {campaign_id}:\\n{json.dumps(updated_state_dict, indent=2, default=json_default_serializer)}")
            
            firestore_service.update_campaign_game_state(user_id, campaign_id, updated_state_dict)
            
        return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: final_response})


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
