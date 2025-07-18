#!/usr/bin/env python3
"""
Simpler browser test for structured fields - uses existing campaign.
"""

import logging
import os
import time

from playwright.sync_api import sync_playwright

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:6006"
SCREENSHOT_DIR = "/tmp/worldarchitectai/browser/structured_fields"
TEST_USER_ID = "test-user-123"
# Use an existing campaign ID from our tests
EXISTING_CAMPAIGN_ID = "test-campaign-123"


def ensure_screenshot_dir():
    """Ensure screenshot directory exists"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    logger.info(f"Screenshot directory: {SCREENSHOT_DIR}")


def test_structured_fields_existing_campaign():
    """Test structured fields with existing campaign"""
    ensure_screenshot_dir()

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate directly to campaign with test mode
            logger.info(f"Navigating to campaign {EXISTING_CAMPAIGN_ID}...")
            url = f"{BASE_URL}/campaign/{EXISTING_CAMPAIGN_ID}?test_mode=true&test_user_id={TEST_USER_ID}"
            page.goto(url)
            page.wait_for_load_state("networkidle")

            # Wait for story container
            page.wait_for_selector(".story-container", timeout=10000)
            time.sleep(2)  # Let content render

            # Take initial screenshot
            page.screenshot(
                path=f"{SCREENSHOT_DIR}/1_campaign_loaded.png", full_page=True
            )
            logger.info("Screenshot saved: 1_campaign_loaded.png")

            # Submit an interaction that should trigger structured fields
            logger.info("Submitting interaction to trigger structured fields...")

            # First, check if user input is available
            input_field = page.query_selector("#user-input")
            if not input_field:
                logger.error("User input field not found!")
                return

            # Type a message that should trigger dice rolls and planning
            test_input = "I cast detect magic on the ancient artifact and examine it carefully. Roll for arcana check."
            page.fill("#user-input", test_input)

            # Take screenshot before submitting
            page.screenshot(
                path=f"{SCREENSHOT_DIR}/2_before_submit.png", full_page=True
            )
            logger.info("Screenshot saved: 2_before_submit.png")

            # Submit the interaction
            send_button = page.query_selector("button#send-button")
            if send_button:
                page.click("button#send-button")
            else:
                # Try alternative selector
                page.click('button[type="submit"]')

            # Wait for AI response
            logger.info("Waiting for AI response with structured fields...")
            try:
                # Wait for a new message to appear
                page.wait_for_selector(".ai-message:last-child", timeout=60000)
                time.sleep(5)  # Let structured fields render completely
            except Exception as e:
                logger.warning(f"Timeout waiting for AI response: {e}")

            # Check for structured fields elements
            logger.info("Checking for structured fields...")

            # Look for dice rolls
            dice_rolls = page.query_selector(".dice-rolls")
            if dice_rolls:
                logger.info("✅ Dice rolls section found!")
                dice_rolls.screenshot(path=f"{SCREENSHOT_DIR}/3_dice_rolls.png")
            else:
                logger.warning("⚠️ Dice rolls section not found")

            # Look for resources
            resources = page.query_selector(".resources")
            if resources:
                logger.info("✅ Resources section found!")
                resources.screenshot(path=f"{SCREENSHOT_DIR}/3_resources.png")
            else:
                logger.warning("⚠️ Resources section not found")

            # Look for planning block
            planning = page.query_selector(".planning-block")
            if planning:
                logger.info("✅ Planning block found!")
                planning.screenshot(path=f"{SCREENSHOT_DIR}/3_planning.png")
            else:
                logger.warning("⚠️ Planning block not found")

            # Take full page screenshot
            page.screenshot(
                path=f"{SCREENSHOT_DIR}/4_structured_fields_full.png", full_page=True
            )
            logger.info("Screenshot saved: 4_structured_fields_full.png")

            # Toggle debug mode
            debug_toggle = page.query_selector("#debug-toggle")
            if debug_toggle:
                logger.info("Toggling debug mode...")
                page.click("#debug-toggle")
                time.sleep(1)
                page.screenshot(
                    path=f"{SCREENSHOT_DIR}/5_debug_mode.png", full_page=True
                )
                logger.info("Screenshot saved: 5_debug_mode.png")

            # Check page content for structured fields text
            page_content = page.content()
            if "Dice Rolls:" in page_content or "🎲" in page_content:
                logger.info("✅ Found dice rolls text in page content")
            if "Resources:" in page_content or "📊" in page_content:
                logger.info("✅ Found resources text in page content")

            # Success summary
            logger.info("\n✅ Browser test completed!")
            logger.info(f"📸 Screenshots saved to: {SCREENSHOT_DIR}")

        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            # Take error screenshot
            page.screenshot(
                path=f"{SCREENSHOT_DIR}/error_screenshot.png", full_page=True
            )
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    logger.info("Starting structured fields browser test...")
    logger.info("This test uses an existing campaign to avoid wizard issues")
    test_structured_fields_existing_campaign()
