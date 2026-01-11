#!/usr/bin/env python3
"""
Phase 4: Helper function tests for firestore_service.py (fixed version)
Test _truncate_log_json and _perform_append functions
"""

import json
import os

# Add parent directory to path
import sys
import types
import unittest
from unittest.mock import patch

# Set test environment before any imports
os.environ["TESTING_AUTH_BYPASS"] = "true"
os.environ["USE_MOCKS"] = "true"

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Stub firebase_admin modules when unavailable to keep unit tests hermetic.
if "firebase_admin" not in sys.modules:
    firebase_admin_stub = types.ModuleType("firebase_admin")
    credentials_stub = types.ModuleType("firebase_admin.credentials")
    auth_stub = types.ModuleType("firebase_admin.auth")
    firestore_stub = types.ModuleType("firebase_admin.firestore")

    firebase_admin_stub.credentials = credentials_stub
    firebase_admin_stub.auth = auth_stub
    firebase_admin_stub.firestore = firestore_stub
    firebase_admin_stub.get_app = lambda *_args, **_kwargs: None
    firebase_admin_stub.initialize_app = lambda *_args, **_kwargs: None
    auth_stub.get_user = lambda *_args, **_kwargs: None
    firestore_stub.client = lambda *_args, **_kwargs: None
    firestore_stub.Client = type("Client", (), {})
    firestore_stub.SERVER_TIMESTAMP = object()

    sys.modules["firebase_admin"] = firebase_admin_stub
    sys.modules["firebase_admin.auth"] = auth_stub
    sys.modules["firebase_admin.credentials"] = credentials_stub
    sys.modules["firebase_admin.firestore"] = firestore_stub

# Mock Firebase before importing firestore_service
with patch("firestore_service.get_db"):
    from firestore_service import (
        DELETE_TOKEN,
        PROTECTED_INVENTORY_FIELDS,
        _expand_dot_notation,
        _handle_companion_equipment_safeguard,
        _handle_inventory_safeguard,
        _perform_append,
        _truncate_log_json,
    )


