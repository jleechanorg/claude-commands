#!/usr/bin/env python3
# ruff: noqa: PT009
"""Unit tests for inventory validation functions in response_validators.py.

Tests the post-processing validator that catches item spawning exploits
where players claim items they don't have.

Functions tested:
- validate_items_used(): Main validator that checks items against inventory
- get_all_inventory_items(): Extracts item names from game state
- _item_in_inventory(): Fuzzy matching for item names

Run:
    TESTING=true vpython mvp_site/tests/test_inventory_validation.py
"""

import os
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mvp_site.response_validators import (
    _item_in_inventory,
    _normalize_item_name,
    comprehensive_item_validation,
    get_all_inventory_items,
    validate_items_used,
)

# =============================================================================
# Mock Game State for Testing
# =============================================================================


@dataclass
class MockGameState:
    """Mock game state with configurable equipment."""

    player_character_data: dict[str, Any]
    item_registry: dict[str, Any] = None

    def __post_init__(self):
        if self.item_registry is None:
            self.item_registry = {}


def create_test_game_state(
    equipped: dict[str, str] = None,
    weapons: list[Any] = None,
    backpack: list[Any] = None,
    item_registry: dict[str, Any] = None,
) -> MockGameState:
    """Create a mock game state with specified equipment."""
    return MockGameState(
        player_character_data={
            "equipment": {
                "equipped": equipped or {},
                "weapons": weapons or [],
                "backpack": backpack or [],
            }
        },
        item_registry=item_registry or {},
    )


# =============================================================================
# Test Cases
# =============================================================================


class TestGetAllInventoryItems(unittest.TestCase):
    """Tests for get_all_inventory_items()."""

    def test_extracts_equipped_items(self):
        """Equipped items should be extracted."""
        gs = create_test_game_state(
            equipped={"weapon": "Longsword", "armor": "Chain Mail", "head": "Helmet"}
        )
        items = get_all_inventory_items(gs)
        self.assertIn("longsword", items)
        self.assertIn("chain mail", items)
        self.assertIn("helmet", items)

    def test_extracts_weapons(self):
        """Weapon list items should be extracted."""
        gs = create_test_game_state(
            weapons=[
                {"name": "Longsword", "damage": "1d8"},
                {"name": "Dagger", "damage": "1d4"},
            ]
        )
        items = get_all_inventory_items(gs)
        self.assertIn("longsword", items)
        self.assertIn("dagger", items)

    def test_extracts_backpack_items(self):
        """Backpack items should be extracted."""
        gs = create_test_game_state(
            backpack=[
                {"name": "Torch"},
                {"name": "Rope"},
                {"name": "Potion of Healing"},
            ]
        )
        items = get_all_inventory_items(gs)
        self.assertIn("torch", items)
        self.assertIn("rope", items)
        self.assertIn("potion of healing", items)

    def test_handles_legacy_string_format(self):
        """Legacy 'Item (stats)' format should be parsed."""
        gs = create_test_game_state(
            equipped={"weapon": "Longsword +1 (1d8+1 slashing)"}
        )
        items = get_all_inventory_items(gs)
        self.assertIn("longsword +1", items)

    def test_uses_item_registry(self):
        """Item registry should be used for ID lookups."""
        gs = create_test_game_state(
            equipped={"weapon": "sword-001"},
            item_registry={"sword-001": {"name": "Flame Tongue"}},
        )
        items = get_all_inventory_items(gs)
        self.assertIn("flame tongue", items)

    def test_empty_equipment(self):
        """Empty equipment should return empty set."""
        gs = create_test_game_state()
        items = get_all_inventory_items(gs)
        self.assertEqual(len(items), 0)

    def test_handles_none_values(self):
        """None values in equipment should be skipped."""
        gs = create_test_game_state(equipped={"weapon": "Longsword", "armor": None})
        items = get_all_inventory_items(gs)
        self.assertIn("longsword", items)
        self.assertEqual(len(items), 1)


