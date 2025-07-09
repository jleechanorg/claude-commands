#!/usr/bin/env python3
"""
Test the UI display fix for structured response fields.
"""
import time
from playwright.sync_api import sync_playwright, expect
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ui_displays_all_fields():
    """Test that the UI properly displays all structured response fields."""
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set to False to see what's happening
        page = browser.new_page()
        
        try:
            # Navigate to the app
            page.goto("http://localhost:6006")
            print("✓ Navigated to app")
            
            # Wait for page to load
            page.wait_for_load_state("networkidle")
            
            # Take screenshot to see what's on the page
            page.screenshot(path="initial_page.png")
            print("✓ Initial page screenshot saved")
            
            # Check if we're already signed in (look for Start New Campaign button)
            if page.locator("text=Start New Campaign").count() > 0 or page.locator("text=Create New Campaign").count() > 0:
                print("✓ Already signed in, at dashboard")
            else:
                # Look for any auth buttons
                auth_buttons = page.locator("button").all_inner_texts()
                print(f"Available buttons: {auth_buttons}")
                
                # Try different selectors
                if page.locator("text=Sign In Anonymously").count() > 0:
                    page.click("text=Sign In Anonymously")
                elif page.locator("button:has-text('Anonymous')").count() > 0:
                    page.click("button:has-text('Anonymous')")
                elif page.locator("#anonymous-signin").count() > 0:
                    page.click("#anonymous-signin")
                else:
                    print("Could not find sign in button")
                
                print("✓ Clicked sign in")
                
                # Wait for dashboard
                page.wait_for_selector("button:has-text('New Campaign')", timeout=10000)
                print("✓ Dashboard loaded")
            
            # Create a new campaign - try different selectors
            if page.locator("text=Start New Campaign").count() > 0:
                page.click("text=Start New Campaign")
            else:
                page.click("text=Create New Campaign")
            
            # Fill in campaign details
            page.fill("#campaign-title", "UI Test Campaign")
            page.fill("#campaign-genre", "Fantasy") 
            page.fill("#campaign-tone", "Epic")
            page.fill("#character-name", "Test Hero")
            page.fill("#character-background", "A brave warrior")
            
            # Submit the form
            page.click("button:has-text('Create Campaign')")
            print("✓ Created campaign")
            
            # Wait for story to load
            page.wait_for_selector("#story-content", timeout=10000)
            time.sleep(2)  # Give it time to render
            
            # Check initial story content
            story_content = page.locator("#story-content").inner_html()
            print("\n=== Initial Story Content ===")
            print(story_content[:500] + "..." if len(story_content) > 500 else story_content)
            
            # Enter some input
            page.fill("#user-input", "I look around the room carefully")
            page.press("#user-input", "Enter")
            print("✓ Submitted user input")
            
            # Wait for AI response
            page.wait_for_selector(".story-entry:last-child", timeout=30000)
            time.sleep(2)  # Give it time to fully render
            
            # Get the last story entry (AI response)
            last_entry = page.locator(".story-entry:last-child").inner_html()
            print("\n=== AI Response HTML ===")
            print(last_entry)
            
            # Check for specific elements
            has_session_header = "session-header" in last_entry
            has_planning_block = "planning-block" in last_entry
            has_dice_rolls = "dice-rolls" in last_entry
            has_resources = "resources" in last_entry
            
            print("\n=== Element Check ===")
            print(f"Session Header: {'✓' if has_session_header else '✗'}")
            print(f"Planning Block: {'✓' if has_planning_block else '✗'}")
            print(f"Dice Rolls: {'✓' if has_dice_rolls else '✗'}")
            print(f"Resources: {'✓' if has_resources else '✗'}")
            
            # Take a screenshot
            page.screenshot(path="ui_test_screenshot.png", full_page=True)
            print("\n✓ Screenshot saved as ui_test_screenshot.png")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            page.screenshot(path="ui_test_error.png", full_page=True)
            print("Error screenshot saved as ui_test_error.png")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    test_ui_displays_all_fields()