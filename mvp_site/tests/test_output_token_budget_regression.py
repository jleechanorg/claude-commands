"""
Regression tests for output token budget calculation.

These tests ensure that the output token budget is calculated correctly
based on the actual model context window, not the compaction limit.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from mvp_site import constants, llm_service
from mvp_site.llm_providers import gemini_provider


class TestOutputTokenBudgetRegression(unittest.TestCase):
    """Tests for output token budget calculation regressions."""

    def test_safe_output_limit_uses_model_context_window(self):
        """
        Output budget uses ACTUAL model context window, not compaction limit.

        Bug fixed: Previously used GEMINI_COMPACTION_TOKEN_LIMIT (300K) for output calc,
        which starved output to 1 token when input exceeded 300K.

        Fix: Use actual model context (1M for Gemini 2.5 Pro) for output calculation.
        Compaction limit is only for INPUT compaction decisions.
        """
        prompt_tokens = 1_000
        system_tokens = 500

        # Use actual model context window for output calculation
        model_context = constants.MODEL_CONTEXT_WINDOW_TOKENS.get(
            constants.DEFAULT_GEMINI_MODEL, constants.DEFAULT_CONTEXT_WINDOW_TOKENS
        )
        safe_context = int(model_context * constants.CONTEXT_WINDOW_SAFETY_RATIO)

        expected = min(
            llm_service.JSON_MODE_MAX_OUTPUT_TOKENS,
            safe_context - (prompt_tokens + system_tokens),
        )

        result = llm_service._get_safe_output_token_limit(
            constants.DEFAULT_GEMINI_MODEL,
            prompt_tokens,
            system_tokens,
        )
        self.assertEqual(result, expected)

    def test_safe_output_limit_high_input_does_not_starve_output(self):
        """
        Regression test: Even with 301K input tokens, output should NOT be starved to 1 token.

        Bug: When input > 300K (GEMINI_COMPACTION_TOKEN_LIMIT), remaining was calculated as:
        remaining = max(1, 300K - 301K) = 1 token - starving output completely!

        Fix: Use actual model context (1M) for output calculation, ensuring minimum of
        OUTPUT_TOKEN_RESERVE_MIN (1024) tokens when there's headroom.
        """
        # Simulate the bug scenario: input tokens exceed old compaction limit but within model context
        prompt_tokens = 300_000
        system_tokens = 5_000  # Total input: 305K tokens (within 900K safe context)

        output_limit = llm_service._get_safe_output_token_limit(
            constants.DEFAULT_GEMINI_MODEL,
            prompt_tokens,
            system_tokens,
        )

        # Output should be at least OUTPUT_TOKEN_RESERVE_MIN since we have headroom
        self.assertGreaterEqual(
            output_limit,
            llm_service.OUTPUT_TOKEN_RESERVE_MIN,
            f"Output starved to {output_limit} tokens! "
            f"Should be at least {llm_service.OUTPUT_TOKEN_RESERVE_MIN}",
        )

    def test_safe_output_limit_context_exceeded_raises_error(self):
        """
        Edge case: When input exceeds 80% of safe context, raise ValueError.

        We reserve 20% of context for output tokens. If input uses more than 80%,
        there's not enough room for quality output, so fail fast with a clear error.

        This allows model cycling to try a model with larger context, or the caller
        can handle the error appropriately.
        """
        # Gemini safe context = 1M * 0.9 = 900K tokens
        # Max input allowed = 900K * 0.8 = 720K tokens (reserve 20% = 180K for output)
        model_context = constants.MODEL_CONTEXT_WINDOW_TOKENS.get(
            constants.DEFAULT_GEMINI_MODEL, constants.DEFAULT_CONTEXT_WINDOW_TOKENS
        )
        safe_context = int(model_context * constants.CONTEXT_WINDOW_SAFETY_RATIO)
        output_reserve = int(safe_context * llm_service.OUTPUT_TOKEN_RESERVE_RATIO)
        max_input_allowed = safe_context - output_reserve

        # Input exceeds 80% threshold by 1K tokens
        prompt_tokens = max_input_allowed + 1_000
        system_tokens = 0

        with self.assertRaises(ValueError) as ctx:
            llm_service._get_safe_output_token_limit(
                constants.DEFAULT_GEMINI_MODEL,
                prompt_tokens,
                system_tokens,
            )

        error_msg = str(ctx.exception)
        self.assertTrue(
            "context" in error_msg.lower() or "token" in error_msg.lower(),
            f"Error should mention context or tokens, got: {error_msg}",
        )
        self.assertTrue(
            "20%" in error_msg or "80%" in error_msg,
            f"Error should mention the 20%/80% reserve ratio, got: {error_msg}",
        )

    def test_output_budget_independent_of_input_size(self):
        """
        Output token budget should be independent of input token size.

        Principle: The output budget should hit JSON_MODE_MAX_OUTPUT_TOKENS cap
        regardless of whether input is 1K, 100K, or 500K tokens - as long as we're
        within model context limits.

        This ensures consistent generation quality regardless of conversation length.
        """
        # Test various input sizes - all should get the same output budget
        input_sizes = [
            (1_000, 500),  # Small: 1.5K tokens
            (50_000, 10_000),  # Medium: 60K tokens
            (200_000, 50_000),  # Large: 250K tokens
            (400_000, 100_000),  # Very large: 500K tokens (still within 1M context)
        ]

        output_budgets = []
        for prompt_tokens, system_tokens in input_sizes:
            output_limit = llm_service._get_safe_output_token_limit(
                constants.DEFAULT_GEMINI_MODEL,
                prompt_tokens,
                system_tokens,
            )
            output_budgets.append(output_limit)

        # All should hit the same cap (JSON_MODE_MAX_OUTPUT_TOKENS)
        # because we have plenty of context headroom in a 1M token model
        expected_cap = llm_service.JSON_MODE_MAX_OUTPUT_TOKENS

        for i, (input_size, budget) in enumerate(zip(input_sizes, output_budgets)):
            total_input = input_size[0] + input_size[1]
            self.assertEqual(
                budget,
                expected_cap,
                f"Input size {total_input:,} got output budget {budget:,}, "
                f"expected {expected_cap:,}. Output should be independent of input size!",
            )

    def test_safe_output_limit_respects_context_budget_for_llama(self):
        """Test output limit respects context budget for Llama models."""
        prompt_tokens = 20_000
        system_tokens = 5_000

        safe_budget = int(
            constants.MODEL_CONTEXT_WINDOW_TOKENS["llama-3.3-70b"]
            * constants.CONTEXT_WINDOW_SAFETY_RATIO
        )
        # Use OUTPUT_TOKEN_RESERVE_MIN as minimum, not 1
        expected_remaining = max(
            llm_service.OUTPUT_TOKEN_RESERVE_MIN,
            safe_budget - (prompt_tokens + system_tokens),
        )
        model_cap = constants.MODEL_MAX_OUTPUT_TOKENS.get(
            "llama-3.3-70b", llm_service.JSON_MODE_MAX_OUTPUT_TOKENS
        )
        expected = min(
            llm_service.JSON_MODE_MAX_OUTPUT_TOKENS, model_cap, expected_remaining
        )

        result = llm_service._get_safe_output_token_limit(
            "llama-3.3-70b",  # Updated: 3.1-70b retired from Cerebras
            prompt_tokens,
            system_tokens,
        )
        self.assertEqual(result, expected)


class TestTokenCalculationProviders(unittest.TestCase):
    """Tests for provider-specific token calculation."""

    def test_calculate_tokens_cerebras_uses_estimate_not_gemini_api(self):
        """
        REGRESSION TEST: Cerebras provider must use estimate_tokens(), NOT Gemini API.

        Bug: When provider_name is 'cerebras', the code was calling gemini_provider.count_tokens()
        with a Cerebras model name (e.g., 'zai-glm-4.6'), causing 404 errors.

        The fix: _calculate_prompt_and_system_tokens() should check provider_name and use
        estimate_tokens() for non-Gemini providers.
        """
        user_prompt_contents = ["Hello, world!", "Test prompt"]
        system_instruction = "You are a helpful assistant."
        provider_name = constants.LLM_PROVIDER_CEREBRAS
        model_name = "zai-glm-4.6"  # A Cerebras model, not a Gemini model

        # Mock gemini_provider.count_tokens to fail if called (it should NOT be called)
        with patch(
            "mvp_site.llm_service.gemini_provider.count_tokens"
        ) as mock_gemini_count:
            mock_gemini_count.side_effect = Exception(
                "FAIL: gemini_provider.count_tokens() should NOT be called for Cerebras provider!"
            )

            # This should NOT raise an exception - it should use estimate_tokens() instead
            prompt_tokens, system_tokens = (
                llm_service._calculate_prompt_and_system_tokens(
                    user_prompt_contents, system_instruction, provider_name, model_name
                )
            )

            # Verify gemini API was NOT called
            mock_gemini_count.assert_not_called()

            # Verify we got reasonable token estimates
            self.assertGreater(
                prompt_tokens,
                0,
                f"Expected positive prompt_tokens, got {prompt_tokens}",
            )
            self.assertGreater(
                system_tokens,
                0,
                f"Expected positive system_tokens, got {system_tokens}",
            )

    def test_calculate_tokens_openrouter_uses_estimate_not_gemini_api(self):
        """Verify OpenRouter provider also uses estimate_tokens() instead of Gemini API."""
        user_prompt_contents = ["Test OpenRouter prompt"]
        system_instruction = "System instruction for OpenRouter"
        provider_name = constants.LLM_PROVIDER_OPENROUTER
        model_name = "anthropic/claude-3-opus"  # An OpenRouter model

        with patch(
            "mvp_site.llm_service.gemini_provider.count_tokens"
        ) as mock_gemini_count:
            mock_gemini_count.side_effect = Exception(
                "FAIL: gemini_provider.count_tokens() should NOT be called for OpenRouter provider!"
            )

            prompt_tokens, system_tokens = (
                llm_service._calculate_prompt_and_system_tokens(
                    user_prompt_contents, system_instruction, provider_name, model_name
                )
            )

            mock_gemini_count.assert_not_called()
            self.assertGreater(prompt_tokens, 0)
            self.assertGreater(system_tokens, 0)

    def test_calculate_tokens_gemini_uses_gemini_api(self):
        """Verify Gemini provider DOES use the Gemini API for token counting."""
        user_prompt_contents = ["Test Gemini prompt"]
        system_instruction = "System instruction for Gemini"
        provider_name = constants.LLM_PROVIDER_GEMINI
        model_name = constants.DEFAULT_GEMINI_MODEL

        with patch(
            "mvp_site.llm_service.gemini_provider.count_tokens"
        ) as mock_gemini_count:
            mock_gemini_count.return_value = 100  # Return mock token count

            prompt_tokens, system_tokens = (
                llm_service._calculate_prompt_and_system_tokens(
                    user_prompt_contents, system_instruction, provider_name, model_name
                )
            )

            # Gemini provider SHOULD call the Gemini API
            self.assertGreaterEqual(
                mock_gemini_count.call_count,
                1,
                "Gemini provider should use gemini_provider.count_tokens()",
            )


class TestEndToEndOutputBudget(unittest.TestCase):
    """End-to-end tests for output token budget."""

    def test_e2e_large_context_does_not_starve_output_tokens(self):
        """
        END-TO-END regression test: Large context input should NOT starve output tokens.

        This test exercises the FULL llm_service flow, only mocking EXTERNAL API calls:
        - gemini_provider.count_tokens (external API)
        - gemini_provider.generate_json_mode_content (external API)

        It verifies that when we have 305K input tokens:
        - OLD BUG: max_output_tokens was starved to 1 (because 300K compaction limit - 305K = -5K -> max(1, -5K) = 1)
        - FIX: max_output_tokens should be at least OUTPUT_TOKEN_RESERVE_MIN (1024)

        This test catches the output starvation bug at the integration level.
        """
        # Capture what json_mode_max_output_tokens is actually passed to the provider
        captured_max_output_tokens = None

        def mock_generate_json_mode_content(**kwargs):
            nonlocal captured_max_output_tokens
            captured_max_output_tokens = kwargs.get("json_mode_max_output_tokens")
            # Return a mock response object
            mock_response = MagicMock()
            mock_response.text = '{"narrative": "Test response"}'
            return mock_response

        # Simulate 305K input tokens (exceeds old 300K compaction limit)
        def mock_count_tokens(model_name, contents):
            # Return large token count to simulate the bug scenario
            return 300_000  # 300K tokens for prompt

        # Ensure we have an API key to avoid fallback logic
        with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"}):
            with (
                patch.object(
                    gemini_provider, "count_tokens", side_effect=mock_count_tokens
                ),
                patch.object(
                    # Updated to patch code_execution method as newer models (gemini-3) use this strategy
                    gemini_provider,
                    "generate_content_with_code_execution",
                    side_effect=mock_generate_json_mode_content,
                ),
            ):
                # Call the full LLM service flow
                llm_service._call_llm_api(
                    prompt_contents=["Large prompt content..."],
                    model_name=constants.DEFAULT_GEMINI_MODEL,
                    current_prompt_text_for_logging="Test large context",
                    system_instruction_text="System instruction (5K tokens simulated)",
                    provider_name=constants.LLM_PROVIDER_GEMINI,
                )

        # Verify output tokens were NOT starved
        self.assertIsNotNone(
            captured_max_output_tokens,
            "json_mode_max_output_tokens was not passed to provider",
        )
        self.assertGreaterEqual(
            captured_max_output_tokens,
            llm_service.OUTPUT_TOKEN_RESERVE_MIN,
            f"OUTPUT STARVATION BUG: max_output_tokens={captured_max_output_tokens} "
            f"but should be at least {llm_service.OUTPUT_TOKEN_RESERVE_MIN}. "
            f"This means the 305K input context starved the output budget!",
        )
        # With the fix, we should get a healthy output budget (close to JSON_MODE_MAX_OUTPUT_TOKENS)
        # since 305K input is well within the 1M model context
        self.assertEqual(
            captured_max_output_tokens,
            llm_service.JSON_MODE_MAX_OUTPUT_TOKENS,
            f"Expected max_output_tokens={llm_service.JSON_MODE_MAX_OUTPUT_TOKENS} (capped by JSON limit), "
            f"got {captured_max_output_tokens}. Output budget should be independent of input size.",
        )


if __name__ == "__main__":
    unittest.main()
