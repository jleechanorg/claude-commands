#!/usr/bin/env python3
"""
Red/Green Test for word boundary bug in token_validator.py
Bug: SimpleTokenValidator uses substring matching, causing false positives
Example: "Gideon" matches in "Gideonville"
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validators.token_validator import SimpleTokenValidator


class TestWordBoundaryBug(unittest.TestCase):
    """Test cases demonstrating the word boundary bug."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = SimpleTokenValidator()

    def test_partial_word_false_positive(self):
        """Test that partial word matches cause false positives (BUG)."""
        # This test should FAIL with current implementation
        narrative = (
            "The party arrived at Gideonville, a town named after an ancient hero."
        )
        expected_entities = ["Gideon"]  # We're looking for the character Gideon

        result = self.validator.validate(narrative, expected_entities)

        # Current implementation will find "Gideon" in "Gideonville" (false positive)
        # This assertion should FAIL, demonstrating the bug
        self.assertEqual(result["entities_found"], [])
        self.assertFalse(result["all_entities_present"])

    def test_compound_word_false_positive(self):
        """Test compound words causing false positives."""
        # This test should FAIL with current implementation
        narrative = "They visited Rowanwood Forest, where ancient trees grew tall."
        expected_entities = ["Rowan"]  # We're looking for the character Rowan

        result = self.validator.validate(narrative, expected_entities)

        # Current implementation will find "Rowan" in "Rowanwood" (false positive)
        # This assertion should FAIL
        self.assertEqual(result["entities_found"], [])
        self.assertFalse(result["all_entities_present"])

    def test_possessive_false_positive(self):
        """Test possessive forms causing false positives."""
        # This test should FAIL with current implementation
        narrative = "In Marcus's shop, they found ancient artifacts. The Marcusson family owned it."
        expected_entities = ["Marcus"]  # We're looking for the character Marcus

        result = self.validator.validate(narrative, expected_entities)

        # Current implementation correctly finds "Marcus" in "Marcus's" (true positive)
        # But also incorrectly finds "Marcus" in "Marcusson" (false positive)
        # We need to check the actual mentions
        self.assertEqual(result["entities_found"], ["Marcus"])
        self.assertTrue(result["all_entities_present"])

    def test_true_positive_whole_word(self):
        """Test that whole word matches work correctly (should pass)."""
        # This test should PASS even with current implementation
        narrative = "Gideon stood ready. The knight Gideon was brave."
        expected_entities = ["Gideon"]

        result = self.validator.validate(narrative, expected_entities)

        # This should work correctly
        self.assertEqual(result["entities_found"], ["Gideon"])
        self.assertTrue(result["all_entities_present"])

    def test_case_variations(self):
        """Test case variations are handled correctly."""
        # This should PASS - case insensitive matching is correct
        narrative = "GIDEON shouted. Meanwhile, gideon prepared."
        expected_entities = ["Gideon"]

        result = self.validator.validate(narrative, expected_entities)

        self.assertEqual(result["entities_found"], ["Gideon"])
        self.assertTrue(result["all_entities_present"])


if __name__ == "__main__":
    print("Running Word Boundary Bug Tests (Red Phase - Expecting Failures)")
    print("=" * 60)
    unittest.main(verbosity=2)
