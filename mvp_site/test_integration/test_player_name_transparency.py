#!/usr/bin/env python3
"""Test that player name choices are respected and never silently substituted."""

import os
import sys
import logging_util
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_service import get_initial_story, continue_story
from game_state import GameState

def test_player_name_transparency():
    """Test that the AI respects player name choices and is transparent about any issues."""
    # Set up environment
    os.environ['TESTING'] = 'true'
    logging_util.basicConfig(level=logging_util.INFO)
    
    print("\n=== Testing Player Name Transparency ===\n")
    
    # Test with a name that might be on a banned list
    test_cases = [
        {
            "name": "Drake",
            "description": "wants to kill all dragons because they destroyed his village",
            "expected": "Should either use Drake or explicitly ask about using it"
        },
        {
            "name": "Corvus",  # This IS on the banned list
            "description": "a mysterious rogue",
            "expected": "Should acknowledge Corvus and offer to use it anyway"
        },
        {
            "name": "Shadowblade McEdgelord",  # Ridiculous but player choice
            "description": "the edgiest edge that ever edged",
            "expected": "Should respect player's choice even if silly"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing with name: {test_case['name']} ---")
        print(f"Description: {test_case['description']}")
        print(f"Expected: {test_case['expected']}\n")
        
        try:
            # Initial setup - get to name selection step
            initial_prompt = "I want to create a character"
            selected_prompts = ['mechanics']
            
            # Simulate getting to the name step (simplified for test)
            game_state = GameState()
            story_context = [
                {"actor": "gemini", "text": "Please provide a name for your character"},
                {"actor": "user", "text": f"1. {test_case['name']} 2. {test_case['description']}"}
            ]
            
            # Get response
            response = continue_story(
                f"1. {test_case['name']} 2. {test_case['description']}", 
                "character", 
                story_context, 
                game_state,
                selected_prompts=selected_prompts
            )
            
            print("AI Response:")
            print(response[:500] + "..." if len(response) > 500 else response)
            
            # Check for transparency
            name_mentioned = test_case['name'].lower() in response.lower()
            substituted = any(name in response for name in ["Lycius", "Thorne", "different name"])
            
            if name_mentioned and not substituted:
                print(f"\n✅ SUCCESS: AI acknowledged and used '{test_case['name']}'")
            elif name_mentioned and "would you like" in response.lower():
                print(f"\n✅ SUCCESS: AI acknowledged '{test_case['name']}' and asked for confirmation")
            elif not name_mentioned:
                print(f"\n❌ FAILURE: AI ignored player's choice of '{test_case['name']}'")
            else:
                print(f"\n⚠️  PARTIAL: AI mentioned name but may have substituted")
                
            print("-" * 50)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_player_name_transparency()