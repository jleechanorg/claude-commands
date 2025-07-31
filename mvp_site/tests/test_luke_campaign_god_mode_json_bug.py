"""Test to reproduce the exact god mode JSON display bug from Luke's campaign log."""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from gemini_response import GeminiResponse
from narrative_response_schema import parse_structured_response


class TestLukeCampaignGodModeJsonBug(unittest.TestCase):
    """Test to reproduce the exact Luke campaign god mode JSON display bug."""

    def test_luke_campaign_scene_31_reproduction(self):
        """Reproduce the exact Scene #31 bug from Luke's campaign."""
        # This is the raw JSON that appeared in Luke's campaign log
        luke_campaign_raw_response = """{
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

        # Parse the response using our current system
        narrative_text, structured_response = parse_structured_response(
            luke_campaign_raw_response
        )

        # The bug: Luke's log showed the raw JSON instead of the processed narrative
        # Our fix should return clean narrative text, not raw JSON

        # Test 1: Should NOT contain raw JSON structure
        assert (
            '"narrative":' not in narrative_text
        ), "Processed narrative should not contain raw JSON keys"
        assert (
            '"god_mode_response":' not in narrative_text
        ), "Processed narrative should not contain raw JSON keys"
        assert (
            '"entities_mentioned":' not in narrative_text
        ), "Processed narrative should not contain raw JSON keys"
        assert (
            "{" not in narrative_text
        ), "Processed narrative should not contain JSON braces"
        assert (
            "}" not in narrative_text
        ), "Processed narrative should not contain JSON braces"

        # Test 2: Should contain the actual god mode response text
        expected_content = (
            "That's another excellent point, and I understand why you'd expect EXP"
        )
        assert (
            expected_content in narrative_text
        ), "Should contain the actual god mode response text"

        # Test 3: Should properly parse structured response
        assert structured_response is not None
        assert len(structured_response.entities_mentioned) == 3
        assert "Luke Skywalker" in structured_response.entities_mentioned

        # Test 4: Create GeminiResponse object as it would be in the real system
        gemini_response = GeminiResponse.create(luke_campaign_raw_response)

        # Test 5: GeminiResponse.narrative_text should be clean (no JSON)
        assert '"god_mode_response":' not in gemini_response.narrative_text
        assert expected_content in gemini_response.narrative_text

    def test_luke_campaign_scene_56_reproduction(self):
        """Reproduce Scene #56 god mode response bug."""
        luke_scene_56_response = """{
    "narrative": "",
    "god_mode_response": "You are absolutely right that corrupting a Level 10 Jedi Master is an incredibly significant act, and it deserved a substantial reward. \\n\\nIn the previous turn (SEQ_ID: 118), I did award you **200 Experience Points** for 'Successfully corrupted the Jedi Master's Force alignment, twisting her to the Dark Side.' This was a direct recognition of that major narrative and mechanical milestone.\\n\\nWhile this wasn't a combat encounter with a standard Challenge Rating that would yield thousands of XP for a kill, the 200 XP represents the profound impact of twisting such a powerful individual's spirit and aligning them to the Dark Side. This act not only solidifies your own Dark Side corruption and demonstrates immense power, but it also provides you with a formidable, albeit broken, asset – a corrupted Jedi Master. The true long-term 'experience' of this event will come from the strategic and combat utility she provides, as well as the dark opportunities her corruption unlocks.\\n\\nYour current XP total is now 200, and you need 2100 more for Level 6. This 200 XP is a significant step towards that next tier of power.\\n\\nI am ready for your next input.",
    "entities_mentioned": ["Luke Skywalker", "Jedi Master"],
    "location_confirmed": "Imperial Installation",
    "state_updates": {},
    "debug_info": {
        "dm_notes": [
            "User questioning XP reward amount",
            "Clarifying previous XP award",
            "Explaining narrative vs combat XP philosophy"
        ]
    }
}"""

        # Test the same processing
        narrative_text, structured_response = parse_structured_response(
            luke_scene_56_response
        )

        # Should return clean narrative, not raw JSON
        assert '{"narrative":' not in narrative_text
        assert '"god_mode_response":' not in narrative_text
        assert "You are absolutely right that corrupting" in narrative_text
        assert "200 Experience Points" in narrative_text

    def test_empty_narrative_with_god_mode_response(self):
        """Test the specific pattern from Luke's campaign: empty narrative + god_mode_response."""
        # This is the exact pattern that appeared in Luke's log
        pattern_response = """{
    "narrative": "",
    "god_mode_response": "Divine intervention occurs as requested.",
    "entities_mentioned": [],
    "location_confirmed": "Unknown",
    "state_updates": {},
    "debug_info": {}
}"""

        narrative_text, structured_response = parse_structured_response(
            pattern_response
        )

        # Should return just the god mode response text, not the JSON structure
        assert narrative_text == "Divine intervention occurs as requested."
        assert '"narrative"' not in narrative_text
        assert '""' not in narrative_text  # Empty string artifacts

    def test_integration_with_gemini_service_flow(self):
        """Test that the god mode response flows correctly through the service layer."""
        # Simulate the flow: raw_response -> parse_structured_response -> GeminiResponse
        raw_ai_response = """{
    "narrative": "",
    "god_mode_response": "The force is strong with this one.",
    "entities_mentioned": ["Luke Skywalker"],
    "location_confirmed": "Death Star",
    "state_updates": {"luke": {"alignment": "chaotic_evil"}},
    "debug_info": {"dm_notes": ["God mode test"]}
}"""

        # Create GeminiResponse using new API (this is what happens in gemini_service.py)
        gemini_response = GeminiResponse.create(raw_ai_response)

        # Step 3: Check that narrative_text is clean (this is what gets displayed)
        assert gemini_response.narrative_text == "The force is strong with this one."
        assert '"god_mode_response":' not in gemini_response.narrative_text

        # Step 4: Check that structured data is preserved
        assert gemini_response.state_updates == {"luke": {"alignment": "chaotic_evil"}}
        assert "Luke Skywalker" in gemini_response.entities_mentioned


if __name__ == "__main__":
    unittest.main()
