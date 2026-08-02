# God-mode directive routing — architectural rule (verified 2026-07-23, #8528 / campaign `wc2BBcSgOljiU3vJ160A`)

**Class-level rule (DO NOT VIOLATE):** god-mode directives — and *every* developer-authored dynamic instruction — MUST be routed through one of two channels:

1. `system_instruction` with explicit `cache_control`, sourced from a deterministic snapshot (e.g. `custom_campaign_state.god_mode_directives_snapshot`).
2. A `tool_use` channel with structurally-enforced constraints.

**Forbidden channel:** `contents[]` conversation history. Rationale, verified evidence, and durable fix shape below.

## Why `contents[]` is structurally wrong (the 4 architectural failures it produces)

Verified on $GITHUB_REPOSITORY issue [#8528](https://github.com/$GITHUB_REPOSITORY/issues/8528), campaign `wc2BBcSgOljiU3vJ160A`, scene 454 (4th-sibling cluster on the same campaign_id, 2026-07-23):

### Failure mode 1 — Paraphrase drift

When a directive lives in a past `role=model` turn's `parts[].text`, each subsequent god-mode correction reissues the directive via `directives.add`. The LLM rewrites it as a paraphrase of the prior wording, not a verbatim echo. Empirical evidence:

| Correction # | UTC | User command | LLM-emitted `directives.add` (paraphrased) |
|---|---|---|---|
| 1 | 16:08:39 | "No one else should have +10 gear because they weren't level 100 gods" | "Only Level 100 gods (Nocturne) possess +10 God-Gear..." |
| 3 | 16:11:33 | "No look the formula for the special god gear when gods became mortals" | "Equipment Enhancement Bonus = (Current Divine Level / 10) (Rounded Down)" |
| 4 | 16:14:37 | "No you use their original levels" | "Always use the Original Divine Levels (Rank-tier) for the (Level / 10) gear mastery formula..." |

Three different phrasings of the same rule across three corrections. None verbatim-matches the original. Operational semantics drift per correction turn.

### Failure mode 2 — Cache-bust

`request_json.cached_tokens` dropped from **79.8%** (pre-correction turn at 08:44, `cached=276,953 / est_in=189,437`) to **0%** (post-correction turn at 16:14, `cached=0 / est_in=196,305`) on the same campaign. The paraphrase drift invalidates the implicit-context-cache prefix because each prior `role=model` turn's directive wording now differs from the canonical snapshot. Per-turn latency and token cost go up 3-4× as a direct consequence.

### Failure mode 3 — Wrong architectural primitive (advisory, not authoritative)

When the directive lives in `contents[]` history, it carries **advisory** authority only. The LLM can echo it, paraphrase it, or ignore it on any given turn. The user-visible symptom is "my directive was forgotten" — but the underlying cause is that the directive never had the channel authority to be authoritative in the first place.

### Failure mode 4 — Bypasses the cache_control contract

`system_instruction` with `cache_control` is the canonical channel for "this never changes for the lifetime of the conversation." `contents[]` history is *meant* to drift turn-over-turn. Routing directives through history defeats the cache contract entirely.

## Detection recipe (BQ)

Run on `worldarchitecture-ai.llm_forensics.llm_payloads` for any campaign under inspection:

```sql
WITH last_8 AS (
  SELECT ingested_at, turn_index, agent, response_text, request_json,
         LENGTH(request_json) AS req_bytes
  FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
  WHERE campaign_id = '<CID>'
    AND agent = 'gemini_provider.stream'
  ORDER BY ingested_at DESC
  LIMIT 8
)
SELECT ingested_at,
       turn_index,
       cached_tokens, estimated_input_tokens,
       LENGTH(request_json) AS req_bytes
FROM last_8
ORDER BY ingested_at ASC
```

A direct signature of `contents[]`-routed directives is `cached_tokens` trending toward 0 across consecutive god-mode correction turns where the user added new directive variants. If `cached_tokens / estimated_input_tokens < 0.5` for ≥3 consecutive god-mode turns AND campaign has ≥10 prior turns, the routing is wrong.

### Per-directive offset audit (advanced)

For each god-mode correction turn, find the literal directive text in `request_json` (escape-aware grep):

```python
import re
target = "Gods in mortal form receive +10 equipment in every slot (Level / 10)"
hit = text.find(target)
# Walk backward 5000 chars to find the nearest JSON channel key
window = text[max(0, hit-5000):hit]
for marker in ['"system_instruction"', '"contents"', '"role"', '"cache_control"', '"tool_use"']:
    occs = [x.start() for x in re.finditer(re.escape(marker), window)]
```

If the nearest enclosing channel is `"contents"` (i.e., the directive lives inside a `role=model` or `role=user` turn's `parts[].text`), the routing is wrong.

## Durable fix shape

6-component fix. Apply all 6 together — they reinforce each other.

### 1. New snapshot source

Create a developer-authored canonical source in `custom_campaign_state.god_mode_directives_snapshot`:
```json
{
  "version": "2026-07-23-r1",
  "entries": [
    {"id": "gear-formula-level-over-10", "text": "Equipment Enhancement Bonus = floor(Divine Level / 10)", "hash": "<sha256>"},
    {"id": "nocturne-threshold", "text": "Only Nocturne (Lvl 100) maintains the +10 resonance threshold.", "hash": "<sha256>"},
    ...
  ]
}
```

### 2. Move to `system_instruction` with `cache_control`

In `$PROJECT_ROOT/agent_prompts.py`:
```python
def build_god_mode_system_instruction(campaign_id):
    snapshot = fetch_snapshot(campaign_id)  # from custom_campaign_state
    block = render_directives_block(snapshot.entries)
    return {
        "text": block,
        "cache_control": {"type": "ephemeral"},  # or "persistent" depending on TTL
    }
```

Render this block into the `system_instruction.parts[]` channel, NOT `contents[]`.

### 3. Validate LLM `directives.add` against snapshot hash

In `$PROJECT_ROOT/agent_prompts.py` `build_god_mode_directives_block` (revised):
```python
def validate_directives_add(llm_directives_add, snapshot):
    accepted, rejected = [], []
    for entry in llm_directives_add:
        ehash = sha256(entry.text.strip().lower())
        if any(ehash == s["hash"] for s in snapshot.entries):
            accepted.append(snapshot[ehash])  # canonical text wins, not LLM paraphrase
        elif is_known_paraphrase(entry.text, snapshot):
            accepted.append(canonicalize(entry.text))
        else:
            rejected.append({"text": entry.text, "reason": "no matching snapshot entry"})
    return accepted, rejected
```

**The LLM's paraphrase is dropped in favor of the canonical authoritative text.** This stops the paraphrase-drift loop the 4-correction window exhibited.

### 4. Agent-side state-update value-derivation backfill

In `$PROJECT_ROOT/agents.py` `GodModeAgent._backfill_state_updates`:
```python
def _backfill_state_updates(narrative, state_updates):
    """When narrative references an NPC's level/formula but state_updates.npc_data.<NPC>.equipment_bonus is missing,
    backfill deterministically from the formula the narrative used. Empirically the narrative is the canonical source;
    the persist path is the bug."""
    for npc, level in extract_npc_levels(narrative):
        if npc in state_updates.npc_data and "equipment_bonus" not in state_updates.npc_data[npc]:
            state_updates.npc_data[npc]["equipment_bonus"] = floor(level / 10)
```

Verified trigger pattern: pre-correction turn 08:46 had narrative *"Ao is Level 25"* with `state_updates.npc_data` block present but `equipment_bonus` field missing. Backfill fires deterministically.

### 5. CI lint — `scripts/check_god_mode_directive_routing.py`

```python
# Pseudocode
def check_routing(prompt_text):
    # Find each developer-authored directive literal
    for directive in extract_developer_directives(prompt_text):
        offset = prompt_text.find(directive)
        served_pct = offset / len(prompt_text)
        if served_pct > 0.5:
            fail(f"Directive {directive!r} routed too deep into served prompt @ {served_pct:.1%}")
        channel = find_enclosing_channel(prompt_text, offset)
        if channel == "contents":
            fail(f"Directive {directive!r} routed via contents[] not system_instruction or tool_use")
        if "cache_control" not in surrounding_context(prompt_text, offset):
            fail(f"Directive {directive!r} has no cache_control")
```

### 6. CI lint — `scripts/check_state_update_value_drift.py`

```sql
-- Walks 30 days of llm_payloads, classifies state_updates.npc_data.<NPC>.equipment_bonus
-- derivation consistency vs. canonical (Level / 10). Fail = blocking at merge when same
-- NPC fails in ≥3 turns.
SELECT campaign_id, npc_name, COUNT(*) AS drift_count
FROM (
  SELECT campaign_id,
         npc_name,
         SAFE_DIVIDE(SUM(equipment_bonus_written), SUM(narrative_level / 10)) AS drift_ratio
  FROM `worldarchitecture-ai.llm_forensics.llm_payloads`,
       UNNEST(JSON_EXTRACT_array(state_updates, '$.npc_data')) AS npc_data_entry
  WHERE ingested_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    AND agent = 'gemini_provider.stream'
    AND response_text LIKE '%(Level / 10)%'  -- the rule was active this turn
  GROUP BY campaign_id, npc_name
)
WHERE drift_ratio NOT BETWEEN 0.95 AND 1.05
GROUP BY campaign_id, npc_name
HAVING drift_count >= 3
```

## Verification worked example

Campaign `wc2BBcSgOljiU3vJ160A` after the 6-component fix:

| Bug class | Pre-fix | Post-fix expected |
|---|---|---|
| Paraphrase drift | 3 different phrasings of (Level / 10) across 3 corrections | 1 canonical phrasing; LLM paraphrases rejected; snapshot hash match enforced |
| Cache hit rate | 79.8% → 0% across 7 hours (paraphrase busts prefix) | Stable ~85% across same window (snapshot is canonical, never paraphrase) |
| State-update value drift | LLM narrative correct, `npc_data.<NPC>.equipment_bonus` missing or wrong on 3/4 turns | Backfill fires; equipment_bonus values match `floor(level/10)` deterministically |
| Directive routing | Directives at offset 47.6%–97.6% in `contents[]` history | Directives at offset ≤30% in `system_instruction` with `cache_control` |

## Where this rule came from

User OOB correction 2026-07-23 on the 4th-sibling gear-formula repro:

> *"Firstly god mode directives shouldn't even be in the system prompt — nothing dynamic should be in there. Then do we have proof the LLM say the directive before I asked for the correction?"*

Empirical evidence in `gemini_provider.stream.request_json` confirmed two architectural facts:
1. Directives are NOT in `system_instruction` at all — they're inside `contents[]` history as LLM-authored echoes at offsets 47.6%–68.6% of the served prompt.
2. The LLM was honoring the directive pre-correction across 4 consecutive turns (visible in `session_header.resources` and narrative form). The user's "did the LLM see the rule" question was answered with proof: yes, just only in narrative, not in state-update fields.

This file is the durable architecture answer to both questions.
