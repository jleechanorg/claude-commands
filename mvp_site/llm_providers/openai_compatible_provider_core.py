"""Shared core for OpenAI-compatible chat-completions providers.

This is the next layer above `openai_chat_common.py`.

Goal: keep each provider module focused on:
- endpoint + auth headers
- response_format choice (json_schema vs json_object)
- provider-specific postprocessing (if any)

Everything else (message building, payload shape, tool_calls detection, and
robust first-choice parsing) is centralized here.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mvp_site.llm_providers.openai_chat_common import (
    build_chat_payload,
    build_messages,
    extract_first_choice,
    extract_first_choice_message,
    extract_tool_calls,
    post_chat_completions,
)


def generate_openai_compatible_content(
    *,
    url: str,
    headers: dict[str, str],
    model_name: str,
    prompt_contents: list[Any],
    system_instruction_text: str | None,
    temperature: float,
    max_output_tokens: int,
    stringify_chat_parts_fn: Callable[[list[Any]], str],
    tools: list[dict] | None = None,
    messages: list[dict] | None = None,
    response_format: dict[str, Any] | None = None,
    tool_choice: str | None = None,
    timeout: int = 300,
    logger: Any | None = None,
    error_log_prefix: str = "",
    extract_text_from_message_fn: Callable[[dict[str, Any]], Any] | None = None,
    postprocess_text_fn: Callable[[Any], str] | None = None,
    validate_response_fn: Callable[
        [dict[str, Any], dict[str, Any], Any, list[dict] | None], None
    ]
    | None = None,
) -> tuple[str, dict[str, Any]]:
    """Call an OpenAI-compatible chat-completions endpoint and return (text, raw_json)."""
    # Use provided messages or build from prompt_contents.
    if messages is None:
        messages = build_messages(
            prompt_contents=prompt_contents,
            system_instruction_text=system_instruction_text,
            stringify_chat_parts_fn=stringify_chat_parts_fn,
        )

    payload = build_chat_payload(
        model_name=model_name,
        messages=messages,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        tools=tools,
        tool_choice=tool_choice if tools else None,
        response_format=response_format,
    )

    data = post_chat_completions(
        url=url,
        headers=headers,
        payload=payload,
        timeout=timeout,
        logger=logger,
        error_log_prefix=error_log_prefix,
    )

    _choice = extract_first_choice(data)
    message = extract_first_choice_message(data)
    raw_text: Any
    if extract_text_from_message_fn is None:
        raw_text = message.get("content") if isinstance(message, dict) else None
    else:
        raw_text = extract_text_from_message_fn(message)

    # Accept content-less responses only if tool_calls exist.
    tool_calls = extract_tool_calls(data)
    if validate_response_fn is not None:
        validate_response_fn(data, message, raw_text, tool_calls)
    elif raw_text is None and not tool_calls:
        raise ValueError("No content and no tool_calls in response message")

    if postprocess_text_fn is None:
        text = "" if raw_text is None else str(raw_text)
    else:
        text = postprocess_text_fn(raw_text)

    return text, data
