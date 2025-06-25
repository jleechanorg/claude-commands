import collections.abc
import datetime
import json
import logging

from decorators import log_exceptions
from firebase_admin import firestore
from game_state import GameState

MAX_TEXT_BYTES = 1000000
MAX_LOG_LINES = 20

def _truncate_log_json(data, max_lines=MAX_LOG_LINES):
    """Truncate JSON logs to max_lines to prevent log spam."""
    try:
        json_str = json.dumps(data, indent=2, default=str)
        lines = json_str.split('\n')
        if len(lines) <= max_lines:
            return json_str
        
        # Truncate and add indicator
        truncated_lines = lines[:max_lines-1] + [f"... (truncated, showing {max_lines-1}/{len(lines)} lines)"]
        return '\n'.join(truncated_lines)
    except Exception:
        # Fallback to string representation if JSON fails
        return str(data)[:500] + "..." if len(str(data)) > 500 else str(data)

def _perform_append(target_list: list, items_to_append, key_name: str, deduplicate: bool = False):
    """
    Safely appends one or more items to a target list, with an option to prevent duplicates.
    This function modifies the target_list in place.
    """
    if not isinstance(items_to_append, list):
        items_to_append = [items_to_append]  # Standardize to list

    newly_added_items = []
    for item in items_to_append:
        # If deduplication is on, skip items already in the list
        if deduplicate and item in target_list:
            continue
        target_list.append(item)
        newly_added_items.append(item)

    if newly_added_items:
        logging.info(f"APPEND/SAFEGUARD: Added {len(newly_added_items)} new items to '{key_name}'.")
    else:
        logging.info(f"APPEND/SAFEGUARD: No new items were added to '{key_name}' (duplicates may have been found).")


def _initialize_missions_list(state_to_update: dict, key: str) -> None:
    """Initialize active_missions as empty list if it doesn't exist or is wrong type."""
    if key not in state_to_update or not isinstance(state_to_update.get(key), list):
        state_to_update[key] = []


def _find_existing_mission_index(missions_list: list, mission_id: str) -> int:
    """Find the index of an existing mission by mission_id. Returns -1 if not found."""
    for i, existing_mission in enumerate(missions_list):
        if isinstance(existing_mission, dict) and existing_mission.get('mission_id') == mission_id:
            return i
    return -1


def _process_mission_data(state_to_update: dict, key: str, mission_id: str, mission_data: dict) -> None:
    """Process a single mission, either updating existing or adding new."""
    # Ensure the mission has an ID
    if 'mission_id' not in mission_data:
        mission_data['mission_id'] = mission_id
    
    # Check if this mission already exists (by mission_id)
    existing_mission_index = _find_existing_mission_index(state_to_update[key], mission_id)
    
    if existing_mission_index != -1:
        # Update existing mission
        logging.info(f"Updating existing mission: {mission_id}")
        state_to_update[key][existing_mission_index].update(mission_data)
    else:
        # Add new mission
        logging.info(f"Adding new mission: {mission_id}")
        state_to_update[key].append(mission_data)


def _handle_missions_dict_conversion(state_to_update: dict, key: str, missions_dict: dict) -> None:
    """Convert dictionary format missions to list append format."""
    for mission_id, mission_data in missions_dict.items():
        if isinstance(mission_data, dict):
            _process_mission_data(state_to_update, key, mission_id, mission_data)
        else:
            logging.warning(f"Skipping invalid mission data for {mission_id}: not a dictionary")


def _handle_active_missions_conversion(state_to_update: dict, key: str, value) -> None:
    """Handle smart conversion of active_missions from various formats to list."""
    logging.warning(f"SMART CONVERSION: AI attempted to set 'active_missions' as {type(value).__name__}. Converting to list append.")
    
    # Initialize active_missions as empty list if it doesn't exist
    _initialize_missions_list(state_to_update, key)
    
    # Convert based on value type
    if isinstance(value, dict):
        # AI is providing missions as a dict like {"main_quest_1": {...}, "side_quest_1": {...}}
        _handle_missions_dict_conversion(state_to_update, key, value)
    else:
        # For other non-list types, log error and skip
        logging.error(f"Cannot convert {type(value).__name__} to mission list. Skipping.")


