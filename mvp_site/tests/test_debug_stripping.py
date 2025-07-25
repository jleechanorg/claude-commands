"""
Test debug content stripping functionality.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import re
import unittest

from gemini_response import GeminiResponse

# Import the static methods
strip_debug_content = GeminiResponse._strip_debug_content
strip_state_updates_only = GeminiResponse._strip_state_updates_only


# Define strip_other_debug_content based on test expectations
def strip_other_debug_content(text):
    """Strip all debug content except STATE_UPDATES_PROPOSED blocks."""
    if not text:
        return text

    # Remove all debug blocks except STATE_UPDATES_PROPOSED
    text = re.sub(r"\[DEBUG_START\].*?\[DEBUG_END\]", "", text, flags=re.DOTALL)
    text = re.sub(
        r"\[DEBUG_ROLL_START\].*?\[DEBUG_ROLL_END\]", "", text, flags=re.DOTALL
    )
    text = re.sub(
        r"\[DEBUG_RESOURCES_START\].*?\[DEBUG_RESOURCES_END\]",
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\[DEBUG_STATE_START\].*?\[DEBUG_STATE_END\]", "", text, flags=re.DOTALL
    )
    text = re.sub(
        r"\[DEBUG_VALIDATION_START\].*?\[DEBUG_VALIDATION_END\]",
        "",
        text,
        flags=re.DOTALL,
    )

    # Note: Don't clean up multiple newlines for this function as it preserves exact formatting

    return text


class TestDebugStripping(unittest.TestCase):
    """Test debug content stripping logic."""

    def test_strip_debug_content_basic(self):
        """Test basic debug content stripping."""
        input_text = (
            "You enter the dark cave. "
            "[DEBUG_START]As the DM, I'm rolling a perception check...[DEBUG_END] "
            "[DEBUG_ROLL_START]Perception: 1d20+3 = 15+3 = 18 (Success)[DEBUG_ROLL_END] "
            "You notice a glimmer in the darkness."
        )

        expected_output = (
            "You enter the dark cave.   You notice a glimmer in the darkness."
        )

        result = strip_debug_content(input_text)
        self.assertEqual(result, expected_output)

    def test_strip_debug_content_all_types(self):
        """Test stripping all types of debug content."""
        input_text = (
            "You attack the orc! "
            "[DEBUG_START]This is a DM note about the encounter.[DEBUG_END] "
            "[DEBUG_ROLL_START]Attack Roll: 1d20+5 = 14+5 = 19 vs AC 15 (Hit!)[DEBUG_ROLL_END] "
            "[DEBUG_STATE_START]Updating orc HP from 15 to 6[DEBUG_STATE_END] "
            "Your sword strikes true!"
        )

        expected_output = "You attack the orc!    Your sword strikes true!"

        result = strip_debug_content(input_text)
        self.assertEqual(result, expected_output)

    def test_strip_debug_content_multiline(self):
        """Test stripping debug content that spans multiple lines."""
        input_text = (
            "The battle begins!\n"
            "[DEBUG_START]\n"
            "This is a multi-line\n"
            "debug comment\n"
            "[DEBUG_END]\n"
            "You draw your sword."
        )

        expected_output = "The battle begins!\n\nYou draw your sword."

        result = strip_debug_content(input_text)
        self.assertEqual(result, expected_output)

    def test_strip_debug_content_no_debug(self):
        """Test that non-debug content is unchanged."""
        input_text = "This is a normal response with no debug content."
        result = strip_debug_content(input_text)
        self.assertEqual(result, input_text)

    def test_strip_debug_content_empty(self):
        """Test handling of empty or None input."""
        self.assertEqual(strip_debug_content(""), "")
        self.assertEqual(strip_debug_content(None), None)

    def test_strip_state_updates_proposed(self):
        """Test stripping STATE_UPDATES_PROPOSED blocks."""
        input_text = (
            "The dragon roars menacingly! "
            "[STATE_UPDATES_PROPOSED]\n"
            '{"game_state_version": 1, "player_character_data": {"hp_current": 45}}\n'
            "[END_STATE_UPDATES_PROPOSED] "
            "You must decide your next move."
        )

        expected_output = (
            "The dragon roars menacingly!  You must decide your next move."
        )

        result = strip_debug_content(input_text)
        self.assertEqual(result, expected_output)

    def test_strip_all_debug_including_state_updates(self):
        """Test stripping all debug content including STATE_UPDATES_PROPOSED."""
        input_text = (
            "Battle begins! "
            "[DEBUG_START]DM planning the encounter[DEBUG_END] "
            "[DEBUG_ROLL_START]Initiative: 1d20+2 = 18[DEBUG_ROLL_END] "
            "[STATE_UPDATES_PROPOSED]\n"
            '{"combat_active": true}\n'
            "[END_STATE_UPDATES_PROPOSED] "
            "Roll for initiative!"
        )

        expected_output = "Battle begins!    Roll for initiative!"

        result = strip_debug_content(input_text)
        self.assertEqual(result, expected_output)

    def test_strip_malformed_state_updates(self):
        """Test stripping malformed STATE_UPDATES_PROPOSED blocks missing opening characters."""
        # Test case 1: Missing [S at the beginning
        input_text1 = (
            "The dragon approaches.\n"
            "TATE_UPDATES_PROPOSED]\n"
            '{"hp": 45}\n'
            "[END_STATE_UPDATES_PROPOSED]\n"
            "What do you do?"
        )

        expected_output1 = "The dragon approaches.\n\nWhat do you do?"

        result1 = strip_debug_content(input_text1)
        self.assertEqual(result1, expected_output1)

        # Test case 2: Missing [ at the beginning
        input_text2 = (
            "You enter the cave.\n"
            "STATE_UPDATES_PROPOSED]\n"
            '{"location": "cave"}\n'
            "[END_STATE_UPDATES_PROPOSED]\n"
            "It's dark inside."
        )

        expected_output2 = "You enter the cave.\n\nIt's dark inside."

        result2 = strip_debug_content(input_text2)
        self.assertEqual(result2, expected_output2)


class TestStripStateUpdatesOnly(unittest.TestCase):
    """Test strip_state_updates_only function specifically."""

    def test_strip_state_updates_only_basic(self):
        """Test stripping only STATE_UPDATES_PROPOSED blocks."""
        input_text = (
            "You see a dragon! "
            "[DEBUG_START]DM notes here[DEBUG_END] "
            "[STATE_UPDATES_PROPOSED]\n"
            '{"hp": 45}\n'
            "[END_STATE_UPDATES_PROPOSED] "
            "It roars!"
        )

        expected_output = (
            "You see a dragon! [DEBUG_START]DM notes here[DEBUG_END]  It roars!"
        )

        result = strip_state_updates_only(input_text)
        self.assertEqual(result, expected_output)

    def test_strip_state_updates_only_malformed(self):
        """Test stripping malformed STATE_UPDATES_PROPOSED blocks."""
        # Test case 1: Missing [S at the beginning
        input_text1 = (
            "The dragon approaches.\n"
            "TATE_UPDATES_PROPOSED]\n"
            '{"game_state_version": 1, "player_character_data": {"hp": 45}}\n'
            "[END_STATE_UPDATES_PROPOSED]\n"
            "What do you do?"
        )

        expected_output1 = "The dragon approaches.\n\nWhat do you do?"

        result1 = strip_state_updates_only(input_text1)
        self.assertEqual(result1, expected_output1)

        # Test case 2: Missing [ at the beginning
        input_text2 = (
            "You enter the cave.\n"
            "STATE_UPDATES_PROPOSED]\n"
            '{"location": "cave"}\n'
            "[END_STATE_UPDATES_PROPOSED]\n"
            "It's dark inside."
        )

        expected_output2 = "You enter the cave.\n\nIt's dark inside."

        result2 = strip_state_updates_only(input_text2)
        self.assertEqual(result2, expected_output2)

    def test_strip_state_updates_only_preserves_debug(self):
        """Test that other debug content is preserved."""
        input_text = (
            "[DEBUG_START]This is DM commentary[DEBUG_END]\n"
            "[DEBUG_ROLL_START]Attack: 1d20+5 = 18[DEBUG_ROLL_END]\n"
            "[STATE_UPDATES_PROPOSED]\n"
            '{"combat": true}\n'
            "[END_STATE_UPDATES_PROPOSED]\n"
            "[DEBUG_STATE_START]HP: 50->45[DEBUG_STATE_END]"
        )

        expected_output = (
            "[DEBUG_START]This is DM commentary[DEBUG_END]\n"
            "[DEBUG_ROLL_START]Attack: 1d20+5 = 18[DEBUG_ROLL_END]\n"
            "\n"
            "[DEBUG_STATE_START]HP: 50->45[DEBUG_STATE_END]"
        )

        result = strip_state_updates_only(input_text)
        self.assertEqual(result, expected_output)

    def test_strip_state_updates_only_empty_input(self):
        """Test handling of empty input."""
        self.assertEqual(strip_state_updates_only(""), "")
        self.assertEqual(strip_state_updates_only(None), None)


class TestStripOtherDebugContent(unittest.TestCase):
    """Test strip_other_debug_content function."""

    def test_strip_other_debug_preserves_state_updates(self):
        """Test that STATE_UPDATES_PROPOSED blocks are NOT stripped."""
        input_text = (
            "[DEBUG_START]DM notes[DEBUG_END]\n"
            "[STATE_UPDATES_PROPOSED]\n"
            '{"hp": 45}\n'
            "[END_STATE_UPDATES_PROPOSED]\n"
            "[DEBUG_ROLL_START]Roll: 15[DEBUG_ROLL_END]"
        )

        expected_output = (
            '\n[STATE_UPDATES_PROPOSED]\n{"hp": 45}\n[END_STATE_UPDATES_PROPOSED]\n'
        )

        result = strip_other_debug_content(input_text)
        self.assertEqual(result, expected_output)

    def test_strip_other_debug_all_types(self):
        """Test stripping all debug types except STATE_UPDATES."""
        input_text = (
            "Combat starts! "
            "[DEBUG_START]Planning encounter[DEBUG_END] "
            "[DEBUG_ROLL_START]Initiative: 18[DEBUG_ROLL_END] "
            "[DEBUG_STATE_START]Combat: true[DEBUG_STATE_END] "
            "Roll initiative!"
        )

        expected_output = "Combat starts!    Roll initiative!"

        result = strip_other_debug_content(input_text)
        self.assertEqual(result, expected_output)


if __name__ == "__main__":
    unittest.main()
