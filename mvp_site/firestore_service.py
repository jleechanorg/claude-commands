import datetime
from firebase_admin import firestore
from decorators import log_exceptions
from game_state import GameState

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
    Retrieves a single campaign and its full story using a robust, single query
    and in-memory sort to handle all data types.
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
        entry['timestamp'] = entry['timestamp'].isoformat()

    return campaign_doc.to_dict(), all_story_entries


@log_exceptions
def add_story_entry(user_id, campaign_id, actor, text, mode=None):
    db = get_db()
    story_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
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
        story_ref.collection('story').add(entry_data)
    story_ref.update({'last_played': timestamp})

@log_exceptions
def create_campaign(user_id, title, initial_prompt, opening_story, initial_game_state: GameState, selected_prompts=None):
    db = get_db()
    campaigns_collection = db.collection('users').document(user_id).collection('campaigns')
    
    # Create the main campaign document
    campaign_ref = campaigns_collection.document()
    campaign_data = {
        'title': title,
        'initial_prompt': initial_prompt,
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'last_played': datetime.datetime.now(datetime.timezone.utc),
        'selected_prompts': selected_prompts or []
    }
    campaign_ref.set(campaign_data)

    # Create the initial game state document
    game_state_ref = campaign_ref.collection('game_states').document('current_state')
    game_state_ref.set(initial_game_state.to_dict())

    # Assuming 'god' mode for the very first conceptual prompt.
    # You might want to make this mode configurable or infer it.
    add_story_entry(user_id, campaign_ref.id, 'user', initial_prompt, mode='god')
    add_story_entry(user_id, campaign_ref.id, 'gemini', opening_story)
    
    return campaign_ref.id

@log_exceptions
def get_campaign_game_state(user_id, campaign_id) -> GameState | None:
    """Fetches the current game state for a given campaign."""
    db = get_db()
    game_state_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id).collection('game_states').document('current_state')
    
    game_state_doc = game_state_ref.get()
    if not game_state_doc.exists:
        return None
    return GameState.from_dict(game_state_doc.to_dict())

@log_exceptions
def update_campaign_game_state(user_id, campaign_id, state_updates: dict):
    """Updates the game state using dot notation for nested fields."""
    db = get_db()
    game_state_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id).collection('game_states').document('current_state')
    
    # Add a timestamp to track the update
    state_updates_with_timestamp = state_updates.copy()
    state_updates_with_timestamp['last_state_update_timestamp'] = datetime.datetime.now(datetime.timezone.utc)
    
    game_state_ref.update(state_updates_with_timestamp)

# --- NEWLY ADDED FUNCTION ---
@log_exceptions
def update_campaign_title(user_id, campaign_id, new_title):
    """Updates the title of a specific campaign."""
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    campaign_ref.update({'title': new_title})
    return True
