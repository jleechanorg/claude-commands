#!/usr/bin/env python3
"""Test that numeric inputs during character creation are handled correctly."""

import os
import sys
import logging_util
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_service import get_initial_story, continue_story
from game_state import GameState

def test_numeric_race_selection():
    """Test that numeric input '1' selects the first race option."""
    # Set up environment
    os.environ['TESTING'] = 'true'
    logging_util.basicConfig(level=logging_util.INFO)
    
    print("\n=== Testing Numeric Input During Character Creation ===\n")
    
    # Step 1: Initial prompt with mechanics enabled
    user_prompt = "I want to play as a knight"
    selected_prompts = ['mechanics', 'narrative']
    
    print(f"Initial prompt: {user_prompt}")
    print(f"Selected prompts: {selected_prompts}")
    print("\n--- Step 1: Getting character creation options ---\n")
    
    try:
        # Get initial response (should present character creation options)
        initial_response = get_initial_story(user_prompt, selected_prompts=selected_prompts)
        print("AI Response:")
        print(initial_response)
        print("\n" + "="*50 + "\n")
        
        # Step 2: Player chooses option 1 (Create a D&D character)
        print("--- Step 2: Player chooses option 1 ---")
        print("Player input: 1\n")
        
        # Create minimal game state for continuation
        game_state = GameState()
        story_context = [
            {"actor": "gemini", "text": initial_response},
            {"actor": "user", "text": "1"}
        ]
        
        # Get response (should present race options)
        race_response = continue_story("1", "character", story_context, game_state, 
                                     selected_prompts=selected_prompts)
        print("AI Response:")
        print(race_response)
        
        # Check if AI understood this as selecting character creation option 1
        if "human" in race_response.lower() and "elf" in race_response.lower():
            print("\n✅ SUCCESS: AI presented race options after player chose option 1")
        else:
            print("\n❌ ISSUE: AI may not have understood option 1 selection")
            
        print("\n" + "="*50 + "\n")
        
        # Step 3: Player chooses race 1 (Human)
        print("--- Step 3: Player chooses race 1 (Human) ---")
        print("Player input: 1\n")
        
        story_context.append({"actor": "gemini", "text": race_response})
        story_context.append({"actor": "user", "text": "1"})
        
        # Get response (should acknowledge Human selection and move to class)
        class_response = continue_story("1", "character", story_context, game_state,
                                      selected_prompts=selected_prompts)
        print("AI Response:")
        print(class_response)
        
        # Check if AI understood this as selecting Human
        if "human" in class_response.lower() and ("class" in class_response.lower() or 
                                                  "fighter" in class_response.lower() or
                                                  "wizard" in class_response.lower()):
            print("\n✅ SUCCESS: AI understood '1' as Human selection and moved to class selection")
        else:
            print("\n❌ FAILURE: AI did not understand '1' as Human selection")
            print("The AI should have acknowledged the Human race selection.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_numeric_race_selection()