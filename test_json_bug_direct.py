#!/usr/bin/env python3
"""
Direct test of gemini_service to reproduce the JSON display bug.
This bypasses the web layer to directly test where JSON parsing might be failing.
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mvp_site'))

# Set test environment
os.environ['TESTING'] = 'true'

from mvp_site import gemini_service

def test_json_bug():
    """Test the exact scenario that produces raw JSON."""
    print("\n=== Direct JSON Bug Test ===")
    
    # The exact prompt that triggered the bug
    prompt = "Play as Nolan's son. He's offering you to join him. TV show invincible"
    
    print(f"\n📝 Testing with prompt: {prompt}")
    
    # Test 1: Generate opening story
    print("\n1️⃣ Testing get_initial_story...")
    try:
        result = gemini_service.get_initial_story(prompt)
        print(f"   Result type: {type(result)}")
        
        if isinstance(result, dict):
            print("   ✅ Returned dict (expected)")
            
            # Check for raw JSON in narrative
            narrative = result.get('narrative', '')
            if '"narrative":' in narrative or 'Scene #' in narrative:
                print(f"   ❌ JSON ARTIFACTS IN NARRATIVE!")
                print(f"   Preview: {narrative[:200]}...")
            else:
                print("   ✅ No JSON artifacts in narrative")
                
        elif isinstance(result, str):
            print("   ⚠️ Returned string (unexpected)")
            if '"narrative":' in result or 'Scene #' in result:
                print(f"   ❌ RAW JSON STRING RETURNED!")
                print(f"   Preview: {result[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Continue story
    print("\n2️⃣ Testing continue_story...")
    action = "I look at my father with confusion. 'Join you? What are you talking about, Dad?'"
    
    # Create a mock story context and game state
    story_context = [{
        'role': 'ai',
        'content': "Nolan stands before you, his Viltrumite uniform gleaming...",
        'entities_mentioned': ['Nolan', 'Mark']
    }]
    
    # Create a mock game state
    from mvp_site.game_state import GameState
    game_state = GameState()
    game_state.world_description = prompt
    
    try:
        result = gemini_service.continue_story(action, "character", story_context, game_state)
        print(f"   Result type: {type(result)}")
        
        if isinstance(result, dict):
            print("   ✅ Returned dict (expected)")
            
            # Check for raw JSON in narrative
            narrative = result.get('narrative', '')
            if '"narrative":' in narrative or 'Scene #' in narrative:
                print(f"   ❌ JSON ARTIFACTS IN NARRATIVE!")
                print(f"   Preview: {narrative[:200]}...")
            else:
                print("   ✅ No JSON artifacts in narrative")
                
        elif isinstance(result, str):
            print("   ⚠️ Returned string (unexpected)")
            if '"narrative":' in result or 'Scene #' in result:
                print(f"   ❌ RAW JSON STRING RETURNED!")
                print(f"   Preview: {result[:200]}...")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check the _process_structured_response method directly
    print("\n3️⃣ Testing _process_structured_response directly...")
    
    # Create a mock response that might trigger the bug
    mock_json_response = '''Scene #2: {
        "narrative": "[Mode: STORY MODE]\\n[CHARACTER CREATION - Step 2 of 7]...",
        "god_mode_response": "",
        "entities_mentioned": ["Mark Grayson", "Nolan"],
        "scene_number": 2,
        "location": "Grayson household"
    }'''
    
    try:
        # Access the private method for testing
        result = gemini_service._process_structured_response(mock_json_response, [])
        print(f"   Result type: {type(result)}")
        
        if isinstance(result, dict):
            narrative = result.get('narrative', '')
            if 'Scene #' in narrative:
                print(f"   ❌ SCENE PATTERN LEAKED INTO NARRATIVE!")
                print(f"   Narrative: {narrative[:200]}...")
            else:
                print("   ✅ JSON properly parsed")
        else:
            print(f"   ⚠️ Unexpected result type: {type(result)}")
            
    except Exception as e:
        print(f"   ❌ Error processing mock response: {e}")
    
    print("\n📊 Test Summary:")
    print("Check server logs for JSON_BUG entries to trace the issue")
    print("Look for patterns where 'Scene #X: {' appears in the output")


if __name__ == "__main__":
    test_json_bug()