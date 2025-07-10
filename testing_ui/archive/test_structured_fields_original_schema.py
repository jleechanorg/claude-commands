#!/usr/bin/env python3
"""
Layer 3 Browser Test - Tests structured fields with original schema design.
This test expects fields to follow the game_state_instruction.md schema exactly.
"""
import os
import sys
import time
import json
from playwright.sync_api import sync_playwright
from unittest.mock import patch, MagicMock

# Configuration
BASE_URL = "http://localhost:8080"
SCREENSHOT_DIR = "/tmp/structured_fields_layer3"

def test_structured_fields_original_schema():
    """Test that structured fields follow the original schema from game_state_instruction.md"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    print(f"Screenshots will be saved to: {SCREENSHOT_DIR}")
    
    # Expected response structure from game_state_instruction.md
    expected_response = {
        "narrative": "You swing your sword at the goblin! The blade cuts through the air...",
        "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Ches 20, 10:00\nLocation: Goblin Cave\nStatus: Lvl 2 Fighter | HP: 15/18",
        "planning_block": "--- PLANNING BLOCK ---\nWhat would you like to do next?\n1. Attack again\n2. Defend\n3. Retreat",
        "dice_rolls": ["Attack roll: 1d20+5 = 15+5 = 20 (Hit!)", "Damage: 1d8+3 = 5+3 = 8"],
        "resources": "HD: 2/2, Second Wind: 0/1, Action Surge: 1/1",
        "entities_mentioned": ["goblin"],
        "location_confirmed": "Goblin Cave",
        "state_updates": {
            "npc_data": {
                "goblin_1": {"hp_current": 3}
            }
        },
        "debug_info": {
            "dm_notes": ["Goblin is wounded"],
            "state_rationale": "Reduced goblin HP by 8"
        }
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Intercept API responses to verify structure
        api_responses = []
        
        def handle_response(response):
            if '/api/campaigns' in response.url and '/interaction' in response.url:
                try:
                    data = response.json()
                    api_responses.append(data)
                    print(f"\n📡 Intercepted API Response:")
                    print(f"   Keys: {list(data.keys())}")
                except:
                    pass
        
        page.on('response', handle_response)
        
        try:
            # 1. Navigate with test mode
            print("\n1. Navigating to app with test mode...")
            page.goto(f"{BASE_URL}/?test_mode=true&test_user_id=test-layer3")
            page.wait_for_load_state('networkidle')
            page.screenshot(path=f"{SCREENSHOT_DIR}/01_landing.png")
            
            # 2. Create a test campaign quickly
            print("2. Creating test campaign...")
            # Check if we're already in a campaign
            if not page.query_selector('#user-input'):
                # Need to create campaign
                if page.query_selector('text="Start New Campaign"'):
                    page.click('text="Start New Campaign"')
                    time.sleep(1)
                    
                    # Fill minimal required fields
                    title_input = page.query_selector('#campaign-title')
                    if title_input:
                        title_input.fill('Layer 3 Schema Test')
                    
                    # Submit campaign creation
                    create_btn = page.query_selector('button:has-text("Create")')
                    if create_btn:
                        create_btn.click()
                    else:
                        # Try any submit button
                        page.click('button[type="submit"]')
                    
                    # Wait for game view
                    page.wait_for_selector('#user-input', timeout=30000)
            
            # 3. Enable debug mode
            print("3. Enabling debug mode...")
            debug_toggle = page.query_selector('#debug-toggle')
            if debug_toggle and not page.is_checked('#debug-toggle'):
                page.click('#debug-toggle')
                time.sleep(0.5)
            
            # 4. Submit interaction
            print("4. Submitting test interaction...")
            page.fill('#user-input', 'I attack the goblin with my sword!')
            page.screenshot(path=f"{SCREENSHOT_DIR}/02_before_submit.png")
            page.click('button#send-button')
            
            # 5. Wait for response
            print("5. Waiting for AI response...")
            page.wait_for_selector('.ai-message, .story-entry:has-text("Scene")', timeout=30000)
            time.sleep(3)  # Let structured fields render
            
            page.screenshot(path=f"{SCREENSHOT_DIR}/03_after_response.png", full_page=True)
            
            # 6. Verify API response structure matches schema
            print("\n6. Verifying API response structure...")
            if api_responses:
                response = api_responses[-1]
                
                # Check for schema compliance
                schema_fields = {
                    'narrative': 'Main story text field',
                    'session_header': 'Session header with timestamp/location/status',
                    'planning_block': 'Planning block with options',
                    'dice_rolls': 'List of dice roll strings',
                    'resources': 'Resource string (HD, spells, etc)',
                    'entities_mentioned': 'List of mentioned entities',
                    'location_confirmed': 'Current location',
                    'state_updates': 'State change object',
                    'debug_info': 'Debug information object'
                }
                
                print("\n📋 Schema Compliance Check:")
                compliance_score = 0
                for field, description in schema_fields.items():
                    if field in response:
                        print(f"   ✅ {field}: Present")
                        compliance_score += 1
                    else:
                        print(f"   ❌ {field}: MISSING - {description}")
                
                # Check for non-schema fields
                non_schema_fields = set(response.keys()) - set(schema_fields.keys())
                if non_schema_fields:
                    print(f"\n   ⚠️  Non-schema fields present: {non_schema_fields}")
                
                print(f"\n   Schema Compliance: {compliance_score}/{len(schema_fields)} fields")
                
                # Detailed structure check
                if 'debug_info' in response:
                    print("\n   Debug info structure:")
                    for key in ['dm_notes', 'dice_rolls', 'resources', 'state_rationale']:
                        if key in response['debug_info']:
                            print(f"     ✅ debug_info.{key}: Present")
                        else:
                            print(f"     ❌ debug_info.{key}: MISSING")
            
            # 7. Verify UI displays structured fields
            print("\n7. Checking UI display of structured fields...")
            ui_checks = {
                '.session-header': 'Session Header',
                '.planning-block': 'Planning Block',
                '.dice-rolls': 'Dice Rolls',
                '.resources': 'Resources',
                '.entities': 'Entities',
                '.location': 'Location',
                '.state-updates': 'State Updates',
                '.debug-info': 'Debug Info'
            }
            
            ui_score = 0
            for selector, name in ui_checks.items():
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"   ✅ {name}: Found ({len(elements)} elements)")
                    ui_score += 1
                    # Take close-up screenshot of first element
                    if elements[0]:
                        elements[0].screenshot(path=f"{SCREENSHOT_DIR}/element_{selector.replace('.', '')}.png")
                else:
                    print(f"   ❌ {name}: NOT FOUND")
            
            print(f"\n   UI Display Score: {ui_score}/{len(ui_checks)} elements")
            
            # 8. Final assessment
            print("\n" + "="*50)
            if compliance_score == len(schema_fields) and ui_score >= 4:
                print("✅ TEST PASSED: Schema compliance and UI display working!")
                return True
            else:
                print("❌ TEST FAILED: Schema non-compliance or missing UI elements")
                print("\nExpected all fields from game_state_instruction.md schema")
                print("Backend should send fields at root level, not nested")
                return False
            
        except Exception as e:
            print(f"\n❌ Test error: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    print("=== Layer 3 Browser Test: Original Schema Compliance ===")
    print("This test verifies structured fields follow game_state_instruction.md")
    print(f"Server should be running at {BASE_URL}\n")
    
    success = test_structured_fields_original_schema()
    sys.exit(0 if success else 1)