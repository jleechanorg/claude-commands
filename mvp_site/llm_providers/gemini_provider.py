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
from mvp_site.dice import DICE_ROLL_TOOLS, execute_dice_tool
from mvp_site.game_state import execute_tool_requests, format_tool_results_text
from mvp_site.llm_providers.provider_utils import (
    build_tool_results_prompt,
    run_json_first_tool_requests_flow,
    stringify_prompt_contents,
)
from mvp_site.llm_providers import gemini_code_execution
# NOTE: Gemini response_schema is NOT used due to strict property requirements
# Gemini requires ALL object types to have non-empty properties - no dynamic keys allowed
# We rely on response_mime_type="application/json" + prompt instruction instead
# Post-response validation in narrative_response_schema.py handles structure enforcement

import re

# Marker pattern for stripping tool_requests dice instructions when using code_execution
_TOOL_REQUESTS_DICE_PATTERN = re.compile(
    r"<!-- BEGIN_TOOL_REQUESTS_DICE[^>]*-->.*?<!-- END_TOOL_REQUESTS_DICE -->",
    re.DOTALL,
)


def strip_tool_requests_dice_instructions(text: str) -> str:
    """Remove tool_requests-specific dice instructions from system prompt.

    When using Gemini code_execution for dice, we need to strip the conflicting
    tool_requests-based dice instructions from game_state_instruction.md.
    This prevents the model from receiving contradictory guidance about how
    to generate dice rolls.

    The markers in game_state_instruction.md look like:
    <!-- BEGIN_TOOL_REQUESTS_DICE: description -->
    ... tool_requests dice content ...
    <!-- END_TOOL_REQUESTS_DICE -->

    Args:
        text: System instruction text that may contain tool_requests dice sections

    Returns:
        Text with tool_requests dice sections removed
    """
    if not text:
        return text
    return _TOOL_REQUESTS_DICE_PATTERN.sub("", text)


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


def extract_code_execution_evidence(response: Any) -> dict[str, int | bool | str]:
    """Backward-compatible re-export (see llm_providers/gemini_code_execution.py)."""
    return gemini_code_execution.extract_code_execution_evidence(response)


def extract_code_execution_parts_summary(
    response: Any,
    *,
    max_parts: int = 5,
    max_chars: int = 500,
) -> dict[str, Any]:
    """Backward-compatible re-export (see llm_providers/gemini_code_execution.py)."""
    return gemini_code_execution.extract_code_execution_parts_summary(
        response, max_parts=max_parts, max_chars=max_chars
    )


