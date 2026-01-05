"""
SIMPLIFIED RED-GREEN test for temporal correction misleading success message bug.

Tests the specific code block (world_logic.py:809-819) directly without full integration.
"""

import unittest

from mvp_site.agent_prompts import build_temporal_warning_message
from mvp_site.world_logic import MAX_TEMPORAL_CORRECTION_ATTEMPTS


class TestTemporalMisleadingMessageSimple(unittest.TestCase):
    """
    Simplified test demonstrating the misleading success message bug.

    Bug Location: mvp_site/world_logic.py lines 809-819

    Current Behavior (BUG):
    - When temporal_correction_attempts > MAX (e.g., 3 > 2), system gives up
    - Line 809 checks: if temporal_correction_attempts > 0:
    - Lines 812-813 say: "corrections were required to fix the timeline continuity"
    - This is MISLEADING because corrections DID NOT fix the timeline (max attempts exceeded)

    Expected Behavior:
    - Message should only say "fix" when corrections actually SUCCEEDED
    - When max attempts exceeded, message should say "exceeded" or "gave up"
    """

    def test_misleading_message_when_max_attempts_exceeded(self):
        """
        🔴 RED PHASE: Demonstrate the bug with a simple assertion.

        This test should FAIL until the bug is fixed.
        """
        # Simulate the scenario: temporal correction exceeded max attempts
        temporal_correction_attempts = 3  # EXCEEDED (gave up)

        temporal_warning = build_temporal_warning_message(
            temporal_correction_attempts, max_attempts=MAX_TEMPORAL_CORRECTION_ATTEMPTS
        )

        # ASSERTION: Verify fix is working correctly
        # When temporal_correction_attempts > MAX, message should mention "exceeded"
        if (
            temporal_warning
            and temporal_correction_attempts > MAX_TEMPORAL_CORRECTION_ATTEMPTS
        ):
            # Check that warning mentions "exceeded" (NOT "fix")
            self.assertIn(
                "exceeded",
                temporal_warning.lower(),
                f"When max attempts exceeded, warning should mention 'exceeded'.\n"
                f"temporal_correction_attempts={temporal_correction_attempts}\n"
                f"Actual warning: '{temporal_warning}'",
            )

            # Ensure it does NOT falsely claim success with "fix"
            # Note: "fix" might appear in context, but shouldn't claim corrections "fixed" it
            if "required to fix the timeline continuity" in temporal_warning.lower():
                self.fail(
                    f"🔴 BUG STILL EXISTS: Warning falsely claims corrections 'fixed' timeline when max attempts were exceeded!\n"
                    f"temporal_correction_attempts={temporal_correction_attempts} > MAX={MAX_TEMPORAL_CORRECTION_ATTEMPTS}\n"
                    f"Actual warning: '{temporal_warning}'"
                )

        # Verify warning was created
        self.assertIsNotNone(
            temporal_warning,
            "Warning should exist when temporal_correction_attempts > 0",
        )

    def test_correct_message_when_corrections_succeed(self):
        """
        Control test: When corrections succeed (attempts <= MAX), message is appropriate.

        This test should PASS even with current buggy code.
        """
        temporal_correction_attempts = 1  # SUCCESS (within limits)

        temporal_warning = build_temporal_warning_message(
            temporal_correction_attempts, max_attempts=MAX_TEMPORAL_CORRECTION_ATTEMPTS
        )

        # When corrections succeed (attempts <= MAX), saying "fix" is correct
        self.assertIsNotNone(
            temporal_warning, "Warning should exist when corrections succeeded"
        )
        self.assertIn(
            "fix",
            temporal_warning.lower(),
            "Message can say 'fix' when corrections succeeded",
        )
        self.assertEqual(temporal_correction_attempts, 1, "1 correction should succeed")


if __name__ == "__main__":
    unittest.main()
