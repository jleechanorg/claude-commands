"""Cerebras direct API provider implementation.

Uses the Cerebras OpenAI-compatible chat completions endpoint to keep
llm_service orchestration provider-agnostic.

IMPORTANT: Uses json_schema (strict:false) instead of legacy json_object
to prevent schema echo issues where API returns {"type": "object"} instead
of actual content. strict:false keeps planning_block flexible for dynamic
choice keys.
"""

from __future__ import annotations

import json
import os
from typing import Any

from mvp_site import logging_util
from mvp_site.game_state import (
    DICE_ROLL_TOOLS,
    execute_dice_tool,
    execute_tool_requests,
    format_tool_results_text,
)
from mvp_site.llm_providers.provider_utils import (
    ContextTooLargeError,
    check_context_too_large,
    get_openai_json_schema_format,
    run_openai_json_first_tool_requests_flow,
    run_openai_native_two_phase_flow,
    stringify_chat_parts,
)
from mvp_site.llm_providers.openai_chat_common import (
    build_messages as build_openai_messages,
    extract_tool_calls as extract_openai_tool_calls,
    post_chat_completions,
)

CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"


class CerebrasSchemaEchoError(Exception):
    """Raised when Cerebras API returns the response_format schema instead of content.

    This is a retriable error - the API echoed back the schema configuration
    instead of generating content.
    """

    # Docstring-only exception.


def _extract_text_from_message(message: dict[str, Any]) -> Any:
    """Extract content text from a message, tolerating model-specific keys."""
    lowered_keys = {str(key).lower(): key for key in message}
    for preferred in ("content", "reasoning"):
        actual = lowered_keys.get(preferred)
        if actual is not None:
            return message.get(actual)
    return None


def _validate_has_content_or_tool_calls(
    *,
    text: Any,
    has_tool_calls: bool,
    finish_reason: str | None,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    if text is None and not has_tool_calls:
        check_context_too_large(
            finish_reason=finish_reason,
            completion_tokens=completion_tokens,
            prompt_tokens=prompt_tokens,
            has_content=False,
        )
        raise KeyError("No 'content' or 'reasoning' field in message")


def _postprocess_response_text(text: Any) -> str:
    """Normalize a successful content payload into a text string."""
    if text is None:
        return ""

    # Some models can return non-string content; coerce defensively.
    text_str = str(text)

    if _is_schema_echo(text_str):
        logging_util.warning(
            "CEREBRAS_SCHEMA_ECHO: API returned schema config instead of content"
        )
        raise CerebrasSchemaEchoError(
            f"Cerebras API echoed schema config instead of content: {text_str[:100]}"
        )

    unwrapped, was_unwrapped = _unwrap_nested_json(text_str)
    if was_unwrapped:
        logging_util.info("CEREBRAS_WRAPPER_FIX: Unwrapped nested JSON wrapper in response")
    return unwrapped


def _is_schema_echo(text: str) -> bool:
    """Check if response is a schema echo (API returning config instead of content)."""
    if not text:
        return False
    stripped = text.strip()
    # Known schema echo patterns
    schema_echo_patterns = [
        '{"type": "object"}',
        '{"type":"object"}',
        '{ "type": "object" }',
        '{"type": "json_object"}',
        '{"type":"json_object"}',
    ]
    if stripped in schema_echo_patterns:
        return True
    # Also check for minimal object with only "type" key
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict) and list(parsed.keys()) == ["type"]:
            return True
    except json.JSONDecodeError:
        # Not valid JSON, so can't be a schema echo
        pass
    return False


def _unwrap_nested_json(text: str) -> tuple[str, bool]:
    """Unwrap nested JSON wrapper pattern from Cerebras API.

    Cerebras sometimes wraps actual content in: {"type": "object", "json": {...actual...}}

    Returns:
        tuple: (unwrapped_content, was_unwrapped)
    """
    if not text:
        return text, False
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, dict):
            # Check for nested "json" key with actual content
            for key in ("json", "response", "content"):
                if key in parsed and isinstance(parsed[key], dict):
                    inner = parsed[key]
                    if "narrative" in inner or "entities_mentioned" in inner:
                        logging_util.info(
                            f"CEREBRAS_WRAPPER_UNWRAP: Extracted content from nested '{key}' wrapper"
                        )
                        return json.dumps(inner), True
    except json.JSONDecodeError:
        # If parsing fails, return the original text and indicate no unwrapping occurred
        pass
    return text, False


class CerebrasResponse:
    """Wrapper exposing a `.text` attribute for downstream parsing."""

    def __init__(self, text: str, raw_response: Any):
        self.text = text
        self.raw_response = raw_response

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"CerebrasResponse(text_length={len(self.text)})"

    def get_tool_calls(self) -> list[dict] | None:
        """Extract tool_calls from the raw response if present."""
        return extract_openai_tool_calls(self.raw_response)

    @property
    def tool_calls(self) -> list[dict] | None:
        """Property accessor for tool_calls."""
        return self.get_tool_calls()


