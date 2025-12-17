#!/usr/bin/env python3
"""
REAL API Test: Social Encounter Planning Loop Detection

This test calls REAL LLMs to verify social skill checks work correctly.
No mock mode - always hits real APIs.

Run with:
    cd testing_mcp && python test_social_encounter_real_api.py

OR run with evidence capture:
    cd testing_mcp && python test_social_encounter_real_api.py --evidence

Expected behavior BEFORE fix:
    - Tool definitions don't mention Persuasion/Intimidation
    - LLM doesn't call roll_skill_check for social encounters
    - Test FAILS

Expected behavior AFTER fix:
    - Tool definitions include social skills
    - LLM calls roll_skill_check for Persuasion/Intimidation/Deception
    - Test PASSES
"""

import json
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# CRITICAL: Set TESTING=false to use real APIs for end-to-end tests
os.environ["TESTING"] = "false"

from mvp_site.game_state import DICE_ROLL_TOOLS


class TestToolDefinitionsForSocialSkills(unittest.TestCase):
    """
    Test that tool definitions include social skills.
    These tests validate the fix for the planning loop bug.
    """

    def test_roll_skill_check_includes_persuasion(self):
        """
        CRITICAL: roll_skill_check MUST mention Persuasion.
        Without this, LLM won't use the tool for social encounters.
        """
        roll_skill_check = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "roll_skill_check":
                roll_skill_check = tool
                break

        self.assertIsNotNone(roll_skill_check, "roll_skill_check tool must exist")

        description = roll_skill_check["function"]["description"].lower()

        self.assertIn(
            "persuasion",
            description,
            f"PLANNING LOOP BUG: roll_skill_check does NOT mention Persuasion!\n"
            f"Current description: {description}\n"
            f"LLM won't know to use this tool for social encounters."
        )

    def test_roll_skill_check_includes_intimidation(self):
        """
        CRITICAL: roll_skill_check MUST mention Intimidation.
        """
        roll_skill_check = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "roll_skill_check":
                roll_skill_check = tool
                break

        self.assertIsNotNone(roll_skill_check, "roll_skill_check tool must exist")

        description = roll_skill_check["function"]["description"].lower()

        self.assertIn(
            "intimidation",
            description,
            f"PLANNING LOOP BUG: roll_skill_check does NOT mention Intimidation!\n"
            f"Current description: {description}"
        )

    def test_roll_skill_check_includes_deception(self):
        """
        CRITICAL: roll_skill_check MUST mention Deception.
        """
        roll_skill_check = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "roll_skill_check":
                roll_skill_check = tool
                break

        self.assertIsNotNone(roll_skill_check, "roll_skill_check tool must exist")

        description = roll_skill_check["function"]["description"].lower()

        self.assertIn(
            "deception",
            description,
            f"PLANNING LOOP BUG: roll_skill_check does NOT mention Deception!\n"
            f"Current description: {description}"
        )

    def test_declare_no_roll_excludes_persuasion(self):
        """
        declare_no_roll_needed MUST explicitly exclude Persuasion.
        Otherwise LLM might skip skill checks for social encounters.
        """
        no_roll_tool = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "declare_no_roll_needed":
                no_roll_tool = tool
                break

        self.assertIsNotNone(no_roll_tool, "declare_no_roll_needed tool must exist")

        description = no_roll_tool["function"]["description"].lower()

        self.assertIn(
            "persuasion",
            description,
            f"BUG: declare_no_roll_needed does NOT exclude Persuasion!\n"
            f"Current description: {description}\n"
            f"LLM might incorrectly skip skill checks for social encounters."
        )

    def test_declare_no_roll_excludes_intimidation(self):
        """
        declare_no_roll_needed MUST explicitly exclude Intimidation.
        """
        no_roll_tool = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "declare_no_roll_needed":
                no_roll_tool = tool
                break

        self.assertIsNotNone(no_roll_tool, "declare_no_roll_needed tool must exist")

        description = no_roll_tool["function"]["description"].lower()

        self.assertIn(
            "intimidation",
            description,
            f"BUG: declare_no_roll_needed does NOT exclude Intimidation!\n"
            f"Current description: {description}"
        )

    def test_declare_no_roll_mentions_convincing_npcs(self):
        """
        declare_no_roll_needed should mention that convincing NPCs needs rolls.
        """
        no_roll_tool = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "declare_no_roll_needed":
                no_roll_tool = tool
                break

        self.assertIsNotNone(no_roll_tool, "declare_no_roll_needed tool must exist")

        description = no_roll_tool["function"]["description"].lower()

        self.assertIn(
            "convincing",
            description,
            f"BUG: declare_no_roll_needed doesn't mention 'convincing' NPCs!\n"
            f"LLM might not understand that resistant NPCs need skill checks."
        )


