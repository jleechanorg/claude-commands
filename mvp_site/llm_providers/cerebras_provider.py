"""Cerebras direct API provider implementation.

Uses the Cerebras OpenAI-compatible chat completions endpoint to keep
llm_service orchestration provider-agnostic.
"""
from __future__ import annotations

import json
import os
from typing import Any

import requests

from mvp_site import logging_util

CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"


class CerebrasResponse:
    """Wrapper exposing a `.text` attribute for downstream parsing."""

    def __init__(self, text: str, raw_response: Any):
        self.text = text
        self.raw_response = raw_response

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"CerebrasResponse(text_length={len(self.text)})"


def _stringify_parts(parts: list[Any]) -> str:
    """Render prompt parts consistently for Cerebras/OpenAI-chat style APIs."""

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


def generate_content(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    max_output_tokens: int,
) -> CerebrasResponse:
    """Call the Cerebras chat completions API.

    Raises:
        ValueError: If the API key is missing or the response is invalid.
    """

    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: CEREBRAS_API_KEY environment variable not found!")

    messages = []
    if system_instruction_text:
        messages.append({"role": "system", "content": system_instruction_text})
    messages.append({"role": "user", "content": _stringify_parts(prompt_contents)})

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_output_tokens,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    logging_util.info(
        f"CEREBRAS REQUEST model={model_name} max_tokens={max_output_tokens}"
    )
    response = requests.post(CEREBRAS_URL, headers=headers, json=payload, timeout=300)

    if not response.ok:
        logging_util.error(
            f"CEREBRAS ERROR {response.status_code}: {response.text[:500]}"
        )
    response.raise_for_status()
    data = response.json()

    try:
        text = data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001 - defensive parsing
        raise ValueError(f"Invalid Cerebras response structure: {data}") from exc

    return CerebrasResponse(text, data)
