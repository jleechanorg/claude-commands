"""
Red-Green TDD Test: Gemini Model Selection - GREEN PHASE

Tests verify that both continue_story() and get_initial_story() respect user model preferences.

FIXED: continue_story() now accepts user_id parameter and uses _select_model_for_user() helper
VERIFIED: User's gemini_model setting is properly read and applied via GEMINI_MODEL_MAPPING
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from mvp_site import constants, gemini_service
from mvp_site.game_state import GameState


class TestGeminiModelSelection(unittest.TestCase):
    """Test that user model preferences are respected in all code paths."""

    def setUp(self):
        """Set up test environment."""
        # Ensure we're in test mode
        os.environ["TESTING"] = "true"
        os.environ["MOCK_SERVICES_MODE"] = "false"  # Test real model selection logic

    def tearDown(self):
        """Clean up after test."""
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

    @patch("mvp_site.gemini_service.get_user_settings")
    @patch("mvp_site.gemini_service._call_gemini_api_with_gemini_request")
    def test_continue_story_respects_user_model_preference(
        self, mock_api_call, mock_get_settings
    ):
        """
        GREEN TEST: Verify continue_story() uses user's preferred model.

        Tests that continue_story() correctly calls _select_model_for_user() and uses
        the user's gemini_model preference from settings.
        """
        # Arrange: User has selected Gemini 3 Pro Preview
        test_user_id = "test_user_123"
        mock_get_settings.return_value = {
            "gemini_model": "gemini-3-pro-preview",
            "debug_mode": False,
        }

        # Mock API response
        mock_response = MagicMock()
        mock_response.text = (
            '{"narrative": "Test story continuation", "entities_identified": []}'
        )
        mock_api_call.return_value = mock_response

        # Create minimal game state
        game_state = GameState()
        game_state.user_id = test_user_id
        game_state.custom_campaign_state = {
            "session_number": 1,
            "scene_number": 1,
            "character_name": "Test Hero",
        }

        story_context = [
            {"actor": "gemini", "text": "Welcome to the adventure!"},
            {"actor": "user", "text": "I look around."},
        ]

        # Act: Call continue_story with user_id to trigger model preference selection
        gemini_service.continue_story(
            user_input="I walk forward.",
            mode=constants.MODE_CHARACTER,
            story_context=story_context,
            current_game_state=game_state,
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            use_default_world=False,
            user_id=test_user_id,
        )

        # Assert: Should have called API with gemini-3-pro-preview, not flash
        assert mock_api_call.called, "API should have been called"

        # Check what model was actually used
        call_kwargs = mock_api_call.call_args.kwargs
        actual_model = call_kwargs.get("model_name")

        assert actual_model == "gemini-3-pro-preview", (
            f"BUG DETECTED: Expected gemini-3-pro-preview but got {actual_model}. "
            f"continue_story() is ignoring user preferences!"
        )

    @patch("mvp_site.gemini_service.get_user_settings")
    @patch("mvp_site.gemini_service._call_gemini_api_with_gemini_request")
    def test_get_initial_story_respects_user_model_preference(
        self, mock_api_call, mock_get_settings
    ):
        """
        BASELINE TEST: get_initial_story() correctly uses user's model preference.

        This test should PASS because get_initial_story() already has proper logic.
        """
        # Arrange: User has selected Gemini 3 Pro Preview
        test_user_id = "test_user_456"
        mock_get_settings.return_value = {
            "gemini_model": "gemini-3-pro-preview",
            "debug_mode": False,
        }

        # Mock API response
        mock_response = MagicMock()
        mock_response.text = (
            '{"narrative": "Your adventure begins!", "entities_identified": []}'
        )
        mock_api_call.return_value = mock_response

        # Act: Call get_initial_story
        gemini_service.get_initial_story(
            prompt="I want to be a brave knight",
            user_id=test_user_id,
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            generate_companions=False,
            use_default_world=False,
        )

        # Assert: Should have called API with gemini-3-pro-preview
        assert mock_api_call.called, "API should have been called"

        call_kwargs = mock_api_call.call_args.kwargs
        actual_model = call_kwargs.get("model_name")

        assert (
            actual_model == "gemini-3-pro-preview"
        ), f"get_initial_story() should respect user preference (got {actual_model})"


if __name__ == "__main__":
    unittest.main()
