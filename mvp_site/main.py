import os
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
import firebase_admin
from firebase_admin import auth

def create_app():
    # Correctly set the static folder path relative to the app's root
    app = Flask(__name__, static_folder='static', static_url_path='')
    
    firebase_admin.initialize_app()
    app.logger.info("Firebase App initialized successfully.")

    import gemini_service
    import firestore_service

    def check_token(f):
        @wraps(f)
        def wrap(*args,**kwargs):
            if not request.headers.get('Authorization'): return {'message': 'No token provided'}, 401
            try:
                id_token = request.headers['Authorization'].split(' ').pop()
                decoded_token = auth.verify_id_token(id_token)
                kwargs['user_id'] = decoded_token['uid']
            except Exception as e:
                app.logger.error(f"Token verification failed: {e}")
                return {'message': 'Invalid token provided.'}, 401
            return f(*args, **kwargs)
        return wrap

    # --- API Routes (all prefixed with /api/) ---
    @app.route('/api/campaigns', methods=['GET'])
    @check_token
    def get_campaigns(user_id):
        return jsonify(firestore_service.get_campaigns_for_user(user_id))

    @app.route('/api/campaigns/<campaign_id>', methods=['GET'])
    @check_token
    def get_campaign(user_id, campaign_id):
        campaign, story = firestore_service.get_campaign_by_id(user_id, campaign_id)
        if not campaign: return jsonify({'error': 'Campaign not found'}), 404
        return jsonify({'campaign': campaign, 'story': story})

    @app.route('/api/campaigns', methods=['POST'])
    @check_token
    def create_campaign(user_id):
        data = request.get_json()
        prompt, title = data.get('prompt'), data.get('title')
        try:
            opening_story = gemini_service.get_initial_story(prompt)
            campaign_id = firestore_service.create_campaign(user_id, title, prompt, opening_story)
            return jsonify({'success': True, 'campaign_id': campaign_id}), 201
        except Exception as e:
            app.logger.error(f"Error creating campaign: {e}")
            return jsonify({'success': False, 'error': 'Could not create campaign.'}), 500

    @app.route('/api/campaigns/<campaign_id>/interaction', methods=['POST'])
    @check_token
    def handle_interaction(user_id, campaign_id):
        data = request.get_json()
        user_input, mode = data.get('input'), data.get('mode', 'character')
        try:
            _, story_context = firestore_service.get_campaign_by_id(user_id, campaign_id)
            firestore_service.add_story_entry(user_id, campaign_id, 'user', user_input, mode)
            gemini_response = gemini_service.continue_story(user_input, mode, story_context)
            firestore_service.add_story_entry(user_id, campaign_id, 'gemini', gemini_response)
            return jsonify({'success': True, 'response': gemini_response})
        except Exception as e:
            app.logger.error(f"Error during interaction: {e}")
            return jsonify({'success': False, 'error': 'Interaction failed.'}), 500

    # --- Frontend Route Catch-all ---
    # This route will match anything not matched by the static file handler or API routes.
    # It ensures that deep-linked frontend routes like /game/some-id serve the main app.
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        return send_from_directory(app.static_folder, 'index.html')

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
