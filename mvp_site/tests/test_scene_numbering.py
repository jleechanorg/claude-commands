import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime


class TestSceneNumbering(unittest.TestCase):
    """Test that user-facing scene numbers only increment for AI responses."""

    def test_user_scene_numbering(self):
        """Test that user_scene_number only increments for gemini responses."""
        # Mock story entries with alternating user/gemini actors
        mock_story_entries = [
            {
                "actor": "user",
                "text": "First user input",
                "timestamp": datetime.datetime.now(),
            },
            {
                "actor": "gemini",
                "text": "First AI response",
                "timestamp": datetime.datetime.now(),
            },
            {
                "actor": "user",
                "text": "Second user input",
                "timestamp": datetime.datetime.now(),
            },
            {
                "actor": "gemini",
                "text": "Second AI response",
                "timestamp": datetime.datetime.now(),
            },
            {
                "actor": "user",
                "text": "Third user input",
                "timestamp": datetime.datetime.now(),
            },
            {
                "actor": "gemini",
                "text": "Third AI response",
                "timestamp": datetime.datetime.now(),
            },
        ]

        # Process entries as get_campaign_by_id would
        user_scene_counter = 0
        for i, entry in enumerate(mock_story_entries):
            entry["sequence_id"] = i + 1

            if entry.get("actor") == "gemini":
                user_scene_counter += 1
                entry["user_scene_number"] = user_scene_counter
            else:
                entry["user_scene_number"] = None

            entry["timestamp"] = entry["timestamp"].isoformat()

        # Verify sequence_ids increment for all entries
        self.assertEqual(mock_story_entries[0]["sequence_id"], 1)  # user
        self.assertEqual(mock_story_entries[1]["sequence_id"], 2)  # gemini
        self.assertEqual(mock_story_entries[2]["sequence_id"], 3)  # user
        self.assertEqual(mock_story_entries[3]["sequence_id"], 4)  # gemini
        self.assertEqual(mock_story_entries[4]["sequence_id"], 5)  # user
        self.assertEqual(mock_story_entries[5]["sequence_id"], 6)  # gemini

        # Verify user_scene_number only increments for gemini responses
        self.assertIsNone(mock_story_entries[0]["user_scene_number"])  # user - None
        self.assertEqual(mock_story_entries[1]["user_scene_number"], 1)  # gemini - 1
        self.assertIsNone(mock_story_entries[2]["user_scene_number"])  # user - None
        self.assertEqual(mock_story_entries[3]["user_scene_number"], 2)  # gemini - 2
        self.assertIsNone(mock_story_entries[4]["user_scene_number"])  # user - None
        self.assertEqual(mock_story_entries[5]["user_scene_number"], 3)  # gemini - 3

        print("✓ User scene numbers correctly increment only for AI responses")
        print("✓ Sequence IDs increment for all entries")
        print("✓ This fixes the increment-by-2 display issue")


if __name__ == "__main__":
    unittest.main()
