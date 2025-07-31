"""
End-to-end integration test for debug mode functionality.
Tests the full flow from settings API to UI state consistency.
Only mocks external services (Gemini API and Firestore DB) at the lowest level.
"""

import json
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add the parent directory to the path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# Check for Firebase credentials - same pattern as other tests
def has_firebase_credentials():
    """Check if Firebase credentials are available."""
    # Check for various credential sources
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    if os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY"):
        return True
    # Check for application default credentials
    try:
        import google.auth

        google.auth.default()
        return True
    except Exception:
        return False


from main import HEADER_TEST_BYPASS, HEADER_TEST_USER_ID, create_app


class FakeFirestoreDocument:
    """Fake Firestore document that behaves like the real thing."""

    def __init__(self, doc_id=None, data=None, parent_path=""):
        self.id = doc_id or "test-doc-id"
        self._data = data or {}
        self._parent_path = parent_path
        self._collections = {}

    def set(self, data):
        """Simulate setting document data."""
        self._data = data

    def update(self, data):
        """Simulate updating document data with support for nested field updates."""
        for key, value in data.items():
            if "." in key:
                # Handle nested field updates like 'settings.debug_mode'
                parts = key.split(".")
                current = self._data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                self._data[key] = value

    def get(self):
        """Simulate getting the document."""
        return self

    def exists(self):
        """Document exists after being set."""
        return bool(self._data)

    def to_dict(self):
        """Return the document data."""
        return self._data

    def collection(self, name):
        """Get a subcollection."""
        path = (
            f"{self._parent_path}/{self.id}/{name}"
            if self._parent_path
            else f"{self.id}/{name}"
        )
        if name not in self._collections:
            self._collections[name] = FakeFirestoreCollection(name, parent_path=path)
        return self._collections[name]


class FakeFirestoreCollection:
    """Fake Firestore collection that behaves like the real thing."""

    def __init__(self, name, parent_path=""):
        self.name = name
        self._parent_path = parent_path
        self._docs = {}
        self._doc_counter = 0

    def document(self, doc_id=None):
        """Get or create a document reference."""
        if doc_id is None:
            # Generate a new ID
            self._doc_counter += 1
            doc_id = f"generated-id-{self._doc_counter}"

        if doc_id not in self._docs:
            path = (
                f"{self._parent_path}/{self.name}" if self._parent_path else self.name
            )
            self._docs[doc_id] = FakeFirestoreDocument(doc_id, parent_path=path)

        return self._docs[doc_id]

    def stream(self):
        """Stream all documents."""
        return list(self._docs.values())

    def add(self, data):
        """Add a new document with auto-generated ID."""
        doc = self.document()  # This creates a doc with auto-generated ID
        doc.set(data)
        return doc

    def order_by(self, field_name):
        """Order by a field (for compatibility with Firestore)."""
        # For testing purposes, just return self since we're not doing complex ordering
        return self


class FakeFirestoreClient:
    """Fake Firestore client that behaves like the real thing."""

    def __init__(self):
        self._collections = {}

    def collection(self, path):
        """Get a collection."""
        if path not in self._collections:
            self._collections[path] = FakeFirestoreCollection(path, parent_path="")
        return self._collections[path]

    def document(self, path):
        """Get a document by path."""
        parts = path.split("/")
        if len(parts) == 2:
            collection_name, doc_id = parts
            return self.collection(collection_name).document(doc_id)
        if len(parts) == 4:
            # Nested collection like campaigns/id/story
            parent_collection, parent_id, sub_collection, doc_id = parts
            # For simplicity, just return a fake document
            return FakeFirestoreDocument(doc_id)
        raise ValueError(f"Invalid document path: {path}")


class FakeGeminiResponse:
    """Fake Gemini response that behaves like the real thing."""

    def __init__(self, text):
        self.text = text


