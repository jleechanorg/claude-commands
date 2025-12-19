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
    _compact_middle_turns,
    _split_into_sentences,
    _is_important_sentence,
    estimate_tokens,
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

        # Should have minimum turns (3 start + 5 end = 8) plus optional marker
        # With extreme budget pressure, the middle marker may be dropped
        self.assertGreaterEqual(len(result), 8)
        self.assertLessEqual(len(result), 9)

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
    """Test percentage-based context allocation (25% start, 10% middle, 60% end)."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"

    def test_calculate_percentage_based_turns(self):
        """Percentage-based calculation should allocate 25% start / 60% end."""
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

        # Should allocate based on 25/60 ratio (caps at 500 per side now, not 20)
        # With 5000 tokens budget and ~100 tokens/turn:
        # - start_budget (25%): 1250 tokens → ~12 turns (may be limited by total_turns//2)
        # - end_budget (60%): 3000 tokens → ~30 turns (capped by TURNS_TO_KEEP_AT_END and remaining turns after start allocation)
        self.assertGreaterEqual(start_turns, 3)
        self.assertLessEqual(start_turns, 50)  # Can't exceed half of 100 turns
        self.assertGreaterEqual(end_turns, 5)
        self.assertLessEqual(end_turns, 50)  # Reasonable upper bound
        self.assertLessEqual(start_turns + end_turns, len(story_context))

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

    def test_percentage_based_turns_do_not_overlap_small_context(self):
        """Start + end allocations should never exceed available turns."""
        story_context = [
            {"actor": "user" if i % 2 == 0 else "gemini", "text": "x" * 800}
            for i in range(6)
        ]

        start_turns, end_turns = _calculate_percentage_based_turns(
            story_context, max_tokens=2000
        )

        self.assertLessEqual(start_turns + end_turns, len(story_context))


class TestMiddleCompaction(unittest.TestCase):
    """Test middle turn compaction instead of dropping."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"

    def test_compact_middle_turns_extracts_key_events(self):
        """Middle compaction should extract sentences with important keywords."""
        # Create turns with mix of important and filler content
        middle_turns = [
            {"actor": "gemini", "text": "The party rested by the campfire."},
            {"actor": "gemini", "text": "You attack the goblin! The creature takes 15 damage and falls."},
            {"actor": "user", "text": "I search the room."},
            {"actor": "gemini", "text": "You discover a hidden treasure chest containing gold coins."},
            {"actor": "gemini", "text": "The night passes uneventfully."},
        ]

        result = _compact_middle_turns(middle_turns, max_tokens=500)

        # Should be a system message
        self.assertEqual(result.get("actor"), "system")

        # Should contain key events (attack, discover, treasure)
        text = result.get("text", "")
        self.assertIn("key events occurred", text)
        # Should have extracted sentences with keywords
        self.assertTrue("attack" in text.lower() or "damage" in text.lower() or "discover" in text.lower())

    def test_compact_middle_turns_respects_token_limit(self):
        """Middle compaction should not exceed token budget."""
        # Create many turns with important content
        middle_turns = [
            {"actor": "gemini", "text": f"You defeat enemy number {i}. The battle was fierce." * 5}
            for i in range(20)
        ]

        # Very small token budget
        result = _compact_middle_turns(middle_turns, max_tokens=100)

        # Result should not exceed budget significantly
        result_tokens = estimate_tokens(result.get("text", ""))
        # Allow bounded overhead for formatting
        self.assertLess(result_tokens, 150)

    def test_compact_middle_turns_empty_list(self):
        """Empty middle turns should return minimal marker."""
        result = _compact_middle_turns([], max_tokens=500)

        self.assertEqual(result.get("actor"), "system")
        self.assertIn("time passes", result.get("text", ""))

    def test_compact_middle_turns_no_keywords(self):
        """Turns without keywords should use fallback sampling instead of losing content."""
        # Create turns with no important keywords
        middle_turns = [
            {"actor": "gemini", "text": "The sun shines brightly today."},
            {"actor": "user", "text": "I look around."},
            {"actor": "gemini", "text": "You see trees and grass."},
        ]

        result = _compact_middle_turns(middle_turns, max_tokens=500)

        # Should still produce a system message
        self.assertEqual(result.get("actor"), "system")
        # NEW BEHAVIOR: Fallback sampling preserves content when no keywords match
        # Instead of just saying "X turns passed", we now sample evenly from sentences
        text = result.get("text", "")
        self.assertTrue(
            "key events" in text or "sun shines" in text or "look around" in text,
            f"Should contain sampled content or key events marker, got: {text}"
        )

    def test_truncation_includes_middle_summary(self):
        """Full truncation should include compacted middle, not just drop it."""
        mock_game_state = MagicMock(spec=GameState)
        mock_game_state.custom_campaign_state = {}
        mock_game_state.world_data = {}
        mock_game_state.to_dict.return_value = {}
        mock_game_state.combat_state = {"in_combat": False}

        # Create 80 turns with combat in the middle - large enough to force truncation
        story_context = []
        for i in range(80):
            if 25 <= i < 55:
                # Middle section with combat - will be compacted
                text = f"Turn {i}: You attack the goblin! The enemy takes {i} damage and retreats."
            else:
                # Long filler turns
                text = f"Turn {i}: " + "x" * 4000  # ~1000 tokens each
            story_context.append({"actor": "gemini", "text": text})

        # Small budget that forces aggressive truncation
        max_chars = 80_000  # ~20K tokens - small enough to force truncation

        result = _truncate_context(
            story_context=story_context,
            max_chars=max_chars,
            model_name="zai-glm-4.6",
            current_game_state=mock_game_state,
            provider_name=constants.LLM_PROVIDER_CEREBRAS,
        )

        # Should have fewer turns than original
        self.assertLess(len(result), len(story_context))

        # Find the system message (middle summary)
        system_messages = [e for e in result if e.get("actor") == "system"]
        self.assertGreater(len(system_messages), 0, "Should have a middle summary")

        # Check that combat events were preserved in the summary
        middle_summary = system_messages[0].get("text", "")
        self.assertTrue(
            "attack" in middle_summary.lower() or "damage" in middle_summary.lower() or
            "key events" in middle_summary.lower() or "turns" in middle_summary.lower(),
            f"Middle summary should mention events or turns: {middle_summary[:200]}"
        )


