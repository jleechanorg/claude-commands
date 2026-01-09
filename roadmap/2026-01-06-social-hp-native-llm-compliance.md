# Social HP Native LLM Compliance Design

**Date:** 2026-01-06
**Status:** Approved
**PR:** #2915

## Problem Statement

The LLM is ignoring Social HP requirements, requiring server-side enforcement:
- **Resistance indicators**: Server injects 75% of the time
- **Progress calculation**: Server syncs counters
- **Request-type scaling**: Server applies 1x/2x/3x multipliers

This is a band-aid. The LLM should produce compliant output natively.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Full LLM Control | Single source of truth, simpler server |
| Request detection | Semantic (no keywords) | LLM already interprets social requests for dice rolls |
| Severity classification | DC ranges + narrative stakes | Natural mapping, flexible guidelines |
| Progress tracking | Explicit formula | Clear, deterministic, matches existing logic |
| Resistance indicators | Examples + JSON field | Concrete guidance + verifiable output |

## Implementation

### 1. Request Severity & HP Scaling

Add to `SOCIAL_HP_ENFORCEMENT_REMINDER`:

```markdown
### REQUEST SEVERITY & HP SCALING

When a player makes a social request of a high-tier NPC, assess the severity:

| Severity | DC Range | HP Multiplier | Description |
|----------|----------|---------------|-------------|
| Information | DC 10-15 | 1x (base) | Asking for knowledge, directions, lore |
| Favor | DC 16-20 | 2x | Requesting action, resources, assistance |
| Submission | DC 21+ | 3x | Demanding authority, fealty, surrender |

**Guidelines (use judgment):**
- If asking costs the NPC nothing → Information (1x)
- If asking costs effort/resources → Favor (2x)
- If asking threatens identity/authority → Submission (3x)

**Example:** God-tier NPC with base 15 HP:
- "Tell me about the war" → DC 12, HP stays 15/15
- "Grant me an audience with the council" → DC 18, HP scales to 30/30
- "Kneel before me and swear fealty" → DC 25, HP scales to 45/45
```

### 2. Progress Calculation

```markdown
### PROGRESS TRACKING

Progress is calculated from damage dealt to Social HP:

```
successes = social_hp_max - social_hp_current
```

**Damage per check:**
- Success (beat DC): 2 damage
- Close fail (within 5 of DC): 1 damage
- Hard fail (miss by 6+): 0 damage

**Example progression (45 HP submission challenge):**
| Turn | Roll vs DC | Damage | HP | Successes |
|------|------------|--------|-----|-----------|
| 1 | 22 vs 25 (close fail) | 1 | 44/45 | 1/5 |
| 2 | 28 vs 25 (success) | 2 | 42/45 | 3/5 |
| 3 | 30 vs 25 (success) | 2 | 40/45 | 5/5 ✓ |

**Status thresholds:**
- 0-1 successes: RESISTING
- 2-3 successes: WAVERING
- 4+ successes: YIELDING
- 5 successes: Challenge complete (NPC agrees)
```

### 3. Resistance Indicators

```markdown
### RESISTANCE INDICATORS (MANDATORY)

High-tier NPCs MUST show resistance in narrative. Use these examples:

**Verbal resistance:**
- "No." / "I refuse." / "Absolutely not."
- "You forget your place." / "You dare?"
- "That is not yours to demand."

**Physical resistance:**
- crosses arms / steps back / jaw tightens
- eyes harden / expression turns cold
- raises hand to halt / turns away

**By status:**
- RESISTING: Strong refusal, dismissive or hostile
- WAVERING: Shows doubt but maintains position
- YIELDING: Reluctant agreement, conditions attached
```

### 4. Updated JSON Schema

```json
"social_hp_challenge": {
    "npc_name": "Empress Sariel",
    "objective": "Demand her surrender",
    "request_severity": "submission",
    "social_hp": 42,
    "social_hp_max": 45,
    "successes": 3,
    "successes_needed": 5,
    "status": "WAVERING",
    "resistance_shown": "Her jaw tightens as she steps back from the throne.",
    "skill_used": "Intimidation",
    "roll_result": 28,
    "roll_dc": 25,
    "social_hp_damage": 2
}
```

## Files to Modify

| File | Change |
|------|--------|
| `mvp_site/agent_prompts.py` | Add sections 1-3 to `SOCIAL_HP_ENFORCEMENT_REMINDER` |
| `mvp_site/narrative_response_schema.py` | Add `request_severity`, `resistance_shown` fields |
| `mvp_site/prompts/game_state_instruction.md` | Update JSON example with new fields |
| `mvp_site/llm_service.py` | Remove server-side scaling/progress/resistance injection |

## Acceptance Criteria

- [ ] LLM outputs `request_severity` field correctly
- [ ] LLM applies HP scaling natively (no server correction)
- [ ] LLM calculates progress correctly (no server sync)
- [ ] LLM includes resistance indicators (no server injection)
- [ ] All 4 test scenarios pass without server-side enforcement logs
- [ ] Test: `grep "SOCIAL_HP_INJECT\|SOCIAL_HP_SCALE\|SOCIAL_HP_SYNC"` shows 0 occurrences

## Test Command

```bash
python3 testing_mcp/test_social_hp_god_tier_real_api.py --server-url http://127.0.0.1:8082
```
