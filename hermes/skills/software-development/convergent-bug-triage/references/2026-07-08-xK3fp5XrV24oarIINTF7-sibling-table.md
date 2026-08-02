# 2026-07-08 — campaign `xK3fp5XrV24oarIINTF7` sibling table

Five investigations on the same campaign within ~12 hours. All reduce to one root family ("LLM emits correct structured field, downstream path drops it") with five different surfaces. This is the canonical example for `convergent-bug-triage`.

## Sibling table

| Time (UTC) | Issue | PR | Surface symptom | Class surface | Root mechanism | File owned | Dispatch decision |
|---|---|---|---|---|---|---|---|
| 2026-07-04 | #8160 | (closed dup of #7885) | Character-creation spells/abilities missing | Modal-completion | Modal-exit guard `character_creation_completed=True` never written | `world_logic.py` modal-finish path | Folded into #7885 |
| 2026-07-08 ~05:00 | #8266 | #8267 (closed) | Aemond capture persistence, scene 149 lineage | State propagation | Wrong-write + missing-write in `state_updates.npc_data` | `$PROJECT_ROOT/game_state.py` canonicalizer + `world_logic.py` save path | Separate PR — closed (superseded by #8265) |
| 2026-07-08 ~05:50 | - | #8271 (open) | NPC narrative status propagation | State propagation | Prompt missing rules for narrative-only status changes | `$PROJECT_ROOT/prompts/game_state_instruction.md` | Sibling — separate worker |
| 2026-07-08 ~04:50 | - | #8265 (open) | Lineage canonicalization | State field preservation | `parentage` field missing from allowed schema keys, moved to `extras` | `$PROJECT_ROOT/game_state.py`, `schemas/`, `world_logic.py` | Sibling — separate worker |
| 2026-07-08 ~06:55 | #8275 | #8276 (open, scaffold only) | Queen-level-14 god-mode directive ignored | God-mode save | Streaming-path save-drop (sibling of #8103, fix PR #8132 still open) | `world_logic.py` LLM-parser save + `agents.py` directive routing | Sibling — needs PR #8132 to merge first |
| 2026-07-08 ~08:06 | #8277 | (dispatched wa-3225) | Scene event `companion_request` not rendered in narrative | Render path | ESSENTIALS contract vs `narrative_integration` field schema contradiction | `$PROJECT_ROOT/prompts/living_world_instruction.md` (line ~841-865) | Sibling — separate worker wa-3225 |

## Triage logic applied

1. **Loaded `gh issue list --limit 20` and saw 5 issues opened today on the same campaign.** Did not panic — checked sibling vs duplicate first.
2. **Read PR bodies for #8267, #8271, #8265, #8276.** All 4 cross-reference each other in their "siblings" sections already — the family was self-evident from the repo state, not just from the new symptom.
3. **Classified the new symptom** (scene_event not rendered) into the family. The LLM wrote `state_updates.scene_event` correctly, but the render path dropped it from `narrative`. **Sibling, not duplicate.**
4. **Cross-referenced** in issue #8277's body — listed all 4 existing investigations + the 2 sibling PRs + the new issue as a 7-line table.
5. **Dispatched ONE AO worker (wa-3225)** for #8277. Did NOT fan out N workers. The user can read wa-3225's GREEN before deciding whether to dispatch the next sibling.
6. **Encoded a "Files to NOT touch" clause** in wa-3225's brief — `game_state_instruction.md` (#8271), `game_state.py` (#8265), `world_logic.py` (#8276) all belong to other workers. wa-3225 owns only `living_world_instruction.md`.

## What this skill would have prevented (in a counterfactual without it)

- The June 13, 2026 repro on campaign `71eQ0Yb1oY205xtKhZS4` (issue #7547) was the **same class**. Without the skill, that investigation ended at iteration cap with no PR filed, no cross-campaign audit, and no recognition that the bug would re-emerge on different campaigns.
- The 2026-06-20 ESSENTIALS-rule patch (added to `living_world_instruction.md`) was a partial fix — it added the contract rule but left the field schema at line 841-865 contradicting it. The skill would have caught this as Pitfall 3 (field schema vs ESSENTIALS contract contradiction) and added the prompt rewrite + field-definition rewrite in one PR.

## Files

- New umbrella skill: `~/.hermes/skills/software-development/convergent-bug-triage/SKILL.md`
- Dispatch-task patch: `~/.hermes/skills/hermes-imports/dispatch-task/SKILL.md` — added 20-session-cap preflight + GitHub-bucket-rate-limit preflight
- Repro skill (`~/.hermes/skills/repro/SKILL.md`) unchanged — thin pointer to canonical at `~/.claude/skills/repro-twin-clone-evidence/SKILL.md`

## Verification

- `skill_view(name='convergent-bug-triage')` returns the new SKILL.md
- `skill_view(name='dispatch-task')` shows the two new preflight sections
- `gh issue view 8277 --repo $GITHUB_REPOSITORY` shows the Sibling investigations table

## Outstanding work (next session)

- After wa-3225 lands its PR, dispatch next sibling: queen-level-14 (#8275/#8276) — but PR #8132 needs to merge first (streaming-path save-drop is the upstream fix; #8276 should land after #8132 to avoid conflict in `world_logic.py` directive routing).
- After #8276, dispatch lineage canonicalization followup if #8265 needs a followup branch (currently OPEN).
- Eventually, audit all 50+-scene campaigns for prompt-discipline divergence (per user's "check other longer campaigns in firestore too" directive). wa-3225 owns this audit.