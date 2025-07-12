#!/usr/bin/env python3
"""Simple test to verify structured fields are displayed in game view."""

import os
import sys
import time
from playwright.sync_api import sync_playwright

# Setup
os.environ['USE_MOCK_GEMINI'] = 'true'
os.environ['USE_MOCK_FIREBASE'] = 'true'
os.environ['TESTING'] = 'true'

BASE_URL = "http://localhost:6006"
CAMPAIGN_ID = "browser_test_campaign_123"
SCREENSHOT_DIR = "/tmp/worldarchitectai/browser"
TEST_USER_ID = "browser-test-user"

def main():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate directly to game view with test mode
        test_url = f"{BASE_URL}/game/{CAMPAIGN_ID}?test_mode=true&test_user_id={TEST_USER_ID}"
        print(f"🌐 Navigating to: {test_url}")
        
        page.goto(test_url, wait_until="networkidle")
        page.wait_for_timeout(5000)
        
        # Take screenshot
        screenshot_path = f"{SCREENSHOT_DIR}/direct_game_view.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Screenshot saved: {screenshot_path}")
        
        # Check for game view
        if page.is_visible("#game-view"):
            print("✅ Game view is visible")
            
            # Check for structured fields
            fields = {
                'session_header': ['.session-header', '[data-field="session_header"]'],
                'narrative': ['.narrative-text', '[data-field="narrative"]', '#story-content'],
                'planning_block': ['.planning-block', '[data-field="planning_block"]'],
                'dice_rolls': ['.dice-rolls', '[data-field="dice_rolls"]'],
                'resources': ['.resources', '[data-field="resources"]'],
            }
            
            for field, selectors in fields.items():
                found = False
                for selector in selectors:
                    if page.locator(selector).count() > 0:
                        print(f"✅ Found {field}: {selector}")
                        found = True
                        break
                if not found:
                    print(f"❌ Missing {field}")
        else:
            print("❌ Game view not found")
            
        # Check console errors
        console_messages = []
        page.on("console", lambda msg: console_messages.append(msg))
        
        browser.close()

if __name__ == "__main__":
    main()