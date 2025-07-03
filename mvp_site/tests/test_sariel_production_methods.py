"""
Test Sariel campaign using actual production methods (get_initial_story, continue_story).
This is kept separate because it tests the methods directly rather than through the API.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_service import get_initial_story, continue_story
from game_state import GameState


class TestSarielProductionMethods(unittest.TestCase):
    """Test actual production methods with Sariel campaign"""
    
    def test_production_methods_entity_tracking(self):
        """Test entity tracking through production methods"""
        print("\n=== Testing Production Methods ===")
        
        # Test initial story generation
        print("\n1. Testing get_initial_story...")
        initial_prompt = """You are Sariel, a member of House Arcanus known for magical prowess. 
        You've been summoned to the throne room where you find your estranged brother Cassian 
        waiting with grave news about your family's legacy."""
        
        initial_result = get_initial_story(initial_prompt)
        self.assertIsNotNone(initial_result)
        self.assertIn('narrative', initial_result)
        
        # Check for Sariel in initial narrative
        narrative = initial_result['narrative']
        self.assertIn('Sariel', narrative, "Player character Sariel missing from initial story")
        
        # Create game state from initial story
        game_state = GameState()
        if 'state_updates' in initial_result and initial_result['state_updates']:
            game_state.apply_state_updates(initial_result['state_updates'])
        
        # Verify player character data was created
        self.assertIsNotNone(game_state.player_character_data)
        self.assertIn('name', game_state.player_character_data)
        
        print(f"✓ Initial story contains Sariel: {'Sariel' in narrative}")
        print(f"✓ Player character data created: {bool(game_state.player_character_data)}")
        
        # Test continue story with Cassian reference
        print("\n2. Testing continue_story with Cassian reference...")
        user_input = "Tell Cassian I was scared and helpless"
        
        continue_result = continue_story(
            game_state=game_state.to_dict(),
            narrative_history="*Previous narrative about meeting Cassian*",
            user_input=user_input,
            turn_number=2
        )
        
        self.assertIsNotNone(continue_result)
        self.assertIn('narrative', continue_result)
        
        # Check for both Sariel and Cassian
        continue_narrative = continue_result['narrative']
        sariel_found = 'Sariel' in continue_narrative
        cassian_found = 'Cassian' in continue_narrative
        
        print(f"✓ Sariel in response: {sariel_found}")
        print(f"✓ Cassian in response: {cassian_found}")
        
        # The Cassian Problem would manifest here
        if not cassian_found and 'scared' in user_input:
            print("⚠️  CASSIAN PROBLEM DETECTED: Player referenced Cassian but AI didn't include him")
        
        # Test entity preloading effectiveness
        if 'debug_info' in continue_result:
            debug = continue_result['debug_info']
            if 'entity_manifest' in debug:
                print("\n3. Entity Preloading Active:")
                print(f"✓ Entity manifest included in prompt")
                
        # Summary
        print("\n=== Production Methods Summary ===")
        print(f"Initial story entity tracking: {'PASS' if 'Sariel' in narrative else 'FAIL'}")
        print(f"Continue story entity tracking: {'PASS' if sariel_found and cassian_found else 'PARTIAL' if sariel_found else 'FAIL'}")
        
        # Assert basic functionality
        self.assertTrue(sariel_found, "Sariel missing from continue_story response")


if __name__ == '__main__':
    # Note: This test makes real API calls
    print("WARNING: This test makes real Gemini API calls")
    print("Set TESTING=true to use faster models")
    unittest.main()