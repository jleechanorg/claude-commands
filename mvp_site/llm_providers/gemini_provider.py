"""Gemini provider implementation isolated from llm_service.

Uses response_json_schema for structured output enforcement.
See: https://ai.google.dev/gemini-api/docs/structured-output
"""

from __future__ import annotations

import json
import os
from typing import Any

from google import genai
from google.genai import types

from mvp_site import constants, logging_util
from mvp_site.game_state import (
    DICE_ROLL_TOOLS,
    execute_dice_tool,
    execute_tool_requests,
    format_tool_results_text,
)
from mvp_site.llm_providers.provider_utils import (
    build_tool_results_prompt,
    stringify_prompt_contents,
)
# NOTE: Gemini response_schema is NOT used due to strict property requirements
# Gemini requires ALL object types to have non-empty properties - no dynamic keys allowed
# We rely on response_mime_type="application/json" + prompt instruction instead
# Post-response validation in narrative_response_schema.py handles structure enforcement

_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Initialize and return a singleton Gemini client."""
    global _client  # noqa: PLW0603
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
    global _client  # noqa: PLW0603
    _client = None


def count_tokens(model_name: str, contents: list[Any]) -> int:
    """Count tokens for provided content using Gemini's native endpoint."""
    client = get_client()
    return client.models.count_tokens(model=model_name, contents=contents).total_tokens


def extract_code_execution_evidence(response: Any) -> dict[str, int | bool]:
    """Best-effort detection of Gemini code_execution usage from a raw SDK response.

    We do not rely on model self-reporting. Instead, we inspect response parts for
    code_execution artifacts (executable_code / code_execution_result) emitted by
    the Gemini API when the built-in tool is actually used.
    """
    executable_code_parts = 0
    code_execution_result_parts = 0

    try:
        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            parts = getattr(content, "parts", None) if content is not None else None
            if not parts:
                continue
            for part in parts:
                if getattr(part, "executable_code", None) is not None:
                    executable_code_parts += 1
                if getattr(part, "code_execution_result", None) is not None:
                    code_execution_result_parts += 1
    except Exception:
        # If the SDK shape changes, keep this non-fatal.
        return {
            "code_execution_used": False,
            "executable_code_parts": 0,
            "code_execution_result_parts": 0,
        }

    used = (executable_code_parts + code_execution_result_parts) > 0
    return {
        "code_execution_used": used,
        "executable_code_parts": executable_code_parts,
        "code_execution_result_parts": code_execution_result_parts,
    }



def generate_json_mode_content(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    safety_settings: list[Any],
    json_mode_max_output_tokens: int,
    tools: list[dict] | None = None,
    json_mode: bool = True,
    messages: list[dict] | None = None,
    enable_code_execution: bool | None = None,
) -> Any:
    """Generate content from Gemini, optionally using tools or JSON mode.

    Note: Code execution is only compatible with JSON mode on Gemini 3.x.
    For other Gemini models, use native two-phase tool calling (Phase 1 tools,
    Phase 2 JSON) to preserve structured output.

    Args:
        prompt_contents: The prompt content to send (if messages not provided)
        model_name: Gemini model name
        system_instruction_text: Optional system instruction
        temperature: Sampling temperature
        safety_settings: Safety settings list
        json_mode_max_output_tokens: Max output tokens
        tools: Optional list of tool definitions
        json_mode: Whether to enforce application/json MIME type
        messages: Optional list of previous messages (for tool loops)
        enable_code_execution: Force-enable/disable code execution tools; defaults
            to capability auto-detection for models in constants.MODELS_WITH_CODE_EXECUTION

    Returns:
        Gemini API response
    """
    client = get_client()

    generation_config_params = {
        "max_output_tokens": json_mode_max_output_tokens,
        "temperature": temperature,
        "safety_settings": safety_settings,
    }

    if json_mode:
        generation_config_params["response_mime_type"] = "application/json"

    # Add tools if provided
    config = types.GenerateContentConfig(**generation_config_params)

    # Determine whether to attach code_execution
    allow_code_execution = (
        enable_code_execution
        if enable_code_execution is not None
        else model_name in constants.MODELS_WITH_CODE_EXECUTION
    )
    # Constraint: Only Gemini 3.x supports code_execution + JSON mode together.
    if json_mode and model_name not in constants.MODELS_WITH_CODE_EXECUTION:
        allow_code_execution = False

    gemini_tools = []

    # Handle tools conversion for Google GenAI SDK
    # The SDK expects tools as a separate argument or part of config
    if tools:
        for tool in tools:
            fn = tool["function"]
            gemini_tools.append(
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=fn["name"],
                            description=fn["description"],
                            parameters=fn.get("parameters"),
                        )
                    ]
                )
            )

    if allow_code_execution:
        gemini_tools.append(types.Tool(code_execution={}))
        logging_util.debug(
            "Code execution enabled for Gemini model %s (json_mode=%s)",
            model_name,
            json_mode,
        )

    if gemini_tools:
        config.tools = gemini_tools

    if system_instruction_text:
        # Use plain string - all current Gemini SDK versions accept string directly
        config.system_instruction = system_instruction_text
    
    # If messages are provided, use them (ChatSession style) or convert to contents
    # The Google GenAI SDK generate_content accepts a list of contents.
    # We need to ensure format compatibility.
    contents = []
    if messages:
        # Convert OpenAI-style messages to Gemini Content objects
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            if msg["role"] == "system":
                continue # Handled in config
            if msg["role"] == "tool":
                # Skip tool responses in history for JSON-mode calls; the tool results
                # are already embedded in prompt_contents for Phase 2.
                continue
            
            parts = []
            if msg.get("content"):
                parts.append(types.Part(text=msg["content"]))
            
            # Helper for tool calls/responses would go here
            contents.append(types.Content(role=role, parts=parts))
            
    else:
        contents = prompt_contents

    return client.models.generate_content(
        model=model_name,
        contents=contents,
        config=config,
    )


