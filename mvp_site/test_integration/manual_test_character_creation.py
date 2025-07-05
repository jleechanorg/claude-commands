#!/usr/bin/env python3
"""Manual test to verify character creation triggers properly."""

import os
import sys
import logging_util
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_service import get_initial_story

def test_character_creation():
    """Test that character creation triggers with a real prompt."""
    # Set up environment
    os.environ['TESTING'] = 'true'
    logging_util.basicConfig(level=logging_util.INFO)
    
    print("\n=== Testing Character Creation Trigger ===\n")
    
    # Test prompt similar to what a user might provide
    user_prompt = "I want to play as a brave knight in a medieval fantasy kingdom"
    selected_prompts = ['mechanics', 'narrative']
    
    print(f"User prompt: {user_prompt}")
    print(f"Selected prompts: {selected_prompts}")
    print("\n--- Generating initial story with mechanics enabled ---\n")
    
    try:
        response = get_initial_story(user_prompt, selected_prompts=selected_prompts)
        
        print("=== AI Response ===")
        print(response)
        print("\n=== End Response ===")
        
        # Check if character creation was triggered
        if "character creation" in response.lower() or "create your character" in response.lower() or "option" in response.lower():
            print("\n✅ SUCCESS: Character creation was triggered!")
        else:
            print("\n❌ FAILURE: Character creation was NOT triggered!")
            print("The AI should have presented character creation options.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_character_creation()