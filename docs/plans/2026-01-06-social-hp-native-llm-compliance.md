# Social HP Native LLM Compliance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move Social HP scaling, progress, and resistance indicators into native LLM output by updating prompts + schema, and remove server-side enforcement.

**Architecture:** Keep Social HP rules in prompts and structured response validation. Server should only pass through LLM output (no scaling, no progress sync, no resistance injection). Add unit tests to lock schema fields, prompt content, and removal of server-side enforcement markers.

**Tech Stack:** Python (pytest), prompt markdown, core service code in `mvp_site/`.

---

### Task 1: Add schema tests for new Social HP fields

**Files:**
- Create: `mvp_site/tests/test_social_hp_challenge_schema.py`
- Modify: `mvp_site/narrative_response_schema.py`

**Step 1: Write the failing test**

```python
from mvp_site.narrative_response_schema import NarrativeResponse


def _base_social_hp() -> dict:
    return {
        "npc_name": "Empress Sariel",
        "objective": "Demand her surrender",
        "social_hp": 42,
        "social_hp_max": 45,
        "successes": 3,
        "successes_needed": 5,
        "status": "WAVERING",
        "skill_used": "Intimidation",
        "roll_result": 28,
        "roll_dc": 25,
        "social_hp_damage": 2,
    }


def test_social_hp_challenge_normalizes_request_severity_and_resistance():
    payload = _base_social_hp()
    payload["request_severity"] = "Submission"
    payload["resistance_shown"] = "Her jaw tightens as she steps back."

    response = NarrativeResponse(narrative="n", social_hp_challenge=payload)

    assert response.social_hp_challenge["request_severity"] == "submission"
    assert response.social_hp_challenge["resistance_shown"] == "Her jaw tightens as she steps back."


def test_social_hp_challenge_invalid_request_severity_defaults_to_information():
    payload = _base_social_hp()
    payload["request_severity"] = "extortion"

    response = NarrativeResponse(narrative="n", social_hp_challenge=payload)

    assert response.social_hp_challenge["request_severity"] == "information"
```

**Step 2: Run test to verify it fails**

Run: `pytest mvp_site/tests/test_social_hp_challenge_schema.py -v`

Expected: FAIL because `request_severity` and `resistance_shown` are not validated yet.

**Step 3: Write minimal implementation**

Update `mvp_site/narrative_response_schema.py`:

```python
SOCIAL_HP_CHALLENGE_SCHEMA = {
    "npc_id": str,
    "npc_name": str,
    "objective": str,
    "request_severity": str,  # information | favor | submission
    "social_hp": int,
    "social_hp_max": int,
    "successes": int,
    "successes_needed": int,
    "status": str,
    "resistance_shown": str,  # required resistance indicator text
    "skill_used": str,
    "roll_result": int,
    "roll_dc": int,
    "social_hp_damage": int,
}

VALID_SOCIAL_HP_REQUEST_SEVERITY = {"information", "favor", "submission"}
```

Then in `_validate_social_hp_challenge`:

```python
        validated["npc_id"] = _coerce_str(social_hp_challenge.get("npc_id", ""))
        validated["npc_name"] = _coerce_str(social_hp_challenge.get("npc_name", ""))
        validated["objective"] = _coerce_str(social_hp_challenge.get("objective", ""))

        request_severity = _coerce_str(
            social_hp_challenge.get("request_severity", "information")
        ).lower()
        if request_severity not in VALID_SOCIAL_HP_REQUEST_SEVERITY:
            logging_util.warning(
                f"Invalid social_hp_challenge request_severity '{request_severity}', defaulting to information"
            )
            request_severity = "information"
        validated["request_severity"] = request_severity

        validated["resistance_shown"] = _coerce_str(
            social_hp_challenge.get("resistance_shown", "")
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest mvp_site/tests/test_social_hp_challenge_schema.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add mvp_site/tests/test_social_hp_challenge_schema.py mvp_site/narrative_response_schema.py
git commit -m "test: cover social hp request severity and resistance fields"
```

---

### Task 2: Update Social HP prompts + docs for new fields and rules

**Files:**
- Create: `mvp_site/tests/test_social_hp_prompt_content.py`
- Modify: `mvp_site/agent_prompts.py`
- Modify: `mvp_site/prompts/game_state_instruction.md`

**Step 1: Write the failing test**

```python
from pathlib import Path

from mvp_site import agent_prompts


def test_social_hp_enforcement_reminder_mentions_request_severity_and_resistance():
    reminder = agent_prompts.SOCIAL_HP_ENFORCEMENT_REMINDER
    assert "REQUEST SEVERITY" in reminder
    assert "request_severity" in reminder
    assert "resistance_shown" in reminder
    assert "PROGRESS TRACKING" in reminder


def test_game_state_instruction_documents_request_severity_and_resistance():
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "game_state_instruction.md"
    content = prompt_path.read_text(encoding="utf-8")
    assert "request_severity" in content
    assert "resistance_shown" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest mvp_site/tests/test_social_hp_prompt_content.py -v`

Expected: FAIL because the new fields are not present yet.

**Step 3: Write minimal implementation**

Replace `SOCIAL_HP_ENFORCEMENT_REMINDER` in `mvp_site/agent_prompts.py` with:

