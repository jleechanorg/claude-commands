"""Cerebras direct API provider implementation.

Uses the Cerebras OpenAI-compatible chat completions endpoint to keep
llm_service orchestration provider-agnostic.

Supports tool use (function calling) for dice rolling when code_execution
is not available. Uses two-stage inference: LLM requests tool -> execute locally
-> send result back -> LLM generates final response.

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
    """Wrapper exposing a `.text` attribute for downstream parsing.

    Also exposes tool_calls for function calling support.
    """

    def __init__(self, text: str, raw_response: Any):
        self.text = text
        self.raw_response = raw_response
        # Extract tool_calls from response if present
        self._tool_calls: list[dict] | None = None
        self._finish_reason: str | None = None
        try:
            choice = raw_response.get("choices", [{}])[0]
            message = choice.get("message", {})
            self._tool_calls = message.get("tool_calls")
            self._finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError):
            pass

    @property
    def tool_calls(self) -> list[dict] | None:
        """Return tool_calls if the LLM requested function calls."""
        return self._tool_calls

    @property
    def finish_reason(self) -> str | None:
        """Return the finish_reason from the response."""
        return self._finish_reason

    def get_tool_calls(self) -> list[dict]:
        """Return tool_calls as a list (empty if none)."""
        return self._tool_calls or []

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"CerebrasResponse(text_length={len(self.text)}, tool_calls={len(self._tool_calls or [])})"


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
        # Use json_schema with strict:false instead of legacy json_object
        # This prevents schema echo issues where API returns {"type": "object"}
        "response_format": get_openai_json_schema_format(),
    }

    # Add tools if provided (for function calling)
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

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


def process_tool_calls(tool_calls: list[dict]) -> list[dict]:
    """Execute tool calls and return results.

    Args:
        tool_calls: List of tool call dicts from the LLM response

    Returns:
        List of tool results in OpenAI-compatible format
    """
    # Import here to avoid circular imports
    from mvp_site.game_state import execute_dice_tool

    results = []
    for tool_call in tool_calls:
        tool_id = tool_call.get("id", "")
        function_info = tool_call.get("function", {})
        tool_name = function_info.get("name", "")
        arguments_str = function_info.get("arguments", "{}")

        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError:
            arguments = {}

        logging_util.info(f"Executing tool: {tool_name} with args: {arguments}")

        try:
            result = execute_dice_tool(tool_name, arguments)
            result_str = json.dumps(result)
        except Exception as e:
            logging_util.error(f"Tool execution error: {tool_name}: {e}")
            result = {"error": str(e)}
            result_str = json.dumps(result)

        results.append({
            "tool_call_id": tool_id,
            "role": "tool",
            "name": tool_name,
            "content": result_str,
            "result": result,
        })

    return results


def generate_content_with_tool_loop(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    max_output_tokens: int,
    tools: list[dict],
    max_iterations: int = 5,
) -> CerebrasResponse:
    """Generate content with automatic tool call handling.

    Uses two-stage inference:
    1. LLM generates response (may include tool_calls)
    2. If tool_calls present, execute tools and send results back
    3. LLM generates final response with tool results

    Args:
        prompt_contents: List of prompt content parts
        model_name: Model name to use
        system_instruction_text: Optional system instruction
        temperature: Sampling temperature
        max_output_tokens: Maximum output tokens
        tools: List of tool definitions for function calling
        max_iterations: Maximum tool call iterations (prevent infinite loops)

    Returns:
        Final CerebrasResponse with complete text
    """
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    # Build initial messages
    messages = []
    if system_instruction_text:
        messages.append({"role": "system", "content": system_instruction_text})
    messages.append({"role": "user", "content": _stringify_parts(prompt_contents)})

    iteration = 0
    while iteration < max_iterations:
        iteration += 1

        # Call API with current messages
        response = generate_content(
            prompt_contents=[],  # Not used when messages provided
            model_name=model_name,
            system_instruction_text=None,  # Already in messages
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            tools=tools,
            messages=messages,
        )

        # Check if we have tool calls
        tool_calls = response.get_tool_calls()
        if not tool_calls:
            # No more tool calls - return final response
            logging_util.debug(
                f"Tool loop complete after {iteration} iteration(s)"
            )
            return response

        logging_util.info(f"Processing {len(tool_calls)} tool call(s), iteration {iteration}")

        # Get the raw message from response to add to conversation
        raw_message = response.raw_response.get("choices", [{}])[0].get("message", {})

        # Add assistant message with tool_calls to conversation
        messages.append({
            "role": "assistant",
            "content": raw_message.get("content"),
            "tool_calls": tool_calls,
        })

        # Execute tools and add results to conversation
        tool_results = process_tool_calls(tool_calls)
        for result in tool_results:
            messages.append({
                "role": "tool",
                "tool_call_id": result["tool_call_id"],
                "name": result["name"],
                "content": result["content"],
            })

    # Max iterations reached
    logging_util.warning(
        f"Tool loop reached max iterations ({max_iterations}), returning last response"
    )
    return response
