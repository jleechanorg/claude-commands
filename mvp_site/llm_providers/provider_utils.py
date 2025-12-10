"""Shared utilities for LLM provider implementations."""

from __future__ import annotations


# =============================================================================
# NARRATIVE_RESPONSE_SCHEMA - Shared JSON schema for structured LLM outputs
# =============================================================================
# Used by: Cerebras (json_schema), Gemini (response_json_schema), OpenRouter (Grok)
# This schema enforces the structure that NarrativeResponse expects.
#
# Format variations by provider:
# - Cerebras/OpenRouter: {"type": "json_schema", "json_schema": {"schema": THIS}}
# - Gemini: {"response_json_schema": THIS}
# =============================================================================

NARRATIVE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "narrative": {
            "type": "string",
            "description": "The main narrative text describing what happens",
        },
        "planning_block": {
            "type": "object",
            "description": "Internal GM planning and analysis with choices for player",
            "properties": {
                "thinking": {
                    "type": "string",
                    "description": "GM's internal reasoning and analysis",
                },
                "context": {
                    "type": "string",
                    "description": "Optional context information",
                },
                "choices": {
                    "type": "object",
                    "description": "Available choices for the player (use snake_case keys)",
                    "properties": {
                        "choice_1": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "description": {"type": "string"},
                                "risk_level": {"type": "string"},
                            },
                            "required": ["text", "description"],
                        },
                        "choice_2": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "description": {"type": "string"},
                                "risk_level": {"type": "string"},
                            },
                            "required": ["text", "description"],
                        },
                        "choice_3": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "description": {"type": "string"},
                                "risk_level": {"type": "string"},
                            },
                            "required": ["text", "description"],
                        },
                    },
                    "required": ["choice_1", "choice_2"],
                },
            },
            "required": ["thinking", "choices"],
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
        "turn_summary": {
            "type": "string",
            "description": "Summary of what happened this turn",
        },
        "state_updates": {
            "type": "object",
            "description": "Game state updates (HP, inventory, conditions, etc.)",
        },
        "debug_info": {
            "type": "object",
            "description": "Debug information for development",
        },
        "god_mode_response": {
            "type": "string",
            "description": "Response for god mode commands",
        },
    },
    "required": ["narrative", "planning_block", "entities_mentioned"],
    # Note: additionalProperties NOT set to false - allows extra fields for flexibility
}


def get_openai_json_schema_format(name: str = "narrative_response") -> dict:
    """Get schema in OpenAI/Cerebras json_schema format.

    Returns the schema wrapped for use with response_format.type="json_schema"
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": NARRATIVE_RESPONSE_SCHEMA,
        },
    }


class ContextTooLargeError(ValueError):
    """Raised when the prompt context is too large for meaningful output.

    This exception indicates that the API returned a response but was unable
    to generate content due to context limitations (e.g., finish_reason='length'
    with minimal completion tokens).
    """

    def __init__(
        self,
        message: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        finish_reason: str | None = None,
    ):
        super().__init__(message)
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.finish_reason = finish_reason


def check_context_too_large(
    finish_reason: str | None,
    completion_tokens: int,
    prompt_tokens: int,
    has_content: bool,
) -> None:
    """Check if API response indicates context was too large for meaningful output.

    Raises ContextTooLargeError if the response suggests the prompt consumed
    too much of the context window, leaving insufficient room for output.

    Args:
        finish_reason: The API's finish reason (e.g., 'stop', 'length')
        completion_tokens: Number of tokens generated in the response
        prompt_tokens: Number of tokens in the prompt
        has_content: Whether the response contains actual content

    Raises:
        ContextTooLargeError: If finish_reason='length' and no meaningful content
    """
    if finish_reason == "length" and completion_tokens <= 1 and not has_content:
        raise ContextTooLargeError(
            f"Context too large: prompt used {prompt_tokens:,} tokens, "
            f"model could only generate {completion_tokens} completion token(s). "
            "The prompt must be reduced to allow room for output.",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=finish_reason,
        )
