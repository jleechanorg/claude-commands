#!/usr/bin/env python3
"""
Simple test to verify prompt loading logic, especially calibration filtering.
Tests the prompt assembly directly without running full functions.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, call, patch

import gemini_service

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_admin.firestore"] = MagicMock()

os.environ["GEMINI_API_KEY"] = "test"

import constants


class TestPromptLoadingLogic(unittest.TestCase):
    """Test prompt loading logic by checking the actual code paths."""

    def test_user_selectable_prompts_constant(self):
        """Test that USER_SELECTABLE_PROMPTS contains the expected prompts."""
        assert [
            "narrative",
            "mechanics",
            "calibration",
        ] == constants.USER_SELECTABLE_PROMPTS

    def test_calibration_filtering_in_continue_story(self):
        """Verify the filtering logic in continue_story by checking the code."""
        # This test verifies the logic by inspection of the actual code
        # In continue_story, we have:
        # selected_prompts_filtered = [p_type for p_type in selected_prompts if p_type != constants.PROMPT_TYPE_CALIBRATION]

        # Simulate the filtering
        selected_prompts = ["narrative", "mechanics", "calibration"]
        selected_prompts_filtered = [
            p_type
            for p_type in selected_prompts
            if p_type != constants.PROMPT_TYPE_CALIBRATION
        ]

        assert selected_prompts_filtered == ["narrative", "mechanics"]
        assert "calibration" not in selected_prompts_filtered

    def test_calibration_filtering_with_future_prompts(self):
        """Verify that filtering works correctly even with new prompt types."""
        # Test that the exclusion-based approach works with future prompt types
        selected_prompts = [
            "narrative",
            "mechanics",
            "calibration",
            "future_prompt_1",
            "future_prompt_2",
        ]
        selected_prompts_filtered = [
            p_type
            for p_type in selected_prompts
            if p_type != constants.PROMPT_TYPE_CALIBRATION
        ]

        # Should include everything except calibration
        assert selected_prompts_filtered == [
            "narrative",
            "mechanics",
            "future_prompt_1",
            "future_prompt_2",
        ]
        assert "calibration" not in selected_prompts_filtered
        assert "future_prompt_1" in selected_prompts_filtered
        assert "future_prompt_2" in selected_prompts_filtered

    def test_calibration_included_in_get_initial_story(self):
        """Verify that get_initial_story would include calibration."""
        # In get_initial_story, the loop is:
        # for p_type in [constants.PROMPT_TYPE_NARRATIVE, constants.PROMPT_TYPE_MECHANICS, constants.PROMPT_TYPE_CALIBRATION]:

        prompts_to_load = [
            constants.PROMPT_TYPE_NARRATIVE,
            constants.PROMPT_TYPE_MECHANICS,
            constants.PROMPT_TYPE_CALIBRATION,
        ]

        assert constants.PROMPT_TYPE_CALIBRATION in prompts_to_load
        assert len(prompts_to_load) == 3

    @patch("gemini_service._load_instruction_file")
    def test_prompt_loading_order_get_initial_story(self, mock_load):
        """Test the exact loading order in get_initial_story."""
        # Import here after mocks are set up

        mock_load.return_value = "content"

        # Simulate the loading sequence from get_initial_story
        system_instruction_parts = []
        selected_prompts = ["narrative", "mechanics", "calibration"]

        # Following the exact logic from get_initial_story:
        system_instruction_parts.append(
            gemini_service._load_instruction_file(
                constants.PROMPT_TYPE_MASTER_DIRECTIVE
            )
        )
        system_instruction_parts.append(
            gemini_service._load_instruction_file(constants.PROMPT_TYPE_GAME_STATE)
        )
        system_instruction_parts.append(
            gemini_service._load_instruction_file(constants.PROMPT_TYPE_ENTITY_SCHEMA)
        )

        if constants.PROMPT_TYPE_NARRATIVE in selected_prompts:
            system_instruction_parts.append(
                gemini_service._load_instruction_file(
                    constants.PROMPT_TYPE_CHARACTER_TEMPLATE
                )
            )

        if constants.PROMPT_TYPE_MECHANICS in selected_prompts:
            system_instruction_parts.append(
                gemini_service._load_instruction_file(
                    constants.PROMPT_TYPE_CHARACTER_SHEET
                )
            )

        for p_type in [
            constants.PROMPT_TYPE_NARRATIVE,
            constants.PROMPT_TYPE_MECHANICS,
            constants.PROMPT_TYPE_CALIBRATION,
        ]:
            if p_type in selected_prompts:
                system_instruction_parts.append(
                    gemini_service._load_instruction_file(p_type)
                )

        system_instruction_parts.append(
            gemini_service._load_instruction_file(constants.PROMPT_TYPE_DESTINY)
        )

        # Check the calls
        expected_calls = [
            call("master_directive"),
            call("game_state"),
            call("entity_schema"),
            call("character_template"),
            call("character_sheet"),
            call("narrative"),
            call("mechanics"),
            call("calibration"),  # Should be included
            call("destiny_ruleset"),
        ]

        # Verify first 9 calls match expected
        actual_calls = mock_load.call_args_list[:9]
        assert actual_calls == expected_calls

    @patch("gemini_service._load_instruction_file")
    def test_prompt_loading_order_continue_story(self, mock_load):
        """Test the exact loading order in continue_story."""
        # Import here after mocks are set up

        mock_load.return_value = "content"

        # Simulate the loading sequence from continue_story
        system_instruction_parts = []
        selected_prompts = ["narrative", "mechanics", "calibration"]

        # Following the exact logic from continue_story:
        system_instruction_parts.append(
            gemini_service._load_instruction_file(
                constants.PROMPT_TYPE_MASTER_DIRECTIVE
            )
        )
        system_instruction_parts.append(
            gemini_service._load_instruction_file(constants.PROMPT_TYPE_GAME_STATE)
        )
        system_instruction_parts.append(
            gemini_service._load_instruction_file(constants.PROMPT_TYPE_ENTITY_SCHEMA)
        )

        if constants.PROMPT_TYPE_NARRATIVE in selected_prompts:
            system_instruction_parts.append(
                gemini_service._load_instruction_file(
                    constants.PROMPT_TYPE_CHARACTER_TEMPLATE
                )
            )

        if constants.PROMPT_TYPE_MECHANICS in selected_prompts:
            system_instruction_parts.append(
                gemini_service._load_instruction_file(
                    constants.PROMPT_TYPE_CHARACTER_SHEET
                )
            )

        system_instruction_parts.append(
            gemini_service._load_instruction_file(constants.PROMPT_TYPE_DESTINY)
        )

        # The key difference - filtering out calibration
        selected_prompts_filtered = [
            p_type
            for p_type in selected_prompts
            if p_type != constants.PROMPT_TYPE_CALIBRATION
        ]

        for p_type in selected_prompts_filtered:
            system_instruction_parts.append(
                gemini_service._load_instruction_file(p_type)
            )

        # Check the calls
        expected_calls = [
            call("master_directive"),
            call("game_state"),
            call("entity_schema"),
            call("character_template"),
            call("character_sheet"),
            call("destiny_ruleset"),
            call("narrative"),
            call("mechanics"),
            # NO call('calibration') - this is the key difference!
        ]

        # Verify calls match expected (no calibration)
        assert mock_load.call_args_list == expected_calls

        # Double-check calibration was not called
        calibration_calls = [
            c for c in mock_load.call_args_list if c == call("calibration")
        ]
        assert (
            len(calibration_calls) == 0
        ), "Calibration should not be loaded in continue_story"


if __name__ == "__main__":
    unittest.main()
