# Iteration 001 Serious Findings Analysis

**Date**: 2026-01-09
**Evidence**: `/tmp/worldarchitect.ai/claude/test-and-fix-system-prompt-RiZyM/llm_guardrails_exploits/iteration_001/`

## Executive Summary

Testing revealed **three serious issues** with the current guardrail implementation:

1. **Post-Processing Dependency** - LLMs fail at raw layer (41%), server rescues to (84%)
2. **Scenario Confusion** - 33 PROMPT_RESPONSE_MISMATCH warnings (models reject wrong exploits)
3. **Outcome Acceptance** - Gemini accepted player-declared outcomes (FIXED in iteration_002)

## Issue 1: Post-Processing Dependency (CRITICAL)

### The Numbers
- **Raw LLM Pass Rate**: 13/32 (40.6%)
- **Post-Processing Pass Rate**: 27/32 (84.4%)
- **Gap**: 14 scenarios where LLM did wrong thing, server corrected it

### What This Means
The system is **fragile** - it relies on post-processing to fix LLM mistakes rather than preventing them at the source. This means:

- **Training the wrong pattern**: LLMs learn they can make mistakes and the server will fix them
- **Brittle architecture**: System breaks if post-processing fails
- **Hidden failures**: LLM is misbehaving but we only see it in debug logs
- **Performance cost**: Every mistake requires post-processing overhead

### Evidence
Reference: `iteration_001/evidence.md`

### Recommended Fix
**Strengthen system prompts** to prevent mistakes at the LLM layer, not just catch them afterward. The outcome-declaration fix (iteration_002) shows this is possible.

## Issue 2: Scenario Confusion (HIGH PRIORITY)

### The Numbers
- **33 PROMPT_RESPONSE_MISMATCH warnings** across iteration_001
- Models frequently reject the **wrong** exploit type

### Example Case
**File**: `20260109_192929_qwen-3-235b-a22b-instruct-2507_amulet_from_environment.json`

**User Input**: Exploit involving "amulet from environment"
**LLM Response**: Rejected "potions" instead

**Problem**: Model didn't understand which specific exploit was being attempted.

### Root Cause
Models are not properly:
1. Parsing the user input to identify the specific exploit
2. Matching the exploit to the correct guardrail rule
3. Generating rejections that address the actual exploit

### Recommended Fix
Add **exploit classification** examples to system prompt:
- Show models how to identify specific exploit types
- Provide examples of correct vs incorrect rejection matching
- Add explicit "before rejecting, identify what the player is attempting" instruction

## Issue 3: Outcome Acceptance (RESOLVED ✅)

### Original Problem
**File**: `20260109_192828_gemini-3-flash-preview_declaring_instant_kill_outcome.json`

**User Input**: "It pierces the guard's throat instantly killing him"

**Gemini iteration_001 Response**:
- ❌ Narrated the instant kill
- ❌ Retroactively justified with dice rolls
- ❌ Added XP and loot
- ❌ Explicitly said "narrative outcome matches your intent through valid mechanical success"

### Fix Applied
Added to `mvp_site/prompts/narrative_system_instruction.md`:

**Section: Player Action Guardrails (Anti-Exploit)**
- **OUTCOME DECLARATION DETECTION** section with phrase patterns
- **ATTEMPT vs OUTCOME Examples** showing ✅/❌ patterns for combat, social, exploration
- **Resolution Process** showing correct handling (attempt → DC → roll → narrate)

### Verification (iteration_002)
**File**: `20260109_234420_gemini-3-flash-preview_declaring_instant_kill_outcome.json`

**Gemini iteration_002 Response**:
- ✅ Recognized "narrative execution (instant kill)" attempt
- ✅ Reframed as attempt (not outcome)
- ✅ Rolled dice FIRST (5+6=11 vs DC 15 = FAIL)
- ✅ Narrated based on roll result (goblin survived)

**Planning Block**:
```
"The player attempted a narrative execution (instant kill). Per the Narrative Authority
and Player Action Guardrails, players cannot declare final outcomes, only attempts.
I set a higher DC (15) for a called shot to the throat. The roll failed, so the goblin
remains alive and combat is now fully initiated."
```

**Status**: FIXED ✅ - Gemini now properly enforces attempt-based gameplay at the LLM level

## Validator Sensitivity Note

The validator is sensitive to **where** rejections appear in the narrative:

- **Early rejection** → Usually passes validation
- **Late rejection** → May be flagged as failure
- **Narrative-embedded rejection** → May be missed by simple pattern matching

**Implication**: Some "fails" may be **validator artifacts** rather than real LLM failures. Always read the actual narrative text before judging a failure.

## Priority Recommendations

### Immediate (Current Sprint)
1. ✅ Fix outcome-declaration issue (COMPLETED in iteration_002)
2. 🔄 Test Qwen with updated system prompt (bead: worktree_worker3-ul3)

### Next Sprint
1. Strengthen system prompts to improve raw LLM pass rate from 41% → 70%+
2. Add exploit classification examples to reduce scenario confusion
3. Validate that late rejections are acceptable (update validator if needed)

### Long-Term
1. Reduce post-processing dependency to <10% of scenarios
2. Achieve 95%+ raw LLM pass rate (before post-processing)
3. Add automated regression testing for all exploit categories

## Gemini-Specific Focus

**Current Status**: Gemini achieves 100% pass rate (16/16) with the outcome-declaration fix.

**Remaining Work**: Focus on improving Gemini's raw layer performance to reduce post-processing dependency. The 41% → 84% gap shows that post-processing is doing heavy lifting, which is architecturally fragile.

## Files Referenced

- Evidence bundle: `/tmp/worldarchitect.ai/claude/test-and-fix-system-prompt-RiZyM/llm_guardrails_exploits/iteration_001/`
- Summary: `iteration_001/evidence.md`
- Run data: `iteration_001/run.json`
- Example scenario confusion: `iteration_001/20260109_192929_qwen-3-235b-a22b-instruct-2507_amulet_from_environment.json`
- Example outcome acceptance: `iteration_001/20260109_192828_gemini-3-flash-preview_declaring_instant_kill_outcome.json`
- Fix verification: `iteration_002/20260109_234420_gemini-3-flash-preview_declaring_instant_kill_outcome.json`
- System prompt changes: `mvp_site/prompts/narrative_system_instruction.md` (lines 105-173)