def _stringify_prompt_contents(prompt_contents: list[Any]) -> str:
    """Backward-compatible wrapper around provider_utils.stringify_prompt_contents."""
    return stringify_prompt_contents(prompt_contents)




def generate_content_with_code_execution(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    safety_settings: list[Any],
    json_mode_max_output_tokens: int,
) -> Any:
    """Generate a SINGLE JSON response using Gemini's code_execution tool.

    Gemini 3.x is the only Gemini family that supports combining:
    - response_mime_type="application/json"
    - built-in tools (code_execution)

    This should be a single inference (one generateContent call). Dice rolls are
    computed inside the model via code_execution, not via server-side tools.
    """
    logging_util.info(
        "Gemini code_execution: Single JSON call (no tool_requests Phase 2)"
    )

    code_exec_override = (
        "\n\nIMPORTANT (Gemini 3 code_execution mode):\n"
        "- Do NOT output `tool_requests`.\n"
        "- Use the built-in code execution tool to roll dice and compute outcomes.\n"
        "- Return the final, complete response JSON in this single response.\n"
        "- If `tool_requests` exists in the schema, set it to an empty list.\n"
        "- If you roll any dice, populate `dice_audit_events` with one event per roll.\n"
        "  Each dice_audit_events item MUST include: source=\"code_execution\", label, notation, rolls, modifier, total.\n"
    )
    effective_system_instruction = (
        f"{system_instruction_text}{code_exec_override}"
        if system_instruction_text
        else code_exec_override
    )

    return generate_json_mode_content(
        prompt_contents=prompt_contents,
        model_name=model_name,
        system_instruction_text=effective_system_instruction,
        temperature=temperature,
        safety_settings=safety_settings,
        json_mode_max_output_tokens=json_mode_max_output_tokens,
        tools=None,
        json_mode=True,
        enable_code_execution=True,
    )


def _execute_native_tool_calls(tool_calls: list) -> list[dict]:
    """Execute native Gemini API function_calls and return results.

    Args:
        tool_calls: List of FunctionCall objects from Gemini response

    Returns:
        List of {tool_call_id, tool, args, result} dicts
    """
    results = []
    for i, call in enumerate(tool_calls):
        try:
            # Gemini FunctionCall has name and args attributes
            tool_name = call.name if hasattr(call, 'name') else str(call.get('name', ''))
            args = dict(call.args) if hasattr(call, 'args') else call.get('args', {})
            call_id = f"call_{i}"  # Gemini doesn't provide IDs like OpenAI

            # Execute the tool
            result = execute_dice_tool(tool_name, args)

            results.append({
                "tool_call_id": call_id,
                "tool": tool_name,
                "args": args,
                "result": result,
            })
            logging_util.info(f"GEMINI_NATIVE_TOOL: {tool_name}({args}) -> {result}")

        except Exception as e:
            logging_util.error(f"Gemini native tool execution error: {e}")
            results.append({
                "tool_call_id": f"call_{i}",
                "tool": str(getattr(call, 'name', 'unknown')),
                "args": {},
                "result": {"error": str(e)},
            })

    return results


