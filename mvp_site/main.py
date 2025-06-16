import os
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
import firebase_admin
from firebase_admin import auth, credentials

import gemini_service
import firestore_service

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Initialize Firebase Admin SDK
# No credentials needed when running on Cloud Run, it uses the service account
firebase_admin.initialize_app()

# Decorator to protect routes with Firebase Auth
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

# --- API Routes ---
@app.route('/api/campaigns', methods=['POST'])
@check_token
def create_campaign(user_id):
    data = request.get_json()
    prompt = data.get('prompt', 'A classic fantasy adventure.')
    title = data.get('title', 'My New Campaign')

    try:
        # 1. Get the opening story from Gemini
        opening_story = gemini_service.get_initial_story(prompt)

        # 2. Create the campaign in Firestore
        campaign_id = firestore_service.create_campaign(user_id, title, prompt, opening_story)
        
        return jsonify({'success': True, 'campaign_id': campaign_id, 'opening_story': opening_story}), 201
    except Exception as e:
        app.logger.error(f"Error creating campaign: {e}")
        return jsonify({'success': False, 'error': 'Could not create campaign.'}), 500

# --- Static file serving ---
@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
