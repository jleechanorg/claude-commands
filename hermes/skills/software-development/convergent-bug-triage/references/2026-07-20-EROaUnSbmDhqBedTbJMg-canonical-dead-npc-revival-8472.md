# Canonical-Dead-NPC Revival Sub-Class — Worked Example (2026-07-20)

## Bug origin

- **Campaign:** `EROaUnSbmDhqBedTbJMg` (Sariel Valyria — Twin to `urhzEeI501zaFfn4OQlb` after copy)
- **Source UID:** `0wf6sCREyLcgynidU5LjyZEfm7D2` (<your-email@gmail.com> twin)
- **Scene:** 492 (USN 492, RewardsAgent, gemini-3-flash-preview)
- **Story doc:** `7PXVzEr6jZVJdlZtP9Ji` (ts `2026-07-20 05:40:06.663 UTC`)
- **Issue:** #8472 ([link](https://github.com/$GITHUB_REPOSITORY/issues/8472))
- **PR:** #8473 ([link](https://github.com/$GITHUB_REPOSITORY/pull/8473))
- **Branch:** `fix/eroa-canonical-dead-npc-8493` @ `f4bb3a6687bc5578c7e0504944c04d3e9585fe87`

## Symptom

LLM narrated `Archon Jaenor Vaelaros` (canonical-dead NPC, Sariel's father) as physically present at the Consular Coronation extending his signet ring to Sariel. Verbatim from the offending prose:

> *"Archon Jaenor Vaelaros (Lvl 20), your figurehead Emperor, stands at the base of the dais, his heavy signet ring extended in a trembling hand. Beside him, the leaders of the Belaerys, Maegyr, and Qeldar lines kneel in the hot ash..."*

And the multi-NPC group activity NPC-internal-monologue claim:

> *"feared your father's indifference"*

## Canonical contradiction (byte-identical on source + twin)

```
npc_data["Archon Jaenor Vaelaros"].status = "dead"
npc_data["Archon Jaenor Vaelaros"].hp_current = 0
npc_data["Archon Jaenor Vaelaros"].role = "Emperor of the Blood-Matrix (Figurehead)"

core_memories[363]:
  "Archon Jaenor is dead; Sariel has ascended as God Empress of the New Valyrian Empire"

core_memories[392] (most recent):
  "Correction: Archon Jaenor Vaelaros is dead; the coronation at the Fourteen Flames
   was for Sariel as the sole God Empress"

core_memories[271]: "Jaenor yields Valyrian signet" (the lore event that placed the signet in canonical state — NOT a presence event)
core_memories[274], [302]: "Aenar Vaelaros dead" (Aenar is Jaenor's ancestor; same canonical-dead state)
```

## User verbatim

Turn 492 (offending, user asked for the coronation):
> *"a grand reception. The 40 families greet me as god empress and fly hundreds of dragons. In parallel ground the anchors"*

Turn 493 (correction, story doc `fHnIc497jvqztaT2fGA3`, ts `2026-07-20 05:58:26.065 UTC`):
> *"My dad is dead why did you forget"*

## Model self-admission (scene 493, story doc `v6i6vWAXtpVICt3SHIiN`, ts `2026-07-20 05:58:26.407 UTC`)

> *"Administrative Correction: Archon Jaenor Vaelaros is canonically deceased. I have corrected the game state and added a persistent directive to ensure he no longer appears in the narrative. The previous turn's description of him at the coronation was a continuity error."*

The model classified its own bug as a continuity error after the user prompt — confirming the LLM "knew" canonically-dead status existed in `core_memories` and `npc_data` but did NOT propagate that constraint to the narrative-emit pass in real time.

## Why this is a NEW sub-class, not the existing NPC-status-erased sub-class

| Sub-class | Direction | Failure surface |
|---|---|---|
| **NPC-status-erased** (existing, verified 2026-07-19 on `Cg2m2TkGFFez7XBynEah` scene 367) | LLM **forgets** canonical NPC status mid-narrative and treats dead NPC as alive | "Aenar would sabotage your success" while Aenar is dead |
| **Canonical-dead-NPC revival** (NEW, verified 2026-07-20 on `EROaUnSbmDhqBedTbJMg` scene 492) | LLM re-introduces canonical-dead NPC with elaborate physical-presence details — actively narrating actions the dead NPC couldn't perform | "stands at the base of the dais, his heavy signet ring extended in a trembling hand" |

The new sub-class is more aggressive: the LLM is not just forgetting the status, it is actively constructing elaborate present-tense narration that presupposes physical presence. The forbidden-pattern enumeration must therefore be much wider (7 categories, not just "do not treat X as alive").

## Sibling cluster trigger — 5th sibling on EROaUnSbmDhqBedTbJMg

| # | Issue/PR | Symptom class |
|---|---|---|
| 1 | #8463 / PR #8464 | NPC-knowledge-of-PC OMITTED (scene 386 Argella suspicion) |
| 2 | #8444 / PR #8445 | NPC co-presence (anchor b) (scene 318 Aegon Mander mouth) |
| 3 | #8451 / PR #8452 | LLM-prose invention (scene 171 frequency-shield) |
| 4 | #8468 / PR #8469 | NPC-knowledge-of-PC VIOLATED (scene 454 Targaryens remember Sariel through mask) |
| **5** | **#8472 / PR #8473** | **canonical-dead-NPC revival** (scene 492 Jaenor at coronation) |

This is the trigger for the campaign-level prompt-fix PR. Per `references/npc-status-persistence-bug.md` §"Campaign-cluster structural trigger", at ≥5 siblings the campaign has a structural bug class that warrants a unified prompt-fix PR — not per-scene fixes.

## Durable-fix shape (PR #8473, the 3-layer architecture)

The state-update layer was already shipped in PR #8352 / commit `31d8b452c5` (June 28, 2026) — §"Narrative Revival of Canonical-Dead NPCs" in `game_state_instruction.md`. The bug was that the rule said "do not resurrect canonical-dead NPCs in `state_updates.npc_data`", which the LLM correctly observed (no `state_updates.npc_data` resurrection write was emitted at scene 492). The narrative-emit pass still narrated the dead NPC as physically present.

PR #8473 landed the missing two halves:

| Layer | File | Section | Lines added |
|---|---|---|---|
| **Narrative-emit** | `$PROJECT_ROOT/prompts/narrative_system_instruction.md` | §NPC Presence at Canonical Status (Forbidden Revival Patterns) | 39 lines |
| **Planning-block** | `$PROJECT_ROOT/prompts/planning_protocol.md` | §NPC Presence at Canonical Status (Choice Premise Validation) | 36 lines |
| **Regression test** | `$PROJECT_ROOT/tests/test_canonical_dead_npc_revival_8493.py` | Prompt-contract pins for both halves | 344 lines (new file) |

Both halves cross-reference the existing state-update half in `game_state_instruction.md` AND each other, so the narrative-emit / state-update / planning-block architecture is explicit.

## The 7 forbidden-pattern categories

Each category is anchored to a scene-492 example (the bug surface) so the LLM cannot re-emit the pattern without a resurrection write:

1. **Physical presence at a scene the NPC is canonically absent from** — *"Archon Jaenor Vaelaros (Lvl 20) stands at the base of the dais"*
2. **Hand-object action** — *"extends his signet ring"*, *"rotates his signet ring"*, *"presses his signet into the wax"*, *"raises his sword"*, *"offers his cup"*
3. **Voicing dialogue** — direct line from a canonical-dead NPC
4. **Vehicle/dragon/mount operation** — *"Jaehaerys rode Vermax toward..."* (rider dead)
5. **Physical posture** — kneeling / bowing / leaning / sitting
6. **Multi-NPC group activity with present-tense verbs** — *"feared your father's indifference"* (presupposes father's current existence)
7. **Artifact custody transfer** — *"Jaenor yields the signet ring"* (transferring one's own artifact requires physical agency)

## Resurrection exception

The rule must explicitly enumerate when a canonical-dead NPC's physical presence IS permitted. Verified shape from PR #8473:

- Same-turn `state_updates.npc_data.<npc_id>` write must:
  - Remove `"dead"` from the status list
  - Restore `hp_current > 0`
  - Provide explicit narrative justification (resurrection ritual, confirmed mistaken-death reveal, spiritual return, etc.)
- The justification MUST appear in the same turn's `state_updates` AND the same narrative block — a deferred resurrection is not a resurrection.
- The planning_block mirror must DROP (not hedge) any choice whose premise requires a canonical-dead NPC's presence without the resurrection write.

## Why all three layers (state-update + narrative-emit + planning-block) must land together

Verified by the 4-week gap between PR #8352 (state-update half) and PR #8473 (narrative-emit + planning-block halves):

- The state-update layer alone is insufficient because the LLM's narrative-emit pass can re-introduce a canonical-dead NPC into the prose even when the game-state pass correctly suppresses the resurrection write.
- The planning-block layer is needed because `planning_block.choices[]` can presuppose a canonical-dead NPC's presence even when the narrative text correctly omits them.
- All three layers cross-reference each other AND the existing `game_state_instruction.md` clause, so a future author touching any one half will see the architecture.

## Test verification (PR #8473's prompt-contract pins)

```
$ cd $HOME/projects/wt-eroa-8493-canonical-dead
$ TESTING_AUTH_BYPASS=true vpython -m unittest mvp_site.tests.test_canonical_dead_npc_revival_8493 -v
... (15 tests)
Ran 15 tests in 0.002s
OK (skipped=1)
```

The 1 skipped test is `test_layer_c_pending_human_approval_placeholder` — the server-side post-LLM guard (Layer C). Per AGENTS.md and `references/repro-planning-block-and-campaign-cluster-2026-07-18.md` §6.2, server-side enforcement requires explicit human approval before being merged; that work is tracked separately.

PR #8469's tests (`test_npc_knowledge_of_pc_constraint_8468.py`, 12 tests, 1 skipped) also still pass after PR #8473 — the cross-reference between the two prompt anchors is intentional and does not regress either contract.

## Twin clone workflow (reproducibility)

```bash
# Source UID: 0wf6sCREyLcgynidU5LjyZEfm7D2
# Twin destination: <your-email@gmail.com> (UID derives automatically)
cd $HOME/projects/your-project.com

# Copy campaign to twin
venv/bin/python scripts/copy_campaign.py \
  --find-by-id EROaUnSbmDhqBedTbJMg \
  --dest-email <your-email@gmail.com>
# → new twin campaign ID: urhzEeI501zaFfn4OQlb

# Export twin
venv/bin/python scripts/download_campaign.py \
  --uid 0wf6sCREyLcgynidU5LjyZEfm7D2 \
  --campaign-id urhzEeI501zaFfn4OQlb \
  --output-dir /tmp/your-project.com/repro-exports/sariel-8493-canonical-dead \
  --format txt
# → export at /tmp/your-project.com/repro-exports/sariel-8493-canonical-dead/Sariel Valyria _copy__urhzEeI5.txt
# → scene-492 offensive prose at line 17754-17768
```

The export serves as regression evidence: if the prompt fix is later verified with a fresh LLM replay, the export's scene-492 prose can be diffed against the new emit to confirm the rule holds.

## Why this is the canonical-state-anchor family's "third missing half" (not a new bug class)

The 5 existing sub-classes (magic-sensor, NPC-status-erased, NPC co-presence, faction-control, Argella-suspicion) all map to the same 3-layer prompt architecture. When filing the durable-fix PR for any new canonical-state-anchor sub-class, the agent should:

1. Check the state-update layer first (`game_state_instruction.md`). If a rule already exists, the bug is in one of the other two layers.
2. Check the narrative-emit layer (`narrative_system_instruction.md`). This is the most-missing layer; PR #8352's commit history shows the team fixed state-update-only first.
3. Check the planning-block layer (`planning_protocol.md`). Often forgotten because the choices look "advisory" but they bind NPC presence in subsequent turns.

The 3-layer architecture is the durable-fix shape for ALL canonical-state-anchor sub-classes — PR #8473 is just the first prompt-fix PR that ships all three halves in a single coordinated change.