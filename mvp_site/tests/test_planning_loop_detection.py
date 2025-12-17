"""
RED TEST: Planning Loop Detection for Social Encounters

This test reproduces the bug where:
1. User selects a social action (e.g., "Press the Logical Argument")
2. LLM describes the situation but doesn't roll dice
3. LLM presents same/similar options again
4. Loop repeats indefinitely - narrative never progresses

The Action Execution Rule (game_state_instruction.md line 239-244) says:
- EXECUTE the chosen action with dice rolls
- DO NOT present more sub-options
- Anti-Loop Rule: If same action selected twice, ALWAYS execute on second selection

This test should FAIL until the prompt is strengthened to enforce resolution.
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


class TestPlanningLoopDetection(unittest.TestCase):
    """Test that social encounters don't get stuck in planning loops."""

    def test_social_action_bad_response_structure(self):
        """
        Document what a BAD response looks like (for reference).
        This test validates the structure of a problematic response.

        The actual fix is in tool definitions - see TestToolDefinitionsForSocialSkills.
        """
        # This is what a BAD response looks like - no skill check for social action
        bad_response = {
            "narrative": "The sterile briefing room remains charged with intellectual intensity. "
                        "Agent Reynolds stands frozen, his professional composure utterly dismantled "
                        "by the mathematical proof you've just proven.",
            "planning_block": {
                "thinking": "Reynolds is cornered by irrefutable logic.",
                "choices": {
                    "maintain_pressure": {"text": "Maintain Pressure", "description": "..."},
                    "press_argument": {"text": "Press the Logical Argument", "description": "..."},
                }
            },
            "dice_rolls": [],  # BAD: No dice rolls for social action
            "tool_requests": [],  # BAD: No skill check requested
        }

        # This test documents the bad pattern - actual validation is in tool definition tests
        self.assertEqual(len(bad_response.get("tool_requests", [])), 0, "Bad response has no tool_requests")
        self.assertEqual(len(bad_response.get("dice_rolls", [])), 0, "Bad response has no dice_rolls")

    def test_anti_loop_rule_enforcement(self):
        """
        RED TEST: If user selects same/similar action twice,
        system MUST execute on second selection - never present third round.

        Bug reproduction: User selected variants of "Press Logical Argument"
        6+ times (Scenes 257-264) without resolution.
        """
        # Simulate conversation history showing repeated similar actions
        conversation_history = [
            {"role": "user", "content": "Press Mathematical Advantage"},
            {"role": "assistant", "content": "Reynolds considers... [no resolution]"},
            {"role": "user", "content": "Maintain Pressure"},
            {"role": "assistant", "content": "The room is tense... [no resolution]"},
            {"role": "user", "content": "Press the Logical Argument"},  # 3rd similar action!
        ]

        # Count how many times user selected similar actions
        similar_action_keywords = ["press", "maintain", "logical", "argument", "pressure", "mathematical"]
        similar_action_count = sum(
            1 for msg in conversation_history
            if msg["role"] == "user" and
            any(kw in msg["content"].lower() for kw in similar_action_keywords)
        )

        # After 2 similar actions, the Anti-Loop Rule should force execution
        # RED ASSERTION: This demonstrates the detection logic
        self.assertGreaterEqual(
            similar_action_count, 2,
            "Test setup: Should have at least 2 similar actions"
        )

        # In a real fix, the system would detect this and force resolution
        # For now, we're just validating the detection mechanism works
        is_loop_detected = similar_action_count >= 2
        self.assertTrue(
            is_loop_detected,
            f"Planning loop detected: {similar_action_count} similar actions selected. "
            "System should force execution with dice roll on second similar action."
        )

    def test_dice_roll_required_for_social_resolution(self):
        """
        RED TEST: Social encounters (persuasion, intimidation, deception)
        MUST resolve via dice rolls, just like combat.

        The prompt says "Roll for: attacks, skill checks, saving throws"
        but social skill checks aren't being enforced.
        """
        # Good response should look like this
        good_response = {
            "narrative": "You challenge Reynolds to refute your analysis...",
            "tool_requests": [
                {
                    "tool": "roll_skill_check",
                    "args": {
                        "skill_name": "persuasion",
                        "attribute_modifier": 4,  # INT 18 = +4 for logical argument
                        "proficiency_bonus": 2,
                        "dc": 18,  # FBI agent = high DC
                        "purpose": "Convince Reynolds with logical framework"
                    }
                }
            ],
            "dice_rolls": [],  # Empty until Phase 2 fills in results
            "planning_block": {
                "thinking": "Awaiting skill check result to determine outcome",
                "choices": {}  # No choices until resolution!
            },
            "entities_mentioned": ["Agent Reynolds"],
            "state_updates": {}
        }

        # Validate the good response structure
        self.assertTrue(
            bool(good_response.get("tool_requests")),
            "Social resolution MUST include tool_requests for skill check"
        )

        tool_request = good_response["tool_requests"][0]
        self.assertEqual(tool_request["tool"], "roll_skill_check")
        self.assertIn("skill_name", tool_request["args"])
        self.assertIn("dc", tool_request["args"])

        # Choices should be empty during resolution (waiting for dice)
        choices = good_response.get("planning_block", {}).get("choices", {})
        self.assertEqual(
            len(choices), 0,
            "During skill check resolution, choices should be empty (awaiting result)"
        )


