"""
Firestore Service - Database Operations and Game State Management

This module provides comprehensive database operations for WorldArchitect.AI,
including campaign management, game state synchronization, and robust data handling.

Key Responsibilities:
- Campaign CRUD operations (Create, Read, Update, Delete)
- Game state serialization and persistence
- Complex state update processing with merge logic
- Mission management and data conversion
- Defensive programming patterns for data integrity
- JSON serialization utilities for Firestore compatibility

Architecture:
- Uses Firebase Firestore for data persistence
- Implements robust state update mechanisms
- Provides mission handling with smart conversion
- Includes comprehensive error handling and logging
- Supports legacy data cleanup and migration

Dependencies:
- Firebase Admin SDK for Firestore operations
- Custom GameState class for state management
- NumericFieldConverter for data type handling
- Logging utilities for comprehensive debugging
"""

import collections.abc
import datetime
import json
import logging_util

from decorators import log_exceptions
from firebase_admin import firestore
from game_state import GameState
# Import numeric field converter
# This handles both package imports (relative) and direct script execution
try:
    from .numeric_field_converter import NumericFieldConverter
except ImportError:
    from numeric_field_converter import NumericFieldConverter

MAX_TEXT_BYTES = 1000000
MAX_LOG_LINES = 20
DELETE_TOKEN = "__DELETE__"  # Token used to mark fields for deletion in state updates

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
        logging_util.info(f"APPEND/SAFEGUARD: Added {len(newly_added_items)} new items to '{key_name}'.")
    else:
        logging_util.info(f"APPEND/SAFEGUARD: No new items were added to '{key_name}' (duplicates may have been found).")


class MissionHandler:
    """
    Handles mission-related operations for game state management.
    Consolidates mission processing, conversion, and updates.
    """
    
    @staticmethod
    def initialize_missions_list(state_to_update: dict, key: str) -> None:
        """Initialize active_missions as empty list if it doesn't exist or is wrong type."""
        if key not in state_to_update or not isinstance(state_to_update.get(key), list):
            state_to_update[key] = []
    
    @staticmethod
    def find_existing_mission_index(missions_list: list, mission_id: str) -> int:
        """Find the index of an existing mission by mission_id. Returns -1 if not found."""
        for i, existing_mission in enumerate(missions_list):
            if isinstance(existing_mission, dict) and existing_mission.get('mission_id') == mission_id:
                return i
        return -1
    
    @staticmethod
    def process_mission_data(state_to_update: dict, key: str, mission_id: str, mission_data: dict) -> None:
        """Process a single mission, either updating existing or adding new."""
        # Ensure the mission has an ID
        if 'mission_id' not in mission_data:
            mission_data['mission_id'] = mission_id
        
        # Check if this mission already exists (by mission_id)
        existing_mission_index = MissionHandler.find_existing_mission_index(state_to_update[key], mission_id)
        
        if existing_mission_index != -1:
            # Update existing mission
            logging_util.info(f"Updating existing mission: {mission_id}")
            state_to_update[key][existing_mission_index].update(mission_data)
        else:
            # Add new mission
            logging_util.info(f"Adding new mission: {mission_id}")
            state_to_update[key].append(mission_data)
    
    @staticmethod
    def handle_missions_dict_conversion(state_to_update: dict, key: str, missions_dict: dict) -> None:
        """Convert dictionary format missions to list append format."""
        for mission_id, mission_data in missions_dict.items():
            if isinstance(mission_data, dict):
                MissionHandler.process_mission_data(state_to_update, key, mission_id, mission_data)
            else:
                logging_util.warning(f"Skipping invalid mission data for {mission_id}: not a dictionary")
    
    @staticmethod
    def handle_active_missions_conversion(state_to_update: dict, key: str, value) -> None:
        """Handle smart conversion of active_missions from various formats to list."""
        logging_util.warning(f"SMART CONVERSION: AI attempted to set 'active_missions' as {type(value).__name__}. Converting to list append.")
        
        # Initialize active_missions as empty list if it doesn't exist
        MissionHandler.initialize_missions_list(state_to_update, key)
        
        # Convert based on value type
        if isinstance(value, dict):
            # AI is providing missions as a dict like {"main_quest_1": {...}, "side_quest_1": {...}}
            MissionHandler.handle_missions_dict_conversion(state_to_update, key, value)
        else:
            # For other non-list types, log error and skip
            logging_util.error(f"Cannot convert {type(value).__name__} to mission list. Skipping.")


def _handle_append_syntax(state_to_update: dict, key: str, value: dict) -> bool:
    """
    Handle explicit append syntax {'append': ...}.
    
    Returns:
        bool: True if handled, False otherwise
    """
    if not (isinstance(value, dict) and 'append' in value):
        return False
    
    logging_util.info(f"update_state: Detected explicit append for '{key}'.")
    if key not in state_to_update or not isinstance(state_to_update.get(key), list):
        state_to_update[key] = []
    _perform_append(state_to_update[key], value['append'], key, deduplicate=(key == 'core_memories'))
    return True


