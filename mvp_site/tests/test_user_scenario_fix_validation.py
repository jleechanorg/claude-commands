"""Test to validate the main user scenario fix - no more raw JSON in god mode."""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from narrative_response_schema import parse_structured_response


class TestUserScenarioFixValidation(unittest.TestCase):
    """Validate that the main user scenario is fixed."""

    def test_luke_scenario_scene_116_type_issue(self):
        """Test the exact type of malformed JSON that caused Luke's issue."""
        # This simulates what might happen when AI generates malformed god mode JSON
        malformed_god_mode_json = """{
    "narrative": "",
    "god_mode_response": "The ancient artifact pulses with power as you grasp it. Reality bends to your will.",
    "entities_mentioned": ["ancient artifact"],
    "location_confirmed": "Forgotten Temple",
    "state_updates": {"artifact_acquired": true, "power_level": 9000}
    "debug_info": {"dm_notes": ["Major plot advancement"]}"""  # Missing closing brace and comma

        # This should NOT return raw JSON - should extract the god mode response cleanly
        narrative_text, structured_response = parse_structured_response(
            malformed_god_mode_json
        )

        # PRIMARY VALIDATION: No raw JSON in output
        assert (
            '"god_mode_response":' not in narrative_text
        ), "User should never see raw JSON keys"
        assert (
            '"narrative":' not in narrative_text
        ), "User should never see raw JSON keys"
        assert (
            '"state_updates":' not in narrative_text
        ), "User should never see raw JSON keys"
        assert '{"' not in narrative_text, "User should never see JSON structure"

        # SECONDARY VALIDATION: Should get clean, readable content
        expected_content = "The ancient artifact pulses with power as you grasp it"
        assert (
            expected_content in narrative_text
        ), "User should see the actual god mode response content"
        assert (
            "Reality bends to your will" in narrative_text
        ), "User should see complete god mode response"

        # TERTIARY VALIDATION: Structured data should be preserved
        assert structured_response is not None
        assert "ancient artifact" in structured_response.entities_mentioned
        if hasattr(structured_response, "god_mode_response"):
            assert "ancient artifact" in structured_response.god_mode_response

    def test_various_malformation_scenarios(self):
        """Test different types of JSON malformation that could occur."""
        scenarios = [
            # Missing closing brace
            (
                "Missing brace",
                """{
                "narrative": "",
                "god_mode_response": "The gods speak through thunder.",
                "entities_mentioned": ["gods"]""",
            ),
            # Invalid JSON but valid content
            (
                "Invalid JSON",
                '''{
                "narrative": "",
                "god_mode_response": "Lightning strikes the battlefield.",
                "entities_mentioned": ["lightning", "battlefield"],
                "state_updates": {"weather": "stormy"}
                "location_confirmed": "Battlefield"''',
            ),  # Missing comma
            # Truncated response
            (
                "Truncated",
                """{
                "narrative": "",
                "god_mode_response": "Ancient magic awakens and""",
            ),  # Cut off mid-sentence
        ]

        for scenario_name, malformed_json in scenarios:
            with self.subTest(scenario=scenario_name):
                narrative_text, structured_response = parse_structured_response(
                    malformed_json
                )

                # Should never return raw JSON structure
                assert (
                    '"god_mode_response":' not in narrative_text
                ), f"Scenario '{scenario_name}' returned raw JSON"
                assert (
                    '"narrative":' not in narrative_text
                ), f"Scenario '{scenario_name}' returned raw JSON"

                # Should have some readable content (not empty)
                assert (
                    len(narrative_text.strip()) > 0
                ), f"Scenario '{scenario_name}' returned empty result"

                # Content should be readable text, not JSON
                assert not narrative_text.strip().startswith(
                    "{"
                ), f"Scenario '{scenario_name}' starts with JSON brace"

    def test_normal_god_mode_still_works(self):
        """Ensure normal god mode responses still work correctly."""
        normal_god_mode = """{
            "narrative": "",
            "god_mode_response": "The cosmic force acknowledges your command.",
            "entities_mentioned": ["cosmic force"],
            "location_confirmed": "Void of Space",
            "state_updates": {"cosmic_awareness": true},
            "debug_info": {"dm_notes": ["God mode test"]}
        }"""

        narrative_text, structured_response = parse_structured_response(normal_god_mode)

        # Should work perfectly for valid JSON
        assert narrative_text == "The cosmic force acknowledges your command."
        assert "cosmic force" in structured_response.entities_mentioned
        assert structured_response.location_confirmed == "Void of Space"

    def test_edge_case_empty_god_mode_response(self):
        """Test edge case where god_mode_response exists but is empty."""
        empty_god_mode = """{
            "narrative": "The story continues with normal narrative.",
            "god_mode_response": "",
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative_text, structured_response = parse_structured_response(empty_god_mode)

        # Should fall back to narrative when god_mode_response is empty
        assert narrative_text == "The story continues with normal narrative."


if __name__ == "__main__":
    unittest.main()
