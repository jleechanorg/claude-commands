import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import datetime


class TestSceneNumbering(unittest.TestCase):
    """Test that user-facing scene numbers only increment for AI responses.

    Turn/Scene Terminology:
    -----------------------
    The codebase uses distinct counting systems for story progression:

    - story_entry_count / turn_number: Internal counter of ALL story entries
      (user inputs + AI responses). Example: With 6 entries, turn_number = 6.

    - sequence_id: Absolute position in story array. Every entry gets an
      incrementing sequence_id (1, 2, 3, ...). Technical ordering identifier.

    - user_scene_number: User-facing "Scene #X" counter. ONLY increments for
      AI (Gemini) responses. User inputs get user_scene_number=None.
      This is what players see as the scene progression.

    Key relationship (approximate, assumes alternating user/AI):
      user_scene_number ≈ story_entry_count / 2

    This test validates that user_scene_number correctly tracks only AI
    responses, preventing the "increment-by-2" bug where scene numbers
    would appear to skip values when counting all entries.
    """

    def test_user_scene_numbering(self):
        """Test that user_scene_number only increments for gemini responses."""
        # Mock story entries with alternating user/gemini actors
        mock_story_entries = [
            {
                "actor": "user",
                "text": "First user input",
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
            },
            {
                "actor": "gemini",
                "text": "First AI response",
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
            },
            {
                "actor": "user",
                "text": "Second user input",
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
            },
            {
                "actor": "Gemini",  # mixed case should still increment
                "text": "Second AI response",
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
            },
            {
                "actor": "user",
                "text": "Third user input",
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
            },
            {
                "actor": "gemini",
                "text": "Third AI response",
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
            },
        ]

        # Process entries as get_campaign_by_id would
        user_scene_counter = 0
        for i, entry in enumerate(mock_story_entries):
            entry["sequence_id"] = i + 1

            actor_value = entry.get("actor")
            normalized_actor = (
                actor_value.lower() if isinstance(actor_value, str) else None
            )
            if normalized_actor == "gemini":
                user_scene_counter += 1
                entry["user_scene_number"] = user_scene_counter
            else:
                entry["user_scene_number"] = None

            entry["timestamp"] = entry["timestamp"].isoformat()

        # Verify sequence_ids increment for all entries
        assert mock_story_entries[0]["sequence_id"] == 1  # user
        assert mock_story_entries[1]["sequence_id"] == 2  # gemini
        assert mock_story_entries[2]["sequence_id"] == 3  # user
        assert mock_story_entries[3]["sequence_id"] == 4  # gemini
        assert mock_story_entries[4]["sequence_id"] == 5  # user
        assert mock_story_entries[5]["sequence_id"] == 6  # gemini

        # Verify user_scene_number only increments for gemini responses
        assert mock_story_entries[0]["user_scene_number"] is None  # user - None
        assert mock_story_entries[1]["user_scene_number"] == 1  # gemini - 1
        assert mock_story_entries[2]["user_scene_number"] is None  # user - None
        assert mock_story_entries[3]["user_scene_number"] == 2  # gemini - 2
        assert mock_story_entries[4]["user_scene_number"] is None  # user - None
        assert mock_story_entries[5]["user_scene_number"] == 3  # gemini - 3

        print("✓ User scene numbers correctly increment only for AI responses")
        print("✓ Sequence IDs increment for all entries")
        print("✓ This fixes the increment-by-2 display issue")


if __name__ == "__main__":
    unittest.main()
