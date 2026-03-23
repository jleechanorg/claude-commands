---
name: agento_report
description: Generate a full agento PR status report — 6-point green checks per PR, display inline, and post to Slack #all-jleechan-ai.
type: skill
---

## Purpose

Produce a comprehensive status report for all PRs agento is handling across jleechanorg repos. Display the report inline in the conversation AND post a summary to Slack.

---

## Execution Steps

### Step 1 — Collect open PRs

```bash
gh api "repos/jleechanorg/jleechanclaw/pulls?state=open&per_page=30&sort=updated" \
  | jq -r '.[] | "\(.number)\t\(.head.ref)\t\(.mergeable // "null")\t\(.mergeable_state // "null")\t\(.title[:60])"'
```

Also collect recently merged (last 12h):
```bash
gh api "repos/jleechanorg/jleechanclaw/pulls?state=closed&per_page=15&sort=updated" \
  | jq -r '.[] | select(.merged_at != null) | select((now - (.merged_at | fromdateiso8601)) < 43200) | "MERGED\t\(.number)\t\(.head.ref)\t\(.title[:60])"'
```

### Step 2 — 6-point green check per open PR

For each open PR number NUM:

**CI status:**
```bash
gh api "repos/jleechanorg/jleechanclaw/commits/$(gh api repos/jleechanorg/jleechanclaw/pulls/NUM | jq -r .head.sha)/check-runs" \
  | jq -r '.check_runs[] | "\(.name)\t\(.status)\t\(.conclusion // "pending")"'
```

Or simpler — use the PR's `statusCheckRollup` via:
```bash
gh api "repos/jleechanorg/jleechanclaw/pulls/NUM" \
  | jq '{mergeable, mergeable_state, draft}'
gh api "repos/jleechanorg/jleechanclaw/pulls/NUM/reviews" \
  | jq '[.[] | select(.user.login == "coderabbitai[bot]")] | last | {state, body_length: (.body | length)}'
gh api "repos/jleechanorg/jleechanclaw/pulls/NUM/reviews" \
  | jq '[.[] | select(.user.login == "cursor[bot]")] | last | {state}'
```

**6-point verdict per PR:**

| # | Condition | Pass criteria |
|---|-----------|---------------|
| 1 | Mergeable | `mergeable == true` |
| 2 | No conflict | `mergeable_state` not `dirty` or `unstable` |
| 3 | CodeRabbit APPROVED | Last CR review: `state == APPROVED` AND body length > 0 |
| 4 | Bugbot reviewed | At least one `cursor[bot]` review exists |
| 5 | Bugbot not blocking | Last Bugbot state not `CHANGES_REQUESTED` |
| 6 | Evidence PASS | Comment containing `**PASS** — evidence review` exists |

**Status label** (pick worst failing condition):
- `GREEN` — all 6 pass
- `CONFLICT` — conditions 1 or 2 fail
- `CI_FAILED` — CI checks failing
- `CI_PENDING` — CI checks still running
- `NO_CR` — CodeRabbit hasn't APPROVED
- `NO_BUGBOT` — Bugbot hasn't reviewed
- `COMMENTS` — unresolved blocking comments

### Step 3 — Check AO sessions (optional, graceful if `ao` not in PATH)

```bash
ao status 2>/dev/null | head -40 || echo "(ao not available)"
```

Note which sessions have PRs (look for PR numbers in the output) and cross-reference with the PR list.

### Step 4 — Format and display the report inline

Display a formatted report in the conversation:

```
## Agento Status Report — YYYY-MM-DD HH:MM

### Summary
- Open PRs tracked: N
- GREEN (ready to merge): N
- Not green: N
- Merged (last 12h): N

### Open PRs

| PR | Branch | Status | Blockers |
|----|--------|--------|----------|
| #123 [title] | branch-name | ✅ GREEN | — |
| #124 [title] | branch-name | ⚠️ NO_CR | CodeRabbit not APPROVED |
| #125 [title] | branch-name | ❌ CI_FAILED | CI check "pytest" failing |

### Merged (last 12h)
- #120 branch-foo — merged ✅

### AO Sessions
(paste ao status output or "(ao not available)")
```

Link each PR number to its GitHub URL: `https://github.com/jleechanorg/jleechanclaw/pull/NUM`

### Step 5 — Post Slack summary via MCP

Post to `#all-jleechan-ai` (channel ID: `C09GRLXF9GR`) using the Slack MCP tool:

```
mcp__slack__conversations_add_message(
  channel_id="C09GRLXF9GR",
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

- If `ao status` is unavailable, skip it gracefully — don't fail the report.
- Always display the inline report FIRST, then post Slack.
- If GitHub API rate-limited, use `--jq` flags to batch requests.
- The Slack post uses MCP (`mcp__slack__conversations_add_message`), NOT curl.
- Target channel for agento reports: `#ai-slack-test` (`C0AKALZ4CKW`). The bot is not in `#all-jleechan-ai` (C09GRLXF9GR) — if that changes, switch channel_id there.
