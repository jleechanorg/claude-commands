#!/usr/bin/env python3
"""Test that state updates are proposed during character creation."""

import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_service import get_initial_story

def test_character_creation_state_updates():
    """Test that character creation proposes state updates."""
    # Set up environment
    os.environ['TESTING'] = 'true'
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== Testing Character Creation State Updates ===\n")
    
    # Initial prompt with mechanics enabled
    user_prompt = "I want to create a warrior character"
    selected_prompts = ['mechanics']
    
    print(f"User prompt: {user_prompt}")
    print(f"Selected prompts: {selected_prompts}\n")
    
    try:
        # Get initial response
        response = get_initial_story(user_prompt, selected_prompts=selected_prompts)
        
        print("AI Response (first 500 chars):")
        print(response[:500] + "..." if len(response) > 500 else response)
        print("\n" + "="*50 + "\n")
        
        # Check for state updates
        has_state_updates = "[STATE_UPDATES_PROPOSED]" in response or "STATE_UPDATES_PROPOSED" in response
        has_end_marker = "[END_STATE_UPDATES_PROPOSED]" in response or "END_STATE_UPDATES_PROPOSED" in response
        
        if has_state_updates and has_end_marker:
            print("✅ SUCCESS: State updates block found in response")
            
            # Extract the state update block
            import re
            state_match = re.search(r'\[STATE_UPDATES_PROPOSED\](.*?)\[END_STATE_UPDATES_PROPOSED\]', 
                                  response, re.DOTALL)
            if state_match:
                state_content = state_match.group(1).strip()
                print("\nState update content:")
                print(state_content[:200] + "..." if len(state_content) > 200 else state_content)
                
                # Check if it tracks character creation
                if "character_creation" in state_content or "custom_campaign_state" in state_content:
                    print("\n✅ Character creation progress being tracked!")
                else:
                    print("\n⚠️  State update found but may not track character creation progress")
        else:
            print("❌ FAILURE: No state updates block found")
            print("The AI should propose state updates in EVERY response")
            
            # Check if response mentions why no state updates
            if "debug" in response.lower() or "state" in response.lower():
                print("\nResponse mentions state/debug:")
                debug_lines = [line for line in response.split('\n') if 'debug' in line.lower() or 'state' in line.lower()]
                for line in debug_lines[:3]:
                    print(f"  - {line.strip()}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_character_creation_state_updates()