"""OpenRouter provider implementation for LLM interactions.

Uses json_schema (strict:false) for models that support it (e.g., Grok).
Other models fall back to json_object mode.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from mvp_site import logging_util
from mvp_site.llm_providers.provider_utils import get_openai_json_schema_format

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_SITE = "https://worldarchitect.ai"
DEFAULT_TITLE = "WorldArchitect.AI"

# Models that support json_schema with strict:false (dynamic choices)
# Other models ignore strict and fall back to best-effort JSON
MODELS_WITH_JSON_SCHEMA_SUPPORT = {
    "x-ai/grok-4.1-fast",  # xAI direct provider - enforces schema
    "x-ai/grok-4.1",  # Full Grok 4.1 also supports it
}


class OpenRouterResponse:
    """Simple response wrapper matching the .text interface used by llm_service."""

    def __init__(self, text: str, raw_response: Any = None):
        self.text = text
        self.raw_response = raw_response or {}

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
    """Generate JSON-oriented content using OpenRouter's chat API.

    Args:
        prompt_contents: List of prompt content parts
        model_name: Model name to use
        system_instruction_text: Optional system instruction
        temperature: Sampling temperature
        max_output_tokens: Maximum output tokens

    Raises:
        ValueError: If the API key is missing or the response is invalid.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: OPENROUTER_API_KEY environment variable not found!")

    user_message = _stringify_parts(prompt_contents)
    messages = []
    if system_instruction_text:
        messages.append({"role": "system", "content": system_instruction_text})
    messages.append({"role": "user", "content": user_message})

    # Use json_schema (strict:false) for models that support it
    # Other models fall back to json_object (best-effort JSON)
    if model_name in MODELS_WITH_JSON_SCHEMA_SUPPORT:
        response_format = get_openai_json_schema_format()
        logging_util.info(f"OpenRouter using json_schema (strict:false) for {model_name}")
    else:
        response_format = {"type": "json_object"}

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_output_tokens,
        "response_format": response_format,
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
        message = data["choices"][0]["message"]
        text = message.get("content") or ""
        if not text:
            raise KeyError("No content in message")
    except Exception as exc:  # noqa: BLE001 - defensive parsing
        raise ValueError(f"Invalid OpenRouter response structure: {data}") from exc

    return OpenRouterResponse(text, data)
