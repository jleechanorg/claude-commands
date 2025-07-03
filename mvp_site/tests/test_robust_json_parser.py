"""
Unit tests for the robust JSON parser
"""
import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from robust_json_parser import RobustJSONParser, parse_llm_json_response


class TestRobustJSONParser(unittest.TestCase):
    """Test cases for the robust JSON parser"""
    
    def test_parse_complete_json(self):
        """Test parsing complete, valid JSON"""
        valid_json = '{"narrative": "Test story", "entities_mentioned": ["a", "b"], "location_confirmed": "here"}'
        result, was_incomplete = RobustJSONParser.parse(valid_json)
        
        self.assertIsNotNone(result)
        self.assertFalse(was_incomplete)
        self.assertEqual(result["narrative"], "Test story")
        self.assertEqual(result["entities_mentioned"], ["a", "b"])
    
    def test_parse_truncated_string(self):
        """Test parsing JSON truncated in the middle of a string value"""
        truncated = '{"narrative": "This is a long story that got cut off in the middle'
        result, was_incomplete = RobustJSONParser.parse(truncated)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertEqual(result["narrative"], "This is a long story that got cut off in the middle")
    
    def test_parse_missing_closing_braces(self):
        """Test parsing JSON missing closing braces"""
        incomplete = '{"narrative": "Complete string", "entities_mentioned": ["hero", "villain"'
        result, was_incomplete = RobustJSONParser.parse(incomplete)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertEqual(result["narrative"], "Complete string")
        self.assertEqual(result["entities_mentioned"], ["hero", "villain"])
    
    def test_parse_nested_json(self):
        """Test parsing nested JSON structures"""
        nested = '{"narrative": "Story", "metadata": {"author": "AI", "version": 1'
        result, was_incomplete = RobustJSONParser.parse(nested)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertEqual(result["narrative"], "Story")
    
    def test_parse_with_escaped_characters(self):
        """Test parsing JSON with escaped characters"""
        escaped = r'{"narrative": "He said, \"Hello!\"\nNew line here"}'
        result, was_incomplete = RobustJSONParser.parse(escaped)
        
        self.assertIsNotNone(result)
        self.assertFalse(was_incomplete)
        self.assertEqual(result["narrative"], 'He said, "Hello!"\nNew line here')
    
    def test_parse_with_unicode(self):
        """Test parsing JSON with unicode characters"""
        unicode_json = '{"narrative": "The café was très bien! 🎉"}'
        result, was_incomplete = RobustJSONParser.parse(unicode_json)
        
        self.assertIsNotNone(result)
        self.assertFalse(was_incomplete)
        self.assertEqual(result["narrative"], "The café was très bien! 🎉")
    
    def test_parse_with_extra_text(self):
        """Test parsing JSON with extra text before/after"""
        wrapped = 'Here is the response: {"narrative": "Story"} end of response'
        result, was_incomplete = RobustJSONParser.parse(wrapped)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)  # Parser had to extract JSON from text
        self.assertEqual(result["narrative"], "Story")
    
    def test_parse_array_truncation(self):
        """Test parsing JSON with truncated array"""
        truncated_array = '{"narrative": "Story", "entities_mentioned": ["a", "b", "c'
        result, was_incomplete = RobustJSONParser.parse(truncated_array)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertEqual(result["entities_mentioned"], ["a", "b", "c"])
    
    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result, was_incomplete = RobustJSONParser.parse("")
        self.assertIsNone(result)
        self.assertFalse(was_incomplete)
    
    def test_parse_non_json_text(self):
        """Test parsing plain text (not JSON)"""
        plain_text = "This is just plain text, not JSON"
        result, was_incomplete = RobustJSONParser.parse(plain_text)
        
        # Should return None since it's not JSON
        self.assertIsNone(result)
        self.assertTrue(was_incomplete)
    
    def test_extract_fields_from_malformed(self):
        """Test field extraction from severely malformed JSON"""
        malformed = '''
        "narrative": "The story begins here",
        "entities_mentioned": ["hero", "dragon"],
        some garbage text
        "location_confirmed": "castle"
        '''
        result, was_incomplete = RobustJSONParser.parse(malformed)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertEqual(result["narrative"], "The story begins here")
        self.assertEqual(result["entities_mentioned"], ["hero", "dragon"])
        self.assertEqual(result["location_confirmed"], "castle")
    
    def test_parse_llm_json_response_wrapper(self):
        """Test the high-level wrapper function"""
        incomplete = '{"narrative": "Test"'
        result, was_incomplete = parse_llm_json_response(incomplete)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertEqual(result["narrative"], "Test")
        # Should have default values for missing fields
        self.assertEqual(result["entities_mentioned"], [])
        self.assertEqual(result["location_confirmed"], "Unknown")
    
    def test_real_world_truncation(self):
        """Test with the actual truncated JSON from the user's example"""
        real_truncated = '''{"narrative": "[SESSION_HEADER]\\nTimestamp: Year 1620, Kythorn, Day 10, 02:05 PM\\nLocation: The Eastern March, on the road to the Dragon's Tooth mountains.\\nStatus: Lvl 1 Fighter/Paladin | HP: 12/12 | Gold: 25gp\\nResources:\\n- Hero Points: 1/1\\n\\nSir Andrew ignored Gareth's probing question, his focus narrowing back to the mission. He folded the map with crisp, efficient movements and tucked it away. His duty was clear; the feelings of his companions were secondary variables. He turned to the other two members of his small company, his expression a mask of command.\\n\\n\\"Report,\\" he said, his voice flat and devoid of warmth. He looked first to Kiera Varrus, the scout, whose cynical eyes were already scanning the treacherous path ahead.\\n\\nKiera spat on the ground, pulling her leather hood tighter against the wind. \\"It's a goat track at best, Sir Knight. Not a proper road. The ground is loose shale, easy to turn an ankle or alert anything hiding in the rocks.\\" She squinted at the mountains.'''
        
        result, was_incomplete = parse_llm_json_response(real_truncated)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertIn("SESSION_HEADER", result["narrative"])
        self.assertIn("Sir Andrew", result["narrative"])
        self.assertIn("Kiera spat on the ground", result["narrative"])
        # Check newlines are properly unescaped
        self.assertIn("\n", result["narrative"])
        self.assertNotIn("\\n", result["narrative"])
    
    def test_multiple_truncation_points(self):
        """Test JSON truncated at various points"""
        truncations = [
            '{"narr',
            '{"narrative"',
            '{"narrative":',
            '{"narrative": ',
            '{"narrative": "',
            '{"narrative": "Test',
            '{"narrative": "Test"',
            '{"narrative": "Test",',
            '{"narrative": "Test", "entities_mentioned"',
            '{"narrative": "Test", "entities_mentioned": [',
            '{"narrative": "Test", "entities_mentioned": ["a"',
        ]
        
        for truncated in truncations:
            result, was_incomplete = RobustJSONParser.parse(truncated)
            # Should handle all these cases gracefully
            if result and "narrative" in result:
                self.assertIsInstance(result["narrative"], str)
    
    def test_empty_string_values(self):
        """Test that empty string values are preserved, not skipped"""
        # Test with empty narrative
        json_empty_narrative = '{"narrative": "", "entities_mentioned": ["test"], "location_confirmed": "place"}'
        result, was_incomplete = parse_llm_json_response(json_empty_narrative)
        
        self.assertIsNotNone(result)
        self.assertFalse(was_incomplete)
        self.assertEqual(result["narrative"], "")  # Should be empty string, not missing
        self.assertEqual(result["entities_mentioned"], ["test"])
        
        # Test with empty location
        json_empty_location = '{"narrative": "Story", "entities_mentioned": [], "location_confirmed": ""}'
        result, was_incomplete = parse_llm_json_response(json_empty_location)
        
        self.assertIsNotNone(result)
        self.assertFalse(was_incomplete)
        self.assertEqual(result["location_confirmed"], "")  # Should be empty string, not "Unknown"
        
        # Test extraction of empty values from truncated JSON
        truncated_empty = '{"narrative": "", "location_confirmed": ""'
        result, was_incomplete = RobustJSONParser.parse(truncated_empty)
        
        self.assertIsNotNone(result)
        self.assertTrue(was_incomplete)
        self.assertEqual(result["narrative"], "")
        self.assertEqual(result["location_confirmed"], "")


if __name__ == '__main__':
    unittest.main()