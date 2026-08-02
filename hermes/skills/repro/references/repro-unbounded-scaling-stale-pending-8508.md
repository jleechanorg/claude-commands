---
name: repro-unbounded-scaling-stale-pending-8508
description: Diagnostic recipe for the new (2026-07-21) "god-mode stuck saying level N isn't complete" bug class on $GITHUB_REPOSITORY — affects characters in the unbounded-scaling regime (L30+, +50,000 XP/level). Distinct from NPC-status-persistence and god-mode-directive-missing. Verified on issue #8508 across two unrelated campaigns (q04GfOEl4SWnEQrFUVST L50 + wSm8Z8McTLJ8oQjqlTyJ L77).
tags: [repro, worldarchitect, level-up, unbounded-scaling, rewards-engine, god-mode, canonical-state-anchor, sibling-cluster, 8508]
---

# Unbounded-scaling stale pending level-up — diagnostic recipe

This file is the durable reference for bug-class-5 in the canonical-state-anchor
taxonomy. The user-reported symptom is:

> "God mode can't clear the pending level up flags — stuck saying level N isn't complete"

…where N is the user's current `player_character_data.level`. Affects characters
in the **unbounded-scaling regime** (level ≥ 30 = `MAX_LEVEL`).

## When this recipe applies

The signal is *exactly*:

1. User pastes a `/game/<id>` URL and reports "stuck saying level N isn't complete" / "god mode can't clear pending level-up" / "level-up modal never closes."
2. `N >= 30` (the `MAX_LEVEL` boundary from `$PROJECT_ROOT/game_state.py:137` `MAX_LEVEL = len(XP_THRESHOLDS) = 30`).
3. The character is in the +50,000 XP/level scaling regime (per `game_state.py:1616-1619` "Infinite scaling beyond the table (50,000 XP per level)").
4. Persistent Firestore `rewards_pending.level_up_available=True` with `new_level > N` is NOT cleared.

## Root cause — three stale-clear branches all miss

The single canonical stale-clear lives in
`$PROJECT_ROOT/game_state.py:ensure_level_up_rewards_pending` (lines 2077-2129).
Three branches try to clear `rewards_pending`; **none of them fires** when the
character is in the unbounded-scaling regime with XP already at/past the next
threshold:

| Branch | File:line | Condition | Fires at L50→L51? |
|---|---|---|---|
| 1. Lazy proxy | `game_state.py:2081` | `_is_stale_rewards_pending_lazy_proxy(...)` | No — target (51) > current (50), modal still projects |
| 2. `stored_level >= existing_new_level` | `game_state.py:2094` | committed level already at/past target | No — 50 < 51 |
| 3. `current_xp < xp_threshold_for_pending` | `game_state.py:2121` | XP below the threshold for the target | No — XP ≥ 1,905,000 already crossed (for L51) |

Symmetrically, `rewards_engine.py:413-433`
(`rewards_box_level_transition_is_actionable`) returns `True` whenever
`target_level > current_level` — so the LLM keeps narrating "you have a level-up
pending" because the box IS actionable by the LLM-side predicate.

## Why god mode can't clear it (architectural asymmetry)

The god-mode `GodModeAgent` final-output contract at
`$PROJECT_ROOT/agents.py:1142-1158` explicitly forbids writing `rewards_pending` from
the admin-commit path. The contract reads (paraphrased):

> "Admin commit: write `state_updates.player_character_data.level`, NO
> `level_up_now` / `finish_level_up_return_to_game` choices, NO top-level
> `level_up_signal`, `rewards_box.level_up_available` unset or false."

So even after the user types `GOD MODE: set level = 51`, the backend ignores
`rewards_pending` and relies on `ensure_level_up_rewards_pending` to clear it
on the next turn. But the next turn's stale-clear branches still don't fire.

## Verified cross-campaign evidence (issue #8508, 2026-07-21)

| Campaign | Symptom | User's `current_level` | Target in `rewards_pending` | XP threshold for target |
|---|---|---|---|---|
| `q04GfOEl4SWnEQrFUVST` | "stuck saying level 50 isn't complete" | 50 | 51 | 1,905,000 |
| `wSm8Z8McTLJ8oQjqlTyJ` | "stuck suggesting level 77" | 77 | 78 | 3,255,000 |

