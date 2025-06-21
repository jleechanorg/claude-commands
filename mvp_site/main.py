import os
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth
import traceback
import document_generator
import logging
from game_state import GameState

def create_app():
    app = Flask(__name__, static_folder='static')
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    if not firebase_admin._apps:
        firebase_admin.initialize_app()

    import gemini_service
    import firestore_service

    def check_token(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if app.config.get('TESTING') and request.headers.get('X-Test-Bypass-Auth') == 'true':
                kwargs['user_id'] = request.headers.get('X-Test-User-ID', 'test-user')
                return f(*args, **kwargs)
            if not request.headers.get('Authorization'): return jsonify({'message': 'No token provided'}), 401
            try:
                id_token = request.headers['Authorization'].split(' ').pop()
                decoded_token = auth.verify_id_token(id_token)
                kwargs['user_id'] = decoded_token['uid']
            except Exception as e:
                return jsonify({'success': False, 'error': f"Auth failed: {e}", 'traceback': traceback.format_exc()}), 401
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
            return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500
        # --- END RESTORED BLOCK ---

    @app.route('/api/campaigns/<campaign_id>', methods=['GET'])
    @check_token
    def get_campaign(user_id, campaign_id):
        # --- RESTORED TRY-EXCEPT BLOCK ---
        try:
            campaign, story = firestore_service.get_campaign_by_id(user_id, campaign_id)
            if not campaign: return jsonify({'error': 'Campaign not found'}), 404
            return jsonify({'campaign': campaign, 'story': story})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500
        # --- END RESTORED BLOCK ---

    @app.route('/api/campaigns', methods=['POST'])
    @check_token
    def create_campaign_route(user_id):
        data = request.get_json()
        prompt, title = data.get('prompt'), data.get('title')
        selected_prompts = data.get('selected_prompts', [])
        
        # Create a blank initial game state. It will be populated by the LLM.
        initial_game_state = GameState(
            player_character_data={},
            world_data={},
            npc_data={},
            custom_campaign_state={}
        )

        opening_story = gemini_service.get_initial_story(prompt, selected_prompts=selected_prompts)
        
        campaign_id = firestore_service.create_campaign(
            user_id, title, prompt, opening_story, initial_game_state, selected_prompts
        )
        return jsonify({'success': True, 'campaign_id': campaign_id}), 201
        
    @app.route('/api/campaigns/<campaign_id>', methods=['PATCH'])
    @check_token
    def update_campaign(user_id, campaign_id):
        data = request.get_json()
        new_title = data.get('title')
        if not new_title:
            return jsonify({'error': 'New title is required'}), 400
        
        try:
            firestore_service.update_campaign_title(user_id, campaign_id, new_title)
            return jsonify({'success': True, 'message': 'Campaign title updated successfully.'})
        except Exception as e:
            traceback.print_exc()
            return jsonify({'error': 'Failed to update campaign', 'details': str(e)}), 500

    @app.route('/api/campaigns/<campaign_id>/interaction', methods=['POST'])
    @check_token
    def handle_interaction(user_id, campaign_id):
        data = request.get_json()
        user_input, mode = data.get('input'), data.get('mode', 'character')
        
        # Fetch campaign metadata and story context
        campaign, story_context = firestore_service.get_campaign_by_id(user_id, campaign_id)
        if not campaign: return jsonify({'error': 'Campaign not found'}), 404
        
        # --- NEW STATE MANAGEMENT WORKFLOW ---
        # 1. Read current game state
        current_game_state = firestore_service.get_campaign_game_state(user_id, campaign_id)
        if not current_game_state:
            # Handle case where state might not exist for some reason (e.g., older campaigns)
            # For V1, we can log a warning and proceed with a default empty state object.
            logging.warning(f"Game state not found for campaign {campaign_id}. Proceeding with new, empty state object.")
            current_game_state = GameState(player_character_data={}, world_data={}, npc_data={}, custom_campaign_state={})

        # 2. Add user's action to the story log
        firestore_service.add_story_entry(user_id, campaign_id, 'user', user_input, mode)
        
        # 3. Process: Get AI response, passing in the current state
        selected_prompts = campaign.get('selected_prompts', [])
        gemini_response = gemini_service.continue_story(user_input, mode, story_context, current_game_state, selected_prompts)
        
        # 4. Write: Add AI response to story log and update state
        firestore_service.add_story_entry(user_id, campaign_id, 'gemini', gemini_response)

        # 5. Parse and apply state changes from AI response
        proposed_changes = gemini_service.parse_llm_response_for_state_changes(gemini_response)
        if proposed_changes:
            logging.info(f"Applying state changes for campaign {campaign_id}: {proposed_changes}")
            firestore_service.update_campaign_game_state(user_id, campaign_id, proposed_changes)
            
        return jsonify({'success': True, 'response': gemini_response})

    @app.route('/api/campaigns/<campaign_id>/export', methods=['GET'])
    @check_token
    def export_campaign(user_id, campaign_id):
        file_format = request.args.get('format', 'txt').lower()
        campaign, story_context = firestore_service.get_campaign_by_id(user_id, campaign_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        campaign_title = campaign.get('title', 'My Story')
        story_text = document_generator.get_story_text_from_context(story_context)
        file_path = None
        mimetype = 'text/plain'
        try:
            if file_format == 'pdf':
                file_path = document_generator.generate_pdf(story_text, campaign_title)
                mimetype = 'application/pdf'
            elif file_format == 'docx':
                file_path = document_generator.generate_docx(story_text, campaign_title)
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                file_path = f"{campaign_title.replace(' ', '_')}.txt"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(story_text)
                mimetype = 'text/plain'
            if not file_path:
                return jsonify({'error': 'Unsupported format'}), 400
            return send_file(file_path, as_attachment=True, mimetype=mimetype)
        except Exception as e:
            traceback.print_exc()
            return jsonify({'error': 'Failed to generate file', 'details': str(e)}), 500
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

    # --- Frontend Serving ---
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        return send_from_directory(app.static_folder, 'index.html')

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    print(f"Development server running: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
