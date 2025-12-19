# Unified Two-Phase Dice Architecture

**Date:** 2024-12-11
**Status:** Planning
**PR:** #2353
**Branch:** `claude/refactor-llm-to-code-01Sr4NxrZzuzRJ2XDSVFPm9s`

## Problem Statement

The pre-computed dice approach has fundamental limitations:
- Hardcoded mechanics (STR-based attacks, 1d8 damage for all weapons)
- Brittle keyword-based intent detection
- Exchanges "LLM hallucination" for "rigid defaults"

The LLM should decide what dice to roll (e.g., "Fireball" = 8d6 fire damage), not a regex parser.

## Root Cause: Gemini API Limitation

```
"Function calling with a response mime type: 'application/json' is unsupported"
```

**Sources:**
- https://github.com/google-gemini/deprecated-generative-ai-python/issues/515
- https://discuss.ai.google.dev/t/function-calling-with-a-response-mime-type-application-json-is-unsupported/105093

## Provider Capabilities

| Provider | Model | Function Calling | JSON Mode | Both Together |
|----------|-------|-----------------|-----------|---------------|
| **Gemini 3** | gemini-3-pro-preview | Yes | Yes | **YES** |
| Gemini 2.x | gemini-2.0/2.5-* | Yes | Yes | **NO** |
| Cerebras | all | Yes | Yes | Yes |
| OpenRouter | all | Yes | Yes | Yes |

**Key Discovery (Dec 2025):** Gemini 3 Pro supports code_execution + JSON mode together!
This means single-phase inference for Gemini 3, same as other providers.

## Solution: Provider-Specific Strategies

### Gemini 3 Pro: Single-Phase with Code Execution (PREFERRED)

```python
# ONE API call - model runs Python for dice, outputs JSON
response = model.generate_content(
    prompt,
    tools=[{"code_execution": {}}],
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": NarrativeResponseSchema
    }
)
# Model executes: import random; roll = random.randint(1,20) + 5
# Returns: {"narrative": "...", "dice_rolls": ["Attack: 1d20+5 = 18"], ...}
```

### Gemini 2.x: Two-Phase (tools → JSON)

```
Phase 1: tools=ON, json=OFF → LLM calls roll_attack()
Phase 2: tools=OFF, json=ON → LLM narrates with results
```

### Cerebras/OpenRouter: Tool Loop (unified config)

```
Phase 1: tools=ON, json=ON → LLM calls roll_attack()
Phase 2: tools=ON, json=ON → LLM narrates with results
```

### Config Matrix

| Provider | Model | Phases | tools | json | code_exec |
|----------|-------|--------|-------|------|-----------|
| Gemini 3 | gemini-3-pro-preview | **1** | ❌ | ✅ | ✅ |
| Gemini 2.x | gemini-2.0/2.5-* | 2 | ✅→❌ | ❌→✅ | ❌ |
| Cerebras | all | 1-2 | ✅ | ✅ | ❌ |
| OpenRouter | all | 1-2 | ✅ | ✅ | ❌ |

## Implementation Plan

### Phase 1: Revert Tool Loop Deletion

**Git command:**
```bash
git revert 9b70c1ff9  # "refactor(dice): delete all tool_use/code_execution infrastructure"
```

**Restores (~1,400 lines):**
- `DICE_ROLL_TOOLS` array (4 tools)
- `execute_dice_tool()` function
- `generate_content_with_tool_loop()` in cerebras_provider.py
- `generate_content_with_tool_loop()` in openrouter_provider.py
- `process_tool_calls()` in both providers
- `MODELS_WITH_TOOL_USE` set
- `get_dice_roll_strategy()` function

### Phase 2: Add Gemini Tool Loop

**New file or update:** `mvp_site/llm_providers/gemini_provider.py`

