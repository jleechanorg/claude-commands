from unittest.mock import patch, MagicMock

import mvp_site.llm_service as llm_service
from mvp_site import constants
from mvp_site.llm_providers import gemini_provider


def test_safe_output_limit_uses_model_context_window():
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

    assert (
        llm_service._get_safe_output_token_limit(
            constants.LLM_PROVIDER_GEMINI,
            constants.DEFAULT_GEMINI_MODEL,
            prompt_tokens,
            system_tokens,
        )
        == expected
    )


def test_safe_output_limit_high_input_does_not_starve_output():
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
        constants.LLM_PROVIDER_GEMINI,
        constants.DEFAULT_GEMINI_MODEL,
        prompt_tokens,
        system_tokens,
    )

    # Output should be at least OUTPUT_TOKEN_RESERVE_MIN since we have headroom
    assert output_limit >= llm_service.OUTPUT_TOKEN_RESERVE_MIN, (
        f"Output starved to {output_limit} tokens! "
        f"Should be at least {llm_service.OUTPUT_TOKEN_RESERVE_MIN}"
    )


def test_safe_output_limit_context_exceeded_avoids_overflow():
    """
    Edge case: When input exceeds safe context, return 1 to avoid API overflow.

    If input is 901K tokens and safe_context is 900K, we should NOT request 1024
    output tokens as that would overflow the context window. Return 1 instead.
    """
    # Gemini safe context = 1M * 0.9 = 900K tokens
    # Simulate input exceeding safe context
    model_context = constants.MODEL_CONTEXT_WINDOW_TOKENS.get(
        constants.DEFAULT_GEMINI_MODEL, constants.DEFAULT_CONTEXT_WINDOW_TOKENS
    )
    safe_context = int(model_context * constants.CONTEXT_WINDOW_SAFETY_RATIO)

    # Input exceeds safe context by 1K tokens
    prompt_tokens = safe_context + 1_000
    system_tokens = 0

    output_limit = llm_service._get_safe_output_token_limit(
        constants.LLM_PROVIDER_GEMINI,
        constants.DEFAULT_GEMINI_MODEL,
        prompt_tokens,
        system_tokens,
    )

    # Should return 1 (minimal) to avoid overflow, NOT 1024
    assert output_limit == 1, (
        f"Expected output limit of 1 when context exceeded, got {output_limit}. "
        f"Requesting {output_limit} tokens would overflow the context window!"
    )


