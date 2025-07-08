"""
Comprehensive test suite for robust_json_parser.py
Tests the RobustJSONParser class and parse_llm_json_response function
"""
import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from robust_json_parser import RobustJSONParser, parse_llm_json_response


class TestRobustJSONParser(unittest.TestCase):
    """Test the RobustJSONParser class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = RobustJSONParser()
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON returns correct result"""
        valid_json = '{"narrative": "Test story", "entities_mentioned": ["hero"], "location_confirmed": "castle"}'
        result, was_incomplete = self.parser.parse(valid_json)
        
        self.assertIsNotNone(result)
        self.assertFalse(was_incomplete)
        self.assertEqual(result["narrative"], "Test story")
        self.assertEqual(result["entities_mentioned"], ["hero"])
        self.assertEqual(result["location_confirmed"], "castle")
    
    def test_parse_empty_string(self):
        """Test parsing empty string returns None"""
        result, was_incomplete = self.parser.parse("")
        self.assertIsNone(result)
        self.assertFalse(was_incomplete)
        
        result, was_incomplete = self.parser.parse("   ")
        self.assertIsNone(result)
        self.assertFalse(was_incomplete)
    
    def test_parse_incomplete_json_missing_brace(self):
        """Test parsing JSON missing closing brace"""
        incomplete = '{"narrative": "Test story", "entities_mentioned": ["hero"]'
        result, was_incomplete = self.parser.parse(incomplete)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertEqual(result["narrative"], "Test story")
        self.assertEqual(result["entities_mentioned"], ["hero"])
    
    def test_parse_incomplete_json_unclosed_string(self):
        """Test parsing JSON with unclosed string"""
        incomplete = '{"narrative": "This is a long story that gets cut off...'
        result, was_incomplete = self.parser.parse(incomplete)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertEqual(result["narrative"], "This is a long story that gets cut off...")
    
    def test_parse_json_with_extra_text(self):
        """Test parsing JSON with surrounding text"""
        text_with_json = 'Here is the response: {"narrative": "Story", "entities_mentioned": []} and some extra text'
        result, was_incomplete = self.parser.parse(text_with_json)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertEqual(result["narrative"], "Story")
        self.assertEqual(result["entities_mentioned"], [])
    
    def test_parse_malformed_json_unquoted_keys(self):
        """Test parsing JSON with unquoted keys"""
        malformed = '{narrative: "Story", entities_mentioned: []}'
        result, was_incomplete = self.parser.parse(malformed)
        
        # Should extract fields even from malformed JSON
        self.assertTrue(was_incomplete)
        # The parser will try various strategies, may or may not succeed
    
    def test_parse_deeply_nested_incomplete(self):
        """Test parsing deeply nested incomplete JSON"""
        nested = '{"narrative": "Story", "data": {"player": {"stats": {"hp": 10'
        result, was_incomplete = self.parser.parse(nested)
        
        self.assertTrue(was_incomplete)
        # Should at least extract the narrative
        if result:
            self.assertIn("narrative", result)
    
    @patch('robust_json_parser.logging_util')
    def test_logging_on_successful_fix(self, mock_logging):
        """Test that successful fixes are logged"""
        incomplete = '{"narrative": "Test"'
        result, was_incomplete = self.parser.parse(incomplete)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        # Check that info logging was called
        self.assertTrue(mock_logging.info.called or mock_logging.debug.called)
    
    def test_extract_fields_from_severely_malformed(self):
        """Test field extraction from severely malformed JSON"""
        malformed = '''
        This isn't even JSON but contains
        "narrative": "A story about heroes",
        "entities_mentioned": ["hero1", "hero2"],
        "location_confirmed": "dungeon"
        '''
        result, was_incomplete = self.parser.parse(malformed)
        
        self.assertTrue(was_incomplete)
        if result:
            # Should extract at least some fields
            self.assertTrue(any(field in result for field in ["narrative", "entities_mentioned", "location_confirmed"]))


class TestParseSpecificFields(unittest.TestCase):
    """Test parsing of specific fields"""
    
    def test_extract_narrative_field(self):
        """Test extraction of narrative field specifically"""
        parser = RobustJSONParser()
        
        # Test with complete narrative
        text = '{"narrative": "Once upon a time in a kingdom far away..."}'
        result, _ = parser.parse(text)
        self.assertEqual(result["narrative"], "Once upon a time in a kingdom far away...")
        
        # Test with incomplete narrative
        text = '{"narrative": "This story is incomplete and'
        result, _ = parser.parse(text)
        self.assertEqual(result["narrative"], "This story is incomplete and")
    
    def test_extract_entities_mentioned(self):
        """Test extraction of entities_mentioned array"""
        parser = RobustJSONParser()
        
        # Test with complete array
        text = '{"entities_mentioned": ["hero", "villain", "dragon"]}'
        result, _ = parser.parse(text)
        self.assertEqual(result["entities_mentioned"], ["hero", "villain", "dragon"])
        
        # Test with incomplete array
        text = '{"entities_mentioned": ["hero", "villain"'
        result, _ = parser.parse(text)
        if result and "entities_mentioned" in result:
            self.assertIsInstance(result["entities_mentioned"], list)
    
    def test_extract_location_confirmed(self):
        """Test extraction of location_confirmed field"""
        parser = RobustJSONParser()
        
        text = '{"location_confirmed": "The Dark Forest"}'
        result, _ = parser.parse(text)
        self.assertEqual(result["location_confirmed"], "The Dark Forest")
        
        # Test with special characters
        text = '{"location_confirmed": "King\'s Landing"}'
        result, _ = parser.parse(text)
        if result and "location_confirmed" in result:
            self.assertIn("Landing", result["location_confirmed"])


