"""
Mock Firestore service for function testing.
Provides in-memory database simulation without making actual Firestore calls.
"""
import copy
import datetime
import os
import sys
from typing import Any, Dict, List, Optional

from .data_fixtures import SAMPLE_CAMPAIGN, SAMPLE_GAME_STATE, SAMPLE_STORY_CONTEXT

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import constants


class MockFirestoreDocument:
    """Mock Firestore document that behaves like the real DocumentSnapshot."""

    def __init__(self, data: Dict[str, Any], doc_id: str = None):
        self._data = data
        self._id = doc_id or "mock_doc_id"
        self._exists = data is not None

    def to_dict(self) -> Dict[str, Any]:
        """Return the document data as a dictionary."""
        return copy.deepcopy(self._data) if self._data else {}

    def get(self, field_path: str, default=None):
        """Get a specific field from the document."""
        if not self._data:
            return default

        # Handle nested field paths like "player.name"
        keys = field_path.split('.')
        value = self._data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    @property
    def exists(self) -> bool:
        """Check if the document exists."""
        return self._exists

    @property
    def id(self) -> str:
        """Get the document ID."""
        return self._id


class MockFirestoreClient:
    """
    Mock Firestore client that simulates database operations in memory.
    Designed to behave like the real Firestore client for testing purposes.
    """

    def __init__(self):
        # In-memory storage
        self.campaigns: Dict[str, Dict[str, Any]] = {}
        self.game_states: Dict[str, Dict[str, Any]] = {}
        self.story_logs: Dict[str, List[Dict[str, Any]]] = {}

        # Operation tracking
        self.operation_count = 0
        self.last_operation = None

        # Initialize with sample data
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize the mock with sample data for testing."""
        campaign_id = SAMPLE_CAMPAIGN["id"]
        user_id = SAMPLE_CAMPAIGN["user_id"]

        # Store sample campaign
        user_campaigns = self.campaigns.setdefault(user_id, {})
        user_campaigns[campaign_id] = copy.deepcopy(SAMPLE_CAMPAIGN)

        # Store sample game state
        state_key = f"{user_id}_{campaign_id}"
        self.game_states[state_key] = copy.deepcopy(SAMPLE_GAME_STATE)

        # Store sample story context
        self.story_logs[state_key] = copy.deepcopy(SAMPLE_STORY_CONTEXT)

        # Also add data for browser test user
        browser_test_user_id = "browser-test-user"
        browser_campaign = copy.deepcopy(SAMPLE_CAMPAIGN)
        browser_campaign["user_id"] = browser_test_user_id
        browser_campaign["id"] = "browser_test_campaign_123"
        browser_campaign["title"] = "Browser Test Campaign"
        browser_campaign["initialPrompt"] = "Test campaign for browser structured fields testing"

        browser_user_campaigns = self.campaigns.setdefault(browser_test_user_id, {})
        browser_user_campaigns[browser_campaign["id"]] = browser_campaign

        # Store browser test game state and story
        browser_state_key = f"{browser_test_user_id}_{browser_campaign['id']}"
        self.game_states[browser_state_key] = copy.deepcopy(SAMPLE_GAME_STATE)
        self.story_logs[browser_state_key] = copy.deepcopy(SAMPLE_STORY_CONTEXT)

        # Log for debugging
        # Browser test campaign added for user

    def get_campaigns_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all campaigns for a user."""
        self.operation_count += 1
        self.last_operation = f"get_campaigns_for_user({user_id})"

        user_campaigns = self.campaigns.get(user_id, {})
        return list(user_campaigns.values())

    def get_campaign_by_id(self, user_id: str, campaign_id: str) -> tuple:
        """Get campaign and story context by ID."""
        self.operation_count += 1
        self.last_operation = f"get_campaign_by_id({user_id}, {campaign_id})"

        # Get campaign data
        campaign = self.campaigns.get(user_id, {}).get(campaign_id)
        if not campaign:
            return None, []

        # Get story context
        state_key = f"{user_id}_{campaign_id}"
        story_context = self.story_logs.get(state_key, [])

        return copy.deepcopy(campaign), copy.deepcopy(story_context)

    def get_campaign_game_state(self, user_id: str, campaign_id: str) -> Optional[MockFirestoreDocument]:
        """Get the game state for a campaign."""
        self.operation_count += 1
        self.last_operation = f"get_campaign_game_state({user_id}, {campaign_id})"

        state_key = f"{user_id}_{campaign_id}"
        state_data = self.game_states.get(state_key)

        if state_data:
            return MockFirestoreDocument(state_data, f"game_state_{campaign_id}")
        return None

    def update_campaign_game_state(self, user_id: str, campaign_id: str, state_dict: Dict[str, Any]):
        """Update the game state for a campaign."""
        self.operation_count += 1
        self.last_operation = f"update_campaign_game_state({user_id}, {campaign_id})"

        state_key = f"{user_id}_{campaign_id}"
        self.game_states[state_key] = copy.deepcopy(state_dict)

    def create_campaign(self, user_id: str, title: str, prompt: str, opening_story: str,
                       initial_game_state: Dict[str, Any], selected_prompts: List[str]) -> str:
        """Create a new campaign."""
        self.operation_count += 1
        campaign_id = f"campaign_{self.operation_count}"
        self.last_operation = f"create_campaign({user_id}, {title})"

        # Create campaign data
        campaign_data = {
            "id": campaign_id,
            "title": title,
            "user_id": user_id,
            "prompt": prompt,
            "selected_prompts": selected_prompts,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "last_played": datetime.datetime.now(datetime.timezone.utc)
        }

        # Store campaign
        user_campaigns = self.campaigns.setdefault(user_id, {})
        user_campaigns[campaign_id] = campaign_data

        # Store initial game state
        state_key = f"{user_id}_{campaign_id}"
        self.game_states[state_key] = copy.deepcopy(initial_game_state)

        # Initialize story log with opening story
        self.story_logs[state_key] = [{
            constants.KEY_ACTOR: constants.ACTOR_GEMINI,
            constants.KEY_TEXT: opening_story,
            constants.KEY_MODE: constants.MODE_CHARACTER,
            "sequence_id": 1,
            "timestamp": datetime.datetime.now(datetime.timezone.utc)
        }]

        return campaign_id

    def add_story_entry(self, user_id: str, campaign_id: str, actor: str, text: str, mode: str = None, structured_fields: Dict[str, Any] = None):
        """Add a story entry to the campaign log."""
        self.operation_count += 1
        self.last_operation = f"add_story_entry({user_id}, {campaign_id}, {actor})"

        state_key = f"{user_id}_{campaign_id}"
        story_log = self.story_logs.setdefault(state_key, [])

        # Calculate next sequence ID
        next_seq_id = len(story_log) + 1

        entry = {
            constants.KEY_ACTOR: actor,
            constants.KEY_TEXT: text,
            constants.KEY_MODE: mode or constants.MODE_CHARACTER,
            "sequence_id": next_seq_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc)
        }

        # Add structured fields if provided
        if structured_fields:
            if structured_fields.get('session_header'):
                entry['session_header'] = structured_fields['session_header']
            if structured_fields.get('planning_block'):
                entry['planning_block'] = structured_fields['planning_block']
            if structured_fields.get('dice_rolls'):
                entry['dice_rolls'] = structured_fields['dice_rolls']
            if structured_fields.get('resources'):
                entry['resources'] = structured_fields['resources']
            if structured_fields.get('debug_info'):
                entry['debug_info'] = structured_fields['debug_info']

        story_log.append(entry)

    def update_campaign_title(self, user_id: str, campaign_id: str, new_title: str):
        """Update a campaign's title."""
        self.operation_count += 1
        self.last_operation = f"update_campaign_title({user_id}, {campaign_id})"

        campaign = self.campaigns.get(user_id, {}).get(campaign_id)
        if campaign:
            campaign["title"] = new_title
            campaign["last_played"] = datetime.datetime.now(datetime.timezone.utc)

    def update_campaign(self, user_id: str, campaign_id: str, updates: Dict[str, Any]):
        """Update a campaign with arbitrary updates."""
        self.operation_count += 1
        self.last_operation = f"update_campaign({user_id}, {campaign_id})"

        campaign = self.campaigns.get(user_id, {}).get(campaign_id)
        if campaign:
            campaign.update(updates)
            campaign["last_played"] = datetime.datetime.now(datetime.timezone.utc)
            return True
        return False

    def delete_campaign(self, user_id: str, campaign_id: str):
        """Delete a campaign and all associated data."""
        self.operation_count += 1
        self.last_operation = f"delete_campaign({user_id}, {campaign_id})"

        # Delete campaign
        user_campaigns = self.campaigns.get(user_id, {})
        if campaign_id in user_campaigns:
            del user_campaigns[campaign_id]

            # Delete associated game state and story logs
            state_key = f"{user_id}_{campaign_id}"
            self.game_states.pop(state_key, None)
            self.story_logs.pop(state_key, None)
            return True
        return False

    def get_game_state(self, user_id: str, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get current game state as a dictionary."""
        self.operation_count += 1
        self.last_operation = f"get_game_state({user_id}, {campaign_id})"

        state_key = f"{user_id}_{campaign_id}"
        return copy.deepcopy(self.game_states.get(state_key))

    def update_game_state(self, user_id: str, campaign_id: str, new_state: Dict[str, Any], interaction_type: str = "normal"):
        """Update the game state."""
        self.operation_count += 1
        self.last_operation = f"update_game_state({user_id}, {campaign_id}, interaction_type={interaction_type})"

        state_key = f"{user_id}_{campaign_id}"
        self.game_states[state_key] = copy.deepcopy(new_state)
        return True

    def get_story_context(self, user_id: str, campaign_id: str, max_turns: int = 15, include_all: bool = False) -> List[Dict[str, Any]]:
        """Get story context for a campaign."""
        self.operation_count += 1
        self.last_operation = f"get_story_context({user_id}, {campaign_id}, max_turns={max_turns})"

        state_key = f"{user_id}_{campaign_id}"
        story_log = self.story_logs.get(state_key, [])

        if include_all:
            return copy.deepcopy(story_log)
        else:
            # Return last max_turns entries
            return copy.deepcopy(story_log[-max_turns:] if len(story_log) > max_turns else story_log)

    def reset(self):
        """Reset the mock to initial state."""
        self.campaigns.clear()
        self.game_states.clear()
        self.story_logs.clear()
        self.operation_count = 0
        self.last_operation = None
        self._initialize_sample_data()

    def get_operation_stats(self) -> Dict[str, Any]:
        """Get statistics about mock operations."""
        return {
            "operation_count": self.operation_count,
            "last_operation": self.last_operation,
            "campaigns_count": sum(len(user_campaigns) for user_campaigns in self.campaigns.values()),
            "game_states_count": len(self.game_states),
            "story_logs_count": len(self.story_logs)
        }

    def set_campaign_data(self, user_id: str, campaign_id: str, campaign_data: Dict[str, Any]):
        """Set specific campaign data for testing."""
        user_campaigns = self.campaigns.setdefault(user_id, {})
        user_campaigns[campaign_id] = copy.deepcopy(campaign_data)

    def set_game_state_data(self, user_id: str, campaign_id: str, state_data: Dict[str, Any]):
        """Set specific game state data for testing."""
        state_key = f"{user_id}_{campaign_id}"
        self.game_states[state_key] = copy.deepcopy(state_data)

    def set_story_context(self, user_id: str, campaign_id: str, story_context: List[Dict[str, Any]]):
        """Set specific story context for testing."""
        state_key = f"{user_id}_{campaign_id}"
        self.story_logs[state_key] = copy.deepcopy(story_context)


# Global mock instance for easy testing
mock_firestore_client = MockFirestoreClient()


def get_mock_firestore_client():
    """Get the global mock Firestore client instance."""
    return mock_firestore_client


# Module-level functions that delegate to the global instance
def add_story_entry(user_id: str, campaign_id: str, actor: str, text: str, mode: str = None, structured_fields: Dict[str, Any] = None):
    """Add a story entry to the campaign log."""
    return mock_firestore_client.add_story_entry(user_id, campaign_id, actor, text, mode, structured_fields)


def get_campaign_by_id(user_id: str, campaign_id: str):
    """Get a campaign by ID."""
    return mock_firestore_client.get_campaign_by_id(user_id, campaign_id)
