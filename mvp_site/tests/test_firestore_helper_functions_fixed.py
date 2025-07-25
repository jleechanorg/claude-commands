#!/usr/bin/env python3
"""
Phase 4: Helper function tests for firestore_service.py (fixed version)
Test _truncate_log_json and _perform_append functions
"""

import json
import os

# Add parent directory to path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from firestore_service import _perform_append, _truncate_log_json


class TestFirestoreHelperFunctions(unittest.TestCase):
    """Test helper functions in firestore_service.py"""

    # Tests for _truncate_log_json
    def test_truncate_log_json_small_data(self):
        """Test _truncate_log_json with data smaller than max_lines"""
        data = {"key1": "value1", "key2": "value2"}
        result = _truncate_log_json(data, max_lines=10)

        # Small data should not be truncated
        self.assertIn("key1", result)
        self.assertIn("key2", result)
        self.assertNotIn("truncated", result.lower())

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
        self.assertEqual(len(lines), 5)
        self.assertIn("truncated", lines[-1].lower())

    def test_truncate_log_json_exact_boundary(self):
        """Test _truncate_log_json with exactly max_lines"""
        data = {"line1": 1, "line2": 2, "line3": 3}
        formatted = json.dumps(data, indent=2)
        line_count = len(formatted.split("\n"))

        result = _truncate_log_json(data, max_lines=line_count)

        # Should not truncate when exactly at boundary
        self.assertNotIn("truncated", result.lower())

    def test_truncate_log_json_invalid_json(self):
        """Test _truncate_log_json exception handling with non-serializable data"""

        # Create object that can't be JSON serialized
        class NonSerializable:
            pass

        data = {"key": NonSerializable()}

        # Should fall back to string representation
        result = _truncate_log_json(data, max_lines=10)

        # Should contain string representation
        self.assertIn("NonSerializable", result)

    def test_truncate_log_json_circular_reference(self):
        """Test _truncate_log_json with circular reference"""
        data = {"key": "value"}
        data["circular"] = data  # Create circular reference

        # Should handle without crashing
        result = _truncate_log_json(data, max_lines=10)
        self.assertIsInstance(result, str)

    def test_truncate_log_json_empty_data(self):
        """Test _truncate_log_json with empty data"""
        result = _truncate_log_json({}, max_lines=10)
        self.assertEqual(result.strip(), "{}")

    def test_truncate_log_json_none_data(self):
        """Test _truncate_log_json with None"""
        result = _truncate_log_json(None, max_lines=10)
        self.assertEqual(result.strip(), "null")

    # Tests for _perform_append
    @patch("logging_util.info")
    def test_perform_append_single_item(self, mock_log):
        """Test _perform_append with single item (not a list)"""
        target_list = ["existing1", "existing2"]

        _perform_append(target_list, "new_item", "test_key", deduplicate=False)

        self.assertEqual(target_list, ["existing1", "existing2", "new_item"])
        mock_log.assert_called_once()
        self.assertIn("Added 1 new items", mock_log.call_args[0][0])

    @patch("logging_util.info")
    def test_perform_append_list_items(self, mock_log):
        """Test _perform_append with list of items"""
        target_list = ["existing"]
        items = ["item1", "item2", "item3"]

        _perform_append(target_list, items, "test_key", deduplicate=False)

        self.assertEqual(target_list, ["existing", "item1", "item2", "item3"])
        mock_log.assert_called_once()
        self.assertIn("Added 3 new items", mock_log.call_args[0][0])

    @patch("logging_util.info")
    def test_perform_append_empty_list(self, mock_log):
        """Test _perform_append with empty items list"""
        target_list = ["existing"]

        _perform_append(target_list, [], "test_key", deduplicate=False)

        self.assertEqual(target_list, ["existing"])  # Unchanged
        mock_log.assert_called_once()
        self.assertIn("No new items were added", mock_log.call_args[0][0])

    @patch("logging_util.info")
    def test_perform_append_deduplicate_true(self, mock_log):
        """Test _perform_append with deduplication enabled"""
        target_list = ["item1", "item2"]
        items = ["item2", "item3", "item1", "item4"]  # item1 and item2 are duplicates

        _perform_append(target_list, items, "test_key", deduplicate=True)

        # Only new items should be added
        self.assertEqual(target_list, ["item1", "item2", "item3", "item4"])
        mock_log.assert_called_once()
        self.assertIn("Added 2 new items", mock_log.call_args[0][0])

    @patch("logging_util.info")
    def test_perform_append_deduplicate_false(self, mock_log):
        """Test _perform_append with deduplication disabled"""
        target_list = ["item1", "item2"]
        items = ["item2", "item3", "item1"]  # Duplicates

        _perform_append(target_list, items, "test_key", deduplicate=False)

        # All items added regardless of duplicates
        self.assertEqual(target_list, ["item1", "item2", "item2", "item3", "item1"])
        mock_log.assert_called_once()
        self.assertIn("Added 3 new items", mock_log.call_args[0][0])

    @patch("logging_util.info")
    def test_perform_append_none_item(self, mock_log):
        """Test _perform_append with None as single item"""
        target_list = ["existing"]

        _perform_append(target_list, None, "test_key", deduplicate=False)

        self.assertEqual(target_list, ["existing", None])
        mock_log.assert_called_once()

    @patch("logging_util.info")
    def test_perform_append_complex_objects(self, mock_log):
        """Test _perform_append with complex objects"""
        target_list = [{"id": 1}]
        items = [{"id": 2}, {"id": 3, "data": {"nested": True}}]

        _perform_append(target_list, items, "test_key", deduplicate=False)

        self.assertEqual(len(target_list), 3)
        self.assertEqual(target_list[1]["id"], 2)
        self.assertEqual(target_list[2]["data"]["nested"], True)

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
        self.assertEqual(len(target_list), 3)
        self.assertEqual(target_list[2]["id"], 3)
        mock_log.assert_called_once()
        self.assertIn("Added 1 new items", mock_log.call_args[0][0])

    def test_truncate_log_json_max_lines_parameter(self):
        """Test _truncate_log_json respects max_lines parameter"""
        # Create data that will format to multiple lines
        data = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8}

        result = _truncate_log_json(data, max_lines=3)
        lines = result.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("truncated", lines[-1].lower())

    @patch("logging_util.info")
    def test_perform_append_all_duplicates(self, mock_log):
        """Test _perform_append when all items are duplicates"""
        target_list = ["item1", "item2", "item3"]
        items = ["item1", "item2", "item3"]  # All duplicates

        _perform_append(target_list, items, "test_key", deduplicate=True)

        # No items should be added
        self.assertEqual(target_list, ["item1", "item2", "item3"])
        mock_log.assert_called_once()
        self.assertIn("No new items were added", mock_log.call_args[0][0])
        self.assertIn("duplicates may have been found", mock_log.call_args[0][0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
