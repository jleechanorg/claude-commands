# Bug-hunt cron rate-limit suppression — 2026-07-22 16:40 PT

The Daily Bug Hunt Report posted to Slack at `bug-hunt-20260722_164009.md` reported:

> PRs reviewed: 0 / Bugs found: 0 / Agent failures: 0/0

That number was wrong. There were **8 merged PRs across the four scanned repos in the last 2 days**, and the report's own sibling runs in the same minute showed that the script knew it had failed — it just suppressed the failure on this one report.

## The smoking-gun: three sibling reports from the same minute

| Timestamp | Bucket | Behavior |
|---|---|---|
| `16:40:07` | **A** (correctly surfaced) | `## PR Discovery Failure` block + GraphQL rate-limit message |
| `16:40:09` | **A** (suppressed — the user-visible report) | "No merged PRs found in the last 2 days." with all-zero counts |
| `16:40:11` | **B** (preflight short-circuit) | Retried with fixture data `(#1: test pr x4)`, `Agent failures: 3/3` |

Files:
- `/tmp/hermes/bug_reports/bug-hunt-20260722_164007.md`
- `/tmp/hermes/bug_reports/bug-hunt-20260722_164009.md` ← the one delivered to Slack
- `/tmp/hermes/bug_reports/bug-hunt-20260722_164011.md`

Plus 0-byte agent outputs at `bug-hunt-{claude,gemini,minimax}-20260722_164011.{json,err}` confirming agents never produced findings on either real or fixture runs.

## Script trace — three lines that mask the failure

### Line 137 — silent coercion

```bash
REPO_PRS=$(get_merged_prs "$REPO" 2>/dev/null || echo "[]")
```

When `gh pr list` hits the GitHub GraphQL rate limit (HTTP 200 with `{"message":"API rate limit already exceeded for user ID 13840161"}`), `get_merged_prs` exits non-zero and the `|| echo "[]"` substitutes an empty array. The script has no way to tell "no PRs merged" from "couldn't even ask".

### Lines 112-114 — `get_merged_prs` body

```bash
gh pr list --repo "$repo" --state merged --limit 100 --json number,title,url,mergedAt | \
    jq --arg since "$since_date" --arg repo "$repo" '[.[] | select(.mergedAt >= $since) | . + {repo: $repo}]'
```

When `gh pr list` writes the GraphQL error string to stdout (because it's a HTTP-200-wrapped error), `jq` fails parsing the string-as-JSON, returns nothing, and exits non-zero. The downstream `|| echo "[]"` swallows the whole failure.

### Lines 405-416 — `FAILURE_WARNING` gated only on agent count

```bash
if [ "${ALL_AGENTS_FAILED:-0}" -eq 1 ]; then FAILURE_WARNING=...rate-limit-banner...
elif [ "${AGENT_FAILURES:-0}" -gt 0 ]; then FAILURE_WARNING=...partial-fail...
fi
```

But if PR discovery failed for every repo, the agent loop is skipped entirely (`TOTAL_PRS=0`, `AGENT_PIDS=()`), `AGENT_FAILURES` stays 0, and **no failure warning is emitted**. The Slack post reads as a clean sweep.

## Identity verification

`gh api user --jq .id` returned `13840161` — exactly the user ID in the rate-limit message. The active `gh` account is `jleechan2015`. This is the script's own credentials hitting the rate limit, not a transient network blip.

## Real PRs the bot failed to review on its 16:40 run

Per fresh `gh pr list --state merged --search "merged:>=2026-07-20"` (run after the rate-limit window passed):

- **$GITHUB_REPOSITORY**: #8521, #8485, #8486, #8483, #8467, #8461, #8446 (7 PRs)
- **jleechanorg/ai_universe**: #1004 (feat(api) conversation sharing) (1 PR)
- **jleechanorg/jleechanclaw**: 0
- **jleechanorg/beads**: 0

Total: 8 PRs unreviewed.

## Durable-fix recipe

Replace the silent-`[]` coercion with a typed status and require the report to distinguish "no merged PRs" from "couldn't discover".

```bash
get_merged_prs() {
    local repo="$1"
    local since_date=...
    local out
    if ! out=$(gh pr list --repo "$repo" --state merged --limit 100 \
               --json number,title,url,mergedAt 2>&1); then
        printf 'ERROR\t%s\t%s\n' "$repo" "$out" >&2
        return 1   # do not silently coerce
    fi
    printf '%s' "$out" | jq --arg since "$since_date" --arg repo "$repo" \
        '[.[] | select(.mergedAt >= $since) | . + {repo: $repo}]'
}
```

Then in the dispatch loop, capture per-repo discovery status and emit a non-empty `PR Discovery Failure` block when any repo failed to query. The Slack post template should carry that block before "Results", not only when `ACTUAL_BUGS=0` AND agents also failed.

A second durable fix: add a `pytest`/`bats` test that injects a mock `gh` returning the rate-limit error string and asserts the report includes a `PR Discovery Failure` section. This pins the contract for future refactors.

A third fix: Bucket B also needs to be addressed — `configure_review_cli()` failure should set `AGENT_FAILURES=${#AGENTS[@]}` so the warning gate fires. Currently the preflight short-circuit leaves `AGENT_FAILURES=0` and the warning never fires.

## Slack post verification

The diagnostic reply landed at:
- channel: `C09GRLXF9GR` (operator direct channel)
- thread_ts: `1784763610.749029` (the bug-hunt report thread)
- ts: `1784763838.339309`
- identity: XOX-P user token (`SLACK_USER_TOKEN` from `~/.profile`) — posted as `$USER`, not hermes bot. Per `slack-cross-workspace-fallback-xoxp` + `slack-reply-inherit-thread-ts`, this is the canonical fallback when MCP Slack is unavailable.

## Cross-link

- Full durable-fix write-up at `$HOME/.hermes/var/bug-hunt-rate-limit-misreport-20260722.md`
- Script under diagnosis: `~/.hermes/scripts/bug-hunt-daily.sh`
- Skill that captured this analysis: `scripted-multi-agent-review-cron-failure-diagnosis` (this skill, v1.0.0)
