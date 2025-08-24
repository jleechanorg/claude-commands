#!/usr/bin/env python3
"""Browser test for structured response fields with real services"""

import os
import time

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:6006"
SCREENSHOT_DIR = "/tmp/structured_response_real"


def test_structured_response_e2e():
    """E2E test with real Firebase and Gemini"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Use real services
            page.goto(f"{BASE_URL}/?test_mode=true&test_user_id=test-e2e")
            page.wait_for_load_state("networkidle")

            # Navigate to existing campaign or create new
            page.click('text="Start New Campaign"')
            page.wait_for_selector("#wizard-step-1:not(.hidden)", state="visible")

            page.fill("#campaign-title", "E2E Structured Fields")
            page.fill("#campaign-description", "Real API test")
            page.click('button:has-text("Next")')

            page.wait_for_selector("#wizard-step-2:not(.hidden)", state="visible")
            page.fill("#character-name", "Real Hero")
            page.fill("#character-class", "Wizard")
            page.fill("#character-race", "Elf")
            page.fill("#character-background", "Scholar")

            page.click('button:has-text("Create Campaign")')
            page.wait_for_selector(".story-container", timeout=60000)
            time.sleep(5)

            # Real prompt to trigger dice rolls
            page.fill("#user-input", "I cast firebolt at the enemy! Roll to hit.")
            page.click("button#send-button")

            # Wait for real AI response
            page.wait_for_selector(".ai-message:last-child", timeout=60000)
            time.sleep(5)

            # Screenshot real response
            page.screenshot(
                path=f"{SCREENSHOT_DIR}/real_ai_response.png", full_page=True
            )

            # Check for elements
            dice_found = page.query_selector(".dice-rolls") is not None
            resources_found = page.query_selector(".resources") is not None
            planning_found = page.query_selector(".planning-block") is not None

            print(f"✅ Screenshot: {SCREENSHOT_DIR}/real_ai_response.png")
            print(f"Dice rolls: {'✅' if dice_found else '❌'}")
            print(f"Resources: {'✅' if resources_found else '❌'}")
            print(f"Planning: {'✅' if planning_found else '❌'}")

        except Exception as e:
            print(f"❌ E2E test failed: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/e2e_error.png")
        finally:
            browser.close()


if __name__ == "__main__":
    test_structured_response_e2e()
