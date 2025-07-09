#!/usr/bin/env python3
"""
Simple test to check UI display of structured fields.
"""
import time
from playwright.sync_api import sync_playwright
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_simple_ui_check():
    """Simple test to see what's displayed in the UI."""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Go directly to a campaign if one exists, or create via API
            page.goto("http://localhost:6006")
            page.wait_for_load_state("networkidle")
            
            # Check current page
            print("Current URL:", page.url)
            print("Page title:", page.title)
            
            # Take initial screenshot
            page.screenshot(path="simple_test_1.png")
            
            # Look for campaign elements
            if page.locator("#story-content").count() > 0:
                print("✓ Found story content area")
                
                # Check if there's existing content
                story_html = page.locator("#story-content").inner_html()
                if story_html.strip():
                    print("✓ Story has content")
                    print("\n=== Current Story Content ===")
                    print(story_html[:500] + "..." if len(story_html) > 500 else story_html)
                else:
                    print("Story content is empty")
                
                # Try to submit a message if we're in a campaign
                if page.locator("#user-input").count() > 0:
                    print("✓ Found user input field")
                    
                    # Type and send a message
                    page.fill("#user-input", "I examine my surroundings carefully")
                    page.screenshot(path="simple_test_2_before_send.png")
                    
                    page.press("#user-input", "Enter")
                    print("✓ Sent user input")
                    
                    # Wait for response
                    print("Waiting for AI response...")
                    time.sleep(5)  # Give it time
                    
                    # Check for new content
                    new_story_html = page.locator("#story-content").inner_html()
                    print("\n=== Story Content After Input ===")
                    print(new_story_html)
                    
                    # Specifically check for our new elements
                    last_entries = page.locator(".story-entry").all()
                    if last_entries:
                        last_entry_html = last_entries[-1].inner_html()
                        print("\n=== Last Story Entry ===")
                        print(last_entry_html)
                        
                        # Check for specific elements
                        print("\n=== Element Check ===")
                        print(f"Has .session-header: {'session-header' in last_entry_html}")
                        print(f"Has .planning-block: {'planning-block' in last_entry_html}")
                        print(f"Has .dice-rolls: {'dice-rolls' in last_entry_html}")
                        print(f"Has .resources: {'resources' in last_entry_html}")
                    
                    page.screenshot(path="simple_test_3_after_response.png", full_page=True)
                    
            else:
                print("Not on a campaign page")
                print("Page content preview:")
                print(page.content()[:1000])
                
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="simple_test_error.png", full_page=True)
        finally:
            # Keep browser open for manual inspection
            print("\n✓ Test complete. Browser will stay open for 10 seconds...")
            time.sleep(10)
            browser.close()

if __name__ == "__main__":
    test_simple_ui_check()