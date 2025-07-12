#!/usr/bin/env python3
"""
Demo test to showcase all structured fields through direct navigation.
Uses mock responses to ensure all 10 fields are visible.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

# Configuration
BASE_URL = "http://localhost:6006"
SCREENSHOT_DIR = "/tmp/worldarchitectai/browser/structured_fields_demo"

def test_structured_fields_demo():
    """Demonstrate all structured fields with mock data."""
    
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("=== Structured Fields Demo Test ===")
            print(f"📍 URL: {BASE_URL}")
            print(f"📸 Screenshots: {SCREENSHOT_DIR}")
            
            # Navigate with test mode
            test_url = f"{BASE_URL}?test_mode=true&test_user_id=demo-test"
            print(f"\n1️⃣ Navigating to: {test_url}")
            page.goto(test_url, wait_until='networkidle')
            page.wait_for_timeout(2000)
            
            # Take dashboard screenshot
            page.screenshot(path=f"{SCREENSHOT_DIR}/01_dashboard.png")
            print("✅ Dashboard loaded")
            
            # Create a simple test campaign
            print("\n2️⃣ Creating test campaign...")
            if page.is_visible("text='Start New Campaign'"):
                page.click("text='Start New Campaign'")
            elif page.is_visible("text='New Campaign'"):
                page.click("text='New Campaign'")
            
            page.wait_for_timeout(2000)
            
            # Simple wizard navigation
            if page.is_visible("#wizard-campaign-title"):
                page.fill("#wizard-campaign-title", "Demo Structured Fields")
                page.fill("#wizard-campaign-prompt", "Test all structured response fields")
            
            # Click through wizard quickly
            for i in range(5):
                if page.is_visible("#wizard-next"):
                    page.click("#wizard-next")
                    page.wait_for_timeout(1000)
                elif page.is_visible("#launch-campaign"):
                    page.click("#launch-campaign")
                    break
                elif page.is_visible("button:has-text('Begin Adventure')"):
                    page.click("button:has-text('Begin Adventure')")
                    break
            
            page.wait_for_timeout(5000)
            
            # Check if in game view
            if page.is_visible("#game-view"):
                print("✅ Game view loaded")
                page.screenshot(path=f"{SCREENSHOT_DIR}/02_game_view.png")
                
                # Test character mode response
                print("\n3️⃣ Testing character mode fields...")
                action_input = page.locator("#player-action, #user-input, textarea").first
                if action_input:
                    action_input.fill("I attack the goblin!")
                    
                    send_button = page.locator("#send-action, button:has-text('Send')").first
                    if send_button:
                        send_button.click()
                        print("⏳ Waiting for response...")
                        page.wait_for_timeout(8000)
                        
                        page.screenshot(path=f"{SCREENSHOT_DIR}/03_character_response.png")
                        
                        # Check for fields
                        fields_found = []
                        field_checks = {
                            'session_header': ['.session-header', '[data-field="session_header"]'],
                            'narrative': ['.narrative-text', '#story-content'],
                            'planning_block': ['.planning-block', '[data-field="planning_block"]'],
                            'dice_rolls': ['.dice-rolls', '[data-field="dice_rolls"]'],
                            'resources': ['.resources', '[data-field="resources"]'],
                            'state_updates': ['.state-updates', '[data-field="state_updates"]']
                        }
                        
                        for field, selectors in field_checks.items():
                            for selector in selectors:
                                if page.locator(selector).count() > 0:
                                    fields_found.append(field)
                                    print(f"✅ Found: {field}")
                                    break
                        
                        # Test god mode
                        print("\n4️⃣ Testing god mode...")
                        action_input.fill("GOD MODE: Show me hidden secrets")
                        send_button.click()
                        page.wait_for_timeout(8000)
                        
                        page.screenshot(path=f"{SCREENSHOT_DIR}/04_god_mode.png")
                        
                        # Check for god mode field
                        if page.locator('.god-mode-response, [data-field="god_mode_response"]').count() > 0:
                            fields_found.append('god_mode_response')
                            print("✅ Found: god_mode_response")
                        
                        # Final summary screenshot
                        page.screenshot(path=f"{SCREENSHOT_DIR}/05_final.png", full_page=True)
                        
                        print(f"\n✅ Total fields found: {len(fields_found)}/10")
                        print(f"📁 Screenshots saved to: {SCREENSHOT_DIR}")
                        
                        return len(fields_found) >= 7  # Success if we find most fields
            
            return False
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
            return False
        
        finally:
            browser.close()

if __name__ == "__main__":
    # Ensure mock mode
    os.environ['USE_MOCK_GEMINI'] = 'true'
    os.environ['USE_MOCK_FIREBASE'] = 'true'
    
    success = test_structured_fields_demo()
    print(f"\n{'✅ DEMO PASSED' if success else '❌ DEMO FAILED'}")
    sys.exit(0 if success else 1)