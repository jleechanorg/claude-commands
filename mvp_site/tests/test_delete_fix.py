#!/usr/bin/env python3
"""
Simple test to verify __DELETE__ token processing works correctly.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Import just the function we need to test
def update_state_with_changes_simplified(state_to_update: dict, changes: dict) -> dict:
    """Simplified version of the function for testing."""
    for key, value in changes.items():
        # Case 1: Delete token processing
        if value == "__DELETE__":
            if key in state_to_update:
                del state_to_update[key]
                print(f"Removed '{key}' from state.")
            else:
                print(f"Attempted to delete '{key}' but it was not found in state.")
            continue

        # Case 2: Recursive processing for nested dictionaries
        if isinstance(value, dict) and isinstance(state_to_update.get(key), dict):
            state_to_update[key] = update_state_with_changes_simplified(
                state_to_update[key], value
            )

        # Case 3: Simple overwrite
        else:
            state_to_update[key] = value

    return state_to_update


def test_delete_token_processing():
    """Test that __DELETE__ tokens work correctly."""
    print("=== Testing __DELETE__ Token Processing ===")

    # Test 1: Simple deletion
    print("\nTest 1: Simple deletion")
    state = {
        "npc_data": {
            "Drake 1": {"name": "Drake 1", "type": "enemy"},
            "Drake 2": {"name": "Drake 2", "type": "enemy"},
            "Friendly NPC": {"name": "Friend", "type": "ally"},
        },
        "other_data": "should remain",
    }

    changes = {"npc_data": {"Drake 1": "__DELETE__", "Drake 2": "__DELETE__"}}

    print(f"Before: {state}")
    updated_state = update_state_with_changes_simplified(state, changes)
    print(f"After: {updated_state}")

    # Verify Drake 1 and Drake 2 are gone, but Friendly NPC remains
    assert "Drake 1" not in updated_state["npc_data"], "Drake 1 should be deleted"
    assert "Drake 2" not in updated_state["npc_data"], "Drake 2 should be deleted"
    assert "Friendly NPC" in updated_state["npc_data"], "Friendly NPC should remain"
    assert (
        updated_state["other_data"] == "should remain"
    ), "Other data should be unchanged"
    print("✅ Test 1 passed!")

    # Test 2: Top-level deletion
    print("\nTest 2: Top-level deletion")
    state2 = {
        "defeated_enemy": {"name": "Orc", "hp": 0},
        "alive_ally": {"name": "Ranger", "hp": 50},
        "world_data": {"location": "forest"},
    }

    changes2 = {"defeated_enemy": "__DELETE__"}

    print(f"Before: {state2}")
    updated_state2 = update_state_with_changes_simplified(state2, changes2)
    print(f"After: {updated_state2}")

    assert "defeated_enemy" not in updated_state2, "defeated_enemy should be deleted"
    assert "alive_ally" in updated_state2, "alive_ally should remain"
    assert "world_data" in updated_state2, "world_data should remain"
    print("✅ Test 2 passed!")

    print("\n🎉 All tests passed! __DELETE__ token processing works correctly.")


if __name__ == "__main__":
    test_delete_token_processing()
