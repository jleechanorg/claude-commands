"""
Isolated unit test for debug content stripping functionality.
Tests the strip_debug_content function without any Flask dependencies.
"""

import re
import unittest


def strip_debug_content_isolated(text):
    """
    Isolated version of strip_debug_content for testing.
    Strip debug content from AI response text while preserving the rest.
    """
    if not text:
        return text

    # Remove DM commentary blocks
    text = re.sub(r"\[DEBUG_START\].*?\[DEBUG_END\]", "", text, flags=re.DOTALL)

    # Remove dice roll blocks
    text = re.sub(
        r"\[DEBUG_ROLL_START\].*?\[DEBUG_ROLL_END\]", "", text, flags=re.DOTALL
    )

    # Remove resource tracking blocks
    text = re.sub(
        r"\[DEBUG_RESOURCES_START\].*?\[DEBUG_RESOURCES_END\]",
        "",
        text,
        flags=re.DOTALL,
    )

    # Remove state change explanation blocks
    text = re.sub(
        r"\[DEBUG_STATE_START\].*?\[DEBUG_STATE_END\]", "", text, flags=re.DOTALL
    )

    # Remove entity validation blocks
    text = re.sub(
        r"\[DEBUG_VALIDATION_START\].*?\[DEBUG_VALIDATION_END\]",
        "",
        text,
        flags=re.DOTALL,
    )

    # Remove state updates proposed blocks
    text = re.sub(
        r"\[STATE_UPDATES_PROPOSED\].*?\[/STATE_UPDATES_PROPOSED\]",
        "",
        text,
        flags=re.DOTALL,
    )

    # Clean up any resulting multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