class TestParseLLMJsonResponse(unittest.TestCase):
    """Test the parse_llm_json_response function"""
    
    def test_parse_complete_response(self):
        """Test parsing complete LLM response"""
        response = '{"narrative": "Story", "entities_mentioned": ["hero"], "location_confirmed": "castle"}'
        result, was_incomplete = parse_llm_json_response(response)
        
        self.assertFalse(was_incomplete)
        self.assertEqual(result["narrative"], "Story")
        self.assertEqual(result["entities_mentioned"], ["hero"])
        self.assertEqual(result["location_confirmed"], "castle")
    
    def test_parse_incomplete_response(self):
        """Test parsing incomplete LLM response"""
        response = '{"narrative": "Incomplete story that'
        result, was_incomplete = parse_llm_json_response(response)
        
        self.assertTrue(was_incomplete)
        self.assertIn("narrative", result)
        self.assertIn("entities_mentioned", result)  # Should add default
        self.assertIn("location_confirmed", result)  # Should add default
    
    def test_parse_non_json_response(self):
        """Test parsing non-JSON response falls back to treating as narrative"""
        response = "This is just plain text, not JSON at all."
        result, was_incomplete = parse_llm_json_response(response)
        
        self.assertTrue(was_incomplete)
        self.assertEqual(result["narrative"], response)
        self.assertEqual(result["entities_mentioned"], [])
        self.assertEqual(result["location_confirmed"], "Unknown")
    
    def test_parse_missing_required_fields(self):
        """Test that missing required fields are added with defaults"""
        response = '{"other_field": "value"}'
        result, was_incomplete = parse_llm_json_response(response)
        
        self.assertIn("narrative", result)
        self.assertEqual(result["narrative"], "")
        self.assertIn("entities_mentioned", result)
        self.assertEqual(result["entities_mentioned"], [])
        self.assertIn("location_confirmed", result)
        self.assertEqual(result["location_confirmed"], "Unknown")
    
    def test_parse_partial_fields(self):
        """Test parsing response with only some fields"""
        response = '{"narrative": "Story text", "other": "data"}'
        result, was_incomplete = parse_llm_json_response(response)
        
        self.assertEqual(result["narrative"], "Story text")
        self.assertEqual(result["entities_mentioned"], [])  # Default added
        self.assertEqual(result["location_confirmed"], "Unknown")  # Default added
    
    @patch('robust_json_parser.logging_util')
    def test_logging_when_no_json_found(self, mock_logging):
        """Test that appropriate logging occurs when no JSON is found"""
        response = "Just plain text"
        result, was_incomplete = parse_llm_json_response(response)
        
        # Should log that no JSON was found
        mock_logging.info.assert_called()
        self.assertTrue(was_incomplete)


class TestRealWorldScenarios(unittest.TestCase):
    """Test with real-world LLM response scenarios"""
    
    def test_parse_truncated_narrative(self):
        """Test the example from the module"""
        incomplete_json = '''{"narrative": "[SESSION_HEADER]\\nTimestamp: Year 1620, Kythorn, Day 10, 02:05 PM\\nLocation: The Eastern March, on the road to the Dragon's Tooth mountains.\\nStatus: Lvl 1 Fighter/Paladin | HP: 12/12 | Gold: 25gp\\nResources:\\n- Hero Points: 1/1\\n\\nSir Andrew ignored Gareth's probing question, his focus narrowing back to the mission. He folded the map with crisp, efficient movements and tucked it away. His duty was clear; the feelings of his companions were secondary variables. He turned to the other two members of his small company, his expression a mask of command.\\n\\n\\"Report,\\" he said, his voice flat and devoid of warmth. He looked first to Kiera Varrus, the scout, whose cynical eyes were already scanning the treacherous path ahead.\\n\\nKiera spat on the ground, pulling her leather hood tighter against the wind. \\"It's a goat track at best, Sir Knight. Not a proper road. The ground is loose shale, easy to turn an ankle or alert anything hiding in the rocks.\\" She squinted at the mountains.'''
        
        result, was_incomplete = parse_llm_json_response(incomplete_json)
        
        self.assertTrue(was_incomplete)
        self.assertIn("narrative", result)
        self.assertIn("SESSION_HEADER", result["narrative"])
        self.assertIn("Sir Andrew", result["narrative"])
    
    def test_parse_json_with_unicode(self):
        """Test parsing JSON containing unicode characters"""
        unicode_json = '{"narrative": "The hero found a 🗡️ sword", "entities_mentioned": ["hero", "sword"]}'
        result, was_incomplete = parse_llm_json_response(unicode_json)
        
        self.assertFalse(was_incomplete)
        self.assertIn("🗡️", result["narrative"])
    
    def test_parse_json_with_newlines(self):
        """Test parsing JSON with embedded newlines"""
        multiline = '{"narrative": "Line 1\\nLine 2\\nLine 3", "location_confirmed": "Multi\\nLine\\nPlace"}'
        result, was_incomplete = parse_llm_json_response(multiline)
        
        self.assertFalse(was_incomplete)
        self.assertIn("Line 1\nLine 2\nLine 3", result["narrative"])


if __name__ == '__main__':
    unittest.main()