#!/usr/bin/env python3
from test_config import BASE_URL, get_test_session
"""
Test multiple gameplay turns in a session.
"""

import os
import sys
import json
import requests
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Using BASE_URL from test_config
SESSION = get_test_session()

def test_multiple_turns():
    """Test playing multiple turns in a campaign."""
    print("🎲 TEST: Multiple Gameplay Turns")
    print("=" * 50)
    
    # Create campaign
    print("\n1️⃣ Creating campaign...")
    campaign_data = {
        "prompt": "Pirates searching for treasure on a mysterious island",
        "enableNarrative": True,
        "enableMechanics": True
    }
    
    response = SESSION.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create campaign: {response.status_code}")
        return False
    
    campaign = response.json()
    campaign_id = campaign.get('campaign_id')
    print(f"✅ Campaign created: {campaign_id}")
    
    # Play multiple turns
    turns = [
        ("I examine the old map carefully", "character"),
        ("I head towards the marked X on the map", "character"),
        ("I use my shovel to dig at the spot", "character"),
        ("GOD MODE: A skeleton emerges from the sand!", "god"),
        ("I draw my cutlass and prepare to fight!", "character"),
        ("I slash at the skeleton's ribcage", "character")
    ]
    
    print(f"\n2️⃣ Playing {len(turns)} turns...")
    
    for i, (action, mode) in enumerate(turns, 1):
        print(f"\n  Turn {i}/{len(turns)}:")
        print(f"  📝 Action: '{action[:50]}...'")
        print(f"  🎮 Mode: {mode}")
        
        # Prepare request based on mode
        if mode == "god" and action.startswith("GOD MODE:"):
            # For god mode, send the text with GOD MODE prefix
            story_data = {
                "campaignId": campaign_id,
                "input": action,
                "mode": "character"  # API detects god mode from text
            }
        else:
            story_data = {
                "campaignId": campaign_id,
                "input": action,
                "mode": mode
            }
        
        # Send action
        response = SESSION.post(f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data)
        
        if response.status_code == 200:
            result = response.json()
            response_length = len(result.get('text', ''))
            print(f"  ✅ AI responded: {response_length} chars")
            
            # Check for state changes
            if 'state' in result:
                print(f"  📊 State updated: {list(result['state'].keys())}")
        else:
            print(f"  ❌ Failed: {response.status_code}")
            return False
        
        # Small delay between turns
        time.sleep(0.5)
    
    # Verify campaign has all entries
    print("\n3️⃣ Verifying campaign history...")
    response = SESSION.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
    
    if response.status_code == 200:
        campaign_data = response.json()
        entries = campaign_data.get('entries', [])
        print(f"✅ Campaign has {len(entries)} entries")
        
        # Count player vs AI entries
        player_entries = sum(1 for e in entries if e.get('actor') == 'user')
        ai_entries = sum(1 for e in entries if e.get('actor') == 'gemini')
        print(f"  👤 Player: {player_entries} entries")
        print(f"  🤖 AI: {ai_entries} entries")
        
        return len(entries) >= len(turns) * 2  # Each turn should have request + response
    
    return False

if __name__ == "__main__":
    try:
        # Check server
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Server running at {BASE_URL}\n")
        
        success = test_multiple_turns()
        print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")