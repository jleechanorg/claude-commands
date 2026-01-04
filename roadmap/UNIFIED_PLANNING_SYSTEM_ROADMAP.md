# Unified Planning System Roadmap

**Bead**: `worktree_worker2-zjr`
**Created**: 2026-01-04
**Updated**: 2026-01-04 (incorporated review feedback)
**Status**: Planning

## Executive Summary

Centralize and unify planning block handling across Think Mode and Story Mode. The LLM can generate enhanced planning analysis at significant decision points while maintaining clear time handling rules.

**Key Clarification**: This is NOT "always freeze time". Planning blocks with choices already exist in every story response. This roadmap:
1. Centralizes the schema (removes duplication)
2. Adds an `intent` signal to distinguish Think Mode (frozen) from Story Mode (advancing)
3. Enables enhanced planning analysis at decision points

---

## Current State Analysis

### Two Types of Planning Blocks

| Type | Time Behavior | Trigger | Agent |
|------|---------------|---------|-------|
| **Think Mode** | Time FROZEN (microsecond only) | `THINK:` prefix or `mode="think"` | `PlanningAgent` |
| **Story Choices** | Time ADVANCES normally | Every story response | `StoryModeAgent` |

**Critical**: These must remain distinct. The roadmap unifies the SCHEMA, not the TIME HANDLING.

### Duplication Map

| Content | think_mode_instruction.md | game_state_instruction.md | Code |
|---------|---------------------------|---------------------------|------|
| planning_block structure | Lines 83-152 | Lines 1847-1920 | `narrative_response_schema.py:480-580` |
| "No narrative advancement" | Lines 72-80 | Lines 1890-1895 | - |
| Microsecond time rule | Lines 6-7, 163, 219 | Lines 1875-1880 | `world_logic.py:1651-1655` |
| Field separation | Lines 72-80 | Multiple sections | `narrative_response_schema.py:strip_*` |
| Choice format | Lines 114-141 | Lines 1847-1870 | `narrative_response_schema.py:505-545` |

### Unused/Legacy Code

| Location | Issue | Action |
|----------|-------|--------|
| `llm_service.py:3084-3160` | `_validate_and_enforce_planning_block` has 5 unused args | Remove unused args |
| `llm_service.py:3093-3108` | Docstring says "kept for signature compatibility" | Clean up signature |
| `narrative_response_schema.py` | Regex-based stripping duplicates validation | Consolidate |

---

## Proposed Architecture

### Phase 1: Centralize Schema (Week 1)

**Goal**: Single source of truth for planning_block structure

```python
# narrative_response_schema.py

PLANNING_BLOCK_SCHEMA = {
    "intent": str,             # NEW: "think" | "story" - determines time handling
    "thinking": str,           # Internal monologue (optional for story mode)
    "situation_assessment": {  # Optional - full analysis for think mode
        "current_state": str,
        "key_factors": list[str],
        "constraints": list[str],
        "resources_available": list[str],
    },
    "choices": {
        "<choice_key>": {
            "text": str,           # Display name
            "description": str,    # What this entails
            "pros": list[str],     # Optional - for enhanced analysis
            "cons": list[str],     # Optional - for enhanced analysis
            "confidence": str,     # high|medium|low (optional)
            "risk_level": str,     # safe|low|medium|high
        }
    },
    "analysis": {              # Optional - for enhanced analysis
        "recommended_approach": str,
        "reasoning": str,
        "contingency": str,
    }
}
```

**Tasks**:
- [ ] Define `PLANNING_BLOCK_SCHEMA` constant
- [ ] Add `intent` field with "think" | "story" values
- [ ] Update validation to use schema
- [ ] Add schema documentation

**Backward Compatibility**:
- [ ] Add fallback logic for missing `intent` field
- [ ] Default to `constants.is_think_mode()` if intent missing
- [ ] Log warnings when intent is missing
- [ ] Document migration strategy

**Intent Validation**:
- [ ] Validate `intent` field is "think" or "story" only
- [ ] Default to "story" if invalid (safe default - advances time)
- [ ] Log warnings for invalid values
- [ ] Add `validate_planning_block_intent()` to schema module

```python
# narrative_response_schema.py
VALID_INTENT_VALUES = {"think", "story"}

def validate_planning_block_intent(planning_block: dict) -> str:
    """Validate and normalize intent field."""
    intent = planning_block.get("intent")
    if intent in VALID_INTENT_VALUES:
        return intent
    logging_util.warning(f"Invalid intent '{intent}', defaulting to 'story'")
    return "story"  # Safe default: advance time
```

