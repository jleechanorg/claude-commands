"""
Red-Green test for embedded planning block JSON appearing raw in narrative.

BUG REPRODUCTION:
When the LLM includes raw JSON like {"thinking": ..., "choices": ...} in the
narrative text, this JSON should be stripped from the displayed narrative since
the planning_block is a separate structured field.

The user reported seeing raw JSON like:
{
    "thinking": "The family has been completely broken...",
    "choices": {
        "magical_oaths_binding": {...},
        ...
    }
}

This should NOT appear in the narrative text - it should only be in the
separate planning_block field.
"""

import json
import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site.narrative_response_schema import NarrativeResponse, parse_structured_response


class TestEmbeddedJsonInNarrativeBug(unittest.TestCase):
    """Test that embedded JSON is properly stripped from narrative text."""

    def setUp(self):
        """Set up test data replicating the reported bug."""
        # This is the raw JSON that appeared in the user's narrative
        self.embedded_planning_json = '''{
    "thinking": "The family has been completely broken by your dramatic revelation. Now is the perfect moment to extract binding oaths while their psychological defenses are shattered.",
    "choices": {
        "magical_oaths_binding": {
            "text": "Magical Oaths and Binding",
            "description": "Use your spellcasting to magically bind each family member",
            "risk_level": "medium",
            "analysis": {
                "pros": ["Absolute supernatural compulsion", "Immediate results"],
                "cons": ["Consumes spell slots", "Detectable by authorities"],
                "confidence": "High"
            }
        },
        "psychological_dominance": {
            "text": "Psychological Dominance",
            "description": "Extract verbal oaths through terror and pressure",
            "risk_level": "low",
            "analysis": {
                "pros": ["Conserves spell slots", "Undetectable"],
                "cons": ["Potential for resistance"],
                "confidence": "Medium"
            }
        }
    }
}'''

    def test_narrative_with_embedded_planning_json_is_cleaned(self):
        """
        RED TEST: Narrative containing raw planning_block JSON should have it stripped.

        This reproduces the bug where the narrative text contains embedded JSON
        that looks like a planning_block structure (with "thinking" and "choices").
        """
        # Narrative text that contains embedded planning block JSON
        narrative_with_embedded_json = f"""--- PLANNING BLOCK ---

**Tactical Analysis:** Your family revelation has achieved perfect impact.

{self.embedded_planning_json}

The family has been completely broken. Choose your approach."""

        # Create a response where the narrative contains embedded JSON
        llm_response = {
            "narrative": narrative_with_embedded_json,
            "entities_mentioned": ["family", "Marcus", "Elora"],
            "location_confirmed": "Chapel",
            "planning_block": {
                "thinking": "Proper planning block in the correct field",
                "choices": {
                    "option_1": {
                        "text": "Option 1",
                        "description": "First option"
                    }
                }
            }
        }

        response_text = json.dumps(llm_response)
        narrative, response_obj = parse_structured_response(response_text)

        # The narrative should NOT contain raw JSON
        self.assertNotIn('"thinking":', narrative,
            "BUG: Raw JSON key 'thinking' should not appear in narrative")
        self.assertNotIn('"choices":', narrative,
            "BUG: Raw JSON key 'choices' should not appear in narrative")
        self.assertNotIn('"magical_oaths_binding":', narrative,
            "BUG: Raw JSON choice key should not appear in narrative")
        self.assertNotIn('"analysis":', narrative,
            "BUG: Raw JSON nested key should not appear in narrative")

        # Should still have the narrative context text
        self.assertIn("PLANNING BLOCK", narrative)
        self.assertIn("Tactical Analysis", narrative)

    def test_narrative_with_only_embedded_json_is_cleaned(self):
        """
        RED TEST: Narrative that is mostly just embedded JSON should be handled.
        """
        # Narrative that is essentially just the JSON block
        llm_response = {
            "narrative": self.embedded_planning_json,
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "planning_block": {}
        }

        response_text = json.dumps(llm_response)
        narrative, response_obj = parse_structured_response(response_text)

        # The narrative should NOT be raw JSON
        self.assertFalse(narrative.strip().startswith('{'),
            "BUG: Narrative should not start with JSON brace")
        self.assertNotIn('"thinking":', narrative,
            "BUG: Raw JSON should not appear in narrative")

    def test_narrative_response_strips_embedded_json_pattern(self):
        """
        RED TEST: NarrativeResponse should clean embedded JSON patterns from narrative.
        """
        narrative_with_json = f"Before the JSON.\n\n{self.embedded_planning_json}\n\nAfter the JSON."

        response = NarrativeResponse(
            narrative=narrative_with_json,
            entities_mentioned=[],
            location_confirmed="Unknown"
        )

        # The narrative stored should not contain the raw JSON
        self.assertNotIn('"thinking":', response.narrative,
            "BUG: NarrativeResponse should strip embedded JSON from narrative")
        self.assertNotIn('"choices":', response.narrative,
            "BUG: NarrativeResponse should strip embedded JSON choices")

        # Should preserve non-JSON content
        self.assertIn("Before the JSON", response.narrative)
        self.assertIn("After the JSON", response.narrative)

    def test_real_world_bug_case(self):
        """
        RED TEST: Exact reproduction of the user-reported bug.

        The user saw a campaign response where the narrative contained the raw
        planning block JSON followed by the properly parsed planning block below.
        """
        # This is the exact structure the user reported
        narrative_text = """Main Character: Extract Binding Oaths - Use magical methods or psychological pressure.

[SESSION_HEADER]
Timestamp: 1492 DR, Mirtul 16, 02:31:00
Location: Abandoned Sosuke Family Chapel
Status: Lvl 12 Rgr5/Rog4/Brd3 | HP: 105/105

Scene #444: --- PLANNING BLOCK ---

**Tactical Analysis:** Your family revelation has achieved perfect impact.

{
    "thinking": "The family has been completely broken by your dramatic revelation.",
    "choices": {
        "magical_oaths_binding": {
            "text": "Magical Oaths and Binding",
            "description": "Use spellcasting to bind family members",
            "risk_level": "medium"
        }
    }
}

The family has been completely broken."""

        llm_response = {
            "narrative": narrative_text,
            "entities_mentioned": ["family"],
            "location_confirmed": "Chapel",
            "session_header": "Timestamp: 1492 DR",
            "planning_block": {
                "thinking": "The family has been completely broken.",
                "choices": {
                    "magical_oaths_binding": {
                        "text": "Magical Oaths and Binding",
                        "description": "Use spellcasting to bind family members",
                        "risk_level": "medium"
                    }
                }
            }
        }

        response_text = json.dumps(llm_response)
        narrative, response_obj = parse_structured_response(response_text)

        # The critical assertion: raw JSON should NOT appear in narrative
        self.assertNotIn('{\n    "thinking":', narrative,
            "BUG: Raw embedded JSON block should be stripped from narrative")
        self.assertNotIn('"choices": {', narrative,
            "BUG: Raw JSON choices should be stripped from narrative")

        # The planning_block field should still have the proper data
        self.assertIsNotNone(response_obj.planning_block)
        self.assertIn("thinking", response_obj.planning_block)


