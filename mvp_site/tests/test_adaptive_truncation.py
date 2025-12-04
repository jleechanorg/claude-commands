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
        from mvp_site.llm_service import _truncate_context

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
        from mvp_site.llm_service import _truncate_context

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

    def test_truncation_no_change_when_under_budget(self):
        """When content is within budget, should return unchanged."""
        from mvp_site.llm_service import _truncate_context

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
        from mvp_site.llm_service import _truncate_context

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


if __name__ == "__main__":
    unittest.main()
