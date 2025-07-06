#!/usr/bin/env python3
"""
Real browser test using Playwright to demonstrate actual browser automation.
This test will:
1. Launch a real browser (with screenshots)
2. Navigate to the WorldArchitect.AI site
3. Perform actual UI interactions
4. Take screenshots as proof
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from playwright.async_api import async_playwright

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8086"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")

async def test_real_browser():
    """
    Launch a real browser and test WorldArchitect.AI with visual proof.
    """
    # Create screenshot directory
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser in headful mode (visible browser window)
        # Use headless=False to see the browser, headless=True for CI/CD
        browser = await p.chromium.launch(
            headless=True,  # Set to False to see the browser window
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        print("🌐 Browser launched successfully")
        
        # Create a new browser context with viewport
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            device_scale_factor=2,  # High DPI screenshots
        )
        
        # Create a new page
        page = await context.new_page()
        print("📄 New page created")
        
        # Enable console logging
        page.on("console", lambda msg: print(f"🖥️ Console: {msg.text}"))
        
        # Navigate to the site
        print(f"🔗 Navigating to {BASE_URL}")
        try:
            await page.goto(BASE_URL, wait_until='networkidle')
            print("✅ Successfully loaded the page")
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            # Take error screenshot
            await page.screenshot(
                path=os.path.join(SCREENSHOT_DIR, "error_page_load.png"),
                full_page=True
            )
            return
        
        # Take initial screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        await page.screenshot(
            path=os.path.join(SCREENSHOT_DIR, f"01_initial_page_{timestamp}.png"),
            full_page=True
        )
        print("📸 Screenshot 1: Initial page captured")
        
        # Wait for page to be fully loaded
        await page.wait_for_load_state('domcontentloaded')
        
        # Check if we're on the campaign list or wizard
        if await page.locator("text=Select Campaign").count() > 0:
            print("📋 On campaign selection page")
            
            # Take screenshot of campaign list
            await page.screenshot(
                path=os.path.join(SCREENSHOT_DIR, f"02_campaign_list_{timestamp}.png"),
                full_page=True
            )
            print("📸 Screenshot 2: Campaign list captured")
            
            # Click "New Campaign" button
            new_campaign_btn = page.locator("button:has-text('New Campaign')")
            if await new_campaign_btn.count() > 0:
                print("🖱️ Clicking 'New Campaign' button")
                await new_campaign_btn.click()
                await page.wait_for_load_state('networkidle')
                
                # Take screenshot after clicking
                await page.screenshot(
                    path=os.path.join(SCREENSHOT_DIR, f"03_after_new_campaign_{timestamp}.png"),
                    full_page=True
                )
                print("📸 Screenshot 3: After clicking New Campaign")
        
        # Check if we're on the campaign wizard
        if await page.locator("text=Campaign Creation Wizard").count() > 0:
            print("🧙 On Campaign Creation Wizard")
            
            # Fill in the campaign prompt
            prompt_textarea = page.locator("textarea#campaignPrompt")
            if await prompt_textarea.count() > 0:
                test_prompt = "A brave knight must save a kingdom from an ancient dragon"
                print(f"⌨️ Typing campaign prompt: '{test_prompt}'")
                await prompt_textarea.fill(test_prompt)
                
                # Take screenshot with filled prompt
                await page.screenshot(
                    path=os.path.join(SCREENSHOT_DIR, f"04_filled_prompt_{timestamp}.png"),
                    full_page=True
                )
                print("📸 Screenshot 4: Filled campaign prompt")
                
                # Wait a moment to simulate user reading
                await page.wait_for_timeout(1000)
                
                # Click "Start Campaign" button
                start_btn = page.locator("button:has-text('Start Campaign')")
                if await start_btn.count() > 0:
                    print("🖱️ Clicking 'Start Campaign' button")
                    
                    # Take screenshot just before clicking
                    await page.screenshot(
                        path=os.path.join(SCREENSHOT_DIR, f"05_before_start_{timestamp}.png"),
                        full_page=True
                    )
                    
                    await start_btn.click()
                    
                    # Wait for loading to start
                    await page.wait_for_timeout(500)
                    
                    # Take screenshot during loading
                    await page.screenshot(
                        path=os.path.join(SCREENSHOT_DIR, f"06_loading_{timestamp}.png"),
                        full_page=True
                    )
                    print("📸 Screenshot 5-6: Before start and during loading")
        
        # Wait for any animations
        await page.wait_for_timeout(2000)
        
        # Take final screenshot
        await page.screenshot(
            path=os.path.join(SCREENSHOT_DIR, f"07_final_state_{timestamp}.png"),
            full_page=True
        )
        print("📸 Screenshot 7: Final state captured")
        
        # Get page metrics as proof of real browser
        metrics = await page.evaluate("""() => {
            return {
                url: window.location.href,
                title: document.title,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                devicePixelRatio: window.devicePixelRatio,
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                cookieEnabled: navigator.cookieEnabled,
                onLine: navigator.onLine,
                language: navigator.language,
                timestamp: new Date().toISOString()
            }
        }""")
        
        print("\n🔍 Browser Metrics (Proof of Real Browser):")
        print(f"  URL: {metrics['url']}")
        print(f"  Title: {metrics['title']}")
        print(f"  Viewport: {metrics['viewport']['width']}x{metrics['viewport']['height']}")
        print(f"  Device Pixel Ratio: {metrics['devicePixelRatio']}")
        print(f"  User Agent: {metrics['userAgent']}")
        print(f"  Platform: {metrics['platform']}")
        print(f"  Cookies Enabled: {metrics['cookieEnabled']}")
        print(f"  Online: {metrics['onLine']}")
        print(f"  Language: {metrics['language']}")
        print(f"  Timestamp: {metrics['timestamp']}")
        
        # Close browser
        await browser.close()
        print("\n✅ Browser closed successfully")
        
        # List all screenshots taken
        print(f"\n📁 Screenshots saved to: {SCREENSHOT_DIR}")
        for file in sorted(os.listdir(SCREENSHOT_DIR)):
            if file.endswith('.png'):
                file_path = os.path.join(SCREENSHOT_DIR, file)
                file_size = os.path.getsize(file_path)
                print(f"  - {file} ({file_size:,} bytes)")

async def main():
    """Main entry point."""
    print("=" * 70)
    print("🎭 Playwright Real Browser Test")
    print("This test launches a real Chromium browser and takes screenshots")
    print("=" * 70)
    
    try:
        # First check if Playwright is installed
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("❌ Playwright not installed. Installing...")
            os.system("pip install playwright")
            os.system("playwright install chromium")
            from playwright.async_api import async_playwright
        
        # Check if test server is running
        import requests
        try:
            response = requests.get(BASE_URL, timeout=2)
            print(f"✅ Test server is running on {BASE_URL}")
        except:
            print(f"❌ Test server not running on {BASE_URL}")
            print("Please run: python3 /tmp/monitored_test_server.py")
            return
        
        # Run the test
        await test_real_browser()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())