class TestSocialEncounterRealAPI(unittest.TestCase):
    """
    End-to-end test: Verify LLM actually calls roll_skill_check for social encounters.

    This test makes REAL API calls to verify the fix works in practice.
    """

    @unittest.skipUnless(
        os.environ.get("GEMINI_API_KEY"),
        "Requires GEMINI_API_KEY for live API testing"
    )
    def test_llm_uses_roll_skill_check_for_persuasion(self):
        """
        CRITICAL END-TO-END TEST: LLM must call roll_skill_check for persuasion.

        This test sends a social encounter prompt and verifies the LLM returns
        a tool call for roll_skill_check (not declare_no_roll_needed).
        """
        from mvp_site.llm_providers import gemini_provider

        # Social encounter prompt - player tries to convince a guard
        social_prompt = """You are a D&D 5e Game Master. The player character Aria the Bard is trying to convince a suspicious town guard to let her pass.

Player action: "I try to persuade the guard to let me through, explaining that I'm here on urgent business for the mayor."

Important rules:
1. This is a contested social encounter - the guard is suspicious and needs convincing
2. You MUST roll a Persuasion skill check to determine if the guard believes Aria
3. Use the roll_skill_check tool with skill_name="persuasion"
4. Do NOT use declare_no_roll_needed - this is a contested social interaction

Generate a response with narrative and the appropriate skill check."""

        system_instruction = """You are a Game Master for D&D 5e. For social encounters where the player is trying to convince, intimidate, or deceive an NPC, you MUST use roll_skill_check with the appropriate social skill (Persuasion, Intimidation, or Deception). Never skip skill checks for contested social interactions."""

        # Make the API call - Phase 1 only to check tool selection
        from google import genai
        from google.genai import types

        client = gemini_provider.get_client()

        # Convert DICE_ROLL_TOOLS to Gemini format
        gemini_tools = []
        for tool in DICE_ROLL_TOOLS:
            func_def = tool["function"]
            gemini_tools.append(types.FunctionDeclaration(
                name=func_def["name"],
                description=func_def["description"],
                parameters=func_def.get("parameters"),
            ))

        config = types.GenerateContentConfig(
            max_output_tokens=2000,
            temperature=0.7,
            tools=[types.Tool(function_declarations=gemini_tools)],
            system_instruction=system_instruction,
            # Force tool use - LLM must call a function
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="ANY")
            ),
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[social_prompt],
            config=config,
        )

        # Check if the response includes a function call for roll_skill_check
        function_calls = []
        response_text = ""
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_calls.append({
                        'name': part.function_call.name,
                        'args': dict(part.function_call.args) if part.function_call.args else {}
                    })
                if hasattr(part, 'text') and part.text:
                    response_text += part.text

        # Debug: Print response details
        print(f"\n--- DEBUG: Response Details ---")
        print(f"Function calls: {function_calls}")
        print(f"Text response (first 500 chars): {response_text[:500]}")
        print(f"Tools passed: {[t['function']['name'] for t in DICE_ROLL_TOOLS]}")
        print(f"--- END DEBUG ---\n")

        # Verify roll_skill_check was called
        roll_skill_calls = [fc for fc in function_calls if fc['name'] == 'roll_skill_check']

        self.assertGreater(
            len(roll_skill_calls), 0,
            f"PLANNING LOOP BUG: LLM did NOT call roll_skill_check for social encounter!\n"
            f"Function calls received: {function_calls}\n"
            f"Expected: roll_skill_check with persuasion skill"
        )

        # Verify it's for persuasion
        skill_name = roll_skill_calls[0]['args'].get('skill_name', '').lower()
        self.assertIn(
            'persuasion',
            skill_name,
            f"LLM called roll_skill_check but not for persuasion!\n"
            f"skill_name={skill_name}, expected 'persuasion'"
        )

        print(f"\n✅ SUCCESS: LLM correctly called roll_skill_check for persuasion!")
        print(f"   Function calls: {function_calls}")

    @unittest.skipUnless(
        os.environ.get("GEMINI_API_KEY"),
        "Requires GEMINI_API_KEY for live API testing"
    )
    def test_llm_uses_roll_skill_check_for_intimidation(self):
        """
        E2E TEST: LLM must call roll_skill_check for intimidation.
        """
        from mvp_site.llm_providers import gemini_provider
        from google.genai import types

        social_prompt = """You are a D&D 5e Game Master. The player character Krag the Barbarian is trying to intimidate a bandit into surrendering.

Player action: "I grab the bandit by the collar and growl 'Drop your weapons or I'll crush you like the others!'"

Important rules:
1. This is a contested social encounter - the bandit is scared but might resist
2. You MUST roll an Intimidation skill check
3. Use the roll_skill_check tool with skill_name="intimidation"

Generate a response with narrative and the appropriate skill check."""

        client = gemini_provider.get_client()
        gemini_tools = [types.FunctionDeclaration(
            name=t["function"]["name"],
            description=t["function"]["description"],
            parameters=t["function"].get("parameters"),
        ) for t in DICE_ROLL_TOOLS]

        config = types.GenerateContentConfig(
            max_output_tokens=2000,
            temperature=0.7,
            tools=[types.Tool(function_declarations=gemini_tools)],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="ANY")
            ),
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[social_prompt],
            config=config,
        )

        function_calls = []
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_calls.append({
                        'name': part.function_call.name,
                        'args': dict(part.function_call.args) if part.function_call.args else {}
                    })

        roll_skill_calls = [fc for fc in function_calls if fc['name'] == 'roll_skill_check']
        self.assertGreater(len(roll_skill_calls), 0, f"LLM did NOT call roll_skill_check! Got: {function_calls}")

        skill_name = roll_skill_calls[0]['args'].get('skill_name', '').lower()
        self.assertIn('intimidation', skill_name, f"Expected intimidation, got: {skill_name}")
        print(f"\n✅ SUCCESS: LLM correctly called roll_skill_check for intimidation!")

    @unittest.skipUnless(
        os.environ.get("GEMINI_API_KEY"),
        "Requires GEMINI_API_KEY for live API testing"
    )
    def test_llm_uses_roll_skill_check_for_deception(self):
        """
        E2E TEST: LLM must call roll_skill_check for deception.
        """
        from mvp_site.llm_providers import gemini_provider
        from google.genai import types

        social_prompt = """You are a D&D 5e Game Master. The player character Silvia the Rogue is trying to deceive a merchant about the origin of some goods.

Player action: "I tell the merchant these gems came from my late grandmother's estate, hiding that I actually stole them."

Important rules:
1. This is a contested social encounter - the merchant might see through the lie
2. You MUST roll a Deception skill check
3. Use the roll_skill_check tool with skill_name="deception"

Generate a response with narrative and the appropriate skill check."""

        client = gemini_provider.get_client()
        gemini_tools = [types.FunctionDeclaration(
            name=t["function"]["name"],
            description=t["function"]["description"],
            parameters=t["function"].get("parameters"),
        ) for t in DICE_ROLL_TOOLS]

        config = types.GenerateContentConfig(
            max_output_tokens=2000,
            temperature=0.7,
            tools=[types.Tool(function_declarations=gemini_tools)],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="ANY")
            ),
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[social_prompt],
            config=config,
        )

        function_calls = []
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_calls.append({
                        'name': part.function_call.name,
                        'args': dict(part.function_call.args) if part.function_call.args else {}
                    })

        roll_skill_calls = [fc for fc in function_calls if fc['name'] == 'roll_skill_check']
        self.assertGreater(len(roll_skill_calls), 0, f"LLM did NOT call roll_skill_check! Got: {function_calls}")

        skill_name = roll_skill_calls[0]['args'].get('skill_name', '').lower()
        self.assertIn('deception', skill_name, f"Expected deception, got: {skill_name}")
        print(f"\n✅ SUCCESS: LLM correctly called roll_skill_check for deception!")


