---
name: agento_report
description: Generate a full agento PR status report — 6-point green checks per PR, display inline, and post to Slack #ai-slack-test.
type: skill
---

## Purpose

Produce a comprehensive status report for all PRs agento is handling in the `jleechanorg/jleechanclaw` repo. Display the report inline in the conversation AND post a summary to Slack `#ai-slack-test`.

---

## Execution Steps

### Step 1 — Collect open PRs

Use the list endpoint only for number, branch, and title (the list endpoint does NOT return `mergeable`/`mergeable_state`):

```bash
gh api "repos/jleechanorg/jleechanclaw/pulls?state=open&per_page=30&sort=updated" \
  | jq -r '.[] | "\(.number)\t\(.head.ref)\t\(.title[:60])"'
```

Also collect recently merged (last 12h):
```bash
gh api "repos/jleechanorg/jleechanclaw/pulls?state=closed&per_page=15&sort=updated" \
  | jq -r '.[] | select(.merged_at != null) | "MERGED\t\(.number)\t\(.head.ref)\t\(.title[:60])"'
```
Filter merged ones to last 12h by comparing `.merged_at` timestamp to current time.

### Step 2 — Per-PR data fetch

For each open PR number NUM, fetch mergeability, CI, and reviews in one batch:

```bash
# Mergeability + CI status + draft state
gh pr view NUM --repo jleechanorg/jleechanclaw \
  --json number,mergeable,mergeStateStatus,statusCheckRollup,isDraft \
  | jq '{mergeable, mergeStateStatus, isDraft, checks: [.statusCheckRollup[] | {name, status, conclusion}]}'

# Reviews
gh api "repos/jleechanorg/jleechanclaw/pulls/NUM/reviews" \
  | jq '[.[] | select(.user.login == "coderabbitai[bot]")] | last | {state, body_len: (.body | length)}'
gh api "repos/jleechanorg/jleechanclaw/pulls/NUM/reviews" \
  | jq '[.[] | select(.user.login == "cursor[bot]")] | last | {state}'

# Evidence PASS comment check
gh api "repos/jleechanorg/jleechanclaw/issues/NUM/comments" \
  | jq -r '[.[] | .body | select(contains("**PASS** — evidence review: agent self-reviewed"))] | length'
```

### Step 3 — 6-point green check per open PR

Apply all 6 conditions using the data from Step 2:

| # | Condition | Pass criteria |
|---|-----------|---------------|
| 1 | Mergeable | `mergeable == "MERGEABLE"` (GraphQL string; REST returns boolean — REST: `mergeable == true`) |
| 2 | No conflict | `mergeStateStatus` is not `DIRTY` (dirty = merge conflict) |
| 3 | CI passing | All `statusCheckRollup` checks: conclusion is `SUCCESS`, `NEUTRAL`, or `SKIPPED` — no `FAILURE`. State `UNSTABLE` → CI_FAILED (not CONFLICT) |
| 4 | CodeRabbit APPROVED | Last CR review: `state == APPROVED` AND body length > 0 |
| 5 | Bugbot not blocking | Last `cursor[bot]` review state is not `CHANGES_REQUESTED` |
| 6 | Evidence PASS | A comment containing the exact string `**PASS** — evidence review: agent self-reviewed ✅, CR reviewed ✅, codex passed ✅` exists (bare `**PASS**` is insufficient per CLAUDE.md) |

**Status label** (pick worst failing condition):
- `GREEN` — all 6 pass
- `CONFLICT` — condition 1 or 2 fails (`mergeable == false` or `mergeStateStatus == DIRTY`)
- `CI_FAILED` — condition 3 fails (any check has `FAILURE` conclusion, or `mergeStateStatus == UNSTABLE`)
- `CI_PENDING` — CI checks still `IN_PROGRESS`
- `NO_CR` — condition 4 fails (CR hasn't APPROVED or approved with empty body)
- `BUGBOT_BLOCKING` — condition 5 fails
- `NO_EVIDENCE` — condition 6 fails (skip this check if the PR has no evidence bundle)
- `COMMENTS` — unresolved Major/Critical comments from any reviewer

### Step 4 — Check AO sessions (optional, graceful if `ao` not in PATH)

```bash
ao status 2>/dev/null | head -40 || echo "(ao not available)"
```

Note which sessions have PR-numbered branches and cross-reference with the PR list.

### Step 5 — Format and display the report inline

Display a formatted report in the conversation:

```
## Agento Status Report — YYYY-MM-DD HH:MM

### Summary
- Open PRs tracked: N (jleechanorg/jleechanclaw)
- GREEN (ready to merge): N
- Not green: N
- Merged (last 12h): N

### Open PRs

| PR | Branch | Status | Blockers |
|----|--------|--------|----------|
| #123 [title] | branch-name | ✅ GREEN | — |
| #124 [title] | branch-name | ⚠️ NO_CR | CodeRabbit not APPROVED |
| #125 [title] | branch-name | ❌ CI_FAILED | CI check "pytest" FAILURE |

### Merged (last 12h)
- #120 branch-foo — merged ✅

### AO Sessions
(paste ao status output or "(ao not available)")
```

Link each PR number to its GitHub URL: `https://github.com/jleechanorg/jleechanclaw/pull/NUM`

### Step 6 — Post Slack summary via MCP

Post to `#ai-slack-test` (channel ID: `C0AKALZ4CKW`) using the Slack MCP tool:

```
mcp__slack__conversations_add_message(
  channel_id="C0AKALZ4CKW",
  text="*Agento Status Report — YYYY-MM-DD HH:MM*\n\n✅ GREEN: N PRs\n⚠️ Not green: N PRs\n🔀 Merged (12h): N PRs\n\n<details per PR>\n\nFull report in Claude conversation."
)
```

Keep the Slack message concise (under 40 lines). Use:
- `✅` for GREEN
- `⚠️` for not-green with the status label
- `🔀` for merged
- Include PR URLs as `<URL|#NUM title>` for Slack hyperlinks

---

## Notes

- Scope: `jleechanorg/jleechanclaw` only (not all jleechanorg repos).
- The list endpoint (`pulls?state=open`) does NOT return `mergeable`/`mergeable_state` — always use `gh pr view NUM --json mergeable,mergeStateStatus` per-PR for those fields.
- `mergeable` from `gh pr view --json` (GraphQL) is a **string**: "MERGEABLE", "CONFLICTING", or "UNKNOWN" — compare with `== "MERGEABLE"`, not `== true`. The REST endpoint (`gh api .../pulls/NUM`) returns boolean true/false/null.
- `mergeStateStatus == UNSTABLE` means CI is failing, not a merge conflict — maps to `CI_FAILED`.
- If `ao status` is unavailable, skip it gracefully — don't fail the report.
- Always display the inline report FIRST, then post Slack.
- The Slack post uses MCP (`mcp__slack__conversations_add_message`), NOT curl.
- Target channel: `#ai-slack-test` (`C0AKALZ4CKW`). The bot is not in `#all-$USER-ai` (C09GRLXF9GR).
- Evidence condition 6 is skipped if the PR clearly has no evidence bundle.
