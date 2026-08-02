# Campaign-tier inventory — 2026-07-20 session

The canonical inventory from the first session that drove this skill. Cached here so future redesigns can re-read the source-of-truth audit outputs without re-running the parallel fan-out.

## Session context

User ask (verbatim): *"I wanna redesign all the god campaign and multi verse mechanics. Lets disable the sovereign/multi verse campaign and prompts for now and revisit the divine campaigns and use /ms and /history to read all the campaigns we have in llm wiki where i became a god and see how they got less challenging or mechanics werent great, then review this thread [Slack C0AH3RY3DK6/p1784580748.125749] to see some new ideas. The god mechanics should be general though and not specific to faerun or D&D. Also read some of my older campaigns where I was aizen the god of tryanny, might be in google docs or really old worldai website campaigns from $USER@gmail.com find it and see why I liekd those better, maybe it was one of the first ones but i liked them better."*

User correction mid-flight: *"Status on this and did you truly find and read aizen campaign and all the others I asked?"* — caught the agent drafting a `clarify` choice menu before delivering the inventory. Became the `memory-search` skill "Delivery contract — receipts before questions" patch.

## Phase 0 inventory outputs (cached at `/tmp/redesign_task{0,1,2}.md`)

| Output | Size | Sources covered |
|---|---:|---|
| `redesign_task0.md` | 50,889 chars | All 9 files in the current god/multiverse system: `$PROJECT_ROOT/prompts/multiverse/{sovereign_ascension_ceremony,sovereign_system}.md`, `$PROJECT_ROOT/prompts/divine/{divine_leverage_system,divine_ascension_ceremony}.md`, `$PROJECT_ROOT/prompts/god_mode_instruction.md`, `$PROJECT_ROOT/campaign_divine.py`, `$PROJECT_ROOT/god_mode_level_up.py`, `world_reference/aizen_god_mechanics.md`, `wiki/sources/god-mode-tips.md`. Each with: absolute path, summary, verbatim mechanical rules, JSON state shapes, cross-references. |
| `redesign_task1.md` | 20,776 chars | 9-store `/ms` fan-out for 5 fused queries (Q1 "sovereign multiverse disable", Q2 "Aizen god tyranny older", Q3 "divine ascension god mode", Q4 "world_reference BG3 faerun design", Q5 "became a god less challenging"). Hits: `~/roadmap/{2026-06-24-0824,2026-06-23-1208,2026-06-21-1724,2026-06-28-0113}-slack-thread-roadmap.md`, beads `$USER-d8lo`/`$USER-c0r`/`$USER-trt2`, claude memories `feedback_2026-05-29_god_mode_broken_prompt_reference.md` etc., hermes sqlite rowids 5972/93426/93427/22712, wiki sources `sovereign-protocol-system.md`/`aizen-bg3-campaign.md`/etc. |
| `redesign_task2.md` | 23,543 chars | Aizen-god-of-tyranny corpus inventory via `gog drive search` + `gog drive download` on $USER@gmail.com: 11 Google Docs + 6 PDF/txt files + 14 local-repo copies + 7 wiki distillations. Tier 1 (the canonical god-arc), Tier 2 (the Nocturne Sosuke "fourth tyrant" arc), Tier 3 (supporting artifacts). |

## Filesystem touch-points for the disable

The user asked to disable sovereign/multiverse. The cleanest disable surface, verified 2026-07-20:

