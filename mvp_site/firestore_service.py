import datetime
from firebase_admin import firestore
from decorators import log_exceptions # Import the decorator

# No need for a separate logger instance here anymore, the decorator handles it.

def get_db():
    """Returns the Firestore client."""
    return firestore.client()

@log_exceptions
def get_campaigns_for_user(user_id):
    """Retrieves all campaigns for a given user, ordered by most recently played."""
    db = get_db()
    campaigns_ref = db.collection('users').document(user_id).collection('campaigns')
    campaigns_query = campaigns_ref.order_by('last_played', direction=firestore.Query.DESCENDING)
    
    campaign_list = []
    for campaign in campaigns_query.stream():
        campaign_data = campaign.to_dict()
        campaign_data['id'] = campaign.id
        campaign_data['created_at'] = campaign_data['created_at'].isoformat()
        campaign_data['last_played'] = campaign_data['last_played'].isoformat()
        campaign_list.append(campaign_data)
    
    return campaign_list

@log_exceptions
def get_campaign_by_id(user_id, campaign_id):
    """Retrieves a single campaign and its full story."""
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    
    campaign_doc = campaign_ref.get()
    if not campaign_doc.exists:
        return None, None

    story_ref = campaign_ref.collection('story').order_by('timestamp', direction=firestore.Query.ASCENDING)
    story_docs = story_ref.stream()
    
    story = []
    for doc in story_docs:
        doc_data = doc.to_dict()
        doc_data['timestamp'] = doc_data['timestamp'].isoformat()
        story.append(doc_data)

    return campaign_doc.to_dict(), story

@log_exceptions
def add_story_entry(user_id, campaign_id, actor, text, mode=None):
    """Adds a new entry to a campaign's story and updates the last_played timestamp."""
    db = get_db()
    campaign_doc_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    story_ref = campaign_doc_ref.collection('story')
    
    entry_data = {
        'actor': actor,
        'text': text,
        'timestamp': datetime.datetime.now(datetime.timezone.utc)
    }
    if mode:
        entry_data['mode'] = mode
        
    story_ref.add(entry_data)
    campaign_doc_ref.update({'last_played': datetime.datetime.now(datetime.timezone.utc)})

@log_exceptions
def create_campaign(user_id, title, initial_prompt, opening_story):
    """Creates a new campaign document in Firestore."""
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document()
    
    campaign_data = {
        'title': title,
        'initial_prompt': initial_prompt,
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'last_played': datetime.datetime.now(datetime.timezone.utc)
    }
    campaign_ref.set(campaign_data)
    add_story_entry(user_id, campaign_ref.id, 'gemini', opening_story)
    return campaign_ref.id
