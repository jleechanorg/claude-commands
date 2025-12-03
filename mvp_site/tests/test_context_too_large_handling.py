"""
Red-Green TDD Test: ContextTooLargeError Handling - RED PHASE

Tests verify that ContextTooLargeError from providers is caught and handled
gracefully by _call_llm_api_with_model_cycling, rather than crashing user flows.

BUG: After removal of CONTEXT_FALLBACK_CHAIN, ContextTooLargeError is no longer
caught in the exception handler, causing 500 errors on long sessions.

Expected behavior: The model cycling loop should catch ContextTooLargeError and
either try a larger-context model or raise a user-friendly error.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from mvp_site import constants
from mvp_site.llm_providers.provider_utils import ContextTooLargeError


class TestContextTooLargeHandling(unittest.TestCase):
    """Test that ContextTooLargeError is handled gracefully in model cycling."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"
        os.environ["MOCK_SERVICES_MODE"] = "false"

    def tearDown(self):
        """Clean up after test."""
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

    @patch("mvp_site.llm_service.gemini_provider")
    def test_context_too_large_error_triggers_model_fallback(
        self, mock_gemini
    ):
        """
        GREEN TEST: ContextTooLargeError should trigger fallback to next model.

        When a model raises ContextTooLargeError (e.g., prompt too large for context
        window), the cycling loop should try the next model in the fallback chain.
        """
        from mvp_site.llm_service import _call_llm_api_with_model_cycling

        # First call raises ContextTooLargeError, second fallback succeeds
        mock_fallback_response = MagicMock()
        mock_fallback_response.text = '{"narrative": "Success after fallback"}'

        mock_gemini.generate_json_mode_content.side_effect = [
            # First model fails with ContextTooLargeError
            ContextTooLargeError(
                "Context too large: prompt used 100,000 tokens",
                prompt_tokens=100000,
                completion_tokens=0,
                finish_reason="length",
            ),
            # Second model (fallback within Gemini) succeeds
            mock_fallback_response,
        ]

        # Act: This should NOT raise, but fall back to next Gemini model
        result = _call_llm_api_with_model_cycling(
            prompt_contents=["Test prompt"],
            model_name="gemini-2.0-flash",
            system_instruction_text="System instruction",
            provider_name=constants.LLM_PROVIDER_GEMINI,
        )

        # Assert: Should have succeeded with fallback model
        self.assertIsNotNone(result)
        self.assertEqual(result.text, '{"narrative": "Success after fallback"}')

        # Verify Gemini was called twice (original + one fallback)
        self.assertEqual(mock_gemini.generate_json_mode_content.call_count, 2)

    @patch("mvp_site.llm_service.gemini_provider")
    def test_context_too_large_error_raises_friendly_message_when_no_fallback(
        self, mock_gemini
    ):
        """
        RED TEST: When all models fail with ContextTooLargeError, raise user-friendly error.

        If ContextTooLargeError occurs and no fallback succeeds, the error message
        should be clear and actionable, not a generic 500.
        """
        from mvp_site.llm_service import _call_llm_api_with_model_cycling

        # All models raise ContextTooLargeError (simulating exhausted fallbacks)
        context_error = ContextTooLargeError(
            "Context too large: prompt used 100,000 tokens",
            prompt_tokens=100000,
            completion_tokens=0,
            finish_reason="length",
        )
        mock_gemini.generate_json_mode_content.side_effect = context_error

        # Act & Assert: Should raise ContextTooLargeError with helpful message
        # after trying all fallback models
        with self.assertRaises(ContextTooLargeError) as ctx:
            _call_llm_api_with_model_cycling(
                prompt_contents=["Test prompt"],
                model_name="gemini-2.0-flash",
                system_instruction_text="System instruction",
                provider_name=constants.LLM_PROVIDER_GEMINI,
            )

        # The error should contain the token count info for debugging
        self.assertIn("100,000", str(ctx.exception))


class TestDefaultProviderFallback(unittest.TestCase):
    """Test that default provider gracefully falls back when API key is missing."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False)
    @patch("mvp_site.llm_service.cerebras_provider")
    def test_missing_gemini_key_falls_back_to_cerebras(self, mock_cerebras):
        """
        RED TEST: When GEMINI_API_KEY is missing and default is gemini,
        should fall back to cerebras if CEREBRAS_API_KEY is available.

        This prevents hard failures in environments with partial API key setup.
        """
        from mvp_site import llm_service

        # Cerebras should work when Gemini fails
        mock_response = MagicMock()
        mock_response.text = '{"narrative": "Cerebras fallback success"}'
        mock_cerebras.generate_content.return_value = mock_response

        # The system should detect missing Gemini key and use Cerebras
        # This tests the provider selection logic, not the full API call
        with patch.dict(
            os.environ,
            {"CEREBRAS_API_KEY": "test-cerebras-key", "GEMINI_API_KEY": ""},
            clear=False,
        ):
            # Get the effective provider when Gemini key is missing
            provider, model = llm_service._select_provider_with_fallback()

            # Should have fallen back to cerebras
            self.assertEqual(provider, constants.LLM_PROVIDER_CEREBRAS)


if __name__ == "__main__":
    unittest.main()