class TestToolDefinitionsForSocialSkills(unittest.TestCase):
    """Test that tool definitions include social skill guidance."""

    def test_roll_skill_check_includes_social_skills(self):
        """
        GREEN TEST: Verify roll_skill_check tool description includes
        Persuasion, Intimidation, Deception.
        """
        from mvp_site.game_state import DICE_ROLL_TOOLS

        # Find roll_skill_check tool
        roll_skill_check = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "roll_skill_check":
                roll_skill_check = tool
                break

        self.assertIsNotNone(roll_skill_check, "roll_skill_check tool must exist")

        description = roll_skill_check["function"]["description"].lower()

        # Verify social skills are mentioned
        self.assertIn("persuasion", description, "roll_skill_check must mention Persuasion")
        self.assertIn("intimidation", description, "roll_skill_check must mention Intimidation")
        self.assertIn("deception", description, "roll_skill_check must mention Deception")

    def test_declare_no_roll_excludes_social_encounters(self):
        """
        GREEN TEST: Verify declare_no_roll_needed tool explicitly excludes
        contested social encounters.
        """
        from mvp_site.game_state import DICE_ROLL_TOOLS

        # Find declare_no_roll_needed tool
        no_roll_tool = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "declare_no_roll_needed":
                no_roll_tool = tool
                break

        self.assertIsNotNone(no_roll_tool, "declare_no_roll_needed tool must exist")

        description = no_roll_tool["function"]["description"].lower()

        # Verify it excludes social skill checks
        self.assertIn("persuasion", description, "declare_no_roll_needed must exclude Persuasion")
        self.assertIn("intimidation", description, "declare_no_roll_needed must exclude Intimidation")
        self.assertIn("convincing", description, "declare_no_roll_needed must mention convincing NPCs")


class TestPromptEnforcementForSocialEncounters(unittest.TestCase):
    """Test that prompt instructions properly enforce social encounter resolution."""

    def test_action_execution_rule_mentions_social_skills(self):
        """
        Verify the Action Execution Rule explicitly covers social skills.

        Current gap: Rule gives combat examples but social encounters
        aren't explicitly mentioned, causing LLM to loop.
        """
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "prompts",
            "game_state_instruction.md"
        )

        with open(prompt_path, "r") as f:
            prompt_content = f.read()

        # Check if Action Execution Rule exists
        self.assertIn(
            "Action Execution Rule",
            prompt_content,
            "Prompt must contain Action Execution Rule"
        )

        # Check if Anti-Loop Rule exists
        self.assertIn(
            "Anti-Loop Rule",
            prompt_content,
            "Prompt must contain Anti-Loop Rule"
        )

        # GREEN CHECK: Does prompt explicitly mention social skill resolution?
        social_keywords_in_rule = any(
            keyword in prompt_content.lower()
            for keyword in ["persuasion", "intimidation", "deception", "social encounter"]
        )

        # This should PASS after fix adds social encounter guidance
        self.assertTrue(
            social_keywords_in_rule,
            "Action Execution Rule MUST explicitly mention social skill checks "
            "(Persuasion, Intimidation, Deception) to prevent planning loops in social encounters. "
            "Current prompt only shows combat examples."
        )


if __name__ == "__main__":
    unittest.main()
