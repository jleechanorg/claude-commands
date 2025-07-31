#!/usr/bin/env python3
"""
Unit tests for GeminiResponse handling of structured fields.
Tests parsing of raw JSON responses containing structured fields.
"""

import json
import os
import sys
import unittest

# Add the parent directory to the Python path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse


class TestGeminiResponseStructuredFields(unittest.TestCase):
    """Test GeminiResponse parsing of structured fields from raw JSON"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_narrative = "You enter the dark dungeon..."

    def test_parse_all_structured_fields_present(self):
        """Test parsing when all structured fields are present"""
        raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "session_header": "Session 5: Into the Depths\nLevel 3 Rogue | HP: 25/30",
                "planning_block": {
                    "thinking": "The player is in a dark dungeon and needs to decide their approach.",
                    "choices": {
                        "search_traps": {
                            "text": "Search for Traps",
                            "description": "Carefully examine the area for hidden dangers",
                            "risk_level": "low",
                        },
                        "move_stealthily": {
                            "text": "Move Stealthily",
                            "description": "Sneak through the darkness quietly",
                            "risk_level": "medium",
                        },
                        "light_torch": {
                            "text": "Light a Torch",
                            "description": "Illuminate the area but reveal your position",
                            "risk_level": "medium",
                        },
                    },
                },
                "dice_rolls": ["Perception: 1d20+5 = 18", "Stealth: 1d20+8 = 22"],
                "resources": "HP: 25/30 | Spell Slots: 2/3 | Gold: 145",
                "debug_info": {
                    "dm_notes": ["Player is being cautious"],
                    "turn_number": 15,
                },
            }
        )

        response = GeminiResponse.create(raw_response)

        # Verify GeminiResponse has the structured_response
        assert response.structured_response is not None
        assert isinstance(response.structured_response, NarrativeResponse)

        # Verify all structured fields are parsed correctly
        structured = response.structured_response
        assert structured.session_header == "Session 5: Into the Depths\nLevel 3 Rogue | HP: 25/30"
        # Check planning block is JSON with expected structure
        assert isinstance(structured.planning_block, dict)
        assert "thinking" in structured.planning_block
        assert "choices" in structured.planning_block
        assert "search_traps" in structured.planning_block["choices"]
        assert len(structured.planning_block["choices"]) == 3
        assert structured.dice_rolls == ["Perception: 1d20+5 = 18", "Stealth: 1d20+8 = 22"]
        assert structured.resources == "HP: 25/30 | Spell Slots: 2/3 | Gold: 145"
        assert isinstance(structured.debug_info, dict)
        assert structured.debug_info["turn_number"] == 15

    def test_parse_missing_structured_fields(self):
        """Test parsing when some structured fields are missing"""
        raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "session_header": "Session 3: The Quest Begins",
                # planning_block missing
                "dice_rolls": ["Initiative: 1d20+2 = 14"],
                # resources missing
                "debug_info": {},
            }
        )

        response = GeminiResponse.create(raw_response)
        structured = response.structured_response

        # Present fields should have values
        assert structured.session_header == "Session 3: The Quest Begins"
        assert structured.dice_rolls == ["Initiative: 1d20+2 = 14"]

        # Missing fields should have defaults
        assert structured.planning_block == {}
        assert structured.resources == ""
        assert structured.debug_info == {}

    def test_parse_empty_structured_fields(self):
        """Test parsing when structured fields are present but empty"""
        raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "session_header": "",
                "planning_block": {},
                "dice_rolls": [],
                "resources": "",
                "debug_info": {},
            }
        )

        response = GeminiResponse.create(raw_response)
        structured = response.structured_response

        # All fields should exist with empty values
        assert structured.session_header == ""
        # Empty planning block gets default structure
        assert structured.planning_block == {"thinking": "", "context": "", "choices": {}}
        assert structured.dice_rolls == []
        assert structured.resources == ""
        assert structured.debug_info == {}

    def test_parse_null_structured_fields(self):
        """Test parsing when structured fields are null"""
        raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "session_header": None,
                "planning_block": None,
                "dice_rolls": None,
                "resources": None,
                "debug_info": None,
            }
        )

        response = GeminiResponse.create(raw_response)
        structured = response.structured_response

        # Null fields should be converted to appropriate defaults
        assert structured.session_header == ""
        assert structured.planning_block == {}
        assert structured.dice_rolls == []
        assert structured.resources == ""
        assert structured.debug_info == {}

    def test_parse_malformed_dice_rolls(self):
        """Test parsing when dice_rolls is not a list"""
        raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "dice_rolls": "Attack: 1d20+5 = 18",  # String instead of list
            }
        )

        response = GeminiResponse.create(raw_response)
        structured = response.structured_response

        # The implementation now converts invalid types to empty list
        assert structured.dice_rolls == []

    def test_parse_complex_debug_info(self):
        """Test parsing complex nested debug_info"""
        raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "debug_info": {
                    "dm_notes": ["Player found secret door", "Awarded inspiration"],
                    "combat_state": {
                        "round": 3,
                        "initiative_order": ["Player", "Goblin1", "Goblin2"],
                        "conditions": {
                            "Player": ["blessed"],
                            "Goblin1": ["frightened"],
                        },
                    },
                    "internal_state": {
                        "tension_level": 7,
                        "plot_threads": ["main_quest", "side_quest_tavern"],
                    },
                },
            }
        )

        response = GeminiResponse.create(raw_response)
        structured = response.structured_response

        # Complex debug info should be preserved
        assert isinstance(structured.debug_info, dict)
        assert "dm_notes" in structured.debug_info
        assert "combat_state" in structured.debug_info
        assert structured.debug_info["combat_state"]["round"] == 3
        assert isinstance(structured.debug_info["combat_state"]["conditions"], dict)

    def test_parse_special_characters_in_fields(self):
        """Test parsing fields with special characters"""
        raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "session_header": 'Session 10: "The Dragon\'s Lair"\n🐉 Boss Fight!',
                "planning_block": {
                    "thinking": "The player faces a critical decision in combat.",
                    "choices": {
                        "attack_sword": {
                            "text": "Attack with Sword ⚔️",
                            "description": "Strike with your enchanted blade",
                            "risk_level": "medium",
                        },
                        "cast_fireball": {
                            "text": "Cast Fireball 🔥",
                            "description": "Unleash magical fire damage",
                            "risk_level": "high",
                        },
                        "negotiate": {
                            "text": "Negotiate 💬",
                            "description": "Attempt diplomatic resolution",
                            "risk_level": "low",
                        },
                    },
                },
                "dice_rolls": ["Attack → 1d20+7 = 19", "Damage ➤ 2d8+4 = 12"],
                "resources": "HP: ♥️ 45/60 | MP: ✨ 12/20",
            }
        )

        response = GeminiResponse.create(raw_response)
        structured = response.structured_response

        # Special characters should be preserved
        assert "🐉" in structured.session_header
        # Check that special characters are preserved in JSON
        assert isinstance(structured.planning_block, dict)
        assert "choices" in structured.planning_block
        # Check that emoji is preserved in choice text
        attack_choice = structured.planning_block["choices"]["attack_sword"]
        assert "⚔️" in attack_choice["text"]
        assert "→" in structured.dice_rolls[0]
        assert "♥️" in structured.resources

    def test_parse_very_long_fields(self):
        """Test parsing fields with very long content"""
        # Create a JSON planning block with many choices
        long_planning = {
            "thinking": "The player has many tactical options available.",
            "choices": {},
        }
        for i in range(1, 51):
            long_planning["choices"][f"option_{i}"] = {
                "text": f"Option {i}",
                "description": f"Description for option {i}",
                "risk_level": "medium",
            }
        long_resources = " | ".join([f"Resource{i}: {i * 10}" for i in range(1, 21)])

        raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "planning_block": long_planning,
                "resources": long_resources,
                "dice_rolls": [f"Roll {i}: 1d20+{i} = {15 + i}" for i in range(1, 11)],
            }
        )

        response = GeminiResponse.create(raw_response)
        structured = response.structured_response

        # Long content should be preserved
        # Check that long content is preserved in JSON
        assert isinstance(structured.planning_block, dict)
        assert "choices" in structured.planning_block
        assert "option_50" in structured.planning_block["choices"]
        assert structured.planning_block["choices"]["option_50"]["text"] == "Option 50"
        assert "Resource20: 200" in structured.resources
        assert len(structured.dice_rolls) == 10


if __name__ == "__main__":
    unittest.main()
