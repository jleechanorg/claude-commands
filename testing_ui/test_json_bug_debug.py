#!/usr/bin/env python3
"""
Browser test to debug JSON display bug.
This test will:
1. Create a campaign
2. Trigger the JSON bug (character creation option 2)
3. Capture console logs and screenshot the issue
"""

import os
import sys
import time
import logging
from playwright.sync_api import sync_playwright, Page, ConsoleMessage
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging_util

# Configure logging
logging_util.setup()
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:6006')
HEADLESS = os.environ.get('HEADLESS', 'true').lower() == 'true'
SCREENSHOT_DIR = os.environ.get('SCREENSHOT_DIR', '/tmp/worldarchitectai/browser')

# Ensure screenshot directory exists
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

class ConsoleCapture:
    """Captures browser console messages"""
    def __init__(self):
        self.messages: List[str] = []
    
    def on_console(self, msg: ConsoleMessage):
        """Capture console messages"""
        text = f"[{msg.type}] {msg.text}"
        self.messages.append(text)
        # Also log to Python logger
        logger.info(f"BROWSER CONSOLE: {text}")
        
        # Log any arguments
        for arg in msg.args:
            try:
                value = arg.json_value()
                if value:
                    logger.info(f"  Console arg: {value}")
            except:
                pass

def test_json_bug_display():
    """Test that reproduces and debugs the JSON display bug"""
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        
        # Set up console capture
        console_capture = ConsoleCapture()
        
        try:
            # Create page and attach console listener
            page = context.new_page()
            page.on("console", console_capture.on_console)
            
            # Enable verbose console logging by injecting debug code
            page.add_init_script("""
                // Override console methods to ensure we capture everything
                const originalLog = console.log;
                const originalError = console.error;
                const originalWarn = console.warn;
                
                console.log = function(...args) {
                    originalLog.apply(console, ['[DEBUG LOG]', ...args]);
                };
                
                console.error = function(...args) {
                    originalError.apply(console, ['[DEBUG ERROR]', ...args]);
                };
                
                console.warn = function(...args) {
                    originalWarn.apply(console, ['[DEBUG WARN]', ...args]);
                };
                
                // Add debugging to fetch/API calls
                const originalFetch = window.fetch;
                window.fetch = async function(...args) {
                    console.log('🔍 FETCH REQUEST:', args[0], args[1]);
                    const response = await originalFetch.apply(window, args);
                    const clonedResponse = response.clone();
                    
                    try {
                        const responseData = await clonedResponse.json();
                        console.log('🔍 FETCH RESPONSE:', {
                            url: args[0],
                            status: response.status,
                            data: responseData
                        });
                        
                        // Check if response contains JSON in text field
                        if (responseData.text && responseData.text.trim().startsWith('{')) {
                            console.error('🔍 JSON BUG DETECTED IN RESPONSE!');
                            console.error('🔍 Response text field contains JSON:', responseData.text.substring(0, 200));
                        }
                    } catch (e) {
                        console.log('🔍 FETCH RESPONSE (non-JSON):', response.status);
                    }
                    
                    return response;
                };
                
                console.log('🔍 Debug instrumentation loaded');
            """)
            
            logger.info(f"Opening {BASE_URL}")
            page.goto(BASE_URL)
            
            # Wait for page to load
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Take initial screenshot
            page.screenshot(path=f"{SCREENSHOT_DIR}/01_homepage.png")
            logger.info("Screenshot saved: 01_homepage.png")
            
            # Click "New Campaign" button
            logger.info("Clicking 'New Campaign' button")
            new_campaign_btn = page.get_by_role("button", name="New Campaign")
            new_campaign_btn.click()
            
            time.sleep(1)
            page.screenshot(path=f"{SCREENSHOT_DIR}/02_new_campaign_form.png")
            
            # Fill in campaign details
            logger.info("Filling campaign form")
            page.fill("#campaignTitle", "JSON Bug Test Campaign")
            page.fill("#campaignPremise", "A brave knight in a land of dragons needs to choose between killing an evil dragon or joining its side.")
            
            # Select "Use Default Setting (Assiah)"
            page.click('input[name="customizationOption"][value="defaultWorld"]')
            
            page.screenshot(path=f"{SCREENSHOT_DIR}/03_campaign_filled.png")
            
            # Submit form
            logger.info("Submitting campaign form")
            page.click('button[type="submit"]')
            
            # Wait for campaign to be created
            page.wait_for_selector("#storyLog", timeout=30000)
            time.sleep(3)
            
            page.screenshot(path=f"{SCREENSHOT_DIR}/04_campaign_created.png")
            logger.info("Campaign created, initial scene displayed")
            
            # Log the initial story content
            story_content = page.query_selector("#storyLog")
            if story_content:
                logger.info(f"Initial story content: {story_content.inner_text()[:200]}...")
            
            # Now trigger the bug - respond with "2" to choose AI character generation
            logger.info("Entering '2' to trigger JSON bug")
            input_field = page.query_selector("#userInput")
            if input_field:
                input_field.fill("2")
                page.screenshot(path=f"{SCREENSHOT_DIR}/05_typed_2.png")
                
                # Submit the response
                submit_btn = page.query_selector("#chatForm button[type='submit']")
                if submit_btn:
                    submit_btn.click()
                else:
                    # Try pressing Enter
                    input_field.press("Enter")
                
                # Wait for response
                logger.info("Waiting for AI response...")
                time.sleep(10)  # Give it time to process
                
                # Take screenshot of the bug
                page.screenshot(path=f"{SCREENSHOT_DIR}/06_json_bug_displayed.png")
                logger.info("Screenshot of JSON bug saved")
                
                # Get the story content again
                story_entries = page.query_selector_all(".message-bubble")
                if story_entries and len(story_entries) > 1:
                    last_entry = story_entries[-1]
                    bug_text = last_entry.inner_text()
                    logger.error(f"🔍 BUG REPRODUCED! Last story entry shows: {bug_text[:200]}...")
                    
                    # Check if it contains JSON
                    if "narrative" in bug_text and bug_text.strip().startswith("Scene"):
                        logger.error("🔍 CONFIRMED: Raw JSON is being displayed with Scene prefix!")
                
                # Log all captured console messages
                logger.info("\n=== CAPTURED BROWSER CONSOLE LOGS ===")
                for msg in console_capture.messages:
                    logger.info(msg)
                logger.info("=== END CONSOLE LOGS ===\n")
                
                # Check for any JavaScript errors
                js_errors = [msg for msg in console_capture.messages if "[error]" in msg.lower()]
                if js_errors:
                    logger.error(f"JavaScript errors detected: {len(js_errors)}")
                    for error in js_errors:
                        logger.error(f"  JS Error: {error}")
                
                return True
            else:
                logger.error("Could not find input field")
                return False
                
        except Exception as e:
            logger.error(f"Test failed with error: {e}")
            page.screenshot(path=f"{SCREENSHOT_DIR}/error_state.png")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    logger.info("Starting JSON bug debug test")
    try:
        success = test_json_bug_display()
        if success:
            logger.info("✅ Test completed - check screenshots and logs")
            sys.exit(0)
        else:
            logger.error("❌ Test failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test crashed: {e}")
        sys.exit(1)