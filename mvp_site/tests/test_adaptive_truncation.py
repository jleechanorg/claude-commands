"""
Test: Adaptive Context Truncation

When 20+20 turns still exceed model context budget, the truncation should
iteratively reduce turns until the content fits. This prevents ContextTooLargeError
for models with smaller context windows (e.g., Cerebras 131K).

Previously, truncation kept a fixed 40 turns regardless of whether that fit,
causing context overflow for long narrative entries.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from mvp_site import constants
from mvp_site.game_state import GameState
from mvp_site.llm_service import (
    _calculate_percentage_based_turns,
    _truncate_context,
)


class TestAdaptiveTruncation(unittest.TestCase):
    """Test adaptive context truncation for smaller context models."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"
        self.mock_game_state = MagicMock(spec=GameState)
        self.mock_game_state.custom_campaign_state = {}
        self.mock_game_state.world_data = {}
        self.mock_game_state.to_dict.return_value = {}
        self.mock_game_state.combat_state = {"in_combat": False}

    def test_truncation_reduces_turns_when_over_budget(self):
        """
        When initial 20+20 turns exceed budget, should reduce turns adaptively.

        Simulates long narrative entries (~2400 tokens each) that would overflow
        Cerebras's 94K input limit with 40 turns.
        """
        # Create 50 story entries with ~2400 tokens each (simulated via long text)
        # 2400 tokens ≈ 9600 chars (4 chars per token estimate)
        long_entry_text = "x" * 9600  # ~2400 tokens per entry
        story_context = [
            {"actor": "user" if i % 2 == 0 else "gemini", "text": long_entry_text}
            for i in range(50)
        ]

        # Budget for 40 turns with 2400 tokens each = 96,000 tokens
        # Set max_chars to allow only ~80,000 tokens (~320,000 chars)
        # This should force adaptive truncation
        max_chars = 320_000  # ~80,000 tokens

        result = _truncate_context(
            story_context=story_context,
            max_chars=max_chars,
            model_name="zai-glm-4.6",
            current_game_state=self.mock_game_state,
            provider_name=constants.LLM_PROVIDER_CEREBRAS,
        )

        # Should have fewer than 40 turns + 1 marker
        self.assertLess(len(result), 42)
        # Should still have meaningful content
        self.assertGreater(len(result), 5)
        # Should contain truncation marker
        marker_texts = [e.get("text", "") for e in result if e.get("actor") == "system"]
        self.assertTrue(any("story continues" in t for t in marker_texts))

    def test_truncation_keeps_minimum_turns(self):
        """Should keep at least 3 start + 5 end turns even with extreme budget."""
        # Create entries that are very long
        huge_entry_text = "x" * 40000  # ~10,000 tokens per entry
        story_context = [
            {"actor": "user" if i % 2 == 0 else "gemini", "text": huge_entry_text}
            for i in range(50)
        ]

        # Very small budget that can't fit even 8 turns
        max_chars = 80_000  # ~20,000 tokens

        result = _truncate_context(
            story_context=story_context,
            max_chars=max_chars,
            model_name="zai-glm-4.6",
            current_game_state=self.mock_game_state,
            provider_name=constants.LLM_PROVIDER_CEREBRAS,
        )

        # Should have minimum turns (3 start + 1 marker + 5 end = 9)
        self.assertEqual(len(result), 9)

    @patch("mvp_site.llm_service.gemini_provider.count_tokens", return_value=100)
    def test_truncation_no_change_when_under_budget(self, mock_count_tokens):
        """When content is within budget, should return unchanged."""

        # Create 10 short entries
        story_context = [
            {"actor": "user" if i % 2 == 0 else "gemini", "text": f"Short entry {i}"}
            for i in range(10)
        ]

        # Generous budget
        max_chars = 1_000_000

        result = _truncate_context(
            story_context=story_context,
            max_chars=max_chars,
            model_name="gemini-2.0-flash",
            current_game_state=self.mock_game_state,
            provider_name=constants.LLM_PROVIDER_GEMINI,
        )

        # Should return original unchanged
        self.assertEqual(len(result), 10)

    def test_truncation_preserves_recent_context(self):
        """Adaptive truncation should prioritize recent (end) context."""
        # Create numbered entries so we can verify which are kept
        story_context = [
            {"actor": "user", "text": f"Entry number {i} " + "x" * 4000}
            for i in range(60)
        ]

        # Budget that forces reduction
        max_chars = 160_000  # ~40,000 tokens

        result = _truncate_context(
            story_context=story_context,
            max_chars=max_chars,
            model_name="zai-glm-4.6",
            current_game_state=self.mock_game_state,
            provider_name=constants.LLM_PROVIDER_CEREBRAS,
        )

        # Last entries should be preserved (check last non-marker entry)
        non_marker_entries = [e for e in result if e.get("actor") != "system"]
        last_entry_text = non_marker_entries[-1].get("text", "")
        # Should contain one of the last entries (55-59)
        self.assertTrue(
            any(f"Entry number {i}" in last_entry_text for i in range(55, 60)),
            f"Last entry should be from recent context, got: {last_entry_text[:50]}"
        )


class TestPercentageBasedTruncation(unittest.TestCase):
    """Test percentage-based context allocation (25% start, 70% end)."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"

    def test_calculate_percentage_based_turns(self):
        """Percentage-based calculation should allocate 25% start / 70% end."""
        # Create 100 entries with ~100 tokens each (400 chars = 100 tokens)
        story_context = [
            {"actor": "user" if i % 2 == 0 else "gemini", "text": "x" * 400}
            for i in range(100)
        ]

        # Budget of 5000 tokens
        max_tokens = 5000

        start_turns, end_turns = _calculate_percentage_based_turns(
            story_context, max_tokens
        )

        # Should allocate based on 25/70 ratio
        self.assertGreaterEqual(start_turns, 3)
        self.assertLessEqual(start_turns, 20)
        self.assertGreaterEqual(end_turns, 5)
        self.assertLessEqual(end_turns, 20)

    def test_percentage_based_turns_scales_with_budget(self):
        """Turn allocation should scale down for smaller budgets."""
        # Create entries with ~500 tokens each
        story_context = [
            {"actor": "user", "text": "x" * 2000}  # ~500 tokens
            for _ in range(50)
        ]

        # Small budget - should get fewer turns
        small_start, small_end = _calculate_percentage_based_turns(
            story_context, max_tokens=3000
        )

        # Larger budget - should get more turns
        large_start, large_end = _calculate_percentage_based_turns(
            story_context, max_tokens=20000
        )

        # Larger budget should allow more turns (or equal if capped)
        self.assertGreaterEqual(large_start + large_end, small_start + small_end)


if __name__ == "__main__":
    unittest.main()
