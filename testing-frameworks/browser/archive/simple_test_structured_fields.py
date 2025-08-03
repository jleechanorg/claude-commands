#!/usr/bin/env python3
"""
Simple test to examine the actual API response structure for structured fields.
Uses mock services to avoid Firebase auth issues.
"""

import json
import sys

# Import test utilities
sys.path.insert(0, "mvp_site")
from test_integration.test_integration import create_test_client


def test_structured_fields():
    """Test structured fields using the test client with mocked services."""
    # Create test client with mocked services
    client = create_test_client()

    # Create a campaign
    print("Creating test campaign...")
    response = client.post(
        "/api/campaigns",
        json={
            "title": "Test Campaign",
            "prompt": "A test campaign for structured fields",
            "campaign_type": "custom",
        },
        headers={"X-Test-User-Id": "test-user-123"},
    )

    campaign_data = response.get_json()
    print(f"Campaign creation response keys: {list(campaign_data.keys())}")
    campaign_id = campaign_data["campaign_id"]

    # Send an interaction with debug mode
    print(f"\nSending interaction to campaign {campaign_id}...")
    response = client.post(
        f"/api/campaigns/{campaign_id}/interaction",
        json={
            "input_text": "I attack the goblin with my sword! Roll for damage.",
            "mode": "character",
            "debug_mode": True,
        },
        headers={"X-Test-User-Id": "test-user-123"},
    )

    data = response.get_json()

    print("\n=== API RESPONSE STRUCTURE ===")
    print(f"Status code: {response.status_code}")
    print(f"Top-level keys: {sorted(data.keys())}")

    # Check field locations
    print("\n=== CHECKING FIELD LOCATIONS ===")

    # Top level fields
    top_level_fields = [
        "response",
        "dice_rolls",
        "resources",
        "planning_block",
        "session_header",
        "debug_info",
        "entities_mentioned",
        "location_confirmed",
        "state_updates",
    ]

    print("\nTop-level fields:")
    for field in top_level_fields:
        if field in data:
            value_type = type(data[field]).__name__
            print(f"  ✓ {field}: {value_type}", end="")
            if value_type in ["str", "int", "float"]:
                print(f" = {repr(data[field])[:50]}")
            elif value_type == "list":
                print(f" with {len(data[field])} items")
            elif value_type == "dict":
                print(f" with keys: {list(data[field].keys())[:5]}")
            else:
                print()

    # Debug info fields
    if "debug_info" in data and isinstance(data["debug_info"], dict):
        print("\ndebug_info contents:")
        for field in ["dice_rolls", "resources", "dm_notes", "state_rationale"]:
            if field in data["debug_info"]:
                value_type = type(data["debug_info"][field]).__name__
                print(f"  ✓ {field}: {value_type}", end="")
                if value_type in ["str", "int", "float"]:
                    print(f" = {repr(data['debug_info'][field])[:50]}")
                elif value_type == "list":
                    print(f" with {len(data['debug_info'][field])} items")
                else:
                    print()

    # Summary
    print("\n=== SUMMARY ===")
    dice_at_top = "dice_rolls" in data
    dice_in_debug = "debug_info" in data and "dice_rolls" in data.get("debug_info", {})

    if dice_at_top and dice_in_debug:
        print("⚠️  dice_rolls appears in BOTH top-level AND debug_info (duplication)")
    elif dice_at_top:
        print("📍 dice_rolls is at TOP LEVEL only")
    elif dice_in_debug:
        print("📍 dice_rolls is in DEBUG_INFO only")
    else:
        print("❌ dice_rolls not found in response")

    resources_at_top = "resources" in data
    resources_in_debug = "debug_info" in data and "resources" in data.get(
        "debug_info", {}
    )

    if resources_at_top and resources_in_debug:
        print("⚠️  resources appears in BOTH top-level AND debug_info (duplication)")
    elif resources_at_top:
        print("📍 resources is at TOP LEVEL only")
    elif resources_in_debug:
        print("📍 resources is in DEBUG_INFO only")
    else:
        print("❌ resources not found in response")

    # Show full response for inspection
    print("\n=== FULL RESPONSE ===")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    test_structured_fields()
