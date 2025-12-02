"""Gemini provider implementation isolated from llm_service."""

from __future__ import annotations

import os
from typing import Any

from google import genai
from google.genai import types

from mvp_site import logging_util

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
) -> Any:
    """Generate content from Gemini using JSON response mode."""
    client = get_client()

    generation_config_params = {
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "safety_settings": safety_settings,
        "tools": [types.Tool(code_execution=types.ToolCodeExecution())],
    }

    generation_config_params["response_mime_type"] = "application/json"
    generation_config_params["max_output_tokens"] = json_mode_max_output_tokens

    if system_instruction_text:
        generation_config_params["system_instruction"] = types.Part(
            text=system_instruction_text
        )

    return client.models.generate_content(
        model=model_name,
        contents=prompt_contents,
        config=types.GenerateContentConfig(**generation_config_params),
    )
