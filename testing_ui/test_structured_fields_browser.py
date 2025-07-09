#!/usr/bin/env python3
"""
Browser test for structured fields UI with real Firebase and Gemini APIs.
Captures screenshots of the structured fields display.
"""
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:6006"
SCREENSHOT_DIR = "/tmp/worldarchitectai/browser/structured_fields"
TEST_USER_ID = "test-user-structured-fields"
TEST_CAMPAIGN_ID = None  # Will be set after creation

def ensure_screenshot_dir():
    """Ensure screenshot directory exists"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    logger.info(f"Screenshot directory: {SCREENSHOT_DIR}")

def test_structured_fields_ui():
    """Test structured fields display with real APIs"""
    ensure_screenshot_dir()
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set to False to see the browser
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 1. Navigate to app with test mode
            logger.info("Navigating to app with test mode...")
            page.goto(f"{BASE_URL}?test_mode=true&test_user_id={TEST_USER_ID}")
            page.wait_for_load_state('networkidle')
            
            # Take screenshot of landing page
            page.screenshot(path=f"{SCREENSHOT_DIR}/1_landing_page.png", full_page=True)
            logger.info("Screenshot saved: 1_landing_page.png")
            
            # 2. Start campaign creation wizard
            logger.info("Starting campaign creation...")
            page.click('text="Start New Campaign"')
            # Wait for wizard step 1 to be visible
            page.wait_for_selector('#wizard-step-1:not(.hidden)', state='visible', timeout=10000)
            
            # 3. Fill in campaign details
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            campaign_title = f"Structured Fields Test {timestamp}"
            
            page.fill('#campaign-title', campaign_title)
            page.fill('#campaign-description', 'Testing structured fields display with dice rolls, resources, and planning blocks')
            
            # Click Next to go to character creation
            page.click('button:has-text("Next: Character Creation")')
            page.wait_for_selector('#wizard-step-2:not(.hidden)', state='visible', timeout=10000)
            
            # Fill character details
            page.fill('#character-name', 'Test Adventurer')
            page.fill('#character-class', 'Wizard')
            page.fill('#character-race', 'Elf')
            page.fill('#character-background', 'Sage studying ancient artifacts and structured magic')
            
            # Take screenshot of filled form
            page.screenshot(path=f"{SCREENSHOT_DIR}/2_campaign_form.png", full_page=True)
            logger.info("Screenshot saved: 2_campaign_form.png")
            
            # 4. Submit campaign creation
            logger.info("Creating campaign...")
            page.click('button:has-text("Create Campaign")')
            
            # Wait for campaign to be created and page to load
            page.wait_for_selector('.story-container', timeout=30000)
            time.sleep(2)  # Let initial content render
            
            # Take screenshot of initial campaign
            page.screenshot(path=f"{SCREENSHOT_DIR}/3_campaign_created.png", full_page=True)
            logger.info("Screenshot saved: 3_campaign_created.png")
            
            # 5. Submit an interaction that should trigger structured fields
            logger.info("Submitting interaction to trigger structured fields...")
            
            # Type a message that should trigger dice rolls and planning
            test_input = "I cast detect magic on the ancient artifact and examine it carefully. Roll for arcana check."
            page.fill('#user-input', test_input)
            
            # Take screenshot before submitting
            page.screenshot(path=f"{SCREENSHOT_DIR}/4_before_submit.png", full_page=True)
            logger.info("Screenshot saved: 4_before_submit.png")
            
            # Submit the interaction
            page.click('button#send-button')
            
            # Wait for AI response with structured fields
            logger.info("Waiting for AI response with structured fields...")
            page.wait_for_selector('.ai-message', timeout=45000)
            time.sleep(3)  # Let structured fields render
            
            # 6. Check for structured fields elements
            logger.info("Checking for structured fields...")
            
            # Look for dice rolls
            dice_rolls = page.query_selector('.dice-rolls')
            if dice_rolls:
                logger.info("✅ Dice rolls section found!")
                # Take close-up screenshot of dice rolls
                dice_rolls.screenshot(path=f"{SCREENSHOT_DIR}/5a_dice_rolls_closeup.png")
            else:
                logger.warning("⚠️ Dice rolls section not found")
            
            # Look for resources
            resources = page.query_selector('.resources')
            if resources:
                logger.info("✅ Resources section found!")
                resources.screenshot(path=f"{SCREENSHOT_DIR}/5b_resources_closeup.png")
            else:
                logger.warning("⚠️ Resources section not found")
            
            # Look for planning block
            planning = page.query_selector('.planning-block')
            if planning:
                logger.info("✅ Planning block found!")
                planning.screenshot(path=f"{SCREENSHOT_DIR}/5c_planning_block_closeup.png")
            else:
                logger.warning("⚠️ Planning block not found")
            
            # Take full page screenshot with structured fields
            page.screenshot(path=f"{SCREENSHOT_DIR}/6_structured_fields_displayed.png", full_page=True)
            logger.info("Screenshot saved: 6_structured_fields_displayed.png")
            
            # 7. Toggle debug mode to see debug_info
            logger.info("Toggling debug mode...")
            page.click('#debug-toggle')
            time.sleep(1)
            
            # Take screenshot with debug mode
            page.screenshot(path=f"{SCREENSHOT_DIR}/7_debug_mode_enabled.png", full_page=True)
            logger.info("Screenshot saved: 7_debug_mode_enabled.png")
            
            # 8. Submit another interaction
            logger.info("Submitting another interaction...")
            page.fill('#user-input', 'I attempt to decipher the magical runes. What do they say?')
            page.click('button#send-button')
            
            # Wait for second response
            page.wait_for_selector('.ai-message:nth-of-type(2)', timeout=45000)
            time.sleep(3)
            
            # Final screenshot
            page.screenshot(path=f"{SCREENSHOT_DIR}/8_multiple_interactions.png", full_page=True)
            logger.info("Screenshot saved: 8_multiple_interactions.png")
            
            # Success summary
            logger.info("\n✅ Browser test completed successfully!")
            logger.info(f"📸 Screenshots saved to: {SCREENSHOT_DIR}")
            logger.info("\nStructured fields test results:")
            logger.info(f"- Dice rolls: {'Found' if dice_rolls else 'Not found'}")
            logger.info(f"- Resources: {'Found' if resources else 'Not found'}")
            logger.info(f"- Planning block: {'Found' if planning else 'Not found'}")
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            # Take error screenshot
            page.screenshot(path=f"{SCREENSHOT_DIR}/error_screenshot.png", full_page=True)
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    logger.info("Starting structured fields browser test with real APIs...")
    logger.info("This test will use real Firebase and Gemini APIs")
    logger.info("Make sure the test server is running on port 6006")
    test_structured_fields_ui()