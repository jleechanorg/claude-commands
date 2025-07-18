"""
Tests for safer JSON cleanup approach
Ensures narrative text containing JSON-like patterns isn't corrupted
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from narrative_response_schema import parse_structured_response


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
        self.assertIn("Cast {spell}", narrative)
        self.assertIn('["power": 10]', narrative)
        self.assertEqual(parsed.entities_mentioned, ["wizard"])

    def test_malformed_json_cleanup_only_when_needed(self):
        """Test that cleanup only applies to clearly malformed JSON"""
        # Plain text that happens to have some JSON-like characters
        response = "The party enters the {treasure room} and finds [gold coins]."

        narrative, parsed = parse_structured_response(response)

        # Should preserve the original text since it's not JSON
        self.assertEqual(narrative, response)
        self.assertEqual(parsed.entities_mentioned, [])

    def test_partial_json_with_narrative_extraction(self):
        """Test extraction of narrative from partial JSON"""
        # Malformed JSON that's clearly JSON but incomplete
        response = (
            '{"narrative": "The dragon breathes fire!", "entities_mentioned": ["dragon"'
        )

        narrative, parsed = parse_structured_response(response)

        # Should extract the narrative cleanly
        self.assertEqual(narrative, "The dragon breathes fire!")
        # Entities might be empty due to incomplete JSON
        self.assertIsInstance(parsed.entities_mentioned, list)

    def test_json_without_quotes_cleanup(self):
        """Test cleanup of JSON-like text without proper quotes"""
        # Malformed JSON that starts and ends like JSON
        response = (
            '{narrative: "The adventure begins", location_confirmed: "Town Square"}'
        )

        narrative, parsed = parse_structured_response(response)

        # Should extract or clean up to readable text
        self.assertIn("The adventure begins", narrative)
        self.assertNotIn("{", narrative)  # JSON syntax should be removed

    def test_nested_json_in_narrative(self):
        """Test that valid JSON with nested structures in narrative works"""
        response = """{
            "narrative": "The merchant shows you his wares: {'sword': 100, 'shield': 50}",
            "entities_mentioned": ["merchant"],
            "location_confirmed": "Market"
        }"""

        narrative, parsed = parse_structured_response(response)

        # Should preserve the nested structure in the narrative
        self.assertIn("'sword': 100", narrative)
        self.assertIn("'shield': 50", narrative)
        self.assertEqual(parsed.location_confirmed, "Market")

    def test_aggressive_cleanup_last_resort(self):
        """Test that aggressive cleanup only happens as last resort"""
        # Clearly malformed JSON that needs cleanup
        response = '{"narrative": "Hello world", "other": "data", "broken": '

        narrative, parsed = parse_structured_response(response)

        # Should extract narrative even from broken JSON
        self.assertEqual(narrative, "Hello world")

    def test_minimal_cleanup_for_json_without_narrative(self):
        """Test minimal cleanup when JSON-like but no narrative field"""
        response = '{"action": "attack", "target": "goblin", "damage": 10}'

        narrative, parsed = parse_structured_response(response)

        # When there's no narrative field in valid JSON, it should handle gracefully
        # The robust parser will parse it but return empty narrative
        self.assertEqual(narrative, "")  # No narrative field means empty narrative
        self.assertEqual(parsed.narrative, "")


if __name__ == "__main__":
    unittest.main()
