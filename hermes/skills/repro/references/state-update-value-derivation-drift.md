# State-update value-derivation drift (new sub-class, verified 2026-07-23, issue #8528)

## Signature

LLM correctly derives a value in narrative prose, correctly writes the
corresponding `state_updates.*.<NPC>` field, but writes **the wrong
numeric value** — typically ~50% under or over the canonical derivation.

The narrative text explicitly states the formula application + intent;
the structured-state write is structurally correct (field exists, key
matches, type matches). Only the *derived numeric* is wrong. This is a
**translation drop between narrative prose and structured fields**, not
a memory/persistence issue.

## Distinct from sibling sub-classes in `references/npc-status-persistence-bug.md`

| Sub-class | Narrative says | Field written | Value correct? |
|---|---|---|---|
| missing-write | "X captured" | ❌ absent | n/a |
| wrong-write (existing) | "X captured" | ✅ present | ❌ wrong status enum |
| prompt-anchor hallucination | "X is here" | ✅ present | ❌ wrong NPC entity_id |
| confused-state with/replace | various | ✅ present | ❌ wrong key update mode |
| **VALUE-DERIVATION DRIFT (new)** | "applying the canonical (Level / 10) gear formula to Original Divine Levels" | ✅ `npc_data.<NPC>.equipment_bonus=N` | ❌ wrong N (e.g. Ao=2, should be floor(95/10)=9) |

The signature distinction: the narrative derivation is correct AND
emitted in prose AND the field path is correct AND the field type is
correct AND the field is written — only the numeric value drifts
between the narrative-computation step and the structured-transcription
step.

## Verified worked example

