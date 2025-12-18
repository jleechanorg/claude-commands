"""Shared utilities for LLM provider implementations.

Schema reference:
- SOURCE OF TRUTH: mvp_site/prompts/game_state_instruction.md (Section: "JSON Response Format (Required Fields)")
- VALIDATION LAYER: mvp_site/schemas/narrative_response_schema.py
- Hierarchy: prompt → NARRATIVE_RESPONSE_SCHEMA → NarrativeResponse

Provider notes:
- Cerebras/OpenRouter uses NARRATIVE_RESPONSE_SCHEMA via get_openai_json_schema_format(strict=False)
- Gemini avoids response_schema and uses response_mime_type="application/json" + prompt instruction
"""

from __future__ import annotations

import json
from typing import Any

# =============================================================================
# NARRATIVE_RESPONSE_SCHEMA - JSON schema for structured LLM outputs
# =============================================================================

# Schema for Cerebras/OpenRouter - supports additionalProperties for dynamic objects
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
            "properties": {
                "thinking": {
                    "type": "string",
                    "description": "GM tactical analysis of the current situation and what the player might want to do",
                },
                "context": {
                    "type": "string",
                    "description": "Current scenario context for choice generation",
                },
                "choices": {
                    "type": "object",
                    "description": "Player choices with snake_case keys (e.g., explore_tavern, attack_goblin)",
                    "minProperties": 1,  # Require at least one choice
                    "additionalProperties": {
                        "type": "object",
                        "description": "A single player choice option",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Short display text for the choice",
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of what this choice entails",
                            },
                            "risk_level": {
                                "type": "string",
                                "description": "Risk assessment: low, medium, high, or unknown",
                            },
                        },
                        "required": ["text", "description"],
                    },
                },
            },
            "required": ["thinking", "choices"],
            # additionalProperties:true allows extra fields like context
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
        "tool_requests": {
            "type": "array",
            "description": "Request dice rolls or skill checks. Server will execute and you'll get results for the final narrative.",
            "items": {
                "type": "object",
                "properties": {
                    "tool": {
                        "type": "string",
                        "enum": ["roll_dice", "roll_attack", "roll_skill_check", "roll_saving_throw"],
                        "description": "The tool to call",
                    },
                    "args": {
                        "type": "object",
                        "description": "Arguments for the tool",
                        "additionalProperties": True,
                    },
                },
                "required": ["tool", "args"],
            },
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


def stringify_prompt_contents(prompt_contents: list[Any]) -> str:
    """Best-effort stringify prompt content parts for provider message payloads."""
    if not prompt_contents:
        return ""

    parts: list[str] = []
    for item in prompt_contents:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict):
            # Handle dict-based content (e.g., {"text": "..."})
            if "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        else:
            parts.append(str(item))

    return "\n".join(parts)


def stringify_chat_parts(parts: list[Any]) -> str:
    """Stringify prompt parts for OpenAI-chat compatible providers (Cerebras/OpenRouter).

    Matches the historical formatting used in those providers: JSON-dump non-strings
    and join with a blank line between parts.
    """
    if not parts:
        return ""

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


def build_tool_results_prompt(tool_results_text: str, extra_instructions: str = "") -> str:
    """Build the Phase 2 prompt snippet for injecting tool results."""
    base = (
        "Tool results (use these exact numbers in your narrative):\n"
        f"{tool_results_text}\n\n"
        "The dice rolls have been executed by the server. Copy these EXACT results into your response. "
        "Do NOT recalculate, round, or modify outcomes. "
        "Now write the final response using these results. Do NOT include tool_requests in your response."
    )
    extra = (extra_instructions or "").strip()
    if not extra:
        return base
    return f"{base}\n\n{extra}"


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