def _handle_core_memories_safeguard(state_to_update: dict, key: str, value) -> bool:
    """
    Handle safeguard for direct 'core_memories' overwrite.
    
    Returns:
        bool: True if handled, False otherwise
    """
    if key != 'core_memories':
        return False
    
    logging_util.warning("CRITICAL SAFEGUARD: Intercepted direct overwrite on 'core_memories'. Converting to safe, deduplicated append.")
    if key not in state_to_update or not isinstance(state_to_update.get(key), list):
        state_to_update[key] = []
    _perform_append(state_to_update[key], value, key, deduplicate=True)
    return True


def _handle_dict_merge(state_to_update: dict, key: str, value) -> bool:
    """
    Handle dictionary merging and creation.
    
    Returns:
        bool: True if handled, False otherwise
    """
    if not isinstance(value, dict):
        return False
    
    # Case 1: Recursive merge for nested dictionaries
    if isinstance(state_to_update.get(key), collections.abc.Mapping):
        state_to_update[key] = update_state_with_changes(state_to_update.get(key, {}), value)
        return True
    
    # Case 2: Create new dictionary when incoming value is dict but existing is not
    state_to_update[key] = update_state_with_changes({}, value)
    return True


def _handle_delete_token(state_to_update: dict, key: str, value) -> bool:
    """
    Handle DELETE_TOKEN for field deletion.
    
    Returns:
        bool: True if handled, False otherwise
    """
    if value != DELETE_TOKEN:
        return False
    
    if key in state_to_update:
        logging_util.info(f"update_state: Deleting key '{key}' due to DELETE_TOKEN.")
        del state_to_update[key]
    else:
        logging_util.info(f"update_state: Attempted to delete key '{key}' but it doesn't exist.")
    return True


def _handle_string_to_dict_update(state_to_update: dict, key: str, value) -> bool:
    """
    Handle string updates to existing dictionaries (preserve dict structure).
    
    Returns:
        bool: True if handled, False otherwise
    """
    if not isinstance(state_to_update.get(key), collections.abc.Mapping):
        return False
    
    logging_util.info(f"update_state: Preserving dict structure for key '{key}', adding 'status' field.")
    existing_dict = state_to_update[key].copy()
    existing_dict['status'] = value
    state_to_update[key] = existing_dict
    
    return True


def update_state_with_changes(state_to_update: dict, changes: dict) -> dict:
    """
    Recursively updates a state dictionary with a changes dictionary using intelligent merge logic.
    
    This is the core function for applying AI-generated state updates to the game state.
    It implements sophisticated handling for different data types and update patterns.
    
    Key Features:
    - Explicit append syntax: {'append': [items]} for safe list operations
    - Core memories safeguard: Prevents accidental overwrite of important game history
    - Recursive dictionary merging: Deep merge for nested objects
    - DELETE_TOKEN support: Allows removal of specific fields
    - Mission smart conversion: Handles various mission data formats
    - Numeric field conversion: Ensures proper data types
    - Defensive programming: Validates data structures before operations
    
    Update Patterns Handled:
    1. DELETE_TOKEN - Removes fields marked for deletion
    2. Explicit append - Safe list operations with deduplication
    3. Core memories safeguard - Protects critical game history
    4. Mission conversion - Handles dict-to-list conversion for missions
    5. Dictionary merging - Recursive merge for nested structures
    6. String-to-dict preservation - Maintains existing dict structures
    7. Simple overwrite - Default behavior for primitive values
    
    Args:
        state_to_update (dict): The current game state to modify
        changes (dict): Changes to apply (typically from AI response)
        
    Returns:
        dict: Updated state dictionary with changes applied
        
    Example Usage:
        current_state = {"health": 100, "items": ["sword"]}
        changes = {"health": 80, "items": {"append": ["potion"]}}
        result = update_state_with_changes(current_state, changes)
        # Result: {"health": 80, "items": ["sword", "potion"]}
    """
    logging_util.info(f"--- update_state_with_changes: applying changes:\\n{_truncate_log_json(changes)}")
    
    for key, value in changes.items():
        # Try each handler in order of precedence
        
        # Case 1: Handle DELETE_TOKEN first (highest priority)
        if _handle_delete_token(state_to_update, key, value):
            continue
        
        # Case 2: Explicit append syntax
        if _handle_append_syntax(state_to_update, key, value):
            continue
        
        # Case 3: Core memories safeguard
        if _handle_core_memories_safeguard(state_to_update, key, value):
            continue
        
        # Case 4: Active missions smart conversion
        if key == 'active_missions' and not isinstance(value, list):
            MissionHandler.handle_active_missions_conversion(state_to_update, key, value)
            continue
        
        # Case 5: Dictionary operations (merge or create)
        if _handle_dict_merge(state_to_update, key, value):
            continue
        
        # Case 6: String to dict updates (preserve structure)
        if _handle_string_to_dict_update(state_to_update, key, value):
            continue
        
        # Case 7: Simple overwrite for everything else
        # Convert numeric fields from strings to integers
        # Note: We handle conversion here instead of in _handle_dict_merge to avoid
        # double conversion when dictionaries are recursively processed
        if isinstance(value, dict):
            # For dictionaries, use convert_dict to handle nested conversions
            converted_value = NumericFieldConverter.convert_dict(value)
        else:
            # For simple values, use convert_value
            converted_value = NumericFieldConverter.convert_value(key, value)
        state_to_update[key] = converted_value
    logging_util.info("--- update_state_with_changes: finished ---")
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
    # Handle SceneManifest objects from entity tracking
    if hasattr(o, 'to_dict') and callable(getattr(o, 'to_dict')):
        return o.to_dict()
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
    # Also add user_scene_number that only increments for AI responses
    user_scene_counter = 0
    for i, entry in enumerate(all_story_entries):
        entry['sequence_id'] = i + 1
        
        # Only increment user scene number for AI responses
        if entry.get('actor') == 'gemini':
            user_scene_counter += 1
            entry['user_scene_number'] = user_scene_counter
        else:
            entry['user_scene_number'] = None
            
        entry['timestamp'] = entry['timestamp'].isoformat()

    return campaign_doc.to_dict(), all_story_entries


