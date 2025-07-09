#!/usr/bin/env python3
"""
Simple test to verify structured fields display in UI.
Focuses on the core issue: are planning blocks and other fields showing up?
"""
import time
from playwright.sync_api import sync_playwright
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_structured_display():
    """Simple test to check if structured fields are displayed."""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate with test mode
            test_url = "http://localhost:6006?test_mode=true&test_user_id=ui-test-123"
            page.goto(test_url)
            print(f"✓ Navigated to: {test_url}")
            
            # Wait a bit for page to load
            page.wait_for_timeout(2000)
            
            # Take screenshot of initial state
            page.screenshot(path="test_1_initial.png")
            
            # Look for campaign list
            if page.locator("#campaign-list").count() > 0:
                print("✓ Found campaign list")
                
                # Check for any button that creates campaigns
                buttons = page.locator("button").all()
                print(f"\nFound {len(buttons)} buttons:")
                for i, btn in enumerate(buttons[:10]):  # First 10 buttons
                    text = btn.inner_text().strip()
                    if text:
                        print(f"  Button {i}: '{text}'")
                
                # Look for campaign creation button with various texts
                create_btn = None
                for text in ["Create New Campaign", "Start New Campaign", "New Campaign", "+ New Campaign"]:
                    if page.locator(f"button:has-text('{text}')").count() > 0:
                        create_btn = page.locator(f"button:has-text('{text}')").first
                        print(f"\n✓ Found campaign button: '{text}'")
                        break
                
                if create_btn:
                    create_btn.click()
                    print("✓ Clicked create campaign button")
                    
                    # Wait for form
                    page.wait_for_timeout(1000)
                    
                    # Fill basic campaign info
                    if page.locator("#campaign-title").count() > 0:
                        page.fill("#campaign-title", "Test Structured Display")
                        page.fill("#campaign-genre", "Fantasy")
                        page.fill("#campaign-tone", "Epic")
                        print("✓ Filled campaign form")
                        
                        # Submit form - look for submit button
                        submit_btn = page.locator("button[type='submit']").or_(
                            page.locator("button:has-text('Create')").or_(
                                page.locator("button:has-text('Start')")
                            )
                        )
                        if submit_btn.count() > 0:
                            submit_btn.first.click()
                            print("✓ Submitted form")
                            
                            # Wait for story view
                            page.wait_for_timeout(3000)
                            page.screenshot(path="test_2_story_view.png")
                            
                            # Check story content
                            if page.locator("#story-content").count() > 0:
                                print("\n✓ In story view")
                                
                                # Submit a test message
                                if page.locator("#user-input").count() > 0:
                                    page.fill("#user-input", "I examine my surroundings carefully")
                                    page.press("#user-input", "Enter")
                                    print("✓ Sent test message")
                                    
                                    # Wait for response
                                    print("\n⏳ Waiting for AI response...")
                                    page.wait_for_timeout(10000)  # 10 seconds should be enough
                                    
                                    # Take screenshot
                                    page.screenshot(path="test_3_after_response.png", full_page=True)
                                    
                                    # Check story content
                                    story_html = page.locator("#story-content").inner_html()
                                    
                                    print("\n=== Checking for structured fields ===")
                                    checks = {
                                        "story-entry": "Story entry divs",
                                        "session-header": "Session header",
                                        "planning-block": "Planning block",
                                        "dice-rolls": "Dice rolls",
                                        "resources": "Resources section",
                                        "--- PLANNING BLOCK ---": "Planning block text",
                                        "What would you like to do": "Action prompt"
                                    }
                                    
                                    for check, name in checks.items():
                                        if check in story_html:
                                            print(f"✓ {name}: FOUND")
                                        else:
                                            print(f"✗ {name}: NOT FOUND")
                                    
                                    # Print last 1000 chars of story HTML
                                    print("\n=== Story HTML (last 1000 chars) ===")
                                    print("..." + story_html[-1000:])
                                    
                                    # Check console for errors
                                    console_msgs = []
                                    page.on("console", lambda msg: console_msgs.append(msg))
                                    if console_msgs:
                                        print("\n=== Console messages ===")
                                        for msg in console_msgs[-5:]:
                                            print(f"{msg.type}: {msg.text}")
                        
                else:
                    print("✗ Could not find campaign creation button")
                    print("Current page URL:", page.url)
            else:
                print("✗ Not on dashboard page")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="test_error.png", full_page=True)
            # Print page content for debugging
            print("\n=== Page content preview ===")
            print(page.content()[:1000])
            raise
        finally:
            print("\n✓ Test complete. Check screenshots:")
            print("  - test_1_initial.png")
            print("  - test_2_story_view.png")
            print("  - test_3_after_response.png")
            print("\nBrowser will stay open for 15 seconds...")
            time.sleep(15)
            browser.close()

if __name__ == "__main__":
    print("=" * 60)
    print("UI Structured Fields Display Test")
    print("=" * 60)
    test_structured_display()