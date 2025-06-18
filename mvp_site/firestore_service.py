import datetime
from firebase_admin import firestore
from decorators import log_exceptions

# Define a safe maximum size for a text field in Firestore, just under the 1 MiB limit.
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
    """Retrieves a single campaign and its full story."""
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    
    campaign_doc = campaign_ref.get()
    if not campaign_doc.exists:
        return None, None

    story_ref = campaign_ref.collection('story').order_by('timestamp').order_by('part')
    story_docs = story_ref.stream()
    
    story = []
    for doc in story_docs:
        doc_data = doc.to_dict()
        doc_data['timestamp'] = doc_data['timestamp'].isoformat()
        story.append(doc_data)

    return campaign_doc.to_dict(), story

@log_exceptions
def add_story_entry(user_id, campaign_id, actor, text, mode=None):
    """
    Adds a new entry to a campaign's story. If the text is too large,
    it splits it into multiple documents (chunks). Refactored for DRYness.
    """
    db = get_db()
    story_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    
    text_bytes = text.encode('utf-8')
    
    # Prepare chunks. If text is small, this will be a list with one item.
    chunks = [text_bytes[i:i + MAX_TEXT_BYTES] for i in range(0, len(text_bytes), MAX_TEXT_BYTES)]
    
    # Create the base data dictionary that is common to all parts.
    base_entry_data = {'actor': actor}
    if mode:
        base_entry_data['mode'] = mode
        
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    
    # A single loop now handles both single and multi-part entries.
    for i, chunk in enumerate(chunks):
        # Create a copy to avoid modifying the base dictionary in the loop
        entry_data = base_entry_data.copy()
        
        # Add the data specific to this chunk
        entry_data['text'] = chunk.decode('utf-8')
        entry_data['timestamp'] = timestamp
        entry_data['part'] = i + 1
        
        # Add the new entry to the story sub-collection
        story_ref.collection('story').add(entry_data)
        
    # Update the last_played timestamp on the parent campaign document once.
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
