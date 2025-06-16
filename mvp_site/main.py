import os
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
import firebase_admin
from firebase_admin import auth

def create_app():
    app = Flask(__name__, static_folder='static')
    firebase_admin.initialize_app()
    app.logger.info("Firebase App initialized successfully.")

    import gemini_service
    import firestore_service

    def check_token(f):
        @wraps(f)
        def wrap(*args,**kwargs):
            if not request.headers.get('Authorization'):
                return {'message': 'No token provided'}, 401
            try:
                id_token = request.headers['Authorization'].split(' ').pop()
                decoded_token = auth.verify_id_token(id_token)
                kwargs['user_id'] = decoded_token['uid']
            except Exception as e:
                app.logger.error(f"Token verification failed: {e}")
                return {'message': 'Invalid token provided.'}, 401
            return f(*args, **kwargs)
        return wrap

    @app.route('/api/campaigns', methods=['GET'])
    @check_token
    def get_campaigns(user_id):
        campaigns = firestore_service.get_campaigns_for_user(user_id)
        return jsonify(campaigns)

    @app.route('/api/campaigns/<campaign_id>', methods=['GET'])
    @check_token
    def get_campaign(user_id, campaign_id):
        campaign, story = firestore_service.get_campaign_by_id(user_id, campaign_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        return jsonify({'campaign': campaign, 'story': story})

    @app.route('/api/campaigns', methods=['POST'])
    @check_token
    def create_campaign(user_id):
        data = request.get_json()
        prompt = data.get('prompt', 'A classic fantasy adventure.')
        title = data.get('title', 'My New Campaign')
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
        user_input = data.get('input')
        mode = data.get('mode', 'character')
        
        try:
            _, story_context = firestore_service.get_campaign_by_id(user_id, campaign_id)
            firestore_service.add_story_entry(user_id, campaign_id, 'user', user_input, mode)
            
            gemini_response = gemini_service.continue_story(user_input, mode, story_context)
            firestore_service.add_story_entry(user_id, campaign_id, 'gemini', gemini_response)
            
            return jsonify({'success': True, 'response': gemini_response})
        except Exception as e:
            app.logger.error(f"Error during interaction: {e}")
            return jsonify({'success': False, 'error': 'Interaction failed.'}), 500

    @app.route('/')
    def serve_index():
        return send_from_directory('static', 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory('static', path)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
