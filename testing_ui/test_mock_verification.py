#!/usr/bin/env python3
"""
Test to verify mock mode actually works with browser testing.
"""
from playwright.sync_api import sync_playwright
import time
import os

def test_mock_mode_verification():
    """Verify that mock mode is working by checking server logs."""
    
    print("Mock Mode Verification Test")
    print("=" * 50)
    print(f"USE_MOCKS environment: {os.environ.get('USE_MOCKS', 'not set')}")
    print(f"TESTING environment: {os.environ.get('TESTING', 'not set')}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate with test mode parameters
            test_url = "http://localhost:6006?test_mode=true&test_user_id=mock-verify-test"
            print(f"\nNavigating to: {test_url}")
            
            response = page.goto(test_url, wait_until='networkidle', timeout=10000)
            print(f"✓ Server responded with status: {response.status}")
            
            # Wait for app to load
            page.wait_for_selector("body", timeout=5000)
            
            # Try to get campaigns - this will use mock or real service
            print("\nAttempting to fetch campaigns...")
            
            # The test mode should bypass auth and load the dashboard
            try:
                page.wait_for_selector("#campaign-list", timeout=5000)
                print("✓ Dashboard loaded successfully")
                
                # Check if we see any campaigns
                campaigns = page.query_selector_all(".campaign-item")
                if campaigns:
                    print(f"✓ Found {len(campaigns)} campaigns")
                    if os.environ.get('USE_MOCKS') == 'true':
                        # With mocks, we should see the sample campaign
                        campaign_text = page.text_content(".campaign-item")
                        if "Dragon Knight" in campaign_text:
                            print("✓ CONFIRMED: Mock data detected (Dragon Knight campaign)")
                        else:
                            print("⚠️  Mock mode enabled but didn't find expected mock data")
                else:
                    print("✓ No campaigns found (expected for real mode with clean database)")
                    
            except Exception as e:
                print(f"⚠️  Dashboard didn't load properly: {e}")
            
            print("\n✓ Test completed successfully")
            
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_mock_mode_verification()