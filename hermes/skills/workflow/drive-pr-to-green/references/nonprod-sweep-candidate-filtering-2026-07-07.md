# Non-prod sweep candidate filtering + lite-green terminology — verified bug case

**Date:** 2026-07-07
**Skill:** drive-pr-to-green (v1.5.0)
**Repo:** $GITHUB_REPOSITORY
**Trigger:** User in Slack #worldai (`C0AH3RY3DK6`, thread `1783405558.744269`): "Lets run /roadmap but focus on the your-project.com repo and tell me about all the non prod PRs that look safe or logging only PRs and then lets /green them and do lite /er as needed"

## What happened

User asked for batch /green of "non prod / safe / logging only PRs" on your-project.com. The user-supplied loose framing ("non prod") does NOT match the project's strict per-file-path classifier. The agent produced a candidate list of 32 PRs filtered by title keywords (`ci:`, `docs:`, `test:`, `feat(observability)`, `feat(telemetry)`, `chore(`, `refactor:`) — but **17 of those 32 had ≥1 file under `$PROJECT_ROOT/` or `testing_*/`** and are PROD-classified by `scripts/green_merge_nonprod.py`'s `PROD_PATH_PREFIXES = ("$PROJECT_ROOT/", "testing_mcp/", "testing_ui/")`.

The script `green_merge_nonprod.py` (added in PR #8207, supersedes #7993) enforces the classification via file-path and refuses to auto-merge prod PRs by design — so a literal "merge all 32" invocation would have correctly skipped the 17 PROD PRs, but the user would have received a misleading status report ("we tried 32, all blocked") instead of the honest one ("14 strict-non-prod, 1 ready at this moment").

## Lite-green terminology clarification

The user said "**lite /er**" — this is **NOT** a documented term in any memory store or skill. The canonical term is **lite-green**, defined as a 3-gate subset of the full 7-green definition:

| Gate | Lite-green | Full 7-green |
|---|---|---|
| G1: CI green (fail-closed on pending checks) | ✅ | ✅ |
| G2: mergeable (no conflicts) | ✅ | ✅ |
| G3: CodeRabbit APPROVED | ✅ | ✅ |
| G4: Bugbot clean (cursor[bot]) | ❌ | ✅ |
| G5: unresolved review threads | ❌ | ✅ |
| G6: evidence pass (`/er` or `/es`) | ❌ | ✅ |
| G7: Skeptic VERDICT: PASS | ❌ | ✅ |
| G8: Smoke Gate Wait | ❌ | ✅ |

The script `green_merge_nonprod.py` implements lite-green (G1/G2/G3 only). `/er` is a separate protocol — it's the evidence-review step that your-project.com's repo-wide PR template references in the body. Lite-green does NOT include `/er`.

If the user says "lite /er," clarify which they mean:
- (a) **lite-green + no /er**: skip the evidence step entirely. Suitable for docs/infra/tooling where evidence is irrelevant.
- (b) **lite-green + lightweight /er**: skip Skeptic Gate 7 but still run a quick evidence check (e.g. grep for `gh` API surface, check the diff is non-behavioral).

The 2026-07-07 sweep default was (a) — for the 14 strict-non-prod PRs, no `/er` was required because none of them touched user-visible behavior.

## Authoritative classifier recipe (verified 2026-07-07)

**Before claiming any candidate list for a /green sweep:**

```bash
# 1. Initial keyword filter (cheap, broad)
CANDIDATES=$(gh pr list --repo $GITHUB_REPOSITORY --state open --limit 200 \
  --json number,title --jq '.[] | select(.title | test("ci:|docs:|test:|feat\\(observability\\)|chore\\(|refactor:"; "i")) | .number')

# 2. Per-PR file-path re-classification against PROD_PATH_PREFIXES
PROD_PREFIXES='^($PROJECT_ROOT/|testing_mcp/|testing_ui/)'
STRICT_NONPROD=()
PROD_CAUGHT=()

for n in $CANDIDATES; do
  FILES=$(gh pr view "$n" --repo $GITHUB_REPOSITORY --json files --jq '[.files[].path] | .[]')
  IS_PROD=false
  for f in $FILES; do
    if echo "$f" | grep -qE "$PROD_PREFIXES"; then
      IS_PROD=true
      break
    fi
  done
  if $IS_PROD; then
    PROD_CAUGHT+=("$n")
  else
    STRICT_NONPROD+=("$n")
  fi
done

echo "Strict-non-prod: ${#STRICT_NONPROD[@]} | Prod-caught: ${#PROD_CAUGHT[@]}"
```

**Verified results on 2026-07-07:**

| Bucket | Count | Examples |
|---|---|---|
| Keyword candidates | 32 | initial filter |
| Strict-non-prod (passed file-path gate) | 14 | #8204, #8197, #8193, #8181, #8179, #8173, #8165, #8152, #8131, #8119, #8074, #7977, #7941, #7868 |
| Prod-caught (had ≥1 prod-prefix file) | 17 | #8206 ($PROJECT_ROOT/Dockerfile), #7946 ($PROJECT_ROOT/bq_logging.py), #7860 ($PROJECT_ROOT/frontend_v1/js/settings.js), #8050 (testing_mcp/...), #7873 (testing_mcp/...) |

After running the script, the live counts further dropped:
- 🟢 Ready for lite-green merge: 1 (#7977)
- 🟡 Need work (gated by G1/G2/G3): 13
- 🔴 Prod (script refuses): 17

## Companion artifacts

- Script: `$HOME/projects/your-project.com-wt-7993-cr/scripts/green_merge_nonprod.py` — the tool that defines the classification and gates
- PR [#8207](https://github.com/$GITHUB_REPOSITORY/pull/8207) — the script (with all CR fixes from #7993)
- Cron `fe0c63821873` — babysit #8207 to merge
- Memory reference: `finish-the-job/references/nonprod-sweep-candidate-filtering-2026-07-07.md` — sibling skill reference

## When NOT to use this skill for sweep classification

If the target repo does NOT have a `green_merge_nonprod.py`-style tool:
- The agent must manually re-classify by `gh pr view --json files` against the user's stated (or inferred) tier taxonomy
- Surface the taxonomy to the user BEFORE sweeping — "non-prod" means different things in different projects
- One block on user direction is acceptable; mid-stream re-classification twice in the same sweep is a bug

If the target repo has a `green_merge_nonprod.py` (or similar) tool already merged:
- The script's classification IS the authoritative answer — don't second-guess it
- The script's `is_prod` guard prevents accidental merges of misclassified PRs
- Surface the script's bucket counts (Ready / Need-work / Caught-as-prod) in the final reply

## Related

- Skill: `drive-pr-to-green` v1.5.0 (this pitfall + reference)
- Skill: `finish-the-job` v1.6.0 (sibling pitfall "Candidate-list classification trap")
- Skill: `roadmap` — the `/roadmap` report's § B PR Auto-Merge Candidates table has the same trap
- Memory: `qa-test-failure-dismissal-anti-pattern` — the "same-name rule" applied to PR-tier dismissal
- Tool: `scripts/green_merge_nonprod.py` — defines `PROD_PATH_PREFIXES` and the lite-green 3-gate contract