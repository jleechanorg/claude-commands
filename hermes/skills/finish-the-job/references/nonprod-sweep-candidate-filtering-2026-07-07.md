# Non-prod sweep candidate filtering — verified bug case

**Date:** 2026-07-07
**Skill:** finish-the-job (v1.6.0)
**Repo:** $GITHUB_REPOSITORY
**Trigger:** User in Slack #worldai (`C0AH3RY3DK6`, thread `1783405558.744269`): "Lets run /roadmap but focus on the your-project.com repo and tell me about all the non prod PRs that look safe or logging only PRs and then lets /green them and do lite /er as needed"
**PRs produced by this session:**
- [#8207](https://github.com/$GITHUB_REPOSITORY/pull/8207) — `feat(scripts): add green_merge_nonprod.py` (fixes the open blocker that made this sweep possible)

## What happened

User asked for "all non-prod / safe / logging-only PRs." Agent pulled the open-PR list (80+ PRs), filtered by **title keywords** (`ci:`, `docs:`, `test:`, `feat(observability)`, `feat(telemetry)`, `chore(`, etc.), and produced a candidate list of 32 PRs.

The first sweep attempt to run `green_merge_nonprod.py` against all 32 revealed 17 had ≥1 file under `$PROJECT_ROOT/` or `testing_*/` — these are PROD-classified and the script refuses to auto-merge them. Specifically:

| Keyword classification | File-path truth | Examples |
|---|---|---|
| `chore(Dockerfile): drop Chainguard workarounds` | `$PROJECT_ROOT/Dockerfile` → PROD | #8206, #8202 |
| `feat(homunculus): swap Gemma3 → Qwen3-Coder 30B` | `$PROJECT_ROOT/llm_providers/gemini_homunculus.py` → PROD | #7936 |
| `feat(observability): BQ rate-limit telemetry` | `$PROJECT_ROOT/bq_logging.py` + `$PROJECT_ROOT/rate_limiting.py` → PROD | #7946, #7947, #7935 |
| `feat(rag): restore all 4 RAG modes` | `$PROJECT_ROOT/frontend_v1/js/settings.js` + `$PROJECT_ROOT/llm_service.py` → PROD | #7860 |
| `fix(infra): separate cron infra failure` | `testing_mcp/infra/*.sh` → PROD | #7873 |

The user said "non prod" loosely (meaning "anything that doesn't look like core product code"), but the project's authoritative definition (per `scripts/green_merge_nonprod.py` `PROD_PATH_PREFIXES`) is per-file-path: `$PROJECT_ROOT/`, `testing_mcp/`, `testing_ui/`.

After re-classification, only **14 PRs were actually strict-non-prod**; of those, only **1 (#7977) passed lite-green** at the moment of the sweep.

## The lesson (now in finish-the-job v1.6.0)

Title-keyword filtering is NOT authoritative for tier classification. The authoritative classifier is per-file-path against the project's `PROD_PATH_PREFIXES` (or equivalent). This applies to any /green sweep, /roadmap audit, or batch-merge triage.

**Mandatory preflight for any candidate-list generation in a /green sweep:**

1. Generate initial candidate list from title keywords (cheap, broad).
2. For each candidate, run `gh pr view <N> --repo OWNER/REPO --json files --jq '.files[].path'` (single API call).
3. Re-classify per file path against `PROD_PATH_PREFIXES` (the project's authoritative list, NOT the agent's assumption).
4. The final sweep list is the intersection: keyword-match AND all-files-non-prod.
5. Surface both buckets to the user — the "rejected as prod" count is itself a useful artifact (shows where the user's intuition diverged from the project's policy).

**Do NOT trust:**
- Title-only heuristics (e.g. `feat:` always non-prod — wrong, see #7860)
- Branch-name heuristics (e.g. `chore/...` always non-prod — wrong, see #8206)
- Author heuristics (e.g. factory PRs always non-prod — wrong, see #8056)
- Label heuristics (no project uses a "non-prod" label consistently)

**DO trust:**
- `gh pr view --json files` output, checked against the project's `PROD_PATH_PREFIXES` tuple
- If the script exists (`scripts/green_merge_nonprod.py`, `scripts/tier_classifier.py`, etc.), run IT — its output is the authoritative answer
- If no script exists, ask the user to confirm the tier taxonomy BEFORE sweeping

## Tier taxonomy — the per-project divergence

Different projects define prod/non-prod differently. The user's mental model and the project's authoritative list can diverge:

| Project | Authoritative NON-PROD rule (per file path) | User might assume |
|---|---|---|
| `$GITHUB_REPOSITORY` | NOT under `$PROJECT_ROOT/`, `testing_mcp/`, `testing_ui/` | `prompts/**` is also PROD; CI/safety/schema are also PROD |
| Other projects | Varies — always check | "non-prod = docs/CI/config" may over- or under-classify |

Before claiming a non-prod candidate list, surface the taxonomy to the user in ONE question if there's any ambiguity. Don't assume the user's loose framing matches the project's strict path-prefix classifier.

## Why this matters

If the agent had run the lite-green sweep on the original 32 PRs (including the 17 PROD ones), the script's `is_prod` guard would have prevented the merge BUT the user would have received a misleading status report ("we tried to green 32 PRs, all blocked") instead of the honest answer ("after file-path re-classification, only 14 were eligible, only 1 is currently ready"). The right framing turns a confusing 0/32 result into a clear 1/14 actionable number.

The `green_merge_nonprod.py` script's design (fail-closed on classification error, refuse to merge anything with a `$PROJECT_ROOT/` file) is the right safety pattern — but the agent must still surface the post-classification numbers honestly.

## Companion artifacts in this session

- PR [#8207](https://github.com/$GITHUB_REPOSITORY/pull/8207) — fixes 8 CodeRabbit review items on the original #7993, including the G1 fail-closed-on-pending-checks logic that prevents PRs with in-flight CI from being falsely marked "CI green"
- Cron `fe0c63821873` — babysit #8207 to merge, self-cancels on success (one-shot, --at 10m, not --every)
- Script: `$HOME/projects/your-project.com-wt-7993-cr/scripts/green_merge_nonprod.py` (the tool itself, on the new branch)

## Related

- Skill: `finish-the-job` v1.6.0 (this pitfall + new pre-flight gate)
- Skill: `green-claim-brief-fabrication-pr-8070-2026-07-06.md` (sibling live-state preflight, for green-claim briefs vs. candidate lists)
- Reference: `~/.claude/CLAUDE.md` § "Merge safety" — MERGE APPROVED gate for prod PRs
- Tool: `scripts/green_merge_nonprod.py` — the script whose behavior defines the classification rules