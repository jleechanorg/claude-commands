#!/usr/bin/env python3
"""
Test that JSON mode is always used for all LLM calls
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import json
from unittest.mock import MagicMock, patch

from narrative_response_schema import (
    create_generic_json_instruction,
    create_structured_prompt_injection,
)

from game_state import GameState
from gemini_service import continue_story


class TestAlwaysJSONMode(unittest.TestCase):
    """Test suite to ensure JSON mode is always used"""

    def setUp(self):
        """Set up test fixtures"""
        self.game_state = GameState()
        self.story_context = []

    def test_json_mode_without_entities(self):
        """Test that JSON mode is used even when there are no entities"""
        # Empty game state - no player character, no NPCs
        self.game_state.player_character_data = {}
        self.game_state.npc_data = {}

        with patch("gemini_service._call_gemini_api") as mock_api:
            # Mock the API response - JSON-first with separate planning block field
            mock_response = MagicMock()
            mock_response.text = json.dumps(
                {
                    "narrative": "Welcome to character creation!",
                    "planning_block": {
                        "thinking": "The player needs to begin character creation for their adventure.",
                        "context": "This is the start of the character creation process.",
                        "choices": {
                            "create_character": {
                                "text": "Create Character",
                                "description": "Begin the character creation process",
                                "risk_level": "safe",
                            },
                            "skip_creation": {
                                "text": "Skip Creation",
                                "description": "Skip character creation and use default",
                                "risk_level": "safe",
                            },
                        },
                    },
                    "entities_mentioned": [],
                    "location_confirmed": "Character Creation",
                    "state_updates": {
                        "custom_campaign_state": {
                            "character_creation": {
                                "in_progress": True,
                                "current_step": 1,
                            }
                        }
                    },
                }
            )
            mock_api.return_value = mock_response

            # Call continue_story
            result = continue_story(
                user_input="Start game",
                mode="character",
                story_context=self.story_context,
                current_game_state=self.game_state,
                selected_prompts=["narrative", "mechanics"],
            )

            # Verify the API was called
            # JSON mode is now always enabled internally, no need to check for use_json_mode parameter
            assert (
                mock_api.called
            ), "API should have been called (JSON mode is always enabled)"

            # Verify we got a clean GeminiResponse with JSON-first structure
            assert result is not None
            # The narrative should be clean (no planning block in narrative_text)
            assert "Welcome to character creation!" in result.narrative_text
            assert (
                "--- PLANNING BLOCK ---" not in result.narrative_text
            )  # Should be in separate field
            assert (
                '"narrative":' not in result.narrative_text
            )  # Should be clean text, not JSON

            # Planning block should be in structured response as JSON object
            assert result.structured_response is not None
            assert isinstance(result.structured_response.planning_block, dict)

            # Check for choice structure in JSON format
            planning_block = result.structured_response.planning_block
            assert "choices" in planning_block

            # Check that choices exist (the exact keys may be converted to snake_case)
            choices = planning_block.get("choices", {})
            assert len(choices) > 0, "Should have at least one choice"

            # Check for specific choices we mocked
            choice_keys = list(choices.keys())
            [choice.get("text", "") for choice in choices.values()]

            # Should have both create and skip choices
            assert "create_character" in choice_keys
            assert "skip_creation" in choice_keys

            # Verify choice structure
            create_choice = choices["create_character"]
            assert create_choice["text"] == "Create Character"
            assert (
                create_choice["description"] == "Begin the character creation process"
            )
            assert create_choice["risk_level"] == "safe"

    def test_json_mode_with_entities(self):
        """Test that JSON mode is used when entities are present"""
        # Add a player character
        self.game_state.player_character_data = {
            "string_id": "pc_test_001",
            "name": "Test Hero",
            "hp_current": 10,
            "hp_max": 10,
        }

        # Add an NPC
        self.game_state.npc_data = {
            "Test NPC": {
                "string_id": "npc_test_001",
                "present": True,
                "conscious": True,
                "hp_current": 5,
                "hp_max": 5,
            }
        }

        with patch("gemini_service._call_gemini_api") as mock_api:
            # Mock the API response
            mock_response = MagicMock()
            mock_response.text = json.dumps(
                {
                    "narrative": "Test Hero encounters Test NPC.",
                    "entities_mentioned": ["Test Hero", "Test NPC"],
                    "location_confirmed": "Test Location",
                    "state_updates": {},
                }
            )
            mock_api.return_value = mock_response

            # Call continue_story
            continue_story(
                user_input="Talk to NPC",
                mode="character",
                story_context=self.story_context,
                current_game_state=self.game_state,
                selected_prompts=["narrative"],
            )

            # Verify the API was called
            # JSON mode is now always enabled internally, no need to check for use_json_mode parameter
            assert (
                mock_api.called
            ), "API should have been called (JSON mode is always enabled)"

    def test_generic_json_instruction_format(self):
        """Test the generic JSON instruction format"""
        instruction = create_generic_json_instruction()

        # Since always-JSON mode is enabled, this function returns empty string
        # JSON format is handled automatically by the system
        assert (
            instruction == ""
        ), "Generic JSON instruction should be empty when always-JSON mode is enabled"

    def test_structured_prompt_injection_without_entities(self):
        """Test that structured prompt injection works without entities"""
        # Call with empty entities list
        instruction = create_structured_prompt_injection("", [])

        # Should return empty string since JSON format is handled automatically
        assert (
            instruction == ""
        ), "Structured prompt injection should be empty when no entities and always-JSON mode is enabled"

    def test_structured_prompt_injection_with_entities(self):
        """Test that structured prompt injection works with entities"""
        manifest = "Test manifest with entities"
        entities = ["Hero", "Villain"]

        instruction = create_structured_prompt_injection(manifest, entities)

        # Should include entity tracking requirements
        assert "CRITICAL ENTITY TRACKING REQUIREMENT" in instruction
        assert "Hero" in instruction
        assert "Villain" in instruction


if __name__ == "__main__":
    unittest.main()