def generate_content_with_native_tools(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    safety_settings: list[Any],
    json_mode_max_output_tokens: int,
) -> Any:
    """Generate content with native two-phase tool calling for Gemini 2.5.

    This flow uses native API tool calling:
    1. Phase 1: `tools` parameter (no JSON mode) → model returns function_calls
    2. Execute tools locally (roll_dice, roll_attack, etc.)
    3. Phase 2: JSON mode (no tools) → structured JSON with results

    This approach works for Gemini 2.5 which cannot combine tools + JSON mode.

    Args:
        prompt_contents: List of prompt content parts
        model_name: Model name to use
        system_instruction_text: Optional system instruction
        temperature: Sampling temperature
        safety_settings: Safety settings list
        json_mode_max_output_tokens: Maximum output tokens

    Returns:
        Gemini API response with structured JSON
    """
    # Convert DICE_ROLL_TOOLS to Gemini format
    gemini_tools = []
    for tool in DICE_ROLL_TOOLS:
        fn = tool["function"]
        gemini_tools.append(
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=fn["name"],
                        description=fn["description"],
                        parameters=fn.get("parameters"),
                    )
                ]
            )
        )

    # Phase 1: Native tool calling (no JSON mode)
    logging_util.info("Gemini NATIVE Phase 1: Calling with tools parameter")
    client = get_client()

    config = types.GenerateContentConfig(
        max_output_tokens=json_mode_max_output_tokens,
        temperature=temperature,
        safety_settings=safety_settings,
        tools=gemini_tools,
        # Force tool use: game rules require dice for combat, skill checks, saves
        # With mode='ANY', the LLM MUST call at least one tool
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode='ANY')
        ),
    )

    if system_instruction_text:
        config.system_instruction = system_instruction_text

    response1 = client.models.generate_content(
        model=model_name,
        contents=prompt_contents,
        config=config,
    )

    # Check for function calls in response
    function_calls = []
    if response1.candidates and response1.candidates[0].content.parts:
        for part in response1.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_calls.append(part.function_call)

    if not function_calls:
        # No tools needed - make Phase 2 call for JSON schema response
        logging_util.info("Gemini NATIVE Phase 1: No function_calls, proceeding to Phase 2")

        # Build history for Phase 2
        history = []
        history.append(types.Content(
            role="user",
            parts=[types.Part(text=stringify_prompt_contents(prompt_contents))]
        ))

        # Add Phase 1 response if it has text
        phase1_text = ""
        if response1.candidates and response1.candidates[0].content.parts:
            for part in response1.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    phase1_text += part.text

        if phase1_text:
            history.append(types.Content(
                role="model",
                parts=[types.Part(text=phase1_text)]
            ))
            history.append(types.Content(
                role="user",
                parts=[types.Part(text="Now provide your response in the required JSON format.")]
            ))

        return generate_json_mode_content(
            prompt_contents=history if phase1_text else prompt_contents,
            model_name=model_name,
            system_instruction_text=system_instruction_text if not phase1_text else None,
            temperature=temperature,
            safety_settings=safety_settings,
            json_mode_max_output_tokens=json_mode_max_output_tokens,
            tools=None,
            json_mode=True,
        )

    # Execute function calls
    logging_util.info(f"Gemini NATIVE Phase 1: Executing {len(function_calls)} function call(s)")
    tool_results = _execute_native_tool_calls(function_calls)

    if not tool_results:
        logging_util.warning("Gemini NATIVE: No valid tool results, making JSON-only call")
        return generate_json_mode_content(
            prompt_contents=prompt_contents,
            model_name=model_name,
            system_instruction_text=system_instruction_text,
            temperature=temperature,
            safety_settings=safety_settings,
            json_mode_max_output_tokens=json_mode_max_output_tokens,
            tools=None,
            json_mode=True,
        )

    # Build Phase 2 context with tool results
    tool_results_text = format_tool_results_text(tool_results)

    # Build conversation history for Phase 2
    history = []
    history.append(types.Content(
        role="user",
        parts=[types.Part(text=stringify_prompt_contents(prompt_contents))]
    ))

    # Add model's Phase 1 response (with function calls)
    phase1_parts = []
    if response1.candidates and response1.candidates[0].content.parts:
        for part in response1.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                phase1_parts.append(types.Part(text=part.text))
            elif hasattr(part, 'function_call') and part.function_call:
                # Include function call reference
                phase1_parts.append(types.Part(text=f"[Called {part.function_call.name}]"))

    if phase1_parts:
        history.append(types.Content(role="model", parts=phase1_parts))

    # Add tool results as user turn
    history.append(types.Content(
        role="user",
        parts=[types.Part(text=build_tool_results_prompt(
            tool_results_text,
            extra_instructions=(
                "Now provide the complete response in the required JSON format. "
                "Include the dice roll results in the dice_rolls array."
            ),
        ))]
    ))

    # Phase 2: JSON schema response with results
    logging_util.info("Gemini NATIVE Phase 2: JSON call with tool results")
    return generate_json_mode_content(
        prompt_contents=history,
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        safety_settings=safety_settings,
        json_mode_max_output_tokens=json_mode_max_output_tokens,
        tools=None,
        json_mode=True,
    )


