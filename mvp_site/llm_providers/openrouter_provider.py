"""OpenRouter provider implementation for LLM interactions."""

from __future__ import annotations

import os
from typing import Any

import requests

from mvp_site import logging_util

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_SITE = "https://worldarchitect.ai"
DEFAULT_TITLE = "WorldArchitect.AI"


class OpenRouterResponse:
    """Simple response wrapper matching the .text interface used by llm_service."""

    def __init__(self, text: str):
        self.text = text

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"OpenRouterResponse(text_length={len(self.text)})"


def _stringify_parts(parts: list[Any]) -> str:
    """Render prompt parts consistently for chat-style payloads."""

    rendered: list[str] = []
    for part in parts:
        if isinstance(part, str):
            rendered.append(part)
        else:
            try:
                rendered.append(json.dumps(part))
            except Exception:  # noqa: BLE001 - defensive stringify
                rendered.append(str(part))
    return "\n\n".join(rendered)


def _build_headers(api_key: str) -> dict[str, str]:
    site_url = os.environ.get("OPENROUTER_SITE_URL", DEFAULT_SITE)
    title = os.environ.get("OPENROUTER_APP_TITLE", DEFAULT_TITLE)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": site_url,
        "X-Title": title,
    }


def generate_content(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    max_output_tokens: int,
) -> OpenRouterResponse:
    """Generate JSON-oriented content using OpenRouter's chat API."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: OPENROUTER_API_KEY environment variable not found!")

    # OpenRouter expects chat-style messages. Consolidate prompt contents into a single user message
    user_message = _stringify_parts(prompt_contents)

    messages = []
    if system_instruction_text:
        messages.append({"role": "system", "content": system_instruction_text})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_output_tokens,
        "response_format": {"type": "json_object"},
    }

    logging_util.info(f"Calling OpenRouter model: {model_name}")
    response = requests.post(
        OPENROUTER_URL,
        json=payload,
        headers=_build_headers(api_key),
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()

    try:
        text = data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001 - defensive parsing
        raise ValueError(f"Invalid OpenRouter response structure: {data}") from exc

    return OpenRouterResponse(text)
