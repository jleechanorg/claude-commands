# Subagent 600s timeout recovery (PR #8269, 2026-07-08)

## The pattern

`ao spawn` workers cap at 600s with a soft warning, then hard-timeout. The worker that ran the load-older-top-only fix hit 600s at 83 API calls with the full body of work already on disk. The gateway-side instinct was either "give up, treat as lost" or "re-dispatch and burn another 600s". Both are wrong. **Recover from the worktree.**

## The diagnostic checklist (5 commands, ~3s)

```bash
# 1. Confirm the worktree exists
ls /tmp/wa-<branch-slug> 2>/dev/null && echo "WORKTREE FOUND"

# 2. Confirm the worker actually committed
cd /tmp/wa-<branch-slug> && git fetch origin --prune 2>&1 | tail -2
git log --oneline origin/main..HEAD

# 3. Confirm the diff is what we expected
git show --stat <HEAD-SHA> | head -20

# 4. Find untracked evidence (worker may have died before final commit)
git status --short | head -20

# 5. Check screenshot/evidence file integrity
find repro/evidence -type f -name "*.png" | head -10
file repro/evidence/<bundle>/real_browser_e2e/BEFORE-mobile-390x844-top.png
```

## The recovery recipe (8 commands, ~10s)

```bash
# A. Stage + commit untracked evidence
cd /tmp/wa-<branch-slug>
git config user.email "jleechan2015@users.noreply.github.com"
git config user.name "jleechan2015"
git add repro/evidence/<bundle>/
git commit -m "evidence(<slug>): real-browser before/after screenshots and harness"

# B. Push the branch
git push -u origin <branch> 2>&1 | tail -5

# C. Open the PR with embedded screenshot tables
gh pr create --repo <OWNER>/<REPO> \
  --base main --head <branch> \
  --title "fix(<scope>): <one-line summary>" \
  --body "$(cat <<'PRBODY'
<full body with BEFORE/AFTER markdown image tables>
PRBODY
)"

# D. Verify the PR exists with the right HEAD
gh api repos/<OWNER>/<REPO>/pulls/<N> --jq '{state, head_sha: .head.sha, files: .changed_files, additions}'

# E. Trigger /skeptic
gh pr comment <N> --repo <OWNER>/<REPO> --body '/skeptic'

# F. Upload the BEFORE/AFTER screenshots to the originating Slack thread
# (use evidence-attach-to-slack skill, scripts/upload_batch.py template)
# 6 PNGs uploaded in ~9s in the verified case.

# G. Post the final status summary in the Slack thread
mcp__slack__conversations_add_message(channel_id=..., thread_ts=..., text=...)
```

## Decision matrix — recover vs re-dispatch

| Worker state | Action | Rationale |
|---|---|---|
| Worktree exists + `git log origin/main..HEAD` non-empty + screenshots on disk | **Recover** | Worker was ≥70% done. Don't burn another 600s. |
| Worktree exists + `git log` empty + screenshots on disk | **Recover + manually commit** | Worker created files but never committed. Commit them, then continue. |
| Worktree exists + `git log` empty + no screenshots | **Re-dispatch** with tighter scope | Worker died during early scaffolding; full re-attempt is faster than triage. |
| Worktree does NOT exist | **Re-dispatch** with a tighter brief | Worker died before `git worktree add`; no starting point to recover from. |
| Worktree exists but `git status` shows unrelated dirty files | **Recover + cherry-pick only the relevant commits** | Worker may have pulled in unrelated dirty state from the user's main worktree. |

## What the worker did NOT finish (the synthesis gap)

Workers that hit timeout during a real-server + Playwright + evidence bundle job almost always finish **all the durable side-effects** (commits, evidence files, screenshots) and stall on the **synthesis steps**:

- `git push` of the final branch
- `gh pr create` with body
- Slack post with attachments
- Final status message

The gateway-side synthesis finishes these in 4–6 inline tool calls, no subagent needed.

## Verified case: 2026-07-08, PR #8269

- Worker timed out at 600s / 83 calls
- Worktree `/tmp/wa-load-older-top-only` had: 2 commits, 8 valid 390x844/1280x800 PNGs, 403-line harness, real Firestore campaign seeded
- Recovery: 4 commits → push → `gh pr create` → 6 attachment uploads → 2 status messages
- Total recovery cost: ~12 tool calls from the gateway (vs 83+ for a re-dispatch)
- PR landed at [#8269](https://github.com/$GITHUB_REPOSITORY/pull/8269) with all 6 attachments visible in thread `C0AH3RY3DK6/p1783487114.025319`

## Anti-pattern

Do NOT just re-dispatch with the same brief if the first worker hit timeout. The second worker will hit the same time pressure (real Flask boot + real Firestore seed + 8 Playwright screenshots + 8 DOM assertions takes ~8-12 min, which is exactly the timeout envelope). If the worker's evidence bundle is on disk, finish the synthesis inline — that's the path of least resistance to a green PR.