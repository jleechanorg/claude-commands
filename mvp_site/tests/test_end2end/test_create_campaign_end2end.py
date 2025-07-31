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
    @patch("google.genai.Client")
    def test_create_campaign_success(
        self, mock_genai_client_class, mock_firestore_client
    ):
        """Test successful campaign creation with full flow."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Set up fake Gemini client
        fake_genai_client = MagicMock()
        mock_genai_client_class.return_value = fake_genai_client

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

        # Make the API request
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

        # Verify Firestore operations
        # Check that campaign was created in users/{user_id}/campaigns
        users_collection = fake_firestore._collections.get("users")
        self.assertIsNotNone(users_collection)

        user_doc = users_collection._docs.get(self.test_user_id)
        self.assertIsNotNone(user_doc)

        campaigns_collection = user_doc._collections.get("campaigns")
        self.assertIsNotNone(campaigns_collection)

        # Should have one campaign
        campaign_docs = list(campaigns_collection._docs.values())
        self.assertEqual(len(campaign_docs), 1)

        # Check campaign data
        campaign_doc = campaign_docs[0]
        campaign_data = campaign_doc._data
        print(f"Campaign data keys: {list(campaign_data.keys())}")
        self.assertEqual(campaign_data["title"], "Epic Dragon Quest")
        # Note: user_id might not be stored in the document since it's in the path

        # Check that Gemini was called
        fake_genai_client.models.generate_content.assert_called_once()

    @patch("firebase_admin.firestore.client")
    @patch("google.genai.Client")
    def test_create_campaign_respects_debug_mode_setting(
        self, mock_genai_client_class, mock_firestore_client
    ):
        """Test that campaign creation respects debug mode setting from user preferences."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Set up fake Gemini client
        fake_genai_client = MagicMock()
        mock_genai_client_class.return_value = fake_genai_client

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
    @patch("google.genai.Client")
    def test_create_campaign_uses_default_debug_mode_when_no_user_setting(
        self, mock_genai_client_class, mock_firestore_client
    ):
        """Test that campaign creation uses default debug mode when user has no specific setting."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Set up fake Gemini client
        fake_genai_client = MagicMock()
        mock_genai_client_class.return_value = fake_genai_client

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


if __name__ == "__main__":
    unittest.main()