```python
def generate_content_with_tool_loop(
    prompt_contents: list,
    model_name: str,
    system_instruction_text: str,
    tools: list[dict],
    max_iterations: int = 5,
) -> GeminiResponse:
    """Two-phase inference for Gemini (tools and JSON mode separate)."""

    # Phase 1: Function calling (no JSON mode)
    response = generate_content(
        prompt_contents,
        model_name,
        system_instruction_text,
        tools=tools,
        response_mime_type=None,  # No JSON mode
    )

    tool_calls = response.get_tool_calls()
    if not tool_calls:
        # No tools called - need second call for JSON
        return generate_json_mode_content(...)

    # Execute tools
    tool_results = execute_tools(tool_calls)

    # Phase 2: JSON mode (no tools)
    return generate_json_mode_content(
        prompt_contents + tool_results,
        model_name,
        system_instruction_text,
        tools=None,  # No tools in phase 2
    )
```

### Phase 3: Delete Pre-Computed Logic

**Remove from `mvp_site/game_state.py`:**
- `detect_action_type()` (~90 lines)
- `compute_combat_results()` (~170 lines)
- `_compute_attack_roll()` (~100 lines)
- `_compute_damage_roll()` (~70 lines)
- `_compute_skill_check()` (~100 lines)
- Pattern constants (ATTACK_PATTERNS, etc.)

**Remove from `mvp_site/llm_service.py`:**
- Pre-computed results injection (~40 lines)

**Remove prompt instructions:**
- `pre_computed_results` section from game_state_instruction.md

**Delete test file:**
- `mvp_site/tests/test_precomputed_dice.py`

### Phase 4: Update Strategy Selection

**File:** `mvp_site/constants.py`

```python
# All models that support function calling
MODELS_WITH_TOOL_USE = {
    # Cerebras
    "qwen-3-235b-a22b-instruct-2507",
    "zai-glm-4.6",
    "llama-3.3-70b",
    # OpenRouter
    "meta-llama/llama-3.1-70b-instruct",
    # Gemini (needs special handling)
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-3-pro-preview",
}

def get_provider_for_model(model_name: str) -> str:
    """Determine provider from model name."""
    if model_name.startswith("gemini"):
        return "gemini"
    if model_name in CEREBRAS_MODELS:
        return "cerebras"
    return "openrouter"
```

### Phase 5: Update llm_service.py Call Site

```python
def _call_llm_api(...):
    provider = get_provider_for_model(model_name)

    if provider == "gemini":
        return gemini_provider.generate_content_with_tool_loop(
            prompt_contents, model_name, system_instruction_text,
            tools=DICE_ROLL_TOOLS
        )
    elif provider == "cerebras":
        return cerebras_provider.generate_content_with_tool_loop(
            prompt_contents, model_name, system_instruction_text,
            tools=DICE_ROLL_TOOLS
        )
    else:
        return openrouter_provider.generate_content_with_tool_loop(
            prompt_contents, model_name, system_instruction_text,
            tools=DICE_ROLL_TOOLS
        )
```

## Files to Modify

| File | Action | Lines |
|------|--------|-------|
| game_state.py | Revert (restore tools) + Delete pre-computed | +200, -530 |
| constants.py | Revert (restore strategy) | +50 |
| cerebras_provider.py | Revert (restore tool loop) | +150 |
| openrouter_provider.py | Revert (restore tool loop) | +150 |
| gemini_provider.py | Add tool loop | +100 |
| llm_service.py | Update call site, remove pre-computed injection | +20, -40 |
| game_state_instruction.md | Remove pre_computed_results, restore tool instructions | ~30 |
| test_precomputed_dice.py | Delete | -377 |
| test_code_execution_dice_rolls.py | Revert (restore tool tests) | +500 |

## Test Plan

1. **Unit tests:** Tool execution functions
2. **Integration tests:** Full tool loop for each provider
3. **Smoke tests:** Real API calls with dice rolling
4. **Regression:** Existing narrative generation still works

## Acceptance Criteria

- [ ] LLM can call `roll_attack()` with correct parameters
- [ ] LLM can call `roll_dice("8d6")` for Fireball
- [ ] Tool results are correctly injected into conversation
- [ ] Final response is valid JSON with dice_rolls populated
- [ ] Works for Gemini, Cerebras, and OpenRouter
- [ ] All existing tests pass

## Rollback Plan

If tool loops cause issues:
```bash
git revert HEAD  # Undo the revert
```

Pre-rolled dice (without pre-computed logic) remains as fallback.
