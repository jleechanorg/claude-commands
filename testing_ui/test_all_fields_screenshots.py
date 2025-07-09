#!/usr/bin/env python3
"""
Comprehensive test to capture screenshots for EVERY field in the schema.
This test will trigger all possible fields and capture individual screenshots.
"""
import os
import time
import json
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8080"
SCREENSHOT_DIR = "/tmp/all_fields_screenshots"
TEST_HEADERS = {
    "X-Test-Bypass-Auth": "true",
    "X-Test-User-ID": "test-all-fields",
    "Content-Type": "application/json"
}

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path

def test_all_fields_screenshots():
    """Test and screenshot every single field from the schema"""
    ensure_dir(SCREENSHOT_DIR)
    print(f"📸 Screenshots will be saved to: {SCREENSHOT_DIR}\n")
    
    # Step 1: Create campaign via API
    print("1️⃣ Creating test campaign...")
    campaign_resp = requests.post(
        f"{BASE_URL}/api/campaigns",
        headers=TEST_HEADERS,
        json={
            "title": "All Fields Test Campaign",
            "prompt": "Test campaign to demonstrate all structured fields",
            "campaign_type": "custom"
        }
    )
    
    if campaign_resp.status_code != 201:
        print(f"❌ Failed to create campaign: {campaign_resp.text}")
        return False
        
    campaign_id = campaign_resp.json()["campaign_id"]
    print(f"✅ Created campaign: {campaign_id}")
    
    # Step 2: Send CHARACTER MODE interaction to get narrative fields
    print("\n2️⃣ Testing CHARACTER MODE fields...")
    char_resp = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interaction",
        headers=TEST_HEADERS,
        json={
            "input": "I enter the dungeon and look around carefully. I want to check for traps and enemies.",
            "mode": "character",
            "debug_mode": True
        }
    )
    
    if char_resp.status_code == 200:
        char_data = char_resp.json()
        print("✅ Character mode response received")
        
        # Print what fields we got
        print("\n📋 Character Mode Fields Present:")
        for field in ['narrative', 'session_header', 'planning_block', 'dice_rolls', 
                     'resources', 'entities_mentioned', 'location_confirmed', 
                     'state_updates', 'debug_info']:
            if field in char_data:
                print(f"  ✅ {field}")
            else:
                print(f"  ❌ {field} - MISSING")
    
    # Step 3: Send GOD MODE interaction to get god_mode_response
    print("\n3️⃣ Testing GOD MODE fields...")
    god_resp = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interaction",
        headers=TEST_HEADERS,
        json={
            "input": "/god show me all NPCs and their current status",
            "mode": "god",
            "debug_mode": True
        }
    )
    
    if god_resp.status_code == 200:
        god_data = god_resp.json()
        print("✅ God mode response received")
        if 'god_mode_response' in god_data or 'response' in god_data:
            print("  ✅ god_mode_response field present")
    
    # Step 4: Use Playwright to capture UI screenshots
    print("\n4️⃣ Capturing UI screenshots...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser for debugging
        page = browser.new_page()
        
        try:
            # Navigate to campaign
            print(f"   Navigating to campaign {campaign_id}...")
            page.goto(f"{BASE_URL}/campaign/{campaign_id}?test_mode=true&test_user_id=test-all-fields")
            page.wait_for_load_state('networkidle')
            time.sleep(3)
            
            # Take full page screenshot first
            page.screenshot(path=f"{SCREENSHOT_DIR}/00_full_page.png", full_page=True)
            print("   ✅ Full page screenshot captured")
            
            # Now capture each field individually
            field_selectors = {
                # Always visible fields
                'narrative': '.story-entry:last-child',  # Last AI response
                'session_header': '.session-header',
                'planning_block': '.planning-block',
                'dice_rolls': '.dice-rolls',
                'resources': '.resources',
                
                # Fields that might be in debug sections
                'entities_mentioned': '.entities',
                'location_confirmed': '.location',
                'state_updates': '.state-updates',
                'debug_info': '.debug-info',
                'dm_notes': '.dm-notes',
                'state_rationale': '.state-rationale',
                
                # God mode specific
                'god_mode_response': '.god-mode-response'
            }
            
            # Try to find and screenshot each field
            print("\n📸 Capturing individual field screenshots:")
            found_count = 0
            
            for field_name, selector in field_selectors.items():
                elements = page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    # Take screenshot of the first matching element
                    element = elements[0]
                    element.screenshot(path=f"{SCREENSHOT_DIR}/{field_name}.png")
                    print(f"   ✅ {field_name} - Screenshot saved")
                    found_count += 1
                else:
                    # Try alternative selectors or content search
                    alt_found = False
                    
                    # Search by content patterns
                    if field_name == 'session_header' and '[SESSION_HEADER]' in page.content():
                        print(f"   ⚠️  {field_name} - Found in content but no dedicated element")
                    elif field_name == 'planning_block' and '--- PLANNING BLOCK ---' in page.content():
                        print(f"   ⚠️  {field_name} - Found in content but no dedicated element")
                    elif field_name == 'dice_rolls' and '🎲' in page.content():
                        print(f"   ⚠️  {field_name} - Dice emoji found but no dedicated element")
                    elif field_name == 'resources' and '📊' in page.content():
                        print(f"   ⚠️  {field_name} - Resources emoji found but no dedicated element")
                    else:
                        print(f"   ❌ {field_name} - Not found in UI")
            
            # Check if we need to enable debug mode
            if found_count < 8:
                print("\n5️⃣ Enabling debug mode to see more fields...")
                debug_toggle = page.query_selector('#debug-toggle')
                if debug_toggle and not page.is_checked('#debug-toggle'):
                    page.click('#debug-toggle')
                    time.sleep(2)
                    
                    # Take another screenshot with debug mode
                    page.screenshot(path=f"{SCREENSHOT_DIR}/00_full_page_debug.png", full_page=True)
                    print("   ✅ Debug mode screenshot captured")
                    
                    # Try to capture debug-only fields again
                    for field_name in ['state_updates', 'debug_info', 'dm_notes', 'state_rationale']:
                        selector = field_selectors.get(field_name)
                        if selector:
                            elements = page.query_selector_all(selector)
                            if elements and len(elements) > 0:
                                elements[0].screenshot(path=f"{SCREENSHOT_DIR}/{field_name}_debug.png")
                                print(f"   ✅ {field_name} (debug mode) - Screenshot saved")
            
            # Try to trigger god mode
            print("\n6️⃣ Attempting to capture god mode response...")
            user_input = page.query_selector('#user-input')
            if user_input:
                # Switch to god mode
                god_mode_radio = page.query_selector('input[value="god"]')
                if god_mode_radio:
                    god_mode_radio.click()
                    time.sleep(0.5)
                
                # Submit god mode command
                user_input.fill("/god show all game state")
                send_button = page.query_selector('#send-button')
                if send_button:
                    send_button.click()
                    time.sleep(5)  # Wait for response
                    
                    # Screenshot god mode response
                    page.screenshot(path=f"{SCREENSHOT_DIR}/00_god_mode_response.png", full_page=True)
                    print("   ✅ God mode response screenshot captured")
            
            # Final summary
            print("\n" + "="*60)
            print(f"📊 Screenshot Summary:")
            print(f"   - Total screenshots saved: {len(os.listdir(SCREENSHOT_DIR))}")
            print(f"   - Location: {SCREENSHOT_DIR}")
            print("\n📋 Schema Field Coverage:")
            
            # Check API response for actual field presence
            all_fields = [
                'narrative', 'session_header', 'planning_block', 'dice_rolls',
                'resources', 'god_mode_response', 'entities_mentioned',
                'location_confirmed', 'state_updates', 'debug_info'
            ]
            
            for field in all_fields:
                screenshot_exists = any(f.startswith(field) for f in os.listdir(SCREENSHOT_DIR))
                if screenshot_exists:
                    print(f"   ✅ {field} - Screenshot captured")
                else:
                    print(f"   ⚠️  {field} - No dedicated screenshot (may be in full page)")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
            raise
        finally:
            input("\n🔍 Press Enter to close browser and finish...")
            browser.close()

if __name__ == "__main__":
    print("=== Comprehensive Field Screenshot Test ===")
    print("This test will capture screenshots for EVERY field in the schema")
    print(f"Server should be running at {BASE_URL}\n")
    
    success = test_all_fields_screenshots()
    exit(0 if success else 1)