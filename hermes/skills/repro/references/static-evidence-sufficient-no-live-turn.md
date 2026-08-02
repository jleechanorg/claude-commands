# Static evidence is sufficient — when to skip the §2.1 live LLM turn

## Pipeline position

This reference covers the **second** static-evidence decision in a `/repro` pipeline. The **first** — classifying the bug class from static evidence BEFORE asking the user phenotype anchors or running the copy — lives in `references/phenotype-lock-static-evidence.md`. Run those 3 greps (code-symbol, prior-export, sibling-issue) FIRST; they often tell you whether the bug is even a persisted-state bug or an LLM-prose/prompt-side bug. If the upstream greps say "natural-language LLM prose, not a canonical field", this reference's "persisted state" framing doesn't apply — the bug isn't observable in Firestore at all.

## The rule in the canonical skill

> "Capture the copied campaign's pre-state with a direct Firestore document read before any app API call that could clean, migrate, normalize, or project state."
>
> "Run the exact production ingress being validated (for gameplay, prefer `/api/campaigns/<id>/interaction/stream`) as the first app touch."

## When static evidence satisfies the rule WITHOUT a live turn

A live LLM turn is required ONLY when the bug is **observable in the LLM's runtime response** (e.g. "the LLM emits X phrase in scene N+1"). If the bug is **fully evidenced by the persisted state** (Firestore docs + story narrative + state_updates history), the live turn adds no new evidence and consumes 30-90s + LLM budget.

**The 3 static signals that satisfy §2.1:**

1. **A `mode: "god"` story doc with `directives.add` array** that contradicts the original `god_mode.setting` — the directive is the bug, and it will be re-injected on every future turn without any live re-test. The narrative text of the doc itself demonstrates the user's reported symptom (e.g. "I have established a persistent directive to ensure the narrative reflects your status as Rhaenyra's daughter in spirit" — that's the LLM calling the user daughter of the queen, in writing).
2. **A `state_updates` record that writes the user's intent AND its opposite into the same field** (the confused-state `with` / `replace` pattern from `npc-status-persistence-bug.md`).
3. **A `core_memories.update` record with the user's intended truth in `replace` AND the LLM's override in `with`** — same doc, semantically opposite meanings, the LLM has already self-contradicted.

If all 3 are present, the verdict is `REPRO` from static data. Label the post-state as `HISTORICAL RED ARTIFACT` per §3 ("the source campaign artifact shows the failure, label as HISTORICAL RED ARTIFACT, not a fresh red replay") — but the pre-state is a fresh copy, and the bug is reproducible in the copy's pre-state (because the copy preserved the bug state).

## When the live turn IS required

- The user reports a symptom that only appears in the LLM's *current* turn output (e.g. "the LLM just called me X in this turn but I can't find it in the story docs")
- The bug requires verifying that the routing layer (agents.py, world_logic.py) chose the right agent for the input
- The bug is in the streaming path (Factor A from god-mode-directive-missing-subclasses.md) — needs the live payload to verify the header is/isn't present
- A backend override regression (Factor D) — needs a turn to observe the override happen

## Extension: LLM-prose invention bug class (added 2026-07-18, #8438)

The 3 static signals above all assume the bug is in a **persisted state field** (god-mode directive, state_updates, core_memories). The "Blood-Scent focus" silver vial bug on campaign `D3iZvnGiBl9wyveQBFj9` is a DIFFERENT shape: the bug is in the LLM's **narrative prose** — an invented artifact (silver vial, violet light, "Vaelaros-tuned focus") attributed to canonical NPC `Lord Gwayne Gaunt` that has no canonical schema, no `item_registry` entry, and is absent from all prompt files.

**Static signals that satisfy §2.1 for LLM-prose inventions:**

4. **A story-doc narrative containing the invented artifact with no canonical anchor** — `grep -rn "<artifact_name>" $PROJECT_ROOT/` and `$PROJECT_ROOT/prompts/` return 0 hits; the artifact appears only in `story/*.txt` text. The source campaign's story doc IS the bug — re-running the LLM on the test copy would just re-produce the same artifact (because the prompt is what authorized the invention).

**Verdict for LLM-prose inventions:** `HISTORICAL RED ARTIFACT` per §3 — the source artifact demonstrates the failure; the test copy's pre-state preserves it; re-running the LLM adds zero new evidence. Fix lives in the prompt (where the LLM learned it could elaborate tracking devices), not in the persisted state.

**Live-replay cost-savings:** for LLM-prose inventions, the live replay burns LLM tokens (~$0.30-2.00) to re-produce an artifact you already have byte-faithfully in the source export. Save the budget for the prompt-review follow-up commit, not the replay.

**Worked example (#8438, 2026-07-18):** source export contained the silver vial + "Blood-Scent focus" prose verbatim at byte offset 328192-328500. Code-symbol grep on `blood.scent`/`vaelaros`/`silver vial`/`violet light` returned 0 in `$PROJECT_ROOT/` and `$PROJECT_ROOT/prompts/`. Test copy was byte-faithful (329925 vs 329928 chars). Verdict: `HISTORICAL RED ARTIFACT — LLM-prose invention`. Live replay deferred to follow-up commit before merge (when prompt reviewer needs a fresh red against the fixed prompt).

## How to label the verdict when you skip the live turn

In the verdict table, mark the post-state row as:

> `HISTORICAL RED ARTIFACT` — bug origin is in the source campaign's story docs; copy pre-state preserves the bug; no fresh red replay performed because the static evidence is sufficient and the bug is in a god-mode directive that re-injects on every turn.

This is the §3 exception applied correctly: the source artifact demonstrates the failure, the copied campaign's pre-state preserves it, and re-running the LLM would only re-produce the same artifact without adding new evidence.

## Cost of the live turn when not needed

- Time: 30-90s per turn (LLM call + Firestore write)
- Tokens: 5-15k input (full story context) + 1-3k output
- Risk: the new turn may inject NEW artifacts (additional `core_memories` entries, `state_updates`) that obscure the bug origin in the post-state diff
- For interactive /repro sessions where the user is waiting: skipping the live turn gets to verdict ~5x faster

## Verified worked example

- 2026-07-08, issue #8283 — all 3 static signals present, skipped the live turn
- Verdict time: ~10 min from `/repro` invocation to `REPRO` posted on issue + PR
- Bug confirmed in `evidence/pr-8283/pre_state.json` (239 KB pre-state) + `evidence/pr-8283/scene_315_bug_origin.json`
- The user was satisfied with static evidence; no followup to re-run with a live turn

## When in doubt, do the live turn

The risk of skipping when you shouldn't is a `NON-REPRO FOR ORIGINAL PHENOTYPE` verdict (§4). If the bug is a runtime-only symptom or you can't isolate it to a single story doc, do the live turn. Static evidence is for clear persistent-state bugs.
