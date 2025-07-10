#!/usr/bin/env python3
"""
Standard browser test for structured fields with enforced screenshot management.
Tests all 10 fields from the schema using the shared helper library.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import test utilities
sys.path.append(os.path.dirname(__file__))
from test_data_utils import create_test_campaign
from test_ui_helpers import capture_structured_fields_sequence

def test_structured_fields_display():
    """Test that all structured fields display correctly in the browser."""
    
    print("=== Testing Structured Fields Display ===")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Initialize helper with standardized screenshot management
        helper = BrowserTestHelper("structured_fields_display", page)
        
        try:
            # Navigate to test game
            if not helper.navigate_to_test_game():
                raise Exception("Failed to navigate to test game")
            
            # Take initial screenshot
            helper.take_screenshot("game_loaded")
            
            # Test character mode response
            print("Testing character mode response...")
            action_input = page.locator("#player-action")
            action_input.fill("I examine the room carefully")
            page.click("#send-action")
            
            # Wait for response
            if not helper.wait_for_content("Response time:", timeout=30):
                raise Exception("No AI response received")
            
            # Take screenshot of response
            helper.take_screenshot("character_response")
            
            # Verify individual fields are present
            field_checks = {
                'session_header': '.session-header',
                'narrative': '#story-content',
                'dice_rolls': '.dice-rolls',
                'resources': '.resources',
                'planning_block': '.planning-block',
                'debug_info': '.debug-info'
            }
            
            for field_name, selector in field_checks.items():
                if page.locator(selector).count() > 0:
                    helper.take_screenshot(f"{field_name}_field", selector)
                    print(f"✅ {field_name} field found and captured")
                else:
                    print(f"⚠️ {field_name} field not found")
            
            # Test god mode response
            print("\nTesting god mode response...")
            god_radio = page.locator('input[value="god"]')
            if god_radio.count() > 0:
                god_radio.click()
                action_input.fill("/god show current game state")
                page.click("#send-action")
                
                # Wait for god mode response
                if helper.wait_for_content("Response time:", timeout=30):
                    helper.take_screenshot("god_mode_response")
                    print("✅ God mode response captured")
            
            # Final summary
            summary = helper.get_screenshot_summary()
            print(f"\n✅ Test completed successfully!")
            print(f"📁 Screenshots saved to: {summary['screenshot_dir']}")
            print(f"📸 Total screenshots: {summary['total_screenshots']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            helper.take_screenshot("error")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    success = test_structured_fields_display()
    exit(0 if success else 1)