class TestNormalizeItemName(unittest.TestCase):
    """Tests for _normalize_item_name()."""

    def test_removes_my_prefix(self):
        """'my ' prefix should be removed."""
        self.assertEqual(_normalize_item_name("my longsword"), "longsword")

    def test_removes_the_prefix(self):
        """'the ' prefix should be removed."""
        self.assertEqual(
            _normalize_item_name("the potion of healing"), "potion of healing"
        )

    def test_removes_a_prefix(self):
        """'a ' prefix should be removed."""
        self.assertEqual(_normalize_item_name("a torch"), "torch")

    def test_removes_an_prefix(self):
        """'an ' prefix should be removed."""
        self.assertEqual(_normalize_item_name("an amulet"), "amulet")

    def test_lowercase(self):
        """Names should be lowercased."""
        self.assertEqual(_normalize_item_name("LONGSWORD"), "longsword")

    def test_strips_whitespace(self):
        """Whitespace should be stripped."""
        self.assertEqual(_normalize_item_name("  longsword  "), "longsword")


class TestItemInInventory(unittest.TestCase):
    """Tests for _item_in_inventory()."""

    def test_exact_match(self):
        """Exact match should succeed."""
        inventory = {"longsword", "torch", "rope"}
        self.assertTrue(_item_in_inventory("longsword", inventory))

    def test_case_insensitive(self):
        """Match should be case-insensitive."""
        inventory = {"longsword"}
        self.assertTrue(_item_in_inventory("Longsword", inventory))

    def test_substring_match_item_in_inventory(self):
        """'sword' should match 'longsword' in inventory."""
        inventory = {"longsword"}
        self.assertTrue(_item_in_inventory("sword", inventory))

    def test_substring_match_inventory_in_item(self):
        """'longsword' should not match when inventory has only 'sword'."""
        inventory = {"sword"}
        self.assertFalse(_item_in_inventory("longsword", inventory))

    def test_prefix_removal(self):
        """'my longsword' should match 'longsword'."""
        inventory = {"longsword"}
        self.assertTrue(_item_in_inventory("my longsword", inventory))

    def test_no_match(self):
        """Non-existent items should not match."""
        inventory = {"longsword", "torch"}
        self.assertFalse(_item_in_inventory("ring of invisibility", inventory))

    def test_empty_inventory(self):
        """Empty inventory should return False for any item."""
        inventory = set()
        self.assertFalse(_item_in_inventory("longsword", inventory))


class TestValidateItemsUsed(unittest.TestCase):
    """Tests for validate_items_used()."""

    def test_valid_items_pass(self):
        """Items in inventory should pass validation."""
        gs = create_test_game_state(
            equipped={"weapon": "Longsword"},
            backpack=[{"name": "Torch"}, {"name": "Rope"}],
        )
        is_valid, invalid_items, msg = validate_items_used(["longsword", "torch"], gs)
        self.assertTrue(is_valid, f"Valid items should pass, but got: {invalid_items}")
        self.assertEqual(len(invalid_items), 0)
        self.assertEqual(msg, "")

    def test_invalid_item_fails(self):
        """Items not in inventory should fail validation."""
        gs = create_test_game_state(equipped={"weapon": "Longsword"})
        is_valid, invalid_items, msg = validate_items_used(["ring of invisibility"], gs)
        self.assertFalse(is_valid, "Invalid item should fail")
        self.assertIn("ring of invisibility", invalid_items)

    def test_rejection_message_single_item(self):
        """Single invalid item should have proper rejection message."""
        gs = create_test_game_state()
        is_valid, invalid_items, msg = validate_items_used(["bag of holding"], gs)
        self.assertFalse(is_valid)
        self.assertIn("bag of holding", msg)
        self.assertIn("don't have", msg)
        self.assertIn("Check your inventory", msg)

    def test_rejection_message_multiple_items(self):
        """Multiple invalid items should list all in rejection message."""
        gs = create_test_game_state()
        is_valid, invalid_items, msg = validate_items_used(
            ["ring of invisibility", "bag of holding"], gs
        )
        self.assertFalse(is_valid)
        self.assertIn("ring of invisibility", msg)
        self.assertIn("bag of holding", msg)
        self.assertIn("don't have them", msg)

    def test_mixed_valid_invalid(self):
        """Mixed valid/invalid should fail with only invalid items listed."""
        gs = create_test_game_state(equipped={"weapon": "Longsword"})
        is_valid, invalid_items, msg = validate_items_used(
            ["longsword", "ring of invisibility"], gs
        )
        self.assertFalse(is_valid)
        self.assertEqual(len(invalid_items), 1)
        self.assertIn("ring of invisibility", invalid_items)
        self.assertNotIn("longsword", invalid_items)

    def test_empty_items_used_passes(self):
        """Empty items_used list should pass validation."""
        gs = create_test_game_state()
        is_valid, invalid_items, msg = validate_items_used([], gs)
        self.assertTrue(is_valid)
        self.assertEqual(len(invalid_items), 0)
        self.assertEqual(msg, "")

    def test_none_items_used_passes(self):
        """None items_used should pass validation (treated as empty)."""
        gs = create_test_game_state()
        # This tests edge case - function should handle None gracefully
        # Current implementation checks `if not items_used:` which handles None
        is_valid, invalid_items, msg = validate_items_used(None, gs)
        self.assertTrue(is_valid)


