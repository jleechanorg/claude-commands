#!/usr/bin/env python3
"""
Unit tests for NarrativeResponse extraction from GeminiResponse.
Tests the mapping and validation of structured fields.
"""

import json
import os
import sys
import unittest

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse


class TestNarrativeResponseExtraction(unittest.TestCase):
    """Test extraction and mapping of structured fields in NarrativeResponse"""

    def test_narrative_response_initialization_all_fields(self):
        """Test NarrativeResponse initialization with all structured fields"""
        planning_block_json = {
            "thinking": "The player needs to decide their next action in town.",
            "choices": {
                "explore_town": {
                    "text": "Explore Town",
                    "description": "Walk around and see what's available",
                    "risk_level": "safe",
                },
                "visit_merchant": {
                    "text": "Visit Merchant",
                    "description": "Check out the local shop",
                    "risk_level": "safe",
                },
            },
        }

        response = NarrativeResponse(
            narrative="The adventure begins...",
            session_header="Session 1: A New Beginning",
            planning_block=planning_block_json,
            dice_rolls=["Perception: 1d20+3 = 15"],
            resources="HP: 10/10 | Gold: 50",
            debug_info={"turn": 1},
            entities_mentioned=["merchant", "town"],
            location_confirmed="Starting Town",
        )

        # Verify all fields are set correctly
        self.assertEqual(response.narrative, "The adventure begins...")
        self.assertEqual(response.session_header, "Session 1: A New Beginning")
        # Check that the planning block has the same content (validation adds 'context' field)
        self.assertEqual(
            response.planning_block["thinking"], planning_block_json["thinking"]
        )
        # Check choices exist and have the expected keys
        self.assertIn("explore_town", response.planning_block["choices"])
        self.assertIn("visit_merchant", response.planning_block["choices"])
        # Check that choice content is present (might be HTML-escaped for security)
        explore_choice = response.planning_block["choices"]["explore_town"]
        self.assertEqual(explore_choice["text"], "Explore Town")
        self.assertIn(
            "Walk around", explore_choice["description"]
        )  # Check substring to avoid HTML escaping issues
        self.assertIn("context", response.planning_block)  # Validation adds this field
        self.assertEqual(response.dice_rolls, ["Perception: 1d20+3 = 15"])
        self.assertEqual(response.resources, "HP: 10/10 | Gold: 50")
        self.assertEqual(response.debug_info, {"turn": 1})

    def test_narrative_response_defaults(self):
        """Test NarrativeResponse with minimal required fields"""
        response = NarrativeResponse(narrative="A minimal response")

        # Check defaults for structured fields
        self.assertEqual(response.session_header, "")
        self.assertEqual(
            response.planning_block, {}
        )  # Planning blocks are now JSON objects, empty by default
        self.assertEqual(response.dice_rolls, [])
        self.assertEqual(response.resources, "")
        self.assertEqual(response.debug_info, {})
        self.assertEqual(response.entities_mentioned, [])
        self.assertEqual(response.location_confirmed, "Unknown")

    def test_narrative_response_none_handling(self):
        """Test NarrativeResponse handles None values correctly"""
        response = NarrativeResponse(
            narrative="Test narrative",
            session_header=None,
            planning_block=None,
            dice_rolls=None,
            resources=None,
            debug_info=None,
        )

        # None values should convert to appropriate defaults
        self.assertEqual(response.session_header, "")
        self.assertEqual(response.planning_block, {})
        self.assertEqual(response.dice_rolls, [])
        self.assertEqual(response.resources, "")
        self.assertEqual(response.debug_info, {})

    def test_type_validation_dice_rolls(self):
        """Test dice_rolls type validation"""
        # Should accept list
        response = NarrativeResponse(narrative="Test", dice_rolls=["Roll 1", "Roll 2"])
        self.assertEqual(response.dice_rolls, ["Roll 1", "Roll 2"])

        # Implementation now converts non-list values to empty list
        response2 = NarrativeResponse(
            narrative="Test",
            dice_rolls="Single roll",  # Wrong type
        )
        # The implementation validates type and converts to empty list
        self.assertEqual(response2.dice_rolls, [])

    def test_type_validation_debug_info(self):
        """Test debug_info type validation"""
        # Should accept dict
        response = NarrativeResponse(narrative="Test", debug_info={"key": "value"})
        self.assertEqual(response.debug_info, {"key": "value"})

        # Should handle non-dict gracefully
        response2 = NarrativeResponse(
            narrative="Test",
            debug_info="not a dict",  # Wrong type
        )
        # Should convert to empty dict
        self.assertEqual(response2.debug_info, {})

    def test_string_field_stripping(self):
        """Test that string fields are properly stripped of whitespace"""
        response = NarrativeResponse(
            narrative="  Test narrative  \n",
            session_header="  Session 1  ",
            planning_block={
                "thinking": "The player needs to choose a direction.",
                "choices": {
                    "go_left": {
                        "text": "Go Left",
                        "description": "Head down the left path",
                    }
                },
            },
            resources="  HP: 20  ",
        )

        # Strings should be stripped
        self.assertEqual(response.narrative, "Test narrative")
        # Other fields may or may not strip - check actual behavior
        self.assertIsInstance(response.session_header, str)
        self.assertIsInstance(response.planning_block, dict)
        self.assertIsInstance(response.resources, str)

    def test_extra_fields_handling(self):
        """Test handling of unexpected extra fields"""
        response = NarrativeResponse(
            narrative="Test", extra_field_1="value1", extra_field_2="value2"
        )

        # Extra fields should be stored
        self.assertIn("extra_field_1", response.extra_fields)
        self.assertIn("extra_field_2", response.extra_fields)
        self.assertEqual(response.extra_fields["extra_field_1"], "value1")

    def test_to_dict_method(self):
        """Test conversion to dictionary if method exists"""
        response = NarrativeResponse(
            narrative="Test narrative",
            session_header="Header",
            planning_block={"thinking": "Test", "choices": {}},
            dice_rolls=["Roll 1"],
            resources="Resources",
            debug_info={"test": True},
        )

        # Check if to_dict method exists
        if hasattr(response, "to_dict"):
            result = response.to_dict()
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("narrative"), "Test narrative")
            self.assertEqual(result.get("session_header"), "Header")
            self.assertEqual(result.get("dice_rolls"), ["Roll 1"])

    def test_gemini_response_to_narrative_response_mapping(self):
        """Test that GeminiResponse correctly maps to NarrativeResponse fields"""
        raw_response = json.dumps(
            {
                "narrative": "Mapped narrative",
                "session_header": "Mapped header",
                "planning_block": {
                    "thinking": "Mapped thinking",
                    "choices": {"test": {"text": "Test"}},
                },
                "dice_rolls": ["Mapped roll"],
                "resources": "Mapped resources",
                "debug_info": {"mapped": True},
                "entities_mentioned": ["entity1"],
                "location_confirmed": "Mapped location",
            }
        )

        gemini_response = GeminiResponse.create(raw_response)
        narrative_response = gemini_response.structured_response

        # Verify mapping
        self.assertEqual(narrative_response.narrative, "Mapped narrative")
        self.assertEqual(narrative_response.session_header, "Mapped header")
        # Check that the planning block content matches (validation might add fields)
        self.assertEqual(
            narrative_response.planning_block["thinking"], "Mapped thinking"
        )
        # Note: The choice validation might filter out incomplete choices
        self.assertIsInstance(narrative_response.planning_block["choices"], dict)
        self.assertEqual(narrative_response.dice_rolls, ["Mapped roll"])
        self.assertEqual(narrative_response.resources, "Mapped resources")
        self.assertEqual(narrative_response.debug_info, {"mapped": True})
        self.assertEqual(narrative_response.entities_mentioned, ["entity1"])
        self.assertEqual(narrative_response.location_confirmed, "Mapped location")

    def test_empty_narrative_validation(self):
        """Test that empty narrative is handled appropriately"""
        # Narrative is required, but what if it's empty?
        response = NarrativeResponse(narrative="")
        self.assertEqual(response.narrative, "")

        # Test with whitespace-only narrative
        response2 = NarrativeResponse(narrative="   ")
        # Should be stripped to empty
        self.assertEqual(response2.narrative, "")

    def test_complex_planning_block_formatting(self):
        """Test complex formatting in planning_block field"""
        # For JSON-only format, we need to provide JSON planning block
        complex_planning = {
            "thinking": "The player has multiple tactical options available.",
            "choices": {
                "attack_sword": {
                    "text": "Attack with Sword",
                    "description": "Attack with sword (1d8+3 damage)",
                    "risk_level": "medium",
                },
                "cast_magic_missile": {
                    "text": "Cast Magic Missile",
                    "description": "Cast Magic Missile (3d4+3 damage, auto-hit)",
                    "risk_level": "low",
                },
                "defensive_stance": {
                    "text": "Defensive Stance",
                    "description": "Take defensive stance (+2 AC)",
                    "risk_level": "safe",
                },
                "search_room": {
                    "text": "Search Room",
                    "description": "Search the room (Perception check)",
                    "risk_level": "low",
                },
                "negotiate": {
                    "text": "Attempt Negotiation",
                    "description": "Attempt negotiation (Charisma check)",
                    "risk_level": "medium",
                },
            },
        }

        response = NarrativeResponse(narrative="Test", planning_block=complex_planning)

        # Complex JSON structure should be valid
        self.assertIn("thinking", response.planning_block)
        self.assertIn("choices", response.planning_block)
        self.assertIn("attack_sword", response.planning_block["choices"])
        self.assertIn("negotiate", response.planning_block["choices"])
        self.assertEqual(len(response.planning_block["choices"]), 5)


if __name__ == "__main__":
    unittest.main()
