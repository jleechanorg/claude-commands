#!/usr/bin/env python3
"""
FULL API Test: Continue an existing campaign using real Firebase and Gemini APIs.

WARNING: This test uses REAL APIs and will incur costs!
"""

import os
import sys
import json
import requests
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_config_full import BASE_URL, get_test_session, validate_config, CostTracker

def test_continue_campaign_full():
    """Test loading and continuing an existing campaign with full APIs."""
    print("🎮 FULL API TEST: Continue Existing Campaign")
    print("⚠️  This test uses REAL Gemini API and costs money!")
    print("=" * 50)
    
    # Validate configuration
    if not validate_config():
        return False
    
    SESSION = get_test_session()
    tracker = CostTracker()
    
    try:
        # Step 1: Create a campaign first
        print("\n1️⃣ Creating initial campaign with REAL Gemini...")
        campaign_data = {
            "prompt": "A knight defending a castle",  # Keep short to minimize cost
            "enableNarrative": True,
            "enableMechanics": False
        }
        
        response = SESSION.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
        tracker.track_gemini(estimated_tokens=2000)  # Campaign creation uses more tokens
        tracker.track_firestore('write', 2)  # Campaign + game state
        
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create campaign: {response.status_code}")
            print(response.json())
            return False
        
        campaign = response.json()
        campaign_id = campaign.get('campaign_id') or campaign.get('campaignId') or campaign.get('id')
        print(f"✅ Campaign created: {campaign_id}")
        
        # Step 2: Make one initial move
        print("\n2️⃣ Making initial move...")
        story_data = {
            "campaignId": campaign_id,
            "input": "I inspect the walls",  # Short to save cost
            "mode": "character"
        }
        
        response = SESSION.post(f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data)
        tracker.track_gemini(estimated_tokens=1000)
        tracker.track_firestore('read', 2)
        tracker.track_firestore('write', 1)
        
        if response.status_code != 200:
            print(f"❌ Failed to make move: {response.status_code}")
            return False
        
        print("✅ Initial move completed")
        time.sleep(1)  # Brief pause
        
        # Step 3: Simulate closing and reopening
        print("\n3️⃣ Simulating browser close/reopen...")
        NEW_SESSION = get_test_session()
        
        # Step 4: Load campaign list
        print("\n4️⃣ Loading campaign list...")
        response = NEW_SESSION.get(f"{BASE_URL}/api/campaigns")
        tracker.track_firestore('read', 10)  # Estimate for list query
        
        campaigns = response.json() if response.status_code == 200 else []
        print(f"  📊 Found {len(campaigns)} campaigns")
        
        found = False
        for camp in campaigns:
            camp_id = camp.get('id') or camp.get('campaignId')
            if camp_id == campaign_id:
                found = True
                print(f"  ✅ Found our campaign: {camp.get('title', 'Untitled')}")
                break
        
        if not found:
            print("  ❌ Campaign not found in list!")
            return False
        
        # Step 5: Load the specific campaign
        print(f"\n5️⃣ Loading campaign {campaign_id}...")
        response = NEW_SESSION.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
        tracker.track_firestore('read', 5)  # Campaign + entries
        
        if response.status_code != 200:
            print(f"  ❌ Failed to load campaign: {response.status_code}")
            return False
        
        campaign_data = response.json()
        entries = campaign_data.get('entries', [])
        print(f"  ✅ Campaign loaded with {len(entries)} entries")
        
        # Step 6: Continue playing (minimal to save cost)
        print("\n6️⃣ Continuing gameplay...")
        continue_move = "I prepare defenses"
        story_data = {
            "campaignId": campaign_id,
            "input": continue_move,
            "mode": "character"
        }
        
        response = NEW_SESSION.post(f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data)
        tracker.track_gemini(estimated_tokens=1000)
        tracker.track_firestore('read', 2)
        tracker.track_firestore('write', 1)
        
        if response.status_code == 200:
            print(f"  ✅ Successfully continued campaign")
            result = response.json()
            print(f"  📜 AI responded with {len(result.get('story', ''))} characters")
            return True
        else:
            print(f"  ❌ Failed to continue: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
        
    finally:
        # Always print cost summary
        tracker.print_summary()

if __name__ == "__main__":
    # Safety confirmation
    print("⚠️  WARNING: This test uses REAL APIs and will cost money!")
    print("Estimated cost: ~$0.001")
    response = input("Continue? (y/n): ")
    
    if response.lower() != 'y':
        print("Test cancelled.")
        sys.exit(0)
    
    # Run test
    success = test_continue_campaign_full()
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")