class TestExploitScenarios(unittest.TestCase):
    """Test realistic exploit scenarios from actual campaign data."""

    def setUp(self):
        """Create a realistic character inventory."""
        self.gs = create_test_game_state(
            equipped={
                "weapon": "Longsword +1",
                "armor": "Chain Mail",
                "shield": "Wooden Shield",
            },
            weapons=[{"name": "Longsword +1", "damage": "1d8+1"}],
            backpack=[
                {"name": "Rope"},
                {"name": "Torch"},
                {"name": "Bedroll"},
                {"name": "Waterskin"},
                {"name": "Rations"},
            ],
        )

    def test_bag_of_holding_exploit(self):
        """Player claims bag of holding they don't have."""
        is_valid, invalid, msg = validate_items_used(
            ["bag of holding", "ring of the hill giant"], self.gs
        )
        self.assertFalse(is_valid)
        self.assertIn("bag of holding", invalid)
        self.assertIn("ring of the hill giant", invalid)

    def test_magic_ring_exploit(self):
        """Player claims magic ring from non-existent container."""
        is_valid, invalid, msg = validate_items_used(
            ["ring of elven dexterity"], self.gs
        )
        self.assertFalse(is_valid)
        self.assertIn("ring of elven dexterity", invalid)

    def test_potion_exploit(self):
        """Player claims potion they don't have."""
        is_valid, invalid, msg = validate_items_used(
            ["potion of invisibility"], self.gs
        )
        self.assertFalse(is_valid)
        self.assertIn("potion of invisibility", invalid)

    def test_amulet_exploit(self):
        """Player claims amulet from environment."""
        is_valid, invalid, msg = validate_items_used(
            ["amulet of the wise beholder"], self.gs
        )
        self.assertFalse(is_valid)
        self.assertIn("amulet of the wise beholder", invalid)

    def test_valid_combat_action(self):
        """Using equipped weapon should succeed."""
        is_valid, invalid, msg = validate_items_used(["longsword"], self.gs)
        self.assertTrue(is_valid, f"Longsword should be valid: {invalid}")

    def test_valid_utility_action(self):
        """Using backpack items should succeed."""
        is_valid, invalid, msg = validate_items_used(["torch", "rope"], self.gs)
        self.assertTrue(is_valid, f"Torch and rope should be valid: {invalid}")