def test_output_budget_independent_of_input_size():
    """
    Output token budget should be independent of input token size.

    Principle: The output budget should hit JSON_MODE_MAX_OUTPUT_TOKENS cap
    regardless of whether input is 1K, 100K, or 500K tokens - as long as we're
    within model context limits.

    This ensures consistent generation quality regardless of conversation length.
    """
    # Test various input sizes - all should get the same output budget
    input_sizes = [
        (1_000, 500),       # Small: 1.5K tokens
        (50_000, 10_000),   # Medium: 60K tokens
        (200_000, 50_000),  # Large: 250K tokens
        (400_000, 100_000), # Very large: 500K tokens (still within 1M context)
    ]

    output_budgets = []
    for prompt_tokens, system_tokens in input_sizes:
        output_limit = llm_service._get_safe_output_token_limit(
            constants.LLM_PROVIDER_GEMINI,
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
        assert budget == expected_cap, (
            f"Input size {total_input:,} got output budget {budget:,}, "
            f"expected {expected_cap:,}. Output should be independent of input size!"
        )


def test_safe_output_limit_respects_context_budget_for_llama():
    prompt_tokens = 20_000
    system_tokens = 5_000

    safe_budget = int(
        constants.MODEL_CONTEXT_WINDOW_TOKENS["llama-3.3-70b"]
        * constants.CONTEXT_WINDOW_SAFETY_RATIO
    )
    # Use OUTPUT_TOKEN_RESERVE_MIN as minimum, not 1
    expected_remaining = max(
        llm_service.OUTPUT_TOKEN_RESERVE_MIN, safe_budget - (prompt_tokens + system_tokens)
    )
    model_cap = constants.MODEL_MAX_OUTPUT_TOKENS.get(
        "llama-3.3-70b", llm_service.JSON_MODE_MAX_OUTPUT_TOKENS
    )
    expected = min(llm_service.JSON_MODE_MAX_OUTPUT_TOKENS, model_cap, expected_remaining)

    assert (
        llm_service._get_safe_output_token_limit(
            constants.LLM_PROVIDER_CEREBRAS,  # Updated: test with Cerebras provider
            "llama-3.3-70b",  # Updated: 3.1-70b retired from Cerebras
            prompt_tokens,
            system_tokens,
        )
        == expected
    )


def test_calculate_tokens_cerebras_uses_estimate_not_gemini_api():
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
    with patch("mvp_site.llm_service.gemini_provider.count_tokens") as mock_gemini_count:
        mock_gemini_count.side_effect = Exception(
            "FAIL: gemini_provider.count_tokens() should NOT be called for Cerebras provider!"
        )

        # This should NOT raise an exception - it should use estimate_tokens() instead
        prompt_tokens, system_tokens = llm_service._calculate_prompt_and_system_tokens(
            user_prompt_contents, system_instruction, provider_name, model_name
        )

        # Verify gemini API was NOT called
        mock_gemini_count.assert_not_called()

        # Verify we got reasonable token estimates
        assert prompt_tokens > 0, f"Expected positive prompt_tokens, got {prompt_tokens}"
        assert system_tokens > 0, f"Expected positive system_tokens, got {system_tokens}"


def test_calculate_tokens_openrouter_uses_estimate_not_gemini_api():
    """Verify OpenRouter provider also uses estimate_tokens() instead of Gemini API."""
    user_prompt_contents = ["Test OpenRouter prompt"]
    system_instruction = "System instruction for OpenRouter"
    provider_name = constants.LLM_PROVIDER_OPENROUTER
    model_name = "anthropic/claude-3-opus"  # An OpenRouter model

    with patch("mvp_site.llm_service.gemini_provider.count_tokens") as mock_gemini_count:
        mock_gemini_count.side_effect = Exception(
            "FAIL: gemini_provider.count_tokens() should NOT be called for OpenRouter provider!"
        )

        prompt_tokens, system_tokens = llm_service._calculate_prompt_and_system_tokens(
            user_prompt_contents, system_instruction, provider_name, model_name
        )

        mock_gemini_count.assert_not_called()
        assert prompt_tokens > 0
        assert system_tokens > 0


def test_calculate_tokens_gemini_uses_gemini_api():
    """Verify Gemini provider DOES use the Gemini API for token counting."""
    user_prompt_contents = ["Test Gemini prompt"]
    system_instruction = "System instruction for Gemini"
    provider_name = constants.LLM_PROVIDER_GEMINI
    model_name = constants.DEFAULT_GEMINI_MODEL

    with patch("mvp_site.llm_service.gemini_provider.count_tokens") as mock_gemini_count:
        mock_gemini_count.return_value = 100  # Return mock token count

        prompt_tokens, system_tokens = llm_service._calculate_prompt_and_system_tokens(
            user_prompt_contents, system_instruction, provider_name, model_name
        )

        # Gemini provider SHOULD call the Gemini API
        assert mock_gemini_count.call_count >= 1, "Gemini provider should use gemini_provider.count_tokens()"


def test_e2e_large_context_does_not_starve_output_tokens():
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
    # Capture what max_output_tokens is actually passed to the provider
    captured_max_output_tokens = None

    def mock_generate_json_mode_content(**kwargs):
        nonlocal captured_max_output_tokens
        captured_max_output_tokens = kwargs.get("max_output_tokens")
        # Return a mock response object
        mock_response = MagicMock()
        mock_response.text = '{"narrative": "Test response"}'
        return mock_response

    # Simulate 305K input tokens (exceeds old 300K compaction limit)
    def mock_count_tokens(model_name, contents):
        # Return large token count to simulate the bug scenario
        return 300_000  # 300K tokens for prompt

    with patch.object(
        gemini_provider, "count_tokens", side_effect=mock_count_tokens
    ), patch.object(
        gemini_provider, "generate_json_mode_content", side_effect=mock_generate_json_mode_content
    ):
        # Call the full LLM service flow
        llm_service._call_llm_api_with_model_cycling(
            prompt_contents=["Large prompt content..."],
            model_name=constants.DEFAULT_GEMINI_MODEL,
            current_prompt_text_for_logging="Test large context",
            system_instruction_text="System instruction (5K tokens simulated)",
            provider_name=constants.LLM_PROVIDER_GEMINI,
        )

    # Verify output tokens were NOT starved
    assert captured_max_output_tokens is not None, "max_output_tokens was not passed to provider"
    assert captured_max_output_tokens >= llm_service.OUTPUT_TOKEN_RESERVE_MIN, (
        f"OUTPUT STARVATION BUG: max_output_tokens={captured_max_output_tokens} "
        f"but should be at least {llm_service.OUTPUT_TOKEN_RESERVE_MIN}. "
        f"This means the 305K input context starved the output budget!"
    )
    # With the fix, we should get a healthy output budget (close to JSON_MODE_MAX_OUTPUT_TOKENS)
    # since 305K input is well within the 1M model context
    assert captured_max_output_tokens == llm_service.JSON_MODE_MAX_OUTPUT_TOKENS, (
        f"Expected max_output_tokens={llm_service.JSON_MODE_MAX_OUTPUT_TOKENS} (capped by JSON limit), "
        f"got {captured_max_output_tokens}. Output budget should be independent of input size."
    )
