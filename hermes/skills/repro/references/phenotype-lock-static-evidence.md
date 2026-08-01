---
name: phenotype-lock-static-evidence
description: 3 static-evidence greps that should run BEFORE asking the user the Step 0.75 phenotype-anchor questions. Often answers your own question and prevents a NON-REPRO replay.
tags: [repro, worldarchitect, phenotype, static-evidence, code-symbol, prior-export, sibling-issue]
---

# Phenotype lock from static evidence

When a `/repro` request comes in, Step 0.75 (bug phenotype capture) historically asked the user 3 clarification questions: (1) what scene was X found, (2) literal text of the planning block, (3) last player input. But often those questions can be partially or fully answered by static evidence BEFORE asking — saving a clarification round-trip AND avoiding a NON-REPRO replay caused by replaying against the wrong bug class.

## The 3 static-evidence greps

Run these in parallel after Hard Gates 1+2 (issue + draft PR exist):

### 1. Code-symbol grep

Does the user-reported bug name match any symbol in the codebase?

```bash
cd $HOME/projects/your-project.com
grep -rn "<bug_token>" $PROJECT_ROOT/ --include="*.py"
grep -rin "<bug_token>" $PROJECT_ROOT/prompts/
```

**Interpretation:**

| Grep result | Bug class | Implication |
|---|---|---|
| **Zero matches** | Natural-language LLM prose (NOT a canonical game-state field) | Bug is stale-context / prompt-side injection. Skip schema-side fixes. |
| **Matches test fixture only** (e.g. `hidden_treasure` in `tests/test_game_state.py`) | LLM-invented element, not a real state object | Bug is LLM hallucination or stale narrative context, not a schema regression. |
| **Matches prompt file** (`$PROJECT_ROOT/prompts/*.md`) | Prompt-side directive that may be wrong/missing | Bug is prompt content. Fix the prompt, not the server. |
| **Matches server code** (`$PROJECT_ROOT/world_logic.py`, `agents.py`) | Canonical game-state logic | Bug is state-management. Standard repro path. |

