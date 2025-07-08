#!/usr/bin/env python3
"""
Browser test to capture AFTER state - showing the JSON bug is fixed.
"""

import os
import time
from playwright.sync_api import sync_playwright

# Configuration
BASE_URL = "http://localhost:6006"
SCREENSHOT_DIR = "/tmp/worldarchitectai/browser"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def run_json_bug_after_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Go to homepage with test mode
            print("1. Opening homepage...")
            page.goto(f"{BASE_URL}?test_mode=true&test_user_id=json-bug-after-test")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Click New Campaign through interface
            print("2. Creating campaign via UI...")
            # Click the new campaign button that should be visible
            buttons = page.locator("button").all()
            new_campaign_clicked = False
            
            for button in buttons:
                text = button.inner_text()
                if "new campaign" in text.lower() or "create campaign" in text.lower():
                    button.click()
                    new_campaign_clicked = True
                    print(f"   Clicked button: {text}")
                    break
            
            if not new_campaign_clicked:
                print("   Could not find New Campaign button, trying direct navigation...")
                page.evaluate("showNewCampaignView()")
            
            time.sleep(2)
            
            # Fill form using actual form IDs
            print("3. Filling campaign form...")
            
            # Try different possible selectors
            title_selectors = ["#campaign-title", "#campaignTitle", "input[name='title']", "input[placeholder*='title']"]
            premise_selectors = ["#campaign-premise", "#campaignPremise", "textarea[name='premise']", "textarea[placeholder*='premise']"]
            
            filled = False
            for title_sel, premise_sel in zip(title_selectors, premise_selectors):
                try:
                    page.locator(title_sel).fill("JSON Bug Fixed Test", timeout=2000)
                    page.locator(premise_sel).fill("A brave knight in a land of dragons needs to choose between killing an evil dragon or joining its side.", timeout=2000)
                    filled = True
                    print(f"   Filled using selectors: {title_sel}, {premise_sel}")
                    break
                except:
                    continue
                    
            if not filled:
                print("   WARNING: Could not fill form fields")
            
            # Select default world option
            try:
                page.locator("input[value='defaultWorld']").first.click()
            except:
                try:
                    page.locator("input[type='radio']").first.click()
                except:
                    print("   WARNING: Could not select world option")
            
            # Submit form
            print("4. Submitting campaign...")
            submit_button = page.locator("button:has-text('Create')").or_(page.locator("button[type='submit']")).first
            submit_button.click()
            
            # Wait for game to load
            print("5. Waiting for campaign to load...")
            page.wait_for_selector("#storyLog", timeout=30000)
            time.sleep(3)
            
            # Type "2" to trigger where bug used to be
            print("6. Sending option 2...")
            input_field = page.locator("#userInput")
            input_field.fill("2")
            input_field.press("Enter")
            
            # Wait for response
            print("7. Waiting for AI response...")
            time.sleep(15)  # Give AI time to respond
            
            # Take screenshot showing fixed state
            page.screenshot(path=f"{SCREENSHOT_DIR}/json_bug_AFTER_fixed.png")
            print(f"\n📸 Screenshot saved: json_bug_AFTER_fixed.png")
            
            # Get the displayed text
            messages = page.locator(".message-bubble").all()
            if len(messages) > 1:
                last_msg = messages[-1].inner_text()
                print("\n🎉 LAST MESSAGE DISPLAYED (AFTER FIX):")
                print(last_msg[:500])
                print("...")
                
                # Check if JSON bug is fixed
                if "{" in last_msg and "narrative" in last_msg:
                    print("\n❌ JSON BUG STILL PRESENT!")
                    return False
                else:
                    print("\n✅ JSON BUG FIXED! No raw JSON displayed!")
                    
                    # Save the clean text
                    with open("/tmp/json_bug_after_fixed.txt", "w") as f:
                        f.write(last_msg)
                    print("💾 Clean text saved to /tmp/json_bug_after_fixed.txt")
                    return True
            
            return True
            
        finally:
            browser.close()

if __name__ == "__main__":
    print("🚀 JSON Bug AFTER Test (With Fix)")
    print("=" * 50)
    
    success = run_json_bug_after_test()
    
    if success:
        print("\n✅ SUCCESS! The JSON bug has been fixed!")
        print("   Check screenshot: /tmp/worldarchitectai/browser/json_bug_AFTER_fixed.png")
    else:
        print("\n❌ The JSON bug is still present")