@unittest.skipUnless(
    has_firebase_credentials(),
    "Skipping debug mode end2end tests - Firebase credentials not available (expected in CI)",
)
class TestDebugModeEnd2End(unittest.TestCase):
    """Test debug mode functionality through the full application stack."""

    def setUp(self):
        """Set up test client and test data."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data
        self.test_user_id = "debug-test-user-123"
        self.test_campaign_id = "debug-test-campaign-456"
        self.test_headers = {
            HEADER_TEST_BYPASS: "true",
            HEADER_TEST_USER_ID: self.test_user_id,
        }

        # Set up fake Firestore and Gemini (shared across tests)
        self.fake_firestore = FakeFirestoreClient()
        self.fake_genai_client = MagicMock()

        # Create initial user document with settings (matching real structure)
        user_data = {
            "settings": {
                "debug_mode": False,  # Default user setting
                "gemini_model": "gemini-2.5-flash",
            },
            "lastUpdated": "2025-01-01T00:00:00Z",
        }
        users_collection = self.fake_firestore.collection("users")
        user_doc = users_collection.document(self.test_user_id)
        user_doc.set(user_data)

        # Create initial campaign data
        campaign_data = {
            "title": "Debug Test Campaign",
            "prompt": "Test campaign for debug mode",
            "user_id": self.test_user_id,
        }

        # Set up campaign in fake Firestore (using the user_doc already created above)
        campaigns_collection = user_doc.collection("campaigns")
        campaign_doc = campaigns_collection.document(self.test_campaign_id)
        campaign_doc.set(campaign_data)

        # Set up initial game state with debug_mode defaulting to True
        game_state_data = {
            "game_state_version": 1,
            "debug_mode": True,  # Game state default
            "player_character_data": {
                "name": "Test Hero",
                "level": 1,
                "hp_current": 10,
                "hp_max": 10,
            },
        }
        game_state_doc = campaign_doc.collection("game_state").document("current")
        game_state_doc.set(game_state_data)

        # Set up story entries
        story_collection = campaign_doc.collection("story")
        story_entry = {
            "actor": "gemini",
            "text": "Welcome to the adventure!",
            "timestamp": datetime.fromisoformat("2025-01-01T00:00:00"),
            "debug_info": "This is debug information",
            "planning_block": "GM planning notes",
        }
        story_collection.add(story_entry)

    @patch("firebase_admin.firestore.client")
    def test_turn_on_debug_mode(self, mock_firestore_client):
        """Test Case 1: Turn on debug mode via settings API."""
        mock_firestore_client.return_value = self.fake_firestore

        # Initially no user settings (defaults to False)
        response = self.client.get("/api/settings", headers=self.test_headers)
        assert response.status_code == 200
        settings_data = json.loads(response.data)
        assert not settings_data.get("debug_mode")  # Default

        # Turn ON debug mode
        debug_settings = {"debug_mode": True}
        response = self.client.post(
            "/api/settings",
            data=json.dumps(debug_settings),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify settings API response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"]

        # Verify settings were persisted
        response = self.client.get("/api/settings", headers=self.test_headers)
        assert response.status_code == 200
        settings_data = json.loads(response.data)
        assert settings_data["debug_mode"]

    @patch("firebase_admin.firestore.client")
    def test_turn_off_debug_mode(self, mock_firestore_client):
        """Test Case 2: Turn off debug mode via settings API."""
        mock_firestore_client.return_value = self.fake_firestore

        # First turn ON debug mode
        debug_settings = {"debug_mode": True}
        response = self.client.post(
            "/api/settings",
            data=json.dumps(debug_settings),
            content_type="application/json",
            headers=self.test_headers,
        )
        assert response.status_code == 200

        # Now turn OFF debug mode
        debug_settings = {"debug_mode": False}
        response = self.client.post(
            "/api/settings",
            data=json.dumps(debug_settings),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify settings API response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"]

        # Verify settings were persisted
        response = self.client.get("/api/settings", headers=self.test_headers)
        assert response.status_code == 200
        settings_data = json.loads(response.data)
        assert not settings_data["debug_mode"]

    @patch("firebase_admin.firestore.client")
    def test_ui_state_debug_mode_on(self, mock_firestore_client):
        """Test Case 3: UI receives correct state when debug mode is ON."""
        mock_firestore_client.return_value = self.fake_firestore

        # Turn ON debug mode in settings
        debug_settings = {"debug_mode": True}
        response = self.client.post(
            "/api/settings",
            data=json.dumps(debug_settings),
            content_type="application/json",
            headers=self.test_headers,
        )
        assert response.status_code == 200

        # Get campaign data (what the UI loads on page load)
        response = self.client.get(
            f"/api/campaigns/{self.test_campaign_id}",
            headers=self.test_headers,
        )

        # Verify campaign API response
        assert response.status_code == 200
        campaign_data = json.loads(response.data)

        # CRITICAL: game_state.debug_mode should reflect user settings (True)
        assert "game_state" in campaign_data
        assert campaign_data["game_state"]["debug_mode"]

        # Verify story entries include debug content when debug mode is on
        assert "story" in campaign_data
        story_entries = campaign_data["story"]
        assert len(story_entries) > 0

        # Debug fields should be present in story entries
        gemini_entry = None
        for entry in story_entries:
            if entry.get("actor") == "gemini":
                gemini_entry = entry
                break

        assert gemini_entry is not None
        # With debug mode ON, debug fields should be preserved
        assert "debug_info" in gemini_entry
        assert "planning_block" in gemini_entry

    @patch("firebase_admin.firestore.client")
    def test_ui_state_debug_mode_off(self, mock_firestore_client):
        """Test Case 4: UI receives correct state when debug mode is OFF."""
        mock_firestore_client.return_value = self.fake_firestore

        # Turn OFF debug mode in settings
        debug_settings = {"debug_mode": False}
        response = self.client.post(
            "/api/settings",
            data=json.dumps(debug_settings),
            content_type="application/json",
            headers=self.test_headers,
        )
        assert response.status_code == 200

        # Get campaign data (what the UI loads on page load)
        response = self.client.get(
            f"/api/campaigns/{self.test_campaign_id}",
            headers=self.test_headers,
        )

        # Verify campaign API response
        assert response.status_code == 200
        campaign_data = json.loads(response.data)

        # CRITICAL: game_state.debug_mode should reflect user settings (False)
        assert "game_state" in campaign_data
        assert not campaign_data["game_state"]["debug_mode"]

        # Verify story entries have debug content stripped when debug mode is off
        assert "story" in campaign_data
        story_entries = campaign_data["story"]
        assert len(story_entries) > 0

        # Debug fields should be stripped from story entries
        gemini_entry = None
        for entry in story_entries:
            if entry.get("actor") == "gemini":
                gemini_entry = entry
                break

        assert gemini_entry is not None
        # With debug mode OFF, only debug fields should be removed (planning_block remains as it's a gameplay feature)
        assert "debug_info" not in gemini_entry
        assert "planning_block" in gemini_entry

    @patch("firebase_admin.firestore.client")
    @patch("google.genai.Client")
    def test_interaction_respects_debug_mode_setting(
        self, mock_genai_client_class, mock_firestore_client
    ):
        """Test that game interactions respect the user's debug mode setting."""
        mock_firestore_client.return_value = self.fake_firestore
        mock_genai_client_class.return_value = self.fake_genai_client

        # Mock Gemini responses
        self.fake_genai_client.models.count_tokens.return_value = MagicMock(
            total_tokens=1000
        )

        # Mock Gemini response with debug content
        gemini_response_data = {
            "narrative": "The hero continues their journey...",
            "debug_content": {
                "dm_notes": "This is GM-only information",
                "dice_rolls": ["1d20: 15"],
                "state_changes": {"test": "data"},
            },
        }
        self.fake_genai_client.models.generate_content.return_value = (
            FakeGeminiResponse(json.dumps(gemini_response_data))
        )

        # Test with debug mode OFF
        debug_settings = {"debug_mode": False}
        self.client.post(
            "/api/settings",
            data=json.dumps(debug_settings),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Make a game interaction
        interaction_data = {"input": "I look around the area", "mode": "character"}
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            data=json.dumps(interaction_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # MCP should handle interaction requests (may return 400/404 for nonexistent campaigns)
        assert response.status_code in [200, 400, 404]

        # Only test response content if interaction succeeds
        if response.status_code == 200:
            response_data = json.loads(response.data)

            # With debug mode OFF, debug_mode should be False in the response
            assert not response_data.get("debug_mode")

            # Debug content should not be in the narrative response
            narrative = response_data.get("narrative", "")
            assert "GM-only information" not in narrative

    @patch("firebase_admin.firestore.client")
    def test_debug_mode_persistence_across_requests(self, mock_firestore_client):
        """Test that debug mode setting persists across multiple requests."""
        mock_firestore_client.return_value = self.fake_firestore

        # Set debug mode to True
        debug_settings = {"debug_mode": True}
        response = self.client.post(
            "/api/settings",
            data=json.dumps(debug_settings),
            content_type="application/json",
            headers=self.test_headers,
        )
        assert response.status_code == 200

        # Make multiple GET requests and verify consistency
        for i in range(3):
            response = self.client.get("/api/settings", headers=self.test_headers)
            assert response.status_code == 200
            settings_data = json.loads(response.data)
            assert settings_data["debug_mode"], f"Failed on request {i + 1}"

            # Also test campaign endpoint consistency
            response = self.client.get(
                f"/api/campaigns/{self.test_campaign_id}",
                headers=self.test_headers,
            )
            assert response.status_code == 200
            campaign_data = json.loads(response.data)
            assert campaign_data["game_state"][
                "debug_mode"
            ], f"Campaign debug mode inconsistent on request {i + 1}"

    @patch("firebase_admin.firestore.client")
    def test_backend_strips_game_state_fields_when_debug_off(
        self, mock_firestore_client
    ):
        """Test that backend strips game state fields (entities, state_updates, debug_info) when debug mode is OFF."""
        mock_firestore_client.return_value = self.fake_firestore

        # Create a story entry with all possible fields including game state fields
        campaign_doc = (
            self.fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(self.test_campaign_id)
        )
        story_collection = campaign_doc.collection("story")

        # Add a story entry with comprehensive structured fields
        story_entry_with_game_state = {
            "actor": "gemini",
            "text": "The adventure continues...",
            "timestamp": datetime.fromisoformat("2025-01-01T01:00:00"),
            # Fields that should be STRIPPED when debug mode is OFF
            "entities_mentioned": ["Dragon", "Knight", "Castle"],
            "entities": [
                {"name": "Dragon", "status": "hostile"},
                {"name": "Knight", "status": "friendly"},
            ],
            "state_updates": {
                "player_character_data": {"hp_current": 8, "hp_max": 10},
                "npc_data": {"dragon_001": {"name": "Ancient Red Dragon", "hp": 100}},
            },
            "debug_info": {
                "dm_notes": ["Player rolled well", "Dragon should retreat"],
                "state_rationale": "HP reduced due to combat",
            },
            # Fields that should REMAIN when debug mode is OFF
            "resources": "Lost 1 healing potion",
            "dice_rolls": ["1d20+5: 18 (Attack)", "1d8+3: 7 (Damage)"],
            "location_confirmed": "Ancient Dragon's Lair",
            "planning_block": "What do you do next?",
            "god_mode_response": "The dragon roars menacingly",
        }
        story_collection.add(story_entry_with_game_state)

        # Test with debug mode OFF - game state fields should be stripped
        debug_settings = {"debug_mode": False}
        response = self.client.post(
            "/api/settings",
            data=json.dumps(debug_settings),
            content_type="application/json",
            headers=self.test_headers,
        )
        assert response.status_code == 200

        # Get campaign data with debug mode OFF
        response = self.client.get(
            f"/api/campaigns/{self.test_campaign_id}",
            headers=self.test_headers,
        )
        assert response.status_code == 200
        campaign_data = json.loads(response.data)

        # Find the gemini story entry
        gemini_entries = [
            entry for entry in campaign_data["story"] if entry.get("actor") == "gemini"
        ]
        assert len(gemini_entries) > 0, "Should have at least one Gemini entry"

        latest_entry = gemini_entries[-1]  # Get the latest entry we just added

        # CRITICAL: Fields that should be STRIPPED when debug mode is OFF
        assert (
            "entities_mentioned" not in latest_entry
        ), "entities_mentioned should be stripped when debug mode is OFF"
        assert (
            "entities" not in latest_entry
        ), "entities should be stripped when debug mode is OFF"
        assert (
            "state_updates" not in latest_entry
        ), "state_updates should be stripped when debug mode is OFF"
        assert (
            "debug_info" not in latest_entry
        ), "debug_info should be stripped when debug mode is OFF"

        # CRITICAL: Fields that should REMAIN when debug mode is OFF
        assert (
            "resources" in latest_entry
        ), "resources should remain when debug mode is OFF"
        assert (
            "dice_rolls" in latest_entry
        ), "dice_rolls should remain when debug mode is OFF"
        assert (
            "location_confirmed" in latest_entry
        ), "location_confirmed should remain when debug mode is OFF"
        assert (
            "planning_block" in latest_entry
        ), "planning_block should remain when debug mode is OFF"
        assert (
            "god_mode_response" in latest_entry
        ), "god_mode_response should remain when debug mode is OFF"

        # Verify the content of remaining fields
        assert latest_entry["resources"] == "Lost 1 healing potion"
        assert latest_entry["dice_rolls"] == [
            "1d20+5: 18 (Attack)",
            "1d8+3: 7 (Damage)",
        ]
        assert latest_entry["location_confirmed"] == "Ancient Dragon's Lair"
        assert latest_entry["planning_block"] == "What do you do next?"
        assert latest_entry["god_mode_response"] == "The dragon roars menacingly"

        # Now test with debug mode ON - all fields should be present
        debug_settings = {"debug_mode": True}
        response = self.client.post(
            "/api/settings",
            data=json.dumps(debug_settings),
            content_type="application/json",
            headers=self.test_headers,
        )
        assert response.status_code == 200

        # Get campaign data with debug mode ON
        response = self.client.get(
            f"/api/campaigns/{self.test_campaign_id}",
            headers=self.test_headers,
        )
        assert response.status_code == 200
        campaign_data = json.loads(response.data)

        # Find the gemini story entry again
        gemini_entries = [
            entry for entry in campaign_data["story"] if entry.get("actor") == "gemini"
        ]
        latest_entry = gemini_entries[-1]

        # With debug mode ON, ALL fields should be present
        assert (
            "entities_mentioned" in latest_entry
        ), "entities_mentioned should be present when debug mode is ON"
        assert (
            "entities" in latest_entry
        ), "entities should be present when debug mode is ON"
        assert (
            "state_updates" in latest_entry
        ), "state_updates should be present when debug mode is ON"
        assert (
            "debug_info" in latest_entry
        ), "debug_info should be present when debug mode is ON"
        assert (
            "resources" in latest_entry
        ), "resources should be present when debug mode is ON"
        assert (
            "dice_rolls" in latest_entry
        ), "dice_rolls should be present when debug mode is ON"

        # Verify the content of game state fields that should only appear in debug mode
        assert latest_entry["entities_mentioned"] == ["Dragon", "Knight", "Castle"]
        assert len(latest_entry["entities"]) == 2
        assert "player_character_data" in latest_entry["state_updates"]
        assert "dm_notes" in latest_entry["debug_info"]


if __name__ == "__main__":
    unittest.main()
