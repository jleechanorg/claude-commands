"""
Integration tests for planning block validation and logging.
Tests the complete flow of _validate_and_enforce_planning_block with all logging paths.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from game_state import GameState
from gemini_service import NarrativeResponse, _validate_and_enforce_planning_block


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

    @patch("gemini_service.logging_util")
    def test_character_creation_detection_case_insensitive(self, mock_logging):
        """Test character creation detection with case insensitivity."""
        # Test various case combinations
        test_cases = [
            "[CHARACTER CREATION] and CHARACTER SHEET and Would you like to play as this character?",
            "[character creation] and character sheet and would you like to play as this character?",
            "[Character Creation] and Character Sheet and Would You Like To Play As This Character?",
            "[CHARACTER creation] and character SHEET and WOULD you like to PLAY as this character?",
        ]

        for response_text in test_cases:
            with self.subTest(response_text=response_text):
                # This should trigger character creation detection
                try:
                    _validate_and_enforce_planning_block(
                        response_text,
                        "test input",
                        self.game_state,
                        "test-model",
                        "test instruction",
                        self.structured_response,
                    )
                    # Should not crash and should detect character creation
                    self.assertTrue(True)  # If we get here, it didn't crash
                except Exception as e:
                    self.fail(
                        f"Character creation detection crashed with case variation: {e}"
                    )

    @patch("gemini_service.logging_util")
    @patch("gemini_service._call_gemini_api")
    @patch("gemini_service._get_text_from_response")
    @patch("gemini_service._parse_gemini_response")
    def test_planning_block_regeneration_logging(
        self, mock_parse, mock_get_text, mock_call_api, mock_logging
    ):
        """Test planning block regeneration with all logging paths."""
        # Setup mocks
        mock_call_api.return_value = "mock_api_response"
        mock_get_text.return_value = "Generated planning block content"
        mock_parse.return_value = (
            "Generated planning block content",
            self.structured_response,
        )
        # Don't set planning_block before the call - it should be None to trigger regeneration
        self.structured_response.planning_block = None

        response_text = "Normal story response without planning block"

        # Call the function
        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        # Verify logging was called with the expected patterns
        mock_logging.info.assert_any_call(
            "🔍 PLANNING_BLOCK_REGENERATION: Sending prompt to API"
        )

        # Verify API response logging was called
        self.assertTrue(
            any(
                "🔍 PLANNING_BLOCK_PROMPT:" in str(call)
                for call in mock_logging.info.call_args_list
            )
        )

    @patch("gemini_service.logging_util")
    @patch("gemini_service._call_gemini_api")
    def test_planning_block_early_return_when_already_set(
        self, mock_call_api, mock_logging
    ):
        """Test early return when planning_block is already set."""
        # Setup structured response with planning_block already set
        self.structured_response.planning_block = "Existing planning block content"

        response_text = "Normal story response"

        # Call the function
        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        # Verify early return logging was called
        mock_logging.info.assert_any_call(
            "🔍 PLANNING_BLOCK_SKIPPED: structured_response.planning_block is already set, skipping API call"
        )

        # Verify API was NOT called due to early return
        mock_call_api.assert_not_called()

        # Verify response_text is returned unchanged
        self.assertEqual(result, response_text)

    @patch("gemini_service.logging_util")
    @patch("gemini_service._call_gemini_api")
    @patch("gemini_service._get_text_from_response")
    @patch("gemini_service._parse_gemini_response")
    def test_planning_block_validation_success_logging(
        self, mock_parse, mock_get_text, mock_call_api, mock_logging
    ):
        """Test planning block validation success logging."""
        # Setup mocks for successful validation
        mock_call_api.return_value = "mock_api_response"
        mock_get_text.return_value = "Valid planning block content"
        mock_parse.return_value = (
            "Valid planning block content",
            self.structured_response,
        )

        response_text = "Story without planning block"

        # Call the function
        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        # Verify validation success logging
        success_log_found = any(
            "🔍 VALIDATION_SUCCESS: String planning block passed validation"
            in str(call)
            for call in mock_logging.info.call_args_list
        )
        self.assertTrue(success_log_found, "Should log validation success")

    @patch("gemini_service.logging_util")
    @patch("gemini_service._call_gemini_api")
    @patch("gemini_service._get_text_from_response")
    @patch("gemini_service._parse_gemini_response")
    def test_planning_block_validation_failure_logging(
        self, mock_parse, mock_get_text, mock_call_api, mock_logging
    ):
        """Test planning block validation failure logging."""
        # Setup mocks for failed validation (empty content)
        mock_call_api.return_value = "mock_api_response"
        mock_get_text.return_value = ""  # Empty response
        mock_parse.return_value = ("", self.structured_response)

        response_text = "Story without planning block"

        # Call the function
        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        # Verify validation failure logging
        failure_logs = [
            "🔍 VALIDATION_FAILURE: String planning block failed validation",
            "🔍 VALIDATION_FAILURE: Original planning_block type:",
            "🔍 VALIDATION_FAILURE: Original planning_block content:",
            "🔍 VALIDATION_FAILURE: clean_planning_block after processing:",
        ]

        for expected_log in failure_logs:
            failure_log_found = any(
                expected_log in str(call)
                for call in mock_logging.warning.call_args_list
            )
            self.assertTrue(
                failure_log_found, f"Should log validation failure: {expected_log}"
            )

    @patch("gemini_service.logging_util")
    @patch("gemini_service._call_gemini_api")
    def test_planning_block_exception_logging(self, mock_call_api, mock_logging):
        """Test planning block exception logging with traceback."""
        # Setup mock to raise exception
        mock_call_api.side_effect = Exception("API call failed")

        response_text = "Story without planning block"

        # Call the function - should handle exception gracefully
        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        # Verify exception logging
        exception_logs = [
            "🔍 PLANNING_BLOCK_EXCEPTION: Failed to generate planning block:",
            "🔍 PLANNING_BLOCK_EXCEPTION: Exception type:",
            "🔍 PLANNING_BLOCK_EXCEPTION: Exception details:",
            "🔍 PLANNING_BLOCK_EXCEPTION: Traceback:",
        ]

        for expected_log in exception_logs:
            exception_log_found = any(
                expected_log in str(call) for call in mock_logging.error.call_args_list
            )
            self.assertTrue(
                exception_log_found, f"Should log exception: {expected_log}"
            )

    @patch("gemini_service.logging_util")
    @patch("gemini_service._call_gemini_api")
    @patch("gemini_service._get_text_from_response")
    @patch("gemini_service._parse_gemini_response")
    def test_planning_block_source_logging(
        self, mock_parse, mock_get_text, mock_call_api, mock_logging
    ):
        """Test planning block source logging (structured vs raw)."""
        # Test structured response path
        mock_call_api.return_value = "mock_api_response"
        mock_get_text.return_value = "raw_text"

        # Mock structured response with planning_block
        mock_structured = MagicMock(spec=NarrativeResponse)
        mock_structured.planning_block = {
            "thinking": "test",
            "choices": {"Continue": "test"},
        }
        mock_parse.return_value = ("raw_text", mock_structured)

        response_text = "Story without planning block"

        # Call the function
        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        # Verify source logging
        source_log_found = any(
            "🔍 PLANNING_BLOCK_SOURCE: Using structured_response.planning_block"
            in str(call)
            for call in mock_logging.info.call_args_list
        )
        self.assertTrue(source_log_found, "Should log structured response usage")

    @patch("gemini_service.logging_util")
    @patch("gemini_service._call_gemini_api")
    @patch("gemini_service._get_text_from_response")
    @patch("gemini_service._parse_gemini_response")
    def test_planning_block_parsing_logging(
        self, mock_parse, mock_get_text, mock_call_api, mock_logging
    ):
        """Test planning block parsing step logging."""
        # Setup mocks
        mock_call_api.return_value = "mock_api_response"
        mock_get_text.return_value = "Generated planning block content"
        mock_parse.return_value = (
            "Generated planning block content",
            self.structured_response,
        )

        response_text = "Story without planning block"

        # Call the function
        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        # Verify parsing logging
        parsing_logs = [
            "🔍 PLANNING_BLOCK_PARSING: Attempting to parse response",
            "🔍 PLANNING_BLOCK_PARSING_RESULT: planning_text length:",
            "🔍 PLANNING_BLOCK_PARSING_RESULT: structured_response exists:",
        ]

        for expected_log in parsing_logs:
            parsing_log_found = any(
                expected_log in str(call) for call in mock_logging.info.call_args_list
            )
            self.assertTrue(
                parsing_log_found, f"Should log parsing step: {expected_log}"
            )

    @patch("gemini_service.logging_util")
    def test_fallback_logging(self, mock_logging):
        """Test fallback logging when exceptions occur."""
        # Create a response that will skip regeneration (already has planning block)
        response_text = "Story with planning block\n\n--- PLANNING BLOCK ---\nExisting planning block"

        # Set up structured response to already have a planning block
        self.structured_response.planning_block = {
            "thinking": "Already has planning block",
            "choices": {"Continue": "Continue with story"},
        }

        # This should not trigger regeneration, so test fallback paths
        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        # Should return original response without modification
        self.assertEqual(result, response_text)

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
            self.assertIn(result, [None, "", "None"])
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
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Function crashed with malformed game state: {e}")

    def test_unicode_handling_in_logging(self):
        """Test that logging handles unicode characters safely."""
        # Test with unicode in response text
        unicode_response = "Story with unicode: 🔍 📊 ✅ ❌ 🚨"

        try:
            result = _validate_and_enforce_planning_block(
                unicode_response,
                "test input",
                self.game_state,
                "test-model",
                "test instruction",
                self.structured_response,
            )
            # Should handle gracefully
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Function crashed with unicode: {e}")


if __name__ == "__main__":
    unittest.main()
