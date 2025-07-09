#!/usr/bin/env python3
"""Manual test to verify structured fields display in UI"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_structured_fields():
    """Test that structured fields are displayed in the UI"""
    print("Testing structured fields display...")
    
    # First get a valid token by navigating to the site
    print("\n1. Please open your browser and navigate to: http://localhost:8080")
    print("2. Sign in with Google")
    print("3. Open browser DevTools (F12)")
    print("4. Go to Application/Storage -> Local Storage -> http://localhost:8080")
    print("5. Find the 'id_token' value")
    
    token = input("\nPaste the id_token value here: ").strip()
    
    if not token:
        print("No token provided, exiting")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Create a test campaign
    print("\nCreating test campaign...")
    campaign_data = {
        'title': 'Structured Fields Test',
        'campaign_prompt': 'You are in a goblin cave. There are 3 goblins here.'
    }
    
    response = requests.post(f'{BASE_URL}/api/campaigns', json=campaign_data, headers=headers)
    if response.status_code != 200:
        print(f"Failed to create campaign: {response.status_code} - {response.text}")
        return
    
    campaign_id = response.json()['id']
    print(f"Created campaign: {campaign_id}")
    
    # Send an interaction with debug mode on
    print("\nSending test interaction with debug_mode=True...")
    interaction_data = {
        'action': 'I attack the nearest goblin with my sword!',
        'mode': 'action',
        'debug_mode': True
    }
    
    response = requests.post(f'{BASE_URL}/api/campaigns/{campaign_id}/interact', 
                           json=interaction_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Interaction failed: {response.status_code} - {response.text}")
        return
    
    result = response.json()
    print("\nAPI Response contains:")
    print(f"- narrative: {'✓' if 'narrative' in result else '✗'}")
    print(f"- entities_mentioned: {'✓' if 'entities_mentioned' in result else '✗'}")
    print(f"- location_confirmed: {'✓' if 'location_confirmed' in result else '✗'}")
    print(f"- debug_info: {'✓' if 'debug_info' in result else '✗'}")
    print(f"- god_mode_response: {'✓' if 'god_mode_response' in result else '✗'}")
    
    if 'debug_info' in result and result['debug_info']:
        print("\ndebug_info contains:")
        for key, value in result['debug_info'].items():
            print(f"  - {key}: {type(value).__name__}")
            if isinstance(value, list) and value:
                print(f"    Example: {value[0]}")
    
    print(f"\n✅ Now check the browser at: {BASE_URL}/#/campaigns/{campaign_id}")
    print("\nYou should see:")
    print("- The narrative text")
    print("- 🎲 Dice Rolls section (if any rolls were made)")
    print("- 📊 Resources section")
    print("- 👥 Entities section (showing 'goblin')")
    print("- 📍 Location section")
    print("- 🔧 State Updates section (in debug mode)")
    print("- 📝 DM Notes section (if any)")
    
    # Test god mode
    print("\n\nTesting god mode response...")
    god_mode_data = {
        'action': 'What are the goblins stats?',
        'mode': 'god',
        'debug_mode': True
    }
    
    response = requests.post(f'{BASE_URL}/api/campaigns/{campaign_id}/interact', 
                           json=god_mode_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if 'god_mode_response' in result:
            print("✅ God mode response received")
            print("\nCheck the browser - you should see:")
            print("- 🔮 God Mode section with the response")
        else:
            print("⚠️  No god_mode_response field in response")
    
if __name__ == "__main__":
    test_structured_fields()