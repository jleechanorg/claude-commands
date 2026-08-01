# God-mode directive writeback gap — the canonical-state asymmetry

**Class-level rule (DO NOT VIOLATE):** the same writeback discipline that
`select_memories_by_budget()` applies to `core_memories[]` MUST also apply to
`god_mode_directives[]`. Whatever the user types in a god-mode turn — and
whatever the LLM acknowledges in `god_mode_response` — must land as a structured
artifact in `custom_campaign_state.god_mode_directives_snapshot` with hash +
timestamp, not just be a paraphrased echo in conversation history.

Verified on $GITHUB_REPOSITORY issue [#8528](https://github.com/$GITHUB_REPOSITORY/issues/8528),
campaign `wc2BBcSgOljiU3vJ160A`, scene 454 (4th-sibling cluster, 2026-07-23).
This reference is the durable-fix answer to:

> *"Why don't we have a record of [Ao's Original Level = 100] anywhere?"*

The answer is asymmetry: **the persistence layer has a `select_memories_by_budget()`
writeback hook for narrative compression into `core_memories[]`, but no
corresponding hook for god-mode responses.** Story entries get compressed and
persisted; god-mode entries only survive as LLM-authored conversation-history
paraphrases.

## The asymmetry in concrete terms

| Channel | Where it lives | When it's written | What survives | Verifiable? |
|---|---|---|---|---|
| `core_memories[]` (narrative) | `custom_campaign_state.core_memories` | Every LLM turn via `select_memories_by_budget` writeback | Verbatim narrative summary, canonical | ✅ read directly |
| `god_mode_directives[]` (god-mode) | `contents[]` history (LLM-authored echoes) | **Never persisted verbatim** | Paraphrases, drifting each turn | ❌ only via grep of `request_json` |

Concretely: the user typed `Select one. Gear formula when god turned mortal` and the LLM's
god-mode response wrote `directives.add = ["Use Original Divine Levels for the (Level/10) formula..."]`.
Four corrections later, the LLM's `directives.add` block paraphrased the rule 3
different ways. NONE of those paraphrases landed in `custom_campaign_state` as a
structured entry. The user's original wording is gone — only the LLM's most
recent rephrasing survives, and that's in conversation history only.

For comparison, `core_memories[]` has the opposite problem solved: the
`select_memories_by_budget()` writeback hook (verified at
`$PROJECT_ROOT/memory_utils.py:186`) fires on every LLM turn and persists the
compressed narrative state canonically. The pattern exists; it just wasn't
applied to god-mode.

## Why this gap exists (the architectural reason)

The narrative writeback exists because `narrative_system_instruction.md` instructs
the LLM to maintain a compressed `core_memories` array as part of
`state_updates`. The compliance path is well-tested (cf. PR #8443, 2026-07-18,
factoring the canonical-state anchor into the prompt layer).

The god-mode writeback does NOT exist because `god_mode_instruction.md` instructs
the LLM to put `directives.add` and `directives.drop` in `god_mode_response` as
planner output, NOT as `state_updates`. The "directive is a planning artifact"
paradigm is correct for *operational* directives (planning block annotations),
but WRONG for *canonical* directives (the user's stated intent).

**Two distinct directive categories exist and the framework conflates them:**

1. **Operational directives** — short-lived, "the next scene should..." framing.
   Belong in `god_mode_response.planning_block.directives`, persisted as
   planner output, treated as advisory.

2. **Canonical directives** — persistent, "from now on, the rules are..."
   framing. Belong in `custom_campaign_state.god_mode_directives_snapshot` as
   structured `{hash, text, added_at, source: "user"|"llm_consensus"}` entries,
   writeback-fired on every turn, treated as authoritative.

The LLM doesn't distinguish between these two types in its current emission
shape — both go into `god_mode_response.directives.add`. The framework needs a
separation: detect directive type from the user's prose (patterns like
"from now on", "remember:", "all future turns", "canonical"), and route the
canonical ones through the snapshot writeback.

## Detection recipe (BQ)

```sql
-- Compare the user's directive (lives in prompt_contents) with what lands in
-- custom_campaign_state.god_mode_directives_snapshot. Discrepancy = writeback gap.
WITH god_mode_turns AS (
  SELECT ingested_at, turn_index, agent,
         response_text,
         -- the user's directive-as-input for this turn:
         JSON_VALUE(request_json, '$.contents[-1].parts[0].text') AS user_input
  FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
  WHERE campaign_id = '<CID>'
    AND agent = 'GodModeAgent'
    AND ingested_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
)
SELECT turn_index, ingested_at, user_input,
       -- count the directives the LLM emitted that ought to land in snapshot:
       ARRAY_LENGTH(JSON_EXTRACT_array(response_text, '$.directives.add')) AS llm_directives_count
FROM god_mode_turns
WHERE LOWER(user_input) LIKE '%from now on%'
   OR LOWER(user_input) LIKE '%remember%'
   OR LOWER(user_input) LIKE '%canonical%'
   OR LOWER(user_input) LIKE '%always%'
ORDER BY ingested_at ASC
```

**Direct evidence of the writeback gap (verified 2026-07-23 on
`wc2BBcSgOljiU3vJ160A` scene 454):**

| User input (verbatim) | LLM-emitted `directives.add` count | Did it land in Firestore snapshot? |
|---|---|---|
| "No one else should have +10 gear because they weren't level 100 gods" | 1 | ❌ no verifiable record |
| "No you forgot the whole formula double check it" | 1 (different phrasing) | ❌ |
| "No look the formula for the special god gear when gods became mortals" | 2 | ❌ |
| "No you use their original levels" | 3 | ❌ |

For each of 4 user-introduced canonical directives, 0 of them landed in the
canonical state. Per `_should_reject_directive` filter patterns verified by the
existing `references/god-mode-directive-enforcement.md` skill ref, the
advisory-only directive model was the deliberate design — but it never
specified what to do for *user-introduced canonical directives*. That hole is
the writeback gap.

## Durable fix shape

Apply BOTH halves; neither alone is sufficient.

### Half 1 — Snapshot writeback on every god-mode turn

Mirror the existing `select_memories_by_budget` writeback pattern. In
`$PROJECT_ROOT/agent_prompts.py`:

```python
def writeback_god_mode_directives(snapshot, llm_directives_add, llm_directives_drop, turn_index, source):
    """Persist each canonical directive as a structured entry. Source tag identifies provenance."""
    accepted, rejected = [], []
    for entry in llm_directives_add:
        ehash = sha256(entry.strip().lower())
        if any(ehash == s["hash"] for s in snapshot.entries):
            continue  # already canonical
        canonical = find_canonical_form(entry) or entry  # parser if available
        snapshot.entries.append({
            "id": f"turn-{turn_index}-directive-{len(snapshot.entries)}",
            "text": canonical,
            "hash": ehash,
            "added_at": now_iso(),
            "source": source,  # "user" | "llm_consensus"
        })
        accepted.append(canonical)
    for entry in llm_directives_drop:
        ehash = sha256(entry.strip().lower())
        snapshot.entries = [s for s in snapshot.entries if s["hash"] != ehash]
        accepted.append(f"dropped:{entry}")
    return snapshot, accepted, rejected


def find_canonical_form(llm_directive_text):
    """If the LLM's wording is a known paraphrase of a snapshot entry, return the snapshot canonical text.
    Otherwise return None (the directive is a new LLM invention — flag for human review)."""
    # Use embedding similarity or pattern match against snapshot; default nil
    # in the absence of evidence — better to require human review than to canonicalize silently.
    return None
```

**Wiring:** call `writeback_god_mode_directives` at the end of every
`GodModeAgent._apply_response` turn. The 4-component fix in
`references/state-update-value-derivation-drift.md` already covers the
state-update side; this gap is about the directive-as-text side.

### Half 2 — Read snapshot into the served prompt

After writeback, the snapshot becomes the canonical source for the next
turn's `system_instruction` directive block. Render order:

1. Pull `custom_campaign_state.god_mode_directives_snapshot` (the
   developer-authored canonical entries with hash + added_at).
2. Apply `select_directives_by_budget()` cap (PR #8531, MAX_GOD_MODE_DIRECTIVES_RENDERED=50, newest-first) to the snapshot's entries.
3. Render the resulting subset into `system_instruction.parts[]` with explicit `cache_control`, NOT `contents[]` history. This is the routing fix from
   `references/god-mode-directive-routing-architecture.md`.

The writeback + read-snapshot loop produces a stable, hashed, versioned source
of truth that survives paraphrase drift and cache-busting. Without it, the
user's directive lives only as long as the conversation lasts.

## Cross-references

- `references/god-mode-directive-routing-architecture.md` — companion reference
  for the channel-side fix (where directives travel). THIS reference covers
  the persistence-side fix (whether directives get written back at all).
- `references/state-update-value-derivation-drift.md` — the 7th sub-class of
  the `npc-status-persistence-bug` taxonomy; covers the state-update side
  (numeric values in `npc_data`). THIS reference covers the directive-text side
  (verbatim wording in `directives.add`).
- PR #8531 (2026-07-23) — caps the rendered directive block at 50 entries,
  requires backfill from canonical snapshot to maintain parity.
- PR #8532 (2026-07-23) — adds the value-drift lint, adjacent problem.
- `references/god-mode-directive-enforcement.md` — the pre-existing
  `_should_reject_directive` advisory-only directive model. THIS reference is
  consistent with the advisory-only model; it just adds a side channel for
  user-introduced *canonical* directives to graduate to snapshot state.

## Verified case

Campaign `wc2BBcSgOljiU3vJ160A`, scene 454, 4 god-mode corrections over 6
minutes, 5 different "Original Divine Level" values for Ao (100, 25, 95, 99,
49). After the 6-component fix (routing + writeback + state-updates + lint),
the expected behavior: Ao's "Original Divine Level" is recorded once in
`custom_campaign_state.god_mode_directives_snapshot` (developer-authored,
hash-pinned), and every turn's LLM response is validated against that
snapshot. The user's "remember Ao is L100" directive produces exactly one
canonical entry, surviving every subsequent correction turn.
