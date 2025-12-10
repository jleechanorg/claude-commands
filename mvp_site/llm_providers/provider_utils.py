"""Shared utilities for LLM provider implementations."""

from __future__ import annotations


# =============================================================================
# NARRATIVE_RESPONSE_SCHEMA - Shared JSON schema for structured LLM outputs
# =============================================================================
# SOURCE OF TRUTH: mvp_site/prompts/game_state_instruction.md
#   Section: "JSON Response Format (Required Fields)" - lines 24-64
#   This prompt tells the LLM what structure to generate.
#
# VALIDATION LAYER: mvp_site/narrative_response_schema.py
#   NarrativeResponse class validates and processes the parsed response.
#   planning_block internal structure (choices with dynamic keys) is validated there.
#
# Used by: Cerebras (json_schema), Gemini (response_schema), OpenRouter (Grok)
#
# Format variations by provider:
# - Cerebras/OpenRouter: {"type": "json_schema", "json_schema": {"schema": THIS}}
# - Gemini: {"response_schema": THIS}
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
            "description": "GM planning with thinking field and dynamic choices (snake_case keys like explore_tavern, attack_goblin, god:option_1)",
            # Gemini requires properties to be non-empty for object types
            # Using additionalProperties:true allows dynamic choice keys
            "additionalProperties": True,
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
            "additionalProperties": True,
        },
        "debug_info": {
            "type": "object",
            "description": "Debug information for development",
            "additionalProperties": True,
        },
        "god_mode_response": {
            "type": "string",
            "description": "Response for god mode commands",
        },
    },
    "required": ["narrative", "planning_block", "entities_mentioned"],
    # Note: With strict:False, additionalProperties defaults to true (allows extra fields)
}


def get_openai_json_schema_format(name: str = "narrative_response") -> dict:
    """Get schema in OpenAI/Cerebras json_schema format.

    Returns the schema wrapped for use with response_format.type="json_schema"

    NOTE: Uses strict=False to allow dynamic choice keys in planning_block.
    The game design requires semantic keys like 'explore_tavern', 'attack_goblin',
    'god:option_1' which cannot be pre-defined in a strict schema.

    Structure enforcement still happens via:
    - Top-level fields (narrative, entities_mentioned) are validated
    - planning_block internal structure validated by narrative_response_schema.py
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": False,  # Allow dynamic choice keys in planning_block
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
