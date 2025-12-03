from unittest.mock import patch

import pytest

from mvp_site import constants, llm_service
from mvp_site.llm_providers.provider_utils import ContextTooLargeError


def test_model_call_surfaces_context_too_large_error():
    context_error = ContextTooLargeError(
        "Context exceeded",
        prompt_tokens=400_000,
        completion_tokens=0,
        finish_reason="context_exceeded",
    )

    with patch(
        "mvp_site.llm_service._calculate_prompt_and_system_tokens",
        return_value=(1, 1),
    ), patch("mvp_site.llm_service._log_token_count"), patch(
        "mvp_site.llm_service._get_safe_output_token_limit", side_effect=context_error
    ), pytest.raises(llm_service.LLMRequestError) as exc_info:
        llm_service._call_llm_api(["prompt"], "model")

    assert exc_info.value.status_code == 422
    assert "context" in str(exc_info.value).lower()


def test_model_call_surfaces_provider_overload_without_retry():
    overload_error = Exception("503 UNAVAILABLE: overloaded")

    with patch(
        "mvp_site.llm_service._calculate_prompt_and_system_tokens",
        return_value=(10, 0),
    ), patch("mvp_site.llm_service._log_token_count"), patch(
        "mvp_site.llm_service._get_safe_output_token_limit", return_value=100
    ), patch(
        "mvp_site.llm_service.gemini_provider.generate_json_mode_content",
        side_effect=overload_error,
    ) as mock_generate, pytest.raises(llm_service.LLMRequestError) as exc_info:
        llm_service._call_llm_api(
            ["prompt"], "model", provider_name=constants.LLM_PROVIDER_GEMINI
        )

    assert exc_info.value.status_code == 503
    mock_generate.assert_called_once()
