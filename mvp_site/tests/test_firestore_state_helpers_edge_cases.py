#!/usr/bin/env python3
"""
Phase 5: Additional edge case tests for state helper functions
"""

import os

# Add parent directory to path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from firestore_service import (
    DELETE_TOKEN,
    _handle_append_syntax,
    update_state_with_changes,
)


class TestFirestoreStateHelpersEdgeCases(unittest.TestCase):
    """Additional edge case tests for state helpers"""

    def test_update_state_nested_append_syntax(self):
        """Test nested append syntax in dict values"""
        state = {"quests": {"active": ["quest1"], "completed": ["quest2"]}}

        changes = {
            "quests": {
                "active": {"append": ["quest3"]},
                "completed": {"append": ["quest4"]},
            }
        }

        with patch("logging_util.info"):
            result = update_state_with_changes(state, changes)

        # Both lists should have appended items
        assert result["quests"]["active"] == ["quest1", "quest3"]
        assert result["quests"]["completed"] == ["quest2", "quest4"]

    def test_update_state_delete_nested_keys(self):
        """Test DELETE_TOKEN on nested dictionary keys"""
        state = {
            "player": {
                "stats": {"hp": 100, "mp": 50},
                "inventory": ["sword"],
                "temp_buff": "strength",
            }
        }

        changes = {"player": {"temp_buff": DELETE_TOKEN, "stats": {"mp": DELETE_TOKEN}}}

        with patch("logging_util.info"):
            result = update_state_with_changes(state, changes)

        # temp_buff should be deleted
        assert "temp_buff" not in result["player"]
        # mp should be deleted from stats
        assert "mp" not in result["player"]["stats"]
        # hp should remain
        assert result["player"]["stats"]["hp"] == 100
        # inventory untouched
        assert result["player"]["inventory"] == ["sword"]

    def test_update_state_empty_changes(self):
        """Test update_state_with_changes with empty changes dict"""
        state = {"key": "value"}
        changes = {}

        result = update_state_with_changes(state, changes)

        assert result == state

    def test_update_state_none_values(self):
        """Test update_state_with_changes with None values"""
        state = {"key1": "value1"}
        changes = {"key1": None, "key2": None}

        result = update_state_with_changes(state, changes)

        assert result["key1"] is None
        assert result["key2"] is None

    @patch("firestore_service._perform_append")
    def test_handle_append_syntax_nested_append_structure(self, mock_append):
        """Test append syntax with nested append structure"""
        state = {"items": []}
        # Nested append structure (unusual but should handle)
        value = {"append": {"append": "nested"}}

        with patch("logging_util.info"):
            result = _handle_append_syntax(state, "items", value)

        assert result
        # Should append the entire nested structure
        mock_append.assert_called_once_with(
            state["items"], {"append": "nested"}, "items", deduplicate=False
        )

    def test_update_state_core_memories_multiple_attempts(self):
        """Test multiple types of core_memories updates in one call"""
        state = {"core_memories": ["memory1"]}

        # Try both direct overwrite and append syntax
        changes = {
            "core_memories": ["memory2", "memory3"]  # Will be safeguarded
        }

        with patch("logging_util.warning") as mock_warning:
            result = update_state_with_changes(state, changes)

        # Should have all memories due to safeguard
        assert "memory1" in result["core_memories"]
        assert "memory2" in result["core_memories"]
        assert "memory3" in result["core_memories"]
        mock_warning.assert_called_once()

    def test_update_state_complex_nested_structure(self):
        """Test deeply nested structure updates"""
        state = {
            "game": {
                "world": {
                    "regions": {
                        "forest": {"enemies": ["wolf"], "items": ["herb"]},
                        "cave": {"enemies": ["bat"], "items": ["ore"]},
                    }
                }
            }
        }

        changes = {
            "game": {
                "world": {
                    "regions": {
                        "forest": {"enemies": {"append": ["bear"]}},
                        "desert": {"enemies": ["scorpion"], "items": ["cactus"]},
                    }
                }
            }
        }

        with patch("logging_util.info"):
            result = update_state_with_changes(state, changes)

        # Forest enemies should have bear appended
        forest_enemies = result["game"]["world"]["regions"]["forest"]["enemies"]
        assert forest_enemies == ["wolf", "bear"]
        # Forest items unchanged
        assert result["game"]["world"]["regions"]["forest"]["items"] == ["herb"]
        # Cave unchanged
        assert result["game"]["world"]["regions"]["cave"] == {"enemies": ["bat"], "items": ["ore"]}
        # Desert added
        assert result["game"]["world"]["regions"]["desert"] == {"enemies": ["scorpion"], "items": ["cactus"]}

    def test_handle_dict_merge_with_delete_token_in_value(self):
        """Test dict merge where new dict contains DELETE_TOKEN"""
        state = {"config": {"a": 1, "b": 2, "c": 3}}
        value = {"b": DELETE_TOKEN, "d": 4}

        with patch("logging_util.info"):
            # The DELETE_TOKEN handling happens in update_state_with_changes
            result = update_state_with_changes(state, {"config": value})

        assert result["config"] == {"a": 1, "c": 3, "d": 4}
        assert "b" not in result["config"]

    def test_update_state_list_overwrite(self):
        """Test that non-append list updates do overwrite"""
        state = {"items": ["sword", "shield"]}
        changes = {"items": ["bow", "arrow"]}  # Direct overwrite

        result = update_state_with_changes(state, changes)

        # Should be completely replaced
        assert result["items"] == ["bow", "arrow"]

    def test_update_state_preserve_unchanged_keys(self):
        """Test that unchanged keys are preserved"""
        state = {
            "unchanged1": "value1",
            "unchanged2": {"nested": "value"},
            "changed": "old_value",
        }

        changes = {"changed": "new_value"}

        result = update_state_with_changes(state, changes)

        assert result["unchanged1"] == "value1"
        assert result["unchanged2"] == {"nested": "value"}
        assert result["changed"] == "new_value"


if __name__ == "__main__":
    unittest.main(verbosity=2)
