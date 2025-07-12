#!/usr/bin/env python3
"""
Simple test to verify campaign_type is being passed correctly
"""
import requests
import json

def test_campaign_type_backend():
    """Test that campaign_type is received by backend"""
    print("🧪 Testing Campaign Type Transmission...")
    
    # Test data
    test_cases = [
        {
            "name": "Dragon Knight Campaign",
            "data": {
                "title": "Test Dragon Knight",
                "character": "Ser Arion", 
                "setting": "World of Assiah",
                "campaign_type": "dragon-knight",
                "selected_prompts": ["narrative"],
                "custom_options": ["defaultWorld"]
            }
        },
        {
            "name": "Custom Campaign",
            "data": {
                "title": "Test Custom",
                "character": "Custom Hero",
                "setting": "Custom World", 
                "campaign_type": "custom",
                "selected_prompts": ["narrative"],
                "custom_options": []
            }
        }
    ]
    
    headers = {
        "Content-Type": "application/json",
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": "test-campaign-type"
    }
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   Campaign Type: {test_case['data']['campaign_type']}")
        
        try:
            response = requests.post(
                "http://localhost:6007/api/campaigns",
                json=test_case['data'],
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"   ✅ Campaign created: {result.get('campaign_id')}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   💥 Error: {e}")

if __name__ == "__main__":
    test_campaign_type_backend()