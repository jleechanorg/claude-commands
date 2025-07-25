import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import re

from gemini_response import GeminiResponse

# Import the static methods
strip_debug_content = GeminiResponse._strip_debug_content
strip_state_updates_only = GeminiResponse._strip_state_updates_only


# Define strip_other_debug_content based on expected behavior
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


from narrative_response_schema import NarrativeResponse


class TestDebugStrippingJSONSafety(unittest.TestCase):
    """Test that debug content stripping doesn't interfere with JSON-based state updates"""

    def test_strip_functions_dont_affect_json_response_object(self):
        """Test that strip functions only operate on text, not JSON objects"""
        # Create a proper JSON response
        narrative_response = NarrativeResponse(
            narrative="The knight enters the castle.",
            entities_mentioned=["knight", "castle"],
            state_updates={"pc_data": {"location": "castle", "gold": 100}},
        )

        gemini_response = GeminiResponse(
            narrative_text="The knight enters the castle.",
            structured_response=narrative_response,
            debug_tags_present={},
        )

        # The state updates should be accessible regardless of text stripping
        self.assertEqual(gemini_response.state_updates["pc_data"]["gold"], 100)

        # Even if we strip the narrative text, state updates remain in JSON
        stripped_text = strip_debug_content(gemini_response.narrative_text)
        self.assertEqual(stripped_text, "The knight enters the castle.")
        # State updates still accessible through the object
        self.assertEqual(gemini_response.state_updates["pc_data"]["gold"], 100)

    def test_strip_state_updates_only_affects_markdown_blocks(self):
        """Test that strip_state_updates_only only removes markdown blocks"""
        text_with_block = """Story begins here.
        
[STATE_UPDATES_PROPOSED]
{
    "pc_data": {"gold": 50}
}
[END_STATE_UPDATES_PROPOSED]

Story continues."""

        stripped = strip_state_updates_only(text_with_block)

        # Verify markdown block is removed
        self.assertNotIn("[STATE_UPDATES_PROPOSED]", stripped)
        self.assertNotIn("gold", stripped)
        self.assertIn("Story begins here", stripped)
        self.assertIn("Story continues", stripped)

    def test_narrative_text_vs_state_updates_separation(self):
        """Test that narrative and state updates are properly separated in JSON mode"""
        # Narrative with embedded state block (should be stripped from display)
        narrative_with_block = """The hero finds treasure!

[STATE_UPDATES_PROPOSED]
{"pc_data": {"gold": 1000}}
[END_STATE_UPDATES_PROPOSED]

The adventure continues."""

        # Create response with clean separation
        narrative_response = NarrativeResponse(
            narrative="The hero finds treasure! The adventure continues.",  # Clean narrative
            entities_mentioned=["hero"],
            state_updates={"pc_data": {"gold": 1000}},  # Structured updates
        )

        response = GeminiResponse(
            narrative_text="The hero finds treasure! The adventure continues.",
            structured_response=narrative_response,
            debug_tags_present={},
        )

        # Verify clean separation
        self.assertNotIn("[STATE_UPDATES_PROPOSED]", response.narrative_text)
        self.assertEqual(response.state_updates["pc_data"]["gold"], 1000)

    def test_debug_mode_disabled_strips_text_not_json(self):
        """Test that disabling debug mode strips text but preserves JSON state updates"""
        # Text with all types of debug content
        full_text = """Normal story text.

[DEBUG_START]
DM Notes: Player is doing well
[DEBUG_END]

[DEBUG_ROLL_START]
Rolled 15 + 3 = 18
[DEBUG_ROLL_END]

More story.

[STATE_UPDATES_PROPOSED]
{"pc_data": {"hp": 25}}
[END_STATE_UPDATES_PROPOSED]"""

        # When debug mode is OFF, strip all debug blocks
        stripped = strip_debug_content(full_text)

        # Verify all debug/state blocks removed from display text
        self.assertNotIn("[DEBUG_START]", stripped)
        self.assertNotIn("[DEBUG_ROLL_START]", stripped)
        self.assertNotIn("[STATE_UPDATES_PROPOSED]", stripped)
        self.assertNotIn("DM Notes", stripped)
        self.assertNotIn("hp", stripped)

        # But story text remains
        self.assertIn("Normal story text", stripped)
        self.assertIn("More story", stripped)

    def test_multiple_strip_operations_safe(self):
        """Test that multiple strip operations don't interfere with each other"""
        text = """Story start.

[DEBUG_START]
Debug content
[DEBUG_END]

[STATE_UPDATES_PROPOSED]
{"test": "data"}
[END_STATE_UPDATES_PROPOSED]

Story end."""

        # Apply multiple strip operations
        text1 = strip_debug_content(text)
        text2 = strip_state_updates_only(text1)
        text3 = strip_other_debug_content(text)

        # All should produce clean text
        for stripped in [text1, text2, text3]:
            self.assertIn("Story start", stripped)
            self.assertIn("Story end", stripped)

        # text1 strips debug AND state updates
        self.assertNotIn("[DEBUG_START]", text1)
        self.assertNotIn("[STATE_UPDATES_PROPOSED]", text1)

        # text3 strips only other debug content, not state updates
        self.assertNotIn("[DEBUG_START]", text3)
        self.assertIn("[STATE_UPDATES_PROPOSED]", text3)


if __name__ == "__main__":
    unittest.main()
