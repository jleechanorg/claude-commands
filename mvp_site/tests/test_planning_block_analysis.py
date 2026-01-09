"""Tests for planning block analysis field handling and Deep Think mode"""

import json
import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site.narrative_response_schema import parse_structured_response


class TestPlanningBlockAnalysis(unittest.TestCase):
    """Test coverage for Deep Think planning blocks with analysis fields"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock()

    def test_switch_to_story_mode_boolean_handling(self):
        """switch_to_story_mode should coerce string/number values consistently."""
        response_text = json.dumps(
            {
                "narrative": "Testing switch_to_story_mode coercion...",
                "planning_block": {
                    "thinking": "Ensuring boolean coercion works",
                    "choices": {
                        "choice_true_str": {
                            "text": "True String",
                            "description": "Should coerce to True",
                            "risk_level": "low",
                            "switch_to_story_mode": "true",
                        },
                        "choice_false_str": {
                            "text": "False String",
                            "description": "Should coerce to False",
                            "risk_level": "low",
                            "switch_to_story_mode": "false",
                        },
                        "choice_numeric": {
                            "text": "Numeric Zero",
                            "description": "Should be False",
                            "risk_level": "low",
                            "switch_to_story_mode": 0,
                        },
                        "choice_bool": {
                            "text": "Boolean True",
                            "description": "Should remain True",
                            "risk_level": "low",
                            "switch_to_story_mode": True,
                        },
                        "choice_missing": {
                            "text": "No Flag",
                            "description": "Missing flag should be absent",
                            "risk_level": "low",
                        },
                    },
                },
            }
        )

        _, response = parse_structured_response(response_text)

        choices = response.planning_block.get("choices", {})
        assert choices["choice_true_str"]["switch_to_story_mode"] is True
        assert choices["choice_false_str"]["switch_to_story_mode"] is False
        assert choices["choice_numeric"]["switch_to_story_mode"] is False
        assert choices["choice_bool"]["switch_to_story_mode"] is True
        assert "switch_to_story_mode" not in choices["choice_missing"]

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
        assert "consider your options" in narrative

        # Check planning block structure
        assert response.planning_block is not None
        choices = response.planning_block.get("choices", {})

        # Verify analysis fields are preserved
        attack_analysis = choices["attack_goblin"]["analysis"]
        assert len(attack_analysis["pros"]) == 3
        assert len(attack_analysis["cons"]) == 3
        assert attack_analysis["confidence"] == "moderate"

        sneak_analysis = choices["sneak_past"]["analysis"]
        assert len(sneak_analysis["pros"]) == 2
        assert len(sneak_analysis["cons"]) == 2

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
        assert analysis["pros"][0] == "Safe option"  # Script tag completely removed
        assert "<script>" not in analysis["pros"][0]
        assert "alert" not in analysis["pros"][0]  # Script content removed

        assert analysis["pros"][1] == "No danger"  # Img tag removed
        assert "<img" not in analysis["pros"][1]
        assert "onerror" not in analysis["pros"][1]  # Event handler removed

        assert analysis["cons"][0] == "Might be boring"  # Script tag removed
        assert "<script>" not in analysis["cons"][0]

        # Bold tags should remain (not dangerous)
        assert "<b>" in analysis["notes"]
        assert "Bold text" in analysis["notes"]

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
        assert "detailed_breakdown" in analysis
        assert "combat_factors" in analysis["detailed_breakdown"]
        assert len(analysis["detailed_breakdown"]["combat_factors"]["advantages"]) == 2

        # Check non-string values are preserved
        assert analysis["success_rate"] == 75

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

        assert analysis["string_field"] == "Just a string"
        assert analysis["number_field"] == 42
        assert analysis["float_field"] == 3.14
        assert analysis["boolean_field"]
        assert analysis["null_field"] is None
        assert len(analysis["list_field"]) == 5
        assert analysis["dict_field"]["nested"] == "value"

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
        assert "simple_choice" in choices
        assert "analysis" not in choices["simple_choice"]


if __name__ == "__main__":
    unittest.main()
