#!/usr/bin/env python3
"""
Quick test to see the actual structure of the API response.
This will show us exactly where fields are located.
"""
import json
import requests
import subprocess
import time
import os
import signal
import sys

def test_api_structure():
    # Start test server
    print("Starting test server on port 8088...")
    env = os.environ.copy()
    env['TESTING'] = 'true'
    env['PORT'] = '8088'
    server = subprocess.Popen(
        ['python', 'mvp_site/main.py', 'serve'],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for server
    time.sleep(5)
    
    # Verify server is up
    for i in range(10):
        try:
            requests.get('http://localhost:8088/health')
            break
        except:
            if i == 9:
                print("Server failed to start!")
                sys.exit(1)
            time.sleep(1)
    
    try:
        # Create campaign
        response = requests.post(
            'http://localhost:8088/api/campaigns',
            headers={'X-Test-User-Id': 'test-123', 'Content-Type': 'application/json'},
            json={'title': 'Test', 'prompt': 'Test campaign', 'campaign_type': 'custom'}
        )
        campaign_data = response.json()
        print(f"Campaign creation response: {campaign_data}")
        if 'error' in campaign_data:
            print(f"Error creating campaign: {campaign_data['error']}")
            return
        campaign_id = campaign_data.get('campaign_id')
        
        # Test interaction
        response = requests.post(
            f'http://localhost:8088/api/campaigns/{campaign_id}/interaction',
            headers={'X-Test-User-Id': 'test-123', 'Content-Type': 'application/json'},
            json={'input_text': 'I attack with my sword!', 'mode': 'character', 'debug_mode': True}
        )
        
        data = response.json()
        
        print("\n=== API RESPONSE STRUCTURE ===")
        print(f"Top-level keys: {sorted(data.keys())}")
        
        # Check specific fields
        print("\n=== FIELD LOCATIONS ===")
        fields_to_check = ['dice_rolls', 'resources', 'debug_info', 'planning_block', 'session_header']
        
        for field in fields_to_check:
            if field in data:
                print(f"\n{field} at TOP LEVEL:")
                value = data[field]
                if isinstance(value, dict):
                    print(f"  Type: dict with keys: {list(value.keys())}")
                elif isinstance(value, list):
                    print(f"  Type: list with {len(value)} items")
                    if value:
                        print(f"  First item: {value[0]}")
                else:
                    print(f"  Type: {type(value).__name__}")
                    print(f"  Value: {repr(value)[:100]}")
        
        # Check debug_info contents
        if 'debug_info' in data and isinstance(data['debug_info'], dict):
            print("\n=== DEBUG_INFO CONTENTS ===")
            for key, value in data['debug_info'].items():
                print(f"{key}: {type(value).__name__} = {repr(value)[:100]}")
        
        # Show full response for manual inspection
        print("\n=== FULL RESPONSE (formatted) ===")
        print(json.dumps(data, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        os.kill(server.pid, signal.SIGTERM)
        server.wait()

if __name__ == '__main__':
    test_api_structure()