def update_state_with_changes(state_to_update: dict, changes: dict) -> dict:
    """
    Recursively updates a state dictionary with a changes dictionary.
    - Handles explicit appends via {'append': ...} syntax.
    - Safeguards 'core_memories' from being overwritten, converting attempts into a safe append.
    - Merges nested dictionaries recursively.
    - Overwrites all other values.
    """
    logging.info(f"--- update_state_with_changes: applying changes:\\n{_truncate_log_json(changes)}")
    
    for key, value in changes.items():

        # Case 1: Explicit append syntax {'append': ...}
        if isinstance(value, dict) and 'append' in value:
            logging.info(f"update_state: Detected explicit append for '{key}'.")
            if key not in state_to_update or not isinstance(state_to_update.get(key), list):
                state_to_update[key] = []
            _perform_append(state_to_update[key], value['append'], key, deduplicate=(key == 'core_memories'))
        
        # Case 2: Smart safeguard for direct 'core_memories' overwrite
        elif key == 'core_memories':
            logging.warning("CRITICAL SAFEGUARD: Intercepted direct overwrite on 'core_memories'. Converting to safe, deduplicated append.")
            if key not in state_to_update or not isinstance(state_to_update.get(key), list):
                state_to_update[key] = []
            # The helper function is designed to handle non-lists, so we call it directly.
            _perform_append(state_to_update[key], value, key, deduplicate=True)

        # NEW Case 2b: Smart safeguard for 'active_missions' list
        elif key == 'active_missions' and not isinstance(value, list):
            _handle_active_missions_conversion(state_to_update, key, value)
            continue  # Skip normal processing since we handled it

        # Case 3: Recursive merge for nested dictionaries
        elif isinstance(value, dict) and isinstance(state_to_update.get(key), collections.abc.Mapping):
            state_to_update[key] = update_state_with_changes(state_to_update.get(key, {}), value)
        
        # Case 3b: Create new dictionary when incoming value is dict but existing is not
        elif isinstance(value, dict):
            state_to_update[key] = update_state_with_changes({}, value)

        # Case 4: Handle string updates to existing dictionaries (preserve dict structure)
        elif isinstance(state_to_update.get(key), collections.abc.Mapping):
            # Special case: __DELETE__ token should delete the key, not update status
            if value == "__DELETE__":
                logging.info(f"update_state: Deleting key '{key}' due to __DELETE__ token.")
                del state_to_update[key]
            else:
                logging.info(f"update_state: Preserving dict structure for key '{key}', adding 'status' field.")
                # Don't overwrite the entire dictionary with a string
                # Instead, treat string values as status updates
                existing_dict = state_to_update[key].copy()
                existing_dict['status'] = value
                state_to_update[key] = existing_dict

        # Case 5: Simple overwrite for everything else
        else:
            state_to_update[key] = value
            
    logging.info("--- update_state_with_changes: finished ---")
    return state_to_update

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

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    if type(obj).__name__ == 'Sentinel':
        return '<SERVER_TIMESTAMP>'
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def json_default_serializer(o):
    """Handles serialization of data types json doesn't know, like datetimes."""
    if isinstance(o, (datetime.datetime, datetime.date)):
        return o.isoformat()
    # Check for Firestore's special DELETE_FIELD sentinel.
    if o == firestore.DELETE_FIELD:
        return None  # Or another appropriate serializable value
    if o == firestore.SERVER_TIMESTAMP:
        return "<SERVER_TIMESTAMP>"
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

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
        
        # Safely get and format timestamps
        created_at = campaign_data.get('created_at')
        if created_at:
            campaign_data['created_at'] = created_at.isoformat()
            
        last_played = campaign_data.get('last_played')
        if last_played:
            campaign_data['last_played'] = last_played.isoformat()
            
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
def update_campaign_game_state(user_id, campaign_id, game_state_update: dict):
    """Updates the game state for a campaign, overwriting with the provided dict."""
    if not user_id or not campaign_id:
        raise ValueError("User ID and Campaign ID are required.")

    db = get_db()
    game_state_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id).collection('game_states').document('current_state')

    try:
        # NOTE: This function now expects a COMPLETE game state dictionary.
        # The merge logic has been moved to the handle_interaction function in main.py
        # to ensure consistency across all update types (AI, GOD_MODE, etc.)
        
        # Add the last updated timestamp before setting.
        game_state_update['last_state_update_timestamp'] = firestore.SERVER_TIMESTAMP
        
        game_state_ref.set(game_state_update) 
        logging.info(f"Successfully set new game state for campaign {campaign_id}.")
        # The log below is for the final state being written.
        logging.info(f"Final state written to Firestore for campaign {campaign_id}:\\n{_truncate_log_json(game_state_update)}")

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
