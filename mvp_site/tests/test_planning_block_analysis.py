"""Tests for planning block analysis field handling and Deep Think mode"""

import json
import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))

from narrative_response_schema import parse_structured_response


class TestPlanningBlockAnalysis(unittest.TestCase):
    """Test coverage for Deep Think planning blocks with analysis fields"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock()

    def test_planning_block_with_analysis_pros_cons(self):
        """Test planning block with pros/cons analysis structure"""
        response_text = json.dumps(
            {
                "narrative": "You consider your options carefully...",
                "planning_block": {
                    "thinking": "This is a dangerous situation",
                    "choices": {
                        "attack_goblin": {
                            "text": "Attack the Goblin",
                            "description": "Charge forward with your sword",
                            "risk_level": "high",
                            "analysis": {
                                "pros": [
                                    "Quick resolution",
                                    "Shows courage",
                                    "Might intimidate others",
                                ],
                                "cons": [
                                    "Could get injured",
                                    "Might alert more enemies",
                                    "Uses resources",
                                ],
                                "confidence": "moderate",
                            },
                        },
                        "sneak_past": {
                            "text": "Sneak Past",
                            "description": "Try to avoid detection",
                            "risk_level": "medium",
                            "analysis": {
                                "pros": ["Conserves resources", "Avoids combat"],
                                "cons": ["Might get caught", "Takes more time"],
                                "confidence": "high",
                            },
                        },
                    },
                },
            }
        )

        narrative, response = parse_structured_response(response_text)

        # Check narrative
        self.assertIn("consider your options", narrative)

        # Check planning block structure
        self.assertIsNotNone(response.planning_block)
        choices = response.planning_block.get("choices", {})

        # Verify analysis fields are preserved
        attack_analysis = choices["attack_goblin"]["analysis"]
        self.assertEqual(len(attack_analysis["pros"]), 3)
        self.assertEqual(len(attack_analysis["cons"]), 3)
        self.assertEqual(attack_analysis["confidence"], "moderate")

        sneak_analysis = choices["sneak_past"]["analysis"]
        self.assertEqual(len(sneak_analysis["pros"]), 2)
        self.assertEqual(len(sneak_analysis["cons"]), 2)

    def test_analysis_field_with_xss_attempts(self):
        """Test that analysis fields are properly sanitized against XSS"""
        response_text = json.dumps(
            {
                "narrative": "Considering options...",
                "planning_block": {
                    "thinking": "Analyzing the situation",
                    "choices": {
                        "test_choice": {
                            "text": "Test Choice",
                            "description": "Testing XSS protection",
                            "risk_level": "low",
                            "analysis": {
                                "pros": [
                                    "<script>alert('xss')</script>Safe option",
                                    "No danger<img src=x onerror=alert('xss')>",
                                ],
                                "cons": [
                                    "Might be boring<script>console.log('evil')</script>"
                                ],
                                "notes": "<b>Bold text</b> should be escaped",
                            },
                        }
                    },
                },
            }
        )

        narrative, response = parse_structured_response(response_text)

        # Get the sanitized analysis
        choices = response.planning_block.get("choices", {})
        analysis = choices["test_choice"]["analysis"]

        # Verify XSS attempts are removed (not escaped)
        self.assertEqual(
            analysis["pros"][0], "Safe option"
        )  # Script tag completely removed
        self.assertNotIn("<script>", analysis["pros"][0])
        self.assertNotIn("alert", analysis["pros"][0])  # Script content removed

        self.assertEqual(analysis["pros"][1], "No danger")  # Img tag removed
        self.assertNotIn("<img", analysis["pros"][1])
        self.assertNotIn("onerror", analysis["pros"][1])  # Event handler removed

        self.assertEqual(analysis["cons"][0], "Might be boring")  # Script tag removed
        self.assertNotIn("<script>", analysis["cons"][0])

        # Bold tags should remain (not dangerous)
        self.assertIn("<b>", analysis["notes"])
        self.assertIn("Bold text", analysis["notes"])

    def test_analysis_with_nested_structures(self):
        """Test analysis field with deeply nested data structures"""
        response_text = json.dumps(
            {
                "narrative": "Complex analysis...",
                "planning_block": {
                    "thinking": "Deep analysis",
                    "choices": {
                        "complex_choice": {
                            "text": "Complex Choice",
                            "description": "Testing nested structures",
                            "risk_level": "medium",
                            "analysis": {
                                "pros": ["Simple pro"],
                                "cons": ["Simple con"],
                                "detailed_breakdown": {
                                    "combat_factors": {
                                        "advantages": ["High ground", "Better weapons"],
                                        "disadvantages": ["Outnumbered"],
                                    },
                                    "resource_impact": {
                                        "health_cost": "10-20 HP",
                                        "spell_slots": "1-2 slots",
                                    },
                                },
                                "success_rate": 75,
                            },
                        }
                    },
                },
            }
        )

        narrative, response = parse_structured_response(response_text)

        # Verify nested structures are preserved
        choices = response.planning_block.get("choices", {})
        analysis = choices["complex_choice"]["analysis"]

        # Check nested dictionaries
        self.assertIn("detailed_breakdown", analysis)
        self.assertIn("combat_factors", analysis["detailed_breakdown"])
        self.assertEqual(
            len(analysis["detailed_breakdown"]["combat_factors"]["advantages"]), 2
        )

        # Check non-string values are preserved
        self.assertEqual(analysis["success_rate"], 75)

    def test_analysis_field_type_variations(self):
        """Test analysis field with various data types"""
        response_text = json.dumps(
            {
                "narrative": "Type testing...",
                "planning_block": {
                    "thinking": "Testing types",
                    "choices": {
                        "type_test": {
                            "text": "Type Test",
                            "description": "Testing data types",
                            "risk_level": "low",
                            "analysis": {
                                "string_field": "Just a string",
                                "number_field": 42,
                                "float_field": 3.14,
                                "boolean_field": True,
                                "null_field": None,
                                "list_field": [1, "two", 3.0, True, None],
                                "dict_field": {"nested": "value"},
                            },
                        }
                    },
                },
            }
        )

        narrative, response = parse_structured_response(response_text)

        # Verify all types are handled correctly
        choices = response.planning_block.get("choices", {})
        analysis = choices["type_test"]["analysis"]

        self.assertEqual(analysis["string_field"], "Just a string")
        self.assertEqual(analysis["number_field"], 42)
        self.assertEqual(analysis["float_field"], 3.14)
        self.assertEqual(analysis["boolean_field"], True)
        self.assertIsNone(analysis["null_field"])
        self.assertEqual(len(analysis["list_field"]), 5)
        self.assertEqual(analysis["dict_field"]["nested"], "value")

    def test_missing_analysis_field(self):
        """Test planning blocks without analysis field work correctly"""
        response_text = json.dumps(
            {
                "narrative": "Simple choice...",
                "planning_block": {
                    "thinking": "Basic options",
                    "choices": {
                        "simple_choice": {
                            "text": "Simple Choice",
                            "description": "No analysis needed",
                            "risk_level": "low",
                        }
                    },
                },
            }
        )

        narrative, response = parse_structured_response(response_text)

        # Verify choice works without analysis field
        choices = response.planning_block.get("choices", {})
        self.assertIn("simple_choice", choices)
        self.assertNotIn("analysis", choices["simple_choice"])


if __name__ == "__main__":
    unittest.main()
