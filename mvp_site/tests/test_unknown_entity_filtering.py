"""Test that 'Unknown' is properly filtered from entity validation"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from dual_pass_generator import DualPassGenerator
from entity_validator import EntityValidator


class TestUnknownEntityFiltering(unittest.TestCase):
    def setUp(self):
        self.generator = DualPassGenerator()
        self.validator = EntityValidator()

    def test_unknown_filtered_from_validation(self):
        """Test that 'Unknown' entity is filtered out during validation"""
        narrative = "The brave knight enters the chamber."
        expected_entities = ["Sir Galahad", "Unknown", "Dragon"]

        # Test validator directly
        result = self.validator.validate_entity_presence(
            narrative, expected_entities, location="Unknown"
        )

        # Unknown should not be in missing entities
        self.assertNotIn("Unknown", result.missing_entities)
        self.assertNotIn("unknown", result.missing_entities)

        # Should only report real missing entities
        self.assertIn("Sir Galahad", result.missing_entities)
        self.assertIn("Dragon", result.missing_entities)

    def test_dual_pass_filters_unknown(self):
        """Test that dual pass generation filters Unknown from expected entities"""

        def mock_generation_callback(prompt):
            return "The hero stands ready."

        result = self.generator.generate_with_dual_pass(
            initial_prompt="Test prompt",
            expected_entities=["Hero", "Unknown"],
            location="Unknown",
            generation_callback=mock_generation_callback,
        )

        # First pass should not fail due to Unknown
        self.assertNotIn(
            "Unknown", result.first_pass.validation_result.missing_entities
        )
        self.assertNotIn(
            "unknown", result.first_pass.validation_result.missing_entities
        )

    def test_empty_expected_entities_after_filtering(self):
        """Test behavior when only Unknown is in expected entities"""
        narrative = "A quiet moment in the journey."
        expected_entities = ["Unknown"]

        result = self.validator.validate_entity_presence(narrative, expected_entities)

        # Should pass validation since no real entities expected
        self.assertTrue(result.passed)
        self.assertFalse(result.retry_needed)
        self.assertEqual(result.missing_entities, [])


if __name__ == "__main__":
    unittest.main()
