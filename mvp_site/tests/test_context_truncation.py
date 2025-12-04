import os
import sys

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import unittest

# We import the service to test its internal functions
from mvp_site import llm_service
from mvp_site.game_state import GameState


class TestContextTruncation(unittest.TestCase):
    def setUp(self):
        """
        This method runs before each test. We can override the constants
        for predictable testing.
        """
        # Create a sample story context with 6 entries
        self.story_context = [
            {"actor": "gemini", "text": "Entry 1 (Oldest)"},
            {"actor": "user", "text": "Entry 2"},
            {"actor": "gemini", "text": "Entry 3"},
            {"actor": "user", "text": "Entry 4"},
            {"actor": "gemini", "text": "Entry 5"},
            {"actor": "user", "text": "Entry 6 (Newest)"},
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
            custom_campaign_state={"core_memories": []},
        )

        # Call the function with the new signature, setting turns_to_keep parameters
        truncated_context = llm_service._truncate_context(
            self.story_context,
            max_chars=1000,  # High char limit - context should be under this
            model_name="test-model",
            current_game_state=mock_game_state,
            turns_to_keep_at_start=0,  # Keep none at start
            turns_to_keep_at_end=3,  # Keep last 3
        )

        # We expect all 6 entries since we're under the char limit
        assert len(truncated_context) == 6
        assert truncated_context[0]["text"] == "Entry 1 (Oldest)"
        assert truncated_context[-1]["text"] == "Entry 6 (Newest)"

        print("--- Test Finished Successfully ---")

    def test_truncates_when_few_turns_over_char_limit(self):
        """
        Verify that when there are few turns but still over char limit,
        it applies adaptive truncation with hard-trimming to fit the budget.

        NEW BEHAVIOR (PR #2311): With a very low token budget (120 chars ≈ 30 tokens),
        adaptive truncation aggressively reduces turns and hard-trims text to fit.
        The function prioritizes recent turns (60% of budget for end) and will
        hard-trim content to guarantee budget fit.
        """
        print("\\n--- Running Test: test_truncates_when_few_turns_over_char_limit ---")

        # Create a context with very long text entries
        long_story_context = [
            {"actor": "gemini", "text": "A" * 50},  # Entry 1
            {"actor": "user", "text": "B" * 50},  # Entry 2
            {"actor": "gemini", "text": "C" * 50},  # Entry 3
            {"actor": "user", "text": "D" * 50},  # Entry 4
        ]

        # Create a mock game state for the new API
        mock_game_state = GameState(
            player_character_data={},
            world_data={},
            npc_data={},
            custom_campaign_state={"core_memories": []},
        )

        # With extremely low budget (120 chars ≈ 30 tokens), adaptive truncation
        # will hard-trim to fit. With 4 turns of 50 chars each = 200 tokens total,
        # this far exceeds the 30 token budget. The function will:
        # 1. Calculate percentage-based turns (25% start / 60% end)
        # 2. Hard-trim entries to fit within budget
        # 3. Return truncation marker + minimal turns that fit
        truncated_context = llm_service._truncate_context(
            long_story_context,
            max_chars=120,  # Very low char limit - forces aggressive truncation
            model_name="test-model",
            current_game_state=mock_game_state,
            turns_to_keep_at_start=0,  # Keep none at start
            turns_to_keep_at_end=3,  # Keep last 3 (requested, but budget may limit this)
        )

        # New adaptive behavior: Hard-trims to fit budget
        # Result: [marker] + hard-trimmed entries that fit in ~30 tokens
        # With very low budget, we expect minimal turns
        assert len(truncated_context) >= 1, "Should have at least truncation marker"
        assert len(truncated_context) <= 4, "Should not exceed 4 entries (marker + 3 turns)"

        # First entry should be truncation marker
        assert truncated_context[0]["actor"] == "system"  # Truncation marker
        assert "turns" in truncated_context[0]["text"] or "story" in truncated_context[0]["text"]

        # Remaining entries should be from the end (most recent)
        # With hard-trimming, text may be truncated
        last_entry = truncated_context[-1]
        assert last_entry["actor"] == "user"  # Last entry should be user turn (entry 4)
        # Text should start with "D" (may be trimmed but should preserve beginning)
        assert last_entry["text"].startswith("D")

        print("--- Test Finished Successfully ---")

    def test_does_not_truncate_if_within_all_limits(self):
        """
        Verify that no truncation happens if the context is within all limits.
        """
        print("\\n--- Running Test: test_does_not_truncate_if_within_all_limits ---")

        # Use a small context that is within all limits
        short_context = self.story_context[-2:]  # Only use last 2 entries

        # Create a mock game state for the new API
        mock_game_state = GameState(
            player_character_data={},
            world_data={},
            npc_data={},
            custom_campaign_state={"core_memories": []},
        )

        truncated_context = llm_service._truncate_context(
            short_context,
            max_chars=1000,  # High char limit
            model_name="test-model",
            current_game_state=mock_game_state,
            turns_to_keep_at_start=2,  # Keep first 2
            turns_to_keep_at_end=3,  # Keep last 3 (but only 2 entries total)
        )

        # The context should be returned unchanged
        assert len(truncated_context) == 2
        assert truncated_context == short_context

        print("--- Test Finished Successfully ---")


if __name__ == "__main__":
    unittest.main()
