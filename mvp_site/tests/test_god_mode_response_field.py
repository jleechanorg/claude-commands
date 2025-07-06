"""Test that god mode responses use the god_mode_response field correctly."""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from narrative_response_schema import parse_structured_response


class TestGodModeResponseField(unittest.TestCase):
    """Test god_mode_response field handling."""
    
    def test_god_mode_response_field_used(self):
        """Test that god_mode_response field is used when present."""
        god_response = '''{
            "narrative": "",
            "god_mode_response": "A mystical fog rolls in from the mountains. The temperature drops suddenly.",
            "entities_mentioned": [],
            "location_confirmed": "Unknown Forest",
            "state_updates": {
                "environment": {
                    "weather": "foggy",
                    "temperature": "cold"
                }
            },
            "debug_info": {}
        }'''
        
        narrative, response_obj = parse_structured_response(god_response)
        
        # Should return the god_mode_response content
        self.assertEqual(narrative, "A mystical fog rolls in from the mountains. The temperature drops suddenly.")
        self.assertEqual(response_obj.god_mode_response, "A mystical fog rolls in from the mountains. The temperature drops suddenly.")
        self.assertEqual(response_obj.narrative, "")
        
    def test_normal_response_without_god_mode(self):
        """Test that normal responses work without god_mode_response field."""
        normal_response = '''{
            "narrative": "You enter the tavern and see a hooded figure in the corner.",
            "entities_mentioned": ["hooded figure"],
            "location_confirmed": "The Rusty Tankard Tavern",
            "state_updates": {},
            "debug_info": {}
        }'''
        
        narrative, response_obj = parse_structured_response(normal_response)
        
        # Should return the narrative content
        self.assertEqual(narrative, "You enter the tavern and see a hooded figure in the corner.")
        self.assertEqual(response_obj.narrative, "You enter the tavern and see a hooded figure in the corner.")
        self.assertIsNone(response_obj.god_mode_response)
        
    def test_god_mode_with_state_updates(self):
        """Test god mode response with complex state updates."""
        god_response = '''{
            "narrative": "",
            "god_mode_response": "The ancient dragon Vermithrax awakens from his slumber. His eyes glow with malevolent intelligence.",
            "entities_mentioned": ["Vermithrax"],
            "location_confirmed": "Dragon's Lair",
            "state_updates": {
                "npc_data": {
                    "vermithrax": {
                        "name": "Vermithrax",
                        "type": "ancient_red_dragon",
                        "hp": 546,
                        "max_hp": 546,
                        "status": "hostile"
                    }
                }
            },
            "debug_info": {
                "dm_notes": ["Adding major boss encounter"]
            }
        }'''
        
        narrative, response_obj = parse_structured_response(god_response)
        
        # Should use god_mode_response
        self.assertIn("ancient dragon Vermithrax", narrative)
        self.assertEqual(response_obj.entities_mentioned, ["Vermithrax"])
        self.assertIsNotNone(response_obj.state_updates)
        self.assertIn("npc_data", response_obj.state_updates)
        
    def test_god_mode_empty_response(self):
        """Test god mode with empty god_mode_response field."""
        empty_response = '''{
            "narrative": "",
            "god_mode_response": "",
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }'''
        
        narrative, response_obj = parse_structured_response(empty_response)
        
        # Should return empty string, not try to extract from elsewhere
        self.assertEqual(narrative, "")
        self.assertEqual(response_obj.god_mode_response, "")
        
    def test_malformed_god_mode_response(self):
        """Test handling of malformed JSON with god_mode_response."""
        malformed = '''{"god_mode_response": "The world shifts...", "state_updates": {'''
        
        narrative, response_obj = parse_structured_response(malformed)
        
        # Should extract the god_mode_response even from incomplete JSON
        self.assertIn("world shifts", narrative)


    def test_backward_compatibility(self):
        """Test that old god mode responses without god_mode_response field still work."""
        old_style_response = '''{
            "narrative": "The ancient tome glows with an eerie light as you speak the command.",
            "entities_mentioned": ["ancient tome"],
            "location_confirmed": "Library",
            "state_updates": {
                "inventory": {
                    "ancient_tome": {
                        "activated": true
                    }
                }
            },
            "debug_info": {}
        }'''
        
        narrative, response_obj = parse_structured_response(old_style_response)
        
        # Should use narrative field as before
        self.assertEqual(narrative, "The ancient tome glows with an eerie light as you speak the command.")
        self.assertIsNone(response_obj.god_mode_response)
        
    def test_god_mode_with_empty_narrative(self):
        """Test god mode response when narrative is empty string."""
        response = '''{
            "narrative": "",
            "god_mode_response": "The world trembles at your command.",
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }'''
        
        narrative, response_obj = parse_structured_response(response)
        
        # Should only return god_mode_response, no extra newlines
        self.assertEqual(narrative, "The world trembles at your command.")
        self.assertNotIn("\n\n", narrative)
        
    def test_combined_god_mode_and_narrative(self):
        """Test that both god_mode_response and narrative are returned when both present."""
        both_fields_response = '''{
            "narrative": "Meanwhile, in the mortal realm, the players sense a change...",
            "god_mode_response": "The deity grants your wish. A shimmering portal opens.",
            "entities_mentioned": ["shimmering portal"],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }'''
        
        narrative, response_obj = parse_structured_response(both_fields_response)
        
        # Should include both god_mode_response first, then narrative
        self.assertIn("The deity grants your wish", narrative)
        self.assertIn("Meanwhile, in the mortal realm", narrative)
        # God mode response should come first
        self.assertTrue(narrative.startswith("The deity grants your wish"))
        self.assertEqual(response_obj.god_mode_response, "The deity grants your wish. A shimmering portal opens.")
        self.assertEqual(response_obj.narrative, "Meanwhile, in the mortal realm, the players sense a change...")


if __name__ == '__main__':
    unittest.main()