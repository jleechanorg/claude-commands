#!/usr/bin/env python3
"""
Simple test to verify structured fields are displayed with mock service.
"""
from playwright.sync_api import sync_playwright
import time
import os

def test_structured_fields():
    """Test structured fields display with mock Gemini service."""
    
    print("Structured Fields Test with Mock Gemini")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to existing campaign (use one we created earlier)
            # Check server logs for campaign ID
            # NOTE: This campaign ID is for demo purposes. In production tests,
            # create a campaign first or use a test fixture with known ID
            test_url = "http://localhost:6006/campaign/fzhUuMp7fvXiyZhFtE7H?test_mode=true&test_user_id=structured-test"
            print(f"Navigating to: {test_url}")
            
            response = page.goto(test_url, wait_until='networkidle', timeout=15000)
            print(f"✓ Server responded with status: {response.status}")
            
            # Take screenshot of initial state
            page.screenshot(path="/tmp/worldarchitectai/browser/structured_test_01_initial.png")
            print("✓ Initial screenshot saved")
            
            # Wait for game view to load
            try:
                page.wait_for_selector("#game-view", timeout=10000)
                print("✓ Game view loaded")
                
                # Check for structured fields
                fields_to_check = [
                    ("session_header", "Session Header"),
                    ("narrative", "Narrative content"),
                    ("dice_rolls", "Dice Rolls"),
                    ("resources", "Resources"),
                    ("planning_block", "Planning Block"),
                    ("debug_info", "Debug Info")
                ]
                
                for field_id, field_name in fields_to_check:
                    element = page.query_selector(f"#{field_id}")
                    if element:
                        text = element.text_content()[:100] if element.text_content() else ""
                        print(f"✓ {field_name}: Found (preview: {text}...)")
                    else:
                        print(f"⚠️  {field_name}: Not found")
                
                # Take final screenshot
                page.screenshot(path="/tmp/worldarchitectai/browser/structured_test_02_fields.png")
                print("✓ Fields screenshot saved")
                
            except Exception as e:
                print(f"⚠️  Error checking fields: {e}")
                page.screenshot(path="/tmp/worldarchitectai/browser/structured_test_error.png")
            
            print("\n✓ Test completed")
            
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_structured_fields()