def get_tool_description(tool_name: str) -> str:
    """Helper to get tool description for logging."""
    for tool in DICE_ROLL_TOOLS:
        if tool.get("function", {}).get("name") == tool_name:
            return tool["function"]["description"]
    return "Tool not found"


def run_with_evidence():
    """Run tests and save evidence to /tmp."""
    evidence_dir = Path("/tmp/worktree_worker3/social_encounter_fix/e2e_test")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()

    # Capture test output
    import io
    from contextlib import redirect_stdout, redirect_stderr

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        # Run tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestToolDefinitionsForSocialSkills)
        suite.addTests(loader.loadTestsFromTestCase(TestSocialEncounterRealAPI))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

    # Save evidence
    evidence = {
        "timestamp": timestamp,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "success": result.wasSuccessful(),
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue(),
        "tool_descriptions": {
            "roll_skill_check": get_tool_description("roll_skill_check"),
            "declare_no_roll_needed": get_tool_description("declare_no_roll_needed"),
        }
    }

    evidence_file = evidence_dir / f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(evidence_file, 'w') as f:
        json.dump(evidence, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Evidence saved to: {evidence_file}")
    print(f"{'='*70}")

    return result


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SOCIAL ENCOUNTER TOOL DEFINITIONS TEST")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print("\nThis test validates that tool definitions include social skills")
    print("to prevent planning loops in social encounters.")
    print("\nCurrent tool descriptions:")
    print(f"\nroll_skill_check:\n{get_tool_description('roll_skill_check')[:200]}...")
    print(f"\ndeclare_no_roll_needed:\n{get_tool_description('declare_no_roll_needed')[:200]}...")
    print("\n" + "=" * 70 + "\n")

    if "--evidence" in sys.argv:
        sys.argv.remove("--evidence")
        result = run_with_evidence()
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        unittest.main(verbosity=2)
