#!/usr/bin/env python3
"""
Simple API test focusing on capturing the actual form submission
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json

# Import test utilities
sys.path.append(os.path.dirname(__file__))
from test_ui_util import run_ui_test, navigate_to_page, fill_wizard_step1, navigate_wizard_to_step, enable_console_logging
from test_ui_helpers import wait_and_click

def test_wizard_api_simple(page, test_name):
    """Simple test to capture wizard API submission"""
    
    print("🔍 SIMPLE API TEST: Checking wizard data submission")
    
    # Enable console logging for debugging
    enable_console_logging(page)
    
    # Track API calls manually for detailed logging
    api_calls = []
    
    def capture_request(request):
        if "api/campaigns" in request.url and request.method == "POST":
            try:
                data = json.loads(request.post_data) if request.post_data else {}
                api_calls.append({
                    'url': request.url,
                    'data': data
                })
                print(f"\n✅ CAPTURED API CALL!")
                print(f"  URL: {request.url}")
                print(f"  Data: {json.dumps(data, indent=2)}")
            except Exception as e:
                print(f"Error parsing request: {e}")
    
    # Set up response capture too
    def capture_response(response):
        if "api/campaigns" in response.url:
            print(f"\n📥 API Response: {response.status}")
    
    page.on("request", capture_request)
    page.on("response", capture_response)
    
    # Navigate to new campaign page
    navigate_to_page(page, "new-campaign", port=6006)
    
    print("\n1️⃣ Filling Step 1...")
    fill_wizard_step1(page, 
                     title="API Test Campaign",
                     campaign_type="custom",
                     character="Astarion who ascended",
                     setting="Baldur's Gate 3 World")
    
    # Navigate through wizard steps
    print("2️⃣ Going to Step 2...")
    navigate_wizard_to_step(page, 2, current_step=1)
    
    print("3️⃣ Going to Step 3...")
    navigate_wizard_to_step(page, 3, current_step=2)
    
    print("4️⃣ Going to Step 4...")
    navigate_wizard_to_step(page, 4, current_step=3)
    
    # Step 4 - Submit
    print("🚀 Submitting campaign...")
    
    # Try to click the wizard button (not the hidden form button)
    if not wait_and_click(page, "#launch-campaign", timeout=5000):
        # Fallback to JavaScript click
        page.evaluate("document.getElementById('launch-campaign').click()")
        print("✅ Used JavaScript click as fallback")
    else:
        print("✅ Clicked wizard Begin Adventure button")
    
    # Wait for API call
    page.wait_for_timeout(3000)
    
    # Analyze results
    print("\n📊 FINAL ANALYSIS:")
    success = False
    if api_calls:
        for call in api_calls:
            data = call['data']
            print(f"\n✅ API Request contained:")
            print(f"  - title: '{data.get('title')}'")
            print(f"  - character: '{data.get('character')}'")
            print(f"  - setting: '{data.get('setting')}'")
            print(f"  - campaignType: '{data.get('campaignType')}'")
            
            # Check if character and setting were sent
            if 'character' in data and 'setting' in data:
                print(f"\n🎉 SUCCESS! Character and setting are sent as separate fields!")
                if data['character'] == 'Astarion who ascended' and data['setting'] == "Baldur's Gate 3 World":
                    print("✅ Values match what we entered!")
                    success = True
                else:
                    print("⚠️ Values don't match:")
                    print(f"   Expected character: 'Astarion who ascended', got: '{data['character']}'")
                    print(f"   Expected setting: 'Baldur's Gate 3 World', got: '{data['setting']}'")
            else:
                print("\n❌ Character and setting were NOT sent as separate fields")
                print("Actual fields sent:", list(data.keys()))
    else:
        print("❌ No API calls were captured")
    
    # Keep browser open for 5 seconds to see result
    page.wait_for_timeout(5000)
    
    return success

if __name__ == "__main__":
    # Run the test using the test runner
    run_ui_test(test_wizard_api_simple, "wizard_api_simple", headless=False, port=6006)