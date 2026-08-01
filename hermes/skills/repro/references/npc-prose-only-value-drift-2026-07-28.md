---
name: npc-prose-only-value-drift-2026-07-28
description: 8th sub-class of npc-status-persistence-bug — LLM writes wrong number in narrative parenthetical but does NOT corrupt npc_data[*].level. Distinct from the 7th sub-class (state-write drift).
---

# Prose-only value-derivation drift (sub-class 8, NEW 2026-07-28)

## TL;DR

A new sub-class of `npc-status-persistence-bug` surfaced on 2026-07-28
in campaign `fZGt3Rhd243H8rr7itto` ("Valeria iseki (wrong npc level)").
The LLM emits a **wrong number in a narrative parenthetical** (e.g.
`"Baronet Kaelen Harth (Lvl 8) is notably absent"`) AND does NOT emit
`state_updates.npc_data[<NPC>].level` at all in that turn. The canonical
state in Firestore stays correct (`npc_data.Baronet Kaelen Harth.level = 3`)
— only the prose is off-canon. The user has to issue a god-mode correction
to fix what the LLM should have written.

This is structurally distinct from the **7th sub-class** (state-write
drift, see `references/state-update-value-derivation-drift.md`) where
the LLM DID write to `state_updates.npc_data` with the wrong numeric. The
fix shape is different: sub-class 7 needs a value-derivation block pre-`state_updates`;
sub-class 8 needs either a runtime-injected parenthetical from
`npc_data[*].level` or a prompt rule forcing the LLM to cross-check
`npc_data[*].level` before writing narrative parentheticals.

## Signature