class TestEmbeddedJsonStripping(unittest.TestCase):
    """Test the JSON stripping utility functions."""

    def test_detect_embedded_planning_block_json(self):
        """Test detection of embedded planning block JSON pattern."""
        text_with_json = '''Some narrative text.

{
    "thinking": "Planning thoughts",
    "choices": {
        "option1": {"text": "Option 1"}
    }
}

More narrative text.'''

        # Should detect this as containing embedded planning JSON
        import re
        planning_json_pattern = re.compile(
            r'\{\s*"thinking"\s*:\s*"[^"]*"[^}]*"choices"\s*:\s*\{',
            re.DOTALL
        )

        self.assertIsNotNone(planning_json_pattern.search(text_with_json),
            "Should detect embedded planning block JSON pattern")

    def test_strip_embedded_planning_json(self):
        """Test stripping embedded planning block JSON from text."""
        import re

        text_with_json = '''Before.

{
    "thinking": "Test",
    "choices": {
        "a": {"text": "A"}
    }
}

After.'''

        # Pattern to match full planning block JSON
        # This pattern matches { "thinking": "..." ... "choices": { ... } }
        planning_block_pattern = re.compile(
            r'\{\s*"thinking"\s*:\s*"[^"]*(?:\\.[^"]*)*"[^}]*"choices"\s*:\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}\s*\}',
            re.DOTALL
        )

        cleaned = planning_block_pattern.sub('', text_with_json).strip()

        self.assertNotIn('"thinking":', cleaned)
        self.assertIn("Before", cleaned)
        self.assertIn("After", cleaned)


if __name__ == "__main__":
    unittest.main()