```python
SOCIAL_HP_ENFORCEMENT_REMINDER = """
## 🚨 CRITICAL: SOCIAL HP ENFORCEMENT ACTIVE (GOD-TIER NPC DETECTED)

**This scene contains a high-tier NPC (God/Primordial/King). The Social HP system is MANDATORY.**

### 🛑 STOP AND READ:
You MUST track "Social HP" for this NPC. Single persuasion rolls CANNOT succeed fully.
You MUST include BOTH:
1. The `social_hp_challenge` JSON field (REQUIRED - for backend tracking)
2. The [SOCIAL SKILL CHALLENGE:] box in narrative (for player visibility)

### MANDATORY JSON OUTPUT - Include in response:

```json
"social_hp_challenge": {
    "npc_name": "{NPC Name}",
    "objective": "{What player wants}",
    "request_severity": "information|favor|submission",
    "social_hp": X,
    "social_hp_max": Total,
    "successes": 0,
    "successes_needed": 5,
    "status": "RESISTING",
    "resistance_shown": "{verbal/physical resistance}",
    "skill_used": "Persuasion",
    "roll_result": 0,
    "roll_dc": 0,
    "social_hp_damage": 0
}
```

### ALSO include the text box in narrative for player visibility:

    [SOCIAL SKILL CHALLENGE: {NPC Name}]
    Objective: {What player wants}
    NPC Social HP: {X}/{Total} (god=15+, king=8-12, lord=5-8)
    Progress: {current}/{required} successes
    Status: RESISTING

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

### PROGRESS TRACKING

Progress is calculated from damage dealt to Social HP:

```
successes = social_hp_max - social_hp_current
```

**Damage per check:**
- Success (beat DC): 2 damage
- Close fail (within 5 of DC): 1 damage
- Hard fail (miss by 6+): 0 damage

**Status thresholds:**
- 0-1 successes: RESISTING
- 2-3 successes: WAVERING
- 4+ successes: YIELDING
- 5 successes: Challenge complete (NPC agrees)

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

### REQUIRED BEHAVIOR:
1. **Resistance Indicators**: Include verbal/physical resistance in narrative + `resistance_shown` field.
2. **No Instant Success**: Even on a Natural 20, a God-tier NPC DOES NOT yield immediately. They take Social HP damage instead.
3. **Tracking**: Update BOTH the JSON field AND the narrative box.

❌ FAILURE TO INCLUDE `social_hp_challenge` JSON FIELD IS A SYSTEM ERROR.
"""
```

Update `mvp_site/prompts/game_state_instruction.md` Social HP field list to include:

```markdown
  - `request_severity`: (string) **REQUIRED** information | favor | submission
  - `successes_needed`: (number) Required successes to win (always 5)
  - `resistance_shown`: (string) **REQUIRED** resistance indicator text (verbal or physical)
```

Also replace the old `npc_response` line with `resistance_shown`, and add a short note under Social HP describing the progress formula:

```markdown
  - Progress formula: `successes = social_hp_max - social_hp_current` (cap at 5)
```

**Step 4: Run test to verify it passes**

Run: `pytest mvp_site/tests/test_social_hp_prompt_content.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add mvp_site/tests/test_social_hp_prompt_content.py mvp_site/agent_prompts.py mvp_site/prompts/game_state_instruction.md
git commit -m "docs: update social hp prompts for severity, progress, resistance"
```

---

### Task 3: Remove server-side Social HP enforcement

**Files:**
- Create: `mvp_site/tests/test_social_hp_server_enforcement_removed.py`
- Modify: `mvp_site/llm_service.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_social_hp_server_enforcement_markers_removed():
    content = Path(__file__).resolve().parents[1] / "llm_service.py"
    text = content.read_text(encoding="utf-8")

    assert "SOCIAL_HP_INJECT" not in text
    assert "SOCIAL_HP_SCALE" not in text
    assert "SOCIAL_HP_PROGRESS_SYNC" not in text
    assert "SOCIAL_HP_RESISTANCE" not in text
```

**Step 2: Run test to verify it fails**

Run: `pytest mvp_site/tests/test_social_hp_server_enforcement_removed.py -v`

Expected: FAIL because enforcement markers are still present.

**Step 3: Write minimal implementation**

In `mvp_site/llm_service.py`, remove the entire server-side Social HP enforcement block that:
- Detects persuasion keywords for high-tier NPCs
- Scales Social HP max
- Syncs progress / status
- Injects Social HP box
- Injects resistance indicators
- Applies server-side damage

Specifically remove the `if high_tier_npcs and not is_god_mode_command:` block starting near the `# Check for persuasion-related keywords in user input` comment (around line ~4060) through the end of the `# 🚨 SERVER-SIDE SOCIAL HP DAMAGE TRACKING` section.

**Step 4: Run test to verify it passes**

Run: `pytest mvp_site/tests/test_social_hp_server_enforcement_removed.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add mvp_site/tests/test_social_hp_server_enforcement_removed.py mvp_site/llm_service.py
git commit -m "refactor: remove server-side social hp enforcement"
```

---

## Final Verification

1. `rg "SOCIAL_HP_INJECT|SOCIAL_HP_SCALE|SOCIAL_HP_PROGRESS_SYNC|SOCIAL_HP_RESISTANCE" mvp_site/llm_service.py` → no matches
2. (Optional) Run the real API test from the design doc:

```bash
python3 testing_mcp/test_social_hp_god_tier_real_api.py --server-url http://127.0.0.1:8082
```