class TestDebugStrippingIsolated(unittest.TestCase):
    """Test debug content stripping in isolation."""

    def setUp(self):
        """Set up test data."""
        self.sample_response = """
        You enter the ancient library. Dust motes dance in the filtered sunlight.
        
        [DEBUG_START]
        The player is entering a key story location. I should describe the atmosphere 
        and hint at the knowledge contained here.
        [DEBUG_END]
        
        The librarian, an elderly elf, looks up from her tome.
        
        [DEBUG_ROLL_START]
        Rolling for librarian's initial reaction: 1d20+2 = 15+2 = 17 (Friendly)
        [DEBUG_ROLL_END]
        
        "Welcome, traveler. It's been some time since we've had visitors."
        
        [DEBUG_RESOURCES_START]
        Resources: 0 EP used (8/8 remaining), no spell slots used, short rests: 2/2
        [DEBUG_RESOURCES_END]
        
        [DEBUG_STATE_START]
        Adding NPC "Elderly Librarian" to the scene with friendly disposition.
        Location updated to "Ancient Library".
        [DEBUG_STATE_END]
        
        She gestures to the vast collection of books surrounding you.
        
        [STATE_UPDATES_PROPOSED]
        {
            "world_data": {
                "current_location_name": "Ancient Library"
            },
            "npc_data": {
                "elderly_librarian": {
                    "name": "Elderly Librarian",
                    "race": "Elf",
                    "disposition": "friendly",
                    "location": "Ancient Library"
                }
            }
        }
        [/STATE_UPDATES_PROPOSED]
        """

    def test_strip_all_debug_content(self):
        """Test that all debug content is removed."""
        result = strip_debug_content_isolated(self.sample_response)

        # Check that all debug tags are removed
        self.assertNotIn("[DEBUG_START]", result)
        self.assertNotIn("[DEBUG_END]", result)
        self.assertNotIn("[DEBUG_ROLL_START]", result)
        self.assertNotIn("[DEBUG_ROLL_END]", result)
        self.assertNotIn("[DEBUG_RESOURCES_START]", result)
        self.assertNotIn("[DEBUG_RESOURCES_END]", result)
        self.assertNotIn("[DEBUG_STATE_START]", result)
        self.assertNotIn("[DEBUG_STATE_END]", result)
        self.assertNotIn("[STATE_UPDATES_PROPOSED]", result)
        self.assertNotIn("[/STATE_UPDATES_PROPOSED]", result)

        # Check that debug content is removed
        self.assertNotIn("key story location", result)
        self.assertNotIn("1d20+2 = 15+2 = 17", result)
        self.assertNotIn("0 EP used", result)
        self.assertNotIn("Adding NPC", result)
        self.assertNotIn("current_location_name", result)

    def test_preserve_narrative_content(self):
        """Test that narrative content is preserved."""
        result = strip_debug_content_isolated(self.sample_response)

        # Check that story content remains
        self.assertIn("You enter the ancient library", result)
        self.assertIn("Dust motes dance", result)
        self.assertIn("The librarian, an elderly elf", result)
        self.assertIn("Welcome, traveler", result)
        self.assertIn("She gestures to the vast collection", result)

    def test_handle_empty_input(self):
        """Test handling of empty or None input."""
        self.assertEqual(strip_debug_content_isolated(""), "")
        self.assertEqual(strip_debug_content_isolated(None), None)
        self.assertEqual(strip_debug_content_isolated("   "), "")

    def test_multiple_debug_blocks(self):
        """Test handling multiple debug blocks of same type."""
        multi_debug = """
        Text 1
        [DEBUG_START]Debug 1[DEBUG_END]
        Text 2
        [DEBUG_START]Debug 2[DEBUG_END]
        Text 3
        [DEBUG_ROLL_START]Roll 1[DEBUG_ROLL_END]
        Text 4
        [DEBUG_ROLL_START]Roll 2[DEBUG_ROLL_END]
        Text 5
        """

        result = strip_debug_content_isolated(multi_debug)

        # All debug content should be removed
        self.assertNotIn("Debug 1", result)
        self.assertNotIn("Debug 2", result)
        self.assertNotIn("Roll 1", result)
        self.assertNotIn("Roll 2", result)

        # All text should remain
        self.assertIn("Text 1", result)
        self.assertIn("Text 2", result)
        self.assertIn("Text 3", result)
        self.assertIn("Text 4", result)
        self.assertIn("Text 5", result)

    def test_nested_brackets(self):
        """Test handling of nested brackets in debug content."""
        nested = """
        Story start
        [DEBUG_START]
        Debug with [nested brackets] and more
        [DEBUG_END]
        Story end
        """

        result = strip_debug_content_isolated(nested)

        self.assertNotIn("nested brackets", result)
        self.assertIn("Story start", result)
        self.assertIn("Story end", result)

    def test_multiline_debug_content(self):
        """Test handling of multiline debug content."""
        multiline = """
        Beginning
        [DEBUG_STATE_START]
        Line 1 of debug
        Line 2 of debug
        Line 3 of debug
        [DEBUG_STATE_END]
        End
        """

        result = strip_debug_content_isolated(multiline)

        self.assertNotIn("Line 1 of debug", result)
        self.assertNotIn("Line 2 of debug", result)
        self.assertNotIn("Line 3 of debug", result)
        self.assertIn("Beginning", result)
        self.assertIn("End", result)

    def test_clean_up_extra_newlines(self):
        """Test that multiple newlines are cleaned up."""
        extra_newlines = """
        Start
        [DEBUG_START]
        
        
        Debug content
        
        
        [DEBUG_END]
        
        
        
        End
        """

        result = strip_debug_content_isolated(extra_newlines)

        # Should not have more than 2 consecutive newlines
        self.assertNotIn("\n\n\n", result)
        self.assertIn("Start", result)
        self.assertIn("End", result)

    def test_debug_validation_blocks(self):
        """Test removal of entity validation debug blocks."""
        validation = """
        Story content
        [DEBUG_VALIDATION_START]
        Entity Tracking Validation Result:
        - Expected entities: ['NPC1', 'NPC2']
        - Found entities: ['NPC1']
        - Missing entities: ['NPC2']
        [DEBUG_VALIDATION_END]
        More story
        """

        result = strip_debug_content_isolated(validation)

        self.assertNotIn("Entity Tracking Validation", result)
        self.assertNotIn("Expected entities", result)
        self.assertIn("Story content", result)
        self.assertIn("More story", result)

    def test_real_world_example(self):
        """Test with a realistic AI response."""
        real_response = """
        The morning sun breaks through the tavern windows as you finish your breakfast.
        
        [DEBUG_START]
        Time to introduce the quest hook. The player has rested and should be ready for adventure.
        [DEBUG_END]
        
        A cloaked figure bursts through the door, breathing heavily.
        
        [DEBUG_ROLL_START]
        Rolling Perception check to notice details: 1d20+3 = 14+3 = 17 (Success)
        [DEBUG_ROLL_END]
        
        You notice blood on their cloak and fear in their eyes. "Please, you must help me!" 
        they gasp. "The goblins... they've taken my daughter!"
        
        [DEBUG_RESOURCES_START]
        Resources: 0 EP used (8/8 remaining), full HP (25/25), spell slots: 3/3 (level 1)
        [DEBUG_RESOURCES_END]
        
        [STATE_UPDATES_PROPOSED]
        {
            "custom_campaign_state": {
                "active_missions": {
                    "append": [{
                        "mission_id": "rescue_daughter",
                        "title": "A Desperate Plea",
                        "description": "A cloaked stranger needs help rescuing their daughter from goblins",
                        "status": "active"
                    }]
                }
            }
        }
        [/STATE_UPDATES_PROPOSED]
        """

        result = strip_debug_content_isolated(real_response)

        # Story should flow naturally without debug content
        self.assertIn("The morning sun breaks", result)
        self.assertIn("A cloaked figure bursts", result)
        self.assertIn("You notice blood", result)
        self.assertIn("Please, you must help me!", result)
        self.assertIn("they've taken my daughter!", result)

        # No debug content should remain
        self.assertNotIn("quest hook", result)
        self.assertNotIn("1d20+3", result)
        self.assertNotIn("EP used", result)
        self.assertNotIn("mission_id", result)


if __name__ == "__main__":
    unittest.main()
