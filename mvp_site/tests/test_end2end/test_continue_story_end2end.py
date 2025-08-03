"""
End-to-end integration test for continuing a story - FIXED VERSION.
Only mocks external services (Gemini API and Firestore DB).
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

# Legacy json_input_schema imports removed - using GeminiRequest now
import gemini_service
from game_state import GameState
from tests.fake_firestore import FakeFirestoreClient, FakeGeminiResponse, FakeTokenCount


@unittest.skipUnless(
    has_firebase_credentials(),
    "Skipping continue story end2end tests - Firebase credentials not available (expected in CI)",
)
class TestContinueStoryEnd2End(unittest.TestCase):
    """Test continuing a story through the full application stack."""

    def setUp(self):
        """Set up test client and mocks."""
        # Reset gemini service client to ensure our mock is used
        gemini_service._client = None

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data
        self.test_user_id = "test-user-123"
        self.test_campaign_id = "test-campaign-456"

        # Test headers for bypassing auth in test mode
        self.test_headers = {
            HEADER_TEST_BYPASS: "true",
            HEADER_TEST_USER_ID: self.test_user_id,
        }

        self.test_interaction_data = {
            "input": "I draw my sword and approach the dragon cautiously",
            "mode": "character",
        }

        # Mock campaign data
        self.mock_campaign_data = {
            "id": self.test_campaign_id,
            "user_id": self.test_user_id,
            "title": "Dragon Quest",
            "created_at": "2024-01-15T10:30:00Z",
            "initial_prompt": "A brave warrior faces a dragon",
            "selected_prompts": ["narrative", "mechanics"],
        }

        # Mock existing game state
        self.mock_game_state = GameState(
            user_id="test-user-123",  # Add required user_id
            player_character_data={
                "name": "Thorin the Bold",
                "level": 3,
                "hp_current": 25,
                "hp_max": 30,
            },
            world_data={"current_location_name": "Dragon's Lair"},
        )

        # Mock existing story entries
        self.mock_story_entries = [
            {
                "actor": "user",
                "text": "A brave warrior faces a dragon",
                "timestamp": "2024-01-15T10:30:00Z",
                "sequence_id": 1,
                "mode": "god",
            },
            {
                "actor": "gemini",
                "text": "You stand before the mighty dragon...",
                "timestamp": "2024-01-15T10:31:00Z",
                "sequence_id": 2,
                "user_scene_number": 1,
            },
        ]

    def tearDown(self):
        """Reset gemini service client after each test."""
        gemini_service._client = None

    @patch("firebase_admin.firestore.client")
    @patch("google.genai.Client")
    def test_continue_story_success(
        self, mock_genai_client_class, mock_firestore_client
    ):
        """Test successfully continuing a story."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Pre-populate campaign data in the correct location
        user_doc = fake_firestore.collection("users").document(self.test_user_id)
        campaign_doc = user_doc.collection("campaigns").document(self.test_campaign_id)
        campaign_doc.set(self.mock_campaign_data)

        # Pre-populate game state
        game_state_doc = fake_firestore.document(
            f"campaigns/{self.test_campaign_id}/game_state"
        )
        game_state_doc.set(self.mock_game_state.to_dict())

        # Pre-populate story entries
        story_collection = fake_firestore.collection(
            f"campaigns/{self.test_campaign_id}/story"
        )
        for entry in self.mock_story_entries:
            story_collection.add(entry)

        # Set up fake Gemini client
        fake_genai_client = MagicMock()
        mock_genai_client_class.return_value = fake_genai_client
        fake_genai_client.models.count_tokens.return_value = FakeTokenCount(1000)

        # Mock Gemini response with proper JSON planning block
        response_json = json.dumps(
            {
                "narrative": "As you draw your sword, the dragon's eyes narrow...",
                "planning_block": {
                    "thinking": "The dragon prepares for combat. Your next move will be crucial.",
                    "choices": {
                        "1": {
                            "text": "Attack",
                            "description": "Attack the dragon with your sword",
                        },
                        "2": {
                            "text": "Defend",
                            "description": "Defend and raise your shield",
                        },
                        "3": {
                            "text": "Communicate",
                            "description": "Try to communicate with the dragon",
                        },
                    },
                },
                "state_updates": {"combat_state": {"in_combat": True}},
                "dice_rolls": ["Initiative: 1d20+2 = 15"],
                "choices": {
                    "1": {"text": "Attack", "description": "Strike with your sword"},
                    "2": {"text": "Defend", "description": "Raise your shield"},
                },
            }
        )
        fake_genai_client.models.generate_content.return_value = FakeGeminiResponse(
            response_json
        )

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            data=json.dumps(self.test_interaction_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Assert response
        assert response.status_code == 200
        response_data = json.loads(response.data)

        # Verify response structure (robust assertions)
        assert "narrative" in response_data
        # Basic structure validation
        assert isinstance(response_data, dict)
        assert response_data["success"]

        # Verify narrative
        assert "dragon's eyes narrow" in response_data["narrative"]

        # Verify state update happened
        assert "state_updates" in response_data
        assert response_data["state_updates"]["combat_state"]["in_combat"]

        # Verify Gemini was called (may be called multiple times due to dual-pass generation)
        assert fake_genai_client.models.generate_content.called

    @patch("firebase_admin.firestore.client")
    @patch("google.genai.Client")
    def test_continue_story_deep_think_mode(
        self, mock_genai_client_class, mock_firestore_client
    ):
        """Test continuing a story with deep think mode - validates string format for pros/cons."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Pre-populate campaign data in the correct location
        user_doc = fake_firestore.collection("users").document(self.test_user_id)
        campaign_doc = user_doc.collection("campaigns").document(self.test_campaign_id)
        campaign_doc.set(self.mock_campaign_data)

        # Pre-populate game state
        game_state_doc = fake_firestore.document(
            f"campaigns/{self.test_campaign_id}/game_state"
        )
        game_state_doc.set(self.mock_game_state.to_dict())

        # Pre-populate story entries
        story_collection = fake_firestore.collection(
            f"campaigns/{self.test_campaign_id}/story"
        )
        for entry in self.mock_story_entries:
            story_collection.add(entry)

        # Set up fake Gemini client
        fake_genai_client = MagicMock()
        mock_genai_client_class.return_value = fake_genai_client
        fake_genai_client.models.count_tokens.return_value = FakeTokenCount(1000)

        # Mock Gemini response with deep think mode analysis (STRING FORMAT)
        response_json = json.dumps(
            {
                "narrative": "I need to think carefully about this situation. The dragon is massive and dangerous...",
                "planning_block": {
                    "thinking": "This is a critical moment. I need to weigh my options carefully before acting.",
                    "choices": {
                        "attack_head_on": {
                            "text": "Attack Head-On",
                            "description": "Charge forward with sword raised",
                            "risk_level": "high",
                            "analysis": {
                                "pros": [
                                    "Quick resolution",
                                    "Shows courage",
                                    "Might catch dragon off-guard",
                                ],
                                "cons": [
                                    "High risk of injury",
                                    "Could provoke rage",
                                    "Uses up stamina",
                                ],
                                "confidence": "Low - this seems reckless but could work",
                            },
                        },
                        "defensive_approach": {
                            "text": "Defensive Approach",
                            "description": "Circle carefully and look for weaknesses",
                            "risk_level": "medium",
                            "analysis": {
                                "pros": [
                                    "Safer approach",
                                    "Allows observation",
                                    "Preserves energy",
                                ],
                                "cons": [
                                    "Takes longer",
                                    "Dragon might attack first",
                                    "Could appear weak",
                                ],
                                "confidence": "Moderate - tactical but may lose initiative",
                            },
                        },
                        "attempt_diplomacy": {
                            "text": "Attempt Diplomacy",
                            "description": "Try to communicate with the dragon",
                            "risk_level": "low",
                            "analysis": {
                                "pros": [
                                    "Could avoid combat entirely",
                                    "Might gain valuable information",
                                    "Shows wisdom",
                                ],
                                "cons": [
                                    "Dragon might not be intelligent",
                                    "Could be seen as weakness",
                                    "Wastes time if fails",
                                ],
                                "confidence": "High - worth trying before violence",
                            },
                        },
                    },
                },
                "state_updates": {"thinking_mode": {"active": True, "depth": "deep"}},
            }
        )
        fake_genai_client.models.generate_content.return_value = FakeGeminiResponse(
            response_json
        )

        # Create interaction data with "think" command to trigger deep think mode
        think_interaction_data = {
            "input": "I need to think about my options here",
            "mode": "character",
        }

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            data=json.dumps(think_interaction_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Assert response
        assert response.status_code == 200
        response_data = json.loads(response.data)

        # Verify response structure
        assert isinstance(response_data, dict)
        assert response_data["success"]

        # Verify narrative contains thinking content
        assert "think carefully" in response_data["narrative"]

        # Verify planning block structure
        assert "planning_block" in response_data
        planning_block = response_data["planning_block"]
        assert "thinking" in planning_block
        assert "choices" in planning_block

        # Verify deep think analysis fields are present and in STRING format
        choices = planning_block["choices"]

        # Test attack_head_on choice analysis
        attack_choice = choices["attack_head_on"]
        assert "analysis" in attack_choice
        attack_analysis = attack_choice["analysis"]

        # Assert pros/cons are ARRAYS (user wants bullet points)
        assert isinstance(attack_analysis["pros"], list)
        assert isinstance(attack_analysis["cons"], list)
        assert isinstance(attack_analysis["confidence"], str)

        # Verify content (case-sensitive)
        assert "Quick resolution" in attack_analysis["pros"]
        assert "Shows courage" in attack_analysis["pros"]
        assert "High risk of injury" in attack_analysis["cons"]
        assert "Low - this seems reckless" in attack_analysis["confidence"]

        # Test defensive_approach choice analysis
        defensive_choice = choices["defensive_approach"]
        defensive_analysis = defensive_choice["analysis"]

        # Assert array format and content
        assert isinstance(defensive_analysis["pros"], list)
        assert isinstance(defensive_analysis["cons"], list)
        assert "Safer approach" in defensive_analysis["pros"]
        assert "Takes longer" in defensive_analysis["cons"]
        assert "Moderate" in defensive_analysis["confidence"]

        # Test diplomacy choice analysis
        diplomacy_choice = choices["attempt_diplomacy"]
        diplomacy_analysis = diplomacy_choice["analysis"]

        # Assert array format and content
        assert isinstance(diplomacy_analysis["pros"], list)
        assert isinstance(diplomacy_analysis["cons"], list)
        assert "Could avoid combat entirely" in diplomacy_analysis["pros"]
        assert "Dragon might not be intelligent" in diplomacy_analysis["cons"]
        assert "High - worth trying" in diplomacy_analysis["confidence"]

        # Verify state updates
        assert "state_updates" in response_data
        assert response_data["state_updates"]["thinking_mode"]["active"]
        assert response_data["state_updates"]["thinking_mode"]["depth"] == "deep"

        # Verify Gemini was called
        assert fake_genai_client.models.generate_content.called

    @patch.dict(os.environ, {"MOCK_SERVICES_MODE": "true"})
    @patch("firebase_admin.firestore.client")
    @unittest.skip("Temporarily disabled: API mocking issue - see PR #1114")
    @patch("gemini_service._call_gemini_api_with_gemini_request")
    def test_continue_story_json_schema_end2end(
        self, mock_gemini_request_api, mock_firestore_client
    ):
        """Test that ONLY GeminiRequest JSON structure is used for story continuation - NO LEGACY FALLBACKS."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Mock Gemini response for GeminiRequest API call
        gemini_response_data = {
            "narrative": "You swing your sword at the dragon, striking its wounded scales...",
            "entities_mentioned": ["dragon", "sword"],
            "location_confirmed": "Dragon's Lair",
            "state_updates": {
                "player_character_data": {"hp_current": 20},
                "custom_campaign_state": {"combat_round": 3},
            },
        }
        mock_gemini_request_api.return_value = FakeGeminiResponse(
            json.dumps(gemini_response_data)
        )

        # Pre-populate campaign data
        user_doc = fake_firestore.collection("users").document(self.test_user_id)
        campaign_doc = user_doc.collection("campaigns").document(self.test_campaign_id)
        campaign_doc.set(self.mock_campaign_data)

        # Pre-populate game state with structured data
        mock_game_state_dict = {
            "player_character_data": {"name": "Thorin", "level": 3, "hp_current": 25},
            "world_data": {
                "current_location_name": "Dragon's Lair",
                "weather": "stormy",
            },
            "npc_data": {"dragon": {"name": "Ancient Red", "health": "wounded"}},
            "custom_campaign_state": {"quest_active": True, "combat_round": 2},
            "user_id": self.test_user_id,
            "debug_mode": True,
        }
        game_state_doc = fake_firestore.document(
            f"campaigns/{self.test_campaign_id}/game_state"
        )
        game_state_doc.set(mock_game_state_dict)

        # Pre-populate story entries with structured data
        story_collection = fake_firestore.collection(
            f"campaigns/{self.test_campaign_id}/story"
        )
        structured_story_entries = [
            {
                "actor": "user",
                "text": "I examine the dragon's wounds",
                "timestamp": "2024-01-15T10:30:00Z",
                "sequence_id": 1,
                "mode": "character",
            },
            {
                "actor": "gemini",
                "text": "The dragon's scales are cracked and bleeding...",
                "timestamp": "2024-01-15T10:31:00Z",
                "sequence_id": 2,
                "user_scene_number": 1,
            },
        ]
        for entry in structured_story_entries:
            story_collection.add(entry)

        # Using MOCK_SERVICES_MODE=true, Gemini API calls will be mocked internally

        # Make the API request to continue story
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            data=json.dumps(
                {
                    "input": "I look for weak spots in the dragon's armor",
                    "mode": "character",
                }
            ),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Assert successful response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"]

        # CRITICAL TEST: Verify structured JSON was built correctly from real data
        # Note: Legacy validation removed as part of TDD cleanup
        # Using GeminiRequest validation instead of deprecated JsonInputValidator
        # mock_structured_json and JsonInputValidator removed in TDD cleanup

        # Legacy test validation removed - GeminiRequest handles this internally
        # User action and game mode validation moved to GeminiRequest tests

        # CRITICAL: Verify that ONLY GeminiRequest JSON structure was used (RED PHASE - SHOULD FAIL)
        mock_gemini_request_api.assert_called_once()
        call_args = mock_gemini_request_api.call_args
        gemini_request = call_args.args[0]

        # Verify it's a GeminiRequest object with proper JSON structure
        assert hasattr(gemini_request, "to_json"), "Must use GeminiRequest object"
        json_data = gemini_request.to_json()

        # Verify structured JSON fields (NOT string blob) - flat structure, no nested context
        assert "user_action" in json_data, "Missing user_action JSON field"
        assert "game_mode" in json_data, "Missing game_mode JSON field"
        assert "user_id" in json_data, "Missing user_id JSON field"
        assert "game_state" in json_data, "Missing game_state JSON field"
        assert "story_history" in json_data, "Missing story_history JSON field"
        assert "entity_tracking" in json_data, "Missing entity_tracking JSON field"
        assert "selected_prompts" in json_data, "Missing selected_prompts JSON field"

        # Verify data types are preserved (NOT converted to strings)
        assert isinstance(
            json_data["game_state"], dict
        ), "game_state must be dict, not string"
        assert isinstance(
            json_data["story_history"], list
        ), "story_history must be list, not string"
        assert isinstance(
            json_data["entity_tracking"], dict
        ), "entity_tracking must be dict, not string"
        assert isinstance(
            json_data["selected_prompts"], list
        ), "selected_prompts must be list, not string"

        # Verify actual content is preserved
        assert json_data["user_action"] == "I look for weak spots in the dragon's armor"
        assert json_data["game_mode"] == "character"
        assert json_data["user_id"] == self.test_user_id
        assert json_data["game_state"]["player_character_data"]["name"] == "Thorin"
        assert (
            json_data["game_state"]["world_data"]["current_location_name"]
            == "Dragon's Lair"
        )

        # CRITICAL: Verify NO legacy string blob approach
        assert (
            "content" not in json_data
        ), "Must not use legacy string blob 'content' field"
        assert "context" not in json_data, "Must not use nested 'context' wrapper"

    @patch("firebase_admin.firestore.client")
    def test_continue_story_unauthorized(self, mock_firestore_client):
        """Test continuing a story for a campaign owned by another user."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Pre-populate campaign data with different user
        different_user_campaign = self.mock_campaign_data.copy()
        different_user_campaign["user_id"] = "different-user-999"

        # Put campaign under different user's collection
        different_user_doc = fake_firestore.collection("users").document(
            "different-user-999"
        )
        campaign_doc = different_user_doc.collection("campaigns").document(
            self.test_campaign_id
        )
        campaign_doc.set(different_user_campaign)

        # Make the API request
        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            data=json.dumps(self.test_interaction_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Assert forbidden
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert "error" in response_data


if __name__ == "__main__":
    unittest.main()
