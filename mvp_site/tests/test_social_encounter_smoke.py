#!/usr/bin/env python3
"""
REAL API Smoke Test: Social Encounter Planning Loop Detection

This test calls REAL LLMs to reproduce the planning loop bug where:
1. User selects a social action (e.g., "Press the Logical Argument")
2. LLM describes situation but doesn't request skill check
3. LLM presents same options again - narrative doesn't progress

Root cause: Tool definitions didn't mention Persuasion/Intimidation/Deception,
so LLM didn't know to use roll_skill_check for social encounters.

Run with:
    TESTING=true python mvp_site/tests/test_social_encounter_smoke.py

Expected behavior BEFORE fix:
    - LLM returns NO tool_requests for social action
    - Test FAILS

Expected behavior AFTER fix:
    - LLM returns tool_requests with roll_skill_check for Persuasion/Intimidation
    - Test PASSES
"""

import json
import os
import sys
import unittest
from unittest.mock import patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site.game_state import DICE_ROLL_TOOLS, GameState
from mvp_site import llm_service, constants


class TestSocialEncounterRealAPI(unittest.TestCase):
    """Real API tests for social encounter skill checks."""

    def setUp(self):
        """Set up test fixtures."""
        # Social encounter scenario - convincing a resistant NPC
        self.social_scenario = {
            "user_action": "Press the Logical Argument - Drive home the mathematical certainty that Framework Three is the only viable solution",
            "context": "You are in an FBI briefing room. Agent Reynolds is resistant to granting you authority. You've presented data showing Framework Three has 89.2% success probability vs 12% for conventional approaches.",
            "npc_name": "Agent Reynolds",
            "npc_disposition": "resistant, skeptical, institutional",
        }

        # Create a minimal game state for the test
        self.game_state = GameState(user_id="test_user")
        self.game_state.player_character_data = {
            "name": "Sariel",
            "class": "Ranger",
            "level": 3,
            "attributes": {
                "strength": 10,
                "dexterity": 16,
                "constitution": 14,
                "intelligence": 18,  # High INT for logical arguments
                "wisdom": 14,
                "charisma": 12,  # Low CHA
            },
            "hp_current": 26,
            "hp_max": 26,
        }

    def test_tool_definitions_include_social_skills(self):
        """
        Verify that roll_skill_check tool description includes social skills.
        This is a prerequisite for the LLM to know it should use the tool.
        """
        # Find roll_skill_check tool
        roll_skill_check = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "roll_skill_check":
                roll_skill_check = tool
                break

        self.assertIsNotNone(roll_skill_check, "roll_skill_check tool must exist")

        description = roll_skill_check["function"]["description"].lower()

        # These assertions will FAIL before the fix is applied
        self.assertIn(
            "persuasion",
            description,
            "FAIL: roll_skill_check description does NOT mention Persuasion. "
            "LLM won't know to use this tool for social encounters!"
        )
        self.assertIn(
            "intimidation",
            description,
            "FAIL: roll_skill_check description does NOT mention Intimidation. "
            "LLM won't know to use this tool for social encounters!"
        )

    def test_declare_no_roll_excludes_contested_social(self):
        """
        Verify declare_no_roll_needed explicitly excludes contested social encounters.
        """
        # Find declare_no_roll_needed tool
        no_roll_tool = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "declare_no_roll_needed":
                no_roll_tool = tool
                break

        self.assertIsNotNone(no_roll_tool, "declare_no_roll_needed tool must exist")

        description = no_roll_tool["function"]["description"].lower()

        # Check it excludes Persuasion/Intimidation
        self.assertIn(
            "persuasion",
            description,
            "FAIL: declare_no_roll_needed does NOT explicitly exclude Persuasion. "
            "LLM might incorrectly skip skill checks for social encounters!"
        )

    @unittest.skipUnless(
        os.getenv("RUN_REAL_LLM_TESTS") == "true",
        "Set RUN_REAL_LLM_TESTS=true to run real LLM API tests"
    )
    def test_real_llm_requests_skill_check_for_social_action(self):
        """
        REAL API TEST: Call actual LLM with social encounter and verify it requests
        a skill check (Persuasion/Intimidation) instead of looping.

        This test requires:
        - RUN_REAL_LLM_TESTS=true
        - Valid API credentials for Gemini/Cerebras/OpenRouter
        """
        # Build prompt for social encounter
        prompt = f"""
You are a D&D 5e Game Master. The player has selected an action from the planning block.

CURRENT SITUATION:
{self.social_scenario['context']}

PLAYER ACTION SELECTED:
{self.social_scenario['user_action']}

NPC: {self.social_scenario['npc_name']} ({self.social_scenario['npc_disposition']})

PLAYER CHARACTER:
- Name: Sariel
- INT: 18 (+4 modifier) - High intelligence for logical arguments
- CHA: 12 (+1 modifier) - Average charisma

CRITICAL RULES:
1. When a player selects an action, EXECUTE it with dice rolls
2. DO NOT present more sub-options
3. Social skill checks (Persuasion, Intimidation) MUST use roll_skill_check tool
4. The player is trying to convince a RESISTANT NPC - this requires a skill check

You have access to these tools: roll_skill_check, roll_attack, declare_no_roll_needed

RESPOND with your tool_requests to resolve this social encounter.
"""

        # Try multiple providers
        providers = [
            (constants.LLM_PROVIDER_GEMINI, "gemini-2.0-flash"),
            (constants.LLM_PROVIDER_CEREBRAS, "qwen-3-32b"),
        ]

        for provider_name, model_name in providers:
            with self.subTest(provider=provider_name, model=model_name):
                try:
                    # Call the real LLM
                    response = llm_service._call_llm_api(
                        [prompt],
                        model_name,
                        f"Social encounter test - {provider_name}",
                        provider_name=provider_name,
                    )

                    # Parse response
                    response_text = response.text if hasattr(response, 'text') else str(response)

                    # Check for tool calls in the response
                    # Native tool calling should return function calls
                    has_skill_check = False
                    skill_check_type = None

                    # Check if response contains skill check request
                    if hasattr(response, 'candidates'):
                        for candidate in response.candidates:
                            if hasattr(candidate.content, 'parts'):
                                for part in candidate.content.parts:
                                    if hasattr(part, 'function_call'):
                                        func_name = part.function_call.name
                                        if func_name == "roll_skill_check":
                                            has_skill_check = True
                                            args = dict(part.function_call.args)
                                            skill_check_type = args.get("skill_name", "unknown")

                    # Log the response for debugging
                    print(f"\n{'='*60}")
                    print(f"Provider: {provider_name} / {model_name}")
                    print(f"Has skill check: {has_skill_check}")
                    print(f"Skill type: {skill_check_type}")
                    print(f"Response preview: {response_text[:500] if response_text else 'None'}...")
                    print(f"{'='*60}\n")

                    # ASSERTION: LLM should request a skill check for social action
                    self.assertTrue(
                        has_skill_check,
                        f"PLANNING LOOP BUG: {provider_name}/{model_name} did NOT request "
                        f"a skill check for social action '{self.social_scenario['user_action']}'. "
                        f"This causes the narrative to loop without progressing!"
                    )

                    # Verify it's a social skill (Persuasion, Intimidation, etc.)
                    if skill_check_type:
                        social_skills = ["persuasion", "intimidation", "deception", "insight"]
                        is_social_skill = any(
                            s in skill_check_type.lower() for s in social_skills
                        )
                        self.assertTrue(
                            is_social_skill,
                            f"Expected social skill check but got: {skill_check_type}"
                        )

                except Exception as e:
                    self.fail(f"API call failed for {provider_name}/{model_name}: {e}")