class TestFirestoreHelperFunctions(unittest.TestCase):
    """Test helper functions in firestore_service.py"""

    # Tests for _truncate_log_json
    def test_truncate_log_json_small_data(self):
        """Test _truncate_log_json with data smaller than max_lines"""
        data = {"key1": "value1", "key2": "value2"}
        result = _truncate_log_json(data, max_lines=10)

        # Small data should not be truncated
        assert "key1" in result
        assert "key2" in result
        assert "truncated" not in result.lower()

    def test_truncate_log_json_large_data(self):
        """Test _truncate_log_json with data exceeding max_lines"""
        # Create large nested data
        large_data = {
            f"key{i}": {"nested": {"data": f"value{i}", "more": list(range(10))}}
            for i in range(50)
        }

        result = _truncate_log_json(large_data, max_lines=5)

        # Result should be truncated
        lines = result.strip().split("\n")
        assert len(lines) == 5
        assert "truncated" in lines[-1].lower()

    def test_truncate_log_json_exact_boundary(self):
        """Test _truncate_log_json with exactly max_lines"""
        data = {"line1": 1, "line2": 2, "line3": 3}
        formatted = json.dumps(data, indent=2)
        line_count = len(formatted.split("\n"))

        result = _truncate_log_json(data, max_lines=line_count)

        # Should not truncate when exactly at boundary
        assert "truncated" not in result.lower()

    def test_truncate_log_json_invalid_json(self):
        """Test _truncate_log_json exception handling with non-serializable data"""

        # Create object that acts like it can't be serialized but our robust serializer handles it
        class NonSerializable:
            __slots__ = []

        data = {"key": NonSerializable()}

        # Should handle it without crashing
        result = _truncate_log_json(data, max_lines=10)

        # The robust serializer will likely turn it into a dict or string
        # We just want to ensure it doesn't crash and returns a string
        assert isinstance(result, str)
        assert "key" in result

    def test_truncate_log_json_circular_reference(self):
        """Test _truncate_log_json with circular reference"""
        data = {"key": "value"}
        data["circular"] = data  # Create circular reference

        # Should handle without crashing
        result = _truncate_log_json(data, max_lines=10)
        assert isinstance(result, str)

    def test_truncate_log_json_empty_data(self):
        """Test _truncate_log_json with empty data"""
        result = _truncate_log_json({}, max_lines=10)
        assert result.strip() == "{}"

    def test_truncate_log_json_none_data(self):
        """Test _truncate_log_json with None"""
        result = _truncate_log_json(None, max_lines=10)
        assert result.strip() == "null"

    # Tests for _perform_append
    @patch("logging_util.info")
    def test_perform_append_single_item(self, mock_log):
        """Test _perform_append with single item (not a list)"""
        target_list = ["existing1", "existing2"]

        _perform_append(target_list, "new_item", "test_key", deduplicate=False)

        assert target_list == ["existing1", "existing2", "new_item"]
        mock_log.assert_called_once()
        assert "Added 1 new items" in mock_log.call_args[0][0]

    @patch("logging_util.info")
    def test_perform_append_list_items(self, mock_log):
        """Test _perform_append with list of items"""
        target_list = ["existing"]
        items = ["item1", "item2", "item3"]

        _perform_append(target_list, items, "test_key", deduplicate=False)

        assert target_list == ["existing", "item1", "item2", "item3"]
        mock_log.assert_called_once()
        assert "Added 3 new items" in mock_log.call_args[0][0]

    @patch("logging_util.info")
    def test_perform_append_empty_list(self, mock_log):
        """Test _perform_append with empty items list"""
        target_list = ["existing"]

        _perform_append(target_list, [], "test_key", deduplicate=False)

        assert target_list == ["existing"]  # Unchanged
        mock_log.assert_called_once()
        assert "No new items were added" in mock_log.call_args[0][0]

    @patch("logging_util.info")
    def test_perform_append_deduplicate_true(self, mock_log):
        """Test _perform_append with deduplication enabled"""
        target_list = ["item1", "item2"]
        items = ["item2", "item3", "item1", "item4"]  # item1 and item2 are duplicates

        _perform_append(target_list, items, "test_key", deduplicate=True)

        # Only new items should be added
        assert target_list == ["item1", "item2", "item3", "item4"]
        mock_log.assert_called_once()
        assert "Added 2 new items" in mock_log.call_args[0][0]

    @patch("logging_util.info")
    def test_perform_append_deduplicate_false(self, mock_log):
        """Test _perform_append with deduplication disabled"""
        target_list = ["item1", "item2"]
        items = ["item2", "item3", "item1"]  # Duplicates

        _perform_append(target_list, items, "test_key", deduplicate=False)

        # All items added regardless of duplicates
        assert target_list == ["item1", "item2", "item2", "item3", "item1"]
        mock_log.assert_called_once()
        assert "Added 3 new items" in mock_log.call_args[0][0]

    @patch("logging_util.info")
    def test_perform_append_none_item(self, mock_log):
        """Test _perform_append with None as single item"""
        target_list = ["existing"]

        _perform_append(target_list, None, "test_key", deduplicate=False)

        assert target_list == ["existing", None]
        mock_log.assert_called_once()

    @patch("logging_util.info")
    def test_perform_append_complex_objects(self, _mock_log):  # noqa: PT019
        """Test _perform_append with complex objects"""
        target_list = [{"id": 1}]
        items = [{"id": 2}, {"id": 3, "data": {"nested": True}}]

        _perform_append(target_list, items, "test_key", deduplicate=False)

        assert len(target_list) == 3
        assert target_list[1]["id"] == 2
        assert target_list[2]["data"]["nested"]

    @patch("logging_util.info")
    def test_perform_append_deduplicate_complex_objects(self, mock_log):
        """Test _perform_append deduplication with complex objects"""
        obj1 = {"id": 1, "name": "Object 1"}
        obj2 = {"id": 2, "name": "Object 2"}
        target_list = [obj1, obj2]

        # Try to add obj1 again (should be deduped) and a new obj3
        items = [obj1, {"id": 3, "name": "Object 3"}]

        _perform_append(target_list, items, "test_key", deduplicate=True)

        # Only obj3 should be added
        assert len(target_list) == 3
        assert target_list[2]["id"] == 3
        mock_log.assert_called_once()
        assert "Added 1 new items" in mock_log.call_args[0][0]

    def test_truncate_log_json_max_lines_parameter(self):
        """Test _truncate_log_json respects max_lines parameter"""
        # Create data that will format to multiple lines
        data = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8}

        result = _truncate_log_json(data, max_lines=3)
        lines = result.strip().split("\n")
        assert len(lines) == 3
        assert "truncated" in lines[-1].lower()

    @patch("logging_util.info")
    def test_perform_append_all_duplicates(self, mock_log):
        """Test _perform_append when all items are duplicates"""
        target_list = ["item1", "item2", "item3"]
        items = ["item1", "item2", "item3"]  # All duplicates

        _perform_append(target_list, items, "test_key", deduplicate=True)

        # No items should be added
        assert target_list == ["item1", "item2", "item3"]
        mock_log.assert_called_once()
        assert "No new items were added" in mock_log.call_args[0][0]
        assert "duplicates may have been found" in mock_log.call_args[0][0]

    # Tests for _expand_dot_notation
    def test_expand_dot_notation_simple(self):
        """Test _expand_dot_notation with simple dot-notation key"""
        input_dict = {"a.b": 1, "c": 2}
        result = _expand_dot_notation(input_dict)

        expected = {"a": {"b": 1}, "c": 2}
        assert result == expected

    def test_expand_dot_notation_deep_nesting(self):
        """Test _expand_dot_notation with deeply nested dot-notation"""
        input_dict = {
            "game_state.custom_campaign_state.arc_milestones.wedding_tour": {
                "status": "completed",
                "phase": "ceremony_complete",
            }
        }
        result = _expand_dot_notation(input_dict)

        expected = {
            "game_state": {
                "custom_campaign_state": {
                    "arc_milestones": {
                        "wedding_tour": {
                            "status": "completed",
                            "phase": "ceremony_complete",
                        }
                    }
                }
            }
        }
        assert result == expected

    def test_expand_dot_notation_mixed_keys(self):
        """Test _expand_dot_notation with mix of dot-notation and regular keys"""
        input_dict = {
            "title": "Campaign Title",
            "metadata.author": "Test Author",
            "game_state.level": 5,
        }
        result = _expand_dot_notation(input_dict)

        expected = {
            "title": "Campaign Title",
            "metadata": {"author": "Test Author"},
            "game_state": {"level": 5},
        }
        assert result == expected

    def test_expand_dot_notation_no_dots(self):
        """Test _expand_dot_notation with no dot-notation keys"""
        input_dict = {"key1": "value1", "key2": {"nested": "value"}}
        result = _expand_dot_notation(input_dict)

        # Should be unchanged
        assert result == input_dict

    def test_expand_dot_notation_empty_dict(self):
        """Test _expand_dot_notation with empty dict"""
        result = _expand_dot_notation({})
        assert result == {}

    def test_expand_dot_notation_multiple_paths_same_prefix(self):
        """Test _expand_dot_notation with multiple paths sharing prefix"""
        input_dict = {
            "game_state.health": 100,
            "game_state.mana": 50,
            "game_state.inventory.slots": 10,
        }
        result = _expand_dot_notation(input_dict)

        # The setdefault() call correctly merges paths with same prefix
        expected = {
            "game_state": {
                "health": 100,
                "mana": 50,
                "inventory": {"slots": 10},
            },
        }
        assert result == expected

    def test_expand_dot_notation_value_is_list(self):
        """Test _expand_dot_notation with list value"""
        input_dict = {"items.weapons": ["sword", "bow", "staff"]}
        result = _expand_dot_notation(input_dict)

        expected = {"items": {"weapons": ["sword", "bow", "staff"]}}
        assert result == expected

    def test_expand_dot_notation_value_is_none(self):
        """Test _expand_dot_notation with None value"""
        input_dict = {"field.subfield": None}
        result = _expand_dot_notation(input_dict)

        expected = {"field": {"subfield": None}}
        assert result == expected

    def test_expand_dot_notation_conflicting_parent_key(self):
        """Test _expand_dot_notation raises for parent/child conflicts."""
        input_dict = {"game_state": {"health": 100}, "game_state.mana": 50}

        with self.assertRaises(ValueError):  # noqa: PT027
            _expand_dot_notation(input_dict)

    def test_expand_dot_notation_overlapping_paths(self):
        """Test _expand_dot_notation raises for overlapping dot paths."""
        input_dict = {"game_state.arc.milestone": 1, "game_state.arc": {"phase": 2}}

        with self.assertRaises(ValueError):  # noqa: PT027
            _expand_dot_notation(input_dict)

    def test_expand_dot_notation_invalid_segments(self):
        """Test _expand_dot_notation rejects empty path segments."""
        input_dict = {"game_state..arc": 1}

        with self.assertRaises(ValueError):  # noqa: PT027
            _expand_dot_notation(input_dict)


