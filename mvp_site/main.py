import os
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth
import traceback

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    if not firebase_admin._apps:
        firebase_admin.initialize_app()

    import gemini_service
    import firestore_service

    def check_token(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            # --- THIS IS THE NEW BYPASS LOGIC ---
            if app.config['TESTING'] and request.headers.get('X-Test-Bypass-Auth') == 'true':
                kwargs['user_id'] = request.headers.get('X-Test-User-ID', 'test-user') # Use a provided test user ID
                return f(*args, **kwargs)
            # --- END OF NEW LOGIC ---

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
        try:
            return jsonify(firestore_service.get_campaigns_for_user(user_id))
        except Exception as e:
            return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500

    @app.route('/api/campaigns/<campaign_id>', methods=['GET'])
    @check_token
    def get_campaign(user_id, campaign_id):
        try:
            campaign, story = firestore_service.get_campaign_by_id(user_id, campaign_id)
            if not campaign: return jsonify({'error': 'Campaign not found'}), 404
            return jsonify({'campaign': campaign, 'story': story})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500

    @app.route('/api/campaigns', methods=['POST'])
    @check_token
    def create_campaign(user_id):
        try:
            data = request.get_json()
            prompt, title = data.get('prompt'), data.get('title')
            opening_story = gemini_service.get_initial_story(prompt)
            campaign_id = firestore_service.create_campaign(user_id, title, prompt, opening_story)
            return jsonify({'success': True, 'campaign_id': campaign_id}), 201
        except Exception as e:
            return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500

    @app.route('/api/campaigns/<campaign_id>/interaction', methods=['POST'])
    @check_token
    def handle_interaction(user_id, campaign_id):
        try:
            data = request.get_json()
            user_input, mode = data.get('input'), data.get('mode', 'character')
            _, story_context = firestore_service.get_campaign_by_id(user_id, campaign_id)
            firestore_service.add_story_entry(user_id, campaign_id, 'user', user_input, mode)
            gemini_response = gemini_service.continue_story(user_input, mode, story_context)
            firestore_service.add_story_entry(user_id, campaign_id, 'gemini', gemini_response)
            return jsonify({'success': True, 'response': gemini_response})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500

    # --- Frontend Serving ---
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        return send_from_directory(app.static_folder, 'index.html')

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
