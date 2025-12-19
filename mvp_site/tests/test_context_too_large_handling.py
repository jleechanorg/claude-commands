"""
Test: ContextTooLargeError Handling

Tests verify that ContextTooLargeError from providers is caught and converted
to LLMRequestError with HTTP 422 status, providing clear user feedback.

The implementation (from origin/main) converts ContextTooLargeError to
LLMRequestError(status_code=422) with a helpful message.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from mvp_site import constants
from mvp_site.llm_providers.provider_utils import ContextTooLargeError
from mvp_site.llm_request import LLMRequestError


class TestContextTooLargeHandling(unittest.TestCase):
    """Test that ContextTooLargeError is converted to LLMRequestError with 422."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"
        os.environ["MOCK_SERVICES_MODE"] = "false"

    def tearDown(self):
        """Clean up after test."""
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

    @patch("mvp_site.llm_service.gemini_provider")
    def test_context_too_large_error_returns_422_status(
        self, mock_gemini
    ):
        """
        ContextTooLargeError should be converted to LLMRequestError with 422 status.

        This ensures users get a clear HTTP error instead of a generic 500.
        """
        from mvp_site.llm_service import _call_llm_api

        # Provider raises ContextTooLargeError
        ctx_err = ContextTooLargeError(
            "Context too large: prompt used 100,000 tokens",
            prompt_tokens=100000,
            completion_tokens=0,
            finish_reason="length",
        )
        # Routing can use either native tools or JSON-first tool_requests depending on model/provider
        mock_gemini.generate_content_with_native_tools.side_effect = ctx_err
        mock_gemini.generate_content_with_tool_requests.side_effect = ctx_err

        # Act & Assert: Should raise LLMRequestError with 422 status
        # Ensure we don't fall back to other providers due to missing key
        with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"}):
            with self.assertRaises(LLMRequestError) as ctx:
                _call_llm_api(
                    prompt_contents=["Test prompt"],
                    model_name="gemini-2.0-flash",
                    system_instruction_text="System instruction",
                    provider_name=constants.LLM_PROVIDER_GEMINI,
                )

        # Verify 422 status code (Unprocessable Entity - context too large)
        self.assertEqual(ctx.exception.status_code, 422)

    @patch("mvp_site.llm_service.gemini_provider")
    def test_context_too_large_error_message_is_helpful(
        self, mock_gemini
    ):
        """
        LLMRequestError from ContextTooLargeError should contain helpful message.
        """
        from mvp_site.llm_service import _call_llm_api

        # Provider raises ContextTooLargeError with token info
        ctx_err = ContextTooLargeError(
            "Context too large: prompt used 100,000 tokens",
            prompt_tokens=100000,
            completion_tokens=0,
            finish_reason="length",
        )
        # Routing can use either native tools or JSON-first tool_requests depending on model/provider
        mock_gemini.generate_content_with_native_tools.side_effect = ctx_err
        mock_gemini.generate_content_with_tool_requests.side_effect = ctx_err

        # Ensure we don't fall back to other providers due to missing key
        with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"}):
            with self.assertRaises(LLMRequestError) as ctx:
                _call_llm_api(
                    prompt_contents=["Test prompt"],
                    model_name="gemini-2.0-flash",
                    system_instruction_text="System instruction",
                    provider_name=constants.LLM_PROVIDER_GEMINI,
                )

        # Error message should contain useful debugging info
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