class TestInventorySafeguard(unittest.TestCase):
    """Test inventory safeguard functions for character item protection."""

    def test_protected_inventory_fields_constant(self):
        """Test that PROTECTED_INVENTORY_FIELDS contains expected fields."""
        expected_fields = {"inventory", "equipment", "backpack", "items"}
        assert expected_fields == PROTECTED_INVENTORY_FIELDS

    def test_inventory_safeguard_non_protected_key(self):
        """Test that non-protected keys are not handled."""
        state = {"health": 100}
        result = _handle_inventory_safeguard(state, "health", 50)
        assert result is False
        # Value should be unchanged
        assert state["health"] == 100

    def test_inventory_safeguard_no_existing_value(self):
        """Test that new inventory values are allowed when no existing value."""
        state = {}
        result = _handle_inventory_safeguard(state, "inventory", ["sword"])
        assert result is False  # Let normal handling proceed

    def test_inventory_safeguard_list_merge(self):
        """Test that list overwrites are converted to safe merges."""
        state = {"inventory": ["sword", "shield"]}
        result = _handle_inventory_safeguard(state, "inventory", ["potion", "shield"])

        assert result is True  # Handled by safeguard
        # Should merge and deduplicate while preserving existing order
        assert len(state["inventory"]) == 3
        assert state["inventory"] == ["sword", "shield", "potion"]

    def test_inventory_safeguard_preserves_existing_duplicates(self):
        """Test that existing duplicates are preserved while deduping new items."""
        state = {"inventory": ["health potion", "health potion", "sword"]}

        result = _handle_inventory_safeguard(
            state, "inventory", ["health potion", "shield"]
        )

        assert result is True
        assert state["inventory"].count("health potion") == 2
        assert "sword" in state["inventory"]
        assert "shield" in state["inventory"]
        assert len(state["inventory"]) == 4

    def test_inventory_safeguard_list_with_complex_items(self):
        """Test list merge with complex dict items."""
        state = {
            "equipment": [
                {"name": "Flaming Sword", "damage": "2d6"},
                {"name": "Iron Shield", "ac": 2},
            ]
        }
        new_items = [
            {"name": "Potion of Healing", "uses": 1},
            {"name": "Flaming Sword", "damage": "2d6"},  # Duplicate
        ]
        result = _handle_inventory_safeguard(state, "equipment", new_items)

        assert result is True
        assert len(state["equipment"]) == 3
        names = [item["name"] for item in state["equipment"]]
        assert "Flaming Sword" in names
        assert "Iron Shield" in names
        assert "Potion of Healing" in names

    def test_inventory_safeguard_blocks_dict_to_non_dict(self):
        """Test that dict inventory cannot be replaced with non-dict."""
        state = {"inventory": {"gold": 100, "gems": 5}}
        result = _handle_inventory_safeguard(state, "inventory", ["new_list"])

        assert result is True  # Blocked
        # Original dict should be preserved
        assert state["inventory"] == {"gold": 100, "gems": 5}

    def test_inventory_safeguard_blocks_list_to_non_list(self):
        """Test that list inventory cannot be replaced with non-list."""
        state = {"items": ["sword", "shield"]}
        result = _handle_inventory_safeguard(state, "items", "just a string")

        assert result is True  # Blocked
        # Original list should be preserved
        assert state["items"] == ["sword", "shield"]

    def test_inventory_safeguard_allows_dict_merge(self):
        """Test that dict-to-dict updates are not blocked (handled by dict_merge)."""
        state = {"inventory": {"gold": 100}}
        result = _handle_inventory_safeguard(state, "inventory", {"gems": 5})

        assert result is False  # Not handled, let dict_merge handle it

    def test_inventory_safeguard_all_protected_fields(self):
        """Test all protected field names trigger safeguard."""
        for field in ["inventory", "equipment", "backpack", "items"]:
            state = {field: ["item1"]}
            result = _handle_inventory_safeguard(state, field, ["item2"])
            assert result is True, f"Field '{field}' should trigger safeguard"
            assert "item1" in state[field], (
                f"Field '{field}' should preserve existing items"
            )

    def test_inventory_safeguard_non_serializable_items(self):
        """Test list merge handles non-serializable items gracefully."""
        import datetime

        class CustomItem:
            """Custom class that can't be JSON serialized."""

            def __init__(self, name):
                self.name = name

            def __str__(self):
                return f"CustomItem({self.name})"

        # Create items with datetime (non-JSON-serializable in standard json)
        state = {
            "equipment": [
                {
                    "name": "Sword",
                    "acquired": datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
                },
            ]
        }
        new_items = [
            {
                "name": "Potion",
                "acquired": datetime.datetime(2024, 1, 2, tzinfo=datetime.UTC),
            },
        ]

        # Should not crash - fallback to str() for dedup
        result = _handle_inventory_safeguard(state, "equipment", new_items)

        assert result is True
        assert len(state["equipment"]) == 2

        # Test with custom class objects
        custom1 = CustomItem("Shield")
        custom2 = CustomItem("Armor")
        custom3 = CustomItem("Shield")  # Duplicate by name but different object

        state2 = {"items": [custom1]}
        result2 = _handle_inventory_safeguard(state2, "items", [custom2, custom3])

        assert result2 is True
        # custom1 and custom3 have same str() but are different objects
        # Deduplication uses str(), so custom3 might be considered duplicate
        assert len(state2["items"]) == 2  # custom1 and custom2 remain


