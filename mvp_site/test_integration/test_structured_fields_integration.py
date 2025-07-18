#!/usr/bin/env python3
"""
Integration test for structured fields flow through main, gemini_service, and firestore_service.
Only mocks external services (Gemini API and Firestore database), not Python modules.
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import constants
from main import create_app


class TestStructuredFieldsIntegration(unittest.TestCase):
    """Integration test for structured fields through the full stack"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data
        self.user_id = "test-user-123"
        self.campaign_id = "test-campaign-456"

        # Headers for test authentication
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.user_id,
        }

        # Sample structured fields data
        self.structured_fields = {
            constants.FIELD_SESSION_HEADER: "Session 5: Dragon's Lair\nLevel 5 Fighter | HP: 45/60",
            constants.FIELD_PLANNING_BLOCK: "**Combat Options:**\n1. Attack with longsword\n2. Use second wind\n3. Action surge",
            constants.FIELD_DICE_ROLLS: [
                "Attack Roll: 1d20+8 = 22",
                "Damage: 2d6+5 = 13",
            ],
            constants.FIELD_RESOURCES: "HP: 45/60 | AC: 18 | Second Wind: Available",
            constants.FIELD_DEBUG_INFO: {
                "combat_round": 3,
                "enemy_hp": 85,
                "dm_notes": "Dragon is wounded",
            },
        }

    def tearDown(self):
        """Clean up after each test"""
        # Reset the app context
        if hasattr(self, "app_context"):
            self.app_context.pop()

    @patch("gemini_service.genai.Client")
    @patch("firestore_service.firestore")
    def test_structured_fields_full_flow(self, mock_firestore, mock_genai_client):
        """Test structured fields flow from API call through to storage"""
        # Mock Firestore database
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db

        # Mock user and campaign data
        mock_user_doc = {"id": self.user_id, "email": "test@example.com"}
        mock_campaign_doc = MagicMock()
        mock_campaign_doc.to_dict.return_value = {
            "id": self.campaign_id,
            "title": "Test Campaign",
            "game_state": {
                "player_character_data": {"name": "Test Hero", "hp_current": 45},
                "debug_mode": True,
            },
        }

        # Set up Firestore call chains
        mock_db.collection.return_value.document.return_value.get.return_value = (
            MagicMock(exists=True, to_dict=lambda: mock_user_doc)
        )
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_campaign_doc

        # Mock story collection for both reading and writing
        mock_story_collection = MagicMock()
        mock_story_collection.stream.return_value = []  # No existing story entries
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value = mock_story_collection

        # Mock Gemini API response with structured fields
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        # Create the response mock with text property
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "narrative": "The dragon roars in pain as your sword strikes true!",
                "session_header": self.structured_fields[
                    constants.FIELD_SESSION_HEADER
                ],
                "planning_block": self.structured_fields[
                    constants.FIELD_PLANNING_BLOCK
                ],
                "dice_rolls": self.structured_fields[constants.FIELD_DICE_ROLLS],
                "resources": self.structured_fields[constants.FIELD_RESOURCES],
                "debug_info": self.structured_fields[constants.FIELD_DEBUG_INFO],
                "entities_mentioned": ["dragon", "sword"],
                "location_confirmed": "Dragon's Lair",
                "state_updates": {"player_character_data": {"hp_current": 45}},
            }
        )

        # Set up the mock to return our response
        mock_client_instance.models.generate_content.return_value = mock_response

        # Mock the count_tokens method to avoid MagicMock arithmetic issues
        mock_token_count = MagicMock()
        mock_token_count.total_tokens = 1000
        mock_client_instance.models.count_tokens.return_value = mock_token_count

        # Make API request
        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            json={"input": "I attack the dragon with my sword!"},
        )

        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode("utf-8"))

        # Verify structured fields in API response
        self.assertEqual(
            response_data[constants.FIELD_SESSION_HEADER],
            self.structured_fields[constants.FIELD_SESSION_HEADER],
        )
        self.assertEqual(
            response_data[constants.FIELD_PLANNING_BLOCK],
            self.structured_fields[constants.FIELD_PLANNING_BLOCK],
        )
        self.assertEqual(
            response_data[constants.FIELD_DICE_ROLLS],
            self.structured_fields[constants.FIELD_DICE_ROLLS],
        )
        self.assertEqual(
            response_data[constants.FIELD_RESOURCES],
            self.structured_fields[constants.FIELD_RESOURCES],
        )
        self.assertEqual(
            response_data[constants.FIELD_DEBUG_INFO],
            self.structured_fields[constants.FIELD_DEBUG_INFO],
        )

        # Verify Firestore add was called with structured fields
        story_add_calls = mock_story_collection.add.call_args_list
        self.assertGreater(len(story_add_calls), 0)

        # Get the Gemini response story entry (should be the second call, after player input)
        gemini_story_data = None
        for call in story_add_calls:
            data = call[0][0]
            if data.get("actor") == "gemini":
                gemini_story_data = data
                break

        self.assertIsNotNone(gemini_story_data, "Gemini story entry not found")

        # Verify structured fields were stored
        self.assertEqual(
            gemini_story_data[constants.FIELD_SESSION_HEADER],
            self.structured_fields[constants.FIELD_SESSION_HEADER],
        )
        self.assertEqual(
            gemini_story_data[constants.FIELD_PLANNING_BLOCK],
            self.structured_fields[constants.FIELD_PLANNING_BLOCK],
        )
        self.assertEqual(
            gemini_story_data[constants.FIELD_DICE_ROLLS],
            self.structured_fields[constants.FIELD_DICE_ROLLS],
        )
        self.assertEqual(
            gemini_story_data[constants.FIELD_RESOURCES],
            self.structured_fields[constants.FIELD_RESOURCES],
        )
        self.assertEqual(
            gemini_story_data[constants.FIELD_DEBUG_INFO],
            self.structured_fields[constants.FIELD_DEBUG_INFO],
        )

    @patch("gemini_service.genai.Client")
    @patch("firestore_service.firestore")
    def test_structured_fields_partial_flow(self, mock_firestore, mock_genai_client):
        """Test when only some structured fields are present"""
        # Mock Firestore database
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db

        # Mock user and campaign
        mock_user_doc = {"id": self.user_id}
        mock_campaign_doc = MagicMock()
        mock_campaign_doc.to_dict.return_value = {
            "id": self.campaign_id,
            "game_state": {"debug_mode": False},
        }

        mock_db.collection.return_value.document.return_value.get.return_value = (
            MagicMock(exists=True, to_dict=lambda: mock_user_doc)
        )
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_campaign_doc

        mock_story_collection = MagicMock()
        mock_story_collection.stream.return_value = []
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value = mock_story_collection

        # Mock Gemini response with only some fields
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "narrative": "You explore the dungeon carefully.",
                "session_header": "Session 2: Exploration",
                "dice_rolls": ["Perception: 1d20+3 = 16"],
                # planning_block, resources, debug_info missing
                "entities_mentioned": [],
                "location_confirmed": "Dungeon Entrance",
            }
        )

        mock_client_instance.models.generate_content.return_value = mock_response

        # Mock token counting
        mock_token_count = MagicMock()
        mock_token_count.total_tokens = 1000
        mock_client_instance.models.count_tokens.return_value = mock_token_count

        # Make request
        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            json={"input": "I look around carefully"},
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode("utf-8"))

        # Verify only present fields are in response
        self.assertEqual(
            response_data[constants.FIELD_SESSION_HEADER], "Session 2: Exploration"
        )
        self.assertEqual(
            response_data[constants.FIELD_DICE_ROLLS], ["Perception: 1d20+3 = 16"]
        )
        self.assertEqual(response_data.get(constants.FIELD_PLANNING_BLOCK, ""), "")
        self.assertEqual(response_data.get(constants.FIELD_RESOURCES, ""), "")
        self.assertEqual(response_data.get(constants.FIELD_DEBUG_INFO, {}), {})

    @patch("gemini_service.genai.Client")
    @patch("firestore_service.firestore")
    def test_structured_fields_empty_flow(self, mock_firestore, mock_genai_client):
        """Test when no structured fields are present"""
        # Mock Firestore database
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db

        mock_user_doc = {"id": self.user_id}
        mock_campaign_doc = MagicMock()
        mock_campaign_doc.to_dict.return_value = {
            "id": self.campaign_id,
            "game_state": {},
        }

        mock_db.collection.return_value.document.return_value.get.return_value = (
            MagicMock(exists=True, to_dict=lambda: mock_user_doc)
        )
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_campaign_doc

        mock_story_collection = MagicMock()
        mock_story_collection.stream.return_value = []
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value = mock_story_collection

        # Mock Gemini response without structured fields
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "narrative": "A simple response without structured fields.",
                "entities_mentioned": [],
                "location_confirmed": "Unknown",
            }
        )

        mock_client_instance.models.generate_content.return_value = mock_response

        # Mock token counting
        mock_token_count = MagicMock()
        mock_token_count.total_tokens = 1000
        mock_client_instance.models.count_tokens.return_value = mock_token_count

        # Make request
        response = self.client.post(
            f"/api/campaigns/{self.campaign_id}/interaction",
            headers=self.test_headers,
            json={"input": "Simple action"},
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode("utf-8"))

        # Verify empty defaults
        self.assertEqual(response_data.get(constants.FIELD_SESSION_HEADER, ""), "")
        self.assertEqual(response_data.get(constants.FIELD_PLANNING_BLOCK, ""), "")
        self.assertEqual(response_data.get(constants.FIELD_DICE_ROLLS, []), [])
        self.assertEqual(response_data.get(constants.FIELD_RESOURCES, ""), "")
        self.assertEqual(response_data.get(constants.FIELD_DEBUG_INFO, {}), {})


if __name__ == "__main__":
    unittest.main()
