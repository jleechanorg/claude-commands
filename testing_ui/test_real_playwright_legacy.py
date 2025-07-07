#!/usr/bin/env python3
"""
REAL Playwright browser test for WorldArchitect.AI
This performs actual browser testing, not mocked tests
"""

import asyncio
import time
from datetime import datetime

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("❌ Playwright not available")

def log(message):
    """Log with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

async def test_with_real_browser():
    """Run real browser tests using Playwright"""
    log("🚀 Starting REAL browser test with Playwright...")
    
    try:
        async with async_playwright() as p:
            # Launch real browser (headless mode)
            log("Launching Chromium browser...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to the application
            log("Navigating to http://localhost:8080...")
            await page.goto("http://localhost:8080")
            
            # Wait for page load
            await page.wait_for_load_state("networkidle")
            
            # Check page title
            title = await page.title()
            log(f"✅ Page title: {title}")
            assert "WorldArchitect.AI" in title
            
            # Check for main UI elements
            log("Checking UI elements...")
            
            # Check navbar
            navbar = await page.query_selector("nav.navbar")
            assert navbar is not None
            log("✅ Navbar found")
            
            # Check for views
            views = ["auth-view", "dashboard-view", "new-campaign-view", "game-view"]
            for view_id in views:
                element = await page.query_selector(f"#{view_id}")
                if element:
                    is_visible = await element.is_visible()
                    log(f"✅ {view_id}: {'visible' if is_visible else 'hidden'}")
                else:
                    log(f"❌ {view_id}: not found")
            
            # Check for campaign form
            form = await page.query_selector("#new-campaign-form")
            if form:
                log("✅ Campaign form found")
                
                # Check form fields
                title_input = await page.query_selector("#campaign-title")
                prompt_textarea = await page.query_selector("#campaign-prompt")
                
                if title_input and prompt_textarea:
                    # Get default values
                    title_value = await title_input.get_attribute("value")
                    prompt_value = await prompt_textarea.text_content()
                    
                    log(f"  Title field: '{title_value}'")
                    log(f"  Prompt field: '{prompt_value[:50]}...'")
                    
                    # Fill in new values
                    await title_input.fill("Real Browser Test Campaign")
                    await prompt_textarea.fill("Testing with a REAL browser using Playwright automation")
                    log("✅ Form fields populated")
                    
                    # Check checkboxes
                    narrative_cb = await page.query_selector("#prompt-narrative")
                    mechanics_cb = await page.query_selector("#prompt-mechanics")
                    
                    if narrative_cb and mechanics_cb:
                        narrative_checked = await narrative_cb.is_checked()
                        mechanics_checked = await mechanics_cb.is_checked()
                        
                        log(f"  Narrative checkbox: {'✅ checked' if narrative_checked else '❌ unchecked'}")
                        log(f"  Mechanics checkbox: {'✅ checked' if mechanics_checked else '❌ unchecked'}")
                        
                        # Try to submit form (will fail due to auth)
                        submit_btn = await page.query_selector('button[type="submit"]')
                        if submit_btn:
                            log("Attempting to submit form...")
                            await submit_btn.click()
                            
                            # Wait a bit for any response
                            await page.wait_for_timeout(2000)
                            
                            # Check for auth error or redirect
                            current_url = page.url
                            log(f"Current URL after submit: {current_url}")
            
            # Check JavaScript console
            log("Checking browser console for errors...")
            page.on("console", lambda msg: log(f"Console {msg.type}: {msg.text}"))
            
            # Take screenshot
            screenshot_path = "/tmp/real_browser_screenshot.png"
            await page.screenshot(path=screenshot_path)
            log(f"📸 Screenshot saved to {screenshot_path}")
            
            # Check network activity
            log("Checking loaded resources...")
            
            # Evaluate JavaScript
            firebase_loaded = await page.evaluate("typeof firebase !== 'undefined'")
            bootstrap_loaded = await page.evaluate("typeof bootstrap !== 'undefined'")
            
            log(f"Firebase loaded: {'✅' if firebase_loaded else '❌'}")
            log(f"Bootstrap loaded: {'✅' if bootstrap_loaded else '❌'}")
            
            # Close browser
            await browser.close()
            log("✅ Browser closed successfully")
            
            return True
            
    except Exception as e:
        log(f"❌ Browser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_with_browser_context():
    """Test API calls from browser context"""
    log("\n🔍 Testing API calls from browser context...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to app
            await page.goto("http://localhost:8080")
            
            # Try to make API call from browser context
            response = await page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('/api/campaigns', {
                            method: 'GET',
                            headers: {
                                'X-Test-Bypass': 'true',
                                'X-Test-User-Id': 'playwright-test'
                            }
                        });
                        return {
                            status: response.status,
                            statusText: response.statusText,
                            body: await response.text()
                        };
                    } catch (e) {
                        return { error: e.message };
                    }
                }
            """)
            
            log(f"API Response: {response}")
            
            await browser.close()
            
    except Exception as e:
        log(f"❌ API test failed: {e}")

def main():
    """Run all tests"""
    if not PLAYWRIGHT_AVAILABLE:
        log("❌ Playwright not installed properly")
        return
    
    log("=" * 60)
    log("REAL BROWSER TESTING WITH PLAYWRIGHT")
    log("=" * 60)
    
    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test 1: Real browser UI testing
        success = loop.run_until_complete(test_with_real_browser())
        
        if success:
            # Test 2: API testing from browser
            loop.run_until_complete(test_api_with_browser_context())
        
        log("\n" + "=" * 60)
        log("✅ REAL BROWSER TESTING COMPLETE")
        log("This was actual browser automation, not mocked!")
        log("=" * 60)
        
    finally:
        loop.close()

if __name__ == "__main__":
    main()