def generate_content_with_tool_requests(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    safety_settings: list[Any],
    json_mode_max_output_tokens: int,
) -> Any:
    """Generate content with JSON-first tool request flow for Gemini 2.x.

    This is the preferred flow that keeps JSON mode throughout:
    1. First call: JSON mode enabled (no tools param) - LLM includes tool_requests if needed
    2. If tool_requests present: Execute tools, inject results, second JSON call
    3. If no tool_requests: Return first response as-is

    This avoids the Gemini API limitation where tools + JSON mode cannot be combined.

    Args:
        prompt_contents: List of prompt content parts
        model_name: Model name to use
        system_instruction_text: Optional system instruction
        temperature: Sampling temperature
        safety_settings: Safety settings list
        json_mode_max_output_tokens: Maximum output tokens

    Returns:
        Gemini API response with complete JSON
    """
    # Phase 1: JSON mode call (no tools) - same as main branch
    logging_util.info("Gemini Phase 1: JSON call (checking for tool_requests)")
    response_1 = generate_json_mode_content(
        prompt_contents=prompt_contents,
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        safety_settings=safety_settings,
        json_mode_max_output_tokens=json_mode_max_output_tokens,
        tools=None,  # No tools = JSON mode enforced
        json_mode=True,
    )

    # Extract text from Gemini response
    try:
        response_text = response_1.text if hasattr(response_1, 'text') else ""
        if response_1.candidates and response_1.candidates[0].content.parts:
            response_text = response_1.candidates[0].content.parts[0].text
    except (AttributeError, IndexError):
        logging_util.warning("Could not extract text from Phase 1 response")
        return response_1

    # Parse response to check for tool_requests
    try:
        response_data = json.loads(response_text) if response_text else {}
    except json.JSONDecodeError:
        logging_util.warning("Gemini Phase 1 response not valid JSON, returning as-is")
        return response_1

    tool_requests = response_data.get("tool_requests", [])
    if not tool_requests:
        logging_util.debug("No tool_requests in response, returning Phase 1 result")
        return response_1

    # Execute tool requests
    logging_util.info(f"Executing {len(tool_requests)} tool request(s)")
    tool_results = execute_tool_requests(tool_requests)

    if not tool_results:
        logging_util.warning("No valid tool results, returning Phase 1 result")
        return response_1

    # Build Phase 2 context with tool results
    tool_results_text = format_tool_results_text(tool_results)

    # For Gemini, we build the conversation history as Content objects
    history = []
    # User turn (original prompt)
    history.append(types.Content(
        role="user",
        parts=[types.Part(text=stringify_prompt_contents(prompt_contents))]
    ))
    # Model turn (Phase 1 response)
    history.append(types.Content(
        role="model",
        parts=[types.Part(text=response_text)]
    ))
    # User turn with tool results
    history.append(types.Content(
        role="user",
        parts=[types.Part(text=build_tool_results_prompt(tool_results_text))]
    ))

    # Phase 2: JSON call with tool results
    logging_util.info("Gemini Phase 2: JSON call with tool results")
    return generate_json_mode_content(
        prompt_contents=history,  # Pass full conversation history
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        safety_settings=safety_settings,
        json_mode_max_output_tokens=json_mode_max_output_tokens,
        tools=None,  # No tools = JSON mode enforced
        json_mode=True,
    )
