#!/usr/bin/env python3
"""Test structured fields API directly."""
import json
import requests
import time

# Test without starting server - assume it's already running
def test_api():
    print("Testing structured fields API...")
    
    headers = {
        'Content-Type': 'application/json',
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-Id': 'test-user-123'
    }
    
    # Create campaign
    response = requests.post(
        'http://localhost:8091/api/campaigns',
        headers=headers,
        json={'title': 'Test', 'prompt': 'Test', 'campaign_type': 'custom'}
    )
    
    if response.status_code != 201:
        print(f"Campaign creation failed: {response.status_code} - {response.text}")
        return
        
    campaign_id = response.json()['campaign_id']
    print(f"Created campaign: {campaign_id}")
    
    # Test interaction
    data = {
        'user_input': 'I attack with my sword!',
        'mode': 'character', 
        'debug_mode': True
    }
    
    response = requests.post(
        f'http://localhost:8091/api/campaigns/{campaign_id}/interaction',
        headers=headers,
        json=data
    )
    
    print(f"\nInteraction status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Top-level keys: {sorted(result.keys())}")
        
        # Check structured fields
        for field in ['dice_rolls', 'resources', 'debug_info']:
            if field in result:
                print(f"✓ {field} found at top level")
            else:
                print(f"✗ {field} NOT at top level")
                
        if 'debug_info' in result:
            print(f"\ndebug_info keys: {list(result['debug_info'].keys())}")
    else:
        print(f"Error: {response.text}")

if __name__ == '__main__':
    test_api()