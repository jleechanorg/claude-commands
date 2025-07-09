#!/usr/bin/env python3
"""
Test UI display of structured fields using proper test mode.
This test uses the ?test_mode=true URL parameter to bypass authentication.
"""
import time
from playwright.sync_api import sync_playwright
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_structured_fields_display():
    """Test that planning_block, session_header, dice_rolls, and resources are displayed."""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate with test mode enabled
            test_url = "http://localhost:6006?test_mode=true&test_user_id=ui-test-user"
            page.goto(test_url)
            print(f"✓ Navigated to app with test mode: {test_url}")
            
            # Wait for test mode to initialize
            page.wait_for_function("window.testAuthBypass !== undefined", timeout=5000)
            print("✓ Test mode initialized")
            
            # Should go directly to dashboard - wait for campaign list
            page.wait_for_selector("#campaign-list", timeout=10000)
            print("✓ Dashboard loaded (auth bypassed)")
            
            # Create a new campaign
            page.click("button:has-text('Create New Campaign')")
            print("✓ Clicked create campaign")
            
            # Fill campaign form
            page.fill("#campaign-title", "UI Structure Test")
            page.fill("#campaign-genre", "Fantasy")
            page.fill("#campaign-tone", "Epic")
            page.fill("#character-name", "Test Hero")
            page.fill("#character-background", "Testing the UI display")
            
            # Submit
            page.click("button:has-text('Create Campaign')")
            print("✓ Submitted campaign creation")
            
            # Wait for story view
            page.wait_for_selector("#story-content", timeout=10000)
            print("✓ Story view loaded")
            
            # Wait for initial story
            page.wait_for_selector(".story-entry", timeout=10000)
            
            # Check initial display
            initial_entries = page.locator(".story-entry").all()
            print(f"✓ Found {len(initial_entries)} initial story entries")
            
            # Submit a player action
            page.fill("#user-input", "I look around the room and check my equipment")
            page.press("#user-input", "Enter")
            print("✓ Submitted player action")
            
            # Wait for AI response
            print("⏳ Waiting for AI response...")
            page.wait_for_function(
                "document.querySelector('#user-input').disabled === false",
                timeout=30000
            )
            
            # Give DOM time to update
            page.wait_for_timeout(2000)
            
            # Get all story entries
            all_entries = page.locator(".story-entry").all()
            print(f"\n✓ Total story entries: {len(all_entries)}")
            
            # Analyze the last AI response
            if all_entries:
                last_entry = all_entries[-1]
                last_html = last_entry.inner_html()
                
                print("\n=== Structured Fields Check ===")
                has_session_header = "session-header" in last_html
                has_planning_block = "planning-block" in last_html
                has_dice_rolls = "dice-rolls" in last_html
                has_resources = "resources" in last_html
                
                print(f"Session Header: {'✓ Found' if has_session_header else '✗ Not found'}")
                print(f"Planning Block: {'✓ Found' if has_planning_block else '✗ Not found'}")
                print(f"Dice Rolls: {'✓ Found' if has_dice_rolls else '✗ Not found'}")
                print(f"Resources: {'✓ Found' if has_resources else '✗ Not found'}")
                
                # Check specific content
                if has_session_header:
                    header = last_entry.locator(".session-header").inner_text()
                    print(f"\nSession Header Preview: {header[:100]}...")
                
                if has_planning_block:
                    planning = last_entry.locator(".planning-block").inner_text()
                    print(f"\nPlanning Block Preview: {planning[:150]}...")
                
                # Take screenshots
                page.screenshot(path="ui_test_success.png", full_page=True)
                print("\n✓ Screenshot saved: ui_test_success.png")
                
                # Print HTML sample for debugging
                print("\n=== Last Entry HTML Sample ===")
                print(last_html[:600] + "..." if len(last_html) > 600 else last_html)
                
            else:
                print("❌ No story entries found!")
                page.screenshot(path="ui_test_no_entries.png", full_page=True)
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="ui_test_error.png", full_page=True)
            raise
        finally:
            print("\n✓ Test complete. Browser will close in 5 seconds...")
            time.sleep(5)
            browser.close()

if __name__ == "__main__":
    print("=" * 60)
    print("UI Structure Display Test")
    print("Make sure server is running with: TESTING=true PORT=6006 python main.py serve")
    print("=" * 60)
    test_structured_fields_display()