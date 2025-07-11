"""
Mock Firestore Service wrapper that provides the same interface as the real firestore_service module.
"""

from .mock_firestore_service import MockFirestoreClient, MockFirestoreDocument
from .data_fixtures import SAMPLE_CAMPAIGN, SAMPLE_GAME_STATE
import logging_util
import json
import copy
from datetime import datetime
from firebase_admin import firestore

# Module constants from the real service
DELETE_FIELD = firestore.DELETE_FIELD

# Module-level client instance
_client = None

def get_client():
    """Get the mock Firestore client instance."""
    global _client
    if _client is None:
        logging_util.info("Mock Firestore Service: Creating mock client")
        _client = MockFirestoreClient()
    return _client

# --- Campaign Management Functions ---

def get_campaigns_for_user(user_id):
    """Get all campaigns for a user."""
    client = get_client()
    return client.get_campaigns_for_user(user_id)

def get_campaign_by_id(user_id, campaign_id):
    """Get campaign and story context by ID."""
    client = get_client()
    return client.get_campaign_by_id(user_id, campaign_id)

def create_campaign(user_id, title, prompt, opening_story, initial_game_state, selected_prompts=None, use_default_world=False, opening_story_structured_fields=None):
    """Create a new campaign with all parameters."""
    client = get_client()
    # The mock client expects different parameters, so we adapt here
    return client.create_campaign(
        user_id=user_id,
        title=title,
        prompt=prompt,
        opening_story=opening_story,
        selected_prompts=selected_prompts or [],
        initial_game_state=initial_game_state
    )

def update_campaign(user_id, campaign_id, updates):
    """Update an existing campaign."""
    client = get_client()
    return client.update_campaign(user_id, campaign_id, updates)

def delete_campaign(user_id, campaign_id):
    """Delete a campaign."""
    client = get_client()
    return client.delete_campaign(user_id, campaign_id)

# --- Game State Management Functions ---

def get_game_state(user_id, campaign_id):
    """Get current game state."""
    client = get_client()
    return client.get_game_state(user_id, campaign_id)

def update_game_state(user_id, campaign_id, new_state, interaction_type="normal"):
    """Update game state."""
    client = get_client()
    return client.update_game_state(user_id, campaign_id, new_state, interaction_type)

def update_state_with_changes(user_id, campaign_id, state_changes, interaction_type="normal"):
    """Update game state with partial changes."""
    client = get_client()
    # Mock implementation - merge changes into existing state
    current_state = client.get_game_state(user_id, campaign_id)
    if current_state:
        # Deep merge the changes
        merged_state = copy.deepcopy(current_state)
        for key, value in state_changes.items():
            if value == DELETE_FIELD:
                merged_state.pop(key, None)
            else:
                merged_state[key] = value
        return client.update_game_state(user_id, campaign_id, merged_state, interaction_type)
    return False

# --- Story Management Functions ---

def add_story_entry(user_id, campaign_id, story_entry, structured_fields=None):
    """Add a story entry to the log."""
    client = get_client()
    return client.add_story_entry(user_id, campaign_id, story_entry, structured_fields)

def get_story_context(user_id, campaign_id, max_turns=15, include_all=False):
    """Get story context for a campaign."""
    client = get_client()
    return client.get_story_context(user_id, campaign_id, max_turns, include_all)

# --- Helper Functions ---

def json_default_serializer(obj):
    """JSON serializer for objects not serializable by default json code."""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)

def _truncate_log_json(state_dict, max_length=1000):
    """Truncate a state dictionary for logging purposes."""
    json_str = json.dumps(state_dict, default=json_default_serializer)
    if len(json_str) <= max_length:
        return json_str
    return json_str[:max_length] + '... (truncated)'

# Export all the same functions as the real service
__all__ = [
    'get_client',
    'get_campaigns_for_user',
    'get_campaign_by_id', 
    'create_campaign',
    'update_campaign',
    'delete_campaign',
    'get_game_state',
    'update_game_state',
    'update_state_with_changes',
    'add_story_entry',
    'get_story_context',
    'json_default_serializer',
    '_truncate_log_json',
    'DELETE_FIELD'
]