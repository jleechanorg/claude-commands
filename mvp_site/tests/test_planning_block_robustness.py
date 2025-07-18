#!/usr/bin/env python3
"""
Test planning block robustness and edge case handling.
Tests validation of null, empty, and malformed planning blocks.
Now tests JSON-only planning block format.
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from narrative_response_schema import NarrativeResponse


class TestPlanningBlockRobustness(unittest.TestCase):
    """Test edge cases and robustness for JSON planning blocks"""

    def test_null_planning_block(self):
        """Test handling of null planning block"""
        response = NarrativeResponse(narrative="Test narrative", planning_block=None)
        self.assertEqual(response.planning_block, {})
        self.assertIsInstance(response.planning_block, dict)

    def test_empty_string_planning_block(self):
        """Test handling of empty string planning block"""
        with self.assertLogs(level="ERROR") as cm:
            response = NarrativeResponse(narrative="Test narrative", planning_block="")
        # Empty strings are rejected and converted to empty dict
        self.assertEqual(response.planning_block, {})
        # Should log error about string format no longer supported
        self.assertTrue(
            any(
                "STRING PLANNING BLOCKS NO LONGER SUPPORTED" in log for log in cm.output
            )
        )

    def test_whitespace_only_planning_block(self):
        """Test handling of whitespace-only planning block"""
        with self.assertLogs(level="ERROR") as cm:
            response = NarrativeResponse(
                narrative="Test narrative", planning_block="   \n\t   "
            )
        # Whitespace-only strings are rejected and converted to empty dict
        self.assertEqual(response.planning_block, {})
        self.assertTrue(
            any(
                "STRING PLANNING BLOCKS NO LONGER SUPPORTED" in log for log in cm.output
            )
        )

    def test_non_string_planning_block(self):
        """Test handling of non-string/dict planning block values"""
        # Test with integer - rejected and converted to empty dict
        with self.assertLogs(level="ERROR") as cm:
            response = NarrativeResponse(narrative="Test narrative", planning_block=123)
        self.assertEqual(response.planning_block, {})
        self.assertTrue(any("INVALID PLANNING BLOCK TYPE" in log for log in cm.output))

        # Test with list - rejected and converted to empty dict
        with self.assertLogs(level="ERROR") as cm:
            response = NarrativeResponse(
                narrative="Test narrative", planning_block=["option1", "option2"]
            )
        self.assertEqual(response.planning_block, {})
        self.assertTrue(any("INVALID PLANNING BLOCK TYPE" in log for log in cm.output))

        # Test with valid dict - should be accepted
        valid_block = {
            "thinking": "Test thinking",
            "choices": {"choice1": {"text": "Choice 1", "description": "First choice"}},
        }
        response = NarrativeResponse(
            narrative="Test narrative", planning_block=valid_block
        )
        self.assertIsInstance(response.planning_block, dict)
        self.assertEqual(response.planning_block["thinking"], "Test thinking")

    def test_json_like_planning_block(self):
        """Test detection of JSON-like string planning blocks"""
        json_block = '{"choices": ["option1", "option2"]}'
        with self.assertLogs(level="ERROR") as cm:
            response = NarrativeResponse(
                narrative="Test narrative", planning_block=json_block
            )

        # String format is rejected
        self.assertTrue(
            any(
                "STRING PLANNING BLOCKS NO LONGER SUPPORTED" in log for log in cm.output
            )
        )
        # Should convert to empty dict
        self.assertEqual(response.planning_block, {})

    def test_extremely_long_planning_block(self):
        """Test handling of very long planning blocks"""
        # Create a valid JSON planning block with many choices
        long_block = {"thinking": "Many choices available", "choices": {}}
        for i in range(100):
            long_block["choices"][f"choice_{i}"] = {
                "text": f"Choice {i}",
                "description": f"Description for choice {i}" * 10,  # Make it long
            }

        response = NarrativeResponse(
            narrative="Test narrative", planning_block=long_block
        )

        # Should preserve all choices
        self.assertEqual(len(response.planning_block["choices"]), 100)
        self.assertIn("choice_99", response.planning_block["choices"])

    def test_null_bytes_in_planning_block(self):
        """Test handling of null bytes in planning block"""
        # For JSON format, null bytes would be in the content
        block_with_nulls = {
            "thinking": "Choice 1\x00Choice 2\x00",
            "choices": {
                "test": {
                    "text": "Test\x00Choice",
                    "description": "Description\x00with null",
                }
            },
        }

        response = NarrativeResponse(
            narrative="Test narrative", planning_block=block_with_nulls
        )

        # HTML escaping should handle null bytes
        # They get sanitized during validation
        self.assertIsInstance(response.planning_block, dict)

    def test_other_structured_fields_validation(self):
        """Test validation of other structured fields"""
        # Test null session_header
        response = NarrativeResponse(narrative="Test", session_header=None)
        self.assertEqual(response.session_header, "")

        # Test non-list dice_rolls
        response = NarrativeResponse(narrative="Test", dice_rolls="not a list")
        self.assertEqual(response.dice_rolls, [])

        # Test list with mixed types
        response = NarrativeResponse(
            narrative="Test", dice_rolls=[1, "roll", None, {"die": 6}]
        )
        self.assertEqual(len(response.dice_rolls), 3)  # None is filtered out
        self.assertIn("1", response.dice_rolls)
        self.assertIn("roll", response.dice_rolls)

    def test_to_dict_with_edge_cases(self):
        """Test to_dict method with edge case values"""
        response = NarrativeResponse(
            narrative="Test narrative",
            planning_block=None,
            session_header=None,
            dice_rolls=None,
            resources=None,
            entities_mentioned=None,
            state_updates="not a dict",  # Invalid type
            debug_info=123,  # Invalid type
        )

        result = response.to_dict()

        # All fields should be present with safe defaults
        self.assertEqual(result["narrative"], "Test narrative")
        self.assertEqual(result["planning_block"], {})  # Empty dict for JSON format
        self.assertEqual(result["session_header"], "")
        self.assertEqual(result["dice_rolls"], [])
        self.assertEqual(result["resources"], "")
        self.assertEqual(result["entities_mentioned"], [])
        self.assertEqual(result["location_confirmed"], "Unknown")
        self.assertEqual(result["state_updates"], {})
        self.assertEqual(result["debug_info"], {})

    def test_special_characters_in_planning_block(self):
        """Test handling of special characters"""
        special_block = {
            "thinking": "Player needs to handle <script>alert('xss')</script>",
            "choices": {
                "action_script": {
                    "text": "Action<script>alert('xss')</script>",
                    "description": "Test XSS",
                },
                "action_amp": {
                    "text": "Action&amp;",
                    "description": 'Test HTML entities & < > "',
                },
            },
        }

        response = NarrativeResponse(
            narrative="Test narrative", planning_block=special_block
        )

        # Special characters should be HTML-escaped for security
        # Check that the structure is preserved
        self.assertIn("action_script", response.planning_block["choices"])
        self.assertIn("action_amp", response.planning_block["choices"])
        # The actual escaping happens during validation
        self.assertIsInstance(response.planning_block, dict)

    def test_valid_planning_block_structure(self):
        """Test valid JSON planning block structure"""
        valid_block = {
            "thinking": "The player is at a crossroads",
            "context": "Additional context about the situation",
            "choices": {
                "go_left": {
                    "text": "Go Left",
                    "description": "Take the left path through the forest",
                    "risk_level": "low",
                },
                "go_right": {
                    "text": "Go Right",
                    "description": "Take the right path up the mountain",
                    "risk_level": "high",
                },
                "go_back": {
                    "text": "Go Back",
                    "description": "Return the way you came",
                    "risk_level": "safe",
                },
            },
        }

        response = NarrativeResponse(
            narrative="Test narrative", planning_block=valid_block
        )

        # Should preserve the full structure
        self.assertEqual(
            response.planning_block["thinking"], "The player is at a crossroads"
        )
        self.assertEqual(len(response.planning_block["choices"]), 3)
        self.assertIn("go_left", response.planning_block["choices"])
        self.assertEqual(
            response.planning_block["choices"]["go_left"]["risk_level"], "low"
        )


if __name__ == "__main__":
    unittest.main()