| Sub-class | Narrative | `state_updates.npc_data` written? | Canonical state corrupted? |
|---|---|---|---|
| 7 (state-write drift, #8528) | ✅ narrative derivation correct | ✅ present | ❌ wrong numeric |
| **8 (prose-only drift, #fZGt3Rhd243H8rr7itto)** | ❌ wrong parenthetical | ❌ absent | ✅ stays canonical |

The smoking gun for sub-class 8:
- `state_updates.npc_data` block is **absent** for the affected NPC (vs. sub-class 7 where it's present-and-wrong)
- `npc_data.<NPC>.<field>` in Firestore matches the canonical core_memory (vs. sub-classes 1-3 where it's missing/wrong)
- The LLM had the canonical truth in BOTH structured state AND core_memories lore at ≤30% of the served prompt
- The drift is purely in narrative — a parenthetical like `(Lvl N)` referencing the wrong number

## Verified worked example (2026-07-28, campaign `fZGt3Rhd243H8rr7itto`)

| Scene | LLM emitted (prose) | Canonical truth | Status |
|---|---|---|---|
| 49 | "Dorian (Lvl 14)" | core_memory: "Sir Dorian Vane is a Level 14 Rune-Vanguard of the Special-class" | ✅ correct |
| 50 | "Dorian corrected to Lvl 9" | User-driven god-mode correction demoted 14→9 | user-side change |
| **51** | **"Baronet Kaelen Harth (Lvl 8) is notably absent"** | `npc_data.Baronet Kaelen Harth.level = 3` AND core_memory: "Calibration: Academy peers are mostly Level 1-2, with elites at Level 3; Valeria's Level 6 status is a freakish anomaly" | 🟥 **wrong** |
| **52** | **"Recalibrated ... to Level 3. His previous mention as Level 8 was an error that violated the established Academy power scaling (Peers: Lvl 1-2, Elites: Lvl 3, Valeria Anomaly: Lvl 6)"** | — | user's correction |

### BQ raw-request evidence (Scene 51 StoryModeAgent, ts 2026-07-29T03:14:52Z, `req_bytes=790909`)

| Pattern in `gemini_provider.stream.request_json` | byte offset | % into prompt |
|---|---|---|
| `npc_data` block start (with `Kaelen.level=3`) | 15047 | 1.9% |
| `Baronet Kaelen Harth` field in `npc_data` | 116007 | **14.7%** |
| `Calibration` canonical lore header | 88832 | 11.2% |
| `Academy peers are mostly Level 1-2` (canonical rule) | 211907 | **26.8%** |
| `Universal Ceilings: ... Level caps Runeless (L4) ... Special-class (L14) ... Highlanders (L20)` | 212906 | 26.9% |

**Both the structured state AND the canonical lore were inside the served prompt at offsets the LLM should attend to (under 30%, well above the lost-in-the-middle threshold).** The LLM had every fact it needed. It still emitted `Lvl 8` in the narrative and **did NOT write `npc_data.Kaelen.level=8`** in scene 51's `state_updates` (scene 51 wrote only `player_character_data`, `world_data`, `rest_taken`, `custom_campaign_state`). The level-3 value in `npc_data` survives the bug; only the prose is wrong.

## Diagnostic recipe (1 SQL query, 1 minute)

```sql
-- For each lore pattern, get the byte offset + percentage into the served prompt.
-- A 1-query-per-pattern loop, with the row's total bytes as denominator.
SELECT FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', ingested_at) AS ts,
       agent,
       REGEXP_INSTR(CAST(request_json AS STRING), r'<Npc Name>') AS npc_offset,
       REGEXP_INSTR(CAST(request_json AS STRING), r'<calibration-lore-keyword>') AS lore_offset,
       REGEXP_INSTR(CAST(request_json AS STRING), r'<canonical-rule-text>') AS rule_offset,
       LENGTH(CAST(request_json AS STRING)) AS total_bytes
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE campaign_id = '<CID>'
  AND agent = 'StoryModeAgent'
  AND ingested_at BETWEEN TIMESTAMP('<BEFORE_TS>') AND TIMESTAMP('<AFTER_TS>')
  AND REGEXP_CONTAINS(response_text, r'\(Lvl\s*\d+\)')
ORDER BY ingested_at DESC
LIMIT 5
```

If both `npc_offset` AND `rule_offset` are under 30% of the served prompt,
the LLM had the canonical anchor; the bug is prose-only; the
`state_updates` payload for the turn confirms the field was absent.

**Then check `state_updates.npc_data` for the affected NPC** via Firestore
direct read or `download_campaign.py`. If `npc_data` was NOT written at
all that turn, this is sub-class 8 (prose-only), not sub-class 7
(state-write).

## Fix shape (2 components, NOT a backend-enforced invariant)

**Component 1 — Runtime injection (durable fix).** The runtime should
inject a deterministic parenthetical from `npc_data[*].level` into the
narrative output rather than trusting the LLM's free-recall. This is the
model-side equivalent of the deterministic-canonical reducer pattern in
`world_logic.py` — the same pattern that already drives the deterministic
NPC status writes from `state_updates`. Land in
`$PROJECT_ROOT/narrative_renderer.py` (or wherever parentheticals are
post-processed before the SSE stream).

**Component 2 — Prompt-side hedge.** Add a rule to
`$PROJECT_ROOT/prompts/narrative_system_instruction.md` (and mirror in
`planning_protocol.md`):

> *"Before writing `<NPC> (Lvl N)` in narrative prose, verify N matches
> `npc_data[<NPC>].level` exactly. If the canonical state is missing,
> omit the parenthetical rather than free-recall a number."*

This is the soft hedge — the LLM still has the freedom to ignore it under
plot pressure. Component 1 is the durable fix.

**Anti-pattern — DO NOT propose a backend invariant.** Per
`AGENTS.md` "Root-cause-first prompt discipline": fix prompt/schema
contradictions first. Component 1 above is a *runtime render* change, not
a backend enforcement that hard-stops the LLM. Component 2 is the prompt
fix. The fix is on the render/narrative side, NOT in `state_updates`
validation.

## Cross-references

- `references/npc-status-persistence-bug.md` "Sub-class 8" section — the
  raw taxonomy entry that this file expands on.
- `references/state-update-value-derivation-drift.md` "Prose-only cousin"
  section — the 7th sub-class cousin (state-write drift).
- `references/bq-llm-payload-truncation-pitfall.md` "REGEXP_INSTR
  offset + LENGTH percentage recipe" — the canonical diagnostic for any
  "did the LLM receive the rule" report.
- `references/phenotype-lock-static-evidence.md` — the 3 static-evidence
  greps that should run first (code-symbol, prior-export, sibling-issue).
- Verified first instance: 2026-07-28, campaign `fZGt3Rhd243H8rr7itto`
  scene 51. No prior sibling on this CID. If a 2nd sibling fires on this
  campaign, set a 3rd-sibling cluster trigger watch and branch a fresh
  worktree for the prompt-side fix.
