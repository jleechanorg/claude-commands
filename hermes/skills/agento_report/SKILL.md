---
name: agento_report
version: 1.0.0
aliases:
  - agentor
description: Get a status report of all PRs agento is handling — merged vs not merged, green status breakdown.
trigger: agento_report or agentor
---

# agento_report

Generate a comprehensive report of all PRs agento is currently handling.

## "Green" Definition

A PR is considered **green** when ALL of these are true:
1. All required CI checks pass (no failures)
2. No merge conflicts — `mergeable: "MERGEABLE"` (not CONFLICTING or UNKNOWN)
3. No serious GitHub comments (no unresolved changes-requested or blocking comments)
4. CodeRabbit has posted APPROVE

## Report Sections

### 1. Get all active AO sessions

Run AO status to find all active sessions:

```bash
cd ~/.hermes && ao status --json 2>/dev/null || ao status
```

Extract the list of PRs being worked on from the output.

## Query each PR — JSON shape corrected 2026-07-08

`gh pr list --json repository` is **wrong** — the field is `headRepository`, with subfield `nameWithOwner`. Without `--repo`, gh falls back to the current directory's default repo and `headRepository` comes back blank. **Always pass `--repo OWNER/REPO`** or the JSON shape collapses.

```bash
# Per-repo (use for every fleet repo — do NOT rely on `gh repo view --json defaultRepository`)
gh pr list --author @me --state open --repo $GITHUB_REPOSITORY \
  --json number,title,headRepository,isDraft,createdAt,headRefName,url,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup \
  > /tmp/open_prs.json
```

To get cross-repo totals, iterate over `gh repo list jleechanorg --limit 50 --json nameWithOwner` and run the query for each. A fleet-wide tally only needs: `number`, `isDraft`, `mergeable`, `reviewDecision` — keep these in the JSON shape to make downstream categorization cheap.

### Categorization (added 2026-07-08)

Per-repo PRs split into 6 buckets. The two non-obvious ones:

- **Conflicts** (`mergeable == CONFLICTING` or `UNKNOWN`) — these are *blocking* next-step items, not "in progress"
- **CHANGES_REQUESTED** — separate from conflicts; needs CR-response commit, not just rebase

For the table shape Jeffrey likes (verified across June 26 + July 8 threads), list per-repo counts of {Total, Drafts, Ready, Conflicts, CHANGES_REQUESTED, APPROVED} as a master row, then drill into the draft-set and the conflict-set per repo.

### 3. Skip recently merged PRs

**Skip PRs merged more than 12 hours ago** — they're no longer relevant to "currently handling".

**CRITICAL:** Always check `mergedAt`, not `updatedAt`. A PR may show old `updatedAt` but be recently merged. Exclude only PRs whose `mergedAt` is older than the 12-hour cutoff (i.e., `mergedAt < now - 12 hours`); keep PRs with `mergedAt == null` or `mergedAt` within the last 12 hours.

### 4. Categorize PRs

| Category | Criteria |
|----------|----------|
| **GREEN** | All 4 green criteria met |
| **CI_PENDING** | Some CI checks still running |
| **CI_FAILED** | One or more required CI checks failing |
| **CONFLICT** | mergeable is CONFLICTING or UNKNOWN |
| **COMMENTS** | Unresolved review comments |
| **NO_CR** | CodeRabbit has not approved |

## Output Format

```
## agento PR Report — <timestamp>

### Summary
- Total active PRs: N
- GREEN: N
- Merged (>12h ago, excluded): N
- CI_FAILED: N
- CONFLICT: N
- CI_PENDING: N
- NO_CR: N
- OTHER: N

### GREEN ✅
| PR | Repo | Title | Merged |
|----|------|-------|--------|
...

### Not Green ❌
| PR | Repo | Status | Blocker |
|----|------|--------|---------|
...
```

## Steps

1. Get active AO sessions via `ao status`
2. For each PR, check merge status — skip if merged > 12h ago
3. Check mergeable status, CI, comments, CodeRabbit
4. Categorize and format the report
## Step 5 corrected 2026-07-08 — channel routing

The original skill said "Post report to Slack channel `#ai-slack-test`" — that was the daemon's test channel from 2024-05. The current fleet's home channel is `#ai-general` (`C0AJQ5M0A0Y`), per `~/.hermes/workspace/SOUL.md` `## COMMIT: slack-channel-routing-policy`. Bare `mcp__slack__conversations_add_message` posts there by default unless overridden.

For per-PR babysit reports, post to the **originating thread** instead (not the home channel). For fleet-wide status sweeps like this one, post to `#ai-general` directly.

## Execution

Run the full report generation and post to Slack:

```bash
# Generate report and save to /tmp/agento-report.md
~/.claude/scripts/agento-report.sh

# Post to Slack
source ~/.profile  # loads $AGENTO_CHANNEL
cat /tmp/agento-report.md | while read line; do
  mcp__slack__conversations_add_message --channel_id "$AGENTO_CHANNEL" --text "$line"
done
```
