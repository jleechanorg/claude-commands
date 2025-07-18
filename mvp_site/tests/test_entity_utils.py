"""
Tests for entity utility functions.
"""

import os
import sys
import unittest

# Add the parent directory to the path so we can import from mvp_site
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from entity_utils import filter_unknown_entities, is_unknown_entity


class TestEntityUtils(unittest.TestCase):
    """Test entity utility functions"""

    def test_filter_unknown_entities_removes_unknown(self):
        """Test that 'Unknown' entities are filtered out"""
        entities = ["Alice", "Unknown", "Bob", "Charlie"]
        filtered = filter_unknown_entities(entities)
        self.assertEqual(filtered, ["Alice", "Bob", "Charlie"])

    def test_filter_unknown_entities_case_insensitive(self):
        """Test that filtering is case-insensitive"""
        entities = ["Alice", "unknown", "UNKNOWN", "Bob", "Unknown"]
        filtered = filter_unknown_entities(entities)
        self.assertEqual(filtered, ["Alice", "Bob"])

    def test_filter_unknown_entities_empty_list(self):
        """Test filtering empty list"""
        entities = []
        filtered = filter_unknown_entities(entities)
        self.assertEqual(filtered, [])

    def test_filter_unknown_entities_only_unknown(self):
        """Test filtering list with only 'Unknown' entities"""
        entities = ["Unknown", "unknown", "UNKNOWN"]
        filtered = filter_unknown_entities(entities)
        self.assertEqual(filtered, [])

    def test_filter_unknown_entities_no_unknown(self):
        """Test filtering list with no 'Unknown' entities"""
        entities = ["Alice", "Bob", "Charlie"]
        filtered = filter_unknown_entities(entities)
        self.assertEqual(filtered, ["Alice", "Bob", "Charlie"])

    def test_is_unknown_entity_true_cases(self):
        """Test is_unknown_entity returns True for unknown entities"""
        self.assertTrue(is_unknown_entity("Unknown"))
        self.assertTrue(is_unknown_entity("unknown"))
        self.assertTrue(is_unknown_entity("UNKNOWN"))
        self.assertTrue(is_unknown_entity("UnKnOwN"))

    def test_is_unknown_entity_false_cases(self):
        """Test is_unknown_entity returns False for known entities"""
        self.assertFalse(is_unknown_entity("Alice"))
        self.assertFalse(is_unknown_entity("Bob"))
        self.assertFalse(is_unknown_entity("Unknown Person"))
        self.assertFalse(is_unknown_entity(""))
        self.assertFalse(is_unknown_entity("Known"))

    def test_filter_unknown_entities_preserves_order(self):
        """Test that filtering preserves the original order"""
        entities = ["Alice", "Unknown", "Bob", "unknown", "Charlie", "UNKNOWN"]
        filtered = filter_unknown_entities(entities)
        self.assertEqual(filtered, ["Alice", "Bob", "Charlie"])


if __name__ == "__main__":
    unittest.main()