Both campaigns hit the same three branches (all False), same admin-commit
forbidden-write contract, same architectural asymmetry. **Bug is structural,
not per-campaign.**

## First-touch diagnostic (5 steps)

Run BEFORE filing the issue (per `~/.hermes/skills/repro/references/static-evidence-sufficient-no-live-turn.md`).

1. **Pull the live Firestore state** for `users/<uid>/campaigns/<cid>/game_states/current_state` (the canonical path per `~/.hermes/skills/repro/references/firestore-path-and-uid-resolution.md`).

   ```bash
   ./venv/bin/python scripts/copy_campaign.py --find-by-id <CID>   # resolve source UID
   # Then REST GET the game_states/current_state doc directly. Do NOT call
   # get_campaign_state before this — it can normalize/clean state.
   ```

2. **Read the three relevant fields in this order:**
   - `player_character_data.level` (the user's current)
   - `rewards_pending.level_up_available` (should be False when complete)
   - `rewards_pending.new_level` (the stuck target — confirm it is > `player_character_data.level`)

3. **Compute the threshold:**
   ```python
   from mvp_site.game_state import xp_needed_for_level, MAX_LEVEL
   threshold = xp_needed_for_level(rewards_pending.new_level)
   ```
   If `rewards_pending.new_level > MAX_LEVEL`, the threshold is in the +50K XP/level regime (`xp_needed_for_level` handles this at `game_state.py:1652-1657`).

4. **Classify**:
   - If `player_character_data.level >= MAX_LEVEL (30)` AND `rewards_pending.level_up_available=True` AND `current_xp >= threshold` AND `rewards_pending.new_level > player_character_data.level` → **THIS BUG CLASS**.
   - Any other combination is a different bug (god-mode-directive-missing Factor A-G, NPC status persistence, etc.).

5. **Sibling-campaign check**:
   ```bash
   gh issue list --repo $GITHUB_REPOSITORY --search "stuck level OR pending level-up OR level-up not complete"
   ```
   When ≥2 issues hit the same root cause across DIFFERENT `campaign_id`s, file a sibling-cluster flag in the issue body.

## Recommended fix shape (3 components, mirror PR #8500 + PR #8498 lessons)

1. **Prompt-layer first** (per `references/prompt-fix-deliverable-shape-2026-07-18.md`):
   - `$PROJECT_ROOT/prompts/level_up_modal_override_instruction.md`: add §"Unbounded-Scaling Level-Up (L30+)" worked example teaching the LLM that god-mode admin-commit beyond `MAX_LEVEL=30` must include `directives.add` clearing `rewards_pending.level_up_available=false`.
   - `$PROJECT_ROOT/prompts/god_mode_instruction.md`: mirror in directives table.
   - `$PROJECT_ROOT/agents.py:1142-1158` `GodModeAgent` final-output contract: extend the "Admin commit" bullet with explicit `rewards_pending.level_up_available:false` write requirement when `target_level > MAX_LEVEL`.

2. **Backend gating** (minimal, logged):
   `$PROJECT_ROOT/game_state.py:2121` — change the third-branch condition from

   ```python
   elif current_xp < xp_threshold_for_pending:
   ```

   to

   ```python
   elif (current_xp < xp_threshold_for_pending) or (
       current_xp >= xp_threshold_for_pending
       and stored_level >= MAX_LEVEL
       and not is_state_flag_true(custom_state.get("level_up_in_progress"))
   ):
   ```

   Plus a follow-up branch that, when `stored_level >= MAX_LEVEL` AND `target_level > stored_level`, clears `rewards_pending` while preserving the existing `level_up_in_progress` interaction.

3. **Test contract**:
   `$PROJECT_ROOT/tests/test_unbounded_scaling_stale_pending_clears_8508.py` — at least 6 cases:
   - L50→L51 basic (the q04GfOEl4SWnEQrFUVST case)
   - L77→L78 basic (the wSm8Z8McTLJ8oQjqlTyJ case)
   - L100 extreme
   - Mid-modal preservation (level_up_in_progress=True keeps rewards_pending)
   - Processed-flag interaction
   - Idempotent double-call
   - No-op when rewards_pending absent

   Use the walk-up `__file__` repo-root resolver pattern from
   `$PROJECT_ROOT/tests/test_clear_level_up_lock_flags.py` so the test works from
   inside a worktree (per `references/contract-test-resolver-pitfall.md`).

## Cross-skill references

- `~/.hermes/skills/repro/references/non-repro-verification-recipe.md` — 5-step
  non-repro verification recipe; load FIRST when the user says "the LLM forgot
  X / X is acting alive but should be dead" — this bug class is NOT that one.
- `~/.hermes/skills/repro/references/prompt-fix-deliverable-shape-2026-07-18.md`
  — 4-component deliverable shape (prompt section + narrative mirror + test
  file + PR body), verified on PR #8446.
- `~/.hermes/skills/repro/references/prompt-delivery-vs-content-2026-07-20.md`
  — BEFORE writing prompt rule, verify via BQ that the LLM does NOT already
  receive the existing rule. If BQ shows it IS in payload, shift to
  `directives.add` narration in `narrative_system_instruction.md` + minimal
  backend gating ONLY.
- `~/.hermes/skills/repro/references/phenotype-lock-static-evidence.md` —
  sibling-campaign structural-issue flag (≥3 open repros across DIFFERENT
  `campaign_id`s on same root cause → structural issue, prompt-layer first).

## Pitfalls

1. **Don't trust the user's exact scene number** — per
   `references/bq-llm-payload-truncation-pitfall.md` pitfall §"scene-number-vs-turn_index":
   the user-reported "scene N" may not match any `turn_index` in BQ. Use
   `MAX(turn_index)` to anchor, then derive scene number from the story-doc
   timestamp-sorted index.

2. **Don't file this as a god-mode-directive-missing Factor A-G sibling** —
   the Factor A-G family is about text directives being dropped from the LLM
   payload. This new class is about a *deterministic stale-clear gate missing
   for unbounded scaling*, with god-mode admin-commit forbidden from writing
   the field. Different mechanism, different fix shape.

3. **Don't skip the prompt-layer component** — per PR #8498 2.9.0 lesson, the
   LLM-already-received-the-rule branch is likely true here. Verify via BQ
   `gemini_provider.stream` raw request that the existing
   `level_up_modal_override_instruction.md` does or does not include the
   unbounded-scaling clause. If BQ shows the rule IS in payload, the fix
   shifts toward `directives.add` narration in
   `narrative_system_instruction.md` and minimal backend gating.

4. **Don't auto-merge the fix-PR** — per user conditional approval pattern
   (`POST APPROVED` for social, `merge approved once /green AND only prompt or
   test changes` for PRs), production-code PRs are excluded from auto-merge
   even when branch protection allows.

## Verified worked example

Issue [#8508](https://github.com/$GITHUB_REPOSITORY/issues/8508)
filed via `gh-safe-publish` on 2026-07-21, gated through
`lib/outbound_secret_gate.py`, comment posted with cross-campaign evidence at
issue-comment 5036950025.

Cluster siblings on `q04GfOEl4SWnEQrFUVST` (this campaign only):
- [#8490](https://github.com/$GITHUB_REPOSITORY/issues/8490) — Factor F (combat scope classifier)
- [#8497](https://github.com/$GITHUB_REPOSITORY/issues/8497) — Factor G (Mantle of the Radiant Slayer default-classifier)
- [#8499](https://github.com/$GITHUB_REPOSITORY/issues/8499) / [PR #8500](https://github.com/$GITHUB_REPOSITORY/pull/8500) — NPC Peer-Autonomy canonical-state anchor §8
- [#8508](https://github.com/$GITHUB_REPOSITORY/issues/8508) — THIS BUG (unbounded-scaling stale pending)

Cross-campaign sibling:
- `wSm8Z8McTLJ8oQjqlTyJ` (same root cause, distinct campaign) — see comment
  on #8508 for the L77→L78 reproduction analysis.

## Status as of 2026-07-21

Issue filed (gated), diagnostic shipped to user. AO dispatch attempt on
`worldarchitect-80/81/82` (3 spawns) all returned `SESSION_INCOMPLETE_HANDLE`
on `ao send` — see `~/.hermes/skills/dispatch-task/SKILL.md` for the new
pitfall entry covering this failure mode. Dispatch brief written to
`~/.hermes/wa-repro-8507/dispatch-brief.md` for the next session that has a
working AO.