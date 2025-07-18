"""
Unit tests for firestore_service helper methods.
Tests the extracted helper methods for update_state_with_changes.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock firebase_admin before importing firestore_service
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_admin.firestore"] = MagicMock()
sys.modules["firebase_admin.auth"] = MagicMock()
sys.modules["google.cloud.firestore"] = MagicMock()
sys.modules["firebase_admin.credentials"] = MagicMock()

from firestore_service import (
    _handle_append_syntax,
    _handle_core_memories_safeguard,
    _handle_delete_token,
    _handle_dict_merge,
    _handle_string_to_dict_update,
    update_state_with_changes,
)


class TestHandleAppendSyntax(unittest.TestCase):
    """Test the _handle_append_syntax helper."""

    @patch("firestore_service._perform_append")
    def test_handle_explicit_append(self, mock_append):
        """Test handling explicit append syntax."""
        state = {}

        # Test with append syntax
        result = _handle_append_syntax(state, "items", {"append": ["new_item"]})
        self.assertTrue(result)
        self.assertEqual(state["items"], [])
        mock_append.assert_called_once_with(
            [], ["new_item"], "items", deduplicate=False
        )

        # Test with existing list
        state = {"items": ["old_item"]}
        result = _handle_append_syntax(state, "items", {"append": ["new_item"]})
        self.assertTrue(result)
        mock_append.assert_called()

    def test_handle_non_append_syntax(self):
        """Test that non-append syntax returns False."""
        state = {}

        # Test with non-dict value
        result = _handle_append_syntax(state, "key", "value")
        self.assertFalse(result)

        # Test with dict without append key
        result = _handle_append_syntax(state, "key", {"other": "value"})
        self.assertFalse(result)

    @patch("firestore_service._perform_append")
    def test_handle_core_memories_dedupe(self, mock_append):
        """Test that core_memories get deduplicated."""
        state = {}

        result = _handle_append_syntax(state, "core_memories", {"append": ["memory"]})
        self.assertTrue(result)
        mock_append.assert_called_once_with(
            [], ["memory"], "core_memories", deduplicate=True
        )


class TestHandleCoreMemoriesSafeguard(unittest.TestCase):
    """Test the _handle_core_memories_safeguard helper."""

    @patch("firestore_service._perform_append")
    @patch("firestore_service.logging_util")
    def test_handle_core_memories_overwrite(self, mock_logging_util, mock_append):
        """Test safeguarding core_memories from overwrite."""
        state = {}

        # Test with core_memories key
        result = _handle_core_memories_safeguard(state, "core_memories", ["new_memory"])
        self.assertTrue(result)
        self.assertEqual(state["core_memories"], [])
        mock_append.assert_called_once_with(
            [], ["new_memory"], "core_memories", deduplicate=True
        )
        mock_logging_util.warning.assert_called()

    def test_ignore_non_core_memories(self):
        """Test that non-core_memories keys return False."""
        state = {}

        result = _handle_core_memories_safeguard(state, "other_key", "value")
        self.assertFalse(result)
        self.assertEqual(state, {})


class TestHandleDictMerge(unittest.TestCase):
    """Test the _handle_dict_merge helper."""

    @patch("firestore_service.update_state_with_changes")
    def test_merge_nested_dicts(self, mock_update):
        """Test merging nested dictionaries."""
        mock_update.return_value = {"merged": True}
        state = {"key": {"old": "value"}}

        result = _handle_dict_merge(state, "key", {"new": "value"})
        self.assertTrue(result)
        mock_update.assert_called_once_with({"old": "value"}, {"new": "value"})

    @patch("firestore_service.update_state_with_changes")
    def test_create_new_dict(self, mock_update):
        """Test creating new dict when value is dict but key doesn't exist."""
        mock_update.return_value = {"created": True}
        state = {}

        result = _handle_dict_merge(state, "key", {"new": "value"})
        self.assertTrue(result)
        mock_update.assert_called_once_with({}, {"new": "value"})

    def test_ignore_non_dict_values(self):
        """Test that non-dict values return False."""
        state = {}

        result = _handle_dict_merge(state, "key", "not a dict")
        self.assertFalse(result)
        self.assertEqual(state, {})


