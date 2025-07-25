#!/usr/bin/env python3
"""
Test to verify that structured fields are properly stored and retrieved.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))

import constants
from mocks import mock_firestore_service


def test_structured_fields_storage():
    """Test that structured fields are stored and retrieved correctly."""
    print("Testing structured fields storage...")

    user_id = "test-user"
    campaign_id = "test-campaign"

    # Create a campaign first
    mock_firestore_service.get_mock_firestore_client().set_campaign_data(
        user_id,
        campaign_id,
        {
            "id": campaign_id,
            "title": "Test Campaign",
            "prompt": "Test prompt",
            "selected_prompts": ["narrative"],
        },
    )

    # Test structured fields data
    structured_fields = {
        "session_header": "Test session header with stats",
        "planning_block": "What would you like to do next?\\n1. Attack\\n2. Defend",
        "dice_rolls": ["Attack roll: d20+5 = 18", "Damage roll: 1d8+3 = 7"],
        "resources": "HP: 25/30, Gold: 150",
        "debug_info": {"test_field": "test_value", "turn_number": 3},
    }

    # Add story entry with structured fields
    mock_firestore_service.add_story_entry(
        user_id,
        campaign_id,
        constants.ACTOR_GEMINI,
        "The goblin attacks you with its rusty sword!",
        structured_fields=structured_fields,
    )

    # Retrieve campaign and story
    campaign, story_entries = mock_firestore_service.get_campaign_by_id(
        user_id, campaign_id
    )

    # Verify structured fields are preserved
    if not story_entries:
        print("❌ No story entries found")
        return False

    ai_entry = None
    for entry in story_entries:
        if entry.get("actor") == constants.ACTOR_GEMINI:
            ai_entry = entry
            break

    if not ai_entry:
        print("❌ No AI story entry found")
        return False

    print(f"✓ Found AI story entry: {ai_entry.get('text', '')[:50]}...")

    # Check each structured field
    success = True

    if ai_entry.get("session_header") != structured_fields["session_header"]:
        print(
            f"❌ session_header mismatch: {ai_entry.get('session_header')} != {structured_fields['session_header']}"
        )
        success = False
    else:
        print("✓ session_header preserved")

    if ai_entry.get("planning_block") != structured_fields["planning_block"]:
        print(
            f"❌ planning_block mismatch: {ai_entry.get('planning_block')} != {structured_fields['planning_block']}"
        )
        success = False
    else:
        print("✓ planning_block preserved")

    if ai_entry.get("dice_rolls") != structured_fields["dice_rolls"]:
        print(
            f"❌ dice_rolls mismatch: {ai_entry.get('dice_rolls')} != {structured_fields['dice_rolls']}"
        )
        success = False
    else:
        print("✓ dice_rolls preserved")

    if ai_entry.get("resources") != structured_fields["resources"]:
        print(
            f"❌ resources mismatch: {ai_entry.get('resources')} != {structured_fields['resources']}"
        )
        success = False
    else:
        print("✓ resources preserved")

    if ai_entry.get("debug_info") != structured_fields["debug_info"]:
        print(
            f"❌ debug_info mismatch: {ai_entry.get('debug_info')} != {structured_fields['debug_info']}"
        )
        success = False
    else:
        print("✓ debug_info preserved")

    if success:
        print("✅ All structured fields stored and retrieved correctly")
    else:
        print("❌ Some structured fields failed to persist")

    return success


if __name__ == "__main__":
    print("Structured Fields Storage Test")
    print("=" * 50)
    test_structured_fields_storage()
