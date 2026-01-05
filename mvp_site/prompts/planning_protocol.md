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

Based on INT or WIS check:

| Roll | Quality Tier | Effect |
|------|--------------|--------|
| 1-5 | Muddled | Miss obvious options, overlook key risks |
| 6-10 | Incomplete | Miss 1-2 good options, analysis has gaps |
| 11-15 | Competent | Standard analysis, most options covered |
| 16-20 | Sharp | Thorough analysis, spot non-obvious options |
| 21-25 | Brilliant | Exceptional insight, creative options |
| 26+ | Masterful | Perfect clarity, optimal strategies |

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

## Validation

The validation code in `narrative_response_schema.py`:
- Validates against `VALID_RISK_LEVELS`
- Validates against `VALID_CONFIDENCE_LEVELS`
- Sanitizes HTML/script content for security
- Requires both `text` and `description` for each choice
