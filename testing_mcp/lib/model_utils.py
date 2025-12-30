"""Model selection and user settings utilities for MCP tests."""

from __future__ import annotations

from typing import Any

from .mcp_client import MCPClient


# Default model matrix for multi-provider testing
DEFAULT_MODEL_MATRIX = [
    "gemini-3-flash-preview",
    "qwen-3-235b-a22b-instruct-2507",
]


def settings_for_model(model_id: str) -> dict[str, Any]:
    """Map model ID to provider settings.

    Args:
        model_id: Model identifier (e.g., "gemini-3-flash-preview", "qwen-3-235b-a22b-instruct-2507")

    Returns:
        Dict with llm_provider and provider-specific model key.

    Raises:
        ValueError: If model provider cannot be determined from ID.
    """
    model = model_id.strip()
    model_lower = model.lower()

    if model_lower.startswith("gemini-"):
        return {"llm_provider": "gemini", "gemini_model": model}

    if model_lower.startswith("qwen-") or model_lower in {
        "zai-glm-4.6",
        "llama-3.3-70b",
        "gpt-oss-120b",
    }:
        return {"llm_provider": "cerebras", "cerebras_model": model}

    if "/" in model_lower:
        return {"llm_provider": "openrouter", "openrouter_model": model}

    raise ValueError(f"Unknown model/provider mapping for: {model}")


def update_user_settings(
    client: MCPClient, *, user_id: str, settings: dict[str, Any]
) -> None:
    """Update user settings for model selection.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        settings: Settings dict (typically from settings_for_model).

    Raises:
        RuntimeError: If the server returns an error.
    """
    payload = client.tools_call(
        "update_user_settings",
        {"user_id": user_id, "settings": settings},
    )
    if payload.get("error"):
        raise RuntimeError(f"update_user_settings error: {payload['error']}")
