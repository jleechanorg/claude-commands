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
        
        # Create a blank initial game state. It will be populated by the LLM.
        initial_game_state = GameState(
            player_character_data={},
            world_data={},
            npc_data={},
            custom_campaign_state={}
        )

        should_include_srd = 'mechanics' in selected_prompts
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
        
        # Fetch campaign metadata and story context
        campaign, story_context = firestore_service.get_campaign_by_id(user_id, campaign_id)
        if not campaign: return jsonify({KEY_ERROR: 'Campaign not found'}), 404
        
        # --- NEW STATE MANAGEMENT WORKFLOW ---
        # 1. Read current game state
        current_game_state = firestore_service.get_campaign_game_state(user_id, campaign_id)
        if not current_game_state:
            # If no game state exists at all, create a fresh one.
            # The migration logic below will handle checking for legacy data.
            current_game_state = GameState(player_character_data={}, world_data={}, npc_data={}, custom_campaign_state={})

        # --- ONE-TIME LEGACY MIGRATION ---
        logging.info(f"Evaluating campaign {campaign_id} for legacy migration. Current status: {current_game_state.migration_status.value}")
        if current_game_state.migration_status == MigrationStatus.NOT_CHECKED:
            logging.info(f"-> Status is NOT_CHECKED. Performing scan.")
            # The story context here still has datetime objects, which is fine for the parser.
            if story_context:
                legacy_state = gemini_service.create_game_state_from_legacy_story(story_context)
            else:
                legacy_state = None
            
            if legacy_state:
                logging.info(f"-> SUCCESS: Found and parsed legacy state for campaign {campaign_id}. Migrating.")
                legacy_state.migration_status = MigrationStatus.MIGRATED
                # Overwrite the current_game_state variable with the migrated one
                current_game_state = legacy_state
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
        if proposed_changes:
            logging.info(f"Applying state changes for campaign {campaign_id}: {proposed_changes}")
            firestore_service.update_campaign_game_state(user_id, campaign_id, proposed_changes)
            
        return jsonify({KEY_SUCCESS: True, KEY_RESPONSE: gemini_response})

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
