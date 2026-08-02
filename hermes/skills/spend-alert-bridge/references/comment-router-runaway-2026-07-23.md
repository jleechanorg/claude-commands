# Comment-router runaway — 2026-07-23 incident recipe

> **2026-07-23 update:** this reference was written when the 5,566 `comment-router.yml`
> runs in 32h looked like the root cause. **It is the SYMPTOM, not the cause.**
> The actual source of the 5,566 comments was the **dark-factory daemon** posting
> the same `🤖 [dark-factory] Escalation required` comment to 3 PRs every ~1h as
> part of an `adoption_branch_collision` feedback loop. See **Mode A.2** in
> `SKILL.md` for the dark-factory-specific fix, and bead $USER-rouf / PR
> jleechanorg/dark-factory#470 for the actual fix shipped. The recipe below
> remains useful for the **diagnosis** (finding the runaway workflow), but the
> **fix** lives in the upstream automation that posts the comments, not in the
> comment-router workflow itself.

## What happened

At 08:43 PT on 2026-07-23, `spend-alert-daily.sh` fired a Spend Alert:
- GitHub Actions daily Δ **$61.114536281 > $10** (vs typical $15/d)
- GitHub Actions 7d sum **$138.951375354 > $70**
- MTD $419.95

User asked to "investigate" via Slack reply.

## Root cause

**`$GITHUB_REPOSITORY` `.github/workflows/comment-router.yml`** was firing
**5,566 times in 32h** on `issue_comment` events. All runs were `conclusion=skipped`
because the `if:` guard rejected non-prefix comments (`/smoke /auth-test /dice /levelup`)
before the runner was allocated. But the workflow_run event was still registered for
every single comment.

The script was supposed to be a **fix** (PR #8354–#8355, header comment quoted in
the file) for a prior 6,000-skipped-runs/48h problem. It consolidated 4 separate
issue_comment workflows into one, but the trigger volume didn't drop — the
`on: issue_comment: types: [created]` trigger still fires for every comment on every
issue and PR.

**What we discovered on deeper investigation:** the 5,566 `issue_comment` events
were NOT user-typed `/smoke /auth-test /dice /levelup` commands. They were
5,334 `🤖 [dark-factory] Escalation required: refusing factory PR adoption`
comments from the dark-factory daemon (verified via
`repos/<repo>/issues/comments?since=...`), concentrated on 3 PRs:
- `your-project.com#8428` — 1,791 dark-factory comments
- `your-project.com#8420` — 1,773 comments
- `your-project.com#8421` — 1,770 comments

The comment-router's job-level `if:` correctly skipped all 5,334 of these, but
each one still created a workflow_run event. The dark-factory daemon fix in
`jleechanorg/dark-factory` PR #470 (re-key dedup on branch + move dedup check
before `comment_external`) is what actually stops the loop.

## Why the bridge looked fine (because it was)

- `spend-alert-daily.sh` log: clean run at 08:43:26 PT — no `set -u` crash
- Alert landed in #worldai-alerts (C0BCVG4F560) at ts 1784821406.165559
- MCP Agent Mail relay also delivered
- `conversations.info` confirms `is_member=true` for the bot identity

The first 30 seconds should confirm the bridge is fine, then pivot to the cost
driver. Don't waste a turn fixing a non-broken bridge.

## Diagnosis recipe (replay any time)

```bash
# 1. Confirm the script ran and the alert posted
tail -10 $HOME/.hermes/logs/spend-alert-daily.log
jq . $HOME/.hermes/state/spend-alert-state.json

# 2. Confirm the alert landed in #worldai-alerts
TOK=$(bash -c 'source ~/.bashrc; echo $HERMES_SLACK_BOT_TOKEN')
curl -fsS -H "Authorization: Bearer $TOK" \
  "https://slack.com/api/conversations.history?channel=C0BCVG4F560&limit=5" \
  | jq '.messages[] | {ts, user, text: .text[0:120]}'

# 3. Identify the cost-driver repo from the billing API
gh api "orgs/jleechanorg/settings/billing/usage" --paginate \
  | jq '[.usageItems[]? | select(.product == "actions") | select(.date == "2026-07-01T00:00:00Z")] | sort_by(-.netAmount) | .[] | {sku, repo: .repositoryName, netAmount, quantity, unitType}'

# 4. For the cost-driver repo, find the runaway workflow
REPO="$GITHUB_REPOSITORY"
for wf in $(gh api "repos/$REPO/actions/workflows" | jq -r '.workflows[].path'); do
  count=$(gh api "repos/$REPO/actions/workflows/$wf/runs?per_page=1&created=>$(date -u -v-32H '+%Y-%m-%dT%H:%M:%SZ')" | jq '.total_count // 0')
  [ "$count" -gt 100 ] && echo "$count  $wf"
done | sort -rn | head -10

# 5. Confirm the runaway is all 'skipped' (zero billable minutes but max event noise)
gh api "repos/$REPO/actions/runs?per_page=100&event=issue_comment&created=>$(date -u -v-32H '+%Y-%m-%dT%H:%M:%SZ')" \
  | jq '{total_count, conclusion_dist: [.workflow_runs[].conclusion] | group_by(.) | map({c: .[0], n: length})}'

# 6. KEY STEP — pull the actual comment BODIES, not just the workflow runs
# This is what reveals the comment-router is a victim, not the cause.
gh api "repos/$REPO/issues/comments?per_page=100&since=$(date -u -v-32H '+%Y-%m-%dT%H:%M:%SZ')&direction=desc&sort=updated" \
  | jq 'group_by(.user.login) | map({user: .[0].user.login, n: length, sample: (.[0].body // "")[0:120]}) | sort_by(-.n) | .[:5]'
```

