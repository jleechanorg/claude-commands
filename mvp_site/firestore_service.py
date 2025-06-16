import datetime
from firebase_admin import firestore

db = firestore.client()

def create_campaign(user_id, title, initial_prompt, opening_story):
    """Creates a new campaign document in Firestore."""
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document()
    
    campaign_data = {
        'title': title,
        'initial_prompt': initial_prompt,
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'last_played': datetime.datetime.now(datetime.timezone.utc)
    }
    campaign_ref.set(campaign_data)

    # Add the first story entry (from Gemini)
    story_entry = {
        'actor': 'gemini',
        'text': opening_story,
        'timestamp': datetime.datetime.now(datetime.timezone.utc)
    }
    campaign_ref.collection('story').add(story_entry)
    
    return campaign_ref.id
