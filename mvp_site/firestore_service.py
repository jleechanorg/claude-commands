import datetime
from firebase_admin import firestore
from decorators import log_exceptions

MAX_TEXT_BYTES = 1000000

def get_db():
    """[Summary of what get_db does]

    [More detailed explanation if needed]

    Returns:
        [return_type]: Description of the return value.
    """
    return firestore.client()

@log_exceptions
def get_campaigns_for_user(user_id):
    """[Summary of what get_campaigns_for_user does]

    [More detailed explanation if needed]

    Args:
        user_id (str): Description of user_id.

    Returns:
        list: Description of the return value.
    """
    db = get_db()
    campaigns_ref = db.collection('users').document(user_id).collection('campaigns')
    campaigns_query = campaigns_ref.order_by('last_played', direction=firestore.Query.DESCENDING)
    
    campaign_list = []
    for campaign in campaigns_query.stream():
        campaign_data = campaign.to_dict()
        campaign_data['id'] = campaign.id
        campaign_data['created_at'] = campaign_data['created_at'].isoformat() # Original line
        campaign_data['last_played'] = campaign_data['last_played'].isoformat() # Original line
        campaign_list.append(campaign_data)
    
    return campaign_list

@log_exceptions
def get_campaign_by_id(user_id, campaign_id):
    """[Summary of what get_campaign_by_id does]

    [More detailed explanation if needed]

    Args:
        user_id (str): Description of user_id.
        campaign_id (str): Description of campaign_id.

    Returns:
        tuple: Description of the return value (e.g., (dict or None, list or None)).
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    
    campaign_doc = campaign_ref.get()
    if not campaign_doc.exists:
        return None, None

    # --- SIMPLIFIED FETCH LOGIC ---
    # 1. Fetch ALL documents, ordered only by the field that always exists: timestamp.
    story_ref = campaign_ref.collection('story').order_by('timestamp')
    story_docs = story_ref.stream()

    # 2. Convert to a list of dictionaries
    all_story_entries = [doc.to_dict() for doc in story_docs]

    # 3. Sort the list in Python, which is more powerful than a Firestore query.
    # We sort by timestamp first, and then by the 'part' number.
    # If 'part' is missing (for old docs), we treat it as 1.
    all_story_entries.sort(key=lambda x: (x['timestamp'], x.get('part', 1)))

    # 4. Convert timestamps to ISO format for JSON serialization AFTER sorting.
    for entry in all_story_entries:
        entry['timestamp'] = entry['timestamp'].isoformat() # Original line

    return campaign_doc.to_dict(), all_story_entries


@log_exceptions
def add_story_entry(user_id, campaign_id, actor, text, mode=None):
    """[Summary of what add_story_entry does]

    [More detailed explanation if needed]

    Args:
        user_id (str): Description of user_id.
        campaign_id (str): Description of campaign_id.
        actor (str): Description of actor.
        text (str): Description of text.
        mode (str, optional): Description of mode. Defaults to None.
    """
    db = get_db()
    story_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id) # Original line
    text_bytes = text.encode('utf-8')
    chunks = [text_bytes[i:i + MAX_TEXT_BYTES] for i in range(0, len(text_bytes), MAX_TEXT_BYTES)]
    base_entry_data = {'actor': actor}
    if mode: base_entry_data['mode'] = mode
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    for i, chunk in enumerate(chunks):
        entry_data = base_entry_data.copy()
        entry_data['text'] = chunk.decode('utf-8')
        entry_data['timestamp'] = timestamp
        entry_data['part'] = i + 1
        story_ref.collection('story').add(entry_data) # Original line
    story_ref.update({'last_played': timestamp}) # Original line

@log_exceptions
def create_campaign(user_id, title, initial_prompt, opening_story, selected_prompts=None):
    """[Summary of what create_campaign does]

    [More detailed explanation if needed]

    Args:
        user_id (str): Description of user_id.
        title (str): Description of title.
        initial_prompt (str): Description of initial_prompt.
        opening_story (str): Description of opening_story.
        selected_prompts (list, optional): Description of selected_prompts. Defaults to None.

    Returns:
        str: Description of the return value (e.g., ID of the new campaign).
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document()
    campaign_data = {
        'title': title,
        'initial_prompt': initial_prompt,
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'last_played': datetime.datetime.now(datetime.timezone.utc),
        'selected_prompts': selected_prompts or [] # Original line
    }
    campaign_ref.set(campaign_data)
    add_story_entry(user_id, campaign_ref.id, 'gemini', opening_story) # Original line
    return campaign_ref.id

# --- NEWLY ADDED FUNCTION --- (This function was in the snapshot you provided as "NEWLY ADDED")
@log_exceptions
def update_campaign_title(user_id, campaign_id, new_title):
    """[Summary of what update_campaign_title does]

    [More detailed explanation if needed]

    Args:
        user_id (str): Description of user_id.
        campaign_id (str): Description of campaign_id.
        new_title (str): Description of new_title.

    Returns:
        bool: Description of the return value.
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    campaign_ref.update({'title': new_title})
    return True # Original line
