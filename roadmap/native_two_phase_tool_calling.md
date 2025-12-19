# Native Two-Phase Tool Calling Implementation Plan

**Bead**: `worktree_worker3-82m`
**PR**: #2353
**Date**: 2025-12-16

## Problem Statement

Current architecture uses prompt-based `tool_requests` in JSON schema, which:
- Works for Qwen-3 (follows prompt instructions)
- Fails for GLM-4.6 (trained for native tool calling, ignores prompt)
- API limitation: `tools` + `response_format` cannot be used together

## Solution: Native Two-Phase Tool Calling

### Strategy Matrix

| Model | Strategy | Phases | Reason |
|-------|----------|--------|--------|
| gemini-2.0-flash | `code_execution` | 1 | Supports code_execution + JSON together |
| gemini-3-pro-preview | `code_execution` | 1 | Supports code_execution + JSON together |
| gemini-2.5-flash | `native_two_phase` | 2 | Cannot combine code_execution + JSON |
| All Cerebras | `native_two_phase` | 2 | Use native `tools` API |
| All OpenRouter | `native_two_phase` | 2 | Use native `tools` API |

### Two-Phase Flow

```
Phase 1: Native Tool Calling
┌─────────────────────────────────────────────────────┐
│ Request:                                            │
│   - tools = DICE_ROLL_TOOLS                        │
│   - tool_choice = "auto"                           │
│   - NO response_format                             │
│                                                     │
│ Response:                                           │
│   - message.tool_calls = [{name, arguments}, ...]  │
│   - OR message.content (no tools needed)           │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
              Execute tool_calls locally
              (roll_dice, roll_attack, etc.)
                         │
                         ▼
Phase 2: JSON Schema Response
┌─────────────────────────────────────────────────────┐
│ Request:                                            │
│   - response_format = JSON_SCHEMA                  │
│   - messages include tool results                  │
│   - NO tools parameter                             │
│                                                     │
│ Response:                                           │
│   - Structured JSON with narrative, dice_rolls,    │
│     entities, game_state_update, etc.              │
└─────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Update constants.py
- Simplify `get_dice_roll_strategy()` to return only `code_execution` or `native_two_phase`
- Remove `MODELS_WITH_TOOL_USE` complexity

### Step 2: Update cerebras_provider.py
- Add `generate_content_with_native_tools()` function
- Handle native `tool_calls` response structure
- Execute tools and build Phase 2 request

### Step 3: Update openrouter_provider.py
- Add `generate_content_with_native_tools()` function
- Same pattern as Cerebras

### Step 4: Update gemini_provider.py
- Add `native_two_phase` support for gemini-2.5-flash
- Keep `code_execution` for 2.0/3.0

### Step 5: Update llm_service.py
- Route to correct strategy based on `get_dice_roll_strategy()`

### Step 6: Update tests
- Add tests for native two-phase flow
- Verify GLM-4.6 produces dice rolls

## Files to Modify

| File | Changes |
|------|---------|
| `mvp_site/constants.py` | Simplify strategy selection |
| `mvp_site/llm_providers/cerebras_provider.py` | Add native tools flow |
| `mvp_site/llm_providers/openrouter_provider.py` | Add native tools flow |
| `mvp_site/llm_providers/gemini_provider.py` | Add native_two_phase for 2.5 |
| `mvp_site/llm_service.py` | Route to strategies |
| `mvp_site/tests/test_code_execution_dice_rolls.py` | Update tests |

## Acceptance Criteria

- [x] All Cerebras models use native tool calling
- [x] All OpenRouter models use native tool calling
- [x] Gemini 2.0/3.0 keep single-phase code_execution
- [x] Gemini 2.5 uses native two-phase
- [ ] GLM-4.6 produces dice rolls in combat (requires smoke test validation)
- [ ] Smoke tests pass for all providers (requires live testing)
- [x] No regression in existing functionality (50 tests passing)

## Rollback Plan

If issues arise:
1. Revert to `tool_requests` JSON schema approach
2. Remove GLM-4.6 from `MODELS_WITH_TOOL_USE` (falls back to precompute)
