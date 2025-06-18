import datetime
from firebase_admin import firestore
from decorators import log_exceptions

MAX_TEXT_BYTES = 1000000

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
    """
    Retrieves a single campaign and its full story, gracefully handling both
    old documents (without a 'part' field) and new ones (with a 'part' field).
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    
    campaign_doc = campaign_ref.get()
    if not campaign_doc.exists:
        return None, None

    story_ref = campaign_ref.collection('story')

    # --- NEW RESILIENT FETCH LOGIC ---
    # Query 1: Fetch new-style documents that have the 'part' field.
    # The composite index on (timestamp, part) will be used here.
    new_data_query = story_ref.order_by('timestamp').order_by('part')
    new_docs = new_data_query.stream()

    # Query 2: Fetch old-style documents that are missing the 'part' field.
    # Firestore allows using '!=' or '==' with None to check for field existence.
    # This query uses the automatic index on 'timestamp'.
    old_data_query = story_ref.where('part', '==', None).order_by('timestamp')
    old_docs = old_data_query.stream()

    # Combine the results from both queries
    all_story_entries = []
    for doc in new_docs:
        doc_data = doc.to_dict()
        doc_data['timestamp'] = doc_data['timestamp'] # Keep as datetime object for sorting
        all_story_entries.append(doc_data)
        
    for doc in old_docs:
        doc_data = doc.to_dict()
        doc_data['timestamp'] = doc_data['timestamp']
        all_story_entries.append(doc_data)

    # Sort the combined list in memory to ensure perfect chronological order
    # This is necessary because we made two separate queries.
    all_story_entries.sort(key=lambda x: x['timestamp'])

    # Convert timestamps to ISO format for JSON serialization AFTER sorting is complete
    for entry in all_story_entries:
        entry['timestamp'] = entry['timestamp'].isoformat()

    return campaign_doc.to_dict(), all_story_entries


@log_exceptions
def add_story_entry(user_id, campaign_id, actor, text, mode=None):
    """
    Adds a new entry to a campaign's story. If the text is too large,
    it splits it into multiple documents (chunks).
    """
    db = get_db()
    story_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    
    text_bytes = text.encode('utf-8')
    chunks = [text_bytes[i:i + MAX_TEXT_BYTES] for i in range(0, len(text_bytes), MAX_TEXT_BYTES)]
    
    base_entry_data = {'actor': actor}
    if mode:
        base_entry_data['mode'] = mode
        
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    
    for i, chunk in enumerate(chunks):
        entry_data = base_entry_data.copy()
        entry_data['text'] = chunk.decode('utf-8')
        entry_data['timestamp'] = timestamp
        entry_data['part'] = i + 1
        story_ref.collection('story').add(entry_data)
        
    story_ref.update({'last_played': timestamp})

@log_exceptions
def create_campaign(user_id, title, initial_prompt, opening_story, selected_prompts=None):
    """Creates a new campaign document in Firestore."""
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document()
    
    campaign_data = {
        'title': title,
        'initial_prompt': initial_prompt,
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'last_played': datetime.datetime.now(datetime.timezone.utc),
        'selected_prompts': selected_prompts if selected_prompts is not None else []
    }
    campaign_ref.set(campaign_data)
    add_story_entry(user_id, campaign_ref.id, 'gemini', opening_story)
    return campaign_ref.id
