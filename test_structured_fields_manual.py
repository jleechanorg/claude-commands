#!/usr/bin/env python3
"""
Manual test to verify structured fields are working in the interaction endpoint
"""
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mvp_site'))

from main import create_app, DEFAULT_TEST_USER, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID

def test_structured_fields_integration():
    """Test that structured fields are properly extracted and returned"""
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Test headers for authentication bypass
    test_headers = {
        HEADER_TEST_BYPASS: 'true',
        HEADER_TEST_USER_ID: DEFAULT_TEST_USER
    }
    
    campaign_id = 'test-campaign-123'
    
    # Make a request to the interaction endpoint
    response = client.post(
        f'/api/campaigns/{campaign_id}/interaction',
        headers=test_headers,
        json={'input': 'I attack the goblin!'}
    )
    
    print(f"Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error response: {response.data.decode('utf-8')}")
        return False
    
    # Parse response data
    response_data = json.loads(response.data.decode('utf-8'))
    
    print("\nResponse structure:")
    print(json.dumps(response_data, indent=2))
    
    # Check if structured_fields are present
    if 'structured_fields' in response_data:
        print("\n✅ structured_fields found in response!")
        structured_fields = response_data['structured_fields']
        print(f"Structured fields: {json.dumps(structured_fields, indent=2)}")
        return True
    else:
        print("\n❌ structured_fields not found in response")
        available_keys = list(response_data.keys())
        print(f"Available keys: {available_keys}")
        return False

if __name__ == '__main__':
    success = test_structured_fields_integration()
    sys.exit(0 if success else 1)