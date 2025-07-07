#!/usr/bin/env python3
"""
Test for the "Scene #X:" prefix JSON bug fix.
Verifies that JSON responses with Scene prefixes are properly parsed.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from narrative_response_schema import parse_structured_response


class TestScenePrefixJSONBug(unittest.TestCase):
    """Test handling of Scene #X: prefix in JSON responses"""
    
    def test_scene_prefix_with_valid_json(self):
        """Test that Scene #X: prefix is stripped and JSON is parsed correctly"""
        # Exact format reported by user
        raw_response = '''Scene #2: {
    "narrative": "[Mode: STORY MODE]\\n[CHARACTER CREATION - Step 2 of 7]\\n\\nYou are Mark Grayson, son of Omni-Man (Nolan Grayson), one of Earth's most powerful superheroes. You've recently discovered your own Viltrumite powers, but you're still learning to control them. Your father has just revealed something shocking to you - he wants you to join him in conquering Earth for the Viltrumite Empire.\\n\\nYou stand in your family's living room, still in your civilian clothes. Your mother Debbie is at work, unaware of this conversation. Nolan stands before you in his Omni-Man costume, his expression serious and expectant.\\n\\n'Mark,' he says, his deep voice carrying the weight of centuries, 'it's time you understood your true heritage. We are Viltrumites - a superior race meant to rule. Earth... Earth is just another planet to be added to our empire. Join me, son. Together, we can bring order to this chaotic world.'\\n\\nYour mind reels. This can't be real. Your father, the hero you've looked up to your entire life, is talking about conquering Earth?",
    "god_mode_response": "",
    "entities_mentioned": ["Mark Grayson", "Nolan Grayson", "Omni-Man", "Debbie", "Viltrumite Empire", "Earth"],
    "location_confirmed": "Grayson family living room",
    "state_updates": {
        "player_character_data": {
            "name": "Mark Grayson",
            "level": 1,
            "attributes": {
                "str": 18,
                "dex": 14,
                "con": 16,
                "int": 12,
                "wis": 10,
                "cha": 13
            }
        }
    }
}'''
        
        narrative_text, structured_response = parse_structured_response(raw_response)
        
        # Verify the narrative was extracted correctly
        self.assertIsNotNone(narrative_text)
        self.assertIn("[Mode: STORY MODE]", narrative_text)
        self.assertIn("Mark Grayson", narrative_text)
        self.assertNotIn('"narrative":', narrative_text)  # No JSON artifacts
        self.assertNotIn('Scene #2:', narrative_text)  # No Scene prefix
        
        # Verify structured response was created
        self.assertIsNotNone(structured_response)
        self.assertEqual(structured_response.location_confirmed, "Grayson family living room")
        self.assertIn("Mark Grayson", structured_response.entities_mentioned)
        
    def test_scene_prefix_variations(self):
        """Test different variations of Scene prefix"""
        test_cases = [
            'Scene #1: {"narrative": "Test story", "entities_mentioned": []}',
            'Scene #123: {"narrative": "Test story", "entities_mentioned": []}',
            'scene #5: {"narrative": "Test story", "entities_mentioned": []}',
            'Scene  #7: {"narrative": "Test story", "entities_mentioned": []}',  # Extra space
        ]
        
        for raw_response in test_cases:
            with self.subTest(raw_response=raw_response):
                narrative_text, structured_response = parse_structured_response(raw_response)
                self.assertEqual(narrative_text, "Test story")
                self.assertNotIn("Scene", narrative_text)
                self.assertNotIn("{", narrative_text)
    
    def test_no_scene_prefix(self):
        """Test that responses without Scene prefix still work"""
        raw_response = '{"narrative": "Direct JSON response", "entities_mentioned": ["Test"]}'
        
        narrative_text, structured_response = parse_structured_response(raw_response)
        self.assertEqual(narrative_text, "Direct JSON response")
        self.assertIsNotNone(structured_response)
        
    def test_scene_prefix_in_markdown(self):
        """Test Scene prefix inside markdown blocks"""
        raw_response = '''```json
Scene #3: {
    "narrative": "Markdown wrapped response",
    "entities_mentioned": ["Test"],
    "location_confirmed": "Test Location"
}
```'''
        
        narrative_text, structured_response = parse_structured_response(raw_response)
        self.assertEqual(narrative_text, "Markdown wrapped response")
        self.assertNotIn("Scene #3:", narrative_text)
        self.assertIsNotNone(structured_response)
        
    def test_malformed_json_with_scene_prefix(self):
        """Test that malformed JSON with Scene prefix still extracts narrative"""
        raw_response = '''Scene #4: {
    "narrative": "This is a long story that might get truncated...",
    "entities_mentioned": ["Hero", "Villain"],
    "location_confirmed": "Battle'''  # Truncated JSON
        
        narrative_text, structured_response = parse_structured_response(raw_response)
        self.assertIsNotNone(narrative_text)
        self.assertIn("This is a long story", narrative_text)
        self.assertNotIn("Scene #4:", narrative_text)


if __name__ == '__main__':
    unittest.main()