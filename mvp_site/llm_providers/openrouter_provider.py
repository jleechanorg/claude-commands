"""OpenRouter provider implementation for LLM interactions.

Uses json_schema (strict:false) for models that support it (e.g., Grok).
Other models fall back to json_object mode.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from mvp_site import logging_util
from mvp_site.game_state import (
    DICE_ROLL_TOOLS,
    execute_dice_tool,
    execute_tool_requests,
    format_tool_results_text,
)
from mvp_site.llm_providers.provider_utils import (
    get_openai_json_schema_format,
    run_openai_json_first_tool_requests_flow,
    run_openai_native_two_phase_flow,
    stringify_chat_parts,
)

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
        user_message = stringify_chat_parts(prompt_contents)
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
    }

    # Add tools OR response_format (NOT both - API limitation)
    # When tools are provided, JSON output is handled by prompt instructions
    if tools:
        payload["tools"] = tools
        # Force tool use: game rules require dice for combat, skill checks, saves
        # With "required", the LLM MUST call at least one tool
        # The prompts tell the LLM WHICH tool to use; this ensures it uses one
        payload["tool_choice"] = "required"
        # DO NOT set response_format - many APIs reject tools + response_format
    else:
        payload["response_format"] = response_format

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
    return run_openai_json_first_tool_requests_flow(
        generate_content_fn=generate_content,
        prompt_contents=prompt_contents,
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        provider_no_tool_requests_log_prefix="OPENROUTER_TOOL_REQUESTS",
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
) -> OpenRouterResponse:
    """Generate content with native two-phase tool calling.

    This flow uses the native API tool calling that ALL models support:
    1. Phase 1: `tools` parameter (no response_format) → model returns `tool_calls`
    2. Execute tools locally (roll_dice, roll_attack, etc.)
    3. Phase 2: `response_format` parameter (no tools) → structured JSON with results

    This approach works for GLM-4.6, Llama, Grok, and other models that support
    native API tool calling.

    Args:
        prompt_contents: List of prompt content parts
        model_name: Model name to use
        system_instruction_text: Optional system instruction
        temperature: Sampling temperature
        max_output_tokens: Maximum output tokens

    Returns:
        Final OpenRouterResponse with structured JSON
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
