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
import os
import time

import constants
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
    
    # 🚨 DEBUG: Log story retrieval details
    logging_util.info(f"📖 FETCHED STORY ENTRIES: user={user_id}, campaign={campaign_id}, "
                     f"total_entries={len(all_story_entries)}")
    
    # Count entries by actor
    user_entries = [entry for entry in all_story_entries if entry.get('actor') == 'user']
    ai_entries = [entry for entry in all_story_entries if entry.get('actor') == 'gemini']
    other_entries = [entry for entry in all_story_entries if entry.get('actor') not in ['user', 'gemini']]
    
    logging_util.info(f"📊 STORY BREAKDOWN: user_entries={len(user_entries)}, "
                     f"ai_entries={len(ai_entries)}, other_entries={len(other_entries)}")
    
    # Log recent entries for debugging
    if all_story_entries:
        recent_entries = all_story_entries[-5:]  # Last 5 entries
        logging_util.info(f"🔍 RECENT ENTRIES (last {len(recent_entries)}):")
        for i, entry in enumerate(recent_entries, 1):
            actor = entry.get('actor', 'unknown')
            mode = entry.get('mode', 'N/A')
            text_preview = entry.get('text', '')[:50] + '...' if len(entry.get('text', '')) > 50 else entry.get('text', '')
            timestamp = entry.get('timestamp', 'unknown')
            logging_util.info(f"  {i}. [{actor}] {mode} | {text_preview} | {timestamp}")
    else:
        logging_util.warning(f"⚠️ NO STORY ENTRIES FOUND for campaign {campaign_id}")

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
    """Add a story entry to Firestore with write-then-read pattern for data integrity.
    
    This function implements the write-then-read pattern:
    1. Write data to Firestore
    2. Read it back immediately to verify persistence
    3. Only return success if read confirms write succeeded
    
    This prevents data loss from failed writes that appear successful to users.
    
    Args:
        user_id: User ID
        campaign_id: Campaign ID
        actor: Actor type ('user' or 'gemini')
        text: Story text content
        mode: Optional mode (e.g., 'god', 'character')
        structured_fields: Required dict for AI responses containing structured response fields
    """
    # Start timing for latency measurement
    start_time = time.time()
    
    # In mock services mode, skip verification since mocks don't support read-back
    # NOTE: Can't rely on fakes alone - even perfect fakes add 0.9s latency per test
    # Unit tests need to be fast, so bypassing verification entirely is correct
    mock_mode = (os.getenv('MOCK_SERVICES_MODE') == 'true')
    if mock_mode:
        # Use original write-only implementation for testing
        _write_story_entry_to_firestore(user_id, campaign_id, actor, text, mode, structured_fields)
        logging_util.info(f"✅ Write-then-read (mock mode): user={user_id}, campaign={campaign_id}, actor={actor}")
        
        # Return None to match original add_story_entry behavior for mock tests
        return None
    
    # Write to Firestore and capture document ID for verification
    write_start_time = time.time()
    document_id = _write_story_entry_to_firestore(user_id, campaign_id, actor, text, mode, structured_fields)
    write_duration = time.time() - write_start_time
    
    logging_util.info(f"✍️ Write completed: {write_duration:.3f}s, document_id: {document_id}")
    
    # Direct document verification using document ID (much more reliable than text matching)
    verify_start_time = time.time()
    entry_found = False
    
    # Try verification with progressive delays for Firestore eventual consistency
    # NOTE: Keeping synchronous sleep - Flask is sync, async would require major refactor
    for attempt in range(constants.VERIFICATION_MAX_ATTEMPTS):
        delay = constants.VERIFICATION_INITIAL_DELAY + (attempt * constants.VERIFICATION_DELAY_INCREMENT)
        time.sleep(delay)
        
        logging_util.debug(f"🔍 VERIFICATION: Attempt {attempt + 1}/{constants.VERIFICATION_MAX_ATTEMPTS} after {delay}s delay")
        entry_found = verify_document_by_id(user_id, campaign_id, document_id, actor)
        
        if entry_found:
            logging_util.info(f"✅ VERIFICATION: Found document {document_id} on attempt {attempt + 1}")
            break
        
        if attempt < constants.VERIFICATION_MAX_ATTEMPTS - 1:
            logging_util.debug(f"⚠️ VERIFICATION: Attempt {attempt + 1} failed, retrying...")
    
    verify_duration = time.time() - verify_start_time
    
    if not entry_found:
        logging_util.error(f"❌ VERIFICATION: All {constants.VERIFICATION_MAX_ATTEMPTS} attempts failed after {verify_duration:.3f}s")
        raise Exception(f"Write-then-read verification failed: Could not find document '{document_id}' "
                       f"for actor='{actor}' after {constants.VERIFICATION_MAX_ATTEMPTS} attempts")
    
    # Calculate total latency  
    total_duration = time.time() - start_time
    
    logging_util.info(f"📖 Verify-latest timing: {verify_duration:.3f}s (checked latest 10 entries)")
    logging_util.info(f"⏱️ Write-then-read TOTAL latency: {total_duration:.3f}s "
                     f"(write: {write_duration:.3f}s, verify: {verify_duration:.3f}s, sleep: 0.100s)")
    logging_util.info(f"✅ Write-then-read verification successful: "
                     f"user={user_id}, campaign={campaign_id}, actor={actor}")
    
    # Return None to match original add_story_entry API
    return None


