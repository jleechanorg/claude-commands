#!/usr/bin/env python3
"""
Phase 5: State helper function tests for firestore_service.py
Test _handle_append_syntax, _handle_core_memories_safeguard,
_handle_dict_merge, _handle_delete_token, _handle_string_to_dict_update
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
    _handle_core_memories_safeguard,
    _handle_delete_token,
    _handle_dict_merge,
    _handle_string_to_dict_update,
    update_state_with_changes,
)


class TestFirestoreStateHelpers(unittest.TestCase):
    """Test state helper functions in firestore_service.py"""

    # Tests for _handle_append_syntax
    @patch("firestore_service._perform_append")
    @patch("logging_util.info")
    def test_handle_append_syntax_valid(self, mock_log, mock_append):
        """Test _handle_append_syntax with valid append syntax"""
        state = {"items": ["existing"]}
        value = {"append": ["new1", "new2"]}

        result = _handle_append_syntax(state, "items", value)

        self.assertTrue(result)
        mock_log.assert_called_with(
            "update_state: Detected explicit append for 'items'."
        )
        mock_append.assert_called_once_with(
            state["items"], ["new1", "new2"], "items", deduplicate=False
        )

    def test_handle_append_syntax_not_dict(self):
        """Test _handle_append_syntax with non-dict value"""
        state = {}
        value = "not a dict"

        result = _handle_append_syntax(state, "key", value)

        self.assertFalse(result)

    def test_handle_append_syntax_no_append_key(self):
        """Test _handle_append_syntax with dict missing 'append' key"""
        state = {}
        value = {"other": "value"}

        result = _handle_append_syntax(state, "key", value)

        self.assertFalse(result)

    @patch("firestore_service._perform_append")
    @patch("logging_util.info")
    def test_handle_append_syntax_creates_list(self, mock_log, mock_append):
        """Test _handle_append_syntax creates list if missing"""
        state = {}
        value = {"append": "single_item"}

        result = _handle_append_syntax(state, "new_key", value)

        self.assertTrue(result)
        self.assertEqual(state["new_key"], [])
        mock_append.assert_called_once()

    @patch("firestore_service._perform_append")
    @patch("logging_util.info")
    def test_handle_append_syntax_core_memories_dedup(self, mock_log, mock_append):
        """Test _handle_append_syntax with core_memories uses deduplication"""
        state = {"core_memories": ["memory1"]}
        value = {"append": ["memory2", "memory1"]}  # memory1 is duplicate

        result = _handle_append_syntax(state, "core_memories", value)

        self.assertTrue(result)
        # Verify deduplicate=True for core_memories
        mock_append.assert_called_once_with(
            state["core_memories"],
            ["memory2", "memory1"],
            "core_memories",
            deduplicate=True,
        )

    # Tests for _handle_core_memories_safeguard
    @patch("firestore_service._perform_append")
    @patch("logging_util.warning")
    def test_handle_core_memories_safeguard_triggered(self, mock_warning, mock_append):
        """Test _handle_core_memories_safeguard prevents overwrite"""
        state = {"core_memories": ["existing"]}
        value = ["new1", "new2"]  # Direct overwrite attempt

        result = _handle_core_memories_safeguard(state, "core_memories", value)

        self.assertTrue(result)
        mock_warning.assert_called_once()
        self.assertIn("CRITICAL SAFEGUARD", mock_warning.call_args[0][0])
        mock_append.assert_called_once_with(
            state["core_memories"], value, "core_memories", deduplicate=True
        )

    def test_handle_core_memories_safeguard_other_key(self):
        """Test _handle_core_memories_safeguard ignores other keys"""
        state = {"other_key": "value"}

        result = _handle_core_memories_safeguard(state, "other_key", ["new"])

        self.assertFalse(result)

    @patch("firestore_service._perform_append")
    @patch("logging_util.warning")
    def test_handle_core_memories_safeguard_creates_list(
        self, mock_warning, mock_append
    ):
        """Test _handle_core_memories_safeguard creates list if missing"""
        state = {}
        value = "single_memory"

        result = _handle_core_memories_safeguard(state, "core_memories", value)

        self.assertTrue(result)
        self.assertEqual(state["core_memories"], [])
        mock_append.assert_called_once()

    # Tests for _handle_dict_merge
    def test_handle_dict_merge_non_dict_value(self):
        """Test _handle_dict_merge with non-dict value"""
        state = {}

        result = _handle_dict_merge(state, "key", "not a dict")

        self.assertFalse(result)

    @patch("firestore_service.update_state_with_changes")
    def test_handle_dict_merge_existing_dict(self, mock_update):
        """Test _handle_dict_merge merges with existing dict"""
        state = {"config": {"a": 1, "b": 2}}
        value = {"b": 3, "c": 4}
        mock_update.return_value = {"a": 1, "b": 3, "c": 4}

        result = _handle_dict_merge(state, "config", value)

        self.assertTrue(result)
        mock_update.assert_called_once_with({"a": 1, "b": 2}, value)
        self.assertEqual(state["config"], {"a": 1, "b": 3, "c": 4})

    @patch("firestore_service.update_state_with_changes")
    def test_handle_dict_merge_new_dict(self, mock_update):
        """Test _handle_dict_merge creates new dict when key missing"""
        state = {}
        value = {"a": 1}
        mock_update.return_value = {"a": 1}

        result = _handle_dict_merge(state, "new_key", value)

        self.assertTrue(result)
        mock_update.assert_called_once_with({}, value)
        self.assertEqual(state["new_key"], {"a": 1})

    @patch("firestore_service.update_state_with_changes")
    def test_handle_dict_merge_overwrite_non_dict(self, mock_update):
        """Test _handle_dict_merge overwrites non-dict existing value"""
        state = {"key": "string_value"}
        value = {"a": 1}
        mock_update.return_value = {"a": 1}

        result = _handle_dict_merge(state, "key", value)

        self.assertTrue(result)
        # Should create new dict, not merge with string
        mock_update.assert_called_once_with({}, value)
        self.assertEqual(state["key"], {"a": 1})

    # Tests for _handle_delete_token
    @patch("logging_util.info")
    def test_handle_delete_token_deletes_existing(self, mock_log):
        """Test _handle_delete_token removes existing key"""
        state = {"key1": "value1", "key2": "value2"}

        result = _handle_delete_token(state, "key1", DELETE_TOKEN)

        self.assertTrue(result)
        self.assertNotIn("key1", state)
        self.assertIn("key2", state)
        mock_log.assert_called_with(
            "update_state: Deleting key 'key1' due to DELETE_TOKEN."
        )

    @patch("logging_util.info")
    def test_handle_delete_token_missing_key(self, mock_log):
        """Test _handle_delete_token with non-existent key"""
        state = {"other": "value"}

        result = _handle_delete_token(state, "missing", DELETE_TOKEN)

        self.assertTrue(result)
        self.assertEqual(state, {"other": "value"})
        mock_log.assert_called_with(
            "update_state: Attempted to delete key 'missing' but it doesn't exist."
        )

    def test_handle_delete_token_wrong_value(self):
        """Test _handle_delete_token with value not DELETE_TOKEN"""
        state = {"key": "value"}

        result = _handle_delete_token(state, "key", "not_delete_token")

        self.assertFalse(result)
        self.assertIn("key", state)  # Key not deleted

    # Tests for _handle_string_to_dict_update
    @patch("logging_util.info")
    def test_handle_string_to_dict_update_preserves_dict(self, mock_log):
        """Test _handle_string_to_dict_update preserves dict structure"""
        state = {"quest": {"name": "Main Quest", "level": 5}}
        value = "completed"

        result = _handle_string_to_dict_update(state, "quest", value)

        self.assertTrue(result)
        self.assertEqual(
            state["quest"], {"name": "Main Quest", "level": 5, "status": "completed"}
        )
        mock_log.assert_called_once()

    def test_handle_string_to_dict_update_non_dict_existing(self):
        """Test _handle_string_to_dict_update with non-dict existing value"""
        state = {"key": "string_value"}

        result = _handle_string_to_dict_update(state, "key", "new_value")

        self.assertFalse(result)

    def test_handle_string_to_dict_update_missing_key(self):
        """Test _handle_string_to_dict_update with missing key"""
        state = {}

        result = _handle_string_to_dict_update(state, "missing", "value")

        self.assertFalse(result)

    @patch("logging_util.info")
    def test_handle_string_to_dict_update_overwrites_status(self, mock_log):
        """Test _handle_string_to_dict_update overwrites existing status"""
        state = {"quest": {"name": "Quest", "status": "active"}}
        value = "completed"

        result = _handle_string_to_dict_update(state, "quest", value)

        self.assertTrue(result)
        self.assertEqual(state["quest"]["status"], "completed")
        self.assertEqual(state["quest"]["name"], "Quest")

    # Integration test for update_state_with_changes
    def test_update_state_with_changes_integration(self):
        """Test update_state_with_changes with various scenarios"""
        state = {
            "hp": 100,
            "inventory": ["sword", "shield"],
            "stats": {"str": 18, "dex": 14},
            "core_memories": ["memory1"],
            "to_delete": "value",
        }

        changes = {
            "hp": 80,  # Simple overwrite
            "inventory": {"append": ["potion"]},  # Append syntax
            "stats": {"con": 16},  # Dict merge
            "core_memories": ["memory2", "memory3"],  # Safeguarded
            "to_delete": DELETE_TOKEN,  # Deletion
            "new_key": "new_value",  # New key
        }

        with patch("logging_util.info"), patch("logging_util.warning"):
            result = update_state_with_changes(state, changes)

        # Verify results
        self.assertEqual(result["hp"], 80)
        self.assertIn("potion", result["inventory"])
        self.assertEqual(result["stats"], {"str": 18, "dex": 14, "con": 16})
        self.assertIn("memory1", result["core_memories"])  # Original preserved
        self.assertIn("memory2", result["core_memories"])  # New added
        self.assertNotIn("to_delete", result)
        self.assertEqual(result["new_key"], "new_value")


if __name__ == "__main__":
    unittest.main(verbosity=2)