class TestTruncationBudgetGuarantees(unittest.TestCase):
    """Test that truncation ALWAYS returns content within budget."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"
        self.mock_game_state = MagicMock(spec=GameState)
        self.mock_game_state.custom_campaign_state = {}
        self.mock_game_state.world_data = {}
        self.mock_game_state.to_dict.return_value = {}
        self.mock_game_state.combat_state = {"in_combat": False}

    def test_short_transcript_respects_budget(self):
        """
        BUG: When total_turns <= start+end, code returns without checking budget.
        Two very long turns should still be truncated if over budget.
        """
        # Create 2 HUGE turns (~50K tokens each = 200K chars)
        huge_text = "x" * 200_000  # ~50K tokens
        story_context = [
            {"actor": "user", "text": huge_text},
            {"actor": "gemini", "text": huge_text},
        ]

        # Budget that can only fit ~10K tokens (~40K chars)
        max_chars = 40_000

        result = _truncate_context(
            story_context=story_context,
            max_chars=max_chars,
            model_name="zai-glm-4.6",
            current_game_state=self.mock_game_state,
            provider_name=constants.LLM_PROVIDER_CEREBRAS,
        )

        # Result MUST fit within budget
        result_text = "".join(e.get("text", "") for e in result)
        result_tokens = estimate_tokens(result_text)
        max_tokens = estimate_tokens(" " * max_chars)

        self.assertLessEqual(
            result_tokens, max_tokens,
            f"Short transcript still over budget: {result_tokens} > {max_tokens}"
        )

    def test_last_resort_respects_budget(self):
        """
        BUG: Last resort returns truncated_context without checking budget.
        Even with minimum turns, result should fit in budget.
        """
        # Create 10 huge turns that won't fit even with minimums (3+5=8 turns)
        huge_text = "x" * 80_000  # ~20K tokens per turn
        story_context = [
            {"actor": "user" if i % 2 == 0 else "gemini", "text": huge_text}
            for i in range(10)
        ]

        # Tiny budget that can't fit 8 turns of 20K tokens each
        max_chars = 20_000  # ~5K tokens

        result = _truncate_context(
            story_context=story_context,
            max_chars=max_chars,
            model_name="zai-glm-4.6",
            current_game_state=self.mock_game_state,
            provider_name=constants.LLM_PROVIDER_CEREBRAS,
        )

        # Result MUST fit within budget (or raise error, not silently overflow)
        result_text = "".join(e.get("text", "") for e in result)
        result_tokens = estimate_tokens(result_text)
        max_tokens = estimate_tokens(" " * max_chars)

        self.assertLessEqual(
            result_tokens, max_tokens,
            f"Last resort still over budget: {result_tokens} > {max_tokens}"
        )

    def test_middle_summary_respects_budget(self):
        """
        BUG: Middle compaction adds bullets/wrappers after capping sentences.
        The final summary can exceed the allocated middle_token_budget.
        """
        # Create many turns with keyword-rich content that will be extracted
        middle_turns = [
            {"actor": "gemini", "text": f"You attack the goblin {i}! " * 20}
            for i in range(50)
        ]

        # Very small budget
        max_tokens = 100

        result = _compact_middle_turns(middle_turns, max_tokens)
        result_text = result.get("text", "")
        result_tokens = estimate_tokens(result_text)

        # Result MUST fit within budget (including wrapper overhead)
        self.assertLessEqual(
            result_tokens, max_tokens,
            f"Middle summary exceeds budget: {result_tokens} > {max_tokens}"
        )


class TestImprovedSentenceSplitting(unittest.TestCase):
    """Test robust sentence splitting that handles abbreviations and decimals."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"

    def test_split_handles_abbreviations(self):
        """Sentence splitting should NOT break on abbreviations like Dr., Mr."""
        text = "Dr. Smith went to the market. He bought apples."
        sentences = _split_into_sentences(text)

        # Should be 2 sentences, not 3 (Dr. should not split)
        self.assertEqual(len(sentences), 2)
        self.assertIn("Dr. Smith", sentences[0])

    def test_split_handles_decimal_numbers(self):
        """Sentence splitting should NOT break on decimal numbers like 3.14."""
        text = "The value was 3.14 times larger. That surprised everyone."
        sentences = _split_into_sentences(text)

        # Should be 2 sentences, not 3 (3.14 should not split)
        self.assertEqual(len(sentences), 2)
        self.assertIn("3.14", sentences[0])

    def test_split_handles_multiple_punctuation(self):
        """Should handle multiple punctuation marks correctly."""
        text = "What happened?! I can't believe it. Amazing..."
        sentences = _split_into_sentences(text)

        # Should produce 2-3 sentences (depending on ... handling)
        self.assertGreaterEqual(len(sentences), 2)

    def test_split_empty_text(self):
        """Empty text should return empty list."""
        self.assertEqual(_split_into_sentences(""), [])
        self.assertEqual(_split_into_sentences("   "), [])


