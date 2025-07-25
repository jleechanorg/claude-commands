"""
Test for the division by zero fix in GameState.validate_checkpoint_consistency
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from game_state import GameState


class TestGameStateDivisionByZero(unittest.TestCase):
    """Test cases for division by zero error fix in validate_checkpoint_consistency."""

    def test_validate_with_zero_hp_max_during_character_creation(self):
        """Test that validation handles hp_max=0 during character creation without crashing."""
        # Create a game state with hp_max=0 during character creation
        game_state = GameState(
            player_character_data={"hp_current": 0, "hp_max": 0},
            custom_campaign_state={"character_creation": {"in_progress": True}},
        )

        # This should not raise ZeroDivisionError and should not flag as invalid
        narrative = (
            "ApproveFoundation: Approve these choices and proceed to ability scores."
        )
        discrepancies = game_state.validate_checkpoint_consistency(narrative)

        # Should return empty list (no validation during character creation)
        self.assertEqual(discrepancies, [])

    def test_validate_with_zero_hp_max_outside_character_creation(self):
        """Test that validation detects invalid hp_max=0 outside character creation."""
        # Create a game state with hp_max=0 outside character creation
        game_state = GameState(player_character_data={"hp_current": 0, "hp_max": 0})

        # This should detect the invalid HP state
        narrative = "The character fights bravely."
        discrepancies = game_state.validate_checkpoint_consistency(narrative)

        # Should return a discrepancy about invalid HP state
        self.assertEqual(len(discrepancies), 1)
        self.assertIn("invalid HP state", discrepancies[0])
        self.assertIn("hp_max should not be 0", discrepancies[0])

    def test_validate_with_none_hp_values(self):
        """Test that validation handles None HP values gracefully."""
        game_state = GameState(
            player_character_data={"hp_current": None, "hp_max": None}
        )

        narrative = "The character takes damage."
        discrepancies = game_state.validate_checkpoint_consistency(narrative)

        # Should not crash and return empty list
        self.assertEqual(discrepancies, [])

    def test_validate_with_normal_hp_values(self):
        """Test that validation works correctly with normal HP values."""
        game_state = GameState(player_character_data={"hp_current": 5, "hp_max": 20})

        # Test narrative that mentions being wounded (which should match low HP)
        narrative = "The character is badly wounded and bleeding."
        discrepancies = game_state.validate_checkpoint_consistency(narrative)

        # Should not find discrepancies (low HP matches wounded narrative)
        self.assertEqual(discrepancies, [])

    def test_validate_detects_hp_narrative_mismatch(self):
        """Test that validation correctly detects HP/narrative mismatches."""
        game_state = GameState(player_character_data={"hp_current": 20, "hp_max": 20})

        # Narrative says wounded but HP is full
        narrative = "The character lies unconscious on the ground."
        discrepancies = game_state.validate_checkpoint_consistency(narrative)

        # Should detect the mismatch (may detect multiple related issues)
        self.assertGreaterEqual(len(discrepancies), 1)
        # Check that at least one discrepancy mentions unconsciousness
        unconscious_discrepancy_found = False
        for discrepancy in discrepancies:
            if "unconscious" in discrepancy and "20/20" in discrepancy:
                unconscious_discrepancy_found = True
                break
        self.assertTrue(
            unconscious_discrepancy_found,
            f"Expected unconsciousness discrepancy not found in: {discrepancies}",
        )

    def test_validate_with_partial_character_data(self):
        """Test validation with incomplete character data (only hp_current)."""
        game_state = GameState(
            player_character_data={
                "hp_current": 10
                # hp_max is missing
            }
        )

        narrative = "The character fights valiantly."
        discrepancies = game_state.validate_checkpoint_consistency(narrative)

        # Should not crash when hp_max is missing
        self.assertEqual(discrepancies, [])

    def test_validate_character_creation_scenario(self):
        """Test the exact scenario from the error: character creation with hp_max=0."""
        # Simulate character creation state
        game_state = GameState(
            player_character_data={
                "name": "New Character",
                "hp_current": 0,
                "hp_max": 0,
                "level": 1,
            },
            world_data={"campaign_state": "character_creation"},
        )

        # The exact user input that caused the error
        narrative = (
            "ApproveFoundation: Approve these choices and proceed to ability scores."
        )

        # This should not raise ZeroDivisionError
        try:
            discrepancies = game_state.validate_checkpoint_consistency(narrative)
            # Test passes if no exception raised
            self.assertIsInstance(discrepancies, list)
        except ZeroDivisionError:
            self.fail(
                "validate_checkpoint_consistency raised ZeroDivisionError with hp_max=0"
            )


if __name__ == "__main__":
    unittest.main()