Campaign `wc2BBcSgOljiU3vJ160A`, scene 454 (1495 DR, Mirtul 6
~20:00 in-fiction time), issue
[#8528](https://github.com/$GITHUB_REPOSITORY/issues/8528)
(4th sibling on this campaign_id; cluster trigger exceeded; root-cause-first
fix mandated by /repro).

### Pre-correction (4 turns, 08:44:45–08:51:23 UTC, BEFORE user's corrections)

The rule *"Gods in mortal form receive +10 equipment in every slot (Level / 10)"*
was at offset **47.6%–68.6%** of the served 350KB request prompt (well-attended).
Across all 4 turns, the LLM wrote **0** `npc_data.equipment_bonus` fields despite
the rule being present and at an attended offset. The "+10" appeared only in
narrative prose, never materialized into structured state.

| UTC (pre-correction) | Rule position | Attended? | `npc_data.equipment_bonus` fields written |
|---|---|---|---|
| 08:44:45 | 240,064 / 350,000 = **68.6%** | ⚠️ borderline | ❌ 0 |
| 08:46:30 | 206,130 / 350,000 = **58.9%** | ⚠️ borderline | ❌ 0 |
| 08:49:41 | 187,122 / 350,000 = **53.5%** | ✅ attended | ❌ 0 (npc_data block present but no equipment_bonus fields) |
| 08:51:23 | 166,739 / 350,000 = **47.6%** | ✅ attended | ❌ 0 |

### Post-correction (4 turns, 16:08:39–16:14:37 UTC, user's 4 corrections)

User issued 4 escalatory god-mode corrections in 6 minutes. The cumulative
`directives.add` history pushed the rule's prompt position from 47.6% to
89.7%–97.6% (past lost-in-the-middle threshold). The narrative derivation
re-synced correctly each turn, but the structured-state value drifted.

| UTC | Rule position | `npc_data` writes | Ao | Bane | Myrkul | Gale |
|---|---|---|---|---|---|---|
| 16:08:39 #1 | 89.7% | ✅ | — | 2 ✓ | 2 ✓ | 2 ✓ |
| 16:10:24 #2 | 97.6% | ❌ none (lost the rule) | — | — | — | — |
| 16:11:33 #3 | 89.8% | ✅ wrong values | **2** ❌ (should be 4) | 2 | 2 | 2 |
| 16:14:37 #4 | 93.9% | ✅ correct | **9** ✓ | **4** ✓ | **4** ✓ | **4** ✓ |

Notes:
- All values for Bane/Myrkul/Gale happen to be the same `floor(L/10)=2`
  on turns 1 and 3 because those NPCs sit at L21–L23 in the campaign state.
- Ao (L95) is the discriminating case: should be `floor(95/10)=9`.
  Turns 1, 2, 3 all wrote Ao=2 (off by ~7); turn 4 finally wrote Ao=9.
- The drift pattern: when the rule is at ≤68.6% (attended), LLM DOES
  derive narrative correctly but DOESN'T materialize the value at all.
  When the rule is at 89.7%+ (lost-in-the-middle), LLM tries to materialize
  but loses track of the `Original Divine Level` lookup-table values.

## User-feedback discipline that unlocked this diagnosis

The user's OOB request *"Read the actual raw LLM request in BQ did the
LLM even see the directive"* — when the agent had just posted an A/B/C
clarifying menu — is the canonical anti-pattern that this sub-class
surfaces. The user's instinct was right: the diagnostic was runnable, the
menu was unnecessary friction. Step 0.77 in this skill codifies the
discipline. **Never post a fix-direction menu before running the BQ
diagnostic for any directive-loss report.**

## Recommended fix shape (4-component)

1. `$PROJECT_ROOT/agent_prompts.py` `build_god_mode_response_prompt`: insert a
   **state-update value-derivation block** that re-computes
   `npc_data.<NPC>.equipment_bonus` from the `Original Divine Levels`
   lookup-table BEFORE the LLM emits `state_updates.npc_data`. Empirical
   evidence: LLM derives the narrative value correctly (turn 16:14:37
   narrative says "applying the canonical (Level / 10) gear formula to
   their Original Divine Levels") but loses track in the structured-
   transcription step. The fix is to mirror the derivation into a
   per-NPC lookup-table in the prompt itself so the LLM has the values
   close to the structured-transcription step.

2. `$PROJECT_ROOT/memory_utils.py` `select_directives_by_budget()` mirroring
   the existing `select_memories_by_budget()` mechanism. Cap the
   rendered `dynamic_instructions` block at ~4K tokens regardless of how
   many `god_mode_directives` entries exist, with recency-weighted
   priority. Fixes the lost-in-the-middle sub-symptom (Factor H, already
   2 sibling repros on this campaign: #8508 directive bloat, #8526
   companion-quest cadence buried at 99.7%).

3. `$PROJECT_ROOT/tests/test_god_mode_gear_formula_consistency_wc2bb_4th_sibling.py`:
   12-test contract.
   - State-update value-derivation block present in prompt.
   - Per-NPC `equipment_bonus` derivation contract: for each NPC in
     `{Nocturne, Ao, Bane, Myrkul, Gale, Mystra, Helm, Lolth}`, given an
     `Original Divine Level` L, the LLM-written
     `npc_data.<NPC>.equipment_bonus` matches `floor(L/10)` within ±0
     across 3 successive god-mode correction turns.
   - `select_directives_by_budget()` keeps `directives.add[-10:]` and
     drops entries older than 10.
   - Rule-offset invariant: rule `drop[...]` and `add[...]` blocks for
     the user's latest correction must render at ≤70% of the served
     prompt, not past 85%.

4. `scripts/check_state_update_value_drift.py`: CI lint. Walks
   `llm_payloads` last 30 days, classifies
   `state_updates.npc_data.<NPC>.equipment_bonus` derivation consistency
   vs. the canonical `(Level / 10)` formula reference. Fail = non-blocking
   warn at PR-time, blocking error at merge when same NPC fails in ≥3
   turns.

## Cross-references

- `repro` Step 0.77 — BQ-first diagnostic for directive-loss reports.
- `repro` Factor H (changelog 3.5.0, 3.6.0) — lost-in-the-middle sub-symptom.
- `repro` Factor G revised doctrine (changelog 2.9.0) — verify LLM received
  the rule before proposing prompt-layer fixes.
- `references/npc-status-persistence-bug.md` — sibling sub-class
  taxonomy; this is the 7th sub-class.
- Verified issue: [#8528](https://github.com/$GITHUB_REPOSITORY/issues/8528)
  on campaign `wc2BBcSgOljiU3vJ160A`. Folder:
  `~/.hermes/wa-repro-PENDING-8528/issue-body.md`.
