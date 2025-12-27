"""
Mock Firestore Service wrapper that provides the same interface as the real firestore_service module.
"""

import copy
import json

from mvp_site import logging_util
from mvp_site.serialization import json_default_serializer

from .mock_firestore_service import MockFirestoreClient

# Module constants from the real service
DELETE_FIELD = object()  # Simple sentinel for mock

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


def create_campaign(
    user_id,
    title,
    prompt,
    opening_story,
    initial_game_state,
    selected_prompts=None,
    use_default_world=False,
    opening_story_structured_fields=None,
):
    """Create a new campaign with all parameters."""
    client = get_client()
    # The mock client expects different parameters, so we adapt here
    return client.create_campaign(
        user_id=user_id,
        title=title,
        prompt=prompt,
        opening_story=opening_story,
        selected_prompts=selected_prompts or [],
        initial_game_state=initial_game_state,
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


def update_state_with_changes(
    user_id, campaign_id, state_changes, interaction_type="normal"
):
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
        return client.update_game_state(
            user_id, campaign_id, merged_state, interaction_type
        )
    return False


def get_campaign_game_state(user_id, campaign_id):
    """Get the current game state for a campaign (compatibility with real service)."""
    # Use the mock client's get_campaign_game_state method which returns a MockFirestoreDocument
    client = get_client()
    return client.get_campaign_game_state(user_id, campaign_id)


def update_campaign_game_state(user_id, campaign_id, state_dict):
    """Update the current game state for a campaign (compatibility with real service)."""
    client = get_client()
    return client.update_campaign_game_state(user_id, campaign_id, state_dict)


# --- Story Management Functions ---


def add_story_entry(
    user_id,
    campaign_id,
    story_entry=None,
    *,
    actor=None,
    text=None,
    mode=None,
    structured_fields=None,
):
    """Add a story entry to the log. Supports both legacy and new calling patterns."""
    client = get_client()

    # Backward compatibility: handle legacy story_entry parameter
    if story_entry is not None:
        if isinstance(story_entry, dict):
            actor = story_entry.get("actor", actor or "Player")
            text = story_entry.get("text", text or str(story_entry))
            mode = story_entry.get("mode", mode or "character")
            structured_fields = story_entry.get(
                "structured_fields", structured_fields or {}
            )
        else:
            # story_entry is a string
            text = str(story_entry)
            actor = actor or "Player"

    # Set defaults
    if mode is None:
        mode = "character"
    if structured_fields is None:
        structured_fields = {}

    return client.add_story_entry(
        user_id, campaign_id, actor, text, mode, structured_fields
    )


def get_story_context(user_id, campaign_id, max_turns=15, include_all=False):
    """Get story context for a campaign."""
    client = get_client()
    return client.get_story_context(user_id, campaign_id, max_turns, include_all)


def _truncate_log_json(state_dict, max_length=1000):
    """Truncate a state dictionary for logging purposes."""
    json_str = json.dumps(state_dict, default=json_default_serializer)
    if len(json_str) <= max_length:
        return json_str
    return json_str[:max_length] + "... (truncated)"


# Export all the same functions as the real service
__all__ = [
    "get_client",
    "get_campaigns_for_user",
    "get_campaign_by_id",
    "create_campaign",
    "update_campaign",
    "delete_campaign",
    "get_game_state",
    "update_game_state",
    "update_state_with_changes",
    "add_story_entry",
    "get_story_context",
    "json_default_serializer",
    "_truncate_log_json",
    "DELETE_FIELD",
]
