import unittest
from unittest.mock import patch

# We import the service to test its internal functions
import gemini_service

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

    def test_truncates_by_history_turn_limit_only(self):
        """
        Verify that if the context is UNDER the character limit,
        it is only truncated by the HISTORY_TURN_LIMIT.
        """
        print("\\n--- Running Test: test_truncates_by_history_turn_limit_only ---")
        
        # Temporarily set the service constants for this test
        with patch.object(gemini_service, 'HISTORY_TURN_LIMIT', 3), \
             patch.object(gemini_service, 'SAFE_CHAR_LIMIT', 1000): # High char limit
            
            # Call the function we are testing
            truncated_context = gemini_service._truncate_context(self.story_context)
            
            # We expect the last 3 entries
            self.assertEqual(len(truncated_context), 3)
            self.assertEqual(truncated_context[0]['text'], 'Entry 4')
            self.assertEqual(truncated_context[1]['text'], 'Entry 5')
            self.assertEqual(truncated_context[2]['text'], 'Entry 6 (Newest)')
            
            print("--- Test Finished Successfully ---")

    def test_truncates_by_char_limit_when_history_is_too_long(self):
        """
        Verify that if the context is OVER the character limit (even after
        the turn limit is applied), it is further truncated by character count.
        """
        print("\\n--- Running Test: test_truncates_by_char_limit_when_history_is_too_long ---")
        
        # Create a context with very long text entries
        long_story_context = [
            {'actor': 'gemini', 'text': 'A' * 50}, # Entry 1
            {'actor': 'user', 'text': 'B' * 50},   # Entry 2
            {'actor': 'gemini', 'text': 'C' * 50}, # Entry 3
            {'actor': 'user', 'text': 'D' * 50},   # Entry 4
        ]
        
        # Set a turn limit of 3, but a very low character limit of 120.
        # The last 3 entries (B, C, D) have a total character count of 150,
        # so the oldest one ('B') should be removed.
        with patch.object(gemini_service, 'HISTORY_TURN_LIMIT', 3), \
             patch.object(gemini_service, 'SAFE_CHAR_LIMIT', 120):
                 
            truncated_context = gemini_service._truncate_context(long_story_context)
            
            # We expect only the last 2 entries to remain to fit under the 120 char limit
            self.assertEqual(len(truncated_context), 2)
            self.assertEqual(truncated_context[0]['text'], 'C' * 50) # Entry 3
            self.assertEqual(truncated_context[1]['text'], 'D' * 50) # Entry 4
            
            print("--- Test Finished Successfully ---")

    def test_does_not_truncate_if_within_all_limits(self):
        """
        Verify that no truncation happens if the context is within all limits.
        """
        print("\\n--- Running Test: test_does_not_truncate_if_within_all_limits ---")

        # Use a small context that is within all limits
        short_context = self.story_context[-2:] # Only use last 2 entries

        with patch.object(gemini_service, 'HISTORY_TURN_LIMIT', 5), \
             patch.object(gemini_service, 'SAFE_CHAR_LIMIT', 1000):

            truncated_context = gemini_service._truncate_context(short_context)
            
            # The context should be returned unchanged
            self.assertEqual(len(truncated_context), 2)
            self.assertEqual(truncated_context, short_context)
            
            print("--- Test Finished Successfully ---")


if __name__ == '__main__':
    unittest.main()