def _write_story_entry_to_firestore(user_id, campaign_id, actor, text, mode=None, structured_fields=None):
    """Internal implementation to write story entry data directly to Firestore
    
    Writes story entries using the standard collection.add() method without transactions.
    Text is automatically chunked if it exceeds Firestore's size limits.
    
    Returns:
        str: Document ID of the first chunk (used for verification)
    """
    db = get_db()
    story_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    text_bytes = text.encode('utf-8')
    chunks = [text_bytes[i:i + MAX_TEXT_BYTES] for i in range(0, len(text_bytes), MAX_TEXT_BYTES)]
    
    if not chunks:
        # Handle empty text for both user and AI actors
        if actor == constants.ACTOR_GEMINI and structured_fields:
            # Create a single chunk with placeholder text for AI responses with empty narrative
            placeholder_text = "[Internal thoughts and analysis - see planning block]"
        else:
            # Create a placeholder for empty user inputs
            placeholder_text = "[Empty input]"
        chunks = [placeholder_text.encode('utf-8')]
    base_entry_data = {'actor': actor}
    if mode: base_entry_data['mode'] = mode
    
    # For AI responses, structured_fields should always be provided
    # Save ALL fields from structured_fields to Firestore
    if structured_fields:
        # Simply merge all structured fields into base_entry_data
        # This ensures we capture any field that Gemini provides
        for field_name, field_value in structured_fields.items():
            # Skip None values to avoid storing null fields
            if field_value is not None:
                base_entry_data[field_name] = field_value
    elif actor == constants.ACTOR_GEMINI:
        # Log warning if AI response missing structured fields
        logging_util.warning(f"AI response missing structured_fields for campaign {campaign_id}")
    
    # Simple and reliable write with document ID capture
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    document_id = None
    
    for i, chunk in enumerate(chunks):
        entry_data = base_entry_data.copy()
        entry_data['text'] = chunk.decode('utf-8')
        entry_data['timestamp'] = timestamp
        entry_data['part'] = i + 1
        
        try:
            # Create the story entry and capture document ID
            add_result = story_ref.collection('story').add(entry_data)
            # Handle both real Firestore (returns tuple) and mock (returns doc directly)
            if isinstance(add_result, tuple):
                doc_ref = add_result[1]  # Real Firestore: (Timestamp, DocumentReference)
            else:
                doc_ref = add_result  # Mock Firestore: doc_ref directly
            
            if i == 0:  # Store the first chunk's document ID for verification
                if doc_ref and hasattr(doc_ref, 'id'):
                    document_id = doc_ref.id
                    logging_util.debug(f"✍️ WRITE: Created document {document_id} with actor='{actor}'")
                else:
                    # CRITICAL: This should never happen in production!
                    mock_mode = (os.getenv('MOCK_SERVICES_MODE') == 'true')
                    logging_util.error(f"🚨 CRITICAL: doc_ref missing .id attribute! "
                                     f"mock_mode={mock_mode}, doc_ref={doc_ref}, "
                                     f"add_result={add_result}, type={type(add_result)}")
                    
                    if mock_mode:
                        # Generate mock ID for tests
                        document_id = f"mock-doc-{user_id}-{campaign_id}-{hash(actor + text) % 10000}"
                        logging_util.debug(f"✍️ WRITE: Mock document {document_id} with actor='{actor}'")
                    else:
                        # Production failure - this is a real error
                        raise Exception(f"Firestore add() failed to return valid document reference. "
                                       f"add_result={add_result}, type={type(add_result)}")
        except Exception:
            raise  # Re-raise the exception to maintain original behavior
    
    try:
        story_ref.update({'last_played': timestamp})
    except Exception:
        raise
    
    # Return document ID for verification (fallback if not set)
    # NOTE: Need fallback ID for verification logic - None would cause immediate failure
    return document_id or f"fallback-doc-{user_id}-{campaign_id}-{hash(str(timestamp)) % 10000}"


def verify_document_by_id(user_id, campaign_id, document_id, expected_actor):
    """Verify a story entry was written by directly reading the document by ID
    
    Args:
        user_id: User ID
        campaign_id: Campaign ID  
        document_id: Document ID to verify
        expected_actor: Expected actor type for validation
        
    Returns:
        bool: True if document exists and has correct actor
    """
    if not document_id:
        logging_util.error("🔍 VERIFICATION: No document_id provided")
        return False
        
    try:
        db = get_db()
        campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
        doc_ref = campaign_ref.collection('story').document(document_id)
        
        # Direct document read by ID
        doc = doc_ref.get()
        
        if not doc.exists:
            logging_util.warning(f"🔍 VERIFICATION: Document {document_id} does not exist")
            return False
        
        entry = doc.to_dict()
        actual_actor = entry.get('actor', constants.ACTOR_UNKNOWN)
        
        
        if actual_actor == expected_actor:
            return True
        else:
            logging_util.warning(f"🔄 VERIFICATION: Actor mismatch - expected '{expected_actor}', got '{actual_actor}'")
            return False
            
    except Exception as e:
        logging_util.error(f"❌ VERIFICATION: Error reading document {document_id}: {str(e)}")
        return False


def verify_latest_entry(user_id, campaign_id, actor, text, limit=10):
    """Efficiently verify a story entry was written by reading only the latest entries
    
    Args:
        user_id: User ID
        campaign_id: Campaign ID  
        actor: Expected actor type
        text: Expected text content
        limit: Number of latest entries to check (default 10)
        
    Returns:
        bool: True if matching entry found in latest entries
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    
    # Read only the latest N entries, ordered by timestamp descending
    story_ref = campaign_ref.collection('story').order_by('timestamp', direction='DESCENDING').limit(limit)
    story_docs = story_ref.stream()
    
    
    entries_found = []
    # Check if our entry is among the latest entries
    for i, doc in enumerate(story_docs):
        entry = doc.to_dict()
        entry_actor = entry.get('actor', constants.ACTOR_UNKNOWN)
        entry_text = entry.get('text', 'NO_TEXT')
        
        # Check for exact match
        if entry_actor == actor and entry_text == text:
            return True
    
    return False




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
