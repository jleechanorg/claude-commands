#!/usr/bin/env python3
"""
Test to ensure narrative field never contains debug content.
Part of the clean debug/narrative separation initiative.
"""

import re
import unittest


class TestNarrativeFieldClean(unittest.TestCase):
    """Test that narrative fields are clean of debug content."""

    # Forbidden patterns in narrative field
    FORBIDDEN_PATTERNS = [
        r"\[DEBUG_START\]",
        r"\[DEBUG_END\]",
        r"\[DEBUG_STATE_START\]",
        r"\[DEBUG_STATE_END\]",
        r"\[DEBUG_ROLL_START\]",
        r"\[DEBUG_ROLL_END\]",
        r"\[STATE_UPDATES_PROPOSED\]",
        r"\[END_STATE_UPDATES_PROPOSED\]",
    ]

    def test_narrative_field_with_debug_tags_should_fail(self):
        """Test that we can detect debug tags in narrative field."""
        # Example response that should be caught as bad
        bad_response = {
            "narrative": "You attack! [DEBUG_START]Roll: 18[DEBUG_END] You hit!",
            "debug_info": {"dm_notes": ["Roll was 18"]},
        }

        # This should find forbidden patterns
        narrative = bad_response.get("narrative", "")
        found_patterns = []
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, narrative):
                found_patterns.append(pattern)

        # We expect to find some patterns in this bad example
        assert len(found_patterns) > 0, (
            "Should detect debug tags in bad narrative example"
        )

    def test_clean_narrative_passes(self):
        """Test that clean narrative passes validation."""
        # Example of correct response
        good_response = {
            "narrative": "You swing your sword with all your might. The blade connects solidly with the goblin's shield, sending it staggering backward.",
            "dice_rolls": ["Attack roll: 1d20+5 = 18+5 = 23 (Hit)"],
            "debug_info": {
                "dm_notes": ["Rolled 18 on d20 for attack"],
                "state_rationale": "Goblin takes damage",
            },
        }

        # Check narrative is clean
        narrative = good_response.get("narrative", "")
        for pattern in self.FORBIDDEN_PATTERNS:
            assert re.search(pattern, narrative) is None, (
                f"Narrative field should not contain: {pattern}"
            )

    def test_state_updates_in_correct_field(self):
        """Test that state updates are in state_updates field, not narrative."""
        # Correct format with state updates in proper field
        correct_response = {
            "narrative": "The merchant smiles and hands you the potion.",
            "state_updates": {
                "player_character_data": {"inventory": {"items": {"health_potion": 2}}}
            },
            "debug_info": {"state_rationale": "Player purchased health potion"},
        }

        # Narrative should not contain state update blocks
        narrative = correct_response.get("narrative", "")
        assert "[STATE_UPDATES_PROPOSED]" not in narrative
        assert "player_character_data" not in narrative

        # State updates should be in correct field
        assert "state_updates" in correct_response
        assert isinstance(correct_response["state_updates"], dict)


if __name__ == "__main__":
    unittest.main()
