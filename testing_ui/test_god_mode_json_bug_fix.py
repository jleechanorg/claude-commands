#!/usr/bin/env python3
"""
Test to verify that god mode responses are properly formatted and not displaying raw JSON.
This test specifically checks for the bug found in Luke's campaign log.
"""

import os
import sys
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_config import BASE_URL, get_test_session

SESSION = get_test_session()

def test_god_mode_json_display_bug():
    """Test that god mode responses display formatted content, not raw JSON."""
    print("🔮 TEST: God Mode JSON Display Bug Fix")
    print("=" * 50)
    
    # Create campaign
    print("\n1️⃣ Creating test campaign...")
    campaign_data = {
        "prompt": "Test campaign for god mode JSON bug",
        "enableNarrative": True,
        "enableMechanics": True
    }
    
    response = SESSION.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
    assert response.status_code in [200, 201], f"❌ Failed to create campaign: {response.status_code}\nResponse: {response.text}"
    
    campaign = response.json()
    campaign_id = campaign.get('campaign_id')
    print(f"✅ Campaign created: {campaign_id}")
    
    # Test god mode commands that previously caused JSON display issues
    test_commands = [
        {
            "input": "GOD MODE: A divine revelation occurs - you gain insight into the nature of reality",
            "description": "Simple god mode command"
        },
        {
            "input": "GOD MODE: The gods grant you experience for your trials and tribulations",
            "description": "XP-related god mode (like Luke's campaign bug)"
        },
        {
            "input": "GOD MODE: A mysterious figure appears and speaks to you with divine authority",
            "description": "Complex god mode with narrative"
        }
    ]
    
    print(f"\n2️⃣ Testing {len(test_commands)} god mode commands for JSON display bugs...")
    
    for i, test_case in enumerate(test_commands, 1):
        print(f"\n  Test {i}: {test_case['description']}")
        print(f"  Command: '{test_case['input'][:50]}...'")
        
        # Send god mode command
        story_data = {
            "input": test_case['input'],
            "mode": "character"  # Server detects god mode from "GOD MODE:" prefix
        }
        
        response = SESSION.post(f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            print(f"  ✅ God command executed (status: {response.status_code})")
            print(f"  📝 Response length: {len(response_text)} characters")
            
            # Check for the specific JSON display bug
            json_indicators = [
                '"narrative":',
                '"god_mode_response":',
                '"entities_mentioned":',
                '"state_updates":',
                '"debug_info":'
            ]
            
            json_found = any(indicator in response_text for indicator in json_indicators)
            
            if json_found:
                print(f"  ❌ BUG DETECTED: Response contains raw JSON structure!")
                print(f"  🔍 Response preview: {response_text[:200]}...")
                
                # Show exactly which JSON indicators were found
                for indicator in json_indicators:
                    if indicator in response_text:
                        print(f"      Found: {indicator}")
                
                return False
            else:
                print(f"  ✅ No raw JSON detected in response")
                print(f"  📖 Response preview: {response_text[:100]}...")
                
                # Additional check: response should contain meaningful content
                if len(response_text.strip()) > 10:
                    print(f"  ✅ Response contains meaningful content")
                else:
                    print(f"  ⚠️  Response seems too short: '{response_text}'")
        else:
            print(f"  ❌ Failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    
    # Test specific Luke campaign scenario reproduction
    print(f"\n3️⃣ Testing Luke campaign scenario reproduction...")
    
    luke_scenario_commands = [
        "I ask about experience points for my actions",
        "GOD MODE: You are absolutely right that completing such a significant task deserves substantial rewards"
    ]
    
    for command in luke_scenario_commands:
        print(f"\n  Command: '{command[:50]}...'")
        
        story_data = {
            "input": command,
            "mode": "character"
        }
        
        response = SESSION.post(f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            # Check for Scene #X: { pattern (the exact bug from Luke's log)
            scene_json_pattern = response_text.strip().startswith('Scene #') and '{' in response_text
            
            if scene_json_pattern:
                print(f"  ❌ EXACT LUKE BUG DETECTED: Scene #X: {{ pattern found!")
                print(f"  🔍 Response: {response_text[:300]}...")
                return False
            else:
                print(f"  ✅ No Scene #X: {{ pattern detected")
        else:
            print(f"  ❌ Failed: {response.status_code}")
            return False
    
    print(f"\n4️⃣ Testing response structure integrity...")
    
    # Get campaign story to check logged entries
    response = SESSION.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
    if response.status_code == 200:
        campaign_data = response.json()
        story_entries = campaign_data.get('story', [])
        
        print(f"  📊 Story has {len(story_entries)} entries")
        
        # Check the last few entries for JSON artifacts
        for entry in story_entries[-3:]:  # Check last 3 entries
            text = entry.get('text', '')
            actor = entry.get('actor', '')
            
            if actor == 'gemini':  # AI responses
                if '"narrative":' in text or '"god_mode_response":' in text:
                    print(f"  ❌ JSON ARTIFACTS IN LOGGED STORY!")
                    print(f"  🔍 Entry text: {text[:200]}...")
                    return False
                else:
                    print(f"  ✅ Story entry clean (length: {len(text)})")
    
    return True

def test_god_mode_response_field_handling():
    """Test that god_mode_response field is properly handled in the API."""
    print("\n🔧 TEST: God Mode Response Field Handling")
    print("=" * 50)
    
    # This simulates what happens when the backend processes a god mode response
    # We can't directly test the internal parse_structured_response function via HTTP,
    # but we can test the end-to-end behavior
    
    # Create a minimal test campaign
    campaign_data = {
        "prompt": "Test god mode field handling",
        "enableNarrative": True,
        "enableMechanics": False
    }
    
    response = SESSION.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create test campaign: {response.status_code}")
        return False
    
    campaign = response.json()
    campaign_id = campaign.get('campaign_id')
    
    # Send a god mode command and check the response structure
    story_data = {
        "input": "GOD MODE: Test response field handling with special characters and newlines",
        "mode": "character"
    }
    
    response = SESSION.post(f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data)
    
    if response.status_code == 200:
        result = response.json()
        
        # Check response structure
        expected_fields = ['success', 'response', 'debug_mode', 'sequence_id']
        
        for field in expected_fields:
            if field in result:
                print(f"  ✅ Field '{field}' present")
            else:
                print(f"  ❌ Field '{field}' missing")
                return False
        
        # The 'response' field should contain clean text, not JSON
        response_text = result.get('response', '')
        if response_text and not response_text.startswith('{'):
            print(f"  ✅ Response field contains clean text")
            return True
        else:
            print(f"  ❌ Response field contains JSON or is empty: '{response_text[:100]}'")
            return False
    else:
        print(f"  ❌ API call failed: {response.status_code}")
        return False

if __name__ == "__main__":
    try:
        # Check if server is running
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Server running at {BASE_URL}\n")
        
        # Run both tests
        test1_success = test_god_mode_json_display_bug()
        test2_success = test_god_mode_response_field_handling()
        
        overall_success = test1_success and test2_success
        
        print(f"\n{'='*50}")
        print(f"God Mode JSON Display Bug Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
        print(f"God Mode Response Field Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
        print(f"Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()