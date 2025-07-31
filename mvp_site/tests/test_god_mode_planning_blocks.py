"""Test that God mode responses include planning blocks when offering choices."""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from narrative_response_schema import parse_structured_response


class TestGodModePlanningBlocks(unittest.TestCase):
    """Test God mode planning block requirements."""

    def test_god_mode_with_planning_block(self):
        """Test that God mode responses can include planning blocks."""
        god_response_with_choices = """{
            "narrative": "",
            "god_mode_response": "As the omniscient game master, I present several plot directions for your campaign.",
            "planning_block": {
                "thinking": "As the omniscient game master, I'm presenting meta-narrative options for the campaign direction.",
                "context": "The player has requested god mode assistance with plot development.",
                "choices": {
                    "god:plot_arc_1": {
                        "text": "Implement Plot Arc 1",
                        "description": "The Silent Scars of Silverwood - investigate Alexiel's legacy",
                        "risk_level": "medium"
                    },
                    "god:plot_arc_2": {
                        "text": "Implement Plot Arc 2",
                        "description": "The Empyrean Whisper - corruption within the Imperial ranks",
                        "risk_level": "high"
                    },
                    "god:return_story": {
                        "text": "Return to Story",
                        "description": "Continue with the current narrative without implementing new plot elements",
                        "risk_level": "safe"
                    },
                    "god:custom_direction": {
                        "text": "Custom Direction",
                        "description": "Describe a different plot direction or modification you'd like to explore",
                        "risk_level": "low"
                    }
                }
            },
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(god_response_with_choices)

        # Should return the god_mode_response content
        assert (
            narrative
            == "As the omniscient game master, I present several plot directions for your campaign."
        )
        assert (
            response_obj.god_mode_response
            == "As the omniscient game master, I present several plot directions for your campaign."
        )

        # Should have planning block
        assert response_obj.planning_block is not None
        assert "thinking" in response_obj.planning_block
        assert "choices" in response_obj.planning_block

        # Verify all God mode choices have "god:" prefix
        choices = response_obj.planning_block.get("choices", {})
        for choice_key in choices:
            assert choice_key.startswith(
                "god:"
            ), f"Choice key '{choice_key}' must start with 'god:' prefix"

        # Verify mandatory "god:return_story" choice exists
        assert (
            "god:return_story" in choices
        ), "Must include 'god:return_story' as default choice"

    def test_god_mode_choices_all_have_prefix(self):
        """Test that all God mode choices use the god: prefix."""
        god_response = """{
            "narrative": "",
            "god_mode_response": "Multiple paths lie before you.",
            "planning_block": {
                "thinking": "Presenting campaign options",
                "choices": {
                    "god:option_1": {
                        "text": "Option 1",
                        "description": "First option"
                    },
                    "god:option_2": {
                        "text": "Option 2",
                        "description": "Second option"
                    },
                    "god:return_story": {
                        "text": "Return to Story",
                        "description": "Continue normal play"
                    }
                }
            },
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(god_response)

        # All choices should have god: prefix
        choices = response_obj.planning_block.get("choices", {})
        assert all(key.startswith("god:") for key in choices)

    def test_god_mode_without_planning_block(self):
        """Test that God mode responses without choices don't require planning blocks."""
        god_response_no_choices = """{
            "narrative": "",
            "god_mode_response": "The ancient artifact has been placed in the dungeon as requested.",
            "entities_mentioned": ["ancient artifact"],
            "location_confirmed": "Dungeon",
            "state_updates": {
                "items": {
                    "ancient_artifact": {
                        "location": "dungeon_level_3"
                    }
                }
            },
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(god_response_no_choices)

        # Should work fine without planning block when no choices offered
        assert (
            narrative
            == "The ancient artifact has been placed in the dungeon as requested."
        )
        # Planning block should be empty dict when not provided
        assert response_obj.planning_block == {}

    def test_missing_return_story_choice(self):
        """Test detection of missing god:return_story choice."""
        god_response_missing_default = """{
            "narrative": "",
            "god_mode_response": "Choose your path.",
            "planning_block": {
                "thinking": "Presenting options",
                "choices": {
                    "god:option_1": {
                        "text": "Option 1",
                        "description": "First option"
                    },
                    "god:option_2": {
                        "text": "Option 2",
                        "description": "Second option"
                    }
                }
            },
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(
            god_response_missing_default
        )

        # Should still parse successfully
        assert response_obj.planning_block is not None
        choices = response_obj.planning_block.get("choices", {})

        # But we can detect the missing default choice
        assert "god:return_story" not in choices

    def test_planning_block_structure(self):
        """Test that God mode planning blocks follow the correct structure."""
        god_response = """{
            "narrative": "",
            "god_mode_response": "Several narrative paths are available.",
            "planning_block": {
                "thinking": "As the omniscient game master, I'm presenting meta-narrative options for the campaign direction.",
                "context": "The player has requested god mode assistance with plot development.",
                "choices": {
                    "god:plot_arc_1": {
                        "text": "Implement Plot Arc 1",
                        "description": "The Silent Scars of Silverwood - investigate Alexiel's legacy",
                        "risk_level": "medium"
                    },
                    "god:return_story": {
                        "text": "Return to Story",
                        "description": "Continue with the current narrative",
                        "risk_level": "safe"
                    }
                }
            },
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(god_response)

        # Verify planning block structure
        planning_block = response_obj.planning_block
        assert planning_block is not None
        assert "thinking" in planning_block
        assert "context" in planning_block
        assert "choices" in planning_block

        # Verify choice structure
        choices = planning_block["choices"]
        for _choice_key, choice_data in choices.items():
            assert "text" in choice_data
            assert "description" in choice_data
            # risk_level is optional but if present should be valid
            if "risk_level" in choice_data:
                assert choice_data["risk_level"] in ["safe", "low", "medium", "high"]


if __name__ == "__main__":
    unittest.main()