class TestCompanionEquipmentSafeguard(unittest.TestCase):
    """Test companion equipment safeguard for key secondary characters."""

    def test_companion_safeguard_non_npc_data(self):
        """Test that non-npc_data keys are not handled."""
        state = {"player_character_data": {"inventory": ["sword"]}}
        result = _handle_companion_equipment_safeguard(
            state, "player_character_data", {"inventory": ["bow"]}
        )
        assert result is False

    def test_companion_safeguard_non_companion(self):
        """Test that non-companion NPCs are not protected."""
        state = {
            "npc_data": {
                "Goblin Guard": {
                    "relationship": "enemy",
                    "equipment": ["rusty sword"],
                }
            }
        }
        result = _handle_companion_equipment_safeguard(
            state,
            "npc_data",
            {"Goblin Guard": {"equipment": ["iron sword"]}},
        )
        # Not handled because not a companion
        assert result is False

    def test_companion_safeguard_protects_companion_equipment(self):
        """Test that companion equipment is protected from overwrite."""
        state = {
            "npc_data": {
                "Elara the Swift": {
                    "relationship": "companion",
                    "equipment": ["elven bow", "leather armor"],
                }
            }
        }
        update_value = {
            "Elara the Swift": {
                "equipment": ["magic quiver", "elven bow"],  # One duplicate
                "hp_current": 25,
            }
        }
        result = _handle_companion_equipment_safeguard(state, "npc_data", update_value)

        # Returns False because it modifies value in place, letting dict_merge proceed
        assert result is False
        # But the value should be modified to merge equipment
        merged_equipment = update_value["Elara the Swift"]["equipment"]
        assert len(merged_equipment) == 3
        assert "elven bow" in merged_equipment
        assert "leather armor" in merged_equipment
        assert "magic quiver" in merged_equipment

    def test_companion_safeguard_preserves_existing_duplicates(self):
        """Test that existing duplicate companion items are preserved."""
        state = {
            "npc_data": {
                "Healer Companion": {
                    "relationship": "companion",
                    "equipment": ["healing potion", "healing potion", "staff"],
                }
            }
        }
        update_value = {"Healer Companion": {"equipment": ["healing potion", "robe"]}}

        _handle_companion_equipment_safeguard(state, "npc_data", update_value)

        merged = update_value["Healer Companion"]["equipment"]
        assert merged.count("healing potion") == 2
        assert "staff" in merged
        assert "robe" in merged
        assert len(merged) == 4

    def test_companion_safeguard_protects_party_member(self):
        """Test that party_member relationship triggers protection."""
        state = {
            "npc_data": {
                "Thoric Ironforge": {
                    "relationship": "party_member",
                    "inventory": ["healing potion", "gold coins"],
                }
            }
        }
        update_value = {
            "Thoric Ironforge": {
                "inventory": ["mana potion"],
            }
        }
        _handle_companion_equipment_safeguard(state, "npc_data", update_value)

        merged = update_value["Thoric Ironforge"]["inventory"]
        assert "healing potion" in merged
        assert "gold coins" in merged
        assert "mana potion" in merged

    def test_companion_safeguard_blocks_list_to_non_list(self):
        """Test that list equipment cannot be replaced with non-list values."""
        state = {
            "npc_data": {
                "Sorla": {
                    "relationship": "companion",
                    "equipment": ["blade", "cloak"],
                }
            }
        }
        update_value = {"Sorla": {"equipment": "not-a-list"}}

        _handle_companion_equipment_safeguard(state, "npc_data", update_value)

        # Should block type conversion and remove unsafe update
        assert "equipment" not in update_value["Sorla"]
        assert state["npc_data"]["Sorla"]["equipment"] == ["blade", "cloak"]

    def test_companion_safeguard_protects_is_important_npc(self):
        """Test that is_important flag triggers protection."""
        state = {
            "npc_data": {
                "Queen Aldara": {
                    "relationship": "neutral",
                    "is_important": True,
                    "equipment": ["royal scepter"],
                }
            }
        }
        update_value = {
            "Queen Aldara": {
                "equipment": ["crown"],
            }
        }
        _handle_companion_equipment_safeguard(state, "npc_data", update_value)

        merged = update_value["Queen Aldara"]["equipment"]
        assert "royal scepter" in merged
        assert "crown" in merged

    def test_companion_safeguard_non_serializable_equipment(self):
        """Test companion equipment merge handles non-serializable items."""
        import datetime

        class MagicItem:
            def __init__(self, name):
                self.name = name

            def __str__(self):
                return f"MagicItem({self.name})"

        state = {
            "npc_data": {
                "Wizard Companion": {
                    "relationship": "companion",
                    "equipment": [
                        {
                            "name": "Staff",
                            "enchanted_at": datetime.datetime(
                                2024, 1, 1, tzinfo=datetime.UTC
                            ),
                        },
                        MagicItem("Robe"),
                    ],
                }
            }
        }
        update_value = {
            "Wizard Companion": {
                "equipment": [
                    {
                        "name": "Wand",
                        "enchanted_at": datetime.datetime(
                            2024, 1, 2, tzinfo=datetime.UTC
                        ),
                    },
                    MagicItem("Hat"),
                ],
            }
        }

        result = _handle_companion_equipment_safeguard(state, "npc_data", update_value)

        assert result is False  # Should allow dict_merge to proceed
        merged = update_value["Wizard Companion"]["equipment"]
        assert len(merged) == 4

    def test_companion_safeguard_protects_ally(self):
        """Test that ally relationship triggers protection."""
        state = {
            "npc_data": {
                "Sir Galahad": {
                    "relationship": "ally",
                    "backpack": ["provisions", "map"],
                }
            }
        }
        update_value = {
            "Sir Galahad": {
                "backpack": ["torch"],
            }
        }
        _handle_companion_equipment_safeguard(state, "npc_data", update_value)

        merged = update_value["Sir Galahad"]["backpack"]
        assert "provisions" in merged
        assert "map" in merged
        assert "torch" in merged

    def test_companion_safeguard_relationship_case_insensitive(self):
        """Test that relationship checks are case-insensitive."""

        state = {
            "npc_data": {
                "Casey": {
                    "relationship": "Companion",  # Capitalized
                    "equipment": ["amulet"],
                }
            }
        }
        update_value = {
            "Casey": {
                "equipment": ["torch"],
            }
        }

        _handle_companion_equipment_safeguard(state, "npc_data", update_value)

        merged = update_value["Casey"]["equipment"]
        assert merged == ["amulet", "torch"]

    def test_companion_safeguard_allows_delete_token(self):
        """Test that DELETE_TOKEN passes through."""

        state = {
            "npc_data": {
                "Fallen Companion": {
                    "relationship": "companion",
                    "equipment": ["sword"],
                }
            }
        }
        update_value = {"Fallen Companion": DELETE_TOKEN}
        result = _handle_companion_equipment_safeguard(state, "npc_data", update_value)

        # Should not interfere with DELETE_TOKEN
        assert result is False
        assert update_value["Fallen Companion"] == DELETE_TOKEN

    def test_companion_safeguard_multiple_npcs(self):
        """Test that multiple NPCs are handled correctly."""
        state = {
            "npc_data": {
                "Companion A": {
                    "relationship": "companion",
                    "equipment": ["item1"],
                },
                "Enemy B": {
                    "relationship": "enemy",
                    "equipment": ["enemy_item"],
                },
                "Companion C": {
                    "relationship": "follower",
                    "items": ["item2"],
                },
            }
        }
        update_value = {
            "Companion A": {"equipment": ["item3"]},
            "Enemy B": {"equipment": ["new_enemy_item"]},
            "Companion C": {"items": ["item4"]},
        }
        _handle_companion_equipment_safeguard(state, "npc_data", update_value)

        # Companion A: equipment should be merged
        assert set(update_value["Companion A"]["equipment"]) == {"item1", "item3"}
        # Enemy B: equipment should NOT be merged (not protected)
        assert update_value["Enemy B"]["equipment"] == ["new_enemy_item"]
        # Companion C: items should be merged
        assert set(update_value["Companion C"]["items"]) == {"item2", "item4"}


if __name__ == "__main__":
    unittest.main(verbosity=2)
