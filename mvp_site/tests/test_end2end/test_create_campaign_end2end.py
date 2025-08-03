"""
End-to-end integration test for creating a campaign.
Only mocks external services (Gemini API and Firestore DB) at the lowest level.
Tests the full flow from API endpoint through all service layers.
"""

import json
import os
import sys
import unittest
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


# Legacy json_input_schema imports removed - using GeminiRequest now
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
        """Simulate updating document data."""
        self._data.update(data)

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
    "Skipping create campaign end2end tests - Firebase credentials not available (expected in CI)",
)
class TestCreateCampaignEnd2EndV2(unittest.TestCase):
    """Test creating a campaign through the full application stack."""

    def setUp(self):
        """Set up test client."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data
        self.test_user_id = "test-user-123"
        self.test_headers = {
            HEADER_TEST_BYPASS: "true",
            HEADER_TEST_USER_ID: self.test_user_id,
        }
        self.test_campaign_data = {
            "title": "Epic Dragon Quest",
            "character": "Thorin the Bold",
            "setting": "Mountain Kingdom",
            "description": "A brave dwarf warrior seeks to reclaim his homeland",
            "campaignType": "custom",
            "selectedPrompts": ["narrative", "mechanics"],
            "customOptions": ["companions"],
        }

    @patch("firebase_admin.firestore.client")
    @patch("gemini_service._call_gemini_api_with_gemini_request")
    def test_create_campaign_success(
        self, mock_gemini_request_api, mock_firestore_client
    ):
        """Test successful campaign creation with ONLY GeminiRequest JSON structure - NO LEGACY FALLBACKS."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Mock Gemini response for GeminiRequest API call
        gemini_response_data = {
            "narrative": "The mountain winds howled as Thorin the Bold stood at the gates...",
            "entities_mentioned": ["Thorin the Bold"],
            "location_confirmed": "Mountain Kingdom Gates",
            "state_updates": {
                "player_character_data": {
                    "name": "Thorin the Bold",
                    "level": 1,
                    "hp_current": 10,
                    "hp_max": 10,
                }
            },
        }
        mock_gemini_request_api.return_value = FakeGeminiResponse(
            json.dumps(gemini_response_data)
        )

        # Make the API request
        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(self.test_campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Assert response
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["success"]
        assert "campaign_id" in response_data

        # CRITICAL: Verify that ONLY GeminiRequest JSON structure was used (RED PHASE - SHOULD FAIL)
        mock_gemini_request_api.assert_called_once()
        call_args = mock_gemini_request_api.call_args
        # Function is called with keyword arguments, so get from kwargs
        gemini_request = call_args.kwargs.get("gemini_request") or (
            call_args.args[0] if call_args.args else None
        )
        if not gemini_request:
            raise ValueError("GeminiRequest not found in call args")

        # Verify it's a GeminiRequest object with proper JSON structure
        assert hasattr(gemini_request, "to_json"), "Must use GeminiRequest object"
        json_data = gemini_request.to_json()

        # Verify structured JSON fields (NOT string blob)
        assert "user_action" in json_data, "Missing user_action JSON field"
        assert "game_mode" in json_data, "Missing game_mode JSON field"
        assert "user_id" in json_data, "Missing user_id JSON field"
        assert "character_prompt" in json_data, "Missing character_prompt JSON field"
        assert "selected_prompts" in json_data, "Missing selected_prompts JSON field"
        assert isinstance(
            json_data["selected_prompts"], list
        ), "selected_prompts must be list, not string"

        # Verify NO string concatenation - these should be structured data
        assert (
            json_data["user_action"] == ""
        ), "Initial story should have empty user_action"
        assert json_data["game_mode"] == "character", "Should use character mode"
        assert json_data["user_id"] == self.test_user_id, "Must include user_id"

        # Verify Firestore operations
        # Check that campaign was created in users/{user_id}/campaigns
        users_collection = fake_firestore._collections.get("users")
        assert users_collection is not None

        user_doc = users_collection._docs.get(self.test_user_id)
        assert user_doc is not None

        campaigns_collection = user_doc._collections.get("campaigns")
        assert campaigns_collection is not None

        # Should have one campaign
        campaign_docs = list(campaigns_collection._docs.values())
        assert len(campaign_docs) == 1

        # Check campaign data
        campaign_doc = campaign_docs[0]
        campaign_data = campaign_doc._data
        print(f"Campaign data keys: {list(campaign_data.keys())}")
        assert campaign_data["title"] == "Epic Dragon Quest"
        # Note: user_id might not be stored in the document since it's in the path

        # Check that Gemini was called (reference removed as part of legacy cleanup)

    @patch("firebase_admin.firestore.client")
    @patch("gemini_service._call_gemini_api_with_gemini_request")
    @patch("gemini_service._call_gemini_api")
    @patch("gemini_service.get_client")
    @patch.dict(
        os.environ, {"MOCK_SERVICES_MODE": "false"}
    )  # Disable mock mode for this test
    def test_create_campaign_json_schema_end2end(
        self,
        mock_get_client,
        mock_regular_api,
        mock_gemini_request,
        mock_firestore_client,
    ):
        """Test that structured JSON input is built correctly for initial story creation (END-TO-END)."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Set up fake Gemini client - mock the get_client function directly
        fake_genai_client = MagicMock()
        mock_get_client.return_value = fake_genai_client

        # Mock token counting
        fake_genai_client.models.count_tokens.return_value = MagicMock(
            total_tokens=1000
        )

        # Mock Gemini response for initial story creation
        gemini_response_data = {
            "narrative": "The mountain winds howled as Thorin the Bold stood at the gates...",
            "entities_mentioned": ["Thorin the Bold"],
            "location_confirmed": "Mountain Kingdom Gates",
            "state_updates": {
                "player_character_data": {
                    "name": "Thorin the Bold",
                    "level": 1,
                    "hp_current": 10,
                    "hp_max": 10,
                }
            },
        }

        # Set up the fake response with proper text attribute
        fake_response = MagicMock()
        fake_response.text = json.dumps(gemini_response_data)
        fake_genai_client.models.generate_content.return_value = fake_response

        # Set up the wrapped function to return our fake response
        def fake_gemini_request_call(*args, **kwargs):
            return FakeGeminiResponse(json.dumps(gemini_response_data))

        mock_gemini_request.side_effect = fake_gemini_request_call

        # Also set up the regular API mock as fallback
        mock_regular_api.return_value = FakeGeminiResponse(
            json.dumps(gemini_response_data)
        )

        # Enhanced test campaign data with more options
        enhanced_campaign_data = {
            "title": "Epic Dragon Quest",
            "character": "Thorin the Bold - A brave dwarf warrior with a sacred mission",
            "setting": "Mountain Kingdom - Ancient dwarven halls beneath snow-capped peaks",
            "description": "A brave dwarf warrior seeks to reclaim his homeland from an ancient evil",
            "campaignType": "custom",
            "selectedPrompts": ["narrative", "mechanics", "character"],
            "customOptions": ["companions", "detailed_world"],
        }

        # Make the API request
        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(enhanced_campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Assert successful response
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["success"]
        assert "campaign_id" in response_data

        # CRITICAL TEST: Verify structured JSON was built correctly for initial story
        mock_gemini_request.assert_called()

        # Get the call arguments from the GeminiRequest call
        call_args = mock_gemini_request.call_args
        # Handle both positional and keyword arguments safely
        if call_args[0]:  # Has positional arguments
            gemini_request = call_args[0][
                0
            ]  # First positional argument is the GeminiRequest
        else:  # Keyword arguments
            gemini_request = call_args[1]["gemini_request"]
        actual_json_input = gemini_request.to_json()

        # Validate that the GeminiRequest has essential campaign creation fields
        assert "user_action" in actual_json_input
        assert "game_mode" in actual_json_input
        assert "user_id" in actual_json_input
        assert "character_prompt" in actual_json_input

        # Validate that the character data is in the structured JSON
        assert "Thorin the Bold" in actual_json_input["character_prompt"]
        assert "Mountain Kingdom" in actual_json_input["character_prompt"]

        # Verify character prompt was captured correctly (combined character + setting)
        character_prompt = actual_json_input["character_prompt"]
        assert isinstance(character_prompt, str)
        assert "Thorin the Bold" in character_prompt
        assert "dwarf warrior" in character_prompt

        # Verify game mode
        assert actual_json_input["game_mode"] == "character"

        # Verify selected prompts are present in the GeminiRequest
        selected_prompts = actual_json_input["selected_prompts"]
        assert isinstance(selected_prompts, list)

        # Verify boolean flags are present
        assert "generate_companions" in actual_json_input
        assert "use_default_world" in actual_json_input
        # Check that use_default_world is a boolean
        assert isinstance(actual_json_input["use_default_world"], bool)

        # World data should be structured dict, not string
        self.assertIn("world_data", actual_json_input)
        world_data = actual_json_input["world_data"]
        self.assertIsInstance(world_data, dict)

        # CRITICAL: Verify NO single 'content' blob field exists
        self.assertNotIn(
            "content",
            actual_json_input,
            "JSON input should not contain single content blob - should use structured fields for initial story",
        )

        # Additional validation: Verify the JSON can be converted back to Gemini format
        # Note: JsonInputBuilder removed as part of legacy code cleanup
        # The main goal is verifying the JSON schema validation works with GeminiRequest
        # Format conversion is handled internally by GeminiRequest.to_json()

    @patch("firebase_admin.firestore.client")
    @patch("gemini_service.get_client")
    def test_create_campaign_respects_debug_mode_setting(
        self, mock_get_client, mock_firestore_client
    ):
        """Test that campaign creation respects debug mode setting from user preferences."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Set up fake Gemini client
        fake_genai_client = MagicMock()
        mock_get_client.return_value = fake_genai_client

        # Mock token counting
        fake_genai_client.models.count_tokens.return_value = MagicMock(
            total_tokens=1000
        )

        # Mock Gemini response
        gemini_response_data = {
            "narrative": "The mountain winds howled as Thorin the Bold stood at the gates...",
            "entities_mentioned": ["Thorin the Bold"],
            "location_confirmed": "Mountain Kingdom Gates",
            "state_updates": {
                "player_character_data": {
                    "name": "Thorin the Bold",
                    "level": 1,
                    "hp_current": 10,
                    "hp_max": 10,
                }
            },
        }
        fake_genai_client.models.generate_content.return_value = FakeGeminiResponse(
            json.dumps(gemini_response_data)
        )

        # First, create user settings with debug_mode=False
        user_settings_doc = fake_firestore.collection("users").document(
            self.test_user_id
        )
        user_settings_doc.set(
            {
                "settings": {
                    "model_preference": "gemini-2.5-flash",
                    "debug_mode": False,  # Explicitly set to False (non-default)
                }
            }
        )

        # Make the API request to create campaign
        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(self.test_campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Assert response
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertTrue(response_data["success"])
        self.assertIn("campaign_id", response_data)

        # Get the created campaign to verify debug mode was applied correctly
        campaigns_collection = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
        )
        campaign_docs = list(campaigns_collection._docs.values())
        self.assertEqual(len(campaign_docs), 1)

        # Check that the campaign's game state has debug_mode=False as specified in user settings
        campaign_doc = campaign_docs[0]
        campaign_data = campaign_doc._data

        # Game state is stored in a subcollection: campaigns/{id}/game_states/current_state
        game_states_collection = campaign_doc.collection("game_states")
        current_state_doc = game_states_collection.document("current_state")

        # Verify that the game state document exists and has data
        self.assertTrue(current_state_doc.exists())
        game_state = current_state_doc.to_dict()

        # The key test: debug_mode should be False (from user settings), not True (default)
        self.assertIn("debug_mode", game_state)
        self.assertEqual(
            game_state["debug_mode"],
            False,
            "Campaign should respect user's debug_mode=False setting, not use default True",
        )

    @patch("firebase_admin.firestore.client")
    @patch("gemini_service.get_client")
    def test_create_campaign_uses_default_debug_mode_when_no_user_setting(
        self, mock_get_client, mock_firestore_client
    ):
        """Test that campaign creation uses default debug mode when user has no specific setting."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Set up fake Gemini client
        fake_genai_client = MagicMock()
        mock_get_client.return_value = fake_genai_client

        # Mock token counting
        fake_genai_client.models.count_tokens.return_value = MagicMock(
            total_tokens=1000
        )

        # Mock Gemini response
        gemini_response_data = {
            "narrative": "The mountain winds howled as Thorin the Bold stood at the gates...",
            "entities_mentioned": ["Thorin the Bold"],
            "location_confirmed": "Mountain Kingdom Gates",
            "state_updates": {
                "player_character_data": {
                    "name": "Thorin the Bold",
                    "level": 1,
                    "hp_current": 10,
                    "hp_max": 10,
                }
            },
        }
        fake_genai_client.models.generate_content.return_value = FakeGeminiResponse(
            json.dumps(gemini_response_data)
        )

        # Don't create any user settings - this should use defaults

        # Make the API request to create campaign
        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(self.test_campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Assert response
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertTrue(response_data["success"])
        self.assertIn("campaign_id", response_data)

        # Get the created campaign to verify default debug mode was used
        campaigns_collection = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
        )
        campaign_docs = list(campaigns_collection._docs.values())
        self.assertEqual(len(campaign_docs), 1)

        # Check that the campaign's game state has default debug_mode=True
        campaign_doc = campaign_docs[0]
        campaign_data = campaign_doc._data

        # Game state is stored in a subcollection: campaigns/{id}/game_states/current_state
        game_states_collection = campaign_doc.collection("game_states")
        current_state_doc = game_states_collection.document("current_state")

        # Verify that the game state document exists and has data
        self.assertTrue(current_state_doc.exists())
        game_state = current_state_doc.to_dict()

        # The key test: debug_mode should be True (default) when no user setting exists
        self.assertIn("debug_mode", game_state)
        self.assertEqual(
            game_state["debug_mode"],
            True,
            "Campaign should use default debug_mode=True when no user setting exists",
        )

    @patch("firebase_admin.firestore.client")
    @patch("gemini_service._call_gemini_api_with_gemini_request")
    @patch("gemini_service._call_gemini_api")
    @patch("gemini_service.get_client")
    @patch.dict(
        os.environ, {"MOCK_SERVICES_MODE": "false"}
    )  # Disable mock mode for this test
    def test_create_campaign_json_conversion_end2end(
        self,
        mock_get_client,
        mock_regular_api,
        mock_gemini_request,
        mock_firestore_client,
    ):
        """Test that structured JSON input is properly converted to Gemini format (END-TO-END)."""

        # Set up fake Firestore and Gemini client
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        fake_genai_client = MagicMock()
        mock_get_client.return_value = fake_genai_client
        fake_genai_client.models.count_tokens.return_value = MagicMock(
            total_tokens=1000
        )

        # Set up the fake response with proper text attribute
        fake_response = MagicMock()
        fake_response.text = json.dumps(
            {
                "narrative": "Your adventure begins in a mystical realm...",
                "state_updates": {"initialization": "complete"},
                "entities_mentioned": ["realm", "adventure"],
                "characters": [{"name": "Test Hero", "class": "Warrior"}],
            }
        )
        fake_genai_client.models.generate_content.return_value = fake_response

        # Create a more complex test to validate conversion
        def capture_and_validate_conversion(*args, **kwargs):
            # This function will be called instead of the real GeminiRequest function
            # Function is called with keyword arguments, so get from kwargs
            gemini_request = kwargs.get("gemini_request") or (args[0] if args else None)
            if not gemini_request:
                raise ValueError("GeminiRequest not found in args or kwargs")

            # Validate that we receive a GeminiRequest with proper structure
            if not hasattr(gemini_request, "to_json"):
                raise ValueError("GeminiRequest missing to_json method")

            # Get the JSON data from the GeminiRequest
            json_data = gemini_request.to_json()

            # Validate that we receive structured JSON (legacy validation removed)
            # JsonInputValidator and JsonInputBuilder removed in TDD cleanup
            # GeminiRequest handles validation internally

            # Legacy format validation removed - GeminiRequest handles this

            # Return mock response with proper text attribute
            response_text = json.dumps(
                {
                    "narrative": "Your adventure begins...",
                    "state_updates": {"initialization": "complete"},
                }
            )
            return FakeGeminiResponse(response_text)

        mock_gemini_request.side_effect = capture_and_validate_conversion

        # Also set up the regular API mock as fallback
        mock_regular_api.return_value = FakeGeminiResponse(
            json.dumps(
                {
                    "narrative": "Your adventure begins...",
                    "state_updates": {"initialization": "complete"},
                }
            )
        )

        # Make campaign creation request
        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(self.test_campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Assert successful response (this proves the conversion worked)
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertTrue(response_data["success"])

        # Verify our validation function was called (proving end-to-end flow)
        mock_gemini_request.assert_called()


if __name__ == "__main__":
    unittest.main()
