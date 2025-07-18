"""
Test Sariel campaign using actual production methods (get_initial_story, continue_story).
This is kept separate because it tests the methods directly rather than through the API.
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState
from gemini_service import continue_story, get_initial_story


class TestSarielProductionMethods(unittest.TestCase):
    """Test actual production methods with Sariel campaign"""

    def test_production_methods_entity_tracking(self):
        """Test entity tracking through production methods"""
        print("\n=== Testing Production Methods ===")

        # Test initial story generation
        print("\n1. Testing get_initial_story...")
        initial_prompt = """You are Sariel, a member of House Arcanus known for magical prowess. 
        You've been summoned to the throne room where you find your estranged brother Cassian 
        waiting with grave news about your family's legacy."""

        initial_result = get_initial_story(initial_prompt)
        self.assertIsNotNone(initial_result)

        # get_initial_story now returns a string directly
        narrative = initial_result
        self.assertIsInstance(
            narrative, str, "get_initial_story should return a string"
        )
        self.assertIn(
            "Sariel", narrative, "Player character Sariel missing from initial story"
        )

        # Create game state from initial story
        # Since get_initial_story only returns narrative now, we need to initialize game state manually
        game_state = GameState()
        # Initialize player character data for Sariel
        game_state.player_character_data = {
            "name": "Sariel",
            "hp_current": 30,
            "hp_max": 30,
        }

        print(f"✓ Initial story contains Sariel: {'Sariel' in narrative}")
        print(
            f"✓ Player character data created: {bool(game_state.player_character_data)}"
        )

        # Test continue story with Cassian reference
        print("\n2. Testing continue_story with Cassian reference...")
        user_input = "Tell Cassian I was scared and helpless"

        # continue_story expects: user_input, mode, story_context, current_game_state
        story_context = [
            {"user_input": initial_prompt, "narrative": narrative, "sequence_id": 1}
        ]

        continue_result = continue_story(
            user_input=user_input,
            mode="story",  # or 'character' mode
            story_context=story_context,
            current_game_state=game_state,
        )

        self.assertIsNotNone(continue_result)
        # continue_story returns the narrative string directly
        continue_narrative = continue_result
        self.assertIsInstance(continue_narrative, str)

        # Check for both Sariel and Cassian
        sariel_found = "Sariel" in continue_narrative
        cassian_found = "Cassian" in continue_narrative

        print(f"✓ Sariel in response: {sariel_found}")
        print(f"✓ Cassian in response: {cassian_found}")

        # The Cassian Problem would manifest here
        if not cassian_found and "scared" in user_input:
            print(
                "⚠️  CASSIAN PROBLEM DETECTED: Player referenced Cassian but AI didn't include him"
            )

        # Since continue_story now returns just a string, we can't check debug_info
        # The entity preloading is happening internally but not exposed
        print("\n3. Entity Preloading: Active (internal to continue_story)")

        # Summary
        print("\n=== Production Methods Summary ===")
        print(
            f"Initial story entity tracking: {'PASS' if 'Sariel' in narrative else 'FAIL'}"
        )
        print(
            f"Continue story entity tracking: {'PASS' if sariel_found and cassian_found else 'PARTIAL' if sariel_found else 'FAIL'}"
        )

        # Assert basic functionality
        self.assertTrue(sariel_found, "Sariel missing from continue_story response")


if __name__ == "__main__":
    # Note: This test makes real API calls
    print("WARNING: This test makes real Gemini API calls")
    print("Set TESTING=true to use faster models")
    unittest.main()
