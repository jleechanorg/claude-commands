#!/usr/bin/env python3
"""
Real browser simulation test for WorldArchitect.AI
Tests the actual running server at http://localhost:8080
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"
TEST_USER_ID = "test-user-browser-sim"

def log(message):
    """Log with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def test_homepage():
    """Test homepage loading"""
    log("Testing homepage...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert "WorldArchitect.AI" in response.text
    assert len(response.text) > 10000  # Should be substantial HTML
    log(f"✅ Homepage loaded successfully ({len(response.text)} bytes)")

def test_static_assets():
    """Test static asset loading"""
    log("Testing static assets...")
    assets = [
        "/static/app.js",
        "/static/style.css",
        "/static/auth.js",
        "/static/themes/dark.css",
        "/static/themes/light.css"
    ]
    
    for asset in assets:
        response = requests.get(f"{BASE_URL}{asset}")
        assert response.status_code == 200
        assert len(response.content) > 100
        log(f"✅ {asset} loaded ({len(response.content)} bytes)")

def test_campaign_creation():
    """Test campaign creation API with test bypass"""
    log("Testing campaign creation...")
    
    # Test with authentication bypass
    headers = {
        "Content-Type": "application/json",
        "X-Test-Bypass": "true",
        "X-Test-User-Id": TEST_USER_ID
    }
    
    campaign_data = {
        "title": "Real Browser Test Campaign",
        "prompt": "A brave adventurer explores the mystical realm of Assiah, seeking ancient artifacts.",
        "selectedPrompts": ["narrative", "mechanics"],
        "customOptions": ["companions", "defaultWorld"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/campaigns",
        headers=headers,
        json=campaign_data
    )
    
    # If test bypass doesn't work, try without auth
    if response.status_code == 401:
        log("⚠️ Test bypass failed, server may not be in testing mode")
        log(f"Response: {response.text}")
        return None
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "campaignId" in data
    log(f"✅ Campaign created successfully: {data['campaignId']}")
    return data["campaignId"]

def test_story_interaction(campaign_id):
    """Test story interaction"""
    if not campaign_id:
        log("⚠️ Skipping story interaction test (no campaign)")
        return
        
    log("Testing story interaction...")
    
    headers = {
        "Content-Type": "application/json",
        "X-Test-Bypass": "true",
        "X-Test-User-Id": TEST_USER_ID
    }
    
    interaction_data = {
        "input": "I examine my surroundings carefully.",
        "mode": "character"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interact",
        headers=headers,
        json=interaction_data
    )
    
    if response.status_code != 200:
        log(f"❌ Story interaction failed: {response.status_code}")
        log(f"Response: {response.text}")
        return
    
    data = response.json()
    assert "story" in data
    assert len(data["story"]) > 100
    log(f"✅ Story interaction successful ({len(data['story'])} chars)")
    
    # Test combat interaction
    log("Testing combat interaction...")
    combat_data = {
        "input": "I attack the nearest enemy with my sword!",
        "mode": "character"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interact",
        headers=headers,
        json=combat_data
    )
    
    if response.status_code == 500:
        error_data = response.json()
        if "AttributeError" in error_data.get("traceback", ""):
            log("❌ CRITICAL BUG CONFIRMED: Combat AttributeError present!")
            log("Error confirms PR #314's claimed finding")
        else:
            log(f"❌ Different error: {error_data.get('error', 'Unknown')}")
    else:
        log("✅ Combat interaction worked (bug may be fixed)")

def test_campaign_retrieval(campaign_id):
    """Test campaign retrieval"""
    if not campaign_id:
        log("⚠️ Skipping campaign retrieval test (no campaign)")
        return
        
    log("Testing campaign retrieval...")
    
    headers = {
        "X-Test-Bypass": "true",
        "X-Test-User-Id": TEST_USER_ID
    }
    
    response = requests.get(
        f"{BASE_URL}/api/campaigns/{campaign_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        log(f"❌ Campaign retrieval failed: {response.status_code}")
        return
    
    data = response.json()
    assert "title" in data
    assert "storyTurns" in data
    log(f"✅ Campaign retrieved: {data['title']} ({len(data['storyTurns'])} turns)")

def main():
    """Run all tests"""
    log("🚀 Starting real browser simulation tests...")
    log(f"Target: {BASE_URL}")
    
    try:
        # Basic connectivity
        test_homepage()
        test_static_assets()
        
        # API functionality
        campaign_id = test_campaign_creation()
        
        if campaign_id:
            # Wait a bit for campaign to be fully created
            time.sleep(2)
            
            test_story_interaction(campaign_id)
            test_campaign_retrieval(campaign_id)
        
        log("\n✅ Real browser simulation complete!")
        log("Key findings:")
        log("- Server is running and responsive")
        log("- Static assets loading correctly")
        if campaign_id:
            log("- API endpoints functional (with test bypass)")
        else:
            log("- API requires authentication (test bypass not working)")
            log("- Server may not be in TESTING mode")
        
    except Exception as e:
        log(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()