**Worked example (#8293, 2026-07-09):** User said "hidden gold" in planning block. `grep -rn "hidden.*gold" $PROJECT_ROOT/` returned one hit: `$PROJECT_ROOT/tests/test_game_state.py:1471: "hidden_treasure": "gold_coins",` — test fixture only. `grep -in "hidden.*gold" $PROJECT_ROOT/prompts/` returned zero hits. **Conclusion:** the bug is natural-language LLM prose, not a canonical game-state field. Bug class = stale-context / prompt-side injection. Saved one LLM call that would have replayed against the wrong hypothesis.

### 2. Prior-export grep

Does the bug token appear in any prior repro's exported campaign data?

```bash
ls /tmp/your-project.com/repro-exports/ | head -20
grep -rin "<bug_token>" /tmp/your-project.com/repro-exports/<campaign_id>-scene*/ 2>/dev/null
grep -rin "<bug_token>" /tmp/your-project.com/repro-exports/issue-<N>*/ 2>/dev/null
```

**Interpretation:**

- **Found in earlier scenes' exports** (e.g. token appears in scene 149 export but not scene 375 export): the element was introduced earlier than the user thinks. Ask the user to confirm which scene they "found" it in.
- **Not found anywhere**: the element was newly introduced. Bug is most likely prompt-side or LLM hallucination, not stale-persistence.
- **Found in sibling repro's pre_state.json**: the element is in Firestore state, not just narrative. Bug class shifts toward persistence, not render.

**Worked example (#8293, 2026-07-09):** `grep -in "gold" /tmp/your-project.com/repro-exports/.../Visenya v7_xK3fp5Xr.txt` returned 40+ hits — but ALL were player currency (`Gold: 25gp`, `Gold: 44,776gp`). Zero hits for "hidden gold" as a quest/treasure object. **Conclusion:** no prior repro touched the element; it was newly introduced between scene 177 and scene 375.

### 3. Sibling-issue scan

Are there other open repros on the same campaign ID?

```bash
gh issue list --repo $GITHUB_REPOSITORY --state open --limit 20 \
  --json number,title --jq '.[] | "\(.number)\t\(.title)"' | grep -i "<campaign_id>"
gh pr list --repo $GITHUB_REPOSITORY --state all --limit 50 \
  --json number,title,headRefName --jq '.[] | "\(.number)\t\(.title)\t\(.headRefName)"' | grep -i "<campaign_id>"
```

**Interpretation:**

- **≥3 open repros on the same campaign ID** → the campaign has a **structural issue**, not just a per-scene bug. The underlying root cause is likely the same across all of them (render-and-persist, god-mode-directive-missing, npc-status-persistence). **Action:** link all siblings in the new issue body and PR description; explicitly note "Nth instance on this campaign — likely same root-cause class."
- **2 open repros** → suspicious but not yet structural. Link the one prior sibling.
- **0-1 open repros** → treat as one-off.

**Worked example (#8293, 2026-07-09):** Found #8275 (queen-level-14 ignored) and #8277 (companion_request not rendered) — both on `xK3fp5XrV24oarIINTF7`. **Conclusion:** 3rd instance on this campaign. Same root-cause class as the prior two (likely the recurring `god-mode-directive-missing` or `render-and-persist` classes). Pushed sibling links + structural-issue note into the issue body and PR description.

## When the 3 greps LEAVE the bug class ambiguous

Only ask the user the 3 Step 0.75 phenotype anchors (find-scene, literal-block-text, last-input). Every clarification question you don't need to ask is a NON-REPRO you don't need to discover.

## Cost/benefit

- **Cost:** ~10 seconds of grep time, 3 read-only commands, zero LLM calls, zero Firestore writes.
- **Benefit:** Often pins the bug class to one of 4 categories BEFORE the first replay, saving a $0.30-$0.80 LLM call that would land NON-REPRO. Also surfaces sibling-campaign patterns that would otherwise be triaged as one-offs.

## Anti-patterns

- **Asking the user first, then running greps.** The user has limited attention and limited recall — they'll often answer "I don't remember the scene." Run greps first, then ask the smallest possible follow-up if still ambiguous.
- **Treating zero code-symbol matches as "no bug".** Zero matches means the bug is LLM prose, not that there's no bug. Continue investigating; the bug is in the prompt construction or streaming bundle, not in a canonical schema.
- **Treating a sibling-issue match as identical bugs.** Sibling repros share a campaign, not necessarily a root cause. Link them, but investigate independently.

## Pair with

- `references/static-evidence-sufficient-no-live-turn.md` — when the §2.1 first-touch rule is satisfiable entirely from pre-state + bug-origin story doc, without a live LLM turn. The current recipe is the *upstream* of that one: classify the bug from static evidence BEFORE deciding whether you even need a live turn.
- `references/god-mode-directive-missing-subclasses.md` — when sibling-issue scan surfaces ≥2 instances on the same campaign, this is the 4-factor matrix to consult (A: streaming save-drop, B: wrong-storage routing, C: stale streaming bundle, D: backend override).
- `references/two-pronged-render-and-persist-bug.md` — when code-symbol grep returns prompt-file hits, the bug is render-side; when it returns server-code hits, the bug is persist-side. One user-reported symptom can need BOTH fixed.

## Bug class → verdict row mapping (added 2026-07-18, #8438; extended #8444)

After running the 3 greps, the bug class determines which verdict row to fill in the §4 verdict table. If the row template is missing from the existing references, USE the template below — don't invent a freeform label.

| Code-symbol grep result | Bug class | Verdict row label (use verbatim) | Reference |
|---|---|---|---|
| Zero matches in code AND prompts | **LLM-prose invention** — artifact exists only in narrative text, no canonical schema, no canonical item_registry entry | `HISTORICAL RED ARTIFACT — LLM-prose invention` (source campaign narrative contains the invented artifact; copy preserves it; no live replay required if static evidence is sufficient) | `references/static-evidence-sufficient-no-live-turn.md` |
| Matches server code (canonical game-state field) | Persisted-state bug | `NON-REPRO / REPRO` after live replay | §2.1 + §4 |
| Matches prompt file only | Prompt-content bug | `REPRO` after live replay (replay confirms prompt emits the wrong prose) | §3 + §4 |
| Matches test fixture only | LLM hallucination / stale narrative context | `NON-REPRO FOR ORIGINAL PHENOTYPE` if symptom differs from test fixture | §4 anti-pattern |
| Zero matches AND planning_block contradicts `npc_data[<X>].location` or `player_character_data.world_data.current_location_name` | **NPC co-presence violation** — choice premise references directional movement where the player or target NPC is already at the destination | `HISTORICAL RED ARTIFACT — NPC co-presence violation` | `references/repro-planning-block-and-campaign-cluster-2026-07-18.md` §5.1 |

**Worked example (#8438, 2026-07-18 — "Blood-Scent focus" silver vial):** `grep -rn "blood.scent|vaelaros" $PROJECT_ROOT/` returned 0 hits; `grep -rn "blood.scent|vaelaros" $PROJECT_ROOT/prompts/` returned 0 hits. But the source campaign narrative contained "He doesn't scan the room; he walks directly toward your table, a small silver vial in his hand glowing with a faint, pulsing violet light—a Vaelaros-tuned 'Blood-Scent' focus." → Bug class: **LLM-prose invention** (artifact exists only in narrative text; canonical NPC `Lord Gwayne Gaunt` IS in npc_data, but the silver vial + violet light + "Vaelaros-tuned" modifier are LLM prose elaboration with no canonical schema). Verdict row: `HISTORICAL RED ARTIFACT — LLM-prose invention`. Live replay deferred to follow-up commit before merge (not required for filing).

**Worked example (#8444, 2026-07-18 — "Rejoin the Host" Aegon co-presence):** `grep -rn "Rejoin the Host"` and `grep -rn "Mander mouth"` returned 0 hits in `$PROJECT_ROOT/`. But the source campaign's `current_state.planning_block.choices[0]` had `"text": "Rejoin the Host"` with description *"Depart Highgarden with your 13 Apex Guards and the signed treaties to rejoin Aegon's main vanguard at the Mander mouth."* Canonical state at the same time: `player_character_data.world_data.current_location_name = "Highgarden, The Sun-Grotto"` + narrative shows Aegon standing 3 paces in front of Sariel, accepting her kiss on his signet ring. → Bug class: **NPC co-presence violation** (anchor (b) in the 5-anchor taxonomy at `references/repro-planning-block-and-campaign-cluster-2026-07-18.md` §5). Verdict row: `HISTORICAL RED ARTIFACT — NPC co-presence violation`. Live replay not required (planning_block field is byte-faithful in test copy).

**Anti-pattern:** inventing a verdict label like "PROSE-ONLY BUG" or "NARRATIVE-ARTIFACT" when the canonical labels are `HISTORICAL RED ARTIFACT` (per §3) and `NON-REPRO FOR ORIGINAL PHENOTYPE` (per §4). The 5-label enum (as of 2026-07-18) is closed: `REPRO` / `RELATED` / `NON-REPRO` / `HISTORICAL RED ARTIFACT` (with the four documented sub-classes — LLM-prose invention, NPC co-presence violation, future-event leak, completed-milestone re-emit). If your bug class needs a 6th label, the issue is misclassified — re-run the 3 greps.