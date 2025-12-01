"""Test that 'Unknown' is properly filtered from entity validation"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site.entity_validator import EntityValidator


class TestUnknownEntityFiltering(unittest.TestCase):
    def setUp(self):
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
        assert "Unknown" not in result.missing_entities
        assert "unknown" not in result.missing_entities

        # Should only report real missing entities
        assert "Sir Galahad" in result.missing_entities
        assert "Dragon" in result.missing_entities

    def test_empty_expected_entities_after_filtering(self):
        """Test behavior when only Unknown is in expected entities"""
        narrative = "A quiet moment in the journey."
        expected_entities = ["Unknown"]

        result = self.validator.validate_entity_presence(narrative, expected_entities)

        # Should pass validation since no real entities expected
        assert result.passed
        assert not result.retry_needed
        assert result.missing_entities == []


if __name__ == "__main__":
    unittest.main()
