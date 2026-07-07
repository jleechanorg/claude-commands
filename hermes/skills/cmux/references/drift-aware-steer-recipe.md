# Drift-Aware Steer Recipe — "Worker Is Already On It (Or Close)"

**When this applies:** User gives a directive ("make X happen", "fix Y", "post Z
to Slack"). Before re-issuing the task, **verify whether the worker is already
implementing it**. If they are, this is the recipe. If they aren't, just spawn
the work normally — the verification-first steer rule from the main cmux skill
(SKILL.md → "Should I steer now or wait?") still applies, but the dual-channel
short-pointer pattern is the key efficiency gain.

**Verified end-to-end on 2026-06-24** — drove the daily-GCP-slack-alerts work
through `workspace:70 "daily jobs + deploy"` (surface:132) without re-issuing
the task that the worker was already mid-flight on. Saved ~30 min of duplicate
work.

## The 3-step verification

```bash
export CMUX_SOCKET_PATH=/private/tmp/cmux-debug-may-18.sock

# Step 1: Find the relevant workspace by title substring (NOT bare integer)
cmux list-workspaces --id-format both
# Pick the one whose title matches the user's directive keywords
# E.g. user says "daily jobs" → look for workspace:70 "daily jobs + deploy"

# Step 2: Verify focus + identify the focused surface
cmux select-workspace --workspace workspace:70
cmux identify
# Captures: socket_path, focused surface_ref, pane_ref

# Step 3: Read the worker's recent output
cmux read-screen --workspace workspace:70 --surface surface:132 \
  --scrollback --lines 100
# Look for: PR/branch names, recent task description, output that
# paraphrases the user's directive. If the worker is already on it, you
# have alignment, not a new task.
```

**If the worker is already implementing the directive** (branch name matches,
PR body cites the user's exact words, recent output aligns with the request):
**proceed to the dual-channel steer below**. **Do NOT** re-issue the task.

**If the worker is on something different**: just spawn new work normally.
This recipe is for the *already-on-it* case.

## The drift-detection technique (PR body vs code grep)

When the worker is already implementing the directive but the PR body cites
user-directive text, the **PR body is the spec** and the **code is the bug**.
Grep the PR's changed files for the user-mentioned identifiers vs what the
code actually hardcodes.

**Concrete example (2026-06-24):**

- User said: *"tag `<@U09GH5BR3QU>` to investigate"* (verified user ID via
  `users_search` → returns their real Slack user ID).
- PR #7904 body paraphrased: *"tag the investigator"* — *ambiguous*, not
  literal.
- Worker code at `testing_mcp/infra/send_report_email.py:24`:
  `DEFAULT_INVESTIGATOR_USER_ID = "U0AEZC7RX1Q"` — that's the **Hermes bot**
  user ID, NOT Jeffrey. Drift.
- Same drift in `scripts/cost_report_lib.py:1558`.

```bash
# 1. Resolve the user's real Slack user ID (NOT from PR body or memory)
mcp__slack.users_search --query "<username>" --limit 1
# Returns: user ID + display name + email + DM channel ID

# 2. List PR files + show diffs
gh pr view <N> --repo <org>/<repo> --json files,title
# Or via REST (if GraphQL is rate-limited — see env-preferences.mdc):
gh api repos/<org>/<repo>/pulls/<N>/files

# 3. Grep for ALL user IDs that appear in the PR
cd /path/to/worktree  # actual worker worktree, not main checkout
grep -nE "U[0-9A-Z]{8,}" <changed files>

# 4. Compare against user's actual user ID from step 1
# If they don't match → drift → flag it
```

**Why PR body matters:** PR bodies paraphrase the operator directive because
the worker cites the directive as the source. The body gives you the *intent*
text to grep for. The code gives you the *implementation*. If they diverge,
the code is wrong.

## The dual-channel steer pattern (PR comment + cmux send)

Once you've detected the drift, **don't just send a long cmux message**. Two
reasons:

1. **Long cmux pastes trigger idle-prompt autocompleter contamination** (see
   SKILL.md "Idle-agent prompt contamination"). The 2026-06-23 /advisor
   incident showed the autocompleter appending garbage at 816 chars.
2. **The PR comment is the audit trail** — it lands in the PR review history
   and is readable to anyone (humans, other agents, future-you) without
   needing cmux access. The cmux steer is for the *current* worker only.

**The pattern: PR comment has full detail, cmux send is a short pointer.**

```bash
# 1. Write the full detail to a file (so it's not lost in shell quoting)
cat > /tmp/steer-<PR>-drift.md <<'EOF'
# PR #N — drift to fix before merge

## Drift: <one-line summary>

PR body cites: `<operator-directive-text>`
But the code has: `<actual-implementation>` in `<file>:<line>`.

### Fix
<step-by-step fix instructions>

### Verification
<how to verify the fix lands — test updates, etc.>
EOF

# 2. Post the PR comment via REST (REST and GraphQL are SEPARATE quota
# buckets per env-preferences.mdc; if gh pr comment is rate-limited, fall
# back to gh api issues/N/comments).
gh api repos/<org>/<repo>/issues/<N>/comments \
  -f body="$(cat /tmp/steer-<PR>-drift.md)"
# OR if GraphQL is healthy:
gh pr comment <N> --repo <org>/<repo> --body-file /tmp/steer-<PR>-drift.md

# 3. Send the SHORT cmux steer (≤ 2 lines, pointer to PR comment)
cmux send --workspace workspace:N --surface surface:M \
  "Drift to fix on #N before merge — see my PR comment: <one-line summary>. <specific action>. Do NOT merge <PR> — wait for MERGE APPROVED. Report status here when fix is committed."

cmux send-key --workspace workspace:N --surface surface:M enter

# 4. Wait, then verify worker picked it up
sleep 5
cmux read-screen --workspace workspace:N --surface surface:M --scrollback --lines 20
# Should see a churning label like "✻ Fixing drift on PR #N… (Xs)"
```

**Why the cmux send is short and points to the PR comment:**
- Worker reads its own PR review context on next refresh — gets full detail
- Idle-prompt autocompleter is less likely to fire on short pastes
- Audit trail lives in the PR, not in cmux scrollback

**The full PR comment body stays ~600-1800 chars** — long enough for fix
details, short enough to not overwhelm. Save it to a file, then `-f body="$(cat ...)"`.

## Guardrails to embed in the steer

Always include these in the cmux send, verbatim or paraphrased:

- **Do NOT merge `<PR>`** — wait for explicit `MERGE APPROVED` (case-insensitive)
  in the Slack thread. Per memory rule + recent merge-guard skill.
- **Do NOT fake-approve CR / resolve threads** — leave CodeRabbit/Bugbot
  reviews alone for human review.
- **Report status in-thread** — when the fix is committed, post a brief note
  in the originating Slack thread so the user knows it landed.

## Companion-repo work (separate PR)

If the directive spans multiple repos (e.g., your-project.com + jleechanclaw),
do NOT try to fit it into one PR. Per memory rule: **"No parallel PRs"** means
*no parallel branches in the same repo* — separate repos are fine and expected.

Tell the worker:
- "Fix the drift in PR #N (this repo) + open a SEPARATE PR in `<other-repo>`"
- Give it the exact file path in the other repo (`scripts/spend-alert-daily.sh`,
  etc.) so it doesn't have to spelunk.
- Don't make it do both in one branch — the deploy pipelines are separate.

## Worked example (2026-06-24, daily GCP slack alerts)

```bash
# Step 1: Found workspace:70 "daily jobs + deploy"
# Step 2: Identified surface:132 (pane:114) focused on terminal
# Step 3: Read 100 lines scrollback → saw worker driving PR #7904 to 7-green,
#         branch feat/slack-alerts-daily-jobs, PR body citing "tag U09GH5BR3QU"

# Step 4: Drift detection
gh pr view 7904 --repo $GITHUB_REPOSITORY --json body
# Body says: "tag U09GH5BR3QU to investigate"
mcp__slack.users_search --query "$USER"
# Returns: U09GH5BR3QU = $USER (the user)
cd /path/to/feat+restore-rag-shadow-mode-worktree
grep -nE "U[0-9A-Z]{8,}" scripts/cost_report_lib.py \
  testing_mcp/infra/send_report_email.py
# Returns: U0AEZC7RX1Q (Hermes bot, NOT Jeffrey) — DRIFT

# Step 5: Dual-channel steer
cat > /tmp/steer-7904-drift.md <<'EOF'
[...full drift detail + fix instructions + companion jleechanclaw PR note...]
EOF

# POST comment via REST (GraphQL was rate-limited on GraphQL bucket)
gh api repos/$GITHUB_REPOSITORY/issues/7904/comments \
  -f body="$(cat /tmp/steer-7904-drift.md)"
# → URL: https://github.com/$GITHUB_REPOSITORY/pull/7904#issuecomment-4791354430

# SHORT cmux send (1 sentence, pointer)
cmux send --workspace workspace:70 --surface surface:132 \
  "Drift to fix on #7904 before merge — see my PR comment: tag default is U0AEZC7RX1Q (Hermes bot) in both send_report_email.py:24 and cost_report_lib.py:1558, but directive says U09GH5BR3QU. Swap the defaults, update the unit tests, and also open a separate PR in jleechanclaw to port the same pattern into spend-alert-daily.sh (wrong channel + no tag today). Do NOT merge #7904 — wait for MERGE APPROVED. Report status here when both PRs have the fix."

cmux send-key --workspace workspace:70 --surface surface:132 enter

# Step 6: Verify worker absorbed it
sleep 10
cmux read-screen --workspace workspace:70 --surface surface:132 --scrollback --lines 30
# Saw: "✻ Fixing drift on PR #7904… (Xs · ↓ 5.1k tokens)"
# Task list updated: "◼ Drift fix on PR #7904: U0AEZC7RX1Q → U09GH5BR3QU"
```

Outcome: Worker fixed the drift on PR #7904, opened the companion jleechanclaw
PR, posted status back to the Slack thread. No parallel PRs in the same repo,
no duplicate work, no bot-tag-instead-of-human bug shipped to prod.

## When NOT to use this pattern

- Worker is **not** on the directive → just spawn fresh work, don't force-fit
  the dual-channel pattern
- Directive is a one-line `cp` / config change → don't need a PR comment
- Worker is **mid-Edit on a different file** (per cmux In-Flight Worker Rule)
  → wait for an empty `❯` prompt with no churn label before sending
- You're **not sure** if worker is on it → still send the verification-first
  steer (no PR comment), let the worker confirm scope before you write a
  ~1000-char PR comment that might be on the wrong PR

## Pitfalls learned

- **Always `cmux select-workspace --workspace workspace:N` with the ref form,
  NOT the bare integer.** Bare `5` is an index, silently misroutes. See
  `references/workspace-routing-trap.md`.
- **REST and GraphQL buckets drain independently.** If `gh pr comment` fails
  with "API rate limit already exceeded", try `gh api repos/.../issues/N/comments`
  via REST — that's the other bucket. Don't assume both are exhausted.
- **`users_search` is the source of truth for Slack user IDs.** Don't trust
  memory, don't trust PR bodies, don't grep for IDs from old logs. Always
  resolve via the live API at steer time.
- **Don't trust worker's progress label alone.** A `✻ Fixing drift…` label
  can sit for 10+ min with no actual code change. Read 30-50 lines of
  scrollback periodically to confirm it's still working, not stuck.