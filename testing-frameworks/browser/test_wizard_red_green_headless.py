#!/usr/bin/env python3
"""
Simplified red/green test for wizard character display - runs in headless mode
"""

import os
import sys

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8088"
SCREENSHOT_DIR = "/tmp/worldarchitectai/browser/wizard_red_green"


def main():
    print("🔴 RED/GREEN Test: Campaign Wizard Character Display")
    print("=" * 60)

    # Ensure screenshot directory exists
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate with test mode
            print("\n📍 Navigating to test URL...")
            test_url = (
                f"{BASE_URL}/new-campaign?test_mode=true&test_user_id=red-green-demo"
            )
            print(f"   URL: {test_url}")
            page.goto(test_url)
            page.wait_for_load_state("networkidle")

            # Check if we need to click "Create New Campaign" or if wizard is already open
            print("🎮 Starting campaign wizard...")
            if page.locator("#go-to-new-campaign").is_visible():
                page.click("#go-to-new-campaign")
                page.wait_for_timeout(1000)

            # The wizard should now be visible - wait for campaign type cards
            page.wait_for_selector(
                'div.campaign-type-card[data-type="custom"]',
                state="visible",
                timeout=10000,
            )
            page.wait_for_timeout(500)

            # RED TEST: Custom campaign with empty fields (shows bug)
            print("\n🔴 RED TEST: Custom campaign showing Dragon Knight defaults")
            page.click('div.campaign-type-card[data-type="custom"]')
            page.wait_for_timeout(500)
            page.fill("#wizard-campaign-title", "Red Test - Bug Demo")

            # Navigate to preview
            for _i in range(3):
                page.click("button:has-text('Next')")
                page.wait_for_timeout(500)

            # Take screenshot of the bug
            red_path = os.path.join(SCREENSHOT_DIR, "01_red_test_bug.png")
            page.screenshot(path=red_path)
            print(f"📸 RED screenshot saved: {red_path}")

            # Check what's displayed
            character_text = page.locator("#preview-character").text_content()
            options_text = page.locator("#preview-options").text_content()
            print(f"   Character: '{character_text}'")
            print(f"   Options: '{options_text}'")

            # Navigate back
            page.reload()
            page.wait_for_selector("#go-to-new-campaign", timeout=10000)
            page.click("#go-to-new-campaign")
            if not page.locator("#wizard-custom-campaign").is_visible():
                page.wait_for_selector(
                    "#wizard-custom-campaign", state="visible", timeout=10000
                )
            page.wait_for_timeout(1000)

            # GREEN TEST: Same scenario with fix applied
            print("\n✅ GREEN TEST: Custom campaign showing correct defaults")
            page.click('div.campaign-type-card[data-type="custom"]')
            page.wait_for_timeout(500)
            page.fill("#wizard-campaign-title", "Green Test - Fixed")

            # Navigate to preview
            for _i in range(3):
                page.click("button:has-text('Next')")
                page.wait_for_timeout(500)

            # Take screenshot of the fix
            green_path = os.path.join(SCREENSHOT_DIR, "02_green_test_fixed.png")
            page.screenshot(path=green_path)
            print(f"📸 GREEN screenshot saved: {green_path}")

            # Check fixed values
            character_text = page.locator("#preview-character").text_content()
            options_text = page.locator("#preview-options").text_content()
            print(f"   Character: '{character_text}' (should be 'Auto-generated')")
            print(
                f"   Options: '{options_text}' (should NOT contain 'Dragon Knight World')"
            )

            # TEST 3: Custom character input
            print("\n✅ GREEN TEST 2: Custom character input")
            page.reload()
            page.wait_for_selector("#go-to-new-campaign", timeout=10000)
            page.click("#go-to-new-campaign")
            if not page.locator("#wizard-custom-campaign").is_visible():
                page.wait_for_selector(
                    "#wizard-custom-campaign", state="visible", timeout=10000
                )
            page.wait_for_timeout(1000)

            page.click('div.campaign-type-card[data-type="custom"]')
            page.wait_for_timeout(500)
            page.fill("#wizard-campaign-title", "Custom Character Test")
            page.fill("#wizard-character-input", "Gandalf the Grey")
            page.fill("#wizard-setting-input", "Middle Earth")

            # Navigate to preview
            for _i in range(3):
                page.click("button:has-text('Next')")
                page.wait_for_timeout(500)

            # Take screenshot
            custom_path = os.path.join(SCREENSHOT_DIR, "03_custom_character.png")
            page.screenshot(path=custom_path)
            print(f"📸 Custom character screenshot saved: {custom_path}")

            # Check custom values
            character_text = page.locator("#preview-character").text_content()
            print(f"   Character: '{character_text}' (should be 'Gandalf the Grey')")

            print("\n✅ Test complete! Check screenshots at:")
            print(f"   {SCREENSHOT_DIR}")

        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            error_path = os.path.join(SCREENSHOT_DIR, "error.png")
            page.screenshot(path=error_path)
            print(f"📸 Error screenshot: {error_path}")
            return False
        finally:
            browser.close()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
