"""
Integration tests for planning block validation and logging.
Tests the complete flow of _validate_and_enforce_planning_block with all logging paths.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path to import modules
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

try:
    from mvp_site.game_state import GameState
    from mvp_site.llm_service import (
        NarrativeResponse,
        _validate_and_enforce_planning_block,
    )

    MODULES_AVAILABLE = True
except ImportError:
    GameState = None
    NarrativeResponse = None
    _validate_and_enforce_planning_block = None
    MODULES_AVAILABLE = False


class TestPlanningBlockValidationIntegration(unittest.TestCase):
    """Integration tests for planning block validation with comprehensive logging coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = GameState()
        self.game_state.player_character_data = {"name": "Test Hero"}
        self.game_state.current_location = {"name": "Test Location"}

        # Create mock structured response
        self.structured_response = MagicMock(spec=NarrativeResponse)
        self.structured_response.planning_block = None

    @patch("mvp_site.llm_service.logging_util", autospec=True)
    def test_missing_planning_block_logs_warning_and_returns_response(
        self, mock_logging
    ):
        """When no planning block is present, return response unchanged and log warning."""
        response_text = "Normal story response without planning block"

        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        mock_logging.warning.assert_any_call(
            "⚠️ PLANNING_BLOCK_MISSING: Story mode response missing required planning block. "
            "The LLM should have generated this - no fallback will be used."
        )
        assert result == response_text

    @patch("mvp_site.llm_service.logging_util", autospec=True)
    def test_empty_planning_block_logs_warning_and_returns_response(self, mock_logging):
        """Existing but empty planning block logs and returns original response."""
        self.structured_response.planning_block = {"thinking": "", "choices": {}}
        response_text = "Story response with empty planning block"

        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        mock_logging.warning.assert_any_call(
            "⚠️ PLANNING_BLOCK_EMPTY: Planning block exists but has no content"
        )
        assert result == response_text

    @patch("mvp_site.llm_service.logging_util", autospec=True)
    def test_string_planning_block_logs_error_and_returns_response(self, mock_logging):
        """String planning blocks are rejected with error log and unchanged response."""
        self.structured_response.planning_block = "invalid"
        response_text = "Story response with string planning block"

        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        mock_logging.error.assert_any_call(
            "❌ STRING PLANNING BLOCKS NO LONGER SUPPORTED: Found str planning block, only JSON format is allowed"
        )
        assert result == response_text

    @patch("mvp_site.llm_service.logging_util", autospec=True)
    def test_valid_planning_block_passes_without_additional_logging(self, mock_logging):
        """Valid planning block returns early without warnings or errors."""
        self.structured_response.planning_block = {
            "thinking": "Plan",
            "choices": {"Continue": "Do thing"},
        }
        response_text = "Story response with planning block"

        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        mock_logging.info.assert_any_call(
            "✅ Planning block found in JSON structured response"
        )
        mock_logging.warning.assert_not_called()
        mock_logging.error.assert_not_called()
        assert result == response_text

    def test_crash_safety_with_malformed_inputs(self):
        """Test that the function doesn't crash with malformed inputs."""
        # Test with None inputs
        try:
            result = _validate_and_enforce_planning_block(
                None,
                "test input",
                self.game_state,
                "test-model",
                "test instruction",
                self.structured_response,
            )
            # Should handle gracefully and return None or empty string
            assert result in [None, "", "None"]
        except Exception as e:
            self.fail(f"Function crashed with None response_text: {e}")

        # Test with malformed game state
        try:
            malformed_game_state = MagicMock()
            malformed_game_state.player_character_data = None
            malformed_game_state.current_location = None

            result = _validate_and_enforce_planning_block(
                "test response",
                "test input",
                malformed_game_state,
                "test-model",
                "test instruction",
                self.structured_response,
            )
            # Should handle gracefully
            assert result is not None
        except Exception as e:
            self.fail(f"Function crashed with malformed game state: {e}")


if __name__ == "__main__":
    unittest.main()
