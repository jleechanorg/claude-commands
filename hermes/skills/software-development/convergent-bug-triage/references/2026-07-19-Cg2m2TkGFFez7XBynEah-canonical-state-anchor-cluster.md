# Canonical-State-Anchor Cluster — Sariel Valyria (`Cg2m2TkGFFez7XBynEah`)

**Date:** 2026-07-19
**Cluster count:** 8 siblings in 24h on a single campaign
**Bug family:** canonical-state-anchor (3rd family, distinct from prompt-discipline and NPC-status persistence)
**Author:** Hermes session `20260719_160921_3faa1909` (continuation) + prior `20260718_175458_556fa5cb` (magic-sensor scene 171)

## Source

- Live URL: `https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/game/Cg2m2TkGFFez7XBynEah`
- Source UID: `vnLp2G3m21PJL6kxcuAqmWSOtm73` (`$USER@gmail.com`)
- Source campaign ID: `Cg2m2TkGFFez7XBynEah` ("Sariel Ash / Sariel Valyria — The Embers of Valyria")
- Test subject UID: `0wf6sCREyLcgynidU5LjyZEfm7D2` (`<your-email@gmail.com>`)
- Test subject export: `/tmp/your-project.com/repro-exports/sariel-171-test/Sariel Valyria _copy__asyto1hC.txt` (6289 lines, SCENE 176 max in export; live UI scene 392 = export SCENE 176 due to offset-216)

## Cluster signal

8 sibling repros in 24h on a single campaign. Per `~/.hermes/skills/repro/references/repro-planning-block-and-campaign-cluster-2026-07-18.md` §3, ≥3 siblings trigger root-cause-first prompt fix. At 8 siblings, the cluster is well past the threshold — the canonical action is **merge the existing unmerged fix branches**, not file a 9th per-scene issue.

