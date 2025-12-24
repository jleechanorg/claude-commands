# PR #2551 RED Test Evidence

## Summary

This document proves the RED-GREEN TDD approach was validated for the system prompt 
enforcement warning tests added to PR #2551.

## Test Added

**File:** `mvp_site/tests/test_code_execution_dice_rolls.py`
**Class:** `TestSystemPromptEnforcementWarning`

### Test 1: `test_RED_enforcement_warning_is_passed_to_llm`
Verifies these phrases are in the system prompt:
- "ENFORCEMENT WARNING"
- "IS INSPECTED"
- "WILL BE REJECTED"

### Test 2: `test_RED_fabrication_example_is_documented`
Verifies these phrases are in the system prompt:
- "hardcoded"
- "without RNG"

## RED State Evidence

**OLD system prompt (before PR):**
```
## 🎲 CRITICAL: DICE VALUES ARE UNKNOWABLE (Gemini 3 code_execution mode)

**ABSOLUTE RULE: You CANNOT know dice values without executing code.**

### Required Protocol:
1. Do NOT output tool_requests - use code_execution instead.
2. For EVERY dice roll, EXECUTE this Python code...

### ❌ FORBIDDEN (Fabrication):
- Writing dice values in narrative without code execution: "[DICE: 1d20 = 15]" ← INVALID
- Inventing numbers: "You roll a 17" without running random.randint() ← INVALID
```

**Test results with OLD prompt:**
```
❌ FAIL (RED): "ENFORCEMENT WARNING" in OLD system prompt: False
❌ FAIL (RED): "IS INSPECTED" in OLD system prompt: False
❌ FAIL (RED): "WILL BE REJECTED" in OLD system prompt: False
❌ FAIL (RED): "hardcoded" in OLD system prompt: False
❌ FAIL (RED): "without RNG" in OLD system prompt: False

Result: Tests would FAIL with old code - enforcement warning was missing!
```

## GREEN State Evidence

**NEW system prompt (after PR):**
```
### 🚨 ENFORCEMENT WARNING:
Your code IS INSPECTED. If `random.randint()` is not found in your executed code,
your response WILL BE REJECTED and you will be asked to regenerate. Do not waste
inference by fabricating - it will be caught and rejected every time.

### ❌ FORBIDDEN (Fabrication - WILL BE DETECTED AND REJECTED):
- Writing dice values in narrative without code execution: "[DICE: 1d20 = 15]" ← REJECTED
- Inventing numbers: "You roll a 17" without running random.randint() ← REJECTED
- Printing hardcoded values: `print('{"rolls": [16]}')` without RNG ← REJECTED
- Populating dice_rolls/dice_audit_events without corresponding JSON stdout ← REJECTED
```

**Test results with NEW prompt:**
```
✅ PASS: test_RED_enforcement_warning_is_passed_to_llm
✅ PASS: test_RED_fabrication_example_is_documented

======================== 2 passed, 5 warnings in 0.68s =========================
```

## Conclusion

The RED-GREEN TDD approach was successfully applied:
1. RED tests were designed to fail without the enforcement warning
2. The enforcement warning was added to the system prompt
3. GREEN tests now pass with the new system prompt

## Timestamp
Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Commit
$(git rev-parse HEAD)
