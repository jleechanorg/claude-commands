#!/usr/bin/env python3
"""
Test API schema compliance directly without browser complexity
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8080"
TEST_HEADERS = {
    "X-Test-Bypass-Auth": "true",
    "X-Test-User-ID": "test-schema",
    "Content-Type": "application/json"
}

def test_api_schema_compliance():
    """Test that API responses follow game_state_instruction.md schema"""
    
    # 1. Create a test campaign
    print("1. Creating test campaign...")
    campaign_data = {
        "title": "Schema Test Campaign",
        "prompt": "Test campaign for schema compliance",
        "campaign_type": "custom"
    }
    
    resp = requests.post(
        f"{BASE_URL}/api/campaigns",
        headers=TEST_HEADERS,
        json=campaign_data
    )
    
    if resp.status_code != 201:
        print(f"❌ Failed to create campaign: {resp.status_code}")
        print(resp.text)
        return False
    
    campaign_id = resp.json()["campaign_id"]
    print(f"✅ Created campaign: {campaign_id}")
    
    # 2. Send interaction to get structured response
    print("\n2. Sending test interaction...")
    interaction_data = {
        "input": "I attack the goblin with my sword! Roll for attack and damage.",
        "mode": "character",
        "debug_mode": True
    }
    
    resp = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interaction",
        headers=TEST_HEADERS,
        json=interaction_data
    )
    
    if resp.status_code != 200:
        print(f"❌ Interaction failed: {resp.status_code}")
        print(resp.text)
        return False
    
    response_data = resp.json()
    print("✅ Received AI response")
    
    # 3. Check schema compliance
    print("\n3. Checking schema compliance...")
    
    # Expected fields from game_state_instruction.md
    schema_fields = {
        'narrative': 'Main story text (currently sent as "response")',
        'session_header': 'Session header with timestamp/location/status',
        'planning_block': 'Planning block with options',
        'dice_rolls': 'List of dice roll strings',
        'resources': 'Resource string (HD, spells, etc)',
        'entities_mentioned': 'List of mentioned entities',
        'location_confirmed': 'Current location',
        'state_updates': 'State change object',
        'debug_info': 'Debug information object'
    }
    
    print("\n📋 Schema Field Analysis:")
    compliance_issues = []
    
    for field, description in schema_fields.items():
        if field in response_data:
            print(f"   ✅ {field}: Present")
            # Check field types
            if field == 'dice_rolls' and not isinstance(response_data[field], list):
                compliance_issues.append(f"{field} should be a list, got {type(response_data[field])}")
            elif field == 'entities_mentioned' and not isinstance(response_data[field], list):
                compliance_issues.append(f"{field} should be a list, got {type(response_data[field])}")
            elif field in ['state_updates', 'debug_info'] and not isinstance(response_data[field], dict):
                compliance_issues.append(f"{field} should be a dict, got {type(response_data[field])}")
        else:
            print(f"   ❌ {field}: MISSING - {description}")
            compliance_issues.append(f"Missing required field: {field}")
    
    # Check if 'response' is being used instead of 'narrative'
    if 'response' in response_data and 'narrative' not in response_data:
        print("\n   ⚠️  Found 'response' field instead of 'narrative'")
        compliance_issues.append("Using 'response' instead of 'narrative' field")
    
    # Check for non-schema fields
    non_schema_fields = set(response_data.keys()) - set(schema_fields.keys())
    if non_schema_fields:
        print(f"\n   ℹ️  Additional fields present: {non_schema_fields}")
    
    # 4. Display actual response structure
    print("\n📦 Actual Response Structure:")
    print(json.dumps(response_data, indent=2)[:500] + "...")
    
    # 5. Summary
    print("\n" + "="*60)
    if not compliance_issues:
        print("✅ SCHEMA COMPLIANT: All fields match game_state_instruction.md")
        return True
    else:
        print("❌ SCHEMA NON-COMPLIANT: Issues found:")
        for issue in compliance_issues:
            print(f"   - {issue}")
        print("\nThe API needs to be updated to match the original schema.")
        return False

if __name__ == "__main__":
    print("=== API Schema Compliance Test ===")
    print("Testing against game_state_instruction.md schema\n")
    
    success = test_api_schema_compliance()
    sys.exit(0 if success else 1)