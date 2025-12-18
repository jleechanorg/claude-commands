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
from collections.abc import Callable
from typing import Any, Protocol

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
        "dice_audit_events": {
            "type": "array",
            "description": (
                "Structured dice audit events with raw rolls and computed totals. "
                "Used for post-hoc RNG auditing and provenance (server_tool vs code_execution)."
            ),
            "items": {
                "type": "object",
                "description": "A single dice audit event",
                "additionalProperties": True,
            },
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


class _Logger(Protocol):
    def info(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...


def execute_openai_tool_calls(
    tool_calls: list[dict],
    *,
    execute_tool_fn: Callable[[str, dict[str, Any]], dict],
    logger: _Logger | None = None,
) -> list[dict]:
    """Execute OpenAI-compatible tool_calls and return a normalized result list.

    Expected tool_calls format:
      [{"id": str, "type": "function", "function": {"name": str, "arguments": str}}]
    """
    results: list[dict] = []
    for call in tool_calls:
        try:
            call_id = str(call.get("id", ""))
            func = call.get("function", {}) or {}
            tool_name = str(func.get("name", ""))
            args_str = func.get("arguments", "{}")

            # Parse arguments JSON
            try:
                args = json.loads(args_str) if args_str else {}
            except json.JSONDecodeError:
                args = {}

            result = execute_tool_fn(tool_name, args)
            results.append(
                {
                    "tool_call_id": call_id,
                    "tool": tool_name,
                    "args": args,
                    "result": result,
                }
            )
            if logger:
                logger.info(f"NATIVE_TOOL_CALL: {tool_name}({args}) -> {result}")
        except Exception as exc:  # noqa: BLE001 - defensive tool loop
            if logger:
                logger.error(f"Native tool execution error: {exc}")
            results.append(
                {
                    "tool_call_id": str(call.get("id", "")),
                    "tool": str((call.get("function", {}) or {}).get("name", "unknown")),
                    "args": {},
                    "result": {"error": str(exc)},
                }
            )
    return results


def _compact_tool_result_for_prompt(result: Any) -> dict[str, Any]:
    """Reduce tool results to the minimal data the model needs to narrate correctly."""
    if not isinstance(result, dict):
        return {"result": result}

    if isinstance(result.get("error"), str) and result["error"]:
        return {"error": result["error"]}

    compact: dict[str, Any] = {}
    if isinstance(result.get("formatted"), str) and result["formatted"]:
        compact["formatted"] = result["formatted"]

    # Common dice payload fields
    for key in ("notation", "rolls", "modifier", "total", "natural_20", "natural_1"):
        if key in result:
            compact[key] = result[key]

    # roll_attack
    for key in ("hit", "critical", "fumble", "target_ac", "weapon_name", "ability_name"):
        if key in result:
            compact[key] = result[key]
    if isinstance(result.get("damage"), dict):
        dmg = result["damage"]
        compact["damage"] = {
            k: dmg.get(k) for k in ("notation", "rolls", "modifier", "total", "critical")
        }

    # roll_skill_check / roll_saving_throw
    for key in ("skill", "dc", "success", "save_type", "proficiency_applied", "attribute_name", "roll"):
        if key in result:
            compact[key] = result[key]

    return compact


def run_openai_json_first_tool_requests_flow(
    *,
    generate_content_fn: Callable[..., Any],
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    max_output_tokens: int,
    provider_no_tool_requests_log_prefix: str,
    execute_tool_requests_fn: Callable[[list[dict]], list[dict]],
    format_tool_results_text_fn: Callable[[list[dict]], str],
    logger: _Logger,
) -> Any:
    """Run the JSON-first tool_requests orchestration shared by OpenAI-chat providers."""
    logger.info("Phase 1: JSON call (checking for tool_requests)")
    response = generate_content_fn(
        prompt_contents=prompt_contents,
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        tools=None,
    )

    try:
        response_data = json.loads(response.text) if response.text else {}
    except json.JSONDecodeError:
        logger.warning("Phase 1 response not valid JSON, returning as-is")
        return response

    tool_requests = response_data.get("tool_requests", [])
    if not tool_requests:
        logger.info(
            f"{provider_no_tool_requests_log_prefix}: No tool_requests in LLM response. "
            f"Response keys: {list(response_data.keys())}"
        )
        return response

    logger.info(f"Executing {len(tool_requests)} tool request(s)")
    tool_results = execute_tool_requests_fn(tool_requests)
    if not tool_results:
        logger.warning("No valid tool results, returning Phase 1 result")
        return response

    tool_results_text = format_tool_results_text_fn(tool_results)

    messages: list[dict[str, Any]] = []
    if system_instruction_text:
        messages.append({"role": "system", "content": system_instruction_text})
    messages.append({"role": "user", "content": stringify_chat_parts(prompt_contents)})
    messages.append({"role": "assistant", "content": response.text})
    messages.append({"role": "user", "content": build_tool_results_prompt(tool_results_text)})

    logger.info("Phase 2: JSON call with tool results")
    return generate_content_fn(
        prompt_contents=[],
        model_name=model_name,
        system_instruction_text=None,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        tools=None,
        messages=messages,
    )


def run_openai_native_two_phase_flow(
    *,
    generate_content_fn: Callable[..., Any],
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    max_output_tokens: int,
    dice_roll_tools: list[dict],
    execute_tool_fn: Callable[[str, dict[str, Any]], dict],
    logger: _Logger,
) -> Any:
    """Run native tool calling (Phase 1 tools, Phase 2 JSON) for OpenAI-chat providers."""
    logger.info("NATIVE Phase 1: Calling with tools parameter")

    base_messages: list[dict[str, Any]] = []
    if system_instruction_text:
        base_messages.append({"role": "system", "content": system_instruction_text})
    base_messages.append({"role": "user", "content": stringify_chat_parts(prompt_contents)})

    response1 = generate_content_fn(
        prompt_contents=prompt_contents,
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        tools=dice_roll_tools,
    )

    tool_calls = getattr(response1, "tool_calls", None)
    if not tool_calls:
        logger.info("NATIVE Phase 1: No tool_calls, proceeding to Phase 2 for JSON")

        phase2_messages = list(base_messages)
        if getattr(response1, "text", ""):
            phase2_messages.append({"role": "assistant", "content": response1.text})
            phase2_messages.append(
                {
                    "role": "user",
                    "content": "Now provide your response in the required JSON format.",
                }
            )

        return generate_content_fn(
            prompt_contents=[],
            model_name=model_name,
            system_instruction_text=None,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            tools=None,
            messages=phase2_messages if getattr(response1, "text", "") else base_messages,
        )

    logger.info(f"NATIVE Phase 1: Executing {len(tool_calls)} tool call(s)")
    tool_results = execute_openai_tool_calls(
        tool_calls,
        execute_tool_fn=execute_tool_fn,
        logger=logger,
    )
    if not tool_results:
        logger.warning("NATIVE: No valid tool results, making JSON-only call")
        return generate_content_fn(
            prompt_contents=prompt_contents,
            model_name=model_name,
            system_instruction_text=system_instruction_text,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            tools=None,
        )

    phase2_messages: list[dict[str, Any]] = list(base_messages)
    phase2_messages.append(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls,
        }
    )
    for result in tool_results:
        phase2_messages.append(
            {
                "role": "tool",
                "tool_call_id": result["tool_call_id"],
                "content": json.dumps(_compact_tool_result_for_prompt(result["result"])),
            }
        )
    phase2_messages.append(
        {
            "role": "user",
            "content": (
                "The dice rolls have been executed. Use these EXACT results in your narrative. "
                "Now provide the complete response in the required JSON format. "
                "Include the dice roll results in the dice_rolls array."
            ),
        }
    )

    logger.info("NATIVE Phase 2: JSON call with tool results")
    return generate_content_fn(
        prompt_contents=[],
        model_name=model_name,
        system_instruction_text=None,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        tools=None,
        messages=phase2_messages,
    )


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
