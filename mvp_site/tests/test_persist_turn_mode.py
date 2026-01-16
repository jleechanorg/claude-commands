"""TDD Test: AI response mode preservation in story entries.

RED Phase: This test verifies that when a turn is persisted to Firestore,
BOTH the user entry AND the AI response entry have the mode preserved.

Bug: Previously, AI responses were stored with mode=None regardless of
the actual mode (think/god/character), making it impossible to identify
think mode responses when the story was retrieved later.

Matrix Coverage:
- [think] User entry: mode='think', AI entry: mode='think' (EXPECTED)
- [god] User entry: mode='god', AI entry: mode='god' (EXPECTED)
- [character] User entry: mode='character', AI entry: mode='character' (EXPECTED)
- [combat] User entry: mode='combat', AI entry: mode='combat' (EXPECTED)
"""

import os
import unittest
from unittest.mock import MagicMock, patch, call

# Set test environment before imports
os.environ["TESTING_AUTH_BYPASS"] = "true"
os.environ["MOCK_SERVICES_MODE"] = "true"


class TestPersistTurnModePreservation(unittest.TestCase):
    """Test that _persist_turn_to_firestore preserves mode for AI responses."""

    def setUp(self):
        """Set up test fixtures."""
        self.user_id = "test_user_123"
        self.campaign_id = "test_campaign_456"
        self.user_input = "THINK: What should I do next?"
        self.ai_response_text = "You pause to consider your options..."
        self.structured_fields = {"planning_block": {"thinking": "Analysis..."}}
        self.updated_game_state = {"player_character_data": {"hp": 100}}

    @patch("mvp_site.world_logic.firestore_service")
    def test_think_mode_preserved_for_ai_response(self, mock_firestore):
        """RED: AI response should have mode='think' when user sends think mode request.

        This is the core bug fix - previously AI responses always had mode=None.
        """
        from mvp_site.world_logic import _persist_turn_to_firestore
        from mvp_site import constants

        # Execute the persist function with think mode
        _persist_turn_to_firestore(
            self.user_id,
            self.campaign_id,
            mode=constants.MODE_THINK,
            user_input=self.user_input,
            ai_response_text=self.ai_response_text,
            structured_fields=self.structured_fields,
            updated_game_state_dict=self.updated_game_state,
        )

        # Verify add_story_entry was called twice (user + AI)
        add_story_calls = mock_firestore.add_story_entry.call_args_list
        self.assertEqual(len(add_story_calls), 2, "Should call add_story_entry twice")

        # Extract the calls
        user_call = add_story_calls[0]
        ai_call = add_story_calls[1]

        # Verify USER entry has mode='think'
        # add_story_entry(user_id, campaign_id, actor, text, mode, structured_fields)
        # Index: 0=user_id, 1=campaign_id, 2=actor, 3=text, 4=mode
        user_call_args = user_call[0]  # positional args
        self.assertEqual(user_call_args[4], constants.MODE_THINK,
                         f"User entry mode should be 'think', got {user_call_args[4]}")

        # Verify AI entry has mode='think' (THIS IS THE BUG FIX)
        ai_call_args = ai_call[0]  # positional args
        self.assertEqual(ai_call_args[4], constants.MODE_THINK,
                         f"AI entry mode should be 'think', got {ai_call_args[4]}")

    @patch("mvp_site.world_logic.firestore_service")
    def test_god_mode_preserved_for_ai_response(self, mock_firestore):
        """RED: AI response should have mode='god' when user sends god mode request."""
        from mvp_site.world_logic import _persist_turn_to_firestore
        from mvp_site import constants

        _persist_turn_to_firestore(
            self.user_id,
            self.campaign_id,
            mode=constants.MODE_GOD,
            user_input="GOD MODE: Set time to midnight",
            ai_response_text="Time has been set to midnight.",
            structured_fields={},
            updated_game_state_dict=self.updated_game_state,
        )

        add_story_calls = mock_firestore.add_story_entry.call_args_list
        ai_call_args = add_story_calls[1][0]

        self.assertEqual(ai_call_args[4], constants.MODE_GOD,
                         f"AI entry mode should be 'god', got {ai_call_args[4]}")

    @patch("mvp_site.world_logic.firestore_service")
    def test_character_mode_preserved_for_ai_response(self, mock_firestore):
        """RED: AI response should have mode='character' for character actions."""
        from mvp_site.world_logic import _persist_turn_to_firestore
        from mvp_site import constants

        _persist_turn_to_firestore(
            self.user_id,
            self.campaign_id,
            mode=constants.MODE_CHARACTER,
            user_input="I attack the goblin",
            ai_response_text="You swing your sword...",
            structured_fields={"dice_rolls": [{"type": "attack"}]},
            updated_game_state_dict=self.updated_game_state,
        )

        add_story_calls = mock_firestore.add_story_entry.call_args_list
        ai_call_args = add_story_calls[1][0]

        self.assertEqual(ai_call_args[4], constants.MODE_CHARACTER,
                         f"AI entry mode should be 'character', got {ai_call_args[4]}")

    @patch("mvp_site.world_logic.firestore_service")
    def test_combat_mode_preserved_for_ai_response(self, mock_firestore):
        """RED: AI response should have mode='combat' for combat actions."""
        from mvp_site.world_logic import _persist_turn_to_firestore
        from mvp_site import constants

        _persist_turn_to_firestore(
            self.user_id,
            self.campaign_id,
            mode=constants.MODE_COMBAT,
            user_input="Attack with longsword",
            ai_response_text="Combat resolved...",
            structured_fields={},
            updated_game_state_dict=self.updated_game_state,
        )

        add_story_calls = mock_firestore.add_story_entry.call_args_list
        ai_call_args = add_story_calls[1][0]

        self.assertEqual(ai_call_args[4], constants.MODE_COMBAT,
                         f"AI entry mode should be 'combat', got {ai_call_args[4]}")

    @patch("mvp_site.world_logic.firestore_service")
    def test_mode_matrix_all_modes(self, mock_firestore):
        """RED: Matrix test - all modes should be preserved for AI responses."""
        from mvp_site.world_logic import _persist_turn_to_firestore
        from mvp_site import constants

        # Test matrix of all modes
        test_modes = [
            constants.MODE_THINK,
            constants.MODE_GOD,
            constants.MODE_CHARACTER,
            constants.MODE_COMBAT,
            constants.MODE_REWARDS,
            constants.MODE_INFO,
        ]

        for mode in test_modes:
            mock_firestore.reset_mock()

            _persist_turn_to_firestore(
                self.user_id,
                self.campaign_id,
                mode=mode,
                user_input=f"Test input for {mode}",
                ai_response_text=f"Test response for {mode}",
                structured_fields={},
                updated_game_state_dict=self.updated_game_state,
            )

            add_story_calls = mock_firestore.add_story_entry.call_args_list

            # Verify both user and AI entries have the correct mode
            user_call_args = add_story_calls[0][0]
            ai_call_args = add_story_calls[1][0]

            self.assertEqual(user_call_args[4], mode,
                             f"Matrix [{mode}]: User entry mode mismatch")
            self.assertEqual(ai_call_args[4], mode,
                             f"Matrix [{mode}]: AI entry mode mismatch - got {ai_call_args[4]}")


if __name__ == "__main__":
    unittest.main()
