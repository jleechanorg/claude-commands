#!/usr/bin/env python3
"""
Integration test to verify structured fields end-to-end functionality.
"""
import os
import sys
import requests
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_structured_fields_api():
    """Test structured fields via the actual API endpoints."""
    print("Testing structured fields via API...")
    
    base_url = "http://localhost:6006"
    headers = {
        "Content-Type": "application/json",
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": "integration-test-user"
    }
    
    # 1. Create a campaign with debug mode enabled
    campaign_data = {
        "title": "Structured Fields Test Campaign",
        "prompt": "A warrior tests structured fields",
        "genre": "Fantasy",
        "tone": "Epic",
        "selected_prompts": ["game_state_instruction.md"],
        "character_name": "Test Warrior",
        "character_background": "A brave warrior for testing",
        "debug_mode": True
    }
    
    try:
        # Create campaign
        response = requests.post(f"{base_url}/api/campaigns", json=campaign_data, headers=headers)
        if response.status_code != 201:
            print(f"❌ Failed to create campaign: {response.status_code} - {response.text}")
            return False
        
        campaign_id = response.json().get("campaign_id")
        print(f"✓ Created campaign: {campaign_id}")
        
        # 2. Send an interaction to generate AI response with structured fields
        interaction_data = {
            "input": "I attack the goblin with my sword! Roll for attack and damage."
        }
        
        interaction_response = requests.post(
            f"{base_url}/api/campaigns/{campaign_id}/interaction",
            json=interaction_data,
            headers=headers
        )
        
        if interaction_response.status_code != 200:
            print(f"❌ Interaction failed: {interaction_response.status_code} - {interaction_response.text}")
            return False
        
        interaction_data = interaction_response.json()
        print("✓ Interaction successful")
        
        # Check if structured fields are in the response
        fields_in_response = []
        if interaction_data.get('session_header'):
            fields_in_response.append('session_header')
        if interaction_data.get('planning_block'):
            fields_in_response.append('planning_block')
        if interaction_data.get('dice_rolls'):
            fields_in_response.append('dice_rolls')
        if interaction_data.get('resources'):
            fields_in_response.append('resources')
        if interaction_data.get('debug_info'):
            fields_in_response.append('debug_info')
        
        print(f"✓ Structured fields in interaction response: {fields_in_response}")
        
        # 3. Fetch the campaign to see if structured fields are stored
        get_response = requests.get(f"{base_url}/api/campaigns/{campaign_id}", headers=headers)
        
        if get_response.status_code != 200:
            print(f"❌ GET campaign failed: {get_response.status_code} - {get_response.text}")
            return False
        
        campaign_data = get_response.json()
        story_entries = campaign_data.get('story', [])
        
        print(f"✓ Retrieved campaign with {len(story_entries)} story entries")
        
        # Find AI story entries and check for structured fields
        ai_entries_with_fields = []
        for entry in story_entries:
            if entry.get('actor') == 'gemini':
                fields_found = []
                if entry.get('session_header'):
                    fields_found.append('session_header')
                if entry.get('planning_block'):
                    fields_found.append('planning_block')
                if entry.get('dice_rolls'):
                    fields_found.append('dice_rolls')
                if entry.get('resources'):
                    fields_found.append('resources')
                if entry.get('debug_info'):
                    fields_found.append('debug_info')
                
                if fields_found:
                    ai_entries_with_fields.append({
                        'text_preview': entry.get('text', '')[:50] + '...',
                        'fields': fields_found
                    })
        
        print(f"✓ AI entries with structured fields: {len(ai_entries_with_fields)}")
        for entry in ai_entries_with_fields:
            print(f"  - {entry['text_preview']} -> {entry['fields']}")
        
        # Check if any structured fields were persisted
        if ai_entries_with_fields:
            print("✅ SUCCESS: Structured fields are being stored and retrieved!")
            return True
        else:
            print("❌ FAILURE: No structured fields found in stored story entries")
            
            # Debug: Show what fields ARE in the story entries
            sample_ai_entry = None
            for entry in story_entries:
                if entry.get('actor') == 'gemini':
                    sample_ai_entry = entry
                    break
            
            if sample_ai_entry:
                print(f"🔍 Sample AI entry fields: {list(sample_ai_entry.keys())}")
                print(f"🔍 Sample AI entry: {json.dumps(sample_ai_entry, indent=2)[:500]}...")
            
            return False
    
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        return False

if __name__ == "__main__":
    print("Structured Fields Integration Test")
    print("=" * 50)
    print("Make sure server is running: TESTING=true PORT=6006 python main.py serve")
    print()
    
    success = test_structured_fields_api()
    
    if success:
        print("\n🎉 Integration test PASSED")
    else:
        print("\n💥 Integration test FAILED")
        sys.exit(1)