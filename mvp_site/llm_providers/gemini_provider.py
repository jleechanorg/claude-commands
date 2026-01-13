"""Gemini provider implementation isolated from llm_service.

Uses response_json_schema for structured output enforcement.
See: https://ai.google.dev/gemini-api/docs/structured-output
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from google import genai
from google.genai import types

from mvp_site import constants, logging_util
from mvp_site.dice import DICE_ROLL_TOOLS
from mvp_site.game_state import execute_tool_requests
from mvp_site.llm_providers import gemini_code_execution
from mvp_site.llm_providers.provider_utils import stringify_prompt_contents

# NOTE: Gemini response_schema is NOT used due to strict property requirements
# Gemini requires ALL object types to have non-empty properties - no dynamic keys allowed
# We rely on response_mime_type="application/json" + prompt instruction instead
# Post-response validation in narrative_response_schema.py handles structure enforcement


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
        "safety_settings": safety_settings,  # Must be inside GenerateContentConfig
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
                continue  # Handled in config
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


def _build_gemini_tools(tool_defs: list[dict]) -> list[types.Tool]:
    """Convert tool definitions into Gemini SDK tools."""
    gemini_tools: list[types.Tool] = []
    for tool in tool_defs:
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
    return gemini_tools


def _extract_function_calls(response: Any) -> list[dict[str, Any]]:
    """Extract Gemini function_call parts into tool request dicts."""
    tool_requests: list[dict[str, Any]] = []
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) if content is not None else None
        if not parts:
            continue
        for part in parts:
            call = getattr(part, "function_call", None)
            if call is None:
                continue
            name = getattr(call, "name", None)
            args = getattr(call, "args", None)
            if not isinstance(name, str) or not name:
                continue
            if isinstance(args, dict):
                normalized_args = args
            elif isinstance(args, str):
                try:
                    normalized_args = json.loads(args)
                except json.JSONDecodeError:
                    normalized_args = {}
            else:
                normalized_args = {}
            tool_requests.append({"tool": name, "args": normalized_args})
    return tool_requests


def generate_content_with_native_tools(
    prompt_contents: list[Any],
    model_name: str,
    system_instruction_text: str | None,
    temperature: float,
    safety_settings: list[Any],
    json_mode_max_output_tokens: int,
) -> Any:
    """Run Gemini native two-phase tool calling to preserve JSON output."""
    client = get_client()
    config = types.GenerateContentConfig(
        max_output_tokens=json_mode_max_output_tokens,
        temperature=temperature,
        safety_settings=safety_settings,
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="AUTO")
        ),
    )
    gemini_tools = _build_gemini_tools(DICE_ROLL_TOOLS)
    if gemini_tools:
        config.tools = gemini_tools
    if system_instruction_text:
        config.system_instruction = system_instruction_text

    response_1 = client.models.generate_content(
        model=model_name,
        contents=prompt_contents,
        config=config,
    )

    tool_requests = _extract_function_calls(response_1)

    if tool_requests:
        # Execute tools and build proper conversation history for Phase 2
        tool_results = execute_tool_requests(tool_requests)
        if len(tool_results) != len(tool_requests):
            logging_util.warning(
                "Gemini native tool loop mismatch: tool_requests=%s tool_results=%s; "
                "building function responses from tool_results only to avoid mispairing",
                len(tool_requests),
                len(tool_results),
            )

        # Build Phase 2 contents preserving conversation context:
        # 1. Original user message(s)
        # 2. Model's Phase 1 response (with function calls)
        # 3. Function responses for each tool call
        phase2_contents: list[Any] = list(prompt_contents)  # Original user input

        # Add model's Phase 1 response (preserves function call context)
        phase1_content = getattr(
            getattr(response_1, "candidates", [None])[0], "content", None
        )
        if phase1_content:
            phase2_contents.append(phase1_content)

        # Add function responses as user content with FunctionResponse parts
        function_response_parts = []
        for tool_result in tool_results:
            if not isinstance(tool_result, dict):
                continue
            tool_name = tool_result.get("tool")
            if not isinstance(tool_name, str) or not tool_name:
                continue
            inner_result = tool_result.get("result", tool_result)
            function_response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={"result": inner_result},
                )
            )
        if function_response_parts:
            phase2_contents.append(
                types.Content(role="user", parts=function_response_parts)
            )

        phase2_prompt_contents = phase2_contents
    else:
        phase2_prompt_contents = prompt_contents

    return generate_json_mode_content(
        prompt_contents=phase2_prompt_contents,
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        safety_settings=safety_settings,
        json_mode_max_output_tokens=json_mode_max_output_tokens,
    )


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
        "Hardcoded dice outputs (e.g., `print('{\"rolls\": [16]}')` without RNG) are rejected.\n\n"
        "### 🚨 ENFORCEMENT WARNING:\n"
        "Your code IS INSPECTED. If `random.randint()` is not found in your executed code,\n"
        "your response WILL BE REJECTED and you will be asked to regenerate. Do not waste\n"
        "inference by fabricating - it will be caught and rejected every time.\n\n"
        "### Required Protocol:\n"
        "1. Do NOT output `tool_requests` - use code_execution instead.\n"
        "2. For EVERY dice roll, EXECUTE Python code with the appropriate format:\n\n"
        "**Attack Roll (vs AC):**\n"
        "```python\n"
        "import json, random, time\n"
        "random.seed(time.time_ns())\n"
        "roll = random.randint(1, 20)\n"
        "modifier = 5\n"
        "total = roll + modifier\n"
        "ac = 15  # Target AC\n"
        'print(json.dumps({"notation": "1d20+5", "rolls": [roll], "modifier": modifier, "total": total, "label": "Longsword Attack", "ac": ac, "hit": total >= ac}))\n'
        "```\n\n"
        "**Skill Check (DC + dc_reasoning REQUIRED):**\n"
        "```python\n"
        "import json, random, time\n"
        "random.seed(time.time_ns())\n"
        "# ⚠️ Set DC and reasoning BEFORE rolling - proves fairness\n"
        "dc = 15\n"
        'dc_reasoning = "guard is alert but area is noisy"  # WHY this DC\n'
        "roll = random.randint(1, 20)  # Roll AFTER DC is set\n"
        "modifier = 3\n"
        "total = roll + modifier\n"
        "success = total >= dc\n"
        'print(json.dumps({"notation": "1d20+3", "rolls": [roll], "modifier": modifier, "total": total, "label": "Stealth", "dc": dc, "dc_reasoning": dc_reasoning, "success": success}))\n'
        "```\n\n"
        "**Saving Throw (DC + dc_reasoning REQUIRED):**\n"
        "```python\n"
        "import json, random, time\n"
        "random.seed(time.time_ns())\n"
        "# ⚠️ Set DC and reasoning BEFORE rolling - proves fairness\n"
        "dc = 15\n"
        'dc_reasoning = "Dragon breath weapon (CR 10, standard DC 15)"  # WHY this DC\n'
        "roll = random.randint(1, 20)  # Roll AFTER DC is set\n"
        "modifier = 4\n"
        "total = roll + modifier\n"
        "success = total >= dc\n"
        'print(json.dumps({"notation": "1d20+4", "rolls": [roll], "modifier": modifier, "total": total, "label": "CON Save", "dc": dc, "dc_reasoning": dc_reasoning, "success": success}))\n'
        "```\n\n"
        "### ⚠️ DC Reasoning is MANDATORY for Skill Checks and Saving Throws\n"
        "The `dc_reasoning` field proves you set the DC BEFORE seeing the roll result.\n"
        "This prevents 'just in time' DC manipulation to fit narratives.\n\n"
    )

    cleaned_system_instruction = strip_tool_requests_dice_instructions(
        system_instruction_text or ""
    ).rstrip()
    if cleaned_system_instruction:
        system_instruction_text = f"{cleaned_system_instruction}{code_exec_override}"
    else:
        system_instruction_text = code_exec_override.lstrip()

    return generate_json_mode_content(
        prompt_contents=prompt_contents,
        model_name=model_name,
        system_instruction_text=system_instruction_text,
        temperature=temperature,
        safety_settings=safety_settings,
        json_mode_max_output_tokens=json_mode_max_output_tokens,
        enable_code_execution=True,
    )