### Phase 2: Unify Prompts with Dynamic Injection (Week 2)

**Goal**: Single protocol document with programmatic schema injection

**Create**: `prompts/planning_protocol.md`

```markdown
# Planning Protocol (Unified)

## Intent Field (REQUIRED)

Every planning_block MUST include an `intent` field:
- `"think"`: Time frozen, deep analysis, user explicitly requested planning
- `"story"`: Time advances, standard choices for player agency

## When to Generate Enhanced Planning Blocks

The LLM SHOULD add enhanced analysis (thinking, situation_assessment, pros/cons) when:
1. User explicitly requests planning (THINK: prefix) → intent: "think"
2. Narrative reaches a SIGNIFICANT decision point → intent: "story" + enhanced fields
3. Multiple viable paths exist with MEANINGFULLY different consequences
4. Combat or social encounter offers TACTICAL choices requiring analysis

The LLM should NOT generate enhanced analysis for:
- Simple movement or exploration
- Routine interactions
- Obvious next steps

## Frequency Guidelines

**Enhanced planning blocks should be rare:**
- Maximum 1 per 3-5 story responses
- Only at truly significant decision points
- Not for every combat round or conversation
- Monitor frequency to prevent spam

**Rationale:**
- Too frequent = degraded player experience
- Too frequent = slower response times
- Too frequent = higher token costs

## Time Rules

| Intent | Time Behavior | Turn Counter |
|--------|---------------|--------------|
| `"think"` | +1 microsecond ONLY | FROZEN |
| `"story"` | Advances normally | Increments |

## Structure Requirements

{{PLANNING_BLOCK_SCHEMA}}

## Field Separation

- planning_block is a SEPARATE field, never embedded in narrative
- narrative field contains story prose ONLY
- choices go in planning_block.choices, not narrative
```

**Dynamic Schema Injection**:
```python
# In PromptBuilder
def inject_schema(protocol_template: str) -> str:
    schema_json = json.dumps(PLANNING_BLOCK_SCHEMA, indent=2)
    return protocol_template.replace("{{PLANNING_BLOCK_SCHEMA}}", schema_json)
```

**Tasks**:
- [ ] Create `planning_protocol.md` with placeholder
- [ ] Implement `inject_schema()` in PromptBuilder
- [ ] Update `think_mode_instruction.md` to reference protocol
- [ ] Update `game_state_instruction.md` to reference protocol
- [ ] Remove duplicated content from both files

### Phase 3: Clean Up Code (Week 3)

**Goal**: Remove legacy code, consolidate validation

**Tasks**:

1. **Clean `_validate_and_enforce_planning_block`**:
   ```python
   # Before: 7 arguments, 5 unused
   def _validate_and_enforce_planning_block(
       response_text, user_input, game_state, chosen_model,
       system_instruction, structured_response, provider_name
   )

   # After: 2 arguments
   def validate_planning_block(
       response_text: str,
       structured_response: NarrativeResponse | None
   ) -> bool
   ```

2. **Move to narrative_response_schema.py**:
   - Consolidate all planning_block logic in one place
   - Remove from llm_service.py

3. **Consolidate detection**:
   - `constants.is_think_mode()` already centralized
   - Remove any remaining duplicates

### Phase 4: Unified Planning Features (Week 4)

**Goal**: Enable enhanced planning analysis at decision points (RENAMED from "Always-On")

**Critical Rule**: Time handling is based on `intent`, NOT presence of planning_block.

**Changes**:

1. **Add intent field support**:
   - PlanningAgent always sets `intent: "think"`
   - StoryModeAgent sets `intent: "story"` (can include enhanced fields)

2. **Update time handling** (world_logic.py):
   ```python
   # CORRECT: Check intent, not presence of planning_block
   def should_freeze_time(mode: str, planning_block: dict | None) -> bool:
       if mode == constants.MODE_THINK:
           return True
       if planning_block and planning_block.get("intent") == "think":
           return True
       return False
   ```

3. **Update frontend**:
   ```javascript
   // app.js - render enhanced analysis when present
   if (data.planning_block) {
     if (data.planning_block.thinking) {
       renderThinkingSection(data.planning_block.thinking);
     }
     if (data.planning_block.choices) {
       renderPlanningChoices(data.planning_block);
     }
   }
   ```