## Why `run_duration_ms` is misleading

For `conclusion=skipped` runs, GH returns `null` or `0` for `run_duration_ms`, even
though the runner was likely allocated for a few seconds before the `if:` guard
rejected the job. Use `updated_at - created_at` to compute real wall-clock time:

```python
from datetime import datetime
def parse_dt(s): return datetime.fromisoformat(s.replace('Z', '+00:00'))
ms = (parse_dt(run['updated_at']) - parse_dt(run['created_at'])).total_seconds() * 1000
```

For 100 PR Comment Router runs on 2026-07-23, total created→updated was ~3.9 min
(average ~2.3 sec per run). That's 5,566 runs × 2.3 sec ≈ 213 min, which at the
Linux rate would be ~$1.28. So the **actual burn from this workflow is tiny**;
the $61 is almost certainly GH's billing API finalizing a previous-day batch.

## Why `gh_delta` is misleading

`gh_delta` in `state.json` is computed as `MTD(now) - MTD(yesterday_snapshot)`.
GH's billing API returns monthly buckets — `date == "2026-07-01T00:00:00Z"` is
the entire month, not a day. The script can't actually compute "today's spend";
it can only compute "MTD movement in the last 24h." That's a laggy, batchy
metric. When GH's billing pipeline finalizes yesterday's runs overnight,
this morning's delta will spike without any real new spend happening.

## Recommended fixes (downstream + upstream)

**Downstream (`comment-router.yml` in $GITHUB_REPOSITORY) — defense in depth:**

```yaml
on:
  issue_comment:
    types: [created]

# Add workflow-level guard so non-trusted authors never even create a run
concurrency:
  group: comment-router-${{ github.event.comment.id }}
  cancel-in-progress: false

jobs:
  route:
    if: |
      github.event.issue.pull_request != null &&
      contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.comment.author_association) &&
      (
        startsWith(github.event.comment.body, '/smoke') ||
        startsWith(github.event.comment.body, '/auth-test') ||
        startsWith(github.event.comment.body, '/dice') ||
        startsWith(github.event.comment.body, '/levelup')
      )
    # (the job-level if: already does the prefix check; just hoist the author_association check up)
```

**Note:** as of 2026-07-23, `on.issue_comment` in GH Actions has NO body-filter
mechanism (verified — only `types:` is supported in the trigger). The
`author_association` hoist is the only workflow-level filter available.
For the 5,566 dark-factory comments (all `author_association=MEMBER`), this
filter would still let them through. **The downstream hardening is a no-op
against the actual dark-factory source** — only the upstream fix in
`jleechanorg/dark-factory` PR #470 stops the spam.

**Upstream (`dark-factory/daemon/src/tick.rs`) — the actual fix (shipped in PR #470):**

Move `escalation_dedup_should_emit` BEFORE `comment_external` AND re-key dedup on
`adopted.head_ref_name` (the stable branch) instead of `adopted.bead_id`
(fresh every slow tick). See jleechanorg/dark-factory PR #470 for the full diff
+ 4 unit tests.

**For the script (`spend-alert-daily.sh`):**

The `gh_delta` metric should be augmented with a **secondary signal** that
checks the actual current MTD vs the prior 7-day average MTD at the same
day-of-month. If `gh_delta > 3 × prior_avg`, it's almost certainly billing-API
lag, not a new spike — and the alert should say so explicitly.

## Files involved

- `~/.hermes/scripts/spend-alert-daily.sh` — the alert script
- `~/.hermes/state/spend-alert-state.json` — current state (last 7-day deltas)
- `~/.hermes/logs/spend-alert-daily.log` — script execution log
- `.github/workflows/comment-router.yml` in $GITHUB_REPOSITORY — the downstream consumer (correctly skips, but counts in `runs` API)
- `~/projects/dark-factory/daemon/src/tick.rs:1377-1424` — the actual source of the comment spam (2026-07-23 fix in jleechanorg/dark-factory PR #470)
- `~/.dark-factory/daemon-cxdb.sqlite` — the `escalation_ledger` table that needs the (branch, reason) key, not (bead_id, reason)
- PR jleechanorg/dark-factory#470 — the actual fix shipped
- Bead $USER-rouf — tracks the fix

## Bridge delivery status (verified 2026-07-23)

- `spend-alert-daily.sh` exited 0 at 08:43:26 PT
- Posted to C0BCVG4F560 ts 1784821406.165559
- `conversations.info` returns `is_member: true` for bot identity
- `conversations.history` confirms the alert is the most recent message in channel
- MCP Agent Mail (U0A4G7LDJ4R) also relayed it (this is the path the user sees in session)
- Diagnosis reply posted at ts 1784823702.965909 (in-thread)
- Final fix-confirmation reply posted at ts 1784833858.814169 (in-thread)

## Reference: how the script's `gh_delta` works

```bash
# In spend-alert-daily.sh process_state():
.s.gh_delta = cap($cgh - .gh_mtd)   # $cgh = today's MTD, .gh_mtd = yesterday's MTD
.gh_roll = ((.gh_roll + [.gh_delta]) | .[-7:])   # last 7 deltas
```

The thresholds are env vars:
- `SPEND_ALERT_GH_DAILY_USD` (default $10)
- `SPEND_ALERT_GH_WEEKLY_USD` (default $70)

When `gh_delta > $10` OR `sum(gh_roll) > $70`, the alert fires. The 7-day sum
of $138.95 vs $70 threshold was the trigger today; daily $61 was secondary.
