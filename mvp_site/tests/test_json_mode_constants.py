#!/usr/bin/env python3
"""
Test that constants have been updated for JSON mode
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site import constants


class TestJSONModeConstants(unittest.TestCase):
    """Test suite for JSON mode constant updates"""

    def test_character_creation_reminder_no_state_updates(self):
        """Test that CHARACTER_DESIGN_REMINDER doesn't instruct to include STATE_UPDATES_PROPOSED"""
        reminder = constants.CHARACTER_DESIGN_REMINDER

        # Should NOT contain the old instruction
        assert "[STATE_UPDATES_PROPOSED]" not in reminder, (
            "CHARACTER_DESIGN_REMINDER should not instruct to include STATE_UPDATES_PROPOSED blocks"
        )
        assert "MANDATORY: Include [STATE_UPDATES_PROPOSED]" not in reminder, (
            "Should not have mandatory STATE_UPDATES_PROPOSED instruction"
        )

        # Should contain JSON guidance for state updates
        assert "State updates must be included in a JSON field" in reminder, (
            "Should mention that state updates go in JSON field"
        )
        assert "not in the narrative text" in reminder, (
            "Should mention that state updates don't go in narrative"
        )

    def test_character_creation_reminder_maintains_other_instructions(self):
        """Test that other important instructions are still present"""
        reminder = constants.CHARACTER_DESIGN_REMINDER

        # Should still have these important instructions
        assert "CRITICAL REMINDER" in reminder
        assert "character design" in reminder
        assert "numeric responses" in reminder
        assert "selections from the presented list" in reminder


if __name__ == "__main__":
    unittest.main()
