"""
Regression test for God Mode combined narrative preservation bug.

BUG (Fixed in PR #3727):
When LLM returns:
- god_mode_response: Contains actual answer (e.g., spell DC calculation)
- narrative: Empty or minimal
- planning_block: Contains thinking text

The _apply_planning_fallback() replaces empty narrative with placeholder:
"You pause to consider your options..."

Then create_from_structured_response() was NOT receiving the combined
narrative (god_mode_response + narrative) as combined_narrative_text,
so it used the placeholder instead of the actual content.

Evidence from scene #187 in campaign qHCtkGaQdhoAeelmAP0f:
- LLM calculated spell DC = 22 correctly
- PARSED_RESPONSE: narrative_length=1005 (correct)
- FINAL_RESPONSE: narrative_length=37 (broken - just placeholder)
- User saw: "You pause to consider your options..."
- Expected: The spell DC calculation and explanation

FIX: Pass narrative_text as combined_narrative_text to create_from_structured_response.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

# Ensure TESTING_AUTH_BYPASS is set before importing app modules
os.environ.setdefault("TESTING_AUTH_BYPASS", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

from mvp_site.llm_response import LLMResponse
from mvp_site.narrative_response_schema import parse_structured_response


class TestGodModeCombinedNarrativePreservation(unittest.TestCase):
    """
    Regression tests for God Mode combined narrative preservation.

    Tests that god_mode_response content is NOT replaced by placeholder
    when narrative is empty but planning_block exists.
    """

    def test_god_mode_response_preserved_with_empty_narrative_and_planning_block(self):
        """
        RED TEST (would fail before fix): god_mode_response must be preserved
        when narrative is empty but planning_block exists.

        This is the exact scenario from scene #187:
        - god_mode_response has actual content
        - narrative is empty
        - planning_block has thinking text
        """
        # This is the LLM response format that triggers the bug
        llm_response = json.dumps({
            "god_mode_response": """## Spell DC Calculation

Your Spell Save DC is **22**, calculated as follows:
- Base: 8
- Proficiency Bonus: +4
- Charisma Modifier: +6 (CHA 21 → +5, plus +1 from items)
- Equipment Bonus: +4 (from Silk of the Abyssal Weaver)

**Total: 8 + 4 + 6 + 4 = 22**

The game state has been updated to reflect DC 22.""",
            "narrative": "",  # Empty narrative - triggers _apply_planning_fallback
            "planning_block": {
                "thinking": "User asked about spell DC. Let me calculate it step by step...",
                "options": []
            },
            "entities_mentioned": ["Nocturne Sosuke"],
            "location_confirmed": "Tollhouse Vault"
        })

        # Parse the structured response
        narrative_text, structured_response = parse_structured_response(llm_response)

        # CRITICAL CHECK 1: Combined narrative should contain god_mode_response
        self.assertIn(
            "Spell DC Calculation",
            narrative_text,
            f"Combined narrative should contain god_mode_response content. "
            f"Got: {narrative_text[:200]}..."
        )
        self.assertIn(
            "22",
            narrative_text,
            f"Combined narrative should contain the calculated DC value. "
            f"Got: {narrative_text[:200]}..."
        )

        # CRITICAL CHECK 2: Should NOT be the placeholder
        self.assertNotEqual(
            narrative_text.strip(),
            "You pause to consider your options...",
            "Combined narrative should NOT be replaced by placeholder"
        )

        # CRITICAL CHECK 3: Create LLMResponse and verify narrative is preserved
        llm_response_obj = LLMResponse.create_from_structured_response(
            structured_response,
            "gemini-3-flash-preview",
            combined_narrative_text=narrative_text,  # This is the fix!
        )

        # Final narrative should contain god_mode_response
        self.assertIn(
            "Spell DC Calculation",
            llm_response_obj.narrative_text,
            f"LLMResponse.narrative_text should contain god_mode_response. "
            f"Got: {llm_response_obj.narrative_text[:200]}..."
        )

        # Should NOT be placeholder
        self.assertNotEqual(
            llm_response_obj.narrative_text.strip(),
            "You pause to consider your options...",
            "LLMResponse.narrative_text should NOT be placeholder"
        )

    def test_without_combined_narrative_text_uses_placeholder_bug(self):
        """
        Demonstrates the bug when combined_narrative_text is NOT passed.

        This shows what happens without the fix - the placeholder replaces
        the actual god_mode_response content.
        """
        llm_response = json.dumps({
            "god_mode_response": "Your Spell Save DC is 22.",
            "narrative": "",  # Empty - triggers placeholder
            "planning_block": {"thinking": "Calculating...", "options": []},
            "entities_mentioned": [],
            "location_confirmed": ""
        })

        # Parse the structured response
        narrative_text, structured_response = parse_structured_response(llm_response)

        # The combined narrative DOES contain god_mode_response
        self.assertIn("22", narrative_text)

        # But if we DON'T pass combined_narrative_text, we get placeholder
        llm_response_obj = LLMResponse.create_from_structured_response(
            structured_response,
            "gemini-3-flash-preview",
            # combined_narrative_text NOT passed - this is the bug!
        )

        # WITHOUT the fix, this would be the placeholder
        # The structured_response.narrative was set to placeholder by _apply_planning_fallback
        # This test documents the buggy behavior (but won't fail because structured_response.narrative
        # is the placeholder when narrative is empty and planning_block exists)

        # Check that structured_response.narrative IS the placeholder
        # (this is the intermediate state that causes the bug)
        self.assertEqual(
            structured_response.narrative.strip(),
            "You pause to consider your options...",
            "structured_response.narrative should be placeholder when narrative empty + planning_block"
        )

    def test_god_mode_response_with_minimal_narrative_uses_narrative(self):
        """
        Test that when both narrative and god_mode_response exist, narrative is used.

        Per _combine_god_mode_and_narrative: if both exist, return ONLY narrative
        to avoid duplication. The god_mode_response is for DM-only content.
        """
        llm_response = json.dumps({
            "god_mode_response": "DM note: Player asked about level 9 features.",
            "narrative": "Acknowledged. Your Level 9 features are now active.",  # Non-empty
            "entities_mentioned": [],
            "location_confirmed": ""
        })

        narrative_text, structured_response = parse_structured_response(llm_response)

        # When BOTH exist, narrative takes precedence (to avoid duplication)
        self.assertIn("Acknowledged", narrative_text)
        self.assertIn("Level 9", narrative_text)

        # Create LLMResponse with combined narrative
        llm_response_obj = LLMResponse.create_from_structured_response(
            structured_response,
            "gemini-3-flash-preview",
            combined_narrative_text=narrative_text,
        )

        self.assertIn("Level 9", llm_response_obj.narrative_text)

    def test_no_god_mode_response_uses_narrative_directly(self):
        """
        Test normal (non-god-mode) responses work correctly.
        """
        llm_response = json.dumps({
            "narrative": "You enter the dungeon. The air is thick with dust.",
            "entities_mentioned": [],
            "location_confirmed": "Dungeon Entrance"
        })

        narrative_text, structured_response = parse_structured_response(llm_response)

        # Should be the narrative
        self.assertEqual(narrative_text.strip(), structured_response.narrative.strip())
        self.assertIn("dungeon", narrative_text.lower())

        # LLMResponse should have the narrative
        llm_response_obj = LLMResponse.create_from_structured_response(
            structured_response,
            "gemini-3-flash-preview",
            combined_narrative_text=narrative_text,
        )

        self.assertIn("dungeon", llm_response_obj.narrative_text.lower())


class TestGodModeCombinedNarrativeIntegration(unittest.TestCase):
    """
    Additional integration tests for edge cases.
    """

    def test_code_execution_result_with_god_mode_response(self):
        """
        Test that god_mode_response is preserved even when code execution is used.

        This matches the real scenario from scene #187 where the LLM used code
        execution to calculate spell DC but the result was lost.
        """
        # This simulates the LLM response after code execution
        llm_response = json.dumps({
            "god_mode_response": """## Game State: Spell DC

