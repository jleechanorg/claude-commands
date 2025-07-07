#!/usr/bin/env python3
"""
Test the complete flow from API response to frontend display simulation.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mvp_site'))

from narrative_response_schema import parse_structured_response

def simulate_frontend_display(api_response_text, user_scene_number):
    """Simulate what the frontend appendToStory function does."""
    
    # Backend processing (what happens in parse_structured_response)
    narrative_text, response_obj = parse_structured_response(api_response_text)
    
    # Frontend processing (what happens in appendToStory)
    frontend_display = f"Scene #{user_scene_number}: {narrative_text}"
    
    return frontend_display, narrative_text

def test_complete_flow():
    """Test complete flow with the exact bug scenario."""
    
    # The exact problematic input from the user's bug report
    problematic_input = '''Scene #2: {
    "narrative": "[Mode: STORY MODE]\\n[CHARACTER CREATION - Step 2 of 7]\\n\\nAs you approach the towering figure of Omni-Man, you can feel the weight of his presence. His cape billows slightly in the breeze, and his eyes—those same eyes that once looked at you with paternal warmth—now regard you with an intensity that makes your heart race.\\n\\n\\"Mark,\\" he says, his voice carrying that familiar authority but tinged with something you've never heard before—uncertainty? Hope? \\"I've been waiting for this moment. The moment when you'd be ready to understand who we really are. Who *you* really are.\\"\\n\\nHe gestures to the sky above, where stars twinkle in the evening light. \\"This world, this planet—it's small, Mark. But what we can accomplish together... what the Viltrumite Empire can accomplish... it's limitless.\\"\\n\\nOmni-Man's expression softens slightly as he looks at you. \\"I know this is overwhelming. I know you have questions. But I need you to understand—everything I've done, everything I'm asking you to consider—it's because I love you. You're my son, and you have the potential to be something greater than even I am.\\"\\n\\nHe extends his hand toward you. \\"The choice is yours, Mark. Stand with me, and we can reshape the universe itself. Or...\\" He doesn't finish the sentence, but the implication hangs heavy in the air.",
    "god_mode_response": "",
    "entities_mentioned": ["Mark Grayson", "Nolan", "Omni-Man"],
    "location_confirmed": "Omni-Man's House"
}'''

    print("=== Testing Complete Flow (Bug Scenario) ===")
    print("Simulating API response processing...")
    
    # Simulate the complete flow
    frontend_display, clean_narrative = simulate_frontend_display(problematic_input, 2)
    
    print(f"✅ Clean narrative extracted: {clean_narrative[:100]}...")
    print(f"✅ Frontend display: {frontend_display[:100]}...")
    
    # Check for JSON artifacts in the final display
    has_json_artifacts = ('"narrative":' in frontend_display or 
                         '"god_mode_response":' in frontend_display or
                         '{"' in frontend_display)
    
    if has_json_artifacts:
        print("❌ JSON artifacts still present in frontend display!")
        return False
    else:
        print("✅ No JSON artifacts in frontend display!")
        return True

if __name__ == "__main__":
    print("Testing complete API to frontend flow...\n")
    success = test_complete_flow()
    print(f"\n🎯 Final result: {'Success - Bug fixed!' if success else 'Failure - Bug still present'}")
    sys.exit(0 if success else 1)