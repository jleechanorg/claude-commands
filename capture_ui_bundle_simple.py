#!/usr/bin/env python3
"""
Simple screenshot capture for UI Release Bundle features.
Focuses on capturing what's actually visible on the deployed site.
"""

import os
import sys
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
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

def take_screenshot(page: Page, name: str, description: str = "") -> str:
    """Take a screenshot with metadata."""
    filename = f"{TIMESTAMP}_{name}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    # Take the screenshot
    page.screenshot(path=filepath, full_page=False)
    
    logger.info(f"📸 Screenshot saved: {filename}")
    if description:
        logger.info(f"   Description: {description}")
    
    return filepath

def main():
    """Main function to capture UI bundle features."""
    logger.info("🚀 Starting Simple UI Bundle Screenshot Capture")
    logger.info(f"📸 Screenshots will be saved to: {SCREENSHOT_DIR}")
    logger.info(f"🌐 Target URL: {DEV_URL}")
    
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=True,  # Run in headless mode
        args=['--no-sandbox', '--disable-dev-shm-usage']
    )
    
    try:
        # Create context with proper viewport
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            device_scale_factor=2  # High DPI screenshots
        )
        
        page = context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: logger.info(f"Console: {msg.text}"))
        
        # 1. Navigate to the site and capture initial state
        logger.info("📍 Step 1: Navigating to site...")
        page.goto(DEV_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        
        take_screenshot(page, "01_initial_page", "Initial page load - auth screen")
        
        # 2. Try test mode
        logger.info("📍 Step 2: Attempting test mode...")
        test_url = f"{DEV_URL}?test_mode=true&test_user_id=ui-test"
        page.goto(test_url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        
        # Force test mode activation
        page.evaluate("""
            window.testAuthBypass = {
                enabled: true,
                userId: 'ui-test'
            };
            // Try to show dashboard
            const authView = document.getElementById('auth-view');
            const dashboardView = document.getElementById('dashboard-view');
            if (authView && dashboardView) {
                authView.classList.remove('active-view');
                dashboardView.classList.add('active-view');
            }
        """)
        page.wait_for_timeout(2000)
        
        take_screenshot(page, "02_test_mode_activated", "After test mode activation")
        
        # 3. Look for campaign elements
        logger.info("📍 Step 3: Looking for campaign elements...")
        
        # Check what's visible on the page
        visible_elements = page.evaluate("""
            (() => {
                const elements = {
                    dashboard: !!document.querySelector('#dashboard-view.active-view'),
                    authView: !!document.querySelector('#auth-view.active-view'),
                    newCampaignBtn: !!document.querySelector('#newCampaignBtn') || 
                                   Array.from(document.querySelectorAll('button')).some(b => b.textContent.toLowerCase().includes('new campaign')),
                    campaignList: !!document.querySelector('#campaignList'),
                    campaignWizard: !!document.querySelector('.campaign-wizard'),
                    storyContainer: !!document.querySelector('#story-container'),
                    downloadBtn: !!document.querySelector('#downloadStoryBtn'),
                    shareBtn: Array.from(document.querySelectorAll('button')).some(b => b.textContent.includes('Share'))
                };
                return elements;
            })()
        """)
        
        logger.info(f"Visible elements: {visible_elements}")
        
        # 4. If we see a new campaign button, click it
        if page.is_visible("text=new campaign"):
            logger.info("Found new campaign button, clicking...")
            page.click("text=new campaign")
            page.wait_for_timeout(2000)
            take_screenshot(page, "03_campaign_wizard", "Campaign wizard interface")
            
            # Look for campaign options
            if page.is_visible("text=Dragon Knight"):
                take_screenshot(page, "04_dragon_knight_option", "Dragon Knight campaign option visible")
        
        # 5. Navigate to a specific campaign URL if available
        logger.info("📍 Step 4: Trying direct campaign navigation...")
        # This would be a real campaign URL if we knew one
        campaign_url = f"{DEV_URL}/campaign/test-campaign?test_mode=true&test_user_id=ui-test"
        page.goto(campaign_url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        
        take_screenshot(page, "05_campaign_page", "Campaign page (if accessible)")
        
        # 6. Look for specific UI elements
        logger.info("📍 Step 5: Looking for UI Release Bundle features...")
        
        # Scroll through the page to find elements
        page.evaluate("window.scrollTo(0, 0)")
        take_screenshot(page, "06_page_top", "Top of page - looking for download/share buttons")
        
        # Check for story reader
        if page.is_visible("#story-container"):
            page.locator("#story-container").scroll_into_view_if_needed()
            take_screenshot(page, "07_story_reader", "Story reader interface")
        
        # Check for any campaign name elements
        if page.is_visible("h2"):
            take_screenshot(page, "08_campaign_name", "Campaign name area")
        
        # Final full page screenshot
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{TIMESTAMP}_09_full_page.png"), full_page=True)
        logger.info("📸 Captured full page screenshot")
        
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
        # Try to capture error state
        try:
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{TIMESTAMP}_error.png"))
        except:
            pass
        raise
    finally:
        browser.close()
        playwright.stop()

if __name__ == "__main__":
    main()