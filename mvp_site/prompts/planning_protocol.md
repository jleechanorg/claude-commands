# Planning Protocol (Unified)

**Purpose**: Single source of truth for planning block structure and rules.

This protocol applies to all planning blocks regardless of mode. The key difference between modes is TIME HANDLING:

| Mode | Trigger | Time Behavior | Agent |
|------|---------|---------------|-------|
| **Think Mode** | `THINK:` prefix or `mode="think"` | Time FROZEN (+1 microsecond only) | `PlanningAgent` |
| **Story Mode** | Every story response | Time ADVANCES normally | `StoryModeAgent` |

---

## Planning Block Structure

The canonical schema is defined below. (Note: This schema is automatically injected from `narrative_response_schema.py` - you see the full schema content here, not just a reference.)

### Core Fields (Canonical Schema)

{{PLANNING_BLOCK_SCHEMA}}

### Choice Structure

{{CHOICE_SCHEMA}}

**CRITICAL ORDERING RULE**: When a parallel execution option is included, it **MUST be placed LAST** in the choices object. All individual situational choices must come first, followed by the parallel execution option as the final choice. This ensures consistent UI presentation with the parallel option always appearing at the bottom.

**Example with Parallel Execution (correct ordering):**
```json
{
  "thinking": "The player faces three critical objectives that could be tackled sequentially or in parallel.",
  "context": "Post-battle strategic planning phase",
  "choices": {
    "audit_avernus": {
      "text": "Audit Avernus Remnants",
      "description": "Systematically collect the remaining diabolical assets and souls in the First Layer while the Hells are in shock.",
      "risk_level": "high",
      "pros": ["Massive soul harvest", "Consolidate Hells territory"],
      "cons": ["Increases chance of meeting Hellfire Auditors"],
      "confidence": "high"
    },
    "return_to_waterdeep": {
      "text": "Return to Waterdeep",
      "description": "Personally oversee the final conversion of the Watchful Order and the Masked Lords to secure the North.",
      "risk_level": "high",
      "pros": ["Total shadow control of the North", "Stabilize 'Paradise' network"],
      "cons": ["Direct exposure to Elminster's proximity"],
      "confidence": "high"
    },
    "parallel_execution": {
      "text": "Execute All Simultaneously",
      "description": "Coordinate the Avernus audit through Ketheric while you return to Waterdeep to finalize shadow control.",
      "risk_level": "high",
      "pros": ["Maximum ROI", "Maintain momentum on all fronts"],
      "cons": ["Divided attention", "High coordination complexity (+2 DC)"],
      "confidence": "medium",
      "analysis": {
        "delegation_targets": ["Ketheric handles Avernus audit"],
        "personal_focus": "Waterdeep conversion requires direct oversight",
        "coordination_dc": 18
      }
    }
  }
}
```

**Note**: The `parallel_execution` choice is always the **last** key in the choices object. Individual situational choices come first.

### Field Requirements by Mode

| Field | Think Mode | Story Mode |
|-------|------------|------------|
| `plan_quality` | REQUIRED (INT/WIS roll) | Not used |
| `thinking` | REQUIRED (deep analysis) | Optional |
| `situation_assessment` | REQUIRED | Optional |
| `choices` | REQUIRED (situation-specific; include return-to-story only when appropriate) | REQUIRED |
| `analysis` | REQUIRED | Optional |

---

## Parallel Execution Option (MANDATORY)

🚨 **MANDATORY**: When presenting 2 or more situational choices (excluding meta-choices like `think:continue` or `god:*`) and none of the exclusion conditions below apply, you **MUST** include a parallel/delegation option as an additional choice. This is not optional—it is a required feature of the planning system.

**CRITICAL ORDERING RULE**: The parallel execution option **MUST always be placed LAST** in the choices object. All individual situational choices must come first, followed by the parallel execution option as the final choice.

**Failure to include the parallel execution option when conditions are met will result in incomplete planning blocks.**

*See "When NOT to Include Parallel Option" section below for the only valid exclusion conditions.*

**Structure**: Use top-level `pros`/`cons`/`confidence` fields for frontend display, and `analysis` object for parallel execution metadata:
- `pros` - advantages (list of strings, at choice level for frontend display)
- `cons` - disadvantages (list of strings, at choice level for frontend display)
- `confidence` - execution confidence level (string, at choice level for frontend display)
- `analysis` object (optional) containing:
  - `delegation_targets` - who handles which tasks (optional)
  - `personal_focus` - character's main focus (optional)
  - `coordination_dc` - coordination difficulty (optional)

**Example**:
```json
"parallel_execution": {
    "text": "Execute All Simultaneously",
    "description": "Coordinate all operations using delegation and split focus",
    "risk_level": "high",
    "pros": ["Faster completion", "Maintain momentum"],
    "cons": ["Divided attention", "Higher coordination complexity"],
    "confidence": "medium",
    "analysis": {
        "delegation_targets": ["Lieutenants for garrison", "Researchers for refinement"],
        "personal_focus": "High Hall audit requires direct oversight",
        "coordination_dc": 16
    }
}
```

