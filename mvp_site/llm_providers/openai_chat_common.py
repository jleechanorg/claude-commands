"""Shared helpers for OpenAI-compatible chat-completions providers.

This repo talks to multiple providers (Cerebras, OpenRouter, etc.) via
OpenAI-compatible /chat/completions semantics. While endpoints and feature
support differ, the *wire shape* for choices/message/tool_calls is shared.

This module centralizes the small-but-duplicated glue:
- building system+user messages from prompt contents
- extracting tool_calls from raw responses defensively
- posting JSON requests with consistent error handling
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import requests


@dataclass(frozen=True)
class OpenAIChatResponse:
    """Minimal response wrapper with `.text` + `.tool_calls` used by llm_service."""

    text: str
    raw_response: Any

    @property
    def tool_calls(self) -> list[dict] | None:
        return extract_tool_calls(self.raw_response)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"{self.__class__.__name__}(text_length={len(self.text)})"


def build_messages(
    *,
    prompt_contents: list[Any],
    system_instruction_text: str | None,
    stringify_chat_parts_fn: Callable[[list[Any]], str],
) -> list[dict[str, Any]]:
    """Build OpenAI-style messages for a single-turn request."""
    messages: list[dict[str, Any]] = []
    if system_instruction_text:
        messages.append({"role": "system", "content": system_instruction_text})
    messages.append({"role": "user", "content": stringify_chat_parts_fn(prompt_contents)})
    return messages


def extract_tool_calls(raw_response: Any) -> list[dict] | None:
    """Extract `tool_calls` from an OpenAI-compatible chat-completions response."""
    try:
        if not isinstance(raw_response, dict):
            return None
        choices = raw_response.get("choices", [])
        if not choices:
            return None
        first = choices[0]
        if not isinstance(first, dict):
            return None
        message = first.get("message", {}) or {}
        if not isinstance(message, dict):
            return None
        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return None
        return tool_calls
    except (AttributeError, IndexError, KeyError, TypeError):
        return None


def post_chat_completions(
    *,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int = 300,
    logger: Any | None = None,
    error_log_prefix: str = "",
) -> dict[str, Any]:
    """POST to an OpenAI-compatible chat completions endpoint and return JSON."""
    response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if logger is not None and not response.ok:
        prefix = f"{error_log_prefix} " if error_log_prefix else ""
        try:
            logger.error(f"{prefix}ERROR {response.status_code}: {response.text[:500]}")
        except Exception:  # noqa: BLE001 - logging must never crash
            pass
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Invalid response JSON: expected dict")
    return data

