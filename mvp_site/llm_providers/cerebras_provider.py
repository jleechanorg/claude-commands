"""Cerebras direct API provider implementation.

Uses the Cerebras OpenAI-compatible chat completions endpoint to keep
llm_service orchestration provider-agnostic.

IMPORTANT: Uses json_schema with strict:true instead of legacy json_object
to prevent schema echo issues where API returns {"type": "object"} instead
of actual content.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from mvp_site import logging_util
from mvp_site.llm_providers.provider_utils import (
    ContextTooLargeError,
    check_context_too_large,
)

CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"


class CerebrasSchemaEchoError(Exception):
    """Raised when Cerebras API returns the response_format schema instead of content.

    This is a retriable error - the API echoed back the schema configuration
    instead of generating content.
    """

    pass


# NarrativeResponse JSON Schema for strict mode
# This schema enforces the structure that NarrativeResponse expects
NARRATIVE_RESPONSE_SCHEMA = {
    "name": "narrative_response",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "narrative": {
                "type": "string",
                "description": "The main narrative text describing what happens",
            },
            "planning_block": {
                "type": "string",
                "description": "Internal GM planning and analysis (shown to user)",
            },
            "entities_mentioned": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of entity names mentioned in the narrative",
            },
            "location_confirmed": {
                "type": "string",
                "description": "Current location name",
            },
            "session_header": {
                "type": "string",
                "description": "Session context header",
            },
            "dice_rolls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of dice roll results",
            },
            "resources": {
                "type": "string",
                "description": "Resource tracking information",
            },
        },
        "required": ["narrative", "planning_block", "entities_mentioned"],
        "additionalProperties": False,
    },
}


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
        pass
    return text, False


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
        # Use json_schema with strict:true instead of legacy json_object
        # This prevents schema echo issues where API returns {"type": "object"}
        "response_format": {
            "type": "json_schema",
            "json_schema": NARRATIVE_RESPONSE_SCHEMA,
        },
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
        choice = data["choices"][0]
        message = choice["message"]
        if not isinstance(message, dict):
            raise TypeError("message is not a dict")

        # Check for context-too-large scenario: finish_reason='length' with no content
        finish_reason = choice.get("finish_reason")
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        # Qwen 3 reasoning models may return content in 'content' or 'reasoning'
        lowered_keys = {str(key).lower(): key for key in message}
        content_key = lowered_keys.get("content")
        reasoning_key = lowered_keys.get("reasoning")

        text = None
        if content_key is not None:
            text = message[content_key]
        if text is None and reasoning_key is not None:
            text = message[reasoning_key]

        if text is None:
            # Check for context-too-large scenario using shared utility
            check_context_too_large(
                finish_reason=finish_reason,
                completion_tokens=completion_tokens,
                prompt_tokens=prompt_tokens,
                has_content=False,
            )
            raise KeyError("No 'content' or 'reasoning' field in message")

        # Check for schema echo (API returning config instead of content)
        if _is_schema_echo(text):
            logging_util.warning(
                "CEREBRAS_SCHEMA_ECHO: API returned schema config instead of content"
            )
            raise CerebrasSchemaEchoError(
                f"Cerebras API echoed schema config instead of content: {text[:100]}"
            )

        # Try to unwrap nested JSON wrapper pattern
        text, was_unwrapped = _unwrap_nested_json(text)
        if was_unwrapped:
            logging_util.info("CEREBRAS_WRAPPER_FIX: Unwrapped nested JSON wrapper in response")

    except ContextTooLargeError:
        raise  # Re-raise without wrapping for proper handling upstream
    except CerebrasSchemaEchoError:
        raise  # Re-raise schema echo for retry handling
    except Exception as exc:  # noqa: BLE001 - defensive parsing
        raise ValueError(f"Invalid Cerebras response structure: {data}") from exc

    return CerebrasResponse(text, data)
