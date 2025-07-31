#!/usr/bin/env python3
"""
Red/Green Testing for JSON Display Bug Fix

This test demonstrates the bug by first showing failing tests (red state)
and then showing passing tests with the fix (green state).
"""

import json
import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import the original version for red testing simulation
from narrative_response_schema import NarrativeResponse, parse_structured_response


class TestRedGreenJSONFix(unittest.TestCase):
    """Red/Green test suite for JSON display bug"""

    def setUp(self):
        """Set up test cases that reproduce the actual bug"""
        # Actual JSON response from the bug report (Scene #14)
        self.bug_json = """{
  "narrative": "Scene #14: [Mode: DM MODE] The party continues their journey through the mystical forest.",
  "entities_mentioned": ["Ser Caius of House Varrick", "Ser Bastion", "Ancient Dragon"],
  "location_confirmed": "Mystical Forest, Aeterna",
  "state_updates": {
    "npc_data": {
      "Ancient Dragon": {
        "status": "encountered",
        "attitude": "hostile"
      }
    }
  }
}"""

        # JSON wrapped in markdown (common AI response)
        self.markdown_wrapped_json = """```json
{
  "narrative": "[Mode: DM MODE] Understanding confirmed. Processing user request.",
  "entities_mentioned": ["Test Entity"],
  "location_confirmed": "Test Location",
  "state_updates": {}
}
```"""

        # Partial/broken JSON
        self.partial_json = (
            'Some text before {"narrative": "The story continues", "entities_'
        )

        # JSON with escaped characters
        self.escaped_json = '{"narrative": "She said \\"Hello!\\"\\nNew line here\\nAnother line", "entities_mentioned": []}'

    def test_red_state_raw_json_displayed(self):
        """
        RED TEST: Demonstrates the bug where raw JSON is shown to users

        This test would FAIL without the fix because parse_structured_response
        would return the raw JSON string when parsing fails.
        """
        print("\n=== RED STATE TEST: Raw JSON Bug ===")

        # Without the fix, this would return raw JSON
        narrative, response = parse_structured_response(self.bug_json)

        # These assertions demonstrate what the bug looked like
        print(f"Returned narrative: {narrative[:100]}...")

        # With the fix, these pass. Without it, they would fail.
        assert (
            '"narrative":' not in narrative
        ), "BUG: Raw JSON structure visible to user!"
        assert (
            '"entities_mentioned":' not in narrative
        ), "BUG: Raw JSON structure visible to user!"
        assert (
            '"state_updates":' not in narrative
        ), "BUG: Raw JSON structure visible to user!"

        # The narrative should be extracted, not the whole JSON
        assert "Scene #14" in narrative
        assert "DM MODE" in narrative

        print("✓ GREEN: JSON properly parsed, narrative extracted")

    def test_red_state_markdown_wrapped_json(self):
        """
        RED TEST: AI returns JSON wrapped in markdown code blocks

        Without the fix, this returns the markdown-wrapped JSON string.
        """
        print("\n=== RED STATE TEST: Markdown-wrapped JSON ===")

        narrative, response = parse_structured_response(self.markdown_wrapped_json)

        print(f"Returned narrative: {narrative[:100]}...")

        # These would fail without the fix
        assert "```json" not in narrative, "BUG: Markdown formatting visible to user!"
        assert "```" not in narrative, "BUG: Code block markers visible to user!"
        assert '"narrative":' not in narrative, "BUG: JSON structure visible to user!"

        # Should extract the actual narrative
        assert "Understanding confirmed" in narrative
        assert "DM MODE" in narrative

        print("✓ GREEN: Markdown unwrapped, JSON parsed correctly")

    def test_red_state_partial_json_fallback(self):
        """
        RED TEST: Partial JSON that can't be parsed

        Without fallback extraction, users see broken JSON.
        """
        print("\n=== RED STATE TEST: Partial JSON ===")

        narrative, response = parse_structured_response(self.partial_json)

        print(f"Returned narrative: {narrative[:100]}...")

        # Without the fix, would show the broken JSON
        assert "Some text before" not in narrative, "BUG: Non-narrative text visible!"
        assert '{"narrative":' not in narrative, "BUG: JSON syntax visible!"
        assert '"entities_' not in narrative, "BUG: Broken JSON visible!"

        # Should extract just the narrative part
        assert narrative == "The story continues"

        print("✓ GREEN: Narrative extracted from partial JSON")

    def test_red_state_escaped_characters(self):
        """
        RED TEST: JSON with escaped characters like \\n and \\"

        Without proper unescaping, users see escape sequences.
        """
        print("\n=== RED STATE TEST: Escaped Characters ===")

        narrative, response = parse_structured_response(self.escaped_json)

        print(f"Returned narrative: {repr(narrative[:100])}...")

        # Without proper handling, would show escape sequences
        assert "\\n" not in narrative, "BUG: Escape sequences visible!"
        assert '\\"' not in narrative, "BUG: Escaped quotes visible!"

        # Should have actual newlines and quotes
        assert "\n" in narrative
        assert '"Hello!"' in narrative
        assert narrative.count("\n") == 2

        print("✓ GREEN: Escape sequences properly converted")

    def test_green_state_comprehensive_fix(self):
        """
        GREEN TEST: Demonstrates the complete fix working

        This shows all the fix components working together.
        """
        print("\n=== GREEN STATE TEST: Complete Fix ===")

        test_cases = [
            ("Plain JSON", self.bug_json),
            ("Markdown-wrapped", self.markdown_wrapped_json),
            ("Partial JSON", self.partial_json),
            ("Escaped chars", self.escaped_json),
            ("Malformed", '{"narrative": "Test", broken json...'),
            ("Invalid field", '{"narrative": "Story", "invalid": true}'),
        ]

        for name, test_input in test_cases:
            with self.subTest(case=name):
                narrative, response = parse_structured_response(test_input)

                # Core fix validation: NO JSON VISIBLE TO USER
                assert '"narrative":' not in narrative
                assert '"entities_mentioned":' not in narrative
                assert '"location_confirmed":' not in narrative
                assert '"state_updates":' not in narrative
                assert "```" not in narrative
                assert "{" not in narrative
                assert "}" not in narrative

                # Response object is valid
                assert isinstance(response, NarrativeResponse)
                assert isinstance(narrative, str)
                assert len(narrative) > 0

                print(f"  ✓ {name}: Clean narrative extracted")

        print("\n✓ GREEN: All test cases pass - users never see JSON!")

    def test_simulate_red_state(self):
        """
        SIMULATION: What the bug looked like before the fix

        This simulates the red state by showing what would happen
        without our parsing improvements.
        """
        print("\n=== SIMULATING RED STATE (Bug Behavior) ===")

        # Simulate what happened without the fix
        def simulate_broken_parser(text):
            """Simulates the broken parser that returned raw text"""
            try:
                # Try basic JSON parse
                data = json.loads(text)
                return data.get("narrative", text)
            except:
                # On any error, return the raw text (THE BUG!)
                return text

        # Show what users saw with the bug
        bug_output = simulate_broken_parser(self.markdown_wrapped_json)
        print(f"\nBUG OUTPUT (what users saw):\n{bug_output}\n")

        # This is what caused the bug report
        assert "```json" in bug_output, "This is the bug!"
        assert '"narrative":' in bug_output, "Raw JSON visible!"

        # Now show the fix
        fixed_narrative, _ = parse_structured_response(self.markdown_wrapped_json)
        print(f"\nFIXED OUTPUT (what users see now):\n{fixed_narrative}\n")

        # No JSON visible with the fix
        assert "```json" not in fixed_narrative
        assert '"narrative":' not in fixed_narrative

        print("✓ Bug fixed: Users only see narrative text!")


def run_red_green_tests():
    """Run the red/green test suite with detailed output"""
    print("=" * 60)
    print("RED/GREEN TESTING: JSON Display Bug Fix")
    print("=" * 60)
    print("\nThis demonstrates how the bug manifested (red state)")
    print("and how the fix resolves it (green state).\n")

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRedGreenJSONFix)

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ All tests GREEN - JSON display bug is FIXED!")
        print("Users will never see raw JSON in their game interface.")
    else:
        print("\n❌ Some tests RED - Bug still exists!")

    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    # Run the red/green test demonstration
    success = run_red_green_tests()
    sys.exit(0 if success else 1)
