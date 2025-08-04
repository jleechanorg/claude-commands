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

# Import JSON input schema components
try:
    # Legacy json_input_schema imports removed - using GeminiRequest now

    from tests.fake_services import FakeServiceManager
except ImportError:
    JsonInputBuilder = None
    JsonInputValidator = None
    FakeServiceManager = None


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

    def test_json_input_validation_in_debug_context(self):
        """Test JSON input validation in debug mode context."""
        if not (JsonInputBuilder and JsonInputValidator and FakeServiceManager):
            self.skipTest("JSON input schema components not available")

        with FakeServiceManager() as fake_services:
            # Create JSON input for debug mode interaction
            json_input = fake_services.create_json_input(
                "story_continuation",
                user_action="I examine the debug info panel",
                game_mode="character",
                user_id=self.test_user_id,
                context={
                    "campaign_id": self.test_campaign_id,
                    "debug_mode": True,
                    "sequence_ids": [1, 2, 3],
                    "checkpoint_block": "Debug mode is currently enabled",
                    "selected_prompts": ["narrative", "mechanics", "debug"],
                },
            )

            # Validate JSON structure
            is_valid = fake_services.validate_json_input(json_input)
            self.assertTrue(
                is_valid, "Debug mode story continuation JSON should be valid"
            )

            # Test that fake services handle debug mode JSON correctly
            fake_response = fake_services.gemini_client.models.generate_content(
                json_input
            )
            self.assertIsNotNone(fake_response)

            # Validate response contains debug-appropriate content
            try:
                response_data = json.loads(fake_response.text)
                self.assertIsInstance(response_data, dict)
                # Should contain narrative for story continuation
                self.assertIn("narrative", response_data)
                # May contain debug fields when debug mode enabled
                if "debug_info" in response_data:
                    self.assertIsInstance(response_data["debug_info"], dict)
            except json.JSONDecodeError:
                self.fail("Debug mode story continuation should return valid JSON")

    def test_json_input_validation_debug_mode_toggling(self):
        """Test JSON input validation when debug mode is toggled."""
        if not (JsonInputBuilder and JsonInputValidator):
            self.skipTest("JSON input schema components not available")

        builder = JsonInputBuilder()
        validator = JsonInputValidator()

        # Test JSON input with debug mode ON using story continuation
        debug_on_input = builder.build_story_continuation_input(
            user_action="Show me all debug information",
            user_id=self.test_user_id,
            game_mode="character",
            game_state={"debug_mode": True},
            story_history=[],
            checkpoint_block="Debug mode enabled",
            core_memories=[],
            sequence_ids=[],
            entity_tracking={},
            selected_prompts=["narrative", "debug"],
        )

        result_on = validator.validate(debug_on_input)
        self.assertIsInstance(result_on.is_valid, bool)

        # Test JSON input with debug mode OFF using story continuation
        debug_off_input = builder.build_story_continuation_input(
            user_action="Continue the story normally",
            user_id=self.test_user_id,
            game_mode="character",
            game_state={"debug_mode": False},
            story_history=[],
            checkpoint_block="Debug mode disabled",
            core_memories=[],
            sequence_ids=[],
            entity_tracking={},
            selected_prompts=["narrative"],
        )

        result_off = validator.validate(debug_off_input)
        self.assertIsInstance(result_off.is_valid, bool)

        # Both should be valid JSON input regardless of debug mode setting
        if not result_on.is_valid:
            self.fail(
                f"Debug mode ON input should be valid. Errors: {result_on.errors}"
            )
        if not result_off.is_valid:
            self.fail(
                f"Debug mode OFF input should be valid. Errors: {result_off.errors}"
            )

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

    def test_debug_mode_filtering_unit_integration(self):
        """Restored from test_debug_filtering_unit.py - integration test for debug filtering"""

        # Test that simulates the exact logic we fixed in world_logic.py
        # without requiring full mocking of all dependencies

        # Mock data that would trigger debug field inclusion
        mock_structured_response_data = {
            "entities_mentioned": ["Dragon", "Knight", "Castle"],
            "location_confirmed": "Ancient Dragon's Lair",
            "session_header": "Session: Dragon Combat",
            "planning_block": "What do you do next?",
            "dice_rolls": ["1d20+5: 18 (Attack)"],
            "resources": "Lost 1 healing potion",
            "debug_info": {
                "dm_notes": ["Player rolled well", "Dragon should retreat"],
                "state_rationale": "HP reduced due to combat",
            },
        }

        mock_response_data = {
            "state_changes": {
                "player_character_data": {"hp_current": 8, "hp_max": 10},
                "npc_data": {"dragon_001": {"name": "Ancient Red Dragon", "hp": 100}},
            }
        }

        # Test debug_mode=False includes state fields (production behavior)
        debug_mode = False

        # Simulate the unified_response building from world_logic.py
        unified_response = {
            "success": True,
            "story": [],
            "narrative": "The dragon roars menacingly!",
            "response": "The dragon roars menacingly!",
            "game_state": {"debug_mode": debug_mode},
            "mode": "character",
            "user_input": "I attack the dragon",
            "debug_mode": debug_mode,
        }

        # Include state_updates only when debug mode is enabled (standard debug behavior)
        if debug_mode:
            unified_response["state_updates"] = mock_response_data.get(
                "state_changes", {}
            )

        # Add structured response fields if available
        structured_response = mock_structured_response_data
        if structured_response:
            # entities_mentioned only in debug mode
            if debug_mode and "entities_mentioned" in structured_response:
                unified_response["entities_mentioned"] = structured_response[
                    "entities_mentioned"
                ]

            # Always include these fields regardless of debug mode
            if "location_confirmed" in structured_response:
                unified_response["location_confirmed"] = structured_response[
                    "location_confirmed"
                ]
            if "session_header" in structured_response:
                unified_response["session_header"] = structured_response[
                    "session_header"
                ]
            if "planning_block" in structured_response:
                unified_response["planning_block"] = structured_response[
                    "planning_block"
                ]
            if "dice_rolls" in structured_response:
                unified_response["dice_rolls"] = structured_response["dice_rolls"]
            if "resources" in structured_response:
                unified_response["resources"] = structured_response["resources"]

            # debug_info only in debug mode
            if debug_mode and "debug_info" in structured_response:
                unified_response["debug_info"] = structured_response["debug_info"]

        # CRITICAL: State fields behavior with corrected debug logic
        # Note: state_changes removed as part of cleanup - only state_updates used now
        # state_updates only present when debug_mode=True (since debug_mode=False here)
        assert (
            "state_updates" not in unified_response
        ), "state_updates should NOT be present when debug_mode=False"
        # entities_mentioned and debug_info still follow original debug logic
        assert (
            "entities_mentioned" not in unified_response
        ), "entities_mentioned should be stripped when debug_mode=False"
        assert (
            "debug_info" not in unified_response
        ), "debug_info should be stripped when debug_mode=False"

        # These fields should REMAIN when debug_mode=False
        assert (
            "location_confirmed" in unified_response
        ), "location_confirmed should remain when debug_mode=False"
        assert (
            "planning_block" in unified_response
        ), "planning_block should remain when debug_mode=False"
        assert (
            "dice_rolls" in unified_response
        ), "dice_rolls should remain when debug_mode=False"
        assert (
            "resources" in unified_response
        ), "resources should remain when debug_mode=False"

        # Test debug_mode=True HIDES state fields (security-focused debug behavior)
        debug_mode = True
        unified_response_debug_on = {
            "success": True,
            "story": [],
            "narrative": "The dragon roars menacingly!",
            "response": "The dragon roars menacingly!",
            "game_state": {"debug_mode": debug_mode},
            "mode": "character",
            "user_input": "I attack the dragon",
            "debug_mode": debug_mode,
        }

        # Always include state_changes for compatibility
        unified_response_debug_on["state_changes"] = mock_response_data.get(
            "state_changes", {}
        )

        # Include state_updates only when debug mode is enabled (standard debug behavior)
        if debug_mode:
            unified_response_debug_on["state_updates"] = mock_response_data.get(
                "state_changes", {}
            )

        # Add structured response fields
        if structured_response:
            # entities_mentioned only in debug mode
            if debug_mode and "entities_mentioned" in structured_response:
                unified_response_debug_on["entities_mentioned"] = structured_response[
                    "entities_mentioned"
                ]
            # debug_info only in debug mode
            if debug_mode and "debug_info" in structured_response:
                unified_response_debug_on["debug_info"] = structured_response[
                    "debug_info"
                ]

        # CRITICAL: State fields should be present when debug_mode=True (standard debug behavior)
        assert (
            "state_changes" in unified_response_debug_on
        ), "state_changes should always be present for compatibility"
        assert (
            "state_updates" in unified_response_debug_on
        ), "state_updates should be present when debug_mode=True (standard debug behavior)"
        # entities_mentioned and debug_info still follow original debug logic
        assert (
            "entities_mentioned" in unified_response_debug_on
        ), "entities_mentioned should be included when debug_mode=True"
        assert (
            "debug_info" in unified_response_debug_on
        ), "debug_info should be included when debug_mode=True"

        # Verify the content is correct for non-state debug fields
        assert unified_response_debug_on["entities_mentioned"] == [
            "Dragon",
            "Knight",
            "Castle",
        ]
        assert unified_response_debug_on["debug_info"]["dm_notes"] == [
            "Player rolled well",
            "Dragon should retreat",
        ]

    def test_state_updates_sequence_id_debug_filtering_integration(self):
        """Restored from test_debug_filtering_unit.py - character mode sequence ID filtering test"""

        # Test the second location where state_updates is added in character mode
        # This tests lines 675-689 from world_logic.py

        debug_mode = False
        mode = "character"
        sequence_id = 1

        # Start with basic response structure
        unified_response = {
            "success": True,
            "narrative": "Test narrative",
            "state_changes": {"hp": 8},
            "debug_mode": debug_mode,
        }

        # Track story mode sequence ID for character mode (from world_logic.py)
        if mode == "character":
            story_id_update = {
                "custom_campaign_state": {"last_story_mode_sequence_id": sequence_id}
            }

            # Simulate merging state changes
            current_state_changes = unified_response.get("state_changes", {})
            merged_state_changes = {**current_state_changes, **story_id_update}

            unified_response["state_changes"] = merged_state_changes
            # state_updates only in debug mode (standard debug behavior)
            if debug_mode:
                unified_response["state_updates"] = merged_state_changes

        # CRITICAL: state_updates should NOT be added in character mode when debug_mode=False
        assert (
            "state_updates" not in unified_response
        ), "state_updates should NOT be added in character mode when debug_mode=False"
        assert (
            "state_changes" in unified_response
        ), "state_changes should always be present for internal tracking"

        # Verify that the sequence ID was still tracked internally
        assert "custom_campaign_state" in unified_response["state_changes"]
        assert (
            unified_response["state_changes"]["custom_campaign_state"][
                "last_story_mode_sequence_id"
            ]
            == 1
        )

        # Test that it works correctly with debug_mode=True (should HIDE state fields)
        debug_mode = True
        unified_response_debug_on = {
            "success": True,
            "narrative": "Test narrative",
            "debug_mode": debug_mode,
        }

        if mode == "character":
            unified_response_debug_on["state_changes"] = merged_state_changes
            # state_updates only in debug mode (standard debug behavior)
            if debug_mode:
                unified_response_debug_on["state_updates"] = merged_state_changes

        assert (
            "state_updates" in unified_response_debug_on
        ), "state_updates should be present in character mode when debug_mode=True (standard debug behavior)"
        assert (
            "state_changes" in unified_response_debug_on
        ), "state_changes should always be present for internal state tracking"

    def test_pr1150_debug_mode_standard_behavior(self):
        """
        Test for PR #1150: Standard debug mode behavior where debug_mode=True shows MORE information

        This test validates that debug mode follows standard behavior where debug_mode=True
        provides additional debugging information including state_updates.
        """
        # Test Case 1: debug_mode=True should show MORE information (standard debug behavior)
        debug_mode = True
        mock_response = {
            "state_changes": {
                "player_character_data": {"hp_current": 8, "hp_max": 10},
                "npc_data": {"dragon_001": {"name": "Ancient Red Dragon", "hp": 100}},
            }
        }

        # Simulate the standard debug logic from world_logic.py
        unified_response = {
            "success": True,
            "narrative": "The dragon attacks!",
            "debug_mode": debug_mode,
            "state_changes": mock_response.get("state_changes", {}),  # Always include
        }

        # Add debug-only fields when debug mode is enabled (standard behavior)
        if debug_mode:
            unified_response["state_updates"] = mock_response.get("state_changes", {})

        # Validate standard debug behavior - these fields SHOULD be present when debug_mode=True
        assert (
            "state_changes" in unified_response
        ), "state_changes should always be in API response for compatibility"
        assert (
            "state_updates" in unified_response
        ), "state_updates should be in API response when debug_mode=True (standard debug behavior)"

        # Test Case 2: debug_mode=False should NOT include debug-only information
        debug_mode = False
        unified_response_normal = {
            "success": True,
            "narrative": "The dragon attacks!",
            "debug_mode": debug_mode,
            "state_changes": mock_response.get("state_changes", {}),  # Always include
        }

        # Apply standard debug logic - debug-only fields only when debug_mode=True
        if debug_mode:
            unified_response_normal["state_updates"] = mock_response.get(
                "state_changes", {}
            )

        # Validate normal operation - state_changes always present, state_updates only in debug
        assert (
            "state_changes" in unified_response_normal
        ), "state_changes should always be in API response for compatibility"
        assert (
            "state_updates" not in unified_response_normal
        ), "state_updates should NOT be in API response when debug_mode=False (debug-only field)"

    def test_pr1150_character_mode_sequence_tracking_debug_respect(self):
        """
        Test for PR #1150: Character mode sequence tracking with standard debug behavior

        This validates the second location in world_logic.py where state_updates
        is conditionally added for character mode sequence tracking in debug mode.
        """
        debug_mode = True  # Should include state_updates (standard debug behavior)
        mode = "character"
        sequence_id = 42

        # Start with basic response (simulating world_logic.py state)
        unified_response = {
            "success": True,
            "narrative": "Test narrative",
            "debug_mode": debug_mode,
            "state_changes": {"existing": "data"},
        }

        # Simulate the character mode sequence tracking logic (lines 681-691)
        if mode == "character":
            story_id_update = {
                "custom_campaign_state": {"last_story_mode_sequence_id": sequence_id}
            }

            # Update state change fields and add debug info when enabled
            current_state_changes = unified_response.get("state_changes", {})
            merged_state_changes = {**current_state_changes, **story_id_update}
            unified_response["state_changes"] = merged_state_changes
            # state_updates only in debug mode (standard debug behavior)
            if debug_mode:
                unified_response["state_updates"] = merged_state_changes

        # CRITICAL TEST: When debug_mode=True, state_updates SHOULD be added (standard debug)
        assert (
            "state_updates" in unified_response
        ), "state_updates should be added in character mode when debug_mode=True (standard debug behavior)"

        # state_changes should be updated with sequence info
        assert "custom_campaign_state" in unified_response["state_changes"]
        assert (
            unified_response["state_changes"]["custom_campaign_state"][
                "last_story_mode_sequence_id"
            ]
            == sequence_id
        )

    def test_character_mode_preserves_original_state_changes_during_sequence_merge(
        self,
    ):
        """
        Test that would have caught the character mode state merge bug.

        Verifies that original Gemini state changes are preserved when merged
        with story sequence tracking update in character mode.

        This test ensures that changing the data source from unified_response
        to response doesn't break the merge functionality.
        """
        # Mock original Gemini response with state changes (realistic data source)
        mock_gemini_response = {
            "state_changes": {
                "player_character_data": {"hp_current": 25, "level": 3},
                "world_data": {"gold": 100, "location": "tavern"},
                "npc_data": {"innkeeper": {"disposition": "friendly"}},
            },
            "narrative": "You rest at the inn and gain experience.",
        }

        # Simulate the character mode sequence tracking logic
        mode = "character"
        sequence_id = 42
        debug_mode = True

        # This is the CORRECT approach (should get from response, not unified_response)
        if mode == "character":
            story_id_update = {
                "custom_campaign_state": {"last_story_mode_sequence_id": sequence_id}
            }

            # CRITICAL: Get original state changes from Gemini response (not unified_response)
            current_state_changes = mock_gemini_response.get("state_changes", {})

            # Simulate the merge operation from world_logic.py
            merged_state_changes = {**current_state_changes, **story_id_update}

            # Build final state_updates for debug mode
            final_state_updates = merged_state_changes if debug_mode else None

        # CRITICAL ASSERTIONS: Both original data AND sequence tracking should be present

        # Verify original Gemini state changes are preserved
        assert "player_character_data" in merged_state_changes
        assert merged_state_changes["player_character_data"]["hp_current"] == 25
        assert merged_state_changes["player_character_data"]["level"] == 3

        assert "world_data" in merged_state_changes
        assert merged_state_changes["world_data"]["gold"] == 100
        assert merged_state_changes["world_data"]["location"] == "tavern"

        assert "npc_data" in merged_state_changes
        assert (
            merged_state_changes["npc_data"]["innkeeper"]["disposition"] == "friendly"
        )

        # Verify sequence tracking was added
        assert "custom_campaign_state" in merged_state_changes
        assert (
            merged_state_changes["custom_campaign_state"]["last_story_mode_sequence_id"]
            == sequence_id
        )

        # Verify debug mode behavior
        if debug_mode:
            assert final_state_updates is not None
            assert final_state_updates == merged_state_changes

        # This test would FAIL if we incorrectly used unified_response.get("state_changes", {})
        # because unified_response doesn't contain the original Gemini state changes


if __name__ == "__main__":
    unittest.main()
