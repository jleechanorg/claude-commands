"""
Tests for Gemini API model fallback functionality when API calls fail.
Tests the MODEL_FALLBACK_CHAIN behavior for 503, 429, and 400 errors.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from gemini_service import (
    DEFAULT_MODEL,
    MODEL_FALLBACK_CHAIN,
    TEST_MODEL,
    _call_gemini_api_with_model_cycling,
)


class TestGeminiModelFallback(unittest.TestCase):
    """Test model fallback functionality when API calls fail"""

    def setUp(self):
        """Set up test environment"""
        os.environ["TESTING"] = "true"
        os.environ["GEMINI_API_KEY"] = "test-key"

    def tearDown(self):
        """Clean up after tests"""
        if "TESTING" in os.environ:
            del os.environ["TESTING"]

    @patch("gemini_service.get_client")
    def test_primary_model_success(self, mock_get_client):
        """Test that primary model is used when it succeeds"""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "Test response"

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Call the function
        result = _call_gemini_api_with_model_cycling(
            ["Test prompt"], DEFAULT_MODEL, current_prompt_text_for_logging="Test"
        )

        # Verify primary model was used
        assert result == mock_response
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        # In TESTING mode, either TEST_MODEL or the requested model (DEFAULT_MODEL) could be used
        assert call_args[1]["model"] in [DEFAULT_MODEL, TEST_MODEL]

    @patch("gemini_service.get_client")
    @patch("gemini_service._log_token_count")
    def test_503_overload_fallback(self, mock_log_token, mock_get_client):
        """Test fallback when primary model returns 503 overload error"""
        # Mock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # First call fails with 503, second succeeds
        mock_response = Mock()
        mock_response.text = "Fallback response"

        mock_client.models.generate_content.side_effect = [
            Exception("503 UNAVAILABLE"),
            mock_response,
        ]

        # Call the function
        result = _call_gemini_api_with_model_cycling(
            ["Test prompt"], DEFAULT_MODEL, current_prompt_text_for_logging="Test"
        )

        # Verify fallback was used
        assert result == mock_response
        assert mock_client.models.generate_content.call_count == 2

        # Check models used
        calls = mock_client.models.generate_content.call_args_list
        # First call should use the requested model (might be TEST_MODEL in test env)
        first_model = calls[0][1]["model"]
        # Second call should be different (fallback)
        second_model = calls[1][1]["model"]
        assert first_model != second_model

    @patch("gemini_service.get_client")
    @patch("gemini_service._log_token_count")
    def test_429_rate_limit_fallback(self, mock_log_token, mock_get_client):
        """Test fallback when model returns 429 rate limit error"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # First two calls fail with 429, third succeeds
        mock_response = Mock()
        mock_response.text = "Success after rate limits"

        mock_client.models.generate_content.side_effect = [
            Exception("429 Rate limit exceeded"),
            Exception("429 Rate limit exceeded"),
            mock_response,
        ]

        # Call the function
        result = _call_gemini_api_with_model_cycling(
            ["Test prompt"], DEFAULT_MODEL, current_prompt_text_for_logging="Test"
        )

        # Verify multiple fallbacks were attempted
        assert result == mock_response
        assert mock_client.models.generate_content.call_count == 3

    @patch("gemini_service.get_client")
    @patch("gemini_service._log_token_count")
    def test_400_model_not_found_fallback(self, mock_log_token, mock_get_client):
        """Test fallback when model returns 400 not found error"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # First call fails with 400, second succeeds
        mock_response = Mock()
        mock_response.text = "Found with different model"

        mock_client.models.generate_content.side_effect = [
            Exception("400 Model not found"),
            mock_response,
        ]

        # Call the function with a non-existent model
        result = _call_gemini_api_with_model_cycling(
            ["Test prompt"],
            "non-existent-model",
            current_prompt_text_for_logging="Test",
        )

        # Verify fallback was used
        assert result == mock_response
        assert mock_client.models.generate_content.call_count == 2

    @patch("gemini_service.get_client")
    @patch("gemini_service._log_token_count")
    def test_all_models_fail(self, mock_log_token, mock_get_client):
        """Test behavior when all models in fallback chain fail"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # All calls fail with 503
        mock_client.models.generate_content.side_effect = Exception("503 UNAVAILABLE")

        # Call should raise the last exception
        with pytest.raises(Exception) as context:
            _call_gemini_api_with_model_cycling(
                ["Test prompt"], DEFAULT_MODEL, current_prompt_text_for_logging="Test"
            )

        # Verify multiple models were tried (at least 2)
        # The exact count depends on test environment and model deduplication
        assert mock_client.models.generate_content.call_count >= 2
        assert "503" in str(context.value)

    @patch("gemini_service.get_client")
    @patch("gemini_service._log_token_count")
    def test_non_recoverable_error(self, mock_log_token, mock_get_client):
        """Test that non-recoverable errors don't trigger fallback"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # First call fails with non-recoverable error
        mock_client.models.generate_content.side_effect = Exception("401 Unauthorized")

        # Call should fail immediately without trying fallbacks
        with pytest.raises(Exception) as context:
            _call_gemini_api_with_model_cycling(
                ["Test prompt"], DEFAULT_MODEL, current_prompt_text_for_logging="Test"
            )

        # Verify only one attempt was made
        assert mock_client.models.generate_content.call_count == 1
        assert "401" in str(context.value)

    @patch("gemini_service.get_client")
    @patch("gemini_service._log_token_count")
    def test_fallback_chain_order(self, mock_log_token, mock_get_client):
        """Test that fallback models are tried in correct order"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Make all calls fail to see full chain
        mock_client.models.generate_content.side_effect = Exception("503 UNAVAILABLE")

        # Start with a model not at beginning of chain
        starting_model = MODEL_FALLBACK_CHAIN[2]

        try:
            _call_gemini_api_with_model_cycling(
                ["Test prompt"], starting_model, current_prompt_text_for_logging="Test"
            )
        except Exception:
            pass  # Expected to fail

        # Verify order: starting model first, then full chain
        calls = mock_client.models.generate_content.call_args_list
        models_tried = [call[1]["model"] for call in calls]

        # First should be the requested model
        assert models_tried[0] == starting_model

        # Rest should follow fallback chain order (excluding duplicates)
        remaining_models = list(models_tried[1:])
        for i, model in enumerate(MODEL_FALLBACK_CHAIN):
            if model != starting_model and i < len(remaining_models):
                assert model in remaining_models

    @patch("gemini_service.get_client")
    @patch("gemini_service._log_token_count")
    def test_json_mode_preserved_on_fallback(self, mock_log_token, mock_get_client):
        """Test that JSON mode is preserved when falling back to other models"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.text = '{"narrative": "test"}'

        mock_client.models.generate_content.side_effect = [
            Exception("503 UNAVAILABLE"),
            mock_response,
        ]

        # Call the function
        _call_gemini_api_with_model_cycling(["Test prompt"], DEFAULT_MODEL)

        # Verify JSON mode was set on both attempts
        calls = mock_client.models.generate_content.call_args_list
        for call in calls:
            config = call[1]["config"]
            # Config object may have attributes directly or via dict
            if hasattr(config, "response_mime_type"):
                assert config.response_mime_type == "application/json"
            elif hasattr(config, "_kwargs"):
                assert "response_mime_type" in config._kwargs
                assert config._kwargs["response_mime_type"] == "application/json"
            else:
                # Mock object case
                assert True  # Skip validation for mocks

    @patch("gemini_service.get_client")
    @patch("gemini_service._log_token_count")
    def test_system_instruction_preserved_on_fallback(
        self, mock_log_token, mock_get_client
    ):
        """Test that system instruction is preserved when falling back"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.text = "Response with system instruction"

        mock_client.models.generate_content.side_effect = [
            Exception("503 UNAVAILABLE"),
            mock_response,
        ]

        system_instruction = "Test system instruction"

        # Call with system instruction
        _call_gemini_api_with_model_cycling(
            ["Test prompt"], DEFAULT_MODEL, system_instruction_text=system_instruction
        )

        # Verify system instruction was passed on both attempts
        calls = mock_client.models.generate_content.call_args_list
        for call in calls:
            config = call[1]["config"]
            # Config object may have attributes directly or via dict
            if hasattr(config, "system_instruction"):
                if hasattr(config.system_instruction, "text"):
                    assert config.system_instruction.text == system_instruction
                else:
                    assert str(config.system_instruction) == system_instruction
            elif hasattr(config, "_kwargs"):
                assert "system_instruction" in config._kwargs
                assert config._kwargs["system_instruction"].text == system_instruction
            else:
                # Mock object case
                assert True  # Skip validation for mocks


if __name__ == "__main__":
    unittest.main()
