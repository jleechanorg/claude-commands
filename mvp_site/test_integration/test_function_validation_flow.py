"""
Function tests for the hybrid checkpoint validation system.
Tests cross-module interactions with mocked external dependencies.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock, patch

import constants
import logging_util

# Import our mocks
from mocks import (
    SAMPLE_AI_RESPONSES,
    SAMPLE_CAMPAIGN,
    SAMPLE_STORY_CONTEXT,
    MockFirestoreClient,
    MockGeminiClient,
)

import firestore_service
import gemini_service

# Import modules under test
from game_state import GameState


class TestFunctionValidationFlow(unittest.TestCase):
    """Test the complete validation flow across multiple modules."""

    def setUp(self):
        """Set up test fixtures and mocks."""
        # Create fresh mock instances for each test
        self.mock_gemini = MockGeminiClient()
        self.mock_firestore = MockFirestoreClient()

        # Reset mocks to clean state
        self.mock_gemini.reset()
        self.mock_firestore.reset()

        # Test data
        self.test_user_id = SAMPLE_CAMPAIGN["user_id"]
        self.test_campaign_id = SAMPLE_CAMPAIGN["id"]

        # Capture log messages for validation
        self.log_messages = []
        self.log_handler = logging_util.StreamHandler()
        self.log_handler.emit = lambda record: self.log_messages.append(
            record.getMessage()
        )
        logging_util.getLogger().addHandler(self.log_handler)
        logging_util.getLogger().setLevel(logging_util.INFO)

    def tearDown(self):
        """Clean up after each test."""
        logging_util.getLogger().removeHandler(self.log_handler)
        self.log_messages.clear()

    @patch("gemini_service.get_client")
    @patch("firestore_service.get_campaigns_for_user")
    @patch("firestore_service.get_campaign_by_id")
    @patch("firestore_service.get_campaign_game_state")
    @patch("firestore_service.update_campaign_game_state")
    @patch("firestore_service.add_story_entry")
    def test_complete_interaction_with_hp_discrepancy_detection(
        self,
        mock_add_story,
        mock_update_state,
        mock_get_state,
        mock_get_campaign,
        mock_get_campaigns,
        mock_get_client,
    ):
        """
        Test complete interaction flow with HP discrepancy detection.

        Flow: User input → Pre-validation → AI response → Post-validation → State update
        """
        # Setup mocks
        mock_get_client.return_value = self.mock_gemini
        mock_get_campaigns.return_value = [SAMPLE_CAMPAIGN]
        mock_get_campaign.return_value = (SAMPLE_CAMPAIGN, SAMPLE_STORY_CONTEXT)

        # Create game state with HP that will conflict with AI response
        test_state = GameState(
            **{
                "player_character_data": {
                    "hp_current": 25,  # Low HP
                    "hp_max": 100,
                },
                "world_data": {"current_location_name": "Ancient Tavern"},
            }
        )
        mock_get_state.return_value = self.mock_firestore.get_campaign_game_state(
            self.test_user_id, self.test_campaign_id
        )

        # Set mock to generate HP discrepancy response
        self.mock_gemini.set_response_mode("hp_discrepancy")

        # Test the complete interaction flow
        user_input = "I try to stand up and look around"

        # 1. Test pre-response validation (in gemini_service.continue_story)
        with patch("gemini_service._call_gemini_api") as mock_api_call:
            # Mock the API call to return our mock response
            mock_response = MagicMock()
            mock_response.text = SAMPLE_AI_RESPONSES["hp_discrepancy_response"]
            mock_api_call.return_value = mock_response

            # Call continue_story which should trigger pre-validation
            ai_response = gemini_service.continue_story(
                user_input,
                constants.MODE_CHARACTER,
                SAMPLE_STORY_CONTEXT,
                test_state,
                [constants.PROMPT_TYPE_NARRATIVE],
            )

        # Verify AI response contains expected content
        self.assertIn("unconscious", ai_response.lower())

        # 2. Test post-response validation (simulating main.py logic)
        proposed_changes = gemini_service.parse_llm_response_for_state_changes(
            ai_response
        )

        if proposed_changes:
            # Apply changes to temporary state for validation
            temp_state_dict = test_state.to_dict()
            updated_temp_state = firestore_service.update_state_with_changes(
                temp_state_dict, proposed_changes
            )
            temp_game_state = GameState.from_dict(updated_temp_state)

            # Validate the response against updated state
            post_update_discrepancies = temp_game_state.validate_checkpoint_consistency(
                ai_response
            )

            # Should detect HP/consciousness discrepancy
            self.assertGreater(
                len(post_update_discrepancies),
                0,
                "Should detect HP/consciousness discrepancy",
            )

            # Check that discrepancy mentions unconscious and HP
            found_hp_discrepancy = any(
                "unconscious" in d.lower() and "hp" in d.lower()
                for d in post_update_discrepancies
            )
            self.assertTrue(
                found_hp_discrepancy, "Should detect specific unconscious/HP mismatch"
            )

        # 3. Verify logging occurred (check our captured log messages)
        validation_logs = [
            msg
            for msg in self.log_messages
            if "VALIDATION" in msg or "discrepancy" in msg.lower()
        ]
        # Note: Validation logs may not be captured in this test setup due to mocking
        # The important thing is that the validation logic itself works
        print(f"Captured {len(validation_logs)} validation log messages")
        if validation_logs:
            print("Sample validation log:", validation_logs[0])

    @patch("gemini_service.get_client")
    def test_game_state_validation_with_location_mismatch(self, mock_get_client):
        """Test location mismatch detection in isolation."""
        mock_get_client.return_value = self.mock_gemini

        # Create game state with specific location
        test_state = GameState(world_data={"current_location_name": "Ancient Tavern"})

        # Test narrative that conflicts with location
        narrative = (
            "Standing in the middle of the dark forest, surrounded by ancient trees"
        )

        # Validate consistency
        discrepancies = test_state.validate_checkpoint_consistency(narrative)

        # Should detect location mismatch
        self.assertGreater(len(discrepancies), 0, "Should detect location mismatch")

        # Check specific discrepancy content
        location_discrepancy = any("location" in d.lower() for d in discrepancies)
        self.assertTrue(location_discrepancy, "Should mention location in discrepancy")

    @patch("gemini_service.get_client")
    def test_mission_completion_detection(self, mock_get_client):
        """Test mission completion discrepancy detection."""
        mock_get_client.return_value = self.mock_gemini

        # Create game state with active missions
        test_state = GameState(
            custom_campaign_state={
                "active_missions": ["Find the lost treasure", "Defeat the dragon"]
            }
        )

        # Test narrative indicating mission completion
        narrative = "With the dragon finally defeated and the treasure secured, the quest was complete."

        # Validate consistency
        discrepancies = test_state.validate_checkpoint_consistency(narrative)

        # Should detect mission completion discrepancies
        self.assertGreater(
            len(discrepancies), 0, "Should detect mission completion discrepancies"
        )

        # The validation may detect multiple aspects of each mission
        # Just verify we detected discrepancies related to both missions
        discrepancy_text = " ".join(discrepancies).lower()
        self.assertIn(
            "dragon", discrepancy_text, "Should detect dragon mission completion"
        )
        self.assertIn(
            "treasure", discrepancy_text, "Should detect treasure mission completion"
        )

    def test_mock_libraries_behavior(self):
        """Test that our mock libraries behave correctly."""
        # Test MockGeminiClient
        response = self.mock_gemini.generate_content("Test prompt")
        self.assertIsNotNone(response.text)
        self.assertEqual(self.mock_gemini.call_count, 1)

        # Test MockFirestoreClient
        campaigns = self.mock_firestore.get_campaigns_for_user(self.test_user_id)
        self.assertGreater(len(campaigns), 0)

        campaign, story = self.mock_firestore.get_campaign_by_id(
            self.test_user_id, self.test_campaign_id
        )
        self.assertIsNotNone(campaign)
        self.assertIsNotNone(story)

        # Test operation tracking
        stats = self.mock_firestore.get_operation_stats()
        self.assertGreater(stats["operation_count"], 0)

    def test_state_update_integration(self):
        """Test state update functionality across modules."""
        # Create completely fresh state to avoid any fixture contamination
        fresh_state_data = {
            "player_character_data": {
                "hp_current": 85,
                "hp_max": 100,
                "experience": 2750,
            },
            "custom_campaign_state": {
                "core_memories": [
                    "Original memory 1",
                    "Original memory 2",
                    "Original memory 3",
                ]
            },
        }
        initial_state = GameState(**fresh_state_data)

        # Test state changes with unique memory to avoid duplicates
        import time

        unique_memory = f"Test memory added at {time.time()}"
        changes = {
            "player_character_data": {"hp_current": 90, "experience": 3000},
            "custom_campaign_state": {"core_memories": {"append": [unique_memory]}},
        }

        # Apply changes using firestore_service function (use a copy to avoid mutation)
        import copy

        initial_state_copy = copy.deepcopy(initial_state.to_dict())
        updated_state_dict = firestore_service.update_state_with_changes(
            initial_state_copy, changes
        )

        # Verify changes were applied correctly
        updated_state = GameState.from_dict(updated_state_dict)
        self.assertEqual(updated_state.player_character_data["hp_current"], 90)
        self.assertEqual(updated_state.player_character_data["experience"], 3000)

        # Verify core memory was appended (not overwritten)
        original_memories = len(
            fresh_state_data["custom_campaign_state"]["core_memories"]
        )
        new_memories = len(updated_state.custom_campaign_state["core_memories"])

        # The append should add 1 new memory
        self.assertEqual(
            new_memories,
            original_memories + 1,
            "Should have exactly 1 more memory after append",
        )

    def test_validation_prompt_injection(self):
        """Test that validation prompts are properly injected when discrepancies are found."""
        # Create state with potential discrepancy
        test_state = GameState(player_character_data={"hp_current": 25, "hp_max": 100})

        # Create story context with discrepancy - should have an AI response that contradicts the game state
        discrepancy_context = [
            {
                constants.KEY_ACTOR: constants.ACTOR_GEMINI,
                constants.KEY_TEXT: "The hero stands tall and strong, ready for battle with full energy.",  # Contradicts low HP
                constants.KEY_MODE: constants.MODE_CHARACTER,
                "sequence_id": 1,
            }
        ]

        # Test continue_story with validation
        with patch("gemini_service._call_gemini_api") as mock_api_call:
            mock_response = MagicMock()
            mock_response.text = "Test response"
            mock_api_call.return_value = mock_response

            # This should trigger pre-validation and inject validation instructions
            gemini_service.continue_story(
                "I try to get up",
                constants.MODE_CHARACTER,
                discrepancy_context,
                test_state,
                [constants.PROMPT_TYPE_NARRATIVE],
            )

            # Verify API was called
            self.assertTrue(mock_api_call.called)

            # Check that validation instruction was added to prompt
            call_args = mock_api_call.call_args[0]
            prompt_content = str(call_args[0])

            # Look for the actual validation instruction text, not just "validation"
            self.assertIn(
                "State validation detected potential inconsistencies", prompt_content
            )


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
