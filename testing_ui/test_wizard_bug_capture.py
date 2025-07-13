#!/usr/bin/env python3
"""
Capture the campaign wizard bug - RED test showing Dragon Knight defaults in custom campaigns
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8088"
SCREENSHOT_DIR = "/tmp/worldarchitectai/browser/wizard_red_green"

def main():
    print("✅ Capturing Campaign Wizard Fix (After Fix)")
    print("=" * 60)
    
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate with test mode
            print("\n📍 Navigating to campaign wizard...")
            page.goto(f"{BASE_URL}/new-campaign?test_mode=true&test_user_id=bug-demo")
            page.wait_for_load_state("networkidle")
            
            # Select custom campaign
            print("🎯 Selecting custom campaign type...")
            page.click('div.campaign-type-card[data-type="custom"]')
            page.wait_for_timeout(500)
            
            # Fill title and check default world (this triggers the bug)
            page.fill("#wizard-campaign-title", "Bug Demo - Custom Campaign")
            page.check("#wizard-default-world")
            print("✓ Filled form with custom campaign + default world checkbox")
            
            # Navigate to preview (step 4)
            print("📍 Navigating to preview step...")
            for i in range(3):
                page.click("button:has-text('Next')")
                page.wait_for_timeout(500)
            
            # Capture the fix
            green_path = os.path.join(SCREENSHOT_DIR, "02_GREEN_FIXED_default_world.png")
            page.screenshot(path=green_path)
            print(f"\n✅ GREEN SCREENSHOT: {green_path}")
            
            # Show what's displayed
            character_text = page.locator("#preview-character").text_content()
            options_text = page.locator("#preview-options").text_content()
            description_text = page.locator("#preview-description").text_content()
            
            print(f"\n✅ GREEN TEST - FIXED:")
            print(f"   Character: '{character_text}'")
            print(f"   Description: '{description_text}'") 
            print(f"   Options: '{options_text}'")
            
            if "Dragon Knight World" in options_text:
                print(f"\n   ❌ Still buggy: Shows 'Dragon Knight World' for custom campaign!")
            else:
                print(f"\n   ✅ FIXED: Shows '{options_text}' instead of 'Dragon Knight World'!")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "error.png"))
        finally:
            browser.close()

if __name__ == "__main__":
    main()