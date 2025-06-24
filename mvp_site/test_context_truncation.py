import unittest
from unittest.mock import patch, MagicMock

# We import the service to test its internal functions
import gemini_service
from game_state import GameState

class TestContextTruncation(unittest.TestCase):

    def setUp(self):
        """
        This method runs before each test. We can override the constants
        for predictable testing.
        """
        # Create a sample story context with 10 entries for better testing
        self.story_context = [
            {'actor': 'gemini', 'text': 'Entry 1 (Oldest)'},
            {'actor': 'user', 'text': 'Entry 2'},
            {'actor': 'gemini', 'text': 'Entry 3'},
            {'actor': 'user', 'text': 'Entry 4'},
            {'actor': 'gemini', 'text': 'Entry 5'},
            {'actor': 'user', 'text': 'Entry 6'},
            {'actor': 'gemini', 'text': 'Entry 7'},
            {'actor': 'user', 'text': 'Entry 8'},
            {'actor': 'gemini', 'text': 'Entry 9'},
            {'actor': 'user', 'text': 'Entry 10 (Newest)'},
        ]
        
        # Create a mock game state with core memories
        self.mock_game_state = MagicMock(spec=GameState)
        self.mock_game_state.custom_campaign_state = {
            'core_memories': ['Memory 1', 'Memory 2', 'Important event']
        }

    def test_no_truncation_when_under_budget(self):
        """
        Verify that no truncation happens when context is under character budget.
        """
        print("\\n--- Running Test: test_no_truncation_when_under_budget ---")
        
        # Use a high character budget (no truncation needed)
        max_chars = 10000
        
        # Call the function we are testing
        truncated_context = gemini_service._truncate_context(
            self.story_context, max_chars, 'gemini-2.5-flash', self.mock_game_state
        )
        
        # Context should be unchanged
        self.assertEqual(len(truncated_context), len(self.story_context))
        self.assertEqual(truncated_context, self.story_context)
        
        print("--- Test Finished Successfully ---")

    def test_compaction_strategy_when_over_budget(self):
        """
        Verify that the new compaction strategy (first X + last Y turns) works correctly.
        """
        print("\\n--- Running Test: test_compaction_strategy_when_over_budget ---")
        
        # Use a very low character budget to force truncation
        max_chars = 50  # Much lower than total context size
        
        # Test with specific start/end turn counts
        turns_at_start = 2
        turns_at_end = 3
        
        truncated_context = gemini_service._truncate_context(
            self.story_context, max_chars, 'gemini-2.5-flash', self.mock_game_state,
            turns_to_keep_at_start=turns_at_start, turns_to_keep_at_end=turns_at_end
        )
        
        # Should have: start turns + marker + end turns = 2 + 1 + 3 = 6 entries
        self.assertEqual(len(truncated_context), 6)
        
        # First 2 entries should be preserved
        self.assertEqual(truncated_context[0]['text'], 'Entry 1 (Oldest)')
        self.assertEqual(truncated_context[1]['text'], 'Entry 2')
        
        # Middle should be truncation marker
        self.assertEqual(truncated_context[2]['actor'], 'system')
        self.assertIn('several moments', truncated_context[2]['text'])
        
        # Last 3 entries should be preserved
        self.assertEqual(truncated_context[3]['text'], 'Entry 8')
        self.assertEqual(truncated_context[4]['text'], 'Entry 9')
        self.assertEqual(truncated_context[5]['text'], 'Entry 10 (Newest)')
        
        print("--- Test Finished Successfully ---")

    def test_small_context_takes_recent_entries(self):
        """
        Verify that when total turns is less than start+end, it takes the most recent entries.
        """
        print("\\n--- Running Test: test_small_context_takes_recent_entries ---")
        
        # Use a small context (4 entries) with low budget
        small_context = self.story_context[:4]  # First 4 entries
        max_chars = 20  # Low budget to force truncation logic
        
        # Set turns to keep more than available (start=3, end=3, total=4)
        turns_at_start = 3
        turns_at_end = 3
        
        truncated_context = gemini_service._truncate_context(
            small_context, max_chars, 'gemini-2.5-flash', self.mock_game_state,
            turns_to_keep_at_start=turns_at_start, turns_to_keep_at_end=turns_at_end
        )
        
        # Should take the most recent entries up to start+end limit
        expected_length = min(len(small_context), turns_at_start + turns_at_end)
        self.assertEqual(len(truncated_context), expected_length)
        
        # Should be the most recent entries
        self.assertEqual(truncated_context[-1]['text'], 'Entry 4')
        
        print("--- Test Finished Successfully ---")

    def test_context_with_core_memories_preserved(self):
        """
        Verify that core memories are preserved and tracked during truncation.
        """
        print("\\n--- Running Test: test_context_with_core_memories_preserved ---")
        
        # Low budget to force truncation
        max_chars = 50
        turns_at_start = 1
        turns_at_end = 2
        
        truncated_context = gemini_service._truncate_context(
            self.story_context, max_chars, 'gemini-2.5-flash', self.mock_game_state,
            turns_to_keep_at_start=turns_at_start, turns_to_keep_at_end=turns_at_end
        )
        
        # Should have start + marker + end = 1 + 1 + 2 = 4 entries
        self.assertEqual(len(truncated_context), 4)
        
        # Verify the structure: first turn, marker, last 2 turns
        self.assertEqual(truncated_context[0]['text'], 'Entry 1 (Oldest)')
        self.assertEqual(truncated_context[1]['actor'], 'system')
        self.assertEqual(truncated_context[2]['text'], 'Entry 9')
        self.assertEqual(truncated_context[3]['text'], 'Entry 10 (Newest)')
        
        # Note: Core memories are preserved in the game state, not in the context itself
        # They are included in context stats but maintained separately
        self.assertEqual(len(self.mock_game_state.custom_campaign_state['core_memories']), 3)
        
        print("--- Test Finished Successfully ---")


if __name__ == '__main__':
    unittest.main()
