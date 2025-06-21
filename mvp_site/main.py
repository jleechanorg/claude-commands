import os
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
import datetime

def deep_merge(source, destination):
    """
    Recursively merges source dict into destination dict.
    - Nested dictionaries are merged.
    - If a value in source is '__DELETE__', the corresponding key in destination is removed.
    - Other values from source overwrite values in destination.
    """
    for key, value in source.items():
        if value == '__DELETE__':
            if key in destination:
                del destination[key]
        elif isinstance(value, dict):
            # Get node or create one
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        else:
            destination[key] = value
    return destination

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
    dictionary of proposed changes. This is more robust than a single JSON blob.
    """
    proposed_changes = {}
    for line in payload_str.strip().splitlines():
        line = line.strip()
        if not line or '=' not in line:
            continue
        
        key_path, value_str = line.split('=', 1)
        key_path = key_path.strip()
        value_str = value_str.strip()

        try:
            # The value must be a valid JSON literal (e.g., "string", 123, true, {}, [])
            value = json.loads(value_str)
        except json.JSONDecodeError:
            logging.warning(f"Skipping line in SET command due to invalid JSON value: {line}")
            continue
        
        # Build the nested dictionary structure from the key path
        keys = key_path.split('.')
        d = proposed_changes
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value
        
    return proposed_changes

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
        opening_story = gemini_service.get_initial_story(
            prompt, 
            selected_prompts=selected_prompts,
            include_srd=should_include_srd
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

        user_input_stripped = user_input.strip()

        if user_input_stripped.startswith(GOD_MODE_SET_COMMAND):
            payload_str = user_input_stripped[len(GOD_MODE_SET_COMMAND):]
            
            # Use the new robust parser for line-by-line updates
            proposed_changes = parse_set_command(payload_str)

            if not proposed_changes:
                logging.warning(f"GOD_MODE_SET command for campaign {campaign_id} resulted in no valid changes.")
                return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: "[System Message: The GOD_MODE_SET command was received, but contained no valid instructions or was empty.]"})

            current_game_state_dict = firestore_service.get_campaign_game_state(user_id, campaign_id)
            if not current_game_state_dict:
                return jsonify({KEY_ERROR: 'Campaign game state not found, cannot apply manual update.'}), 404

            # --- NEW: Enhanced logging ---
            log_message = format_state_changes(proposed_changes)
            logging.info(f"Received GOD_MODE_SET for campaign {campaign_id}. Raw payload:\\n---\\n{payload_str}\\n---")
            logging.info(f"Applying PARSED state changes for campaign {campaign_id}:\\n{log_message}")

            updated_state_dict = deep_merge(proposed_changes, current_game_state_dict)
            
            firestore_service.update_campaign_game_state(user_id, campaign_id, updated_state_dict)
            
            firestore_service.add_story_entry(user_id, campaign_id, constants.ACTOR_USER, user_input, mode)
            
            # Return a confirmation message showing what was changed.
            return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: f"[System Message: Game state has been manually updated via GOD_MODE_SET command.]\\n\\n{log_message}"})

        if user_input_stripped == GOD_ASK_STATE_COMMAND:
            current_game_state_dict = firestore_service.get_campaign_game_state(user_id, campaign_id)
            if not current_game_state_dict:
                return jsonify({KEY_ERROR: 'Campaign game state not found.'}), 404
            
            game_state_json = json.dumps(current_game_state_dict, indent=2, default=json_default_serializer)
            
            firestore_service.add_story_entry(user_id, campaign_id, constants.ACTOR_USER, user_input, mode)
            
            response_text = f"```json\\n{game_state_json}\\n```"
            return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: response_text})
        # --- END of special command handling ---

        # Fetch campaign metadata and story context
        campaign, story_context = firestore_service.get_campaign_by_id(user_id, campaign_id)
        if not campaign: return jsonify({KEY_ERROR: 'Campaign not found'}), 404
        
        # --- NEW STATE MANAGEMENT WORKFLOW ---
        # 1. Read current game state
        current_game_state_dict = firestore_service.get_campaign_game_state(user_id, campaign_id)
        if not current_game_state_dict:
            # If no game state exists at all, create a fresh one.
            current_game_state_dict = GameState().to_dict()

        # Instantiate a GameState object from the dictionary for use in this turn
        current_game_state = GameState.from_dict(current_game_state_dict)

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
                # Instantiate a new GameState object from the migrated dict
                legacy_game_state = GameState.from_dict(legacy_state_dict)
                legacy_game_state.migration_status = MigrationStatus.MIGRATED
                
                # Overwrite the current_game_state object and its dictionary representation
                current_game_state = legacy_game_state
                current_game_state_dict = legacy_game_state.to_dict()
                
                # Save the newly migrated state to Firestore.
                firestore_service.update_campaign_game_state(user_id, campaign_id, current_game_state_dict)
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
                proposed_changes = deep_merge(story_id_update, proposed_changes)

            # --- NEW: Enhanced Logging for normal gameplay ---
            logging.info(f"AI proposed changes for campaign {campaign_id}:\\n{json.dumps(proposed_changes, indent=2, default=json_default_serializer)}")

            log_message = format_state_changes(proposed_changes)
            logging.info(f"Applying formatted state changes for campaign {campaign_id}:\\n{log_message}")
            
            # --- FIX: DEEP MERGE STATE UPDATES ---
            updated_state_dict = deep_merge(proposed_changes, current_game_state.to_dict())

            logging.info(f"New complete game state for campaign {campaign_id}:\\n{json.dumps(updated_state_dict, indent=2, default=json_default_serializer)}")
            
            firestore_service.update_campaign_game_state(user_id, campaign_id, updated_state_dict)
            
        return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: final_response})

    @app.route('/api/campaigns/<campaign_id>/export', methods=['GET'])
    @check_token
    def export_campaign(user_id, campaign_id):
        file_format = request.args.get(constants.KEY_FORMAT, constants.FORMAT_TXT).lower()
        campaign, story_context = firestore_service.get_campaign_by_id(user_id, campaign_id)
        if not campaign:
            return jsonify({KEY_ERROR: 'Campaign not found'}), 404
        campaign_title = campaign.get(constants.KEY_TITLE, 'My Story')
        story_text = document_generator.get_story_text_from_context(story_context)
        file_path = None
        mimetype = constants.MIMETYPE_TXT
        try:
            if file_format == constants.FORMAT_PDF:
                file_path = document_generator.generate_pdf(story_text, campaign_title)
                mimetype = constants.MIMETYPE_PDF
            elif file_format == constants.FORMAT_DOCX:
                file_path = document_generator.generate_docx(story_text, campaign_title)
                mimetype = constants.MIMETYPE_DOCX
            else:
                file_path = f"{campaign_title.replace(' ', '_')}.txt"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(story_text)
                mimetype = constants.MIMETYPE_TXT
            if not file_path:
                return jsonify({KEY_ERROR: 'Unsupported format'}), 400
            return send_file(file_path, as_attachment=True, mimetype=mimetype)
        except Exception as e:
            traceback.print_exc()
            return jsonify({KEY_ERROR: 'Failed to generate file', KEY_DETAILS: str(e)}), 500
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

    # --- Frontend Serving ---
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if not app.static_folder:
            # This should never happen in our configuration, but it satisfies the linter.
            return jsonify({KEY_ERROR: 'Static folder not configured'}), 500
        return send_from_directory(app.static_folder, 'index.html')

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    print(f"Development server running: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
