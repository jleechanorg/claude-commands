import os
import io
import uuid
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth
import traceback
import document_generator
import logging
from game_state import GameState, MigrationStatus
import constants
import json
import datetime
import collections
import urllib.parse
from firestore_service import update_state_with_changes
import mimetypes
from werkzeug.utils import secure_filename
from werkzeug.http import dump_options_header

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

def _cleanup_legacy_state(state_dict: dict) -> tuple[dict, bool]:
    """
    Removes legacy data structures from a game state dictionary.
    Specifically, it removes top-level keys with '.' in them and the old 'world_time' key.
    Returns the cleaned dictionary and a boolean indicating if changes were made.
    """
    keys_to_delete = [key for key in state_dict.keys() if '.' in key]
    if 'world_time' in state_dict:
        keys_to_delete.append('world_time')
    
    if not keys_to_delete:
        return state_dict, False

    logging.info(f"Performing one-time cleanup. Deleting legacy keys: {keys_to_delete}")
    cleaned_state = state_dict.copy()
    for key in keys_to_delete:
        if key in cleaned_state:
             del cleaned_state[key]
    
    return cleaned_state, True

def format_state_changes(changes: dict) -> str:
    """Formats a dictionary of state changes into a readable, multi-line string."""
    if not changes:
        return "No state changes."

    log_lines = ["State changes applied:"]

    def recurse_items(d, prefix=""):
        for key, value in d.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                recurse_items(value, prefix=path)
            else:
                log_lines.append(f"  - {path}: {json.dumps(value)}")

    recurse_items(changes)
    return "\\n".join(log_lines)

def json_default_serializer(o):
    """Handles serialization of data types json doesn't know, like datetimes."""
    if isinstance(o, (datetime.datetime, datetime.date)):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

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

    import gemini_service
    import firestore_service

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
        
        # Create a blank initial game state.
        initial_game_state = GameState().to_dict()

        should_include_srd = constants.PROMPT_TYPE_MECHANICS in selected_prompts
        
        # 1. Get both the story and the structured character profile
        opening_story, character_profile = gemini_service.get_initial_story(
            prompt, 
            selected_prompts=selected_prompts,
            include_srd=should_include_srd
        )

        # 2. If a profile was returned, merge it into the initial game state
        if character_profile:
            logging.info("Merging generated character profile into initial game state.")
            # Use the deep merge utility to safely add the profile
            initial_game_state = update_state_with_changes(
                initial_game_state, 
                {'player_character_data': character_profile}
            )
        else:
            logging.warning("No character profile was returned from gemini_service.get_initial_story.")
        
        # 3. Create the campaign with the enriched game state
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

        # --- One-time legacy state cleanup on any interaction ---
        current_game_state_doc = firestore_service.get_campaign_game_state(user_id, campaign_id)
        if not current_game_state_doc:
            return jsonify({KEY_SUCCESS: False, KEY_ERROR: "Game state not found for this campaign."}), 404
        
        current_state_dict = current_game_state_doc.to_dict()
        current_state_dict, was_cleaned = _cleanup_legacy_state(current_state_dict)
        if was_cleaned:
            firestore_service.update_campaign_game_state(user_id, campaign_id, current_state_dict)
            logging.info("Legacy state cleanup complete.")
        # --- End cleanup ---

        if user_input_stripped.startswith(GOD_MODE_SET_COMMAND):
            payload_str = user_input_stripped[len(GOD_MODE_SET_COMMAND):]
            logging.info(f"--- GOD_MODE_SET received for campaign {campaign_id} ---")
            logging.info(f"GOD_MODE_SET raw payload:\\n---\\n{payload_str}\\n---")
            
            proposed_changes = parse_set_command(payload_str)
            logging.info(f"GOD_MODE_SET parsed changes to be merged:\\n{json.dumps(proposed_changes, indent=2, default=json_default_serializer)}")

            if not proposed_changes:
                logging.warning(f"GOD_MODE_SET command resulted in no valid changes.")
                return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: "[System Message: The GOD_MODE_SET command was received, but contained no valid instructions or was empty.]"})

            # No need to re-fetch state, it's already loaded and cleaned above.
            current_state_dict_before_update = current_state_dict.copy()
            logging.info(f"GOD_MODE_SET state BEFORE update:\\n{json.dumps(current_state_dict_before_update, indent=2, default=json_default_serializer)}")
            
            updated_state = update_state_with_changes(current_state_dict_before_update, proposed_changes)
            logging.info(f"GOD_MODE_SET state AFTER update:\\n{json.dumps(updated_state, indent=2, default=json_default_serializer)}")
            
            firestore_service.update_campaign_game_state(user_id, campaign_id, updated_state)
            logging.info(f"--- GOD_MODE_SET for campaign {campaign_id} complete ---")

            return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: "[System Message: Game state has been forcefully updated.]"})

        if user_input_stripped == GOD_ASK_STATE_COMMAND:
            # No need to re-fetch state, it's already loaded and cleaned.
            game_state_json = json.dumps(current_state_dict, indent=2, default=json_default_serializer)
            
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
                
                # Convert back to GameState object *after* the update to validate and use its methods
                final_game_state = GameState.from_dict(updated_state_dict)

                firestore_service.update_campaign_game_state(user_id, campaign_id, final_game_state.to_dict())

                log_message = format_state_changes(state_changes)
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
        
        # --- NEW STATE MANAGEMENT WORKFLOW ---
        # 1. Read current game state
        current_game_state = firestore_service.get_campaign_game_state(user_id, campaign_id)
        if not current_game_state:
            # If no game state exists at all, create a fresh one.
            current_game_state = GameState()

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

            log_message = format_state_changes(proposed_changes)
            logging.info(f"Applying formatted state changes for campaign {campaign_id}:\\n{log_message}")
            
            # --- FIX: UPDATE STATE WITH CHANGES ---
            updated_state_dict = update_state_with_changes(current_game_state.to_dict(), proposed_changes)

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

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    print(f"Development server running: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
