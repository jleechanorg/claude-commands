# Guardrails Test Findings - Outcome Declaration Detection

**Date**: 2026-01-10  
**Test**: `testing_mcp/test_outcome_declaration_guardrails.py`  
**Evidence**: `/tmp/worldarchitect.ai/handoff-llm_guardrails_validation-merge/outcome_declaration_guardrails_v2/20260110T033614Z/`

## Executive Summary

Test results show **guardrails are NOT being enforced** by the LLM. Only 3/8 scenarios passed (37.5% pass rate). The LLM is accepting outcome declarations instead of rejecting them.

## Test Results

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Combat - Instant Kill Declaration | REJECT | ACCEPTED | ❌ FAIL |
| Combat - Attempt (Valid) | ACCEPT | ACCEPTED | ✅ PASS |
| Combat - Past Tense Outcome | REJECT | ACCEPTED | ❌ FAIL |
| Social - NPC Decision Declaration | REJECT | REFRAMED | ❌ FAIL |
| Social - Attempt (Valid) | ACCEPT | ACCEPTED | ✅ PASS |
| Exploration - Finding Declaration | REJECT | REFRAMED | ❌ FAIL |
| Exploration - Attempt (Valid) | ACCEPT | ACCEPTED | ✅ PASS |
| Combat - Future Tense Outcome | REJECT | ACCEPTED | ❌ FAIL |

**Pass Rate**: 3/8 (37.5%)

## Key Findings

### 1. Outcome Declarations Are Being Accepted

**Example 1: Instant Kill**
- **Input**: "It pierces the guard's throat instantly killing him"
- **Expected**: Rejection with message asking for attempt
- **Actual**: LLM narrated the kill: *"the steel finds the gap in his leather collar... There is no struggle—only the wet slide of metal and the heavy thud of a body hitting the forest floor"*
- **Status**: ❌ FAIL - Outcome declaration accepted

**Example 2: Past Tense Outcome**
- **Input**: "My sword slices through, and he falls dead"
- **Expected**: Rejection
- **Actual**: LLM narrated: *"It falls with a wet thud onto the forest floor"*
- **Status**: ❌ FAIL - Outcome declaration accepted

### 2. Some Declarations Are Reframed (Not Rejected)

**Example: Social Decision**
- **Input**: "The king agrees with my proposal"
- **Expected**: Rejection
- **Actual**: LLM reframed as attempt and rolled dice (DC 15, Roll 6 = Failure)
- **Status**: ❌ FAIL - Should reject, not reframe

**Example: Finding Declaration**
- **Input**: "I find the hidden treasure"
- **Expected**: Rejection
- **Actual**: LLM reframed as "Search for hidden treasure" and rolled dice
- **Status**: ❌ FAIL - Should reject, not reframe

### 3. Valid Attempts Work Correctly

All three valid attempt scenarios passed:
- ✅ "I try to pierce the goblin's throat" → Processed correctly
- ✅ "I try to convince the king to help us" → Processed correctly
- ✅ "I search the room for traps" → Processed correctly

## Root Cause Analysis

### Prompt Is Loaded

Evidence shows `narrative_system_instruction.md` is loaded when `selected_prompts=["narrative", "mechanics"]`:
- System instruction files: `['prompts/master_directive.md', 'prompts/character_creation_instruction.md', 'prompts/dnd_srd_instruction.md', 'prompts/mechanics_system_instruction.md', 'prompts/narrative_system_instruction.md']`
- System instruction char count: ~51,782 chars

### Guardrails Section Exists

The guardrails section is present in `mvp_site/prompts/narrative_system_instruction.md` (lines 173-241):
- ✅ OUTCOME DECLARATION DETECTION section exists
- ✅ Examples match test scenarios
- ✅ Rejection response template provided

### Why Guardrails Aren't Working

**Hypothesis 1: Prompt Position**
- Guardrails section is at line 173, after ~170 lines of other content
- LLMs may prioritize earlier instructions
- **Recommendation**: Move guardrails section earlier in prompt (after ESSENTIALS, before other sections)

**Hypothesis 2: Instruction Strength**
- Current instruction: "**REJECT** and ask for an attempt"
- May not be strong enough for LLM to override narrative generation instincts
- **Recommendation**: Strengthen language with explicit "DO NOT NARRATE" and "STOP IMMEDIATELY"

**Hypothesis 3: Example Confusion**
- Examples in prompt match test inputs exactly
- LLM may see examples as patterns to follow rather than patterns to reject
- **Recommendation**: Add explicit "DO NOT DO THIS" markers to examples

**Hypothesis 4: Prompt Length**
- ~51K chars total system instruction
- Guardrails section may be lost in context
- **Recommendation**: Add guardrails to ESSENTIALS section (token-constrained mode) for higher priority

## Recommendations

### Immediate Actions

1. **Move Guardrails to ESSENTIALS Section**
   - Add outcome declaration detection to the ESSENTIALS comment block (lines 3-22)
   - This ensures it's always loaded even in token-constrained mode
   - Format: `- 🚨 OUTCOME DECLARATIONS: REJECT immediately. Players describe attempts, not outcomes.`

2. **Strengthen Rejection Language**
   - Change from: "**REJECT** and ask for an attempt"
   - Change to: "**STOP IMMEDIATELY. DO NOT NARRATE. REJECT** with exact message: 'I cannot process outcome declarations...'"

3. **Add Explicit DO NOT Examples**
   - Mark all ❌ examples with "**DO NOT DO THIS**" prefix
   - Add warning: "If you see these patterns, STOP and reject immediately"

4. **Add Guardrails Checkpoint**
   - Insert checkpoint at start of narrative generation: "BEFORE narrating, check: Is this an outcome declaration? If yes, REJECT."

### Testing Improvements

1. **Add More Edge Cases**
   - Test with partial outcome declarations
   - Test with mixed attempt/outcome language
   - Test with indirect outcome declarations

2. **Verify Prompt Loading**
   - Add test to verify guardrails section appears in actual LLM prompt
   - Check if prompt is truncated or filtered

3. **Test Multiple Models**
   - Current test uses Gemini 3 Flash
   - Test with Qwen, GPT-OSS to see if behavior varies

## Next Steps

1. ✅ Test created and evidence captured
2. ✅ Updated prompt with strengthened guardrails (moved to ESSENTIALS, strengthened language)
3. ✅ Reordered guardrails (outcome declarations FIRST, inventory SECOND)
4. ✅ Re-ran test v4 - Still 3/8 pass rate
5. 🔄 **Current Issue**: LLM applying wrong guardrail (inventory) or triggering character creation mode
6. 🔄 **Next**: Consider server-side validation as backup, or improve prompt further

## Test Run v4 Results (After Prompt Updates)

**Pass Rate**: Still 3/8 (37.5%)

**Behavior Changes**:
- Some scenarios now trigger character creation mode (different failure mode)
- Some still use inventory rejection instead of outcome declaration rejection
- Valid attempts still work correctly

**Root Cause**: Character creation mode may be overriding guardrails, or LLM is not consistently detecting outcome declarations even with strengthened prompt.

## Related Files

- **Test**: `testing_mcp/test_outcome_declaration_guardrails.py`
- **Guide**: `testing_mcp/GUARDRAILS_TEST_GUIDE.md`
- **Prompt**: `mvp_site/prompts/narrative_system_instruction.md` (lines 173-241)
- **Evidence Bundle**: `/tmp/worldarchitect.ai/handoff-llm_guardrails_validation-merge/outcome_declaration_guardrails_v2/20260110T033614Z/`
