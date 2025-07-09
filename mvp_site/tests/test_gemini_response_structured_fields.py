#!/usr/bin/env python3
"""
Unit tests for GeminiResponse handling of structured fields.
Tests parsing of raw JSON responses containing structured fields.
"""
import unittest
import sys
import os
import json
from unittest.mock import Mock, patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse
import constants


class TestGeminiResponseStructuredFields(unittest.TestCase):
    """Test GeminiResponse parsing of structured fields from raw JSON"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_narrative = "You enter the dark dungeon..."
        
    def test_parse_all_structured_fields_present(self):
        """Test parsing when all structured fields are present"""
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "session_header": "Session 5: Into the Depths\nLevel 3 Rogue | HP: 25/30",
            "planning_block": "**Available Actions:**\n1. Search for traps\n2. Move stealthily\n3. Light a torch",
            "dice_rolls": ["Perception: 1d20+5 = 18", "Stealth: 1d20+8 = 22"],
            "resources": "HP: 25/30 | Spell Slots: 2/3 | Gold: 145",
            "debug_info": {
                "dm_notes": ["Player is being cautious"],
                "turn_number": 15
            }
        })
        
        response = GeminiResponse.create(raw_response)
        
        # Verify GeminiResponse has the structured_response
        self.assertIsNotNone(response.structured_response)
        self.assertIsInstance(response.structured_response, NarrativeResponse)
        
        # Verify all structured fields are parsed correctly
        structured = response.structured_response
        self.assertEqual(structured.session_header, "Session 5: Into the Depths\nLevel 3 Rogue | HP: 25/30")
        self.assertEqual(structured.planning_block, "**Available Actions:**\n1. Search for traps\n2. Move stealthily\n3. Light a torch")
        self.assertEqual(structured.dice_rolls, ["Perception: 1d20+5 = 18", "Stealth: 1d20+8 = 22"])
        self.assertEqual(structured.resources, "HP: 25/30 | Spell Slots: 2/3 | Gold: 145")
        self.assertIsInstance(structured.debug_info, dict)
        self.assertEqual(structured.debug_info["turn_number"], 15)
    
    def test_parse_missing_structured_fields(self):
        """Test parsing when some structured fields are missing"""
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "session_header": "Session 3: The Quest Begins",
            # planning_block missing
            "dice_rolls": ["Initiative: 1d20+2 = 14"],
            # resources missing
            "debug_info": {}
        })
        
        response = GeminiResponse.create(raw_response)
        structured = response.structured_response
        
        # Present fields should have values
        self.assertEqual(structured.session_header, "Session 3: The Quest Begins")
        self.assertEqual(structured.dice_rolls, ["Initiative: 1d20+2 = 14"])
        
        # Missing fields should have defaults
        self.assertEqual(structured.planning_block, "")
        self.assertEqual(structured.resources, "")
        self.assertEqual(structured.debug_info, {})
    
    def test_parse_empty_structured_fields(self):
        """Test parsing when structured fields are present but empty"""
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "session_header": "",
            "planning_block": "",
            "dice_rolls": [],
            "resources": "",
            "debug_info": {}
        })
        
        response = GeminiResponse.create(raw_response)
        structured = response.structured_response
        
        # All fields should exist with empty values
        self.assertEqual(structured.session_header, "")
        self.assertEqual(structured.planning_block, "")
        self.assertEqual(structured.dice_rolls, [])
        self.assertEqual(structured.resources, "")
        self.assertEqual(structured.debug_info, {})
    
    def test_parse_null_structured_fields(self):
        """Test parsing when structured fields are null"""
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "session_header": None,
            "planning_block": None,
            "dice_rolls": None,
            "resources": None,
            "debug_info": None
        })
        
        response = GeminiResponse.create(raw_response)
        structured = response.structured_response
        
        # Null fields should be converted to appropriate defaults
        self.assertEqual(structured.session_header, "")
        self.assertEqual(structured.planning_block, "")
        self.assertEqual(structured.dice_rolls, [])
        self.assertEqual(structured.resources, "")
        self.assertEqual(structured.debug_info, {})
    
    def test_parse_malformed_dice_rolls(self):
        """Test parsing when dice_rolls is not a list"""
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "dice_rolls": "Attack: 1d20+5 = 18"  # String instead of list
        })
        
        response = GeminiResponse.create(raw_response)
        structured = response.structured_response
        
        # The implementation stores the string as-is, not converting to list
        self.assertEqual(structured.dice_rolls, "Attack: 1d20+5 = 18")
    
    def test_parse_complex_debug_info(self):
        """Test parsing complex nested debug_info"""
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "debug_info": {
                "dm_notes": ["Player found secret door", "Awarded inspiration"],
                "combat_state": {
                    "round": 3,
                    "initiative_order": ["Player", "Goblin1", "Goblin2"],
                    "conditions": {
                        "Player": ["blessed"],
                        "Goblin1": ["frightened"]
                    }
                },
                "internal_state": {
                    "tension_level": 7,
                    "plot_threads": ["main_quest", "side_quest_tavern"]
                }
            }
        })
        
        response = GeminiResponse.create(raw_response)
        structured = response.structured_response
        
        # Complex debug info should be preserved
        self.assertIsInstance(structured.debug_info, dict)
        self.assertIn("dm_notes", structured.debug_info)
        self.assertIn("combat_state", structured.debug_info)
        self.assertEqual(structured.debug_info["combat_state"]["round"], 3)
        self.assertIsInstance(structured.debug_info["combat_state"]["conditions"], dict)
    
    def test_parse_special_characters_in_fields(self):
        """Test parsing fields with special characters"""
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "session_header": "Session 10: \"The Dragon's Lair\"\n🐉 Boss Fight!",
            "planning_block": "**Options:**\n• Attack with sword ⚔️\n• Cast fireball 🔥\n• Negotiate 💬",
            "dice_rolls": ["Attack → 1d20+7 = 19", "Damage ➤ 2d8+4 = 12"],
            "resources": "HP: ♥️ 45/60 | MP: ✨ 12/20"
        })
        
        response = GeminiResponse.create(raw_response)
        structured = response.structured_response
        
        # Special characters should be preserved
        self.assertIn("🐉", structured.session_header)
        self.assertIn("⚔️", structured.planning_block)
        self.assertIn("→", structured.dice_rolls[0])
        self.assertIn("♥️", structured.resources)
    
    def test_parse_very_long_fields(self):
        """Test parsing fields with very long content"""
        long_planning = "**Extensive Planning:**\n" + "\n".join([f"{i}. Option {i}" for i in range(1, 51)])
        long_resources = " | ".join([f"Resource{i}: {i*10}" for i in range(1, 21)])
        
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "planning_block": long_planning,
            "resources": long_resources,
            "dice_rolls": [f"Roll {i}: 1d20+{i} = {15+i}" for i in range(1, 11)]
        })
        
        response = GeminiResponse.create(raw_response)
        structured = response.structured_response
        
        # Long content should be preserved
        self.assertIn("50. Option 50", structured.planning_block)
        self.assertIn("Resource20: 200", structured.resources)
        self.assertEqual(len(structured.dice_rolls), 10)


if __name__ == '__main__':
    unittest.main()