"""Summary test demonstrating the Unknown entity fix"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dual_pass_generator import dual_pass_generator
from entity_validator import entity_validator


class TestUnknownEntityFixSummary(unittest.TestCase):
    """
    Summary test showing:
    1. The problem: Unknown was treated as a missing entity
    2. The fix: Filter Unknown from validation
    3. The result: No unnecessary dual-pass generation
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
        self.assertNotIn("Unknown", result.missing_entities)
        self.assertFalse(result.retry_needed)

        # Also test dual-pass generator
        def mock_callback(prompt):
            return narrative

        dual_result = dual_pass_generator.generate_with_dual_pass(
            initial_prompt="Continue the story",
            expected_entities=expected_entities_with_bug,
            location="Unknown",
            generation_callback=mock_callback,
        )

        print("3. THE RESULT:")
        print("   Dual-pass generator also filters 'Unknown'")
        print(f"   Second pass needed: {dual_result.second_pass is not None}")
        print(f"   Success on first pass: {dual_result.success}")
        print("\n✅ Fix verified: No unnecessary dual-pass for 'Unknown' entity!")

        self.assertIsNone(dual_result.second_pass)
        self.assertTrue(dual_result.success)

    def test_real_entities_still_validated(self):
        """Ensure real entities are still properly validated"""

        narrative = "The hero walks alone."
        expected = ["Hero", "Unknown", "Villain"]  # Mix of real and Unknown

        result = entity_validator.validate_entity_presence(narrative, expected)

        # Unknown filtered out, but Villain still missing
        self.assertNotIn("Unknown", result.missing_entities)
        self.assertIn("Villain", result.missing_entities)
        self.assertTrue(result.retry_needed)  # Because Villain is missing

        print("\n✅ Real entity validation still works correctly!")


if __name__ == "__main__":
    unittest.main(verbosity=2)
