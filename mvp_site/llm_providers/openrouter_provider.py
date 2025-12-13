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
    tools: list[dict] | None = None,
    messages: list[dict] | None = None,
) -> OpenRouterResponse:
    """Generate JSON-oriented content using OpenRouter's chat API.

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
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: OPENROUTER_API_KEY environment variable not found!")

    # Use provided messages or build from prompt_contents
    if messages is None:
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

    # Add tools if provided (for function calling)
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

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
        # Check for tool_calls - content may be null
        has_tool_calls = "tool_calls" in message and message["tool_calls"]
        if not text and not has_tool_calls:
            raise KeyError("No content or tool_calls in message")
    except Exception as exc:  # noqa: BLE001 - defensive parsing
        raise ValueError(f"Invalid OpenRouter response structure: {data}") from exc

    return OpenRouterResponse(text, data)


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
) -> OpenRouterResponse:
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
        Final OpenRouterResponse with complete text
    """
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    # Build initial messages
    messages = []
    if system_instruction_text:
        messages.append({"role": "system", "content": system_instruction_text})
    messages.append({"role": "user", "content": _stringify_parts(prompt_contents)})

    iteration = 0
    response = None  # Initialize for the return at the end
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

    # Max iterations reached - make one final call WITHOUT tools to force text generation
    logging_util.warning(
        f"Tool loop reached max iterations ({max_iterations}), forcing final response without tools"
    )

    # If the last response still has tool_calls but no text, we need to force text generation
    # by making one more API call without the tools parameter
    if response.text == "" and response.get_tool_calls():
        logging_util.info("Forcing final text generation (no tools)")
        # Get the raw message to add to conversation
        raw_message = response.raw_response.get("choices", [{}])[0].get("message", {})
        messages.append({
            "role": "assistant",
            "content": raw_message.get("content"),
            "tool_calls": response.get_tool_calls(),
        })
        # Execute the pending tools
        tool_results = process_tool_calls(response.get_tool_calls())
        for result in tool_results:
            messages.append({
                "role": "tool",
                "tool_call_id": result["tool_call_id"],
                "name": result["name"],
                "content": result["content"],
            })
        # Final call WITHOUT tools to force text generation
        response = generate_content(
            prompt_contents=[],
            model_name=model_name,
            system_instruction_text=None,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            tools=None,  # No tools - force text response
            messages=messages,
        )

    return response


def execute_tool_requests(tool_requests: list[dict]) -> list[dict]:
    """Execute tool requests from JSON response and return results.

    Args:
        tool_requests: List of {"tool": "roll_dice", "args": {...}} dicts

    Returns:
        List of {"tool": str, "args": dict, "result": dict} with execution results
    """
    from mvp_site.game_state import execute_dice_tool

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
) -> OpenRouterResponse:
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
        Final OpenRouterResponse with complete JSON
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