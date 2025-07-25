"""Debug test to identify exactly where god mode response parsing fails."""

import os
import sys
import unittest

import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))
from narrative_response_schema import _combine_god_mode_and_narrative

import json
import logging

from narrative_response_schema import NarrativeResponse, parse_structured_response


class TestGodModeResponseParsingDebug(unittest.TestCase):
    """Debug test to find the exact failure point in god mode response parsing."""

    def setUp(self):
        """Set up logging to capture debug information."""
        logging.basicConfig(level=logging.DEBUG)

    def test_luke_campaign_scene_31_exact_debug(self):
        """Debug the exact Scene #31 response from Luke's campaign."""

        # This is the exact JSON that should have been processed correctly
        luke_scene_31 = """{
    "narrative": "",
    "god_mode_response": "That's another excellent point, and I understand why you'd expect EXP for such a significant and impactful act. \\n\\nFrom a mechanical perspective, the 'visions of your friends' were not true creatures or enemies with a defined Challenge Rating (CR) or a threat profile that would typically grant EXP in D&D 5E. They were an internal, psychological projection, a manifestation of your past weaknesses and attachments.\\n\\nThink of it as the culmination of your commitment to the Dark Side. The 'reward' for that act of purging was the deeper solidification of your corruption, represented by the acquisition of the 'Purity of Hatred' feature, and the definitive shift in your alignment to 'Chaotic Evil'. These are powerful narrative and mechanical gains that unlock new avenues for your character.\\n\\nWhile incredibly brutal and effective, that specific act was a *rite of passage* into your new Dark Side identity, rather than a combat encounter against a living foe. The experience gained from that moment is the *transformation itself* and the abilities it has unlocked within you, setting the stage for future encounters where you *will* earn experience for tangible victories.\\n\\nYour upcoming confrontation with the Jedi Master, for instance, represents a concrete challenge that will certainly yield EXP upon its resolution.",
    "entities_mentioned": ["Luke Skywalker", "Darth Vader", "Jedi Master"],
    "location_confirmed": "Imperial Installation",
    "state_updates": {},
    "debug_info": {
        "dm_notes": [
            "User questioning EXP mechanics",
            "Clarifying D&D 5E rules vs narrative rewards",
            "Setting expectations for future encounters"
        ]
    }
}"""

        # Debug: Test JSON parsing first
        try:
            parsed_json = json.loads(luke_scene_31)
            print(f"JSON parsing successful. Keys: {list(parsed_json.keys())}")
            print(f"narrative: '{parsed_json.get('narrative')}'")
            print(
                f"god_mode_response length: {len(parsed_json.get('god_mode_response', ''))}"
            )
        except json.JSONDecodeError as e:
            self.fail(f"JSON parsing failed: {e}")

        # Debug: Test parse_structured_response
        try:
            narrative_text, structured_response = parse_structured_response(
                luke_scene_31
            )
            print("parse_structured_response succeeded")
            print(
                f"Returned narrative_text: '{narrative_text[:100]}...' (length: {len(narrative_text)})"
            )
            print(f"Structured response type: {type(structured_response)}")

            # Test the critical issue: should NOT contain JSON structure
            self.assertNotIn(
                '"narrative":', narrative_text, "Should not contain JSON keys"
            )
            self.assertNotIn(
                '"god_mode_response":', narrative_text, "Should not contain JSON keys"
            )
            self.assertNotIn("{", narrative_text, "Should not contain JSON braces")

            # Should contain the actual content
            self.assertIn("That's another excellent point", narrative_text)

        except Exception as e:
            self.fail(f"parse_structured_response failed: {e}")

    def test_narrative_response_creation_with_god_mode(self):
        """Test if NarrativeResponse creation fails with god mode data."""

        god_mode_data = {
            "narrative": "",
            "god_mode_response": "Test god mode response",
            "entities_mentioned": ["Test Entity"],
            "location_confirmed": "Test Location",
            "state_updates": {},
            "debug_info": {},
        }

        # Test if NarrativeResponse can be created directly
        try:
            response = NarrativeResponse(**god_mode_data)
            print("NarrativeResponse creation succeeded")
            print(
                f"Has god_mode_response attr: {hasattr(response, 'god_mode_response')}"
            )
            if hasattr(response, "god_mode_response"):
                print(f"god_mode_response value: {response.god_mode_response}")
        except Exception as e:
            print(f"NarrativeResponse creation failed: {e}")
            # This might explain why it falls to the except block

    def test_simulate_parsing_paths(self):
        """Simulate different parsing paths to see which one is taken."""

        test_response = """{
    "narrative": "",
    "god_mode_response": "Test response for path debugging",
    "entities_mentioned": [],
    "location_confirmed": "Test",
    "state_updates": {},
    "debug_info": {}
}"""

        # Step 1: Parse JSON


        parsed_data = json.loads(test_response)

        # Step 2: Try to create NarrativeResponse
        try:
            validated_response = NarrativeResponse(**parsed_data)
            print("MAIN PATH: NarrativeResponse creation succeeded")

            # Check if god_mode_response handling works
            if (
                hasattr(validated_response, "god_mode_response")
                and validated_response.god_mode_response
            ):
                print("MAIN PATH: god_mode_response detected")


                combined_response = _combine_god_mode_and_narrative(
                    validated_response.god_mode_response, validated_response.narrative
                )
                print(f"MAIN PATH: Combined response: '{combined_response}'")
                return "main_path"
            print("MAIN PATH: No god_mode_response or empty")
            return "main_path_no_god_mode"

        except Exception as e:
            print(f"FALLBACK PATH: NarrativeResponse creation failed: {e}")

            # Fallback path for god mode
            god_mode_response = parsed_data.get("god_mode_response")
            if god_mode_response:
                print("FALLBACK PATH: god_mode_response detected")
                narrative = parsed_data.get("narrative")
                if narrative is None:
                    narrative = ""


                combined_response = _combine_god_mode_and_narrative(
                    god_mode_response, narrative
                )
                print(f"FALLBACK PATH: Combined response: '{combined_response}'")
                return "fallback_path"
            print("FALLBACK PATH: No god_mode_response")
            return "fallback_path_no_god_mode"

    def test_check_narrative_response_schema(self):
        """Check if NarrativeResponse schema supports god_mode_response field."""

        # Check the NarrativeResponse class definition
        print(
            f"NarrativeResponse fields: {getattr(NarrativeResponse, '__annotations__', 'No annotations')}"
        )

        # Try to create a minimal god mode response
        try:
            response = NarrativeResponse(
                narrative="",
                god_mode_response="test",
                entities_mentioned=[],
                location_confirmed="test",
                state_updates={},
                debug_info={},
            )
            print("God mode response creation succeeded")
        except TypeError as e:
            print(f"God mode response creation failed - field not supported: {e}")
            return False
        return True


if __name__ == "__main__":
    unittest.main(verbosity=2)
