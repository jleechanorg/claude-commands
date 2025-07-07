#!/usr/bin/env python3
"""
REAL integration test to reproduce and verify the JSON bug fix.
Uses actual Gemini API and Firestore - costs money but gives real results.
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'mvp_site'))

def test_real_json_bug_reproduction():
    """
    Test the exact user scenario that caused the JSON bug.
    This uses REAL APIs (Gemini + Firestore) and costs money.
    """
    
    print("🔴 REAL INTEGRATION TEST - Using actual APIs (costs money)")
    print("=" * 60)
    
    base_url = "http://localhost:6009"
    
    # Headers for testing bypass (but still uses real Gemini API)
    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-json-bug',
        'Content-Type': 'application/json'
    }
    
    # Check server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Server responding: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False
    
    # Step 1: Create the exact campaign from the bug report
    print("\n🔄 Step 1: Creating campaign with problematic prompt...")
    
    campaign_data = {
        "title": "JSON Bug Test Campaign",
        "prompt": "Play as Nolan's son. He's offering you to join him. TV show invincible",
        "selected_prompts": ["narrative", "mechanics"],
        "generate_companions": False,
        "use_default_world": False
    }
    
    try:
        # This will call real Gemini API
        print("⚠️  Calling REAL Gemini API for initial story...")
        response = requests.post(
            f"{base_url}/api/campaigns",
            json=campaign_data,
            headers=headers,
            timeout=60  # Gemini can be slow
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ Campaign creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        campaign_result = response.json()
        campaign_id = campaign_result.get('campaign_id')
        
        print(f"✅ Campaign created: {campaign_id}")
        
        # Get the campaign details to see the initial story
        print("🔄 Retrieving campaign details to check initial story...")
        response = requests.get(
            f"{base_url}/api/campaigns/{campaign_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get campaign: {response.status_code}")
            return False
        
        campaign_details = response.json()
        story = campaign_details.get('story', [])
        
        if not story:
            print("❌ No story found in campaign")
            return False
        
        # Check the initial AI response (should be the first Gemini entry)
        initial_ai_response = None
        for entry in story:
            if entry.get('actor') == 'gemini':
                initial_ai_response = entry.get('text', '')
                break
        
        if not initial_ai_response:
            print("❌ No initial AI response found")
            return False
        
        print(f"📖 Initial story preview: {initial_ai_response[:200]}...")
        
        # Check for JSON artifacts in initial response
        has_json_artifacts = (
            '"narrative":' in initial_ai_response or 
            '"god_mode_response":' in initial_ai_response or
            '{"narrative"' in initial_ai_response
        )
        
        if has_json_artifacts:
            print("❌ JSON artifacts found in INITIAL story!")
            print(f"Raw content: {initial_ai_response[:500]}...")
            return False
        else:
            print("✅ Initial story clean - no JSON artifacts")
        
    except Exception as e:
        print(f"❌ Campaign creation error: {e}")
        return False
    
    # Step 2: Continue the story multiple times to trigger the bug scenario
    print(f"\n🔄 Step 2: Continuing story to reproduce JSON bug scenario...")
    
    for turn in range(1, 4):
        print(f"\n--- Turn {turn} ---")
        
        try:
            # Real user input that might trigger the bug
            user_input = f"I consider Omni-Man's offer carefully. This is turn {turn}."
            
            print(f"📝 User input: {user_input}")
            print("⚠️  Calling REAL Gemini API for story continuation...")
            
            interaction_data = {
                "input": user_input,
                "mode": "character"
            }
            
            response = requests.post(
                f"{base_url}/api/campaigns/{campaign_id}/interaction",
                json=interaction_data,
                headers=headers,
                timeout=60  # Real Gemini calls take time
            )
            
            if response.status_code != 200:
                print(f"❌ Interaction failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            result = response.json()
            ai_response = result.get('response', '')
            scene_number = result.get('user_scene_number', 'unknown')
            
            print(f"🤖 AI response preview: {ai_response[:200]}...")
            print(f"📊 Scene number: {scene_number}")
            
            # CRITICAL TEST: Check for JSON artifacts in the response
            has_json_artifacts = (
                '"narrative":' in ai_response or 
                '"god_mode_response":' in ai_response or
                '"entities_mentioned":' in ai_response or
                '{"narrative"' in ai_response
            )
            
            if has_json_artifacts:
                print(f"❌ JSON BUG DETECTED in turn {turn}!")
                print(f"Raw JSON artifacts found: {ai_response[:500]}...")
                print("💥 THE FIX DID NOT WORK!")
                return False
            else:
                print(f"✅ Turn {turn} clean - no JSON artifacts")
            
            # Check if this would create the bug display pattern
            simulated_frontend_display = f"Scene #{scene_number}: {ai_response}"
            if '{"' in simulated_frontend_display[:100]:  # Check first 100 chars for JSON start
                print(f"❌ Frontend would display JSON artifacts!")
                print(f"Display preview: {simulated_frontend_display[:200]}...")
                return False
            else:
                print(f"✅ Frontend display would be clean")
            
        except Exception as e:
            print(f"❌ Turn {turn} error: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("🎉 REAL INTEGRATION TEST PASSED!")
    print("✅ No JSON artifacts found in any AI responses")
    print("✅ Frontend display simulation clean")
    print("✅ JSON bug fix VERIFIED with real APIs")
    print("=" * 60)
    
    return True

def main():
    """Run the real integration test."""
    
    # Confirm this is intentional
    print("⚠️  WARNING: This test uses REAL APIs and will cost money!")
    print("⚠️  It will make actual calls to Gemini API (gemini-1.5-flash) and Firestore")
    print("⚠️  Server must be running with TESTING=true for auth bypass")
    
    # Check server is running in real mode
    try:
        response = requests.get("http://localhost:6009/")
        print("✅ Server accessible")
    except:
        print("❌ Server not accessible at localhost:6008")
        sys.exit(1)
    
    print("\n🚀 Proceeding with REAL integration test...")
    
    success = test_real_json_bug_reproduction()
    
    if success:
        print("\n✅ JSON BUG FIX VERIFIED WITH REAL APIS")
        sys.exit(0)
    else:
        print("\n💥 JSON BUG STILL EXISTS - FIX FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()