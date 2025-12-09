"""Gemini provider implementation isolated from llm_service."""

from __future__ import annotations

import os
from typing import Any

from google import genai
from google.genai import types

from mvp_site import constants, logging_util

_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Initialize and return a singleton Gemini client."""
    global _client
    if _client is None:
        logging_util.info("Initializing Gemini Client")
        api_key: str | None = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GEMINI_API_KEY environment variable not found!")
        _client = genai.Client(api_key=api_key)
        logging_util.info("Gemini Client initialized successfully")
    return _client


def clear_cached_client() -> None:
    """Clear the cached client (primarily for tests)."""
    global _client
    _client = None


def count_tokens(model_name: str, contents: list[Any]) -> int:
    """Count tokens for provided content using Gemini's native endpoint."""
    client = get_client()
    return client.models.count_tokens(model=model_name, contents=contents).total_tokens


def generate_json_mode_content(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    max_output_tokens: int,
    temperature: float,
    safety_settings: list[Any],
    json_mode_max_output_tokens: int,
    enable_code_execution: bool | None = None,
) -> Any:
    """Generate content from Gemini using JSON response mode.

    Args:
        prompt_contents: The prompt content to send
        model_name: Gemini model name
        system_instruction_text: Optional system instruction
        max_output_tokens: Max tokens (unused, kept for API compat)
        temperature: Sampling temperature
        safety_settings: Safety settings list
        json_mode_max_output_tokens: Actual max output tokens for JSON mode
        enable_code_execution: Whether to enable code_execution tool.
            If None, auto-detect based on model capabilities.

    Returns:
        Gemini API response

    Note:
        Code execution + JSON mode is supported on Gemini 2.0 and 3.0 models.
        See: https://ai.google.dev/gemini-api/docs/structured-output
    """
    client = get_client()

    # Auto-detect code execution capability if not explicitly set
    if enable_code_execution is None:
        enable_code_execution = model_name in constants.MODELS_WITH_CODE_EXECUTION

    generation_config_params = {
        "max_output_tokens": json_mode_max_output_tokens,
        "temperature": temperature,
        "safety_settings": safety_settings,
        "response_mime_type": "application/json",
    }

    # Enable code_execution for supported models (Gemini 2.0/3.0)
    # This allows the LLM to run Python code for true dice roll randomness
    if enable_code_execution:
        generation_config_params["tools"] = [types.Tool(code_execution={})]
        logging_util.debug(f"Code execution enabled for model: {model_name}")

    if system_instruction_text:
        generation_config_params["system_instruction"] = types.Part(
            text=system_instruction_text
        )

    return client.models.generate_content(
        model=model_name,
        contents=prompt_contents,
        config=types.GenerateContentConfig(**generation_config_params),
    )
