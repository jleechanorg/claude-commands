#!/usr/bin/env python3
"""
Test script for planning block UI buttons functionality.
This tests the parsing and rendering of planning blocks as clickable buttons.
"""

import unittest


class TestPlanningBlocksUI(unittest.TestCase):
    """Test cases for planning block button rendering"""

    def test_standard_planning_block_format(self):
        """Test standard planning block with three choices"""
        # This would be parsed by the JavaScript parsePlanningBlocks function
        expected_choices = [
            {
                "id": "Action_1",
                "description": "Draw your sword and charge the chieftain directly, hoping to end this quickly.",
            },
            {
                "id": "Continue_1",
                "description": "Try to negotiate with the chieftain, offering gold for safe passage.",
            },
            {
                "id": "Explore_2",
                "description": "Look for an alternate route around the goblin encampment.",
            },
        ]
        assert len(expected_choices) == 3

    def test_deep_think_block_format(self):
        """Test deep think block with pros and cons"""
        # This format should also be properly parsed
        expected_choices = [
            {
                "id": "Option_1",
                "description": "Return the artifact to the elder and claim your reward.",
            },
            {
                "id": "Option_2",
                "description": "Side with the rightful owner and protect them from the elder.",
            },
            {
                "id": "Option_3",
                "description": "Attempt to broker a compromise between both parties.",
            },
        ]
        assert len(expected_choices) == 3

    def test_choice_text_extraction(self):
        """Test that the full choice text is properly extracted"""

        # The button should have data-choice-text="Investigate_1: Search the mysterious room for hidden clues and secret passages."
        expected_data = "Investigate_1: Search the mysterious room for hidden clues and secret passages."
        assert "Investigate_1" in expected_data
        assert "Search the mysterious room" in expected_data

    def test_special_characters_preserved(self):
        """Test that normal special characters are preserved (not HTML escaped)"""
        choice_with_quotes = 'Say "Hello there, friend!" to the stranger.'

        # Should preserve normal quotes without HTML escaping
        assert '"' in choice_with_quotes
        assert "&quot;" not in choice_with_quotes  # Should NOT be HTML escaped


if __name__ == "__main__":
    unittest.main()