def maybe_log_code_execution_parts(
    response: Any,
    *,
    model_name: str,
    context: str,
) -> None:
    """Backward-compatible wrapper (see llm_providers/gemini_code_execution.py)."""
    gemini_code_execution.log_code_execution_parts(
        response, model_name=model_name, context=context
    )



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

    # Determine whether to attach code_execution
    allow_code_execution = (
        enable_code_execution
        if enable_code_execution is not None
        else model_name in constants.MODELS_WITH_CODE_EXECUTION
    )

    # Add thinkingConfig for Gemini 3 models with code_execution.
    # Use thinking_budget per google-genai SDK (ThinkingConfig fields).
    if allow_code_execution and model_name.startswith("gemini-3"):
        generation_config_params["thinking_config"] = types.ThinkingConfig(
            thinking_budget=1024
        )
        logging_util.debug(
            "ThinkingConfig enabled for %s to improve code_execution compliance",
            model_name,
        )

    # Add tools if provided
    config = types.GenerateContentConfig(**generation_config_params)
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
        "\n\n## 🎲 CRITICAL: DICE VALUES ARE UNKNOWABLE (Gemini 3 code_execution mode)\n\n"
        "**ABSOLUTE RULE: You CANNOT know dice values without executing code.**\n\n"
        "Dice results are quantum-random. Like checking real-world temperature, you MUST query\n"
        "the random number generator to OBSERVE the value. You cannot predict, estimate, or\n"
        "fabricate dice results - they do not exist until you execute code to generate them.\n\n"
        "### 🚨 ENFORCEMENT WARNING:\n"
        "Your code IS INSPECTED. If `random.randint()` is not found in your executed code,\n"
        "your response WILL BE REJECTED and you will be asked to regenerate. Do not waste\n"
        "inference by fabricating - it will be caught and rejected every time.\n\n"
        "### Required Protocol:\n"
        "1. Do NOT output `tool_requests` - use code_execution instead.\n"
        "2. For EVERY dice roll, EXECUTE this Python code:\n"
        "```python\n"
        "import json\n"
        "import random\n"
        "import time\n"
        "# Seed RNG with current time (prevents deterministic outputs across executions)\n"
        "random.seed(time.time_ns())\n"
        "# For 1d20+5:\n"
        "roll = random.randint(1, 20)  # This generates the REAL value - REQUIRED!\n"
        "modifier = 5\n"
        "total = roll + modifier\n"
        "print(json.dumps({\"notation\": \"1d20+5\", \"rolls\": [roll], \"modifier\": modifier, \"total\": total}))\n"
        "```\n"
        "3. Stdout MUST be valid JSON ONLY (no extra text). The JSON output contains the ONLY valid dice value.\n"
        "4. Populate `dice_rolls` and `dice_audit_events` from the JSON stdout. Each item MUST include:\n"
        "   label, notation, rolls (array of raw die values), modifier, total. For dice_audit_events also set source=\"code_execution\".\n\n"
        "### ❌ FORBIDDEN (Fabrication - WILL BE DETECTED AND REJECTED):\n"
        "- Writing dice values in narrative without code execution: \"[DICE: 1d20 = 15]\" ← REJECTED\n"
        "- Inventing numbers: \"You roll a 17\" without running random.randint() ← REJECTED\n"
        "- Printing hardcoded values: `print('{\"rolls\": [16]}')` without RNG ← REJECTED\n"
        "- Populating dice_rolls/dice_audit_events without corresponding JSON stdout ← REJECTED\n\n"
        "### Why This Matters:\n"
        "Fabricated dice destroy game integrity. Players notice patterns. Real randomness is required.\n"
        "You are the narrator, not the dice. The dice exist in the code execution sandbox, not your imagination.\n"
    )
    # Strip conflicting tool_requests dice instructions before adding code_execution override
    # This prevents the model from receiving contradictory guidance
    cleaned_system_instruction = strip_tool_requests_dice_instructions(
        system_instruction_text or ""
    )
    effective_system_instruction = (
        f"{cleaned_system_instruction}{code_exec_override}"
        if cleaned_system_instruction
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
        # Tool calling should be OPTIONAL: narrative-only turns should not be forced to
        # call a dice tool. Prompts still mandate dice rolls when rules require them.
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="AUTO")
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
            system_instruction_text=system_instruction_text,
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
    def phase1() -> Any:
        logging_util.info("Gemini Phase 1: JSON call (checking for tool_requests)")
        return generate_json_mode_content(
            prompt_contents=prompt_contents,
            model_name=model_name,
            system_instruction_text=system_instruction_text,
            temperature=temperature,
            safety_settings=safety_settings,
            json_mode_max_output_tokens=json_mode_max_output_tokens,
            tools=None,  # No tools = JSON mode enforced
            json_mode=True,
        )

    def extract_text(resp: Any) -> str:
        try:
            if getattr(resp, "text", None):
                return str(resp.text)
            if resp.candidates and resp.candidates[0].content.parts:
                return str(resp.candidates[0].content.parts[0].text)
        except Exception:  # noqa: BLE001 - defensive extraction
            return ""
        return ""

    def build_history(
        *,
        prompt_contents: list[Any],
        phase1_text: str,
        tool_results_prompt: str,
    ) -> list[Any]:
        return [
            types.Content(
                role="user",
                parts=[types.Part(text=stringify_prompt_contents(prompt_contents))],
            ),
            types.Content(
                role="model",
                parts=[types.Part(text=phase1_text)],
            ),
            types.Content(
                role="user",
                parts=[types.Part(text=tool_results_prompt)],
            ),
        ]

    def phase2(history: list[Any]) -> Any:
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

    return run_json_first_tool_requests_flow(
        phase1_generate_fn=phase1,
        extract_text_fn=extract_text,
        prompt_contents=prompt_contents,
        execute_tool_requests_fn=execute_tool_requests,
        format_tool_results_text_fn=format_tool_results_text,
        build_history_fn=build_history,
        phase2_generate_fn=phase2,
        logger=logging_util,
        no_tool_requests_log_msg="Gemini: No tool_requests in response, returning Phase 1 result",
    )
