import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from mvp_site import gemini_service
from mvp_site.gemini_response import GeminiResponse
from mvp_site.narrative_response_schema import (
    NarrativeResponse,
    parse_structured_response,
)


class TestJSONModePreference(unittest.TestCase):
    """Test that JSON mode is always preferred over regex parsing when available"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_state_updates = {
            "pc_data": {"gold": 500, "attributes": {"strength": 16}}
        }

    def test_json_mode_preferred_over_markdown_blocks(self):
        """Test that when both JSON and markdown blocks exist, JSON is used"""
        # Create a response with state updates in both JSON and markdown
        narrative_with_block = """The adventurer finds treasure!

[STATE_UPDATES_PROPOSED]
{
    "pc_data": {
        "gold": 100
    }
}
[END_STATE_UPDATES_PROPOSED]"""

        # JSON response has different values
        narrative_response = NarrativeResponse(
            narrative=narrative_with_block,
            entities_mentioned=["adventurer"],
            state_updates={
                "pc_data": {
                    "gold": 500  # Different from markdown block
                }
            },
        )

        gemini_response = GeminiResponse(
            narrative_text=narrative_with_block,
            structured_response=narrative_response,
            debug_tags_present={},
        )

        # Verify JSON is preferred
        assert gemini_response.state_updates["pc_data"]["gold"] == 500
        assert gemini_response.state_updates["pc_data"]["gold"] != 100

    def test_no_fallback_parsing_exists(self):
        """Test that parse_llm_response_for_state_changes no longer exists"""
        # Function should not exist
        assert not hasattr(gemini_service, "parse_llm_response_for_state_changes")

        # Create response with JSON state updates
        narrative_response = NarrativeResponse(
            narrative="Test narrative",
            entities_mentioned=[],
            state_updates=self.sample_state_updates,
        )

        gemini_response = GeminiResponse(
            narrative_text="Test narrative",
            structured_response=narrative_response,
            debug_tags_present={},
        )

        # Simulate the main.py logic (now simplified)
        proposed_changes = gemini_response.state_updates

        # Verify we get state updates from JSON
        assert proposed_changes == self.sample_state_updates

    def test_no_state_updates_when_no_json(self):
        """Test that no state updates are available when no JSON response"""
        # Create response without structured response
        gemini_response = GeminiResponse(
            narrative_text='Story with [STATE_UPDATES_PROPOSED]{"pc_data": {"gold": 200}}[END_STATE_UPDATES_PROPOSED]',
            structured_response=None,  # No JSON response
            debug_tags_present={},
        )

        # JSON mode is the ONLY mode - no fallback
        proposed_changes = gemini_response.state_updates

        # Should be empty since there's no structured response
        assert proposed_changes == {}

    def test_strip_debug_content_preserves_json_state_updates(self):
        """Test that strip_debug_content doesn't interfere with JSON state updates"""
        # Import strip_debug_content

        strip_debug_content = GeminiResponse._strip_debug_content

        # Text with debug content
        text_with_debug = """Story text here.

[DEBUG_START]
Debug info
[DEBUG_END]

More story."""

        # Strip debug content
        stripped = strip_debug_content(text_with_debug)

        # Verify story is preserved but debug is removed
        assert "Story text here" in stripped
        assert "More story" in stripped
        assert "[DEBUG_START]" not in stripped
        assert "Debug info" not in stripped

    def test_json_extraction_from_code_blocks(self):
        """Test JSON extraction from markdown code blocks"""

        # Test with json language identifier
        json_block = """Here's the response:
```json
{
    "narrative": "The story continues",
    "entities_mentioned": ["hero"],
    "state_updates": {"pc_data": {"level": 2}}
}
```"""

        narrative, response = parse_structured_response(json_block)
        assert narrative == "The story continues"
        assert response.state_updates["pc_data"]["level"] == 2

        # Test with generic code block
        generic_block = """```
{
    "narrative": "Another story",
    "entities_mentioned": ["wizard"],
    "state_updates": {"pc_data": {"mana": 50}}
}
```"""

        narrative2, response2 = parse_structured_response(generic_block)
        assert narrative2 == "Another story"
        assert response2.state_updates["pc_data"]["mana"] == 50

    def test_no_double_parsing(self):
        """Test that state updates aren't parsed twice"""
        # Create a response where the narrative contains a state update block
        # but we already have JSON state updates
        narrative_with_embedded = """The hero gains experience.

[STATE_UPDATES_PROPOSED]
{"pc_data": {"exp": 100}}
[END_STATE_UPDATES_PROPOSED]"""

        narrative_response = NarrativeResponse(
            narrative=narrative_with_embedded,
            entities_mentioned=["hero"],
            state_updates={"pc_data": {"exp": 200}},  # Different value
        )

        response = GeminiResponse(
            narrative_text=narrative_with_embedded,
            structured_response=narrative_response,
            debug_tags_present={},
        )

        # The JSON value should win
        assert response.state_updates["pc_data"]["exp"] == 200


if __name__ == "__main__":
    unittest.main()
