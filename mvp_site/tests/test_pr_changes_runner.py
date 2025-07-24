#!/usr/bin/env python3
"""
Simple test runner for PR changes that avoids import issues
"""

import os
import sys

from entity_tracking import create_from_game_state
from game_state import GameState
import constants

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_pr_change_tests():
    """Run all PR change validation tests"""

    # Test debug mode default change
    print("\n=== Testing Debug Mode Default Change ===")
    try:


        # Test 1: Default to True
        gs = GameState()
        assert gs.debug_mode == True, (
            f"Expected debug_mode=True by default, got {gs.debug_mode}"
        )
        print("✓ GameState defaults to debug_mode=True")

        # Test 2: Can be set to False
        gs = GameState(debug_mode=False)
        assert gs.debug_mode == False, (
            f"Expected debug_mode=False when set, got {gs.debug_mode}"
        )
        print("✓ GameState can be set to debug_mode=False")

        # Test 3: Serialization includes debug_mode
        data = gs.to_dict()
        assert "debug_mode" in data, "debug_mode missing from serialization"
        print("✓ debug_mode is included in serialization")

        # Test 4: Deserialization preserves debug_mode
        gs2 = GameState.from_dict({"debug_mode": True})
        assert gs2.debug_mode == True, (
            f"Expected debug_mode=True from dict, got {gs2.debug_mode}"
        )
        print("✓ debug_mode is preserved in deserialization")

    except Exception as e:
        print(f"✗ Debug mode tests failed: {e}")
        sys.exit(1)

    # Test entity schema constant
    print("\n=== Testing Entity Schema Constant ===")
    try:


        # PROMPT_TYPE_ENTITY_SCHEMA was integrated into game_state_instruction.md
        # So we check that it's no longer a separate constant
        assert not hasattr(constants, "PROMPT_TYPE_ENTITY_SCHEMA"), (
            "PROMPT_TYPE_ENTITY_SCHEMA should be removed (integrated into game_state)"
        )

        # Verify that PROMPT_TYPE_GAME_STATE exists instead
        assert hasattr(constants, "PROMPT_TYPE_GAME_STATE"), (
            "Missing PROMPT_TYPE_GAME_STATE constant"
        )
        assert constants.PROMPT_TYPE_GAME_STATE == "game_state", (
            f"Wrong value: {constants.PROMPT_TYPE_GAME_STATE}"
        )
        print(
            "✓ Entity schema has been properly integrated into game_state instructions"
        )

    except Exception as e:
        print(f"✗ Entity schema constant test failed: {e}")
        sys.exit(1)

    # Test manifest cache exclusion
    print("\n=== Testing Manifest Cache Exclusion ===")
    try:


        gs = GameState()
        gs.player_character_data = {"name": "TestHero"}

        # Add internal attributes
        gs._manifest_cache = {"should": "not appear"}
        gs._internal_data = "also should not appear"

        # Serialize
        data = gs.to_dict()

        # Check exclusions
        assert "_manifest_cache" not in data, "_manifest_cache should be excluded"
        assert "_internal_data" not in data, "_internal_data should be excluded"
        assert "player_character_data" in data, "Normal data should be included"

        print("✓ Internal attributes starting with _ are excluded from serialization")

    except Exception as e:
        print(f"✗ Manifest cache exclusion test failed: {e}")
        sys.exit(1)

    # Test entity ID format
    print("\n=== Testing Entity ID Format ===")
    try:


        game_state = {
            "player_character_data": {"name": "Test Hero", "hp": 100, "hp_max": 100},
            "npc_data": {
                "Guard Captain": {"name": "Guard Captain", "hp": 50, "hp_max": 50}
            },
            "world_data": {"current_location_name": "Test Town"},
        }

        manifest = create_from_game_state(game_state, session_number=1, turn_number=1)

        # Check PC ID format
        pc = manifest.player_characters[0]
        assert pc.entity_id.startswith("pc_"), (
            f"PC ID should start with 'pc_', got {pc.entity_id}"
        )
        assert "_" in pc.entity_id[3:], (
            f"PC ID should have underscores, got {pc.entity_id}"
        )
        print(f"✓ PC entity ID format correct: {pc.entity_id}")

        # Check NPC ID format
        npc = manifest.npcs[0]
        assert npc.entity_id.startswith("npc_"), (
            f"NPC ID should start with 'npc_', got {npc.entity_id}"
        )
        assert "_" in npc.entity_id[4:], (
            f"NPC ID should have underscores, got {npc.entity_id}"
        )
        print(f"✓ NPC entity ID format correct: {npc.entity_id}")

    except Exception as e:
        print(f"✗ Entity ID format test failed: {e}")
        sys.exit(1)

    print("\n=== All PR Change Tests Passed! ===")


if __name__ == "__main__":
    run_pr_change_tests()
