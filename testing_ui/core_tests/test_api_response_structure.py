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
from testing_ui.config import BASE_URL

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
            requests.get(f'{BASE_URL}/health')
            break
        except:
            if i == 9:
                print("Server failed to start!")
                sys.exit(1)
            time.sleep(1)
    
    try:
        # Create campaign
        response = requests.post(
            f'{BASE_URL}/api/campaigns',
            headers={
                'X-Test-Bypass-Auth': 'true',
                'X-Test-User-ID': 'test-123',
                'Content-Type': 'application/json'
            },
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
            f'{BASE_URL}/api/campaigns/{campaign_id}/interaction',
            headers={
                'X-Test-Bypass-Auth': 'true',
                'X-Test-User-ID': 'test-123',
                'Content-Type': 'application/json'
            },
            json={'input': 'I attack with my sword!', 'mode': 'character', 'debug_mode': True}
        )
        
        data = response.json()
        
        print("\n=== API RESPONSE STRUCTURE ===")
        print(f"Top-level keys: {sorted(data.keys())}")
        
        # Check specific fields
        print("\n=== FIELD LOCATIONS ===")
        fields_to_check = ['dice_rolls', 'resources', 'debug_info', 'planning_block', 'session_header', 'god_mode_response']
        
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
            else:
                print(f"\n❌ {field} MISSING from response")

        # 🔴 RED TEST: Test God Mode specifically
        print("\n=== 🔴 TESTING GOD MODE RESPONSE ===")
        god_response = requests.post(
            f'{BASE_URL}/api/campaigns/{campaign_id}/interaction',
            headers={
                'X-Test-Bypass-Auth': 'true',
                'X-Test-User-ID': 'test-123',
                'Content-Type': 'application/json'
            },
            json={'input': 'GOD_ASK_STATE', 'mode': 'character'}
        )
        
        if god_response.status_code == 200:
            god_data = god_response.json()
            if 'god_mode_response' in god_data:
                print(f"✅ PASS: god_mode_response found: {god_data['god_mode_response'][:100]}...")
            else:
                print("❌ FAIL: god_mode_response missing from God mode API response")
                print(f"Available fields: {sorted(god_data.keys())}")
        else:
            print(f"God mode request failed: {god_response.status_code} - {god_response.text}")
        
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