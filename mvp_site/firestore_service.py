import collections.abc
import datetime
import json
import logging

from decorators import log_exceptions
from firebase_admin import firestore
from game_state import GameState

MAX_TEXT_BYTES = 1000000

def deep_merge(d, u):
    """
    Recursively merges dictionary `u` into dictionary `d`.
    If a key in `u` is a dictionary, it recursively merges.
    Otherwise, the value from `u` overwrites the value in `d`.
    """
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_merge(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def _expand_dot_notation(d: dict) -> dict:
    """
    Expands a dictionary with dot-notation keys into a nested dictionary.
    Example: {'a.b': 1, 'c': 2} -> {'a': {'b': 1}, 'c': 2}
    """
    expanded_dict = {}
    for k, v in d.items():
        if '.' in k:
            keys = k.split('.')
            d_ref = expanded_dict
            for part in keys[:-1]:
                d_ref = d_ref.setdefault(part, {})
            d_ref[keys[-1]] = v
        else:
            expanded_dict[k] = v
    return expanded_dict

def get_db():
    """Returns the Firestore client."""
    return firestore.client()

@log_exceptions
def get_campaigns_for_user(user_id):
    """Retrieves all campaigns for a given user, ordered by most recently played."""
    db = get_db()
    campaigns_ref = db.collection('users').document(user_id).collection('campaigns')
    campaigns_query = campaigns_ref.order_by('last_played', direction='DESCENDING')
    
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

    # 4. Add a sequence ID and convert timestamps AFTER sorting.
    for i, entry in enumerate(all_story_entries):
        entry['sequence_id'] = i + 1
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
def create_campaign(user_id, title, initial_prompt, opening_story, initial_game_state: dict, selected_prompts=None):
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
    game_state_ref.set(initial_game_state)

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
    """Updates the game state for a campaign using a deep merge."""
    if not user_id or not campaign_id:
        raise ValueError("User ID and Campaign ID are required.")

    db = get_db()
    game_state_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)

    try:
        # Perform a full read-modify-write to ensure deep merge
        current_game_state_doc = game_state_ref.get()
        if current_game_state_doc.exists:
            current_state = current_game_state_doc.to_dict()
            
            # First, expand any dot-notation keys into a nested structure.
            # Then, deep merge the expanded updates into the current state.
            expanded_updates = _expand_dot_notation(state_updates)
            merged_state = deep_merge(current_state, expanded_updates)

            # Add the last updated timestamp
            merged_state['last_state_update_timestamp'] = firestore.SERVER_TIMESTAMP
            
            game_state_ref.set(merged_state) # Use set to overwrite with the fully merged state
            logging.info(f"Successfully deep-merged and updated game state for campaign {campaign_id}.")
            logging.info(f"New complete game state for campaign {campaign_id}:\\n{json.dumps(merged_state, indent=2)}")

        else:
            # If the document doesn't exist, create it with the updates.
            logging.warning(f"Game state for campaign {campaign_id} not found. Creating new document.")
            state_updates['last_state_update_timestamp'] = firestore.SERVER_TIMESTAMP
            game_state_ref.set(state_updates)

    except Exception as e:
        logging.error(f"Failed to update game state for campaign {campaign_id}: {e}", exc_info=True)
        raise

# --- NEWLY ADDED FUNCTION ---
@log_exceptions
def update_campaign_title(user_id, campaign_id, new_title):
    """Updates the title of a specific campaign."""
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    campaign_ref.update({'title': new_title})
    return True