**Note on coordination_dc**: Set this to the base DC for the primary task + 2 per additional parallel task + modifiers for complexity. (e.g., base DC 12 + 2 (one additional task) = DC 14).

### When NOT to Include Parallel Option

- Only 1 situational choice available (nothing to parallelize)
- Choices are mutually exclusive by nature (e.g., "Surrender" vs "Fight to the death")
- Meta-choices only (`think:continue`, `think:return_story`, `god:*`)
- Explicit sequential dependencies (must do A before B is possible)

### Parallel Option Mechanics

When a player selects a parallel execution choice:
- **DC Modifier**: +2 to +4 (coordinating multiple tasks is harder). Use:
  - **+2** when coordinating **2 relatively simple, compatible tasks** with generally competent allies and no severe time/pressure constraints.
  - **+3** when coordinating **3 tasks** or when at least one task is moderately complex, conditions are somewhat chaotic, or some allies are less capable.
  - **+4** when coordinating **4+ tasks** and/or **high-complexity or conflicting tasks**, under high stress or chaotic conditions, or with poorly coordinated/untrained allies.
- **Success**: All tasks execute with reduced time cost. The exact time calculation is system-dependent, but the intent is "faster than pure sequencing while still incurring a coordination penalty." For example:
  - 2 tasks: ~1.25x–1.5x the longest single-task time instead of 2x
  - 3 tasks: ~1.5x the longest single-task time instead of 3x
  - 4 tasks: ~1.75x–2x the longest single-task time instead of 4x
  - 5+ tasks: cap at ~2x–2.5x the longest single-task time, or use your own system's parallel-action rules
- **Partial Success**: Some tasks succeed, others fail or are delayed
- **Failure**: Coordination breakdown - tasks may interfere with each other or none succeed
- **Rewards**: On success, ×1.2 XP multiplier for efficient multi-tasking and strategic thinking (stacks with other modifiers per Risk/Reward Balance section)

---

## Choice Key Naming

Choice keys must follow these conventions:
- **Format**: `snake_case` identifiers
- **Allowed prefixes**: `god:`, `think:`
- **Pattern**: `^(god:|think:)?[a-zA-Z_][a-zA-Z0-9_]*$`

### Contextual Choice Keys

Use these prefixes only when the situation calls for them:

| Key | Purpose |
|-----|---------|
| `think:continue` | Optional: stay in Think Mode for deeper analysis |
| `think:return_story` | Optional: include only when the situation calls for exiting Think Mode and resuming the story; omit otherwise |
| `god:*` | God Mode actions (DM commands) |

---

## Risk Levels

Valid values for `risk_level`: {{VALID_RISK_LEVELS}}

- `safe` - No risk, guaranteed success
- `low` - Minor consequences if failed
- `medium` - Notable consequences possible
- `high` - Significant danger or cost

---

## Confidence Levels

Valid values for `confidence`: {{VALID_CONFIDENCE_LEVELS}}

- `high` - Character is confident this will work
- `medium` - Reasonable chance of success
- `low` - Uncertain outcome

---

## Mechanical Impact (Plan Quality → DC)

**Planning is NOT just flavor.** Plan quality and choice selection directly affect operation DCs.

### How It Works

When a player executes a choice from a planning block, the DC is adjusted:

| Factor | DC Modifier |
|--------|-------------|
| Chose `recommended_approach` | **-2** |
| Chose `high` risk option | **+2** |
| Planning tier `Brilliant`/`Masterful` | **-1** |
| Planning tier `Confused` | **+2** |
| Confidence `low` on chosen approach | **+1** |

### Why This Matters

- **Smart planning is rewarded**: Choosing the recommended approach gives a mechanical advantage
- **Risk has consequences**: High-risk choices are genuinely harder to execute
- **INT/WIS matters for execution**: A brilliant plan (high INT/WIS roll) makes operations easier
- **Failed planning hurts**: A confused analysis creates real obstacles

### Example Flow

1. Player enters Think Mode: "How do I sneak past the guards?"
2. **Planning check:** Character rolls INT 22 vs planning DC 12 → **Brilliant** tier (margin = 22 - 12 = +10)
3. Planning block presents options with `risk_level` and `confidence`
4. Player selects the `recommended_approach` (timing patrol rotations)
5. **Execution check:** Base execution DC 15 - 2 (recommended) - 1 (brilliant) = **DC 12**

*Note: Planning DC and execution DC are separate. The planning check determines quality tier; the execution DC is set by the situation and then adjusted by modifiers.*

### Caps

