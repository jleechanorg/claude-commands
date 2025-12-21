# Smart Skill Check Testing (DICE-ayy Regression Tests)

## Purpose

This test suite specifically validates the **DICE-ayy gap fix** - ensuring the system catches dice fabrication when the LLM makes intelligent skill check decisions WITHOUT explicit user requests.

## The DICE-ayy Gap

**What it was:**
- User input: `"Demand Lantry's Release"` (NO combat keywords, NO "Make a check")
- LLM decision: Smartly determines Intimidation check is needed
- OLD SYSTEM: Only checked user input for combat keywords → missed this → dice fabricated
- NEW SYSTEM: Also scans LLM narrative for dice patterns → catches fabrication

**Why existing tests missed it:**
- All existing tests use explicit combat keywords OR "Make a check" language
- The gap was about SMART LLM DECISIONS without those triggers

## Test Coverage

### Scenarios Tested

All scenarios have:
- ✅ NO combat keywords in user input
- ✅ NO explicit "Make a check" requests
- ✅ LLM must intelligently decide skill check needed
- ✅ Dice MUST come from code_execution, not fabrication

**Social Skill Checks:**
1. **Intimidation (implicit)**: `"I demand the guard stand down immediately and let us pass."`
2. **Persuasion (implicit)**: `"I try to convince the merchant to lower the price by 50 gold pieces."`
3. **Deception (implicit)**: `"I tell the captain a convincing story about why we're here."`

**Investigation Checks:**
4. **Perception (implicit)**: `"I carefully examine the bookshelf for anything unusual."`
5. **Insight (implicit)**: `"I watch the noble's reactions carefully as he speaks."`

### Validation Logic

For each scenario, the test validates:

1. **Test Integrity**: User input has NO combat keywords or explicit check requests
2. **LLM Decision**: Dice rolls present (LLM decided check was needed)
3. **Dice Provenance**:
   - **Gemini (code_execution)**: `debug_info.code_execution_used = True` (or stdout evidence)
   - **Native two-phase**: `tool_results` present (requires CAPTURE_EVIDENCE)
4. **Executable Code Parts** (Gemini only): `debug_info.executable_code_parts > 0` when present
5. **No Integrity Violation**: `debug_info.dice_integrity_violation = False`
6. **Check Type Match**: Dice rolls contain expected check type (Intimidation, Persuasion, etc.)

**CRITICAL FAILURE**:
- Gemini code_execution dice without code_execution evidence
- Native two-phase dice without tool_results

## Usage

### Quick Test (Local MCP Server)

```bash
# Assumes local MCP server is already running on 8001
cd testing_mcp
python test_smart_skill_checks_real_api.py --server-url http://127.0.0.1:8001
```

### Auto-Start Local Server (Mock Mode)

```bash
cd testing_mcp
python test_smart_skill_checks_real_api.py --start-local
```

Note: The local server launched by this script enables CAPTURE_EVIDENCE and
CAPTURE_TOOL_RESULTS automatically so native two-phase models can be validated
via tool_results.

### Real API Testing

```bash
# Requires GEMINI_API_KEY and CEREBRAS_API_KEY
cd testing_mcp
python test_smart_skill_checks_real_api.py --start-local --real-services
```

### With Evidence Collection

```bash
cd testing_mcp
python test_smart_skill_checks_real_api.py --start-local --real-services --evidence

# Evidence saved to: testing_mcp/evidence/smart_skill_checks/
```

### Custom Models

```bash
cd testing_mcp
python test_smart_skill_checks_real_api.py --start-local --real-services \
  --models "gemini-3-flash-preview,qwen-3-235b-a22b-instruct-2507"
```

### Relaxed Mode (Allow No Dice)

```bash
cd testing_mcp
python test_smart_skill_checks_real_api.py --start-local --allow-no-dice
```

## Expected Output

### Success (All Tests Pass)

```
🧪 Running 10 smart skill check tests
   Models: gemini-3-flash-preview, qwen-3-235b-a22b-instruct-2507
   Scenarios: 5
   Real services: True
======================================================================

📦 Testing model: gemini-3-flash-preview
----------------------------------------------------------------------
✅ Intimidation (implicit): 1 rolls, code_execution=True
✅ Persuasion (implicit): 1 rolls, code_execution=True
✅ Deception (implicit): 1 rolls, code_execution=True
✅ Perception (implicit): 1 rolls, code_execution=True
✅ Insight (implicit): 1 rolls, code_execution=True

📦 Testing model: qwen-3-235b-a22b-instruct-2507
----------------------------------------------------------------------
✅ Intimidation (implicit): 1 rolls, tool_results=True
✅ Persuasion (implicit): 1 rolls, tool_results=True
✅ Deception (implicit): 1 rolls, tool_results=True
✅ Perception (implicit): 1 rolls, tool_results=True
✅ Insight (implicit): 1 rolls, tool_results=True

======================================================================
📊 Test Summary: 10/10 passed
✅ ALL TESTS PASSED - DICE-ayy gap detection working
```

### Failure (DICE-ayy Regression Detected)

```
📦 Testing model: gemini-3-flash-preview
----------------------------------------------------------------------
❌ Intimidation (implicit)
   Input: I demand the guard stand down immediately and let us pass.
   Error: Expected tool_results for native_two_phase dice rolls; enable CAPTURE_EVIDENCE on the server
```

## Integration with CI/CD

Add to your test suite:

```bash
# In .github/workflows/test.yml or similar

- name: DICE-ayy Regression Test
  run: |
    cd testing_mcp
    python test_smart_skill_checks_real_api.py --start-local --real-services
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    CEREBRAS_API_KEY: ${{ secrets.CEREBRAS_API_KEY }}
```

## Evidence Collection

When `--evidence` flag is used, detailed JSON files are saved for each test:

```json
{
  "timestamp": "20251220_183045",
  "model_id": "gemini-3-flash-preview",
  "scenario_name": "Intimidation (implicit)",
  "user_input": "I demand the guard stand down immediately and let us pass.",
  "validation_passed": true,
  "validation_errors": [],
  "dice_rolls": ["Intimidation: 1d20+5 = 18"],
  "debug_info": {
    "code_execution_used": true,
    "executable_code_parts": 1,
    "dice_integrity_violation": false
  },
  "narrative": "The guard's eyes widen as you speak with commanding authority..."
}
```

## Troubleshooting

### "No dice rolls" Error

If the LLM doesn't make a skill check decision:
- Check that the campaign setting includes context for social interactions
- Verify the character has relevant social stats (CHA, WIS)
- Ensure the LLM provider is configured correctly
- Use `--allow-no-dice` if you want to ignore missing dice rolls

### "DICE-ayy REGRESSION" Error

This is a **CRITICAL FAILURE** indicating:
- The narrative dice pattern detection is broken
- Dice are being fabricated without the correct evidence
- The DICE-ayy gap has returned

**Action Required**:
1. Check `mvp_site/llm_service.py:_detect_narrative_dice_fabrication()`
2. Verify reprompt loop is triggering on fabricated dice
3. Review recent changes to dice enforcement system

## Related Files

- `test_dice_rolls_comprehensive.py` - Combat and explicit check testing
- `test_social_encounter_real_api.py` - Social encounters with explicit checks
- `mvp_site/llm_service.py` - Dice enforcement implementation
- `scripts/audit_dice_rolls.py` - Production campaign audit tool

## Commit Reference

- **DICE-ayy Fix**: commit `b51e7cb07` (2025-12-20)
- **Implementation**: Added `_detect_narrative_dice_fabrication()` function
- **Coverage Gap**: Identified from Tyranny campaign audit showing 100% fabrication rate