Based on code execution calculation:
- Spell Save DC = 22
- Calculation: 8 (base) + 4 (prof) + 6 (CHA) + 4 (items) = 22

The game state field `player_character_data.spell_dc` is now set to 22.""",
            "narrative": "",  # Empty - triggers placeholder bug
            "planning_block": {
                "thinking": "Running calculation to verify spell DC...",
                "options": []
            },
            "entities_mentioned": [],
            "location_confirmed": "",
            "debug_info": {
                "code_execution_used": True,
                "stdout": '{"calculation": {"base": 8, "proficiency": 4, "charisma_mod": 6, "equipment": 4, "total": 22}}'
            }
        })

        narrative_text, structured_response = parse_structured_response(llm_response)

        # The combined narrative should contain the god_mode_response
        self.assertIn("Spell DC", narrative_text)
        self.assertIn("22", narrative_text)

        # Create LLMResponse with combined narrative (the fix)
        llm_response_obj = LLMResponse.create_from_structured_response(
            structured_response,
            "gemini-3-flash-preview",
            combined_narrative_text=narrative_text,
        )

        # Verify god_mode_response is preserved
        self.assertIn("22", llm_response_obj.narrative_text)
        self.assertNotEqual(
            llm_response_obj.narrative_text.strip(),
            "You pause to consider your options...",
            "Should NOT be placeholder when god_mode_response has content"
        )

    def test_empty_god_mode_response_with_planning_uses_placeholder(self):
        """
        Test that placeholder IS used when god_mode_response is also empty.

        The placeholder is correct behavior when BOTH narrative and
        god_mode_response are empty but planning_block has thinking.
        """
        llm_response = json.dumps({
            "god_mode_response": "",  # Empty god_mode_response
            "narrative": "",  # Empty narrative
            "planning_block": {
                "thinking": "Considering the options...",
                "options": [
                    {"action": "Attack", "outcome": "Damage the enemy"},
                    {"action": "Defend", "outcome": "Reduce incoming damage"}
                ]
            },
            "entities_mentioned": [],
            "location_confirmed": ""
        })

        narrative_text, structured_response = parse_structured_response(llm_response)

        # With BOTH empty, placeholder is correct (thinking is shown separately)
        self.assertEqual(
            narrative_text.strip(),
            "You pause to consider your options...",
            "Placeholder is correct when both narrative and god_mode_response are empty"
        )


if __name__ == "__main__":
    unittest.main()