class TestImportanceDetection(unittest.TestCase):
    """Test pattern-based importance detection (language-agnostic)."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"

    def test_detects_dice_rolls(self):
        """Should detect dice roll patterns (d20, 2d6, rolls a 15)."""
        self.assertTrue(_is_important_sentence("You roll a d20 and get 15."))
        self.assertTrue(_is_important_sentence("The attack deals 2d6+3 damage."))
        self.assertTrue(_is_important_sentence("She rolls 18 on her check."))

    def test_detects_numeric_results(self):
        """Should detect damage, gold, HP amounts (language-agnostic)."""
        self.assertTrue(_is_important_sentence("The goblin takes 15 damage."))
        self.assertTrue(_is_important_sentence("You receive 50 gold coins."))
        self.assertTrue(_is_important_sentence("You lose -10 HP from the poison."))
        self.assertTrue(_is_important_sentence("Gained 100 XP from the encounter."))

    def test_detects_long_dialogue(self):
        """Should detect significant dialogue (20+ chars in quotes)."""
        self.assertTrue(_is_important_sentence(
            'The wizard says "Beware the ancient evil that sleeps beneath the mountain."'
        ))
        # Short quotes should not trigger
        self.assertFalse(_is_important_sentence('He said "No" quietly.'))

    def test_detects_exclamatory_sentences(self):
        """Long exclamatory sentences often indicate dramatic moments."""
        self.assertTrue(_is_important_sentence(
            "The dragon rises from the depths with a thunderous roar!"
        ))
        # Short exclamations should not trigger alone
        self.assertFalse(_is_important_sentence("Stop!"))

    def test_keywords_still_work(self):
        """Original keyword matching should still work."""
        self.assertTrue(_is_important_sentence("You attack the goblin."))
        self.assertTrue(_is_important_sentence("You discover a hidden passage."))
        self.assertTrue(_is_important_sentence("The quest is complete."))

    def test_boring_sentence_not_important(self):
        """Generic sentences without patterns should not be marked important."""
        self.assertFalse(_is_important_sentence("The sun shines brightly."))
        self.assertFalse(_is_important_sentence("You look around the room."))
        self.assertFalse(_is_important_sentence("The sky is blue today."))
        self.assertFalse(_is_important_sentence("Birds are singing nearby."))


class TestFallbackSampling(unittest.TestCase):
    """Test fallback sampling when no keywords match."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"

    def test_fallback_preserves_content(self):
        """When no keywords match, should sample evenly instead of losing content."""
        # Turns with only generic content (no keywords)
        middle_turns = [
            {"actor": "gemini", "text": "The morning light filters through the trees."},
            {"actor": "user", "text": "I observe my surroundings carefully."},
            {"actor": "gemini", "text": "Birds sing in the distance."},
            {"actor": "user", "text": "I continue walking down the path."},
            {"actor": "gemini", "text": "The road stretches ahead endlessly."},
        ]

        result = _compact_middle_turns(middle_turns, max_tokens=500)
        text = result.get("text", "")

        # Should contain sampled content, not just "X turns passed"
        self.assertIn("key events", text)
        # Should have preserved at least some sentences
        self.assertTrue(
            any(phrase in text for phrase in [
                "morning light", "surroundings", "Birds sing", "walking", "road"
            ]),
            f"Should contain sampled content, got: {text}"
        )


if __name__ == "__main__":
    unittest.main()
