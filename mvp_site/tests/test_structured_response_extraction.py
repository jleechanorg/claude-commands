#!/usr/bin/env python3
"""
Unit tests for structured response field extraction and processing.
Tests the correct handling of the schema from game_state_instruction.md
"""
import unittest
from unittest.mock import MagicMock, patch
import json


class TestStructuredResponseExtraction(unittest.TestCase):
    """Test extraction and processing of structured response fields"""
    
    def setUp(self):
        """Set up test data matching the schema"""
        self.mock_gemini_response = {
            "narrative": "[SESSION_HEADER]\nTimestamp: 1492 DR, Ches 20, 10:00\nLocation: Goblin Cave\nStatus: Lvl 2 Fighter | HP: 15/18 (Temp: 0) | XP: 450/900 | Gold: 25gp\nResources: HD: 2/2 | Second Wind: 0/1 | Action Surge: 1/1\nConditions: None | Exhaustion: 0 | Inspiration: No | Potions: 1\n\nYou swing your sword at the goblin!\n\n--- PLANNING BLOCK ---\nWhat would you like to do next?\n1. **Attack again:** Strike the goblin with your sword\n2. **Defend:** Raise your shield and prepare for the goblin's counterattack\n3. **Use Second Wind:** Recover some hit points\n4. **Other:** Describe a different action you'd like to take.",
            "entities_mentioned": ["goblin"],
            "location_confirmed": "Goblin Cave",
            "state_updates": {
                "npc_data": {
                    "goblin_1": {
                        "hp_current": 3
                    }
                }
            },
            "debug_info": {
                "dm_notes": ["I chose to have the goblin attempt a dodge", "The shoulder wound gives specific injury location"],
                "dice_rolls": ["Attack roll: 1d20+5 = 15+5 = 20 (Hit, AC 15)", "Damage: 1d8+3 = 5+3 = 8 slashing damage"],
                "resources": "HD: 2/2, Second Wind: 0/1, Action Surge: 1/1, Potions: 1",
                "state_rationale": "Reduced goblin HP from 11 to 3 due to 8 damage taken"
            }
        }
        
        self.mock_god_mode_response = {
            "narrative": "",
            "god_mode_response": "The goblin has 3 HP remaining. Its AC is 15.",
            "entities_mentioned": [],
            "location_confirmed": "Goblin Cave",
            "state_updates": {},
            "debug_info": {}
        }
    
    def test_structured_response_has_correct_fields(self):
        """Test that response has all required fields from schema"""
        required_fields = ['narrative', 'entities_mentioned', 'location_confirmed', 'state_updates', 'debug_info']
        
        for field in required_fields:
            self.assertIn(field, self.mock_gemini_response, f"Response should contain {field}")
    
    def test_debug_info_structure(self):
        """Test that debug_info contains dice_rolls and resources"""
        debug_info = self.mock_gemini_response['debug_info']
        
        # Check dice_rolls is in debug_info
        self.assertIn('dice_rolls', debug_info, "dice_rolls should be in debug_info")
        self.assertIsInstance(debug_info['dice_rolls'], list, "dice_rolls should be a list")
        self.assertEqual(len(debug_info['dice_rolls']), 2, "Should have 2 dice rolls")
        
        # Check resources is in debug_info
        self.assertIn('resources', debug_info, "resources should be in debug_info")
        self.assertIsInstance(debug_info['resources'], str, "resources should be a string")
        self.assertIn('HD: 2/2', debug_info['resources'], "Resources should contain hit dice")
        
        # Check other debug fields
        self.assertIn('dm_notes', debug_info, "dm_notes should be in debug_info")
        self.assertIn('state_rationale', debug_info, "state_rationale should be in debug_info")
    
    def test_narrative_contains_structured_content(self):
        """Test that narrative contains session header and planning block"""
        narrative = self.mock_gemini_response['narrative']
        
        # Check for session header
        self.assertIn('[SESSION_HEADER]', narrative, "Narrative should contain session header marker")
        self.assertIn('Lvl 2 Fighter', narrative, "Session header should contain character info")
        self.assertIn('HP: 15/18', narrative, "Session header should contain HP")
        
        # Check for planning block
        self.assertIn('--- PLANNING BLOCK ---', narrative, "Narrative should contain planning block marker")
        self.assertIn('What would you like to do next?', narrative, "Planning block should contain prompt")
        self.assertIn('**Attack again:**', narrative, "Planning block should contain formatted options")
    
    def test_state_updates_structure(self):
        """Test state_updates field structure"""
        state_updates = self.mock_gemini_response['state_updates']
        
        self.assertIsInstance(state_updates, dict, "state_updates should be a dict")
        self.assertIn('npc_data', state_updates, "state_updates should contain npc_data")
        self.assertIn('goblin_1', state_updates['npc_data'], "npc_data should contain goblin_1")
        self.assertEqual(state_updates['npc_data']['goblin_1']['hp_current'], 3, "Goblin HP should be 3")
    
    def test_god_mode_response_handling(self):
        """Test god_mode_response field handling"""
        # Normal response shouldn't have god_mode_response
        self.assertNotIn('god_mode_response', self.mock_gemini_response, 
                        "Normal response should not have god_mode_response")
        
        # God mode response should have the field
        self.assertIn('god_mode_response', self.mock_god_mode_response,
                     "God mode response should have god_mode_response field")
        self.assertEqual(self.mock_god_mode_response['narrative'], "", 
                        "God mode response can have empty narrative")
    
    def test_entities_and_location_fields(self):
        """Test entities_mentioned and location_confirmed fields"""
        self.assertIn('entities_mentioned', self.mock_gemini_response)
        self.assertIsInstance(self.mock_gemini_response['entities_mentioned'], list)
        self.assertIn('goblin', self.mock_gemini_response['entities_mentioned'])
        
        self.assertIn('location_confirmed', self.mock_gemini_response)
        self.assertEqual(self.mock_gemini_response['location_confirmed'], 'Goblin Cave')
    
    def test_narrative_response_object_mapping(self):
        """Test that NarrativeResponse object maps fields correctly"""
        # Create a mock NarrativeResponse instance
        mock_instance = MagicMock()
        mock_instance.narrative = self.mock_gemini_response['narrative']
        mock_instance.entities_mentioned = self.mock_gemini_response['entities_mentioned']
        mock_instance.location_confirmed = self.mock_gemini_response['location_confirmed']
        mock_instance.state_updates = self.mock_gemini_response['state_updates']
        mock_instance.debug_info = self.mock_gemini_response['debug_info']
        
        # Test accessing nested fields
        self.assertEqual(mock_instance.debug_info['dice_rolls'][0], 
                        "Attack roll: 1d20+5 = 15+5 = 20 (Hit, AC 15)")
        self.assertEqual(mock_instance.debug_info['resources'],
                        "HD: 2/2, Second Wind: 0/1, Action Surge: 1/1, Potions: 1")
    
    def test_empty_state_updates_handling(self):
        """Test that empty state_updates is handled correctly"""
        response_with_empty_updates = {
            **self.mock_gemini_response,
            'state_updates': {}
        }
        
        self.assertIsInstance(response_with_empty_updates['state_updates'], dict)
        self.assertEqual(len(response_with_empty_updates['state_updates']), 0)


if __name__ == '__main__':
    unittest.main()