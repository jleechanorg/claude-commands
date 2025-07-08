"""Test to check if initial story generation returns raw JSON."""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the environment
os.environ['TESTING'] = 'true'

from gemini_service import get_initial_story
from game_state import GameState


class TestInitialStoryJsonBug(unittest.TestCase):
    """Test initial story generation for JSON artifacts."""
    
    def test_initial_story_generation_for_json_artifacts(self):
        """Test that initial story generation returns clean narrative, not raw JSON."""
        
        # Create a test prompt similar to the user's
        test_prompt = "You are Nolan's son from the TV show Invincible. Play as Mark Grayson discovering his powers."
        
        print(f"\nTesting initial story generation...")
        print(f"Prompt: {test_prompt}")
        
        try:
            # Call the initial story generation
            response = get_initial_story(
                prompt=test_prompt,
                selected_prompts=['narrative', 'mechanics'],
                generate_companions=False,
                use_default_world=False
            )
            
            print(f"\nResponse type: {type(response)}")
            print(f"Narrative text preview: {response.narrative_text[:200]}...")
            
            if hasattr(response, 'raw_response'):
                print(f"Raw response preview: {response.raw_response[:200]}...")
            
            # Check for JSON artifacts in the narrative_text
            narrative_has_json = (
                '"narrative":' in response.narrative_text or 
                '"god_mode_response":' in response.narrative_text or
                '"entities_mentioned":' in response.narrative_text
            )
            
            print(f"Contains JSON artifacts: {narrative_has_json}")
            
            # The critical test
            self.assertNotIn('"narrative":', response.narrative_text, 
                           "Initial story narrative_text should not contain JSON keys")
            self.assertNotIn('"god_mode_response":', response.narrative_text, 
                           "Initial story narrative_text should not contain JSON keys") 
            self.assertNotIn('"entities_mentioned":', response.narrative_text, 
                           "Initial story narrative_text should not contain JSON keys")
            self.assertNotIn('{"', response.narrative_text,
                           "Initial story narrative_text should not contain JSON structure")
            
            # Should contain actual story content
            self.assertTrue(len(response.narrative_text) > 50, 
                          "Should have substantial narrative content")
            
            # Check that it's not the entire raw JSON response
            if hasattr(response, 'raw_response'):
                self.assertNotEqual(response.narrative_text, response.raw_response,
                                  "narrative_text should be different from raw_response")
            
            print("✅ Initial story generation test passed!")
            
        except Exception as e:
            print(f"❌ Initial story generation failed: {e}")
            raise
    
    def test_simple_initial_story(self):
        """Test with a very simple prompt to isolate the issue."""
        
        simple_prompt = "A hero begins their adventure."
        
        print(f"\nTesting simple initial story generation...")
        print(f"Simple prompt: {simple_prompt}")
        
        try:
            response = get_initial_story(
                prompt=simple_prompt,
                selected_prompts=[],
                generate_companions=False,
                use_default_world=False
            )
            
            print(f"Simple response preview: {response.narrative_text[:100]}...")
            
            # Should not contain JSON structure (but allow legitimate content with braces)
            self.assertNotIn('"narrative":', response.narrative_text)
            self.assertNotIn('{"narrative":', response.narrative_text)
            self.assertNotIn('"god_mode_response":', response.narrative_text)
            
            print("✅ Simple initial story test passed!")
            
        except Exception as e:
            print(f"❌ Simple initial story failed: {e}")
            raise


if __name__ == '__main__':
    unittest.main()