"""
TDD tests for keyword parsing refactor.

This tests the removal of hacky keyword-based prompt switching in get_current_turn_prompt().

The problem being addressed:
- "think" and "plan" keywords in user input would change prompt template
- This caused false positives: "I plan to attack" triggers thinking mode
- The LLM system instruction already knows how to handle think commands

The fix:
- Remove keyword detection from get_current_turn_prompt()
- Use a consistent prompt template for all character mode inputs
- Let the LLM interpret user intent from its system instructions

NOTE: Run with TESTING=true vpython mvp_site/tests/test_keyword_parsing_refactor.py
      This ensures TESTING env var is set before module-level imports.
"""

import os
import sys
import unittest

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Module-level import (TESTING env var must be set before test execution)
from mvp_site.agent_prompts import get_current_turn_prompt


class TestKeywordParsingRefactor(unittest.TestCase):
    """Test cases for keyword parsing refactor in get_current_turn_prompt()."""

    def test_action_with_plan_word_not_treated_as_think_command(self):
        """
        User says "I plan to attack" - this should NOT trigger think mode.

        Before fix: This triggered think mode due to "plan" keyword.
        After fix: This generates a standard story continuation prompt.
        """
        user_input = "I plan to attack the goblin"
        result = get_current_turn_prompt(user_input, "character")

        # Should NOT contain think-specific instructions
        self.assertNotIn("internal thoughts", result.lower())
        self.assertNotIn("mental deliberation", result.lower())
        self.assertNotIn("DO NOT take any physical actions", result)

        # SHOULD contain standard story continuation language
        self.assertIn("Continue the story", result)

    def test_action_describing_existing_plan_not_think_command(self):
        """
        User references "the plan" - should NOT trigger think mode.

        Before fix: "The merchant explains the plan" triggered think mode.
        After fix: Standard story continuation.
        """
        user_input = "The merchant explains the plan to infiltrate the castle"
        result = get_current_turn_prompt(user_input, "character")

        self.assertNotIn("internal thoughts", result.lower())
        self.assertIn("Continue the story", result)

    def test_sentence_with_think_word_not_think_command(self):
        """
        User says something with "think" that's not a think command.

        "I think the guard is lying" is an observation, not a deliberation request.
        """
        user_input = "I think the guard is lying to us"
        result = get_current_turn_prompt(user_input, "character")

        self.assertNotIn("mental deliberation", result.lower())
        self.assertIn("Continue the story", result)

    def test_character_mode_consistent_prompt_template(self):
        """
        All character mode inputs should use the same prompt template.

        The LLM's system instructions already tell it how to handle
        think/plan commands - we don't need keyword detection.
        """
        inputs = [
            "I attack the dragon",
            "I think about my options",
            "Let me plan my next move",
            "I open the door",
            "Main Character: think about the situation",
        ]

        prompts = [get_current_turn_prompt(inp, "character") for inp in inputs]

        # All should contain "Continue the story" (consistent template)
        for prompt in prompts:
            self.assertIn("Continue the story", prompt)
            self.assertTrue(
                prompt.startswith("Main character:"),
                "Prompt template should keep the standard 'Main character:' prefix.",
            )

    def test_god_mode_unchanged(self):
        """God mode prompts should be unchanged."""
        user_input = "Show me the enemy stats"
        result = get_current_turn_prompt(user_input, "god")

        self.assertIn("GOD MODE:", result)
        self.assertIn(user_input, result)


if __name__ == "__main__":
    unittest.main()
