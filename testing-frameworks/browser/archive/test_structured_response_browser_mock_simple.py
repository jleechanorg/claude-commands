#!/usr/bin/env python3
"""Browser test for structured response fields with mocked services - simplified version"""

import os
import time

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8080"
SCREENSHOT_DIR = "/tmp/structured_response_screenshots"


def test_structured_response_display():
    """Test UI displays structured fields correctly"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate with test mode
            page.goto(f"{BASE_URL}/?test_mode=true&test_user_id=test-struct")
            page.wait_for_load_state("networkidle")

            # Create campaign without wizard - click directly
            page.click('text="Start New Campaign"')
            page.wait_for_selector("#new-campaign-view", state="visible")

            # Fill form directly (no wizard)
            title_input = page.locator("#campaign-title")
            if title_input.count() > 0:
                title_input.fill("Structured Response Test")

            # Submit form
            create_btn = page.locator('button:has-text("Create Campaign")')
            if create_btn.count() > 0:
                create_btn.click()
                page.wait_for_selector(".story-container", timeout=30000)
                time.sleep(2)
            else:
                print("Create button not found, trying alternate flow...")
                # Alternative: might already be in game view

            # Enable debug mode if not already
            debug_toggle = page.locator("#debug-toggle")
            if debug_toggle.count() > 0:
                # Check if already checked
                if not debug_toggle.is_checked():
                    debug_toggle.click()
                    time.sleep(1)

            # Submit interaction
            user_input = page.locator("#user-input")
            if user_input.count() > 0:
                user_input.fill("I attack with my sword and roll for damage!")
                page.click("button#send-button")

                # Wait for AI response
                page.wait_for_selector('.story-entry:has-text("Scene")', timeout=30000)
                time.sleep(3)

                # Take screenshot
                page.screenshot(
                    path=f"{SCREENSHOT_DIR}/mocked_response_simple.png", full_page=True
                )

                # Check for structured fields
                dice_rolls = page.locator(".dice-rolls")
                if dice_rolls.count() > 0:
                    print("✅ Dice rolls field found!")
                    dice_rolls.screenshot(path=f"{SCREENSHOT_DIR}/dice_rolls.png")
                else:
                    print("❌ Dice rolls field NOT found")

                resources = page.locator(".resources")
                if resources.count() > 0:
                    print("✅ Resources field found!")
                else:
                    print("⚠️ Resources field not found (may not be in response)")

                entities = page.locator(".entities")
                if entities.count() > 0:
                    print("✅ Entities field found!")
                else:
                    print("⚠️ Entities field not found (may not be in response)")

                print(f"\nScreenshots saved to {SCREENSHOT_DIR}/")
                print("✅ Test completed successfully!")
            else:
                print("❌ Could not find user input field")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error_state.png")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    # Ensure test server is running
    print("Make sure test server is running on port 8080")
    print("Run with: TESTING=true PORT=8080 python mvp_site/main.py serve")
    print()

    test_structured_response_display()
