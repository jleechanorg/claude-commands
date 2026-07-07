# gbrain skillify v1.1.0 → Hermes port rationale

This document explains why specific items of the [gbrain skillify v1.1.0](https://github.com/garrytan/gbrain/blob/master/skills/skillify/SKILL.md) 11-item checklist are deferred or marked N/A in the Hermes backport.

## Items shipped

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | SKILL.md | **shipped** | Rewritten with the 11-item contract verbatim; YAML frontmatter + Contract + Phases + Output Format. |
| 2 | Deterministic code | **shipped** | `scripts/skillify_check.py` is the 11-item audit; `scripts/check_resolvable.py` is the structural pass; `scripts/trigger_eval.py` is the semantic pass. |
| 4 | Unit tests | **shipped** | `tests/test_*.py` covers the major branches of every script. |
| 5 | Integration tests | **shipped** | Tests invoke the shipped scripts on the **live** skill tree (no mocks at the boundary). |
| 7 | Resolver trigger entry | **shipped** | `## skillify` heading in `skills/RESOLVER.md` with triggers on the same line. |
| 8 | Resolver trigger eval | **shipped** | `routing-eval.jsonl` uses the gbrain schema `{intent, expected_skill, ambiguous_with?}`; `tests/test_trigger_eval.py` runs the fixture through `trigger_eval.py`. |
| 9 | check-resolvable | **shipped** | `scripts/check_resolvable.py` walks `skills/RESOLVER.md` and asserts each heading points to a real SKILL.md (no orphan, no dup, no ambiguous). |
| 10 | E2E smoke test | **shipped** | `tests/test_e2e.py` exercises the full pipeline: invoke `skillify_check` + `check_resolvable` + `trigger_eval` against the live tree and assert the combined exit code is 0. |

## Items deferred

| # | Item | Why deferred | Substitute in Hermes |
|---|------|--------------|-----------------------|
| 3 | Cross-modal eval (3 frontier models, ≥7 mean, ≥5 floor) | **Deferred.** Requires the gbrain cross-modal orchestration (`gbrain eval cross-modal`) which dispatches 3 frontier models from 3 different providers in parallel and scores on 5 documented dimensions. Hermes does not yet wire that into its gateway; the substitute is the `advice` skill, which calls a single hostile-reviewer subagent for an adversarial pass at the cost of one LLM turn. We accept the lower confidence floor in exchange for shipping the other 9 items now. | `/advice` adversarial review. When `skillify` is applied to a production change, the SOP is `(/advice → /skillify → /advice → /er)` rather than the gbrain SOP `(/skillify → cross-modal eval)`. |

## Items N/A

| # | Item | Why N/A |
|---|------|---------|
| 6 | LLM evals | **Conditional.** Required only when the skill calls an LLM as part of its run. The `skillify` skill itself does not invoke an LLM in its CLI (`scripts/skillify_check.py`, `scripts/check_resolvable.py`, `scripts/trigger_eval.py` are all deterministic). However we ship `evals/{rubric.json, cases.jsonl, run_eval.py}` as scaffolding so a *derived* skillify skill — one that uses an LLM for rubric scoring or eval improvement — has a starting point. |
| 11 | Brain filing | **N/A.** The `skillify` skill does not write brain pages. If a future skill uses `skillify` to create a brain-filing skill, that derived skill's SKILL.md will describe its own `brain/RESOLVER.md` filing rule. |

## Items deferred to a follow-up PR

| # | Item | Why deferred | Tracking |
|---|------|--------------|----------|
| 9 (extended) | MECE / DRY overlap detection | Out of scope for v2.0.0. Detecting overlapping triggers across 166+ skills requires pairwise comparison over parsed YAML frontmatter + a similarity metric; ship as a follow-up. |