- Maximum adjustment: ±4 DC
- Minimum DC: 5 (trivial tasks don't need rolls)
- Maximum DC: 30 (impossible is impossible)

### Risk/Reward Balance

**High-risk options have higher DCs but better rewards on success - XP, loot, AND narrative.**

| Risk Level | DC Effect | XP | Loot | Narrative |
|------------|-----------|-----|------|-----------|
| `safe`/`low` | +0 | ×1.0 | Standard | Standard outcome |
| `medium` | +0 | ×1.25 | +10% gold | Minor bonus |
| `high` | **+2** | **×1.5** | **+25% gold, bonus item** | **Superior outcome** |

*`safe` = no meaningful downside; `low` = minor stakes. Both share mechanical modifiers but differ narratively.*

#### Planning Quality Reward Bonuses

| Tier | XP | Loot |
|------|-----|------|
| `Masterful` | ×1.25 | Rare item chance |
| `Brilliant` | ×1.1 | Uncommon item chance |
| Others | ×1.0 | Standard |

**Stack Example:** High-risk (×1.5) × Masterful (×1.25) = **×1.875 XP**

#### High-Risk Rewards Include:
- **More information** (interrogation vs killing)
- **Better positioning** (infiltrate vs sneak past)
- **Bonus loot** (claim artifact vs destroy it)
- **Story branches** (ally vs enemy)
- **Reputation gains** (bold success impresses NPCs)

#### Example Pairs

| Safe (easier) | Risky (harder but better) |
|--------------|---------------------------|
| Kill the guard | Capture for interrogation |
| Pick one lock | Disable whole alarm system |
| Flee the dragon | Negotiate an alliance |
| Destroy the artifact | Claim its power |

This creates meaningful choice: safe = reliable, risky = potentially superior outcome.

---

## Quality Tiers (Think Mode)

Valid values: {{VALID_QUALITY_TIERS}}

**See `think_mode_instruction.md` for complete DC scaling and quality tier rules.**

Summary: Roll INT/WIS check vs DC (DC 2-20 for typical play, scales higher for epic scope). Quality tier determined by margin:
- **Success**: Competent (meet DC) → Sharp (+5) → Brilliant (+10) → Masterful (+15)
- **Failure**: Incomplete (-1 to -4) → Muddled (-5 to -9) → Confused (-10+)

---

## Time Handling Rules

### Think Mode (FROZEN)
When mode is "think" or user prefixed with `THINK:`:
- Time advances by exactly 1 microsecond
- Turn counter does NOT increment
- No narrative advancement (no dice rolls that advance story)
- Response is pure strategic analysis

### Story Mode (ADVANCES)
All other story responses:
- Time advances normally based on actions
- Turn counter increments
- Narrative progresses
- Choices represent player agency

**CRITICAL**: Time handling is determined by MODE, not by presence of planning_block.

---

## Field Separation Rule

The planning_block is a SEPARATE JSON field:
- Never embed planning_block JSON in the `narrative` field
- The `narrative` field contains story prose ONLY
- Choices go in `planning_block.choices`, not in narrative text
- The frontend reads `planning_block` as a structured object

---

## Plan Freeze Mechanic (Think Mode Only)

When a planning check **FAILS**, the character cannot re-think the same topic until a cooldown period passes.

### Freeze Duration by DC (Scales with Scope)

| Original DC | Freeze Duration |
|-------------|-----------------|
| DC 2-8 | 1 hour |
| DC 9-12 | 2 hours |
| DC 13-16 | 4 hours |
| DC 17-20 | 8 hours |
| DC 21+ | 24 hours |

**Note**: Freeze durations are in **game time**.

### Freeze Tracking in State

On failed planning check, add to `state_updates.frozen_plans`:

```json
"frozen_plans": {
    "<plan_topic_key>": {
        "failed_at": "<current_world_time>",
        "freeze_until": "<world_time + freeze_duration>",
        "original_dc": 14,
        "freeze_hours": 4,
        "description": "planning the warehouse ambush"
    }
}
```

### Freeze Rules

1. **On Failure**: Record frozen plan in state_updates
2. **On Re-attempt**: Check if topic is frozen; if so, reject with remaining time and skip re-rolling
3. **Different Topics**: Always allowed - freeze is topic-specific; use distinct topic keys
4. **Early Break**: Lift freeze when significant new information arrives, a materially different approach is taken (new topic key), relevant assistance is provided, or an orchestrator override/`gm_override` is explicitly set

---

## Validation

The validation code in `narrative_response_schema.py`:
- Validates against `VALID_RISK_LEVELS`
- Validates against `VALID_CONFIDENCE_LEVELS`
- Validates against `VALID_QUALITY_TIERS`
- Validates `plan_quality` DC/margin/success consistency and coerces invalid inputs
- `frozen_plans` is enforced by the LLM via prompts (timestamps/DC-derived durations are constrained in prompts, not Python code)
- Sanitizes HTML/script content for security
- Requires both `text` and `description` for each choice
