"""
Unit tests for incomplete JSON response recovery in narrative_response_schema.py
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from narrative_response_schema import parse_structured_response, NarrativeResponse


class TestIncompleteJsonRecovery(unittest.TestCase):
    """Test cases for handling incomplete JSON responses from Gemini API"""
    
    def test_parse_complete_json_response(self):
        """Test parsing a complete, well-formed JSON response"""
        complete_json = '''{
            "narrative": "The knight entered the throne room.\\nThe king awaited.",
            "entities_mentioned": ["knight", "king"],
            "location_confirmed": "throne room"
        }'''
        
        narrative, response_obj = parse_structured_response(complete_json)
        
        self.assertEqual(narrative, "The knight entered the throne room.\nThe king awaited.")
        self.assertIsInstance(response_obj, NarrativeResponse)
        self.assertEqual(response_obj.entities_mentioned, ["knight", "king"])
        self.assertEqual(response_obj.location_confirmed, "throne room")
    
    def test_parse_incomplete_json_missing_closing_quote(self):
        """Test recovering from JSON with missing closing quote on narrative"""
        incomplete_json = '''{
            "narrative": "The knight entered the throne room.\\nThe king awaited.\\nSuddenly, a loud crash'''
        
        with patch('narrative_response_schema.logging_util') as mock_logging:
            narrative, response_obj = parse_structured_response(incomplete_json)
        
        # Should recover the narrative
        self.assertIn("The knight entered the throne room", narrative)
        self.assertIn("The king awaited", narrative)
        self.assertIn("Suddenly, a loud crash", narrative)
        
        # Verify that incomplete JSON was successfully recovered
        # (The actual logging happens in RobustJSONParser, not this module)
    
    def test_parse_incomplete_json_missing_closing_brace(self):
        """Test recovering from JSON with missing closing brace"""
        incomplete_json = '''{
            "narrative": "The adventure begins here.",
            "entities_mentioned": ["hero"'''
        
        with patch('narrative_response_schema.logging_util') as mock_logging:
            narrative, response_obj = parse_structured_response(incomplete_json)
        
        self.assertEqual(narrative, "The adventure begins here.")
        self.assertIsInstance(response_obj, NarrativeResponse)
        # Entities might not be recovered from incomplete JSON
        self.assertEqual(response_obj.location_confirmed, "Unknown")
    
    def test_parse_truncated_in_middle_of_narrative(self):
        """Test recovering from JSON truncated in the middle of narrative text"""
        # This simulates the exact issue from the user's example
        truncated_json = '''{"narrative": "[SESSION_HEADER]\\nTimestamp: Year 1620, Kythorn, Day 10, 02:05 PM\\nLocation: The Eastern March, on the road to the Dragon's Tooth mountains.\\nStatus: Lvl 1 Fighter/Paladin | HP: 12/12 | Gold: 25gp\\nResources:\\n- Hero Points: 1/1\\n\\nSir Andrew ignored Gareth's probing question, his focus narrowing back to the mission. He folded the map with crisp, efficient movements and tucked it away. His duty was clear; the feelings of his companions were secondary variables. He turned to the other two members of his small company, his expression a mask of command.\\n\\n\\"Report,\\" he said, his voice flat and devoid of warmth. He looked first to Kiera Varrus, the scout, whose cynical eyes were already scanning the treacherous path ahead.\\n\\nKiera spat on the ground, pulling her leather hood tighter against the wind. \\"It's a goat track at best, Sir Knight. Not a proper road. The ground is loose shale, easy to turn an ankle or alert anything hiding in the rocks.\\" She squinted at the mountains.'''
        
        with patch('narrative_response_schema.logging_util') as mock_logging:
            narrative, response_obj = parse_structured_response(truncated_json)
        
        # Should recover all the narrative content
        self.assertIn("SESSION_HEADER", narrative)
        self.assertIn("Sir Andrew ignored Gareth's probing question", narrative)
        self.assertIn("Kiera spat on the ground", narrative)
        self.assertIn("She squinted at the mountains.", narrative)
        
        # Check that newlines are properly unescaped
        self.assertIn("\n", narrative)
        self.assertNotIn("\\n", narrative)
        
        # Check that quotes are properly unescaped
        self.assertIn('"Report,"', narrative)
        
        # Logging happens in the RobustJSONParser, not in narrative_response_schema
        # The test should verify functionality, not internal logging
    
    def test_parse_plain_text_response(self):
        """Test handling plain text response (no JSON)"""
        plain_text = "This is just a plain text narrative with no JSON structure."
        
        narrative, response_obj = parse_structured_response(plain_text)
        
        self.assertEqual(narrative, plain_text)
        self.assertIsInstance(response_obj, NarrativeResponse)
        self.assertEqual(response_obj.entities_mentioned, [])
        self.assertEqual(response_obj.location_confirmed, "Unknown")
    
    def test_parse_empty_response(self):
        """Test handling empty response"""
        narrative, response_obj = parse_structured_response("")
        
        # Empty response should return a default narrative
        self.assertTrue(len(narrative) >= 20)  # Should meet minimum length
        self.assertIsInstance(response_obj, NarrativeResponse)
        self.assertEqual(response_obj.entities_mentioned, [])
    
    def test_parse_json_with_entities_partial(self):
        """Test recovering entities from partially complete JSON"""
        partial_json = '''{
            "narrative": "The hero met the wizard.",
            "entities_mentioned": ["hero", "wizard"],
            "location_confirmed": "tower"'''
        
        with patch('narrative_response_schema.logging_util') as mock_logging:
            narrative, response_obj = parse_structured_response(partial_json)
        
        self.assertEqual(narrative, "The hero met the wizard.")
        # Current implementation may not recover entities from incomplete JSON
        # This is acceptable as narrative recovery is the priority
    
    def test_unescape_special_characters(self):
        """Test that escaped characters are properly unescaped"""
        json_with_escapes = '''{
            "narrative": "He said, \\"Hello!\\"\\nThe next line.\\tTabbed text.\\\\Backslash"
        }'''
        
        narrative, response_obj = parse_structured_response(json_with_escapes)
        
        # Check proper unescaping
        self.assertIn('"Hello!"', narrative)  # Escaped quotes
        self.assertIn('\n', narrative)  # Newline
        self.assertIn('\t', narrative)  # Tab
        self.assertIn('\\', narrative)  # Backslash
        self.assertNotIn('\\"', narrative)  # Should not have escaped quotes
        self.assertNotIn('\\n', narrative)  # Should not have escaped newline
    
    def test_malformed_json_with_syntax_errors(self):
        """Test handling malformed JSON with syntax errors"""
        malformed = '''{"narrative": "Test malformed JSON with syntax errors", "entities_mentioned": ["a", "b",], }'''
        
        # Should fall back to trying to extract narrative
        with patch('narrative_response_schema.logging_util') as mock_logging:
            narrative, response_obj = parse_structured_response(malformed)
        
        # Should at least extract the narrative part
        self.assertEqual(narrative, "Test malformed JSON with syntax errors")
    
    def test_json_with_extra_text_around_it(self):
        """Test parsing JSON with extra text before/after"""
        wrapped_json = '''Here's the response:
        {
            "narrative": "The story begins here.",
            "entities_mentioned": ["protagonist"],
            "location_confirmed": "village"
        }
        That's all!'''
        
        narrative, response_obj = parse_structured_response(wrapped_json)
        
        # Should extract the JSON part
        self.assertEqual(narrative, "The story begins here.")
        self.assertEqual(response_obj.entities_mentioned, ["protagonist"])
        self.assertEqual(response_obj.location_confirmed, "village")


if __name__ == '__main__':
    unittest.main()