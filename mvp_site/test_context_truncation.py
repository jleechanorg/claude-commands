import unittest
from unittest.mock import patch

# We import the service to test its internal functions
import gemini_service
from game_state import GameState

class TestContextTruncation(unittest.TestCase):

    def setUp(self):
        """
        This method runs before each test. We can override the constants
        for predictable testing.
        """
        # Create a sample story context with 6 entries
        self.story_context = [
            {'actor': 'gemini', 'text': 'Entry 1 (Oldest)'},
            {'actor': 'user', 'text': 'Entry 2'},
            {'actor': 'gemini', 'text': 'Entry 3'},
            {'actor': 'user', 'text': 'Entry 4'},
            {'actor': 'gemini', 'text': 'Entry 5'},
            {'actor': 'user', 'text': 'Entry 6 (Newest)'},
        ]

    def test_no_truncation_when_under_char_limit(self):
        """
        Verify that if the context is UNDER the character limit,
        no truncation occurs (new behavior).
        """
        print("\\n--- Running Test: test_no_truncation_when_under_char_limit ---")
        
        # Create a mock game state for the new API
        mock_game_state = GameState(
            player_character_data={},
            world_data={},
            npc_data={},
            custom_campaign_state={'core_memories': []}
        )
        
        # Call the function with the new signature, setting turns_to_keep parameters
        truncated_context = gemini_service._truncate_context(
            self.story_context, 
            max_chars=1000,  # High char limit - context should be under this
            model_name='test-model',
            current_game_state=mock_game_state,
            turns_to_keep_at_start=0,  # Keep none at start
            turns_to_keep_at_end=3     # Keep last 3
        )
        
        # We expect all 6 entries since we're under the char limit
        self.assertEqual(len(truncated_context), 6)
        self.assertEqual(truncated_context[0]['text'], 'Entry 1 (Oldest)')
        self.assertEqual(truncated_context[-1]['text'], 'Entry 6 (Newest)')
        
        print("--- Test Finished Successfully ---")

    def test_truncates_when_few_turns_over_char_limit(self):
        """
        Verify that when there are few turns but still over char limit,
        it takes the most recent turns that fit the turn limits.
        """
        print("\\n--- Running Test: test_truncates_when_few_turns_over_char_limit ---")
        
        # Create a context with very long text entries
        long_story_context = [
            {'actor': 'gemini', 'text': 'A' * 50}, # Entry 1
            {'actor': 'user', 'text': 'B' * 50},   # Entry 2
            {'actor': 'gemini', 'text': 'C' * 50}, # Entry 3
            {'actor': 'user', 'text': 'D' * 50},   # Entry 4
        ]
        
        # Create a mock game state for the new API
        mock_game_state = GameState(
            player_character_data={},
            world_data={},
            npc_data={},
            custom_campaign_state={'core_memories': []}
        )
        
        # With 4 total turns and wanting 3 at end, it uses the "few turns" logic
        # and returns the last 3 entries regardless of char limit
        truncated_context = gemini_service._truncate_context(
            long_story_context, 
            max_chars=120,  # Low char limit (will be ignored due to few turns)
            model_name='test-model',
            current_game_state=mock_game_state,
            turns_to_keep_at_start=0,  # Keep none at start
            turns_to_keep_at_end=3     # Keep last 3
        )
        
        # Current implementation: few turns logic returns last 3 entries
        self.assertEqual(len(truncated_context), 3)
        self.assertEqual(truncated_context[0]['text'], 'B' * 50) # Entry 2
        self.assertEqual(truncated_context[1]['text'], 'C' * 50) # Entry 3
        self.assertEqual(truncated_context[2]['text'], 'D' * 50) # Entry 4
        
        print("--- Test Finished Successfully ---")

    def test_does_not_truncate_if_within_all_limits(self):
        """
        Verify that no truncation happens if the context is within all limits.
        """
        print("\\n--- Running Test: test_does_not_truncate_if_within_all_limits ---")

        # Use a small context that is within all limits
        short_context = self.story_context[-2:] # Only use last 2 entries

        # Create a mock game state for the new API
        mock_game_state = GameState(
            player_character_data={},
            world_data={},
            npc_data={},
            custom_campaign_state={'core_memories': []}
        )

        truncated_context = gemini_service._truncate_context(
            short_context, 
            max_chars=1000,  # High char limit
            model_name='test-model',
            current_game_state=mock_game_state,
            turns_to_keep_at_start=2,  # Keep first 2
            turns_to_keep_at_end=3     # Keep last 3 (but only 2 entries total)
        )
        
        # The context should be returned unchanged
        self.assertEqual(len(truncated_context), 2)
        self.assertEqual(truncated_context, short_context)
        
        print("--- Test Finished Successfully ---")


if __name__ == '__main__':
    unittest.main()