def generate_content(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    max_output_tokens: int,
    tools: list[dict] | None = None,
    messages: list[dict] | None = None,
) -> CerebrasResponse:
    """Call the Cerebras chat completions API.

    Args:
        prompt_contents: List of prompt content parts
        model_name: Model name to use
        system_instruction_text: Optional system instruction
        temperature: Sampling temperature
        max_output_tokens: Maximum output tokens
        tools: Optional list of tool definitions for function calling
        messages: Optional pre-built messages list (for tool loop continuation)

    Raises:
        ValueError: If the API key is missing or the response is invalid.
    """

    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: CEREBRAS_API_KEY environment variable not found!")

    # Use provided messages or build from prompt_contents
    if messages is None:
        messages = build_openai_messages(
            prompt_contents=prompt_contents,
            system_instruction_text=system_instruction_text,
            stringify_chat_parts_fn=stringify_chat_parts,
        )

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_output_tokens,
    }

    # Add tools if provided (for function calling)
    # NOTE: Cerebras API does NOT support tools + response_format together
    # When using tools, JSON output is handled by prompt instructions
    if tools:
        payload["tools"] = tools
        # Force tool use: game rules require dice for combat, skill checks, saves
        # With "required", the LLM MUST call at least one tool
        payload["tool_choice"] = "required"
        # DO NOT set response_format - API rejects tools + response_format
    else:
        # Only use JSON schema format when NOT using tools
        payload["response_format"] = get_openai_json_schema_format()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    logging_util.info(
        f"CEREBRAS REQUEST model={model_name} max_tokens={max_output_tokens}"
    )
    data = post_chat_completions(
        url=CEREBRAS_URL,
        headers=headers,
        payload=payload,
        timeout=300,
        logger=logging_util,
        error_log_prefix="CEREBRAS",
    )

    try:
        choice = data["choices"][0]
        message = choice["message"]
        if not isinstance(message, dict):
            raise TypeError("message is not a dict")

        finish_reason = choice.get("finish_reason")
        usage = data.get("usage", {}) or {}
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        text = _extract_text_from_message(message)
        has_tool_calls = bool(extract_openai_tool_calls(data))
        _validate_has_content_or_tool_calls(
            text=text,
            has_tool_calls=has_tool_calls,
            finish_reason=finish_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        text = _postprocess_response_text(text)
    except ContextTooLargeError:
        raise  # Re-raise without wrapping for proper handling upstream
    except CerebrasSchemaEchoError:
        raise  # Re-raise schema echo for retry handling
    except Exception as exc:  # noqa: BLE001 - defensive parsing
        raise ValueError(f"Invalid Cerebras response structure: {data}") from exc

    return CerebrasResponse(text, data)


def generate_content_with_tool_requests(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    max_output_tokens: int,
) -> CerebrasResponse:
    """Generate content with JSON-first tool request flow.

    This is the preferred flow that keeps JSON schema enforcement throughout:
    1. First call: JSON mode with response_format (like origin/main)
       - LLM can include tool_requests array if it needs dice/skills
    2. If tool_requests present: Execute tools, inject results, second JSON call
    3. If no tool_requests: Return first response as-is

    This avoids the API limitation where tools + response_format cannot be used together.

    Args:
        prompt_contents: List of prompt content parts
        model_name: Model name to use
        system_instruction_text: Optional system instruction
        temperature: Sampling temperature
        max_output_tokens: Maximum output tokens

    Returns:
        Final CerebrasResponse with complete JSON
    """
    return run_openai_json_first_tool_requests_flow(
        generate_content_fn=generate_content,
        prompt_contents=prompt_contents,
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        provider_no_tool_requests_log_prefix="CEREBRAS_TOOL_REQUESTS",
        execute_tool_requests_fn=execute_tool_requests,
        format_tool_results_text_fn=format_tool_results_text,
        logger=logging_util,
    )


def generate_content_with_native_tools(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    max_output_tokens: int,
) -> CerebrasResponse:
    """Generate content with native two-phase tool calling.

    This flow uses the native API tool calling that ALL models support:
    1. Phase 1: `tools` parameter (no response_format) → model returns `tool_calls`
    2. Execute tools locally (roll_dice, roll_attack, etc.)
    3. Phase 2: `response_format` parameter (no tools) → structured JSON with results

    This approach works for GLM-4.6 and other models that ignore prompt-based
    tool_requests but properly support native API tool calling.

    Args:
        prompt_contents: List of prompt content parts
        model_name: Model name to use
        system_instruction_text: Optional system instruction
        temperature: Sampling temperature
        max_output_tokens: Maximum output tokens

    Returns:
        Final CerebrasResponse with structured JSON
    """
    return run_openai_native_two_phase_flow(
        generate_content_fn=generate_content,
        prompt_contents=prompt_contents,
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        dice_roll_tools=DICE_ROLL_TOOLS,
        execute_tool_fn=execute_dice_tool,
        logger=logging_util,
    )
