"""
Test: Auto-Fallback to Larger Context Model

When ContextTooLargeError occurs, the system should automatically try
to fallback to a model with a larger context window (e.g., Gemini 2.0 Flash
with 1M context) before giving up with an error.

This test validates the fix for GCP error logs showing:
"Context too large for model zai-glm-4.6: input uses 95,622 tokens,
max allowed is 94,372 tokens"

Instead of failing immediately, the system should:
1. Detect context exceeds current model's limit
2. Check if a larger model is available (Gemini 2.0 Flash has 1M context)
3. Retry with the larger model
4. Only fail if no larger model is available or if fallback also fails
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from mvp_site import constants
from mvp_site.llm_providers.provider_utils import ContextTooLargeError
from mvp_site.llm_request import LLMRequestError


class TestAutoFallbackToLargerContext(unittest.TestCase):
    """Test automatic fallback to larger context model when context is too large."""

    def setUp(self):
        """Set up test environment."""
        os.environ["TESTING"] = "true"
        os.environ["MOCK_SERVICES_MODE"] = "false"

    def tearDown(self):
        """Clean up after test."""
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

    @patch("mvp_site.llm_service.gemini_provider")
    @patch("mvp_site.llm_service.cerebras_provider")
    def test_cerebras_context_too_large_falls_back_to_gemini(
        self, mock_cerebras, mock_gemini
    ):
        """
        RED TEST: When Cerebras model context is too large, should fallback to Gemini.

        Scenario:
        - User is on Cerebras zai-glm-4.6 (131K context)
        - Input tokens exceed 80% of context (94K threshold)
        - System should automatically try Gemini 2.0 Flash (1M context)
        - Request should succeed with the larger model
        """
        from mvp_site.llm_service import _call_llm_api

        # Cerebras raises ContextTooLargeError (input 95K > 94K max)
        mock_cerebras.generate_content.side_effect = ContextTooLargeError(
            "Context too large for model zai-glm-4.6: input uses 95,622 tokens, "
            "max allowed is 94,372 tokens",
            prompt_tokens=95622,
            completion_tokens=0,
            finish_reason="context_exceeded",
        )

        # Gemini should succeed with its larger context window
        mock_response = MagicMock()
        mock_response.text = '{"narrative": "Story continues successfully"}'
        mock_gemini.generate_json_mode_content.return_value = mock_response

        # Act: Call with Cerebras model
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False):
            result = _call_llm_api(
                prompt_contents=["Long story context..."] * 100,  # Simulate large context
                model_name="zai-glm-4.6",
                system_instruction_text="System instruction",
                provider_name=constants.LLM_PROVIDER_CEREBRAS,
                allow_context_fallback=True,  # Enable fallback
            )

        # Assert: Should have called Gemini after Cerebras failed
        mock_gemini.generate_json_mode_content.assert_called_once()
        self.assertIsNotNone(result)

    @patch("mvp_site.llm_service.gemini_provider")
    def test_gemini_context_too_large_no_fallback_available(
        self, mock_gemini
    ):
        """
        When Gemini (largest model) context is too large, should raise error.

        Gemini 2.0 Flash has the largest context (1M), so if it fails
        there's no larger model to fallback to - error should propagate.
        """
        from mvp_site.llm_service import _call_llm_api

        # Even Gemini with 1M context is exceeded
        mock_gemini.generate_json_mode_content.side_effect = ContextTooLargeError(
            "Context too large for model gemini-2.0-flash: input uses 850,000 tokens",
            prompt_tokens=850000,
            completion_tokens=0,
            finish_reason="context_exceeded",
        )

        # Act & Assert: Should raise LLMRequestError since no larger model exists
        with self.assertRaises(LLMRequestError) as ctx:
            _call_llm_api(
                prompt_contents=["Extremely long context..."],
                model_name="gemini-2.0-flash",
                system_instruction_text="System instruction",
                provider_name=constants.LLM_PROVIDER_GEMINI,
                allow_context_fallback=True,
            )

        self.assertEqual(ctx.exception.status_code, 422)

    @patch("mvp_site.llm_service.gemini_provider")
    @patch("mvp_site.llm_service.cerebras_provider")
    def test_fallback_disabled_raises_error_immediately(
        self, mock_cerebras, mock_gemini
    ):
        """
        When allow_context_fallback=False, should not attempt fallback.

        Some users may prefer to fail immediately rather than switch models.
        """
        from mvp_site.llm_service import _call_llm_api

        # Cerebras raises ContextTooLargeError
        mock_cerebras.generate_content.side_effect = ContextTooLargeError(
            "Context too large for model zai-glm-4.6",
            prompt_tokens=95622,
            completion_tokens=0,
            finish_reason="context_exceeded",
        )

        # Act & Assert: Should raise error without trying Gemini
        with self.assertRaises(LLMRequestError) as ctx:
            _call_llm_api(
                prompt_contents=["Long story context..."],
                model_name="zai-glm-4.6",
                system_instruction_text="System instruction",
                provider_name=constants.LLM_PROVIDER_CEREBRAS,
                allow_context_fallback=False,  # Disable fallback
            )

        # Gemini should NOT have been called
        mock_gemini.generate_json_mode_content.assert_not_called()
        self.assertEqual(ctx.exception.status_code, 422)

    @patch("mvp_site.llm_service.gemini_provider")
    @patch("mvp_site.llm_service.cerebras_provider")
    def test_openrouter_context_too_large_falls_back_to_gemini(
        self, mock_cerebras, mock_gemini
    ):
        """
        When OpenRouter model context is too large, should fallback to Gemini.
        """
        from mvp_site.llm_service import _call_llm_api

        # Mock OpenRouter via the same pattern (openrouter raises error)
        with patch("mvp_site.llm_service.openrouter_provider") as mock_openrouter:
            mock_openrouter.generate_content.side_effect = ContextTooLargeError(
                "Context too large for OpenRouter model",
                prompt_tokens=120000,
                completion_tokens=0,
                finish_reason="context_exceeded",
            )

            # Gemini should succeed
            mock_response = MagicMock()
            mock_response.text = '{"narrative": "Fallback worked"}'
            mock_gemini.generate_json_mode_content.return_value = mock_response

            # Act
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False):
                result = _call_llm_api(
                    prompt_contents=["Long context..."],
                    model_name="meta-llama/llama-3.1-70b-instruct",
                    system_instruction_text="System instruction",
                    provider_name=constants.LLM_PROVIDER_OPENROUTER,
                    allow_context_fallback=True,
                )

            # Assert: Gemini was used as fallback
            mock_gemini.generate_json_mode_content.assert_called_once()
            self.assertIsNotNone(result)


class TestContextFallbackModelSelection(unittest.TestCase):
    """Test model selection for context fallback."""

    def test_get_larger_context_model_for_cerebras(self):
        """Should return Gemini as fallback for Cerebras models."""
        from mvp_site.llm_service import _get_larger_context_model

        provider, model = _get_larger_context_model(
            current_provider=constants.LLM_PROVIDER_CEREBRAS,
            current_model="zai-glm-4.6",
        )

        # Gemini 2.0 Flash has the largest context window (1M)
        self.assertEqual(provider, constants.LLM_PROVIDER_GEMINI)
        self.assertEqual(model, "gemini-2.0-flash")

    def test_get_larger_context_model_for_openrouter(self):
        """Should return Gemini as fallback for OpenRouter models."""
        from mvp_site.llm_service import _get_larger_context_model

        provider, model = _get_larger_context_model(
            current_provider=constants.LLM_PROVIDER_OPENROUTER,
            current_model="meta-llama/llama-3.1-70b-instruct",
        )

        self.assertEqual(provider, constants.LLM_PROVIDER_GEMINI)
        self.assertEqual(model, "gemini-2.0-flash")

    def test_get_larger_context_model_for_gemini_returns_none(self):
        """Should return None for Gemini since it already has the largest context."""
        from mvp_site.llm_service import _get_larger_context_model

        result = _get_larger_context_model(
            current_provider=constants.LLM_PROVIDER_GEMINI,
            current_model="gemini-2.0-flash",
        )

        # No larger model available
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
