#!/usr/bin/env python3
"""
Direct browser test to reproduce JSON bug quickly.
"""

import os
import time
from playwright.sync_api import sync_playwright

# Configuration
BASE_URL = "http://localhost:6006"
SCREENSHOT_DIR = "/tmp/worldarchitectai/browser"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def run_json_bug_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Go to homepage with test mode
            print("1. Opening homepage...")
            page.goto(f"{BASE_URL}?test_mode=true&test_user_id=json-bug-test")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Take screenshot
            page.screenshot(path=f"{SCREENSHOT_DIR}/json_direct_01_home.png")
            
            # Click New Campaign
            print("2. Creating campaign...")
            new_btn = page.locator("button:has-text('New Campaign')").first
            new_btn.click()
            time.sleep(1)
            
            page.screenshot(path=f"{SCREENSHOT_DIR}/json_direct_02_form.png")
            
            # Fill form
            print("3. Filling form...")
            page.locator("#campaignTitle").fill("JSON Bug Direct Test")
            page.locator("#campaignPremise").fill("A brave knight in a land of dragons needs to choose between killing an evil dragon or joining its side.")
            page.locator('input[value="defaultWorld"]').click()
            
            page.screenshot(path=f"{SCREENSHOT_DIR}/json_direct_03_filled.png")
            
            # Submit
            print("4. Submitting...")
            page.locator('button[type="submit"]').click()
            
            # Wait for game to load
            print("5. Waiting for campaign...")
            page.wait_for_selector("#storyLog", timeout=30000)
            time.sleep(3)
            
            page.screenshot(path=f"{SCREENSHOT_DIR}/json_direct_04_created.png")
            
            # Type "2" to trigger bug
            print("6. Triggering JSON bug with option 2...")
            input_field = page.locator("#userInput")
            input_field.fill("2")
            input_field.press("Enter")
            
            # Wait for response
            print("7. Waiting for AI response...")
            time.sleep(15)  # Give AI time to respond
            
            # Take final screenshot
            page.screenshot(path=f"{SCREENSHOT_DIR}/json_direct_05_BUG_VISIBLE.png")
            
            # Get the displayed text
            messages = page.locator(".message-bubble").all()
            if len(messages) > 1:
                last_msg = messages[-1].inner_text()
                print("\n🚨 LAST MESSAGE DISPLAYED:")
                print(last_msg[:500])
                print("...")
                
                # Save full text
                with open("/tmp/json_bug_displayed.txt", "w") as f:
                    f.write(last_msg)
                print("\n💾 Full text saved to /tmp/json_bug_displayed.txt")
                
                if "{" in last_msg and "narrative" in last_msg:
                    print("\n✅ JSON BUG REPRODUCED!")
                    return True
            
            return False
            
        finally:
            browser.close()

if __name__ == "__main__":
    print("🚀 Direct JSON Bug Test")
    print("=" * 50)
    
    # Check if server is running
    import requests
    try:
        r = requests.get(BASE_URL, timeout=2)
        print("✅ Server is running")
    except:
        print("❌ Server not running! Start with:")
        print("   TESTING=true PORT=6006 python mvp_site/main.py serve")
        exit(1)
    
    success = run_json_bug_test()
    
    if success:
        print("\n✅ Bug reproduced! Check:")
        print(f"   - Screenshot: {SCREENSHOT_DIR}/json_direct_05_BUG_VISIBLE.png")
        print("   - Text file: /tmp/json_bug_displayed.txt")
    else:
        print("\n❌ Failed to reproduce bug")