"""Summary test demonstrating the Unknown entity fix"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site.entity_validator import entity_validator


class TestUnknownEntityFixSummary(unittest.TestCase):
    """
    Summary test showing:
    1. The problem: Unknown was treated as a missing entity
    2. The fix: Filter Unknown from validation
    3. The result: No unnecessary retries
    """

    def test_complete_fix_demonstration(self):
        """Complete demonstration of the fix"""

        print("\n=== Unknown Entity Fix Demonstration ===\n")

        # Scenario: A narrative that doesn't mention "Unknown"
        narrative = "The brave knight Sir Galahad enters the mysterious chamber."

        # Problem: When location defaults to 'Unknown', it gets added to expected entities
        expected_entities_with_bug = ["Sir Galahad", "Unknown"]

        print("1. THE PROBLEM:")
        print(f"   Expected entities: {expected_entities_with_bug}")
        print(f"   Narrative: '{narrative}'")
        print("   Without fix: 'Unknown' would be flagged as missing\n")

        # The fix in action
        result = entity_validator.validate_entity_presence(
            narrative,
            expected_entities_with_bug,
            location="Unknown",  # Default location
        )

        print("2. THE FIX:")
        print("   Entity validator filters out 'Unknown'")
        print(f"   Missing entities: {result.missing_entities}")
        print(f"   Retry needed: {result.retry_needed}\n")

        # Verify the fix
        assert "Unknown" not in result.missing_entities
        assert not result.retry_needed

        print("3. THE RESULT:")
        print(
            "   Entity validation no longer triggers unnecessary retries for 'Unknown'"
        )
        print("\n✅ Fix verified: No unnecessary retry for 'Unknown' entity!")

    def test_real_entities_still_validated(self):
        """Ensure real entities are still properly validated"""

        narrative = "The hero walks alone."
        expected = ["Hero", "Unknown", "Villain"]  # Mix of real and Unknown

        result = entity_validator.validate_entity_presence(narrative, expected)

        # Unknown filtered out, but Villain still missing
        assert "Unknown" not in result.missing_entities
        assert "Villain" in result.missing_entities
        assert result.retry_needed  # Because Villain is missing

        print("\n✅ Real entity validation still works correctly!")


if __name__ == "__main__":
    unittest.main(verbosity=2)
