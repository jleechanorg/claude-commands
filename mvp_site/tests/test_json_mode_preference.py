import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse
import gemini_service
import main


class TestJSONModePreference(unittest.TestCase):
    """Test that JSON mode is always preferred over regex parsing when available"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_state_updates = {
            "pc_data": {
                "gold": 500,
                "attributes": {
                    "strength": 16
                }
            }
        }
        
    def test_json_mode_preferred_over_markdown_blocks(self):
        """Test that when both JSON and markdown blocks exist, JSON is used"""
        # Create a response with state updates in both JSON and markdown
        narrative_with_block = """The adventurer finds treasure!

[STATE_UPDATES_PROPOSED]
{
    "pc_data": {
        "gold": 100
    }
}
[END_STATE_UPDATES_PROPOSED]"""
        
        # JSON response has different values
        narrative_response = NarrativeResponse(
            narrative=narrative_with_block,
            entities_mentioned=["adventurer"],
            state_updates={
                "pc_data": {
                    "gold": 500  # Different from markdown block
                }
            }
        )
        
        gemini_response = GeminiResponse(
            narrative_text=narrative_with_block,
            structured_response=narrative_response,
            debug_tags_present={},
            
        )
        
        # Verify JSON is preferred
        self.assertEqual(gemini_response.state_updates["pc_data"]["gold"], 500)
        self.assertNotEqual(gemini_response.state_updates["pc_data"]["gold"], 100)
        
    def test_no_fallback_parsing_exists(self):
        """Test that parse_llm_response_for_state_changes no longer exists"""
        # Function should not exist
        self.assertFalse(hasattr(gemini_service, 'parse_llm_response_for_state_changes'))
        
        # Create response with JSON state updates
        narrative_response = NarrativeResponse(
            narrative="Test narrative",
            entities_mentioned=[],
            state_updates=self.sample_state_updates
        )
        
        gemini_response = GeminiResponse(
            narrative_text="Test narrative",
            structured_response=narrative_response,
            debug_tags_present={},
            
        )
        
        # Simulate the main.py logic (now simplified)
        proposed_changes = gemini_response.state_updates
        
        # Verify we get state updates from JSON
        self.assertEqual(proposed_changes, self.sample_state_updates)
            
    def test_no_state_updates_when_no_json(self):
        """Test that no state updates are available when no JSON response"""
        # Create response without structured response
        gemini_response = GeminiResponse(
            narrative_text="Story with [STATE_UPDATES_PROPOSED]{\"pc_data\": {\"gold\": 200}}[END_STATE_UPDATES_PROPOSED]",
            structured_response=None,  # No JSON response
            debug_tags_present={},
            
        )
        
        # JSON mode is the ONLY mode - no fallback
        proposed_changes = gemini_response.state_updates
        
        # Should be empty since there's no structured response
        self.assertEqual(proposed_changes, {})
        
    def test_strip_debug_content_preserves_json_state_updates(self):
        """Test that strip_debug_content doesn't interfere with JSON state updates"""
        # Import strip_debug_content
        from main import strip_debug_content
        
        # Text with debug content
        text_with_debug = """Story text here.
        
[DEBUG_START]
Debug info
[DEBUG_END]

More story."""
        
        # Strip debug content
        stripped = strip_debug_content(text_with_debug)
        
        # Verify story is preserved but debug is removed
        self.assertIn("Story text here", stripped)
        self.assertIn("More story", stripped)
        self.assertNotIn("[DEBUG_START]", stripped)
        self.assertNotIn("Debug info", stripped)
        
    def test_json_extraction_from_code_blocks(self):
        """Test JSON extraction from markdown code blocks"""
        from narrative_response_schema import parse_structured_response
        
        # Test with json language identifier
        json_block = '''Here's the response:
```json
{
    "narrative": "The story continues",
    "entities_mentioned": ["hero"],
    "state_updates": {"pc_data": {"level": 2}}
}
```'''
        
        narrative, response = parse_structured_response(json_block)
        self.assertEqual(narrative, "The story continues")
        self.assertEqual(response.state_updates["pc_data"]["level"], 2)
        
        # Test with generic code block
        generic_block = '''```
{
    "narrative": "Another story",
    "entities_mentioned": ["wizard"],
    "state_updates": {"pc_data": {"mana": 50}}
}
```'''
        
        narrative2, response2 = parse_structured_response(generic_block)
        self.assertEqual(narrative2, "Another story") 
        self.assertEqual(response2.state_updates["pc_data"]["mana"], 50)
        
    def test_no_double_parsing(self):
        """Test that state updates aren't parsed twice"""
        # Create a response where the narrative contains a state update block
        # but we already have JSON state updates
        narrative_with_embedded = """The hero gains experience.

[STATE_UPDATES_PROPOSED]
{"pc_data": {"exp": 100}}
[END_STATE_UPDATES_PROPOSED]"""
        
        narrative_response = NarrativeResponse(
            narrative=narrative_with_embedded,
            entities_mentioned=["hero"],
            state_updates={"pc_data": {"exp": 200}}  # Different value
        )
        
        response = GeminiResponse(
            narrative_text=narrative_with_embedded,
            structured_response=narrative_response,
            debug_tags_present={},
            
        )
        
        # The JSON value should win
        self.assertEqual(response.state_updates["pc_data"]["exp"], 200)


if __name__ == "__main__":
    unittest.main()