class TestEmptyInventoryBypass(unittest.TestCase):
    """Test the critical empty inventory bypass vulnerability fix.

    Tests that comprehensive_item_validation() correctly blocks exploits
    when inventory is empty/missing, rather than bypassing validation.

    This tests the fix for equipment_display.py:1348-1354 where the
    function was returning (True, [], "") for empty inventory, allowing
    item spawning exploits to succeed.
    """

    def test_empty_inventory_blocks_item_claims(self):
        """CRITICAL: Empty inventory must NOT bypass validation.

        Before fix: comprehensive_item_validation returned (True, [], "")
        After fix: Should return (False, invalid_items, message)
        """
        # Create game state with completely empty inventory
        gs = MockGameState(
            player_character_data={"equipment": {}}, item_registry={}
        )

        # Simulate LLM claiming non-existent items
        user_input = "Take a ring of the Hill Giant out of your bag of holding"
        items_used = ["bag of holding", "ring of the hill giant"]
        narrative = "You reach for your bag of holding..."

        # CRITICAL TEST: Must return False (exploit blocked)
        is_valid, invalid_items, msg = comprehensive_item_validation(
            user_input=user_input,
            narrative=narrative,
            items_used=items_used,
            game_state=gs,
        )

        # Assertions proving the fix works
        self.assertFalse(
            is_valid,
            "EMPTY INVENTORY BYPASS: comprehensive_item_validation returned True "
            "for empty inventory! This allows item spawning exploits.",
        )
        # At least 2 invalid items (may have extra from parsing)
        self.assertGreaterEqual(
            len(invalid_items), 2, f"Expected at least 2 invalid items, got {len(invalid_items)}"
        )
        self.assertIn("bag of holding", invalid_items)
        # Case-insensitive check
        found_ring = any("ring" in item.lower() and "hill giant" in item.lower() for item in invalid_items)
        self.assertTrue(found_ring, f"Expected ring of hill giant in {invalid_items}")
        self.assertIn("don't have", msg.lower())

    def test_missing_equipment_field_blocks_exploits(self):
        """Empty player_character_data should block item claims."""
        gs = MockGameState(player_character_data={}, item_registry={})

        items_used = ["potion of invisibility", "amulet of power"]
        user_input = "Drink the potion of invisibility"
        narrative = "You drink the potion..."

        is_valid, invalid_items, msg = comprehensive_item_validation(
            user_input=user_input,
            narrative=narrative,
            items_used=items_used,
            game_state=gs,
        )

        self.assertFalse(
            is_valid,
            "Missing equipment field should block exploits, not bypass validation",
        )
        # At least 2 (may extract extra items like "potion" from input)
        self.assertGreaterEqual(len(invalid_items), 2)

    def test_none_inventory_blocks_exploits(self):
        """None values in inventory fields should block item claims."""
        gs = MockGameState(
            player_character_data={
                "equipment": {"equipped": None, "weapons": None, "backpack": None}
            },
            item_registry={},
        )

        items_used = ["ring of elven dexterity"]
        user_input = "Use my ring of elven dexterity"
        narrative = "You activate the ring..."

        is_valid, invalid_items, msg = comprehensive_item_validation(
            user_input=user_input,
            narrative=narrative,
            items_used=items_used,
            game_state=gs,
        )

        self.assertFalse(
            is_valid, "None inventory values should block exploits, not bypass validation"
        )
        self.assertIn("ring of elven dexterity", invalid_items)

    def test_empty_inventory_with_llm_rejection_still_blocks(self):
        """Even if LLM rejects in narrative, validation must block exploits."""
        gs = MockGameState(
            player_character_data={"equipment": {}}, item_registry={}
        )

        items_used = ["bag of holding"]
        user_input = "Take ring from bag of holding"
        # LLM correctly rejects in narrative
        narrative = "You don't have a bag of holding. Check your inventory."

        is_valid, invalid_items, msg = comprehensive_item_validation(
            user_input=user_input,
            narrative=narrative,
            items_used=items_used,
            game_state=gs,
        )

        # Even though LLM rejected it narratively, validation must also catch it
        self.assertFalse(
            is_valid,
            "Validation must block exploits even if LLM rejects in narrative",
        )
        self.assertIn("bag of holding", invalid_items)

    def test_populated_inventory_works_normally(self):
        """Verify the fix doesn't break normal validation with items."""
        gs = create_test_game_state(
            equipped={"weapon": "Longsword"},
            backpack=[{"name": "Torch"}],
        )

        items_used = ["longsword", "torch"]
        user_input = "Use the longsword"  # Simple input to avoid parsing issues
        narrative = "You swing your longsword."

        is_valid, invalid_items, msg = comprehensive_item_validation(
            user_input=user_input,
            narrative=narrative,
            items_used=items_used,
            game_state=gs,
        )

        # Normal case: valid items should pass
        self.assertTrue(
            is_valid,
            f"Valid items with populated inventory should pass. Invalid items: {invalid_items}, msg: {msg}"
        )
        self.assertEqual(len(invalid_items), 0)


if __name__ == "__main__":
    # Set TESTING env var for test mode
    os.environ["TESTING"] = "true"
    unittest.main(verbosity=2)
