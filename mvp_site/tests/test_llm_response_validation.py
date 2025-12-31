"""
Tests for Gemini response validation and parsing in llm_service.py.
Focus on JSON parsing, schema validation, and field validation.
"""

import json
import os
import sys
import unittest

# Add the root directory (two levels up) to the Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set testing environment
os.environ["TESTING"] = "true"


from mvp_site.narrative_response_schema import (
    NarrativeResponse,
    parse_structured_response,
)


class TestLLMResponseValidation(unittest.TestCase):
    """Test suite for Gemini API response validation and parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.maxDiff = None

    # Group 1 - JSON Parsing Tests

    def test_valid_json_parsing(self):
        """Test that valid JSON responses are parsed correctly."""
        # Create valid JSON response
        valid_json = {
            "narrative": "The wizard enters the room cautiously.",
            "entities_mentioned": ["wizard", "room"],
            "location_confirmed": "Dungeon Chamber",
            "turn_summary": "Wizard explores the chamber",
            "state_updates": {"position": "chamber_entrance"},
            "debug_info": {"rolls": ["perception: 18"]},
        }

        # Test with raw JSON
        response_text = json.dumps(valid_json, indent=2)
        parsed_text, structured = parse_structured_response(response_text)

        assert isinstance(structured, NarrativeResponse)
        assert structured.narrative == "The wizard enters the room cautiously."
        assert structured.entities_mentioned == ["wizard", "room"]
        assert structured.location_confirmed == "Dungeon Chamber"
        assert parsed_text == "The wizard enters the room cautiously."

        # Test with markdown-wrapped JSON
        markdown_response = f"```json\n{response_text}\n```"
        parsed_text, structured = parse_structured_response(markdown_response)

        assert isinstance(structured, NarrativeResponse)
        assert structured.narrative == "The wizard enters the room cautiously."

    def test_invalid_json_recovery(self):
        """Test that malformed JSON triggers proper error handling."""
        # Test completely malformed JSON
        malformed_json = (
            '{"narrative": "The story begins...", "entities_mentioned": ["hero"'
        )

        parsed_text, structured = parse_structured_response(malformed_json)

        # Should recover partial data or fall back
        assert isinstance(structured, NarrativeResponse)
        # The robust parser should recover what it can
        assert "story" in parsed_text.lower()

        # Test JSON with syntax errors
        syntax_error_json = '{"narrative": "Test", "entities_mentioned": ["a", "b",], "location": "here"}'

        parsed_text, structured = parse_structured_response(syntax_error_json)
        assert isinstance(structured, NarrativeResponse)

    def test_partial_json_handling(self):
        """Test handling of truncated JSON responses."""
        # Simulate truncated response (common with token limits)
        truncated_json = """{
            "narrative": "The adventurer walks through the ancient forest, noticing strange markings on the trees. As they examine the symbols more closely, they realize these are warnings about",
            "entities_mentioned": ["adventurer", "forest", "trees", "symbols"],
            "location_confirmed": "Ancient Forest",
            "turn_summary": "Adventurer discovers mysterious"""

        parsed_text, structured = parse_structured_response(truncated_json)

        # Should recover partial narrative
        assert isinstance(structured, NarrativeResponse)
        assert "adventurer walks through" in parsed_text
        assert "ancient forest" in parsed_text
        # Entities should be recovered if possible
        if structured.entities_mentioned:
            assert "adventurer" in structured.entities_mentioned

    def test_dice_audit_events_parsing(self):
        """dice_audit_events should parse as list[dict] and ignore invalid items."""
        response = {
            "narrative": "You lunge forward.",
            "entities_mentioned": ["hero"],
            "planning_block": {
                "thinking": "Attack!",
                "choices": {"attack": {"text": "Attack", "description": "Strike"}},
            },
            "dice_rolls": ["Attack: 1d20+5 = 12+5 = 17 vs AC 15 (Hit!)"],
            "dice_audit_events": [
                {
                    "source": "code_execution",
                    "label": "Attack",
                    "notation": "1d20+5",
                    "rolls": [12],
                    "modifier": 5,
                    "total": 17,
                },
                "not-a-dict",
            ],
        }

        parsed_text, structured = parse_structured_response(json.dumps(response))
        assert parsed_text == "You lunge forward."
        assert isinstance(structured, NarrativeResponse)
        assert structured.dice_rolls == ["Attack: 1d20+5 = 12+5 = 17 vs AC 15 (Hit!)"]
        assert structured.dice_audit_events == [
            {
                "source": "code_execution",
                "label": "Attack",
                "notation": "1d20+5",
                "rolls": [12],
                "modifier": 5,
                "total": 17,
            }
        ]

    # Group 2 - Required Fields Tests

    def test_missing_content_field(self):
        """Test response parsing when 'narrative' content field is missing."""
        # Response without narrative field
        missing_narrative = {
            "entities_mentioned": ["wizard", "goblin"],
            "location_confirmed": "Cave",
            "turn_summary": "Battle continues",
        }

        response_text = json.dumps(missing_narrative)

        # Parse response - should handle missing narrative gracefully
        parsed_text, structured = parse_structured_response(response_text)

        # Should still create a valid response
        assert isinstance(structured, NarrativeResponse)
        # When narrative is missing, it seems to return empty string for parsed_text
        # but the structured response should have the data
        assert parsed_text is not None  # Can be empty string
        assert structured.narrative is not None
        # Other fields should be parsed correctly
        assert structured.entities_mentioned == ["wizard", "goblin"]
        assert structured.location_confirmed == "Cave"

    def test_missing_role_field(self):
        """Test response parsing when role-related fields are missing."""
        # Note: Based on the schema, there's no 'role' field, but we have entities_mentioned
        # Test missing entities_mentioned which is similar to role tracking
        missing_entities = {
            "narrative": "The battle rages on.",
            "location_confirmed": "Battlefield",
            "turn_summary": "Combat round",
        }

        response_text = json.dumps(missing_entities)
        parsed_text, structured = parse_structured_response(response_text)

        # Should handle missing entities_mentioned gracefully
        assert isinstance(structured, NarrativeResponse)
        assert structured.entities_mentioned == []  # Should default to empty list
        assert structured.narrative == "The battle rages on."

    def test_missing_parts_field(self):
        """Test response parsing when complex structure fields are missing."""
        # Test missing state_updates (which has parts/structure)
        missing_parts = {
            "narrative": "The hero ponders their next move.",
            "entities_mentioned": ["hero"],
        }

        response_text = json.dumps(missing_parts)
        parsed_text, structured = parse_structured_response(response_text)

        # Should handle missing fields gracefully
        assert isinstance(structured, NarrativeResponse)
        assert structured.state_updates == {}  # Should default to empty dict
        assert structured.location_confirmed == "Unknown"  # Should have default
        assert structured.turn_summary is None  # Optional field can be None

    # Group 3 - Type Validation Tests

    def test_invalid_content_type(self):
        """Test response parsing when content is wrong type (number not string)."""
        # Narrative as number instead of string
        invalid_type = {
            "narrative": 12345,  # Should be string
            "entities_mentioned": ["player"],
            "location_confirmed": "Town",
        }

        response_text = json.dumps(invalid_type)

        # Should handle type conversion or error appropriately
        try:
            parsed_text, structured = parse_structured_response(response_text)
            # If it succeeds, check that it converted to string
            assert isinstance(structured, NarrativeResponse)
            assert isinstance(structured.narrative, str)
            assert structured.narrative == "12345"
        except (ValueError, TypeError) as e:
            # If it fails, that's also acceptable
            assert "must be" in str(e).lower()

    def test_invalid_parts_structure(self):
        """Test response parsing when parts/list fields have wrong structure."""
        # entities_mentioned as string instead of list
        invalid_structure = {
            "narrative": "The adventure begins.",
            "entities_mentioned": "wizard,goblin",  # Should be list
            "location_confirmed": "Forest",
        }

        response_text = json.dumps(invalid_structure)

        # Should handle graceful recovery (default to empty list)
        parsed_text, structured = parse_structured_response(response_text)

        assert isinstance(structured, NarrativeResponse)
        assert structured.entities_mentioned == []

    def test_null_values_handling(self):
        """Test response parsing with null values in required fields."""
        # Test various null scenarios
        null_narrative = {
            "narrative": None,  # Null narrative
            "entities_mentioned": ["hero"],
            "location_confirmed": "Castle",
        }

        response_text = json.dumps(null_narrative)
        parsed_text, structured = parse_structured_response(response_text)

        # Should handle null narrative by using fallback
        assert isinstance(structured, NarrativeResponse)
        assert structured.narrative is not None
        # Should use fallback for null narrative - could be response_text or default message
        assert parsed_text is not None
        # For null narrative, we now return empty string which is acceptable
        # The important thing is that it doesn't crash and returns a valid structure
        assert isinstance(parsed_text, str)
        assert isinstance(structured.narrative, str)

        # Test null in list fields
        null_entities = {
            "narrative": "The quest continues.",
            "entities_mentioned": None,  # Will be converted to empty list
            "location_confirmed": "Town",
        }

        response_text2 = json.dumps(null_entities)

        # Parse and check - null entities_mentioned should become empty list
        parsed_text2, structured2 = parse_structured_response(response_text2)
        assert isinstance(structured2, NarrativeResponse)
        assert structured2.entities_mentioned == []  # Null becomes empty list
        assert structured2.narrative == "The quest continues."

    # Group 4 - Size Limits Tests

    def test_oversized_response(self):
        """Test handling of very large responses (simulating 10MB)."""
        # Create a large narrative (not actually 10MB for test efficiency)
        large_text = "Once upon a time... " * 10000  # ~200KB

        oversized_response = {
            "narrative": large_text,
            "entities_mentioned": ["hero"] * 1000,  # Large entity list
            "location_confirmed": "Kingdom",
            "state_updates": {
                f"key_{i}": f"value_{i}" for i in range(1000)
            },  # Large dict
        }

        response_text = json.dumps(oversized_response)

        # Should handle large responses without crashing
        parsed_text, structured = parse_structured_response(response_text)

        assert isinstance(structured, NarrativeResponse)
        # Narrative is stripped, so it will be slightly shorter
        assert len(structured.narrative) == len(large_text.strip())
        assert structured.narrative.startswith("Once upon a time...")
        # Large entity list should be preserved
        assert len(structured.entities_mentioned) == 1000
        # State updates should be preserved
        assert len(structured.state_updates) == 1000

    def test_empty_content_handling(self):
        """Test handling of empty content fields."""
        # Test empty narrative
        empty_content = {
            "narrative": "",  # Empty string
            "entities_mentioned": [],
            "location_confirmed": "Void",
        }

        response_text = json.dumps(empty_content)
        parsed_text, structured = parse_structured_response(response_text)

        # Should handle empty narrative
        assert isinstance(structured, NarrativeResponse)
        assert structured.narrative == ""
        assert structured.entities_mentioned == []
        assert parsed_text == ""  # Empty narrative returns empty parsed_text

        # Test completely empty response
        empty_response = ""
        parsed_text2, structured2 = parse_structured_response(empty_response)

        # Should return default response
        assert isinstance(structured2, NarrativeResponse)
        assert structured2.narrative == "The story awaits your input..."
        assert parsed_text2 == "The story awaits your input..."

    def test_whitespace_only_content(self):
        """Test handling of whitespace-only content."""
        # Various whitespace scenarios
        whitespace_tests = [
            {
                "narrative": "   ",
                "entities_mentioned": ["ghost"],
                "location_confirmed": "Limbo",
            },
            {
                "narrative": "\n\n\n",
                "entities_mentioned": [],
                "location_confirmed": "Space",
            },
            {
                "narrative": "\t\t",
                "entities_mentioned": ["void"],
                "location_confirmed": "Tab Land",
            },
            {
                "narrative": " \n \t ",
                "entities_mentioned": [],
                "location_confirmed": "Mixed Space",
            },
        ]

        for test_case in whitespace_tests:
            response_text = json.dumps(test_case)
            parsed_text, structured = parse_structured_response(response_text)

            # Should preserve whitespace in narrative
            assert isinstance(structured, NarrativeResponse)
            # Narrative should be stripped in validation but original preserved
            assert len(structured.narrative.strip()) == 0
            assert structured.location_confirmed == test_case["location_confirmed"]

        # Test response with Unicode and emojis
        unicode_response = {
            "narrative": "The wizard casts a spell: ✨🔮✨ «Абракадабра!» 中文测试",
            "entities_mentioned": ["wizard", "spell"],
            "location_confirmed": "Magic Tower 🏰",
        }

        response_text = json.dumps(unicode_response, ensure_ascii=False)
        parsed_text, structured = parse_structured_response(response_text)

        # Should handle Unicode and emojis correctly
        assert isinstance(structured, NarrativeResponse)
        assert "✨" in structured.narrative
        assert "🔮" in structured.narrative
        assert "Абракадабра" in structured.narrative
        assert "中文测试" not in structured.narrative  # CJK should be stripped
        assert "🏰" in structured.location_confirmed


if __name__ == "__main__":
    unittest.main()