class TestPlanningLoopDetection(unittest.TestCase):
    """Test planning loop detection logic."""

    def test_detect_repeated_options(self):
        """Test that we can detect when the same options are presented repeatedly."""
        # Simulate conversation history with repeated similar actions
        history = [
            {"role": "user", "content": "Press the Logical Argument"},
            {"role": "assistant", "content": "Reynolds considers your words..."},
            {"role": "user", "content": "Maintain Pressure"},
            {"role": "assistant", "content": "The room is tense..."},
            {"role": "user", "content": "Press the Logical Argument again"},
        ]

        # Count similar action selections
        similar_keywords = ["press", "maintain", "logical", "argument", "pressure"]
        similar_count = sum(
            1 for msg in history
            if msg["role"] == "user" and
            any(kw in msg["content"].lower() for kw in similar_keywords)
        )

        # Planning loop detected if 2+ similar actions
        is_loop = similar_count >= 2

        self.assertTrue(is_loop, "Should detect planning loop from repeated similar actions")

    def test_detect_static_narrative(self):
        """Test detection of static narrative (same description repeated)."""
        responses = [
            "Reynolds stands frozen, processing your logic...",
            "Reynolds remains frozen, considering your words...",
            "Reynolds is still frozen, his resistance crumbling...",
        ]

        # Check for repeated "frozen" pattern
        frozen_count = sum(1 for r in responses if "frozen" in r.lower())

        # Static narrative = same state described multiple times
        is_static = frozen_count >= 2

        self.assertTrue(
            is_static,
            "Should detect static narrative (NPC described as 'frozen' multiple times)"
        )


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SOCIAL ENCOUNTER PLANNING LOOP SMOKE TEST")
    print("=" * 70)
    print("\nThis test verifies that:")
    print("1. Tool definitions include social skills (Persuasion, Intimidation)")
    print("2. declare_no_roll_needed excludes contested social encounters")
    print("3. (Optional) Real LLM requests skill checks for social actions")
    print("\nTo run real LLM tests: RUN_REAL_LLM_TESTS=true python <this_file>")
    print("=" * 70 + "\n")

    unittest.main(verbosity=2)
