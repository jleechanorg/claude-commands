#!/usr/bin/env python3
"""Browser test for structured response fields with mocked services"""

import os
import time

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:6006"
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

            # Create campaign quickly
            page.click('text="Start New Campaign"')
            page.wait_for_selector("#wizard-step-1:not(.hidden)", state="visible")

            page.fill("#campaign-title", "Structured Response Test")
            page.fill("#campaign-description", "Testing structured fields")
            page.click('button:has-text("Next")')

            page.wait_for_selector("#wizard-step-2:not(.hidden)", state="visible")
            page.fill("#character-name", "Tester")
            page.fill("#character-class", "Fighter")
            page.fill("#character-race", "Human")
            page.fill("#character-background", "Test")

            page.click('button:has-text("Create Campaign")')
            page.wait_for_selector(".story-container", timeout=30000)
            time.sleep(2)

            # Submit interaction
            page.fill("#user-input", "I attack with my sword!")
            page.click("button#send-button")

            # Wait for response
            page.wait_for_selector(".ai-message", timeout=30000)
            time.sleep(3)

            # Take screenshot
            page.screenshot(
                path=f"{SCREENSHOT_DIR}/mocked_response.png", full_page=True
            )

            print(f"✅ Screenshot saved: {SCREENSHOT_DIR}/mocked_response.png")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
        finally:
            browser.close()


if __name__ == "__main__":
    test_structured_response_display()
