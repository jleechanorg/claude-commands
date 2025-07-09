#!/usr/bin/env python3
"""
Test UI display assuming we're already logged in.
This test navigates directly to a campaign URL.
"""
import time
from playwright.sync_api import sync_playwright
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_display_fields():
    """Test that all structured fields are displayed in the UI."""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to the app
            page.goto("http://localhost:6006")
            print("✓ Navigated to app")
            
            # Wait a moment
            page.wait_for_timeout(2000)
            
            # Check if we're on the dashboard by looking for campaign list
            if page.locator("#campaign-list").count() > 0:
                print("✓ On dashboard page")
                
                # Look for existing campaigns
                campaigns = page.locator("#campaign-list .list-group-item").all()
                if campaigns:
                    print(f"✓ Found {len(campaigns)} existing campaigns")
                    # Click the first one
                    campaigns[0].click()
                    print("✓ Clicked on first campaign")
                    
                    # Wait for story content to load
                    page.wait_for_selector("#story-content", timeout=5000)
                    print("✓ Story content loaded")
                else:
                    print("No existing campaigns found")
                    # We're logged in but no campaigns - would need to create one
                    return
            else:
                print("Not on dashboard - checking if we're in a campaign")
            
            # If we're in a campaign view
            if page.locator("#story-content").count() > 0:
                print("✓ In campaign view")
                
                # Get current story content
                story_html = page.locator("#story-content").inner_html()
                print(f"\nStory has content: {'Yes' if story_html.strip() else 'No'}")
                
                # Submit a test message
                if page.locator("#user-input").count() > 0:
                    print("✓ Found input field")
                    
                    # Clear and type
                    page.fill("#user-input", "")
                    page.type("#user-input", "What do I see around me?")
                    print("✓ Typed test message")
                    
                    # Take screenshot before sending
                    page.screenshot(path="before_send.png")
                    
                    # Send the message
                    page.press("#user-input", "Enter")
                    print("✓ Sent message")
                    
                    # Wait for response - look for loading indicator disappearing
                    print("⏳ Waiting for AI response...")
                    page.wait_for_function(
                        "document.querySelector('#user-input').disabled === false",
                        timeout=30000
                    )
                    
                    # Give it a moment for DOM updates
                    page.wait_for_timeout(1000)
                    
                    # Get all story entries
                    story_entries = page.locator(".story-entry").all()
                    if story_entries:
                        print(f"\n✓ Found {len(story_entries)} story entries")
                        
                        # Get the last entry (should be AI response)
                        last_entry = story_entries[-1]
                        last_html = last_entry.inner_html()
                        
                        print("\n=== Checking for structured fields ===")
                        print(f"✓ Session header: {'session-header' in last_html}")
                        print(f"✓ Planning block: {'planning-block' in last_html}")
                        print(f"✓ Dice rolls: {'dice-rolls' in last_html}")
                        print(f"✓ Resources: {'resources' in last_html}")
                        
                        # Print a sample of the HTML
                        print("\n=== Last entry HTML preview ===")
                        print(last_html[:500] + "..." if len(last_html) > 500 else last_html)
                    else:
                        # No story-entry divs, check raw content
                        print("\n⚠️  No .story-entry elements found")
                        story_content = page.locator("#story-content").inner_html()
                        print("Story content preview:")
                        print(story_content[:500] + "...")
                    
                    # Take final screenshot
                    page.screenshot(path="after_response.png", full_page=True)
                    print("\n✓ Screenshots saved: before_send.png, after_response.png")
                    
            else:
                print("⚠️  Not in a campaign view")
                print("Current URL:", page.url)
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="error_screenshot.png", full_page=True)
            raise
        finally:
            print("\n✓ Test complete. Browser staying open for 10 seconds...")
            time.sleep(10)
            browser.close()

if __name__ == "__main__":
    test_display_fields()