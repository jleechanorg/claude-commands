# PR-topology pre-flight for recurring alerts — verified 2026-07-09

## Origin

Slack thread `C0BCVG4F560 / 1783581813.596099` — the daily-level-up-and-dice-test-watcher cron
(`8ccfba727015`, schedule `0 5,17 * * *`) auto-posted a "Daily Level Up Test: FAIL (work=daily-scheduled-2026-07-09, exit=1)"
heartbeat at `2026-07-09T07:23:33Z`. Jeffrey replied with the single word "Investigate."

The natural finish-the-job Phase 2 reflex was: diagnose the alert → draft an AO brief → spawn an
AO worker on a fresh `fix/daily-levelup-2026-07-09` worktree → drive to merge. The PR-topology
pre-flight check found [PR #8290](https://github.com/$GITHUB_REPOSITORY/pull/8290)
already in flight on `feat/daily-level-up-2026-07-08`, head `8cd5f1fb`, 5/7-green (CI pass,
MERGEABLE, CodeRabbit APPROVED, Bugbot clean, threads resolved). Pivoted to reporting the
existing PR state + scheduling a one-time follow-up cron for skeptic verdict. Saved one
worktree, one AO session, one CodeRabbit round, and one merge-conflict window.

## Decision matrix

| Alert recurrence signal | `gh pr list` match | Action |
|---|---|---|
| None (one-off CI failure, no prior history) | 0 matches | Normal diagnose → AO spawn recipe |
| Date-stamped work id (e.g. `daily-scheduled-2026-07-09`) | 1 match on `feat/daily-<date>-<scope>` | Pivot to existing PR — verify, report, schedule follow-up cron |
| Same GCP execution prefix across multiple cron runs (≥2 in 7d) | ≥2 matches on different `feat/daily-<date>-*` branches | Load `dispatch-task` skill, triage canonical fix vs sibling investigations |
| Bot alert references an issue number (e.g. "issue #8290") | 1 match on PR linked to that issue | Pivot to that PR |
| Recurring alert + 0 matches | 0 matches | Either the alert is a new failure class OR a PR was opened in a different repo/worktree; broaden `gh pr list --state all --search "<keywords>"` |

## Verification recipe — confirm the existing PR is the same fix

After finding a candidate PR via branch-name pattern, verify it actually addresses this alert
before pivoting the entire response. Two-step check:

```bash
# 1. Confirm the failing test/source file appears in the PR diff
gh pr view <N> --repo <OWNER>/<REPO> --json files \
  --jq '.files[].path' | grep -E "<failing-test-or-source-file>"

# 2. Confirm the PR body references the alert's failure mode
gh pr view <N> --repo <OWNER>/<REPO> --json body,title \
  --jq '{title, body_preview: (.body | .[0:500])}'
```

Verified case study: alert cited `test_level_up_organic.py` assertion
`rewards_box.level_up_available=true without canonical level-up planning choices`.
PR #8290's `gh pr view --json files` returned
`['$PROJECT_ROOT/rewards_engine.py', '$PROJECT_ROOT/tests/test_bug_rewards_box_atomicity.py',
'testing_mcp/lib/campaign_utils.py', 'testing_mcp/test_stream_parser_tolerance.py']`.
The `$PROJECT_ROOT/rewards_engine.py` change is the canonical fix for the rewards_box assertion
(see PR body: *"Modified the main canonicalize_rewards routine to verify if the turn's
response closes the level-up modal ... explicitly set level_up_available = False"*).
Match confirmed.

## GitHub actor audit (zero-touch check)

If the existing PR has zero `$USER` actor actions (created + pushed by `jleechan2015`
or an AO bot, no human reviews in GitHub, no `MERGE APPROVED` in PR comments), it's
already zero-touch AO-managed. Pivoting is the only correct move — re-spawning would
race the existing AO worker.

```bash
gh api "repos/<OWNER>/<REPO>/issues/<N>/timeline?per_page=100" \
  --jq '.[] | select(.actor.login == "jleechan2015" or .actor.login == "$USER") | {event, actor: .actor.login, ts: .created_at}'
```

If any `$USER` action is on the timeline (besides the PR creator), the PR is NOT
zero-touch-managed and the user may be steering it manually. In that case, post the
investigation result to the user's thread (do NOT auto-pivot), let the user decide
whether to use the existing PR or spawn a new one.

## Companion skills

- **`drive-pr-to-green`** — once you've pivoted to an existing PR, this skill governs driving
  it to merge (worktree at explicit SHA, fix iteration, CI watch, review clear, merge).
- **`one-time-status-cron-after-every-task`** (SOUL.md `## COMMIT`) — when pivoting to an
  existing PR awaiting external verdicts (skeptic, MERGE APPROVED), schedule a one-time
  cron per this commit to fire at +30 min and post a state-check update.
- **`dispatch-task`** — when ≥2 PR matches and you need to triage which is canonical,
  load this skill for the AO worker brief + env -i wrapper + bead-tracked dispatch.
- **`agento` v1.22.0 PR-topology pre-flight** — the underlying rule this extends. The
  agento rule fires on PR-remediation triggers; this pitfall extends to investigation-
  shaped triggers.

## Worked reply shape (verified 2026-07-09)

After PR-topology pre-flight found PR #8290 5/7-green, the Phase 4 reply was:

```
:white_check_mark: PR already exists for this exact failure: <PR URL>

:white_check_mark: 5/7 applicable conditions pass on head <SHA>:
• CI: 31/31 SUCCESS on `gh pr checks`
• Mergeable: MERGEABLE (zero conflicts)
• CodeRabbit: APPROVED (review <id> at <ts>)
• Bugbot: Cursor Bugbot NEUTRAL — usage limit, not error
• Threads: 0 unresolved
• Evidence Gate (6): GREEN precheck passed at <ts>
• Skeptic (7): no fresh verdict on this SHA yet — skeptic-cron.yml will auto-fire within ≤30 min

:lock: Awaiting `MERGE APPROVED` from you — without it, AO workers may not execute
`gh pr merge` for $GITHUB_REPOSITORY. Reply *MERGE APPROVED* and I'll either
land it inline or queue the auto-merge via skeptic-cron when the verdict arrives.

Will not post further unless I see new state (skeptic verdict, MERGE APPROVED, or CI flip).
```

No follow-up question. No "want me to spawn a worker?" No new branch. The work was already
done by the time the alert fired.