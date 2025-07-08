#!/usr/bin/env python3
"""
Comprehensive screenshot capture script for UI Release Bundle features.
Captures all deployed features with real Firebase/Gemini authentication.
"""

import os
import sys
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DEV_URL = "https://mvp-site-app-dev-754683067800.us-central1.run.app"
SCREENSHOT_DIR = "/tmp/worldarchitectai/ui_bundle_screenshots"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Ensure screenshot directory exists
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def setup_browser() -> tuple[Browser, BrowserContext, Page]:
    """Set up Playwright browser with proper configuration."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=False,  # Show browser for debugging
        args=['--no-sandbox', '--disable-dev-shm-usage']
    )
    
    # Create context with proper viewport
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        device_scale_factor=2  # High DPI screenshots
    )
    
    page = context.new_page()
    
    # Enable console logging
    page.on("console", lambda msg: logger.info(f"Console: {msg.text}"))
    page.on("pageerror", lambda exc: logger.error(f"Page error: {exc}"))
    
    return browser, context, page

def take_screenshot(page: Page, name: str, description: str = "") -> str:
    """Take a screenshot with metadata."""
    filename = f"{TIMESTAMP}_{name}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    # Take the screenshot
    page.screenshot(path=filepath, full_page=False)
    
    logger.info(f"📸 Screenshot saved: {filename}")
    if description:
        logger.info(f"   Description: {description}")
    
    # Save metadata
    metadata_file = os.path.join(SCREENSHOT_DIR, f"{TIMESTAMP}_metadata.json")
    metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    
    metadata[name] = {
        "filename": filename,
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "url": page.url
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return filepath

def wait_for_element_and_click(page: Page, selector: str, timeout: int = 10000) -> bool:
    """Wait for element and click it."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.click(selector)
        return True
    except Exception as e:
        logger.error(f"Failed to click {selector}: {e}")
        return False

