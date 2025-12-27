"""
Tests for safer JSON cleanup approach
Ensures narrative text containing JSON-like patterns isn't corrupted
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from mvp_site.debug_hybrid_system import (
    clean_json_artifacts,
    contains_json_artifacts,
    process_story_entry_for_display,
)
from mvp_site.narrative_response_schema import parse_structured_response


class TestJSONCleanupSafety(unittest.TestCase):
    """Test cases for safer JSON cleanup implementation"""

    def test_narrative_with_json_like_content_preserved(self):
        """Test that narrative containing JSON-like syntax is preserved"""
        # Valid JSON response with narrative containing brackets and quotes
        response = """{
            "narrative": "The wizard says: 'Cast {spell} with [\\"power\\": 10]!' He winks.",
            "entities_mentioned": ["wizard"],
            "location_confirmed": "Tower"
        }"""

        narrative, parsed = parse_structured_response(response)

        # The narrative should preserve the brackets and quotes
        assert "Cast {spell}" in narrative
        assert '["power": 10]' in narrative
        assert parsed.entities_mentioned == ["wizard"]

    def test_malformed_json_cleanup_only_when_needed(self):
        """Test that cleanup only applies to clearly malformed JSON"""
        # Plain text that happens to have some JSON-like characters
        response = "The party enters the {treasure room} and finds [gold coins]."

        narrative, parsed = parse_structured_response(response)

        # Should preserve the original text since it's not JSON
        assert narrative == response
        assert parsed.entities_mentioned == []

    def test_partial_json_with_narrative_extraction(self):
        """Test extraction of narrative from partial JSON"""
        # Malformed JSON that's clearly JSON but incomplete
        response = (
            '{"narrative": "The dragon breathes fire!", "entities_mentioned": ["dragon"'
        )

        narrative, parsed = parse_structured_response(response)

        # Should extract the narrative cleanly
        assert narrative == "The dragon breathes fire!"
        # Entities might be empty due to incomplete JSON
        assert isinstance(parsed.entities_mentioned, list)

    def test_json_without_quotes_cleanup(self):
        """Test cleanup of JSON-like text without proper quotes"""
        # Malformed JSON that starts and ends like JSON
        response = (
            '{narrative: "The adventure begins", location_confirmed: "Town Square"}'
        )

        narrative, parsed = parse_structured_response(response)

        # Should extract or clean up to readable text
        assert "The adventure begins" in narrative
        assert "{" not in narrative  # JSON syntax should be removed

    def test_nested_json_in_narrative(self):
        """Test that valid JSON with nested structures in narrative works"""
        response = """{
            "narrative": "The merchant shows you his wares: {'sword': 100, 'shield': 50}",
            "entities_mentioned": ["merchant"],
            "location_confirmed": "Market"
        }"""

        narrative, parsed = parse_structured_response(response)

        # Should preserve the nested structure in the narrative
        assert "'sword': 100" in narrative
        assert "'shield': 50" in narrative
        assert parsed.location_confirmed == "Market"

    def test_aggressive_cleanup_last_resort(self):
        """Test that aggressive cleanup only happens as last resort"""
        # Clearly malformed JSON that needs cleanup
        response = '{"narrative": "Hello world", "other": "data", "broken": '

        narrative, parsed = parse_structured_response(response)

        # Should extract narrative even from broken JSON
        assert narrative == "Hello world"

    def test_minimal_cleanup_for_json_without_narrative(self):
        """Test minimal cleanup when JSON-like but no narrative field"""
        response = '{"action": "attack", "target": "goblin", "damage": 10}'

        narrative, parsed = parse_structured_response(response)

        # When there's no narrative field in valid JSON, it should handle gracefully
        # The robust parser will parse it but return empty narrative
        assert narrative == ""  # No narrative field means empty narrative
        assert parsed.narrative == ""

    def test_json_artifact_detection(self):
        """Test that JSON artifacts are properly detected."""
        # Test cases that should be detected as JSON artifacts
        json_cases = [
            '{"narrative": "Campaign summary\\n\\nYou are Ser Arion...", "entities_mentioned": ["Arion"]}',
            '"narrative": "Some story text"',
            '{"god_mode_response": "GM thoughts here"}',
            '{entities_mentioned: ["character"]}',
            'Description with \\n newlines and \\"escaped quotes\\" in content',  # JSON-escaped content
        ]

        for case in json_cases:
            assert contains_json_artifacts(case), (
                f"Should detect JSON artifacts in: {case[:50]}..."
            )

        # Test cases that should NOT be detected as JSON artifacts
        normal_cases = [
            "You enter the {treasure room} and find [gold coins].",
            "The wizard says: 'Cast the spell!'",
            "A simple story with no JSON.",
            "Some text with {brackets} but not JSON.",
        ]

        for case in normal_cases:
            assert not contains_json_artifacts(case), (
                f"Should NOT detect JSON artifacts in: {case}"
            )

    def test_dragon_knight_description_cleaning(self):
        """Test cleaning of the Dragon Knight campaign description with JSON escapes."""
        # This is similar to what the user was seeing - JSON-escaped text
        malformed_description = (
            "Description: # Campaign summary\\n\\nYou are Ser Arion, a 16 year old "
            "honorable knight on your first mission, sworn to protect the vast Celestial "
            "Imperium. For decades, the Empire has been ruled by the iron-willed Empress "
            "Sariel, a ruthless tyrant who uses psychic power to crush dissent. While her "
            "methods are terrifying, her reign has brought undeniable benefits: the roads "
            "are safe, trade flourishes, and the common people no longer starve or fear "
            'bandits. You are a product of this \\"Silent Peace,\\" and your oath binds '
            "you to the security and prosperity it provides.\\n\\nYour loyalty is now "
            "brutally tested."
        )

        cleaned = clean_json_artifacts(malformed_description)

        # Verify the cleaning worked
        assert "\\n" not in cleaned, "Should not contain literal \\n characters"
        assert "\n" in cleaned, "Should contain actual newlines"
        assert "Description: # Campaign summary" in cleaned, (
            "Content should be preserved"
        )
        assert "Silent Peace" in cleaned, "Should contain the phrase 'Silent Peace'"

    def test_json_structure_cleaning(self):
        """Test cleaning of JSON structure from campaign description."""
        # JSON that contains a description field
        json_description = (
            '{"description": "# Campaign summary\\n\\nYou are Ser Arion, a brave knight...", '
            '"entities_mentioned": ["Arion"]}'
        )

        cleaned = clean_json_artifacts(json_description)

        # Should extract just the description content
        expected = "# Campaign summary\n\nYou are Ser Arion, a brave knight..."
        assert cleaned == expected, f"Expected clean description text, got: {cleaned}"

    def test_god_mode_response_extraction(self):
        """Test extraction of god_mode_response from JSON."""
        json_with_god_mode = (
            '{"god_mode_response": "This is GM content with special instructions.", '
            '"narrative": "Regular story"}'
        )
        cleaned = clean_json_artifacts(json_with_god_mode)

        assert cleaned == "This is GM content with special instructions.", (
            f"Expected god_mode_response extraction, got: {cleaned}"
        )

    def test_normal_description_preservation(self):
        """Test that normal descriptions are preserved."""
        normal_description = (
            "This is a normal campaign description with no JSON artifacts. "
            "It has some {brackets} and [arrays] but is clearly not JSON."
        )

        cleaned = clean_json_artifacts(normal_description)

        assert cleaned == normal_description, (
            f"Normal description was modified: {cleaned}"
        )

    def test_story_entry_json_cleaning(self):
        """Test that story entries are properly processed to remove JSON artifacts."""
        # Test AI response with JSON artifacts
        story_entry_with_json = {
            "actor": "gemini",
            "text": '{"narrative": "You stand at the crossroads, unsure which path to take.", "entities_mentioned": ["Hero"]}',
            "timestamp": "2024-01-01T00:00:00Z",
        }

        processed = process_story_entry_for_display(
            story_entry_with_json, debug_mode=False
        )

        expected_text = "You stand at the crossroads, unsure which path to take."
        assert processed["text"] == expected_text, (
            f"Expected clean text, got: {processed['text']}"
        )

        # Test user entry (should not be processed)
        user_entry = {
            "actor": "user",
            "text": "I go north",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        processed_user = process_story_entry_for_display(user_entry, debug_mode=False)

        assert processed_user == user_entry, "User entries should not be modified"

        # Test clean AI entry (should not be modified)
        clean_entry = {
            "actor": "gemini",
            "text": "A clean narrative response with no artifacts.",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        processed_clean = process_story_entry_for_display(clean_entry, debug_mode=False)

        assert processed_clean == clean_entry, "Clean entries should not be modified"

    def test_escaped_json_content_cleaning(self):
        """Test cleaning of escaped JSON content without structure."""
        # Text that has JSON escapes but isn't JSON structure
        escaped_content = (
            'Some text with \\n newlines and \\"quotes\\" that needs unescaping.'
        )

        cleaned = clean_json_artifacts(escaped_content)

        assert "\\n" not in cleaned, "Should not contain literal \\n"
        assert "\n" in cleaned, "Should contain actual newlines"
        assert '\\"' not in cleaned, "Should not contain escaped quotes"
        assert '"' in cleaned, "Should contain actual quotes"


if __name__ == "__main__":
    unittest.main()