@log_exceptions
def add_story_entry(user_id, campaign_id, actor, text, mode=None, structured_fields=None):
    db = get_db()
    story_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    text_bytes = text.encode('utf-8')
    chunks = [text_bytes[i:i + MAX_TEXT_BYTES] for i in range(0, len(text_bytes), MAX_TEXT_BYTES)]
    base_entry_data = {'actor': actor}
    if mode: base_entry_data['mode'] = mode
    
    # Add structured fields if provided (for AI responses)
    if structured_fields:
        if structured_fields.get('session_header'):
            base_entry_data['session_header'] = structured_fields['session_header']
        if structured_fields.get('planning_block'):
            base_entry_data['planning_block'] = structured_fields['planning_block']
        if structured_fields.get('dice_rolls'):
            base_entry_data['dice_rolls'] = structured_fields['dice_rolls']
        if structured_fields.get('resources'):
            base_entry_data['resources'] = structured_fields['resources']
        if structured_fields.get('debug_info'):
            base_entry_data['debug_info'] = structured_fields['debug_info']
    
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    for i, chunk in enumerate(chunks):
        entry_data = base_entry_data.copy()
        entry_data['text'] = chunk.decode('utf-8')
        entry_data['timestamp'] = timestamp
        entry_data['part'] = i + 1
        story_ref.collection('story').add(entry_data)
    story_ref.update({'last_played': timestamp})

@log_exceptions
def create_campaign(user_id, title, initial_prompt, opening_story, initial_game_state: dict, selected_prompts=None, use_default_world=False, opening_story_structured_fields=None):
    db = get_db()
    campaigns_collection = db.collection('users').document(user_id).collection('campaigns')
    
    # Create the main campaign document
    campaign_ref = campaigns_collection.document()
    campaign_data = {
        'title': title,
        'initial_prompt': initial_prompt,
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'last_played': datetime.datetime.now(datetime.timezone.utc),
        'selected_prompts': selected_prompts or [],
        'use_default_world': use_default_world
    }
    campaign_ref.set(campaign_data)

    # Create the initial game state document
    game_state_ref = campaign_ref.collection('game_states').document('current_state')
    game_state_ref.set(initial_game_state)

    # Assuming 'god' mode for the very first conceptual prompt.
    # You might want to make this mode configurable or infer it.
    add_story_entry(user_id, campaign_ref.id, 'user', initial_prompt, mode='god')
    
    add_story_entry(user_id, campaign_ref.id, 'gemini', opening_story, structured_fields=opening_story_structured_fields)
    
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
        logging_util.info(f"Successfully set new game state for campaign {campaign_id}.")
        # The log below is for the final state being written.
        logging_util.info(f"Final state written to Firestore for campaign {campaign_id}:\\n{_truncate_log_json(game_state_update)}")

    except Exception as e:
        logging_util.error(f"Failed to update game state for campaign {campaign_id}: {e}", exc_info=True)
        raise

# --- NEWLY ADDED FUNCTION ---
@log_exceptions
def update_campaign_title(user_id, campaign_id, new_title):
    """Updates the title of a specific campaign."""
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    campaign_ref.update({'title': new_title})
    return True
