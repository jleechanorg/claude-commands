# Planning Protocol (Unified)

**Purpose**: Single source of truth for planning block structure and rules.

This protocol applies to all planning blocks regardless of mode. The key difference between modes is TIME HANDLING:

| Mode | Trigger | Time Behavior | Agent |
|------|---------|---------------|-------|
| **Think Mode** | `THINK:` prefix or `mode="think"` | Time FROZEN (+1 microsecond only) | `PlanningAgent` |
| **Story Mode** | Every story response | Time ADVANCES normally | `StoryModeAgent` |

---

## Planning Block Structure

The canonical schema is defined in `narrative_response_schema.py` as `PLANNING_BLOCK_SCHEMA`.

### Core Fields (Canonical Schema)

{{PLANNING_BLOCK_SCHEMA}}

### Choice Structure

{{CHOICE_SCHEMA}}

### Field Requirements by Mode

| Field | Think Mode | Story Mode |
|-------|------------|------------|
| `plan_quality` | REQUIRED (INT/WIS roll) | Not used |
| `thinking` | REQUIRED (deep analysis) | Optional |
| `situation_assessment` | REQUIRED | Optional |
| `choices` | REQUIRED (situation-specific; include return-to-story only when appropriate) | REQUIRED |
| `analysis` | REQUIRED | Optional |

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
