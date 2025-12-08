# Context Budget Design Document

**Status**: Implemented (PR #2311) - **Timeline log fix applied (Dec 2025)**
**Last Updated**: 2025-12-07
**Author**: Claude Code

## Overview

This document describes the context budget allocation system for LLM API calls in WorldArchitect.AI. The system ensures story context fits within model-specific token limits while preserving narrative coherence.

## Problem Statement

GCP logs showed repeated `ContextTooLargeError` for users with long campaigns:
```
Context too large for model zai-glm-4.6: input uses 95,622 tokens,
max allowed is 94,372 tokens (80% of 117,964)
```

**Root Cause**: Fixed 20+20 turn truncation didn't account for:
1. Variable turn lengths (some turns are 2,400+ tokens)
2. Different model context windows (Cerebras 131K vs Gemini 1M)
3. Story budget varies based on scaffold overhead

## Architecture Decision: No Auto-Fallback

**DO NOT add automatic fallback to larger context models.**

This was explicitly removed in PR #2311. See bead WA-1 for tracking. Reasons:
1. **Cost unpredictability** - larger models cost more per token
2. **Voice inconsistency** - different models have different personalities
3. **Latency variance** - larger contexts increase response time
4. **Proper solution** - improve truncation, not switch models

If `ContextTooLargeError` occurs, the solution is to improve truncation logic.

## Context Budget Hierarchy

```
Model Context Window (100%)
│
├── Safety Margin (90%)
│   │
│   ├── Output Reserve (20%)
│   │   └── Reserved for LLM response generation
│   │
│   └── Max Input Allowed (80%)
│       │
│       ├── Scaffold (~15-20% of input)
│       │   ├── System instruction (~5-8K tokens)
│       │   ├── Game state JSON (~2-4K tokens)
│       │   ├── Checkpoint block (~1-2K tokens)
│       │   └── Core memories/companions (~2-3K tokens)
│       │
│       ├── Entity Tracking Reserve (10.5K tokens fixed)
│       │   ├── entity_preload_text (~2-3K)
│       │   ├── entity_specific_instructions (~1.5-2K)
│       │   └── entity_tracking_instruction (~1-1.5K)
│       │
│       ├── Timeline Log (DUPLICATES story content!)
│       │   └── ~story_tokens × 1.05 (story + SEQ_ID prefixes)
│       │   NOTE: This is NOT a small fixed reserve - it scales
│       │   with story size and can be 25K+ tokens for long campaigns!
│       │
│       └── Story Budget (remaining ~50-60%)
│           ├── Start turns (25% of story budget)
│           ├── Middle summary (10% - compacted key events)
│           ├── End turns (60% of story budget)
│           └── Truncation marker (5% safety margin)
```

### Component Token Targets

| Component | Target Tokens | Notes |
|-----------|---------------|-------|
| System instruction | 5,000-8,000 | Core rules and world context |
| Game state JSON | 2,000-4,000 | Current state snapshot |
| Checkpoint block | 1,000-2,000 | Session continuity |
| Core memories | 2,000-3,000 | Character/companion data |
| Entity tracking | 10,500 (fixed) | Added post-truncation |
| Story start | 25% of story budget | Context setup turns |
| Story middle | 10% of story budget | Compacted key events from dropped turns |
| Story end | 60% of story budget | Recent action turns |
| Truncation marker | 5% of story budget | Safety margin |

## Budget Constants

### Global Token Reserves

| Constant | Value | Purpose |
|----------|-------|---------|
| `CONTEXT_WINDOW_SAFETY_RATIO` | 0.90 | Use 90% of model context |
| `OUTPUT_TOKEN_RESERVE_RATIO` | 0.20 | Reserve 20% for output |
| `OUTPUT_TOKEN_RESERVE_COMBAT` | 24,000 | Combat scenes need more output |
| `OUTPUT_TOKEN_RESERVE_MIN` | 1,024 | Absolute minimum for output |
| `ENTITY_TRACKING_TOKEN_RESERVE` | 10,500 | Entity data added post-truncation |

### Story Budget Allocation

| Constant | Value | Purpose |
|----------|-------|---------|
| `STORY_BUDGET_START_RATIO` | 0.25 | 25% for context setup turns |
| `STORY_BUDGET_MIDDLE_RATIO` | 0.10 | 10% for compacted key events |
| `STORY_BUDGET_END_RATIO` | 0.60 | 60% for recent action turns |
| Reserved | 0.05 | Truncation marker + safety |

### Legacy Maximums (Caps)

| Constant | Value | Purpose |
|----------|-------|---------|
| `TURNS_TO_KEEP_AT_START` | 20 | Max start turns (legacy cap) |
| `TURNS_TO_KEEP_AT_END` | 20 | Max end turns (legacy cap) |
| `ABS_MIN_START` | 3 | Absolute minimum start turns |
| `ABS_MIN_END` | 5 | Absolute minimum end turns |

## Model Context Windows

| Model | Context | Safe (90%) | Max Input (80%) |
|-------|---------|------------|-----------------|
| gemini-2.0-flash | 1,000,000 | 900,000 | 720,000 |
| zai-glm-4.6 (Cerebras) | 131,072 | 117,964 | 94,372 |
| qwen-3-235b (Cerebras) | 131,072 | 117,964 | 94,372 |
| llama-3.3-70b (Cerebras) | 65,536 | 58,982 | 47,186 |
| meta-llama/llama-3.1-70b | 131,072 | 117,964 | 94,372 |

## Algorithm: Percentage-Based Turn Allocation

### Step 1: Calculate Story Budget

```python
safe_token_budget = model_context * CONTEXT_WINDOW_SAFETY_RATIO  # 90%
output_reserve = safe_token_budget * OUTPUT_TOKEN_RESERVE_RATIO  # 20%
max_input_allowed = safe_token_budget - output_reserve           # 80%

scaffold_tokens = estimate_tokens(prompt_scaffold) + ENTITY_TRACKING_TOKEN_RESERVE
story_budget = max_input_allowed - scaffold_tokens
```

### Step 2: Calculate Percentage-Based Turn Limits

```python
def _calculate_percentage_based_turns(story_context, max_tokens):
    # Calculate average tokens per turn from actual content
    total_story_tokens = estimate_tokens(combined_text)
    avg_tokens_per_turn = total_story_tokens / len(story_context)

    # Allocate based on percentages
    start_token_budget = max_tokens * 0.25  # 25%
    end_token_budget = max_tokens * 0.70    # 70%

    # Convert to turn counts
    start_turns = min(
        int(start_token_budget / avg_tokens_per_turn),
        20,  # Legacy cap
        total_turns // 2  # Never more than half
    )
    end_turns = min(
        int(end_token_budget / avg_tokens_per_turn),
        20,  # Legacy cap
        total_turns - start_turns  # Don't overlap
    )

    return max(3, start_turns), max(5, end_turns)
```

### Step 3: Adaptive Reduction Loop

If percentage-based allocation still exceeds budget:

```python
while current_start >= min_start and current_end >= min_end:
    truncated = start_context + [marker] + end_context
    if estimate_tokens(truncated) <= max_tokens:
        return truncated  # Found a fit

    # Reduce turns (prioritize keeping recent context)
    if current_start > min_start and current_start >= current_end:
        current_start -= 2
    elif current_end > min_end:
        current_end -= 2
    else:
        break  # Can't reduce further
```

## Example Calculations

### Cerebras zai-glm-4.6 (131K context)

```
Model context:     131,072 tokens
Safe budget (90%): 117,964 tokens
Output (20%):       23,592 tokens
Max input (80%):    94,372 tokens
Scaffold (~20K):    20,000 tokens (estimated)
Story budget:       74,372 tokens

Story allocation:
- Start (25%):     18,593 tokens → ~7-8 turns @ 2,400 avg
- End (70%):       52,060 tokens → ~20 turns @ 2,400 avg (capped at 20)
- Reserved (5%):    3,719 tokens
```

### Gemini 2.0 Flash (1M context)

```
Model context:   1,000,000 tokens
Safe budget:       900,000 tokens (but capped at 300K for latency)
Output:             60,000 tokens
Max input:         240,000 tokens
Scaffold:           25,000 tokens (estimated)
Story budget:      215,000 tokens

Story allocation:
- Start (25%):     53,750 tokens → 20 turns (capped)
- End (70%):      150,500 tokens → 20 turns (capped)
```

## Defense-in-Depth Layers

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| 1 | Percentage-based allocation | Scales with model context |
| 2 | Adaptive reduction loop | Handles variable turn lengths |
| 3 | Minimum turn guarantees | Maintains narrative coherence |

## Logging

The system logs budget calculations for debugging:

```
📊 BUDGET: model_limit=131072tk, safe_budget=117964tk,
   scaffold=20500tk (raw:10000+entity_reserve:10500),
   output_reserve=23592tk (normal), story_budget=73872tk,
   actual_story=95000tk ⚠️ OVER

📊 PERCENTAGE-BASED TURNS: avg_tokens/turn=2400,
   start_budget=18468tk→7 turns (25%),
   end_budget=51710tk→20 turns (70%)

⚠️ Adaptive truncation reduced to 5+12 turns (from 7+20) to fit budget.
```

## Test Coverage

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `test_adaptive_truncation.py` | 6 | Adaptive + percentage-based |
| `test_context_truncation.py` | 3 | Legacy behavior |
| `test_output_token_budget_regression.py` | 9 | Budget calculations |

## Related PRs

- PR #2284: Add 20% output token reserve
- PR #2294: Centralize context budget calculation
- PR #2201: Adjust compaction to 20+20 turns
- PR #2311: Add percentage-based allocation + adaptive truncation

## Known Issues

### Timeline Log Budget Bug (Dec 2025) - FIXED

**Status**: ✅ Fixed (Dec 7, 2025)

**Problem**: The scaffold calculation did NOT include `timeline_log_string`, but the final prompt DOES include it. This caused story content to be counted once but included twice, leading to `ContextTooLargeError` in production.

**Production Evidence**:
```
Model: zai-glm-4.6 (131K context)
Budget check: story=25,127 tokens ✓ OK
Final prompt: 96,396 tokens ✗ OVERFLOW (expected ~53K)
Root cause: timeline_log added ~27K tokens NOT in budget
```

**Why This Happens**:
- `_build_timeline_log()` reformats the entire story context with `[SEQ_ID: X] Actor:` prefixes
- This is essentially the same content as `story_context` with ~5% overhead
- The scaffold estimate includes story_context tokens but NOT timeline_log tokens
- Result: Final prompt is approximately `scaffold + story + story×1.05` instead of `scaffold + story`

**Test**: `mvp_site/tests/test_end2end/test_timeline_log_budget_end2end.py`

**Fix Applied**:
The story budget is now divided by `TIMELINE_LOG_DUPLICATION_FACTOR = 2.05` to account for timeline_log duplicating the story content. This ensures truncation happens earlier, preventing overflow.

```python
# llm_service.py line 3193-3201
TIMELINE_LOG_DUPLICATION_FACTOR = 2.05
available_story_tokens = int(available_story_tokens_raw / TIMELINE_LOG_DUPLICATION_FACTOR)
```

## Policy: No Model Switching

**Model cycling and auto-fallback are NOT supported.**

The system uses a single configured model per request. If errors occur:
- API errors: Fail and let user retry
- Context too large: Fix truncation logic, don't switch models

**Reasons**:
1. Cost unpredictability - larger models cost more per token
2. Voice inconsistency - different models have different personalities
3. Latency variance - larger contexts increase response time
4. Debugging complexity - model switching hides root causes

If `ContextTooLargeError` occurs, the proper fix is to improve the truncation/compaction logic.
