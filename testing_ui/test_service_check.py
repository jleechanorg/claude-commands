#!/usr/bin/env python3
"""Quick test to verify which services are being used in test mode."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from playwright.sync_api import sync_playwright
import time

def test_service_verification():
    """Verify which services are being used."""
    
    print(f"Environment variables:")
    print(f"  TESTING = {os.environ.get('TESTING', 'not set')}")
    print(f"  USE_MOCKS = {os.environ.get('USE_MOCKS', 'not set')}")
    print(f"  GEMINI_API_KEY = {'set' if os.environ.get('GEMINI_API_KEY') else 'not set'}")
    print(f"  PORT = {os.environ.get('PORT', 'not set')}")
    
    # Check if we can import the services
    try:
        from mvp_site import gemini_service
        print("\n✓ Gemini service imported successfully")
        
        # Check if it's using real API key
        if os.environ.get('GEMINI_API_KEY'):
            print("  → Using REAL Gemini API (API key is set)")
        else:
            print("  → No Gemini API key set")
            
    except Exception as e:
        print(f"\n✗ Failed to import gemini_service: {e}")
    
    try:
        import firebase_admin
        print("\n✓ Firebase admin imported successfully")
        if firebase_admin._apps:
            print("  → Firebase is initialized (REAL Firebase)")
        else:
            print("  → Firebase not yet initialized")
    except Exception as e:
        print(f"\n✗ Failed to import firebase_admin: {e}")
    
    # Quick browser test to check server response
    print("\n\nChecking server response with browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate with test mode parameters
        test_url = "http://localhost:6006?test_mode=true&test_user_id=test-service-check"
        print(f"Navigating to: {test_url}")
        
        try:
            response = page.goto(test_url, wait_until='networkidle', timeout=10000)
            print(f"✓ Server responded with status: {response.status}")
            
            # Check if we can see the main app
            title = page.title()
            print(f"✓ Page title: {title}")
            
        except Exception as e:
            print(f"✗ Failed to load page: {e}")
        
        browser.close()

if __name__ == "__main__":
    test_service_verification()