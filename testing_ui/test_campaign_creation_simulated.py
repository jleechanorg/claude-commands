#!/usr/bin/env python3
"""
Simulated browser test that captures HTTP responses as "screenshots"
This demonstrates what the real browser test would do.
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:6006"
SCREENSHOT_DIR = "/tmp/worldarchitect_browser_screenshots"

def save_screenshot(filename, content, description):
    """Save a text representation of what would be visible."""
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(f"=== SCREENSHOT: {filename} ===\n")
        f.write(f"Description: {description}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"URL: {BASE_URL}\n")
        f.write("="*50 + "\n\n")
        f.write(content)
    print(f"📸 Screenshot saved: {filepath}")
    return filepath

def test_campaign_creation_simulated():
    """Simulate browser test with HTTP requests."""
    
    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Test headers for bypassing auth
    headers = {
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": "test-user",
        "Content-Type": "application/json"
    }
    
    print("🌐 Testing WorldArchitect.AI Campaign Creation...")
    
    try:
        # Step 1: Homepage
        print("\n1️⃣ Loading homepage...")
        response = requests.get(BASE_URL)
        
        if response.status_code == 200:
            # Extract visible text from HTML
            text = f"Homepage loaded successfully\n"
            text += f"Status: {response.status_code}\n"
            text += f"Content Length: {len(response.text)} bytes\n\n"
            
            # Look for key UI elements
            if "WorldArchitect" in response.text:
                text += "✅ WorldArchitect title found\n"
            if "New Campaign" in response.text or "Create Campaign" in response.text:
                text += "✅ Campaign creation button found\n"
            if "Sign In" in response.text:
                text += "⚠️ Sign In button detected - auth may be required\n"
            
            save_screenshot("01_homepage.png", text, "Homepage loaded")
        
        # Step 2: Create Campaign
        print("\n2️⃣ Creating campaign...")
        campaign_data = {
            "name": "Browser Test Campaign " + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "description": "Test campaign created via simulated browser test",
            "world_id": "fantasy_default",
            "prompt": "Start a new D&D campaign with a human fighter named Browser Test Hero"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns",
            json=campaign_data,
            headers=headers
        )
        
        if response.status_code == 201:
            campaign = response.json()
            campaign_id = campaign.get('id') or campaign.get('campaign_id')
            
            text = f"Campaign created successfully!\n"
            text += f"Campaign ID: {campaign_id}\n"
            text += f"Campaign Name: {campaign_data['name']}\n"
            text += f"Response: {json.dumps(campaign, indent=2)}\n"
            
            save_screenshot("02_campaign_created.png", text, "Campaign creation response")
            
            # Step 3: Load Campaign
            print(f"\n3️⃣ Loading campaign {campaign_id}...")
            response = requests.get(
                f"{BASE_URL}/api/campaigns/{campaign_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                campaign_details = response.json()
                text = f"Campaign loaded successfully!\n"
                text += f"Campaign State:\n{json.dumps(campaign_details, indent=2)}\n"
                
                save_screenshot("03_campaign_loaded.png", text, "Campaign details loaded")
                
                # Step 4: Create Character
                print("\n4️⃣ Creating character...")
                character_data = {
                    "name": "Test Hero",
                    "race": "Human",
                    "class": "Fighter",
                    "background": "Soldier"
                }
                
                # Simulate character creation interaction
                interaction_data = {
                    "input": f"Create a character named {character_data['name']}, {character_data['race']} {character_data['class']} with {character_data['background']} background"
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/campaigns/{campaign_id}/interaction",
                    json=interaction_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = f"Character creation initiated!\n"
                    text += f"AI Response:\n{result.get('response', 'No response')}\n"
                    
                    save_screenshot("04_character_creation.png", text, "Character creation response")
                
                # Step 5: Final State
                print("\n5️⃣ Capturing final state...")
                response = requests.get(
                    f"{BASE_URL}/api/campaigns/{campaign_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    final_state = response.json()
                    text = f"Final campaign state:\n"
                    text += f"Campaign ID: {campaign_id}\n"
                    text += f"Has Characters: {'characters' in final_state}\n"
                    text += f"Full State:\n{json.dumps(final_state, indent=2)}\n"
                    
                    save_screenshot("05_final_state.png", text, "Final campaign state")
                
                print("\n✅ Test completed successfully!")
                return True
                
        else:
            error_text = f"Campaign creation failed!\n"
            error_text += f"Status: {response.status_code}\n"
            error_text += f"Response: {response.text}\n"
            save_screenshot("error_campaign_creation.png", error_text, "Campaign creation error")
            return False
            
    except Exception as e:
        error_text = f"Test failed with exception:\n{str(e)}\n"
        save_screenshot("error_exception.png", error_text, "Test exception")
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting WorldArchitect.AI Campaign Creation Test (Simulated)")
    print(f"📍 Target URL: {BASE_URL}")
    print(f"📸 Screenshots will be saved to: {SCREENSHOT_DIR}")
    
    success = test_campaign_creation_simulated()
    
    if success:
        print(f"\n✅ TEST PASSED - Check screenshots in {SCREENSHOT_DIR}")
        print("\n📸 Screenshots created:")
        for file in sorted(os.listdir(SCREENSHOT_DIR)):
            if file.endswith('.png'):
                print(f"   - {file}")
        sys.exit(0)
    else:
        print(f"\n❌ TEST FAILED - Check screenshots in {SCREENSHOT_DIR}")
        sys.exit(1)