4. **Require think:return_story in enhanced blocks**:
   - REQUIRED when LLM spontaneously generates enhanced planning in story mode
   - NOT required when user explicitly requested planning (THINK: prefix)
   - Must include a choice to "Execute original intent"
   - Backend should validate and add if missing (with warning)
   - Prevents user confusion when they asked for action

5. **Update agent logic**:
   - `StoryModeAgent` can generate enhanced planning_block with `intent: "story"`
   - `PlanningAgent` required for `intent: "think"` (explicit requests)

6. **Agent-Intent Consistency**:
   - Agent selection is authoritative (PlanningAgent → always freeze time)
   - If LLM provides inconsistent intent, log warning and use agent's intent
   - Intent field is for LLM-initiated enhanced planning in Story Mode
   - Rationale: Prevents LLM errors from breaking time handling

---

## File Changes Summary

### Files to Create
- `prompts/planning_protocol.md` - Unified planning rules

### Files to Modify
- `narrative_response_schema.py` - Add schema, intent field, consolidate validation
- `think_mode_instruction.md` - Reference protocol, remove duplication
- `game_state_instruction.md` - Reference protocol, remove duplication
- `llm_service.py` - Clean up function signature
- `world_logic.py` - Time handling based on intent field
- `frontend_v1/app.js` - Render enhanced analysis when present
- `PromptBuilder` - Add schema injection

### Files to Keep As-Is
- `agents.py` - PlanningAgent still useful for explicit requests
- `constants.py` - `is_think_mode()` still useful

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Duplicated planning rules | 5+ locations | 1 location |
| Lines of planning docs | ~400 | ~150 |
| Unused function arguments | 5 | 0 |
| Schema drift possible | Yes | No (dynamic injection) |
| Time handling clarity | Ambiguous | Explicit (intent field) |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing Think Mode | Keep THINK: prefix working, intent="think" |
| LLM generates too many enhanced blocks | Trigger guidelines in protocol |
| Time handling confusion | Explicit intent field, NOT presence-based |
| User asks for action, gets planning | Require think:return_story choice |
| Frontend breaks on enhanced blocks | Already handles choices; add thinking render |
| Schema drift between code and prompts | Dynamic injection via PromptBuilder |

---

## Testing Plan

1. **Unit Tests**:
   - Schema validation with intent field
   - Time handling: intent="think" freezes, intent="story" advances
   - Dynamic schema injection

2. **Integration Tests**:
   - Think Mode still works with THINK: prefix
   - Story mode with enhanced planning_block advances time
   - Frontend renders enhanced analysis correctly

3. **E2E Tests**:
   - Full flow with explicit think request
   - Full flow with LLM-initiated enhanced planning
   - think:return_story choice works correctly

---

## Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Centralize Schema | `PLANNING_BLOCK_SCHEMA` with intent field, updated validation |
| 2 | Unify Prompts | `planning_protocol.md`, dynamic injection, updated instruction files |
| 3 | Clean Up Code | Removed unused args, consolidated logic |
| 4 | Unified Planning Features | Intent-based time handling, enhanced analysis support |

---

## Review Feedback Incorporated

### Accepted

| Feedback | Source | Implementation |
|----------|--------|----------------|
| Dynamic schema injection | Review 1 | Phase 2: PromptBuilder injects schema |
| Explicit intent signal | Message #358 | Phase 1: `intent: "think" \| "story"` field |
| Rename Phase 4 | Review 2 | "Unified Planning Features" not "Always-On" |
| Trigger guidelines | Review 2 | Phase 2: Protocol includes when/when-not rules |
| think:return_story for enhanced blocks | Review 1 | Phase 4: Required for spontaneous deep-think |
| Fix time handling | Review 2 | Phase 4: Intent-based, not presence-based |

### Key Clarification

**The critical bug in the original roadmap**: "If response has planning_block, freeze turn counter" would freeze ALL gameplay because planning blocks exist in every story response.

**Fix**: Time handling is based on `intent` field value, not presence of planning_block.

---

## References

- Bead: `worktree_worker2-zjr`
- PR #2993: Initial Think Mode implementation
- `constants.is_think_mode()`: Centralized detection (already done)
- `get_agent_for_input(mode)`: Now accepts mode parameter (already done)