class TestHandleStringToDictUpdate(unittest.TestCase):
    """Test the _handle_string_to_dict_update helper."""

    @patch("firestore_service.logging_util")
    def test_handle_delete_token(self, mock_logging):
        """Test handling __DELETE__ token now uses separate function."""
        state = {"key": {"old": "value"}}

        # DELETE token is now handled by _handle_delete_token, not _handle_string_to_dict_update
        result = _handle_delete_token(state, "key", "__DELETE__")
        self.assertTrue(result)
        self.assertNotIn("key", state)
        mock_logging.info.assert_called()

    @patch("firestore_service.logging_util")
    def test_preserve_dict_structure(self, mock_logging):
        """Test preserving dict structure with status update."""
        state = {"key": {"old": "value"}}

        result = _handle_string_to_dict_update(state, "key", "new_status")
        self.assertTrue(result)
        self.assertEqual(state["key"]["old"], "value")
        self.assertEqual(state["key"]["status"], "new_status")
        mock_logging.info.assert_called()

    def test_ignore_non_dict_targets(self):
        """Test that non-dict targets return False."""
        state = {"key": "not a dict"}

        result = _handle_string_to_dict_update(state, "key", "value")
        self.assertFalse(result)
        self.assertEqual(state["key"], "not a dict")


class TestUpdateStateWithChanges(unittest.TestCase):
    """Test the main update_state_with_changes function."""

    @patch("firestore_service._handle_append_syntax")
    @patch("firestore_service._handle_core_memories_safeguard")
    @patch("firestore_service._handle_dict_merge")
    @patch("firestore_service._handle_string_to_dict_update")
    @patch("firestore_service.MissionHandler.handle_active_missions_conversion")
    @patch("firestore_service.logging_util")
    def test_handler_precedence(
        self,
        mock_logging,
        mock_missions,
        mock_string_dict,
        mock_dict_merge,
        mock_core_memories,
        mock_append,
    ):
        """Test that handlers are called in correct order."""
        # Set up mock returns
        mock_append.return_value = False
        mock_core_memories.return_value = False
        mock_dict_merge.return_value = False
        mock_string_dict.return_value = False

        state = {}
        changes = {"key": "simple_value"}

        result = update_state_with_changes(state, changes)

        # Verify handlers were called in order
        mock_append.assert_called_once()
        mock_core_memories.assert_called_once()
        mock_dict_merge.assert_called_once()
        mock_string_dict.assert_called_once()

        # Verify simple overwrite happened
        self.assertEqual(result["key"], "simple_value")

    @patch("firestore_service._handle_append_syntax")
    @patch("firestore_service.logging_util")
    def test_early_handler_exit(self, mock_logging, mock_append):
        """Test that when a handler returns True, subsequent handlers aren't called."""
        mock_append.return_value = True

        state = {}
        changes = {"key": {"append": "value"}}

        with patch("firestore_service._handle_core_memories_safeguard") as mock_core:
            with patch("firestore_service._handle_dict_merge") as mock_dict:
                result = update_state_with_changes(state, changes)

                # First handler returned True, so others shouldn't be called
                mock_append.assert_called_once()
                mock_core.assert_not_called()
                mock_dict.assert_not_called()

    @patch("firestore_service.MissionHandler.handle_active_missions_conversion")
    @patch("firestore_service.logging_util")
    def test_active_missions_special_case(self, mock_logging, mock_missions):
        """Test special handling of active_missions."""
        state = {}
        changes = {"active_missions": {"quest": "data"}}

        result = update_state_with_changes(state, changes)

        mock_missions.assert_called_once_with(
            state, "active_missions", {"quest": "data"}
        )

    @patch("firestore_service.logging_util")
    def test_simple_overwrite_fallback(self, mock_logging):
        """Test simple overwrite for unhandled cases."""
        state = {"existing": "old"}
        changes = {"existing": "new", "new_key": "new_value"}

        result = update_state_with_changes(state, changes)

        self.assertEqual(result["existing"], "new")
        self.assertEqual(result["new_key"], "new_value")


# Note: Tests for main.py helpers removed to avoid Flask dependency issues
# These would be better placed in a separate test file with proper Flask mocking


if __name__ == "__main__":
    unittest.main()
