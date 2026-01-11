"""Tests for legacy JSON cleanup and fallback code in narrative_response_schema.py"""

import json
import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site.narrative_response_schema import parse_structured_response


class TestNarrativeResponseLegacyFallback(unittest.TestCase):
    """Test coverage for legacy JSON cleanup code (lines 500-557)"""

    def test_malformed_json_aggressive_cleanup(self):
        """Test aggressive cleanup for severely malformed JSON"""
        # Malformed JSON that triggers aggressive cleanup
        response_text = """
        {"narrative": "The player enters", "other": broken json here
        with no proper closing
        """

        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative

    def test_json_artifacts_in_text(self):
        """Test cleanup of JSON artifacts in narrative text"""
        response_text = """
        "narrative": "The player walks in",
        "entities_mentioned": ["player"],
        "location_confirmed": "tavern"
        """

        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative

    def test_nested_json_string_escapes(self):
        """Test handling of nested JSON string escapes"""
        # Note: This test case is technically invalid JSON (missing closing brace)
        # so it triggers the error path now that recovery is disabled.
        response_text = """
        {
            "narrative": "The player says, \\"Hello!\\"\\nThen walks away.",
            "partial": true
        """

        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative

    def test_json_with_no_narrative_field(self):
        """Test fallback when JSON has no narrative field"""
        response_text = """
        {
            "message": "This is the actual content",
            "status": "success",
            "data": {
                "player": "enters tavern"
            }
        }
        """

        narrative, response = parse_structured_response(response_text)

        # Should apply minimal cleanup
        assert narrative is not None

    def test_multiple_narrative_patterns(self):
        """Test extraction with multiple narrative patterns in text"""
        response_text = """
        Some text before
        "narrative": "First narrative",
        more text
        "narrative": "Second narrative",
        final text
        """

        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative

    def test_json_comma_separator_cleanup(self):
        """Test JSON comma separator replacement"""
        response_text = """
        "narrative": "Item one", "next": "Item two", "last": "Item three"
        """

        # This should trigger the comma separator cleanup
        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative

    def test_whitespace_normalization(self):
        """Test whitespace pattern normalization"""
        response_text = """
        {
            "narrative": "Too    many     spaces\\n\\n\\nAnd too many newlines",
            "broken": json
        }
        """

        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative

    def test_final_json_artifact_check(self):
        """Test the final JSON artifact check and cleanup"""
        # Text that still has JSON artifacts after initial processing
        response_text = """
        The actual narrative text but still has "narrative": markers
        and "god_mode_response": artifacts that need cleaning
        """

        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative

    def test_deeply_broken_json_with_narrative_hint(self):
        """Test extraction from deeply broken JSON with narrative hint"""
        response_text = """
        {{{{
            data: {
                "narrative": "The actual story content here
                with multiple lines
                and broken JSON structure"
            missing brackets everywhere
        """

        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative

    def test_mixed_valid_and_invalid_json(self):
        """Test handling of mixed valid and invalid JSON"""
        response_text = """
        {
            "narrative": "Valid part of response",
            "entities_mentioned": ["player", "npc"],
            this part is broken
            "but_then": "valid again"
        }
        """

        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative

    def test_escaped_quotes_in_narrative(self):
        """Test handling of escaped quotes in narrative"""
        response_text = r"""
        {
            "narrative": "The NPC says, \"Welcome to my shop!\" and smiles.",
            "entities_mentioned": ["NPC"]
        }
        """

        narrative, response = parse_structured_response(response_text)

        # Should properly handle escaped quotes
        assert '"Welcome to my shop!"' in narrative

    def test_partial_json_at_end_of_response(self):
        """Test handling when JSON is cut off at the end"""
        response_text = """
        {
            "narrative": "The adventure begins as you enter the dungeon...",
            "entities_mentioned": ["player", "dungeon"],
            "location_confirmed": "Dunge
        """

        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative

    def test_json_with_unicode_characters(self):
        """Test handling of Unicode characters in JSON"""
        response_text = json.dumps(
            {
                "narrative": "The sign reads: Café ☕ Open 24/7 🌙",
                "entities_mentioned": ["sign", "café"],
            }
        )

        narrative, response = parse_structured_response(response_text)

        # Should preserve Unicode characters
        assert "☕" in narrative
        assert "🌙" in narrative
        assert "Café" in narrative

    def test_completely_non_json_response(self):
        """Test handling of completely non-JSON response"""
        response_text = "Just plain text with no JSON structure at all."

        narrative, response = parse_structured_response(response_text)

        # Should return error message as recovery is disabled
        assert "Invalid JSON response received" in narrative


if __name__ == "__main__":
    unittest.main()