| # | Issue / PR | Symptom scene | Symptom | Sub-class | Anchor violation |
|---|---|---|---|---|---|
| 1 | #8438 / [PR #8439](https://github.com/$GITHUB_REPOSITORY/pull/8439) | 78 | "Vaelaros-tuned Blood-Scent focus" silver vial, violet light, Gardener Inquisitor (LLM-invented NPC) | magic-sensor invention | No canonical item; `npc_data.Gardener Inquisitor` should never have been persisted |
| 2 | (no issue, retcon-only) | 81 | "Vaelaros signature vial" continued — not undone after scene 78 retcon | magic-sensor invention retcon-persistence | Scene 78 retcon didn't survive subsequent emit |
| 3 | #8440 / [PR #8441](https://github.com/$GITHUB_REPOSITORY/pull/8441) | (planning_block) | Inquisition choice emits despite retcon directive [3] | directive-vs-prose | `custom_campaign_state.god_mode_directives[3]` not honored |
| 4 | #8442 / wt #63 | (narrative) | MBTI / Alignment letters leaked to player-facing prose | internal-only vs player-facing | `master_directive.md` MBTI internal-only constraint not propagated |
| 5 | [#8444](https://github.com/$GITHUB_REPOSITORY/issues/8444) / [PR #8445](https://github.com/$GITHUB_REPOSITORY/pull/8445) | (planning_block) | "Rejoin the Host" choice presupposes Aegon at Mander mouth while co-present at Highgarden | NPC co-presence | `entity_tracking.active_entities["Aegon Targaryen"].status.location` contradicts choice premise |
| 6 | [#8451](https://github.com/$GITHUB_REPOSITORY/issues/8451) / [PR #8452](https://github.com/$GITHUB_REPOSITORY/pull/8452) | 171 | "frequency-sensitive ward" / "draconic resonance" / "Ghost-Hunter" / "Reaver-Hounds" — magic-sensor invention in middle of low-magic Reach | magic-sensor invention | `core_memories` Reach is non-magic; `custom_campaign_state.rule` forbids magical tracking |
| 7 | (AO `worldarchitect-65` / bead `rev-gkl06`) | 318/335/367/369 | "LLM keeps forgetting Aenar is dead" — Aenar revived as `status="surrendered"` after being `status="dead"` | NPC status erased | `npc_data["Aenar Vaelaros"].status` |
| 8 | session `20260719_160921_3faa1909` | 386 | "scene 386 should've referenced earlier suspicious from argella that I am more than I seem" — continuity gap | scene-history continuity | `narrative_history` of scenes where Argella established the suspicion was lost |
| 9 (this one) | repro `Cg2m2TkGFFez7XBynEah` scene 392 | 392 | "LLM forgot in control iron bank" — faction-control anchor contradiction | faction-control anchor | `core_memories` section 5 lists Iron Bank of Braavos; whoever is "in control" must be validated |

## What's in core memories (verified 2026-07-19)

Direct read of the test subject's `Sariel Valyria _copy__asyto1hC_game_state.json`:

```
core_memories:
  - §Campaign Bible Section 5: "The Iron Bank of Braavos"
    Primary Objective: To leverage the Valyrian civil war to seize control of
    eastern trade ports
    Listed as one of 9 antagonists (alongside Inquisition, Black-Glass Guild,
    Ironborn pirates, Citadel Gatekeepers, etc.)

custom_campaign_state:
  rule: "Explicitly forbid magical 'Iron-Scent' or 'Shadow-Signature' tracking
         of..."  (anti-tracking prompt rule)

npc_data (relevant):
  - "Aenar Vaelaros": {"tier": "noble", ..., "status": "dead"}  (scene 318 canonical)
  - "Aegon Targaryen": {"status": "co-present at Highgarden"}
  - "Argella Durrandon": (no `lore_origin` field; suspicion memory only in narrative_history)
```

**The Iron Bank IS in canon** — it's a faction-level anchor in §Section 5. The LLM emits "Iron Bank in control" without validating `custom_campaign_state` or `npc_data` for whoever actually controls it.

## Deployed-vs-branch-state gap (the actual root cause)

The durable fix exists in **two PR branches but neither is on `origin/main`**:

| PR | Branch | Status | What it adds |
|---|---|---|---|
| [PR #8443](https://github.com/$GITHUB_REPOSITORY/pull/8443) | `fix/narrative-anti-tracking-prompt-rule` | OPEN, NOT DRAFT, mergeable=true | §"NPC CANON ANCHORING (MANDATORY)" in `narrative_system_instruction.md` (lines 1389+):<br/>"Ground every NPC behavior, prop, and piece of equipment in `core_memories`, the entity manifest, named-NPC/faction data, and the setting's established constraints. Missing canon is not permission to invent."<br/><br/>17 follow-up commits including:<br/>- `b7b2620671` "fix(prompt): prioritize explicit canon over stale memories"<br/>- `dd5f94b279` "fix(prompt): preserve NPC canon rule through compaction"<br/>- `e8ca714baa` "ci: refresh PR evidence payload" (head) |
| [PR #8445](https://github.com/$GITHUB_REPOSITORY/pull/8445) | `fix/aegon-rejoin-co-presence-8444` | CLOSED (branch alive, head `ff419d7a7`) | Commit `4524525569` adds §"Canonical-State Anchor" to `planning_protocol.md` covering 4 anchor types:<br/>- §4 NPC Co-Presence (no "depart to find someone already present")<br/>- §5 God-Mode Directive Compliance (no choosing against an active rule)<br/>- §6 NPC Reachability (no "travel to where they aren't")<br/>- §7 NPC Status Alignment (no "trade with a dead enemy") |

**`origin/main` HEAD is `444c83d825`** — does NOT contain either commit. The deployed DEV bundle is therefore serving prompts WITHOUT either rule, which is exactly why the LLM keeps forgetting canonical state.

## Pre-flight recipe (the gap this reference exists to fill)

The user explicitly asked: *"is this related to other bugs? what's in core memories?"* This reference encodes the answer shape:

1. **Sibling enumeration** — `gh issue list --repo $GITHUB_REPOSITORY --state all --search "<entity> OR <campaign-id>" --limit 30`
2. **Core-memories direct read** — pull test subject's `_game_state.json`, search for the named entity in `core_memories` and `custom_campaign_state.rule`
3. **Canonical anchor validation** — check `npc_data.<entity>.status`, `entity_tracking.active_entities[].status.location`, `core_memories` section content
4. **Deployed-vs-branch gap check** — `git log origin/main --oneline | grep <fix-commit>` — if NOT present, the fix is sitting in an unmerged PR branch

If step 4 reveals the fix is in an unmerged branch: **the correct action is "merge the existing branches" not "file a 9th per-scene issue"**. Comment on the open PR requesting review; reopen the closed-but-branch-alive PR if needed.

## Architectural gap: `custom_state_keys == []` (Pitfall 10)

`state.custom_campaign_state` contains an explicit anti-tracking `rule` field, but there is **no structured state field** the LLM can check on every emit for per-campaign "do not invent" constraints. The rule lives in the prompt; it doesn't materialize as `custom_state.no_magic_detection_zone: bool` or `custom_state.faction_control: {<faction>: <owner-npc>}`.

The LLM re-derives these constraints from `core_memories` archetype descriptors every turn. The 8-sibling cluster on this campaign is structural evidence that prompt-layer rules alone are insufficient — the data-model needs `lore_origin` provenance fields and structured per-campaign "do not invent" zones.

**Recommended follow-up PR (not in scope for #8443 / #8445):**
- Add `custom_campaign_state.no_magic_detection_zone: bool` to `$PROJECT_ROOT/game_state.py`
- Add `npc_data.<NPC>.lore_origin = "user-introduced" | "LLM-invented"` provenance field
- Cross-campaign reproduction guard test against both `D3iZvnGiBl9wyveQBFj9` and `Cg2m2TkGFFez7XBynEah`

## Lessons learned

### 1. The cluster signal fires at 8, not 3

The original `repro-planning-block-and-campaign-cluster-2026-07-18.md` says "STOP filing per-scene issues at ≥3 siblings". At 8 siblings on a single campaign in 24h, the right action is also "merge existing unmerged branches" — the cluster-trigger recipe didn't model that the durable fix might already be sitting in PR branches waiting for ship.

### 2. PR-closed-but-branch-alive is a real pattern

PR #8445 is `CLOSED` (no merge), but the branch `fix/aegon-rejoin-co-presence-8444` is still alive and reachable via `git fetch origin`. The fix commit `4524525569` lives on this branch. Without `git branch --contains <commit> -a` + `gh pr view --json state`, an agent would assume the fix is lost.

### 3. The canonical-state-anchor family is structural, not per-scene

Even if PR #8443 + the commit from PR #8445's branch merge to origin/main, the underlying structural issue remains: most campaigns have `custom_state_keys == []`. The LLM has no architectural surface to enforce per-campaign canonical rules. Prompt-layer rules reduce the bug class by ~80%; the remaining 20% requires the custom_state extension.

### 4. `gh pr view --json` field-name pitfall (re-verified)

`gh pr view --json changed_files` (snake_case) returns `Unknown JSON field`. Use `changedFiles` (camelCase) or skip the field and use `gh pr diff <N>`. Same pitfall as the session `20260719_024714_3183418e` log — both 2026-07-18 and 2026-07-19 hit this.

## Cross-references

- [PR #8443](https://github.com/$GITHUB_REPOSITORY/pull/8443) — NPC CANON ANCHORING + Anti-Invented-Artifact (OPEN, NOT DRAFT, mergeable)
- [PR #8445](https://github.com/$GITHUB_REPOSITORY/pull/8445) — Canonical-State Anchor in `planning_protocol.md` (CLOSED, branch alive)
- Commit `4524525569` — "fix(prompts): add Canonical-State Anchor rule for planning_block + narrative emit (#8444 / cluster sibling fix)" on branch `fix/aegon-rejoin-co-presence-8444`
- `~/.hermes/skills/repro/references/repro-llm-invented-lore-artifacts-2026-07-18.md` — bug-class-4 (LLM-prose invention) durable-fix reference
- `~/.hermes/skills/repro/references/repro-planning-block-and-campaign-cluster-2026-07-18.md` — 5-anchor taxonomy + cluster-trigger decision tree
- `~/.hermes/skills/software-development/convergent-bug-triage/SKILL.md` — this umbrella skill (v1.2.0 added canonical-state-anchor family)
- AO worker `worldarchitect-65` / bead `rev-gkl06` — Aenar-dead-status follow-up
- `/tmp/your-project.com/repro-exports/sariel-171-test/Sariel Valyria _copy__asyto1hC.txt` — full test-subject prose export (6289 lines, SCENE 1-176)
- `/tmp/your-project.com/repro-exports/sariel-171-test/Sariel Valyria _copy__asyto1hC_game_state.json` — full test-subject game_state export (1878 lines)