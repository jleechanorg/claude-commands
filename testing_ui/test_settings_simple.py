#!/usr/bin/env python3
"""
Simple browser test to debug settings page loading
"""

from playwright.sync_api import sync_playwright
import os

def test_settings_simple():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        try:
            # Navigate directly to settings with test auth
            url = "http://localhost:6006/settings?test_mode=true&test_user_id=test-user"
            print(f"Navigating to: {url}")
            page.goto(url)
            
            # Wait for page load
            page.wait_for_load_state("networkidle")
            
            # Take screenshot
            os.makedirs("testing_ui/test_results", exist_ok=True)
            page.screenshot(path="testing_ui/test_results/simple_settings_test.png")
            
            # Print page content
            print("\nPage HTML:")
            print("=" * 50)
            print(page.content()[:1000])
            print("=" * 50)
            
            # Check for key elements
            print(f"\nPage title: '{page.title()}'")
            print(f"URL: {page.url}")
            
            # Check what we can find
            try:
                if page.locator("text=Settings").count() > 0:
                    print("✅ 'Settings' text found")
                else:
                    print("❌ 'Settings' text NOT found")
                    
                if page.locator("input[name='geminiModel']").count() > 0:
                    print(f"✅ Found {page.locator('input[name=\"geminiModel\"]').count()} radio buttons")
                else:
                    print("❌ Radio buttons NOT found")
                    
                # Check if any h3 elements exist
                h3_count = page.locator("h3").count()
                print(f"Found {h3_count} h3 elements")
                
                if h3_count > 0:
                    for i in range(h3_count):
                        h3_text = page.locator("h3").nth(i).text_content()
                        print(f"  H3 #{i}: '{h3_text}'")
                        
            except Exception as e:
                print(f"Error checking elements: {e}")
                
            input("\nPress Enter to close browser...")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_settings_simple()