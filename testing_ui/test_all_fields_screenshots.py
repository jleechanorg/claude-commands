#!/usr/bin/env python3
"""
Comprehensive test to capture screenshots for every structured field from the schema.
This test demonstrates all 10 fields from game_state_instruction.md working in the UI.
Uses the shared browser_test_helpers library for standardized screenshot management.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from testing_ui.browser_test_helpers import BrowserTestHelper, create_test_campaign

def test_all_structured_fields():
    """Test that captures screenshots of all structured fields in action."""
    
    print("=== Testing All Structured Fields Screenshots ===")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Initialize helper with standardized screenshot management
        helper = BrowserTestHelper("structured_fields_comprehensive", page)
        
        try:
            # Navigate to test application and take initial screenshot
            page.goto("http://localhost:6006?test_mode=true&test_user_id=test-user-123")
            
            # Wait for dashboard to load
            if not helper.wait_for_element("text='My Campaigns'", timeout=10):
                raise Exception("Dashboard failed to load")
            
            helper.take_screenshot("full_page")
            
            # Look for existing test campaign or create one
            campaign_name = "All Fields Test Campaign"
            try:
                page.click(f"text='{campaign_name}'", timeout=5000)
            except:
                # Campaign doesn't exist, create it
                print("Creating test campaign...")
                if not create_test_campaign(page, campaign_name):
                    raise Exception("Failed to create test campaign")
            
            # Wait for game view to load
            if not helper.wait_for_element("#game-view", timeout=30):
                raise Exception("Game view failed to load")
            
            helper.take_screenshot("initial_campaign")
            
            # Use helper's structured fields capture sequence
            screenshots = helper.capture_structured_fields_sequence("I attack the goblin")
            
            # Print summary
            summary = helper.get_screenshot_summary()
            print(f"\n✅ Test completed successfully!")
            print(f"📁 Screenshots saved to: {summary['screenshot_dir']}")
            print(f"📸 Total screenshots: {summary['total_screenshots']}")
            print(f"🗂️ Files: {', '.join(summary['directory_listing'])}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            helper.take_screenshot("error")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    test_all_structured_fields()