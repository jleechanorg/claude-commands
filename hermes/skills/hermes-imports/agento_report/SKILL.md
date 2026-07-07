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

### 2. Query each PR

For each PR, run these checks:

```bash
# Get PR state
gh pr view <PR> --repo <OWNER>/<REPO> --json state,title,mergeable,mergedAt,mergeStateStatus

# Get CI status
gh pr checks <PR> --repo <OWNER>/<REPO> --required

# Get CodeRabbit review
gh pr reviews <PR> --repo <OWNER>/<REPO> | grep -i coderabbit

# Get unresolved comments
gh api repos/<OWNER>/<REPO>/pulls/<PR>/comments --jq '[.[] | select(.user.id != 612194)]'
```

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
5. Post report to Slack channel `#ai-slack-test`

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
