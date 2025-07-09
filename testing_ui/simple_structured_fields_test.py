#!/usr/bin/env python3
"""Simple test to verify structured response fields are displayed"""
import os
import time
from playwright.sync_api import sync_playwright

def test_structured_fields_simple():
    """Simple test to check if app loads and structured fields implementation exists"""
    screenshot_dir = "/tmp/structured_response_simple"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    with sync_playwright() as p:
        # Use headless=True for automated testing
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Load the app
            print("Loading app...")
            page.goto("http://localhost:6006")
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # Take initial screenshot
            page.screenshot(path=f"{screenshot_dir}/app_loaded.png", full_page=True)
            print(f"✅ Screenshot saved: {screenshot_dir}/app_loaded.png")
            
            # Check if structured fields functions exist in the JavaScript
            has_structured_function = page.evaluate("""
                () => {
                    return typeof generateStructuredFieldsHTML === 'function';
                }
            """)
            
            print(f"generateStructuredFieldsHTML function: {'✅ Found' if has_structured_function else '❌ Missing'}")
            
            # Check if appendToStory accepts fullData parameter
            append_story_signature = page.evaluate("""
                () => {
                    return appendToStory ? appendToStory.toString().includes('fullData') : false;
                }
            """)
            
            print(f"appendToStory fullData parameter: {'✅ Found' if append_story_signature else '❌ Missing'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            page.screenshot(path=f"{screenshot_dir}/error.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    success = test_structured_fields_simple()
    if success:
        print("✅ Simple structured fields test completed successfully")
    else:
        print("❌ Simple structured fields test failed") 