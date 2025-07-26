"""Simple test to check if we can isolate the JSON bug."""

import os
import sys
import traceback
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Ensure testing environment
os.environ["TESTING"] = "true"

# Test just the parsing logic with known problematic JSON
from narrative_response_schema import parse_structured_response


class TestSimpleJsonBugCheck(unittest.TestCase):
    """Simple test to check parsing of problematic JSON."""

    def test_character_creation_json_parsing(self):
        """Test parsing of character creation JSON like the user's example."""

        # This is similar to what the AI might return during character creation
        character_creation_json = """{
    "narrative": "[CHARACTER CREATION - Step 1 of 7]\\n\\nWelcome, adventurer! Before we begin your journey, we need to create your character.\\n\\nWould you like to:\\n1. **Create a D&D character** - Choose from established D&D races and classes\\n2. **Let me create one for you** - I'll design a character based on the campaign setting\\n3. **Create a custom character** - Design your own unique character concept with custom class/abilities\\n\\nWhich option would you prefer? (1, 2, or 3)",
    "god_mode_response": "",
    "entities_mentioned": [],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "custom_campaign_state": {
            "character_creation": {
                "in_progress": true,
                "current_step": 1,
                "method_chosen": null
            }
        }
    },
    "debug_info": {
        "dm_notes": ["Starting character creation process"],
        "dice_rolls": [],
        "resources": "Character Creation Mode",
        "state_rationale": "Initializing character creation workflow"
    }
}"""

        print("\\n=== Testing Character Creation JSON Parsing ===")
        print(f"Input JSON length: {len(character_creation_json)}")

        try:
            # Parse the JSON
            result_text, result_obj = parse_structured_response(character_creation_json)

            print("✅ Parsing succeeded!")
            print(f"Result text length: {len(result_text)}")
            print(f"Result preview: {result_text[:100]}...")

            # Verify no JSON artifacts
            has_json_artifacts = (
                '"narrative":' in result_text
                or '"god_mode_response":' in result_text
                or '"entities_mentioned":' in result_text
            )
            print(f"Contains JSON artifacts: {has_json_artifacts}")

            # Test assertions
            self.assertNotIn(
                '"narrative":', result_text, "Should not contain JSON keys"
            )
            self.assertNotIn(
                '"god_mode_response":', result_text, "Should not contain JSON keys"
            )
            self.assertIn(
                "CHARACTER CREATION", result_text, "Should contain actual content"
            )
            self.assertIsNotNone(result_obj, "Should return valid structured response")

            return True

        except Exception as e:
            print(f"❌ Parsing failed with exception: {e}")
            print(f"Exception type: {type(e)}")

            traceback.print_exc()

            # This is the critical test - if parsing fails, what happens?
            self.fail(f"Parsing should not fail: {e}")

    def test_what_happens_on_parsing_exception(self):
        """Test what happens when parsing encounters an exception."""

        # Create malformed JSON that might cause parsing to fail
        malformed_json = """{
    "narrative": "Some content here",
    "god_mode_response": "",
    "entities_mentioned": ["test"],
    "location_confirmed": "Test Location",
    "state_updates": {
        "malformed": "missing closing brace somewhere
    },
    "debug_info": {}
}"""  # This JSON is intentionally malformed

        print("\\n=== Testing Malformed JSON Handling ===")

        try:
            result_text, result_obj = parse_structured_response(malformed_json)

            print(f"Result: {result_text}")
            print(f"Contains original JSON: {malformed_json[:50] in result_text}")

            # Even with malformed JSON, we should not get the original JSON back
            self.assertNotIn(
                'malformed": "missing closing brace',
                result_text,
                "Should not return malformed JSON content",
            )

        except Exception as e:
            print(f"Exception during malformed JSON parsing: {e}")
            # We should handle this gracefully, not throw exceptions
            self.fail(f"Should handle malformed JSON gracefully: {e}")


if __name__ == "__main__":
    unittest.main()
