# PR #2353 Cleanup Plan - Code Execution Removal

## Phase 0: Context Assessment

**Your Comments (4 items):**
1. `"gemini-2.5-flash"` should use constant `GEMINI_2_5_FLASH` not hardcoded string
2. Documentation claiming "Gemini 2.0/3.0 support code_execution + JSON together" is disputed - needs verification
3. `MODELS_WITH_TOOL_USE` and related code may be removable since we precompute
4. `get_dice_roll_strategy()` can be deleted since always returns "precompute"

## Phase 1: Research Findings

**Gemini API Code Execution + JSON Mode:**

| Source | Finding |
|--------|---------|
| [Google Issue #706](https://github.com/googleapis/python-genai/issues/706) | "Function calling with response mime type: 'application/json' is unsupported" |
| [Google Issue #515](https://github.com/google-gemini/deprecated-generative-ai-python/issues/515) | Same error message confirmed |
| [Structured Output Docs](https://ai.google.dev/gemini-api/docs/structured-output) | "Gemini 3 lets you combine Structured Outputs with built-in tools, including...Code Execution" (Gemini 3 only!) |
| Smoke test failure | Gemini 2.0 flash returned: "controlled generation is not supported with Code Execution tool" |

**Conclusion:** You were RIGHT to question this. My original documentation was incorrect. **NO Gemini model before Gemini 3** supports code_execution + JSON mode together. However, since we now use **pre-rolled dice** injected into prompts, code_execution is unnecessary anyway.

## Phase 2: Files Changed in PR (16 files, +2760/-148 lines)

| File | Lines Changed | Code Execution Related? | Action |
|------|---------------|------------------------|--------|
| `constants.py` | +102 | **YES** - strategy sets, get_dice_roll_strategy | **CLEANUP** |
| `gemini_provider.py` | +44 | **YES** - enable_code_execution param | **CLEANUP** |
| `cerebras_provider.py` | +264 | **YES** - tool loop, process_tool_calls | **KEEP** (tool_use for future) or **CLEANUP** |
| `openrouter_provider.py` | +253 | **YES** - tool loop, process_tool_calls | **KEEP** or **CLEANUP** |
| `game_state.py` | +893 | **PARTIAL** - DICE_ROLL_TOOLS, execute_dice_tool, generate_pre_rolled_dice | **CLEANUP tools, KEEP pre-rolled** |
| `llm_service.py` | +31 | **PARTIAL** - pre_rolled_dice injection | **KEEP** |
| `llm_request.py` | +8 | NO - just pre_rolled_dice field | **KEEP** |
| `test_code_execution_dice_rolls.py` | +751 | **YES** - tool loop tests | **CLEANUP tests** |
| `test_game_state.py` | +379 | NO - D&D mechanics tests | **KEEP** |
| `clock_skew_credentials.py` | +16 | NO - testing fix | **KEEP** |
| `game_state_instruction.md` | +52 | NO - pre-rolled dice prompts | **KEEP** |
| `mechanics_system_instruction.md` | +28 | NO - prompts | **KEEP** |
| `narrative_system_instruction.md` | +9 | NO - prompts | **KEEP** |
| `settings.html` | +4 | NO - gemini 2.5 option | **KEEP** (but fix constant) |
| `api.js` | +44 | NO - error handling | **KEEP** |
| `app.js` | +30 | NO - error handling | **KEEP** |

## Phase 3: Cleanup Plan

### 3.1 `mvp_site/constants.py` - MAJOR CLEANUP

**DELETE:**
- `MODELS_WITH_CODE_EXECUTION` set (empty, deprecated)
- `MODELS_WITH_TOOL_USE` set (not used with precompute)
- `MODELS_PRECOMPUTE_ONLY` set (empty, not used)
- `get_dice_roll_strategy()` function (always returns "precompute")
- ASCII table documentation (inaccurate anyway)

**FIX:**
- Line 51: `"gemini-2.5-flash"` → use constant `GEMINI_2_5_FLASH` (define it first)

**KEEP:**
- `ALLOWED_GEMINI_MODELS` list (needed for settings)
- `PREMIUM_GEMINI_MODELS` list
- `GEMINI_3_ALLOWED_USERS` list

### 3.2 `mvp_site/llm_providers/gemini_provider.py` - SIMPLIFY

**DELETE:**
- `enable_code_execution` parameter from `generate_json_mode_content()`
- All code_execution related comments and logging
- `from mvp_site import constants` import (if no longer needed)

**KEEP:**
- JSON mode generation (response_mime_type)

### 3.3 `mvp_site/llm_providers/cerebras_provider.py` - DECISION NEEDED

**Option A: Full Cleanup (Recommended for simplicity)**
- DELETE: `tool_calls` property, `get_tool_calls()`, `process_tool_calls()`, `generate_content_with_tool_loop()`
- DELETE: `tools` parameter from `generate_content()`
- This removes ~150 lines of unused code

**Option B: Keep for Future**
- KEEP all tool_use infrastructure but document as "reserved for future use"
- Risk: Dead code that may rot

### 3.4 `mvp_site/llm_providers/openrouter_provider.py` - SAME AS CEREBRAS

Same decision as 3.3 - mirror the approach.

### 3.5 `mvp_site/game_state.py` - PARTIAL CLEANUP

**DELETE:**
- `DICE_ROLL_TOOLS` list (tool definitions, ~80 lines)
- `execute_dice_tool()` function (~50 lines)
- Related imports for tool execution

**KEEP:**
- `generate_pre_rolled_dice()` function (this is the new approach)
- `DiceRollResult` dataclass
- All D&D mechanics (roll_dice, attack calculations, etc.)

### 3.6 `mvp_site/llm_service.py` - MINOR CLEANUP

**DELETE:**
- Any imports of `DICE_ROLL_TOOLS` or tool-related constants
- Any remaining references to `get_dice_roll_strategy()`

**KEEP:**
- Pre-rolled dice injection logic
- Direct LLM calls (no tool loops)

### 3.7 `mvp_site/tests/test_code_execution_dice_rolls.py` - SIGNIFICANT CLEANUP

**DELETE:**
- `TestToolLoopAllCodePaths` class (tests tool loop paths we're removing)
- `TestCerebrasToolUseIntegration` class (if removing tool_use)
- `TestOpenRouterToolUseIntegration` class (if removing tool_use)

**RENAME FILE:** `test_dice_rolls.py` (since no more code_execution)

**KEEP:**
- `TestHybridDiceRollSystem` (rename to TestDiceRollSystem)
- `TestPreRolledDiceGeneration` tests
- `TestLLMServiceToolIntegration` → rename to `TestLLMServiceIntegration`

### 3.8 `mvp_site/templates/settings.html` - MINOR FIX

**FIX:**
- Use `GEMINI_2_5_FLASH` constant reference in template (or just keep string since Jinja)

## Phase 4: Execution Order

1. **Define constant** `GEMINI_2_5_FLASH = "gemini-2.5-flash"` in constants.py
2. **Delete deprecated code** from constants.py (strategy function, sets)
3. **Simplify gemini_provider.py** (remove enable_code_execution param)
4. **Delete tool infrastructure** from cerebras_provider.py and openrouter_provider.py
5. **Delete DICE_ROLL_TOOLS** from game_state.py
6. **Clean up llm_service.py** imports
7. **Clean up tests** - delete tool loop tests, rename file
8. **Run tests** to verify nothing breaks
9. **Update PR description** with accurate documentation

## Phase 5: Estimated Deletions

| File | Lines Deleted |
|------|---------------|
| constants.py | ~60 |
| gemini_provider.py | ~20 |
| cerebras_provider.py | ~150 |
| openrouter_provider.py | ~150 |
| game_state.py | ~130 |
| test_code_execution_dice_rolls.py | ~400 |
| **TOTAL** | **~910 lines** |

## Decision Points for User

1. **Keep or Delete tool_use infrastructure?**
   - DELETE = cleaner code, -300 lines
   - KEEP = future flexibility but dead code

2. **Rename test file?**
   - `test_code_execution_dice_rolls.py` → `test_dice_rolls.py`

3. **Fix gemini-2.5-flash constant or leave as string?**
   - Constants are cleaner but template uses strings anyway

---

**AWAITING APPROVAL** to proceed with cleanup implementation.