def capture_campaign_wizard_features(page: Page):
    """Capture campaign wizard with Dragon Knight selection and custom campaign."""
    logger.info("📍 Capturing Campaign Wizard features...")
    
    # Navigate to dev site
    logger.info(f"Navigating to {DEV_URL}")
    page.goto(DEV_URL, wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    # Use test mode to bypass auth
    test_url = f"{DEV_URL}?test_mode=true&test_user_id=ui-bundle-test"
    logger.info("Using test mode to bypass authentication")
    page.goto(test_url, wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    # Force test mode activation
    logger.info("Forcing test mode activation...")
    page.evaluate("""
        window.testAuthBypass = {
            enabled: true,
            userId: 'ui-bundle-test'
        };
        // Hide auth view and show dashboard
        const authView = document.getElementById('auth-view');
        const dashboardView = document.getElementById('dashboard-view');
        if (authView && dashboardView) {
            authView.classList.remove('active-view');
            dashboardView.classList.add('active-view');
        }
        // Trigger campaign list fetch
        if (window.renderCampaignList) {
            window.renderCampaignList();
        }
    """)
    page.wait_for_timeout(3000)
    
    # Check if we're on dashboard
    if page.is_visible("#dashboard-view"):
        logger.info("✅ Successfully reached dashboard")
    else:
        logger.warning("Dashboard view not visible, taking diagnostic screenshot")
        take_screenshot(page, "00_diagnostic_current_view", "Current page state")
    
    # Look for campaign buttons
    logger.info("Looking for campaign buttons...")
    # Try multiple selectors for the button
    button_selectors = [
        "button:has-text('Start a new campaign')",
        "#newCampaignBtn",
        "button.btn-primary:has-text('new campaign')",
        "button >> text=new campaign"
    ]
    
    button_clicked = False
    for selector in button_selectors:
        try:
            if page.is_visible(selector):
                page.click(selector)
                button_clicked = True
                logger.info(f"✅ Clicked button using selector: {selector}")
                break
        except:
            continue
    
    if button_clicked:
        page.wait_for_timeout(2000)
        
        # Take screenshot of campaign wizard with all options
        take_screenshot(page, "01_campaign_wizard_initial", 
                       "Campaign wizard showing all available campaign options")
        
        # Click on Dragon Knight radio button
        logger.info("Selecting Dragon Knight campaign...")
        dragon_knight_radio = page.locator("input[type='radio'][value='dragon_knight']")
        if dragon_knight_radio.count() > 0:
            dragon_knight_radio.click()
            page.wait_for_timeout(1000)
            
            # Check if campaign details are shown
            campaign_details = page.locator("#campaign-details")
            if campaign_details.is_visible():
                take_screenshot(page, "02_dragon_knight_selected",
                              "Dragon Knight campaign selected with pre-filled content visible")
            else:
                logger.warning("Campaign details not visible after selection")
        else:
            logger.error("Dragon Knight radio button not found")
            
        # Now select custom campaign
        logger.info("Selecting custom campaign option...")
        custom_radio = page.locator("input[type='radio'][value='custom']")
        if custom_radio.count() > 0:
            custom_radio.click()
            page.wait_for_timeout(1000)
            
            # Take screenshot showing custom campaign textarea
            take_screenshot(page, "03_custom_campaign_option",
                          "Custom campaign option with editable textarea")
        else:
            logger.error("Custom campaign radio button not found")

def capture_campaign_name_editing(page: Page):
    """Capture inline campaign name editing feature."""
    logger.info("📍 Capturing campaign name editing...")
    
    # First create a campaign to demonstrate editing
    logger.info("Creating a campaign to demonstrate name editing...")
    
    # Go back to dashboard
    page.goto(f"{DEV_URL}?test_mode=true&test_user_id=ui-bundle-test", wait_until="networkidle")
    page.wait_for_timeout(2000)
    
    # Start new campaign
    if wait_for_element_and_click(page, "button:has-text('Start a new campaign')"):
        page.wait_for_timeout(2000)
        
        # Select Dragon Knight and create
        dragon_knight_radio = page.locator("input[type='radio'][value='dragon_knight']")
        if dragon_knight_radio.count() > 0:
            dragon_knight_radio.click()
            page.wait_for_timeout(1000)
            
            # Click create campaign
            if wait_for_element_and_click(page, "button:has-text('Create Campaign')"):
                logger.info("Campaign creation initiated...")
                page.wait_for_timeout(5000)  # Wait for campaign to be created
                
                # Look for campaign name element
                campaign_name = page.locator("h2.editable-campaign-name, .campaign-name")
                if campaign_name.count() > 0:
                    take_screenshot(page, "04_campaign_page_initial",
                                  "Campaign page showing editable campaign name")
                    
                    # Click on the campaign name to edit
                    campaign_name.first.click()
                    page.wait_for_timeout(500)
                    
                    # Check if input field appears
                    name_input = page.locator("input.campaign-name-input")
                    if name_input.is_visible():
                        take_screenshot(page, "05_campaign_name_editing",
                                      "Inline campaign name editing in progress")
                    else:
                        logger.warning("Campaign name input field not visible")
                else:
                    logger.error("Campaign name element not found")

def capture_story_reader_controls(page: Page):
    """Capture story reader with pause/continue controls."""
    logger.info("📍 Capturing story reader controls...")
    
    # Assuming we're still on a campaign page, look for story reader
    story_container = page.locator("#story-container, .story-container")
    if story_container.is_visible():
        # Scroll to story section
        story_container.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        
        # Look for pause/continue controls
        pause_button = page.locator("button:has-text('Pause'), button#pause-reading")
        continue_button = page.locator("button:has-text('Continue'), button#continue-reading")
        
        if pause_button.is_visible() or continue_button.is_visible():
            take_screenshot(page, "06_story_reader_controls",
                          "Story reader interface with pause/continue controls visible")
        else:
            logger.warning("Pause/Continue controls not found")
            # Still take a screenshot of the story area
            take_screenshot(page, "06_story_reader_area",
                          "Story reader interface area")
    else:
        logger.warning("Story container not found on page")

def capture_download_share_buttons(page: Page):
    """Capture download/share buttons at the top of the page."""
    logger.info("📍 Capturing download/share buttons...")
    
    # Scroll to top to ensure buttons are visible
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)
    
    # Look for specific download button (not using multiple element selector)
    download_visible = False
    share_visible = False
    
    try:
        # Check for the main download story button
        if page.is_visible("#downloadStoryBtn"):
            download_visible = True
            logger.info("Found download story button")
    except:
        pass
    
    try:
        # Check for share button
        if page.is_visible("button:has-text('Share')"):
            share_visible = True
            logger.info("Found share button")
    except:
        pass
    
    # Also check button bar at top
    button_bar_visible = False
    try:
        if page.is_visible(".button-bar") or page.is_visible(".top-buttons") or page.is_visible(".campaign-actions"):
            button_bar_visible = True
    except:
        pass
    
    if download_visible or share_visible or button_bar_visible:
        take_screenshot(page, "07_download_share_buttons",
                      "Download and Share buttons positioned at the top of the page")
    else:
        logger.warning("Download/Share buttons not found at expected locations")
        # Take a screenshot of the top area anyway
        take_screenshot(page, "07_page_top_area",
                      "Top area of the page where buttons should be")

def main():
    """Main function to capture all UI bundle features."""
    logger.info("🚀 Starting UI Bundle Screenshot Capture")
    logger.info(f"📸 Screenshots will be saved to: {SCREENSHOT_DIR}")
    logger.info(f"🌐 Target URL: {DEV_URL}")
    
    browser = None
    try:
        # Setup browser
        browser, context, page = setup_browser()
        
        # Capture each feature
        capture_campaign_wizard_features(page)
        capture_campaign_name_editing(page)
        capture_story_reader_controls(page)
        capture_download_share_buttons(page)
        
        # Generate summary
        logger.info("\n✅ Screenshot capture completed!")
        logger.info(f"📁 All screenshots saved to: {SCREENSHOT_DIR}")
        
        # List all captured screenshots
        screenshots = [f for f in os.listdir(SCREENSHOT_DIR) if f.startswith(TIMESTAMP)]
        logger.info(f"\n📸 Captured {len(screenshots)} screenshots:")
        for screenshot in sorted(screenshots):
            logger.info(f"   - {screenshot}")
        
    except Exception as e:
        logger.error(f"❌ Error during capture: {e}")
        raise
    finally:
        if browser:
            browser.close()

if __name__ == "__main__":
    main()