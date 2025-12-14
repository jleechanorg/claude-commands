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

import requests

from mvp_site import logging_util
from mvp_site.game_state import execute_dice_tool
from mvp_site.llm_providers.provider_utils import (
    ContextTooLargeError,
    check_context_too_large,
    get_openai_json_schema_format,
)

CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"


class CerebrasSchemaEchoError(Exception):
    """Raised when Cerebras API returns the response_format schema instead of content.

    This is a retriable error - the API echoed back the schema configuration
    instead of generating content.
    """

    pass


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
        try:
            choices = self.raw_response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                tool_calls = message.get("tool_calls")
                return tool_calls if tool_calls else None
        except (AttributeError, IndexError, KeyError):
            return None
        return None

    @property
    def tool_calls(self) -> list[dict] | None:
        """Property accessor for tool_calls."""
        return self.get_tool_calls()


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
        messages = []
        if system_instruction_text:
            messages.append({"role": "system", "content": system_instruction_text})
        messages.append({"role": "user", "content": _stringify_parts(prompt_contents)})

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
        payload["tool_choice"] = "auto"
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

        # Check for tool_calls response - content may be null when tools are called
        has_tool_calls = "tool_calls" in message and message["tool_calls"]

        if text is None and not has_tool_calls:
            # Check for context-too-large scenario using shared utility
            check_context_too_large(
                finish_reason=finish_reason,
                completion_tokens=completion_tokens,
                prompt_tokens=prompt_tokens,
                has_content=False,
            )
            raise KeyError("No 'content' or 'reasoning' field in message")

        # If we have tool_calls but no text, use empty string (tool loop will handle)
        if text is None:
            text = ""
        else:
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


def execute_tool_requests(tool_requests: list[dict]) -> list[dict]:
    """Execute tool requests from JSON response and return results.

    Args:
        tool_requests: List of {"tool": "roll_dice", "args": {...}} dicts

    Returns:
        List of {"tool": str, "args": dict, "result": dict} with execution results
    """
    results = []
    for request in tool_requests:
        tool_name = request.get("tool", "")
        args = request.get("args", {})

        try:
            result = execute_dice_tool(tool_name, args)
        except Exception as e:
            logging_util.error(f"Tool execution error: {tool_name}: {e}")
            result = {"error": str(e)}

        results.append({
            "tool": tool_name,
            "args": args,
            "result": result,
        })

    return results


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
    # First call: JSON mode (no tools) - same as origin/main
    logging_util.info("Phase 1: JSON call (checking for tool_requests)")
    response = generate_content(
        prompt_contents=prompt_contents,
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        tools=None,  # No tools = JSON schema enforced
    )

    # Parse response to check for tool_requests
    try:
        response_data = json.loads(response.text) if response.text else {}
    except json.JSONDecodeError:
        logging_util.warning("Phase 1 response not valid JSON, returning as-is")
        return response

    tool_requests = response_data.get("tool_requests", [])
    if not tool_requests:
        logging_util.debug("No tool_requests in response, returning Phase 1 result")
        return response

    # Execute tool requests
    logging_util.info(f"Executing {len(tool_requests)} tool request(s)")
    tool_results = execute_tool_requests(tool_requests)

    # Build Phase 2 context with tool results
    tool_results_text = "\n".join([
        f"- {r['tool']}({r['args']}): {r['result']}"
        for r in tool_results
    ])

    # Build messages for Phase 2
    messages = []
    if system_instruction_text:
        messages.append({"role": "system", "content": system_instruction_text})
    messages.append({"role": "user", "content": _stringify_parts(prompt_contents)})
    messages.append({"role": "assistant", "content": response.text})
    messages.append({
        "role": "user",
        "content": f"Tool results (use these exact numbers in your narrative):\n{tool_results_text}\n\nNow write the final response using these results. Do NOT include tool_requests in your response."
    })

    # Phase 2: JSON call with tool results
    logging_util.info("Phase 2: JSON call with tool results")
    final_response = generate_content(
        prompt_contents=[],  # Not used when messages provided
        model_name=model_name,
        system_instruction_text=None,  # Already in messages
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        tools=None,  # No tools = JSON schema enforced
        messages=messages,
    )

    return final_response