| Layer | File | Line | Change |
|---|---|---|---|
| Constants | `$PROJECT_ROOT/constants.py` | 459–465 | `UNIVERSE_CONTROL_THRESHOLD = 70` → `99999` (sentinel — trigger never fires) |
| Detection | `$PROJECT_ROOT/campaign_divine.py` | 75–99 (`is_multiverse_upgrade_available`) | Short-circuit to `False` for any non-divine tier; preserve explicit-flag override |
| Detection | `$PROJECT_ROOT/campaign_divine.py` | 143 (`get_pending_upgrade_type`) | Remove multiverse-first priority |
| Prompt loader | `$PROJECT_ROOT/agent_prompts.py` | 2899–2905 | Add `disallow: sovereign` mirror of the divine loader |
| Prompts | `$PROJECT_ROOT/prompts/multiverse/` | (whole dir) | Move to `$PROJECT_ROOT/prompts/multiverse_disabled/` (don't delete) |
| Wiki | `~/llm_wiki/wiki/sources/sovereign-protocol-system.md` | (frontmatter) | Add `disabled: true` + `disabled_date: 2026-07-20` + `redesign_target: world_reference/god_mechanics_redesign_v2.md` |

Beads affected:
- `$USER-d8lo` (priority 1, fix): gate god-mode `campaign_tier` writes through `CampaignUpgradeAgent`. Can be partially closed by PR A (the disable) and fully closed by PR B (the redesign + correct routing).
- `$USER-trt2` (orphaned worktree `repro/multiverse-disable-divine-directive-8103`, never pushed): this session is the canonical resurrection. Salvage the 4 commits, branch from `origin/main`, ship as PR A.

## Production code touch-points for the redesign

Per `$PROJECT_ROOT/campaign_divine.py` audit + `$PROJECT_ROOT/god_mode_level_up.py` audit:

- `$PROJECT_ROOT/campaign_divine.py` (114 lines, 6 functions): replace `is_divine_upgrade_available` with the new setting-agnostic threshold table.
- `$PROJECT_ROOT/god_mode_level_up.py` (PR #7376): Path A/B/C contract is well-tested (19 tests in `tests/test_god_mode_level_up_contract.py`). **Preserve the fail-closed invariants** — they're load-bearing for the 17-day level-up saga.
- `$PROJECT_ROOT/prompts/god_mode_instruction.md`: the admin pause-menu prompt. Update the cross-reference block (currently names `sovereign_system_instruction.md` and `divine_system_instruction.md` — replace with the new v2 path).
- `$PROJECT_ROOT/prompts/divine/divine_leverage_system.md` (full rulebook, ~12K tokens): the canonical content for the redesign. Don't edit in place — write `divine_leverage_system_v2.md` and route the loader at it via feature flag.
- `$PROJECT_ROOT/prompts/divine/divine_ascension_ceremony.md` (8-phase ceremony): same — write `_v2.md` and route.
- `$PROJECT_ROOT/constants.py` (DIVINE_RANK_* thresholds, level 1–51+): preserve the level→rank mapping; remap the names per the setting-agnostic request (Quasi-Deity → Tier 1, Demigod → Tier 2, etc.).
- `wiki/sources/god-mode-tips.md` (editorial guidance, 2026-04-13): update the "Divine and sovereign instruction files load automatically" block to reflect the new tier list.

## Open question deferred to PR B

Per the user's explicit "lets disable sovereign for now and revisit the divine" — PR A is purely disable, no redesign. PR B is the redesign. The user asked for a scope check before either ship. As of session end (2026-07-20 22:xx PT), the agent delivered inventory + 1-scope-question; user has not yet picked (A) code-PR-both or (D) campaign-modules-only. Status as of this writing: **awaiting user scope decision**.

## What's in `/tmp/` for handoff

```
/tmp/redesign_task0.md      # 50,889 chars — file audit
/tmp/redesign_task1.md      # 20,776 chars — /ms 9-store fan-out
/tmp/redesign_task2.md      # 23,543 chars — Aizen corpus inventory
/tmp/gemini_v7_full.txt     # 11,054 words — God of Murder BG3 campaign from linked thread (saved by prior session)
/tmp/pr_body_god_of_murder.md  # PR body for the linked-thread deliverable (PR #8483)
```

`/tmp/` is sandbox-scoped per `execute_code` calls, so these will not survive a sandbox restart. For long-term storage, write the design doc to `world_reference/god_mechanics_redesign_v2.md` in the your-project.com repo (per Phase 2 of the umbrella skill).

## Cross-references to other skills / docs

- `memory-search` skill — the parallel fan-out pattern that produced these files (Phase -1 "Delivery contract — receipts before questions").
- `google-credentials-fallback` §5 — the `gog drive search` recipe that produced the Aizen doc IDs.
- `references/aizen-god-mechanics-pattern.md` (in this skill) — the durable knowledge extracted from the inventory.
- `~/.hermes/workspace/SOUL.md` `## COMMIT: push-pr-donot-stop-halfway` — durable state must be a `git push origin`, not a local commit.
- `~/.hermes/workspace/SOUL.md` `## COMMIT: pr-clean-branch-from-main-no-history-bloat` — branch from `origin/main` for both PRs.
- `~/.claude/skills/zero-touch.md` — 7-green gate per PR.