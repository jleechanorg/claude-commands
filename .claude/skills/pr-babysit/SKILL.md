---
name: pr-babysit
description: Drive all open PRs to 7-green by fixing CI failures, triggering bot reviews, resolving comments, and running skeptic/smoke gates. Use when the user wants to nurse PRs to merge-readiness.
---

# /babysit — PR Green-Gate Babysitter

## Purpose

Systematically drive all open PRs toward 7-green merge-readiness. For each PR:
1. Audit all 7 gates
2. Fix any blocking failures
3. Trigger missing bot reviews or gates
4. Once 6/7 green, run `/skeptic` and `/smoke`

## 7-Gate Criteria (from skeptic-cron.yml)

| # | Gate | Check |
|---|------|-------|
| 1 | CI green | All GitHub Actions checks pass (no FAILURE conclusions) |
| 2 | No conflicts | `mergeable == "MERGEABLE"` |
| 3 | CR APPROVED | CodeRabbit latest review state == "APPROVED" |
| 4 | Bugbot clean | cursor[bot] zero error-severity comments |
| 5 | Comments resolved | Zero unresolved non-nit inline review comments |
| 6 | Evidence pass | Evidence bundle exists or N/A justified |
| 7 | Skeptic PASS | github-actions[bot] posted VERDICT: PASS |

## Execution Protocol

### Phase 1: Discover All Open PRs

```bash
gh pr list --state open --json number,title,headRefName,headRefOid,mergeable \
  --jq '.[] | "\(.number)|\(.title)|\(.headRefName)|\(.headRefOid[:12])|\(.mergeable)"'
```

### Phase 2: Audit Each PR (7-Gate Check)

For each open PR, check all 7 gates:

```bash
# Gate 1: CI status
gh pr view <NUM> --json statusCheckRollup \
  --jq '[.statusCheckRollup[] | select(.conclusion == "FAILURE")] | length'

# Gate 2: Mergeable
gh pr view <NUM> --json mergeable --jq '.mergeable'

# Gate 3: CodeRabbit review
gh api repos/$GITHUB_REPOSITORY/pulls/<NUM>/reviews \
  --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | last | .state'

# Gate 4: Bugbot errors
gh api repos/$GITHUB_REPOSITORY/pulls/<NUM>/comments \
  --jq '[.[] | select(.user.login=="cursor[bot]" and (.body | test("error";"i")))] | length'

# Gate 5: Unresolved comments
gh api graphql -f query='
  query($owner:String!, $name:String!, $pr:Int!) {
    repository(owner:$owner, name:$name) {
      pullRequest(number:$pr) {
        reviewThreads(first:100) {
          nodes { isResolved }
        }
      }
    }
  }
' -f owner=jleechanorg -f name=your-project.com -F pr=<NUM> \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false)] | length'

# Gate 6: Evidence in PR body
gh pr view <NUM> --json body --jq '.body' | grep -i -E "evidence|gist|video|mp4|N/A"

# Gate 7: Skeptic verdict
gh api repos/$GITHUB_REPOSITORY/issues/<NUM>/comments \
  --jq '[.[] | select(.user.login=="github-actions[bot]" and (.body | test("VERDICT: PASS";"i")))] | length'
```

### Phase 3: Categorize PRs

Group PRs into:
- **RED** (3+ gates failing): needs code fixes
- **YELLOW** (1-2 gates failing): needs bot triggers or comment resolution
- **GREEN** (6/7 gates passing): run `/skeptic` and `/smoke`

### Phase 4: Fix RED PRs

For each RED PR, use subagents (Agent tool, subagent_type: copilot-fixpr) to:
1. Read the Green Gate workflow log to identify the exact failing gate
2. Fix the root cause:
   - **CI test failures**: read test output, fix code, push
   - **Design Doc Gate**: add design doc reference to PR body
   - **Lint/type errors**: fix code, push
3. Dispatch agents in parallel — one per PR or group of related PRs

Common fixes:
- Test assertion mismatch after rebase → rebase onto `origin/main`
- Missing `@coderabbitai` trigger → comment on PR
- Missing evidence → create evidence bundle or add N/A justification
- Stale review threads → resolve via GitHub API

### Phase 5: Fix YELLOW PRs

For each YELLOW PR:
1. **Gate 3 (CR not APPROVED)**: Comment `@coderabbitai all good?`
2. **Gate 5 (unresolved comments)**: Resolve review threads
3. **Gate 6 (no evidence)**: Add evidence or N/A to PR body
4. Do NOT push during active bot review (PR Green Loop Protocol)

### Phase 6: Run Skeptic + Smoke on GREEN PRs

For PRs at 6/7 gates (only Skeptic missing):

```bash
# Trigger Green Gate workflow if no recent run
gh workflow run green-gate.yml --ref <branch> -f pr_number=<NUM>

# Trigger smoke tests via PR comment
gh pr comment <NUM> --body "/smoke"
```

Skeptic-cron runs every 30 min automatically. Once it posts VERDICT: PASS, the PR is 7-green.

### Phase 7: Report Final Status

Print a summary table:

```
PR #<N> — age: <Xh Ym> — status: <red|yellow|green|7-green>
  Gates: 1=✓ 2=✓ 3=✓ 4=✓ 5=✓ 6=✓ 7=✗ (Skeptic pending)
  Action: /smoke triggered, waiting for Skeptic-cron
```

## PR Green Loop Protocol (MANDATORY)

- **Never push during active bot review** — wait for Bugbot COMPLETED, CR posted, Copilot done
- **Batch all fixes** into one commit, not one per finding
- **Push once**, then freeze until all bots finish
- **Never dismiss** CR CHANGES_REQUESTED reviews

## Subagent Dispatch Strategy

- **Independent PRs**: Dispatch one agent per PR in parallel
- **Related PRs** (same feature area): Group under one agent
- **GREEN PRs**: One agent to trigger skeptic/smoke on all

Agent type: `copilot-fixpr` for fixing, `general-purpose` for auditing/triggering

### Phase 8: Hold Loop — Stay Alive Until All PRs Merge

After Phase 7, if any PRs are still open, **do not exit**. Schedule a wakeup to re-check:

```python
# In /loop mode (Claude Code interactive) — fires only when REPL is idle, never interrupts work
ScheduleWakeup(
    delaySeconds=180,   # 3 min — within 5-min cache window, catches Design Doc bot commits
    prompt="<<autonomous-loop-dynamic>>",
    reason="babysit hold: re-checking stale Skeptic verdicts after Design Doc bot commits"
)
```

On each wakeup iteration, run a **lightweight stale-verdict sweep** (not a full audit):

```bash
# Check each open PR for stale Skeptic SHA
for pr in $(gh pr list --repo $GITHUB_REPOSITORY --state open --json number --jq '.[].number'); do
  head=$(gh pr view $pr --repo $GITHUB_REPOSITORY --json headRefOid --jq '.headRefOid[0:8]')
  verdict=$(gh api --paginate repos/$GITHUB_REPOSITORY/issues/${pr}/comments | python3 -c "
import sys,json,re
# gh api --paginate emits one JSON array per page; merge all pages before parsing
raw=sys.stdin.read().strip()
c=json.loads('['+raw[1:-1].replace(']\n[',',')+']') if raw.startswith('[') else json.loads(raw)
b=[x for x in c if x.get('user',{}).get('login')=='github-actions[bot]' and 'VERDICT: PASS' in x.get('body','')]
m=re.search(r'skeptic-head-sha-([a-f0-9]+)',b[-1]['body']) if b else None
print(m.group(1)[:8] if m else 'none')")
  # Also check: don't re-dispatch if CI is still pending/failing (Skeptic will fail at Gate 1)
  ci_failures=$(gh pr view $pr --repo $GITHUB_REPOSITORY --json statusCheckRollup \
    --jq '[.statusCheckRollup[] | select((.conclusion == "FAILURE" or .conclusion == "ERROR" or .conclusion == "TIMED_OUT") and .name != "Green Gate")] | length')
  ci_pending=$(gh pr view $pr --repo $GITHUB_REPOSITORY --json statusCheckRollup \
    --jq '[.statusCheckRollup[] | select(.status == "IN_PROGRESS" or .status == "QUEUED")] | length')
  if [[ "$verdict" != "$head" && "$ci_failures" == "0" && "$ci_pending" == "0" ]]; then
    gh workflow run "Skeptic Self-Verify" --repo $GITHUB_REPOSITORY -f pr_number=$pr
    echo "Re-dispatched Skeptic for #$pr (verdict=$verdict head=$head)"
  elif [[ "$ci_failures" != "0" || "$ci_pending" != "0" ]]; then
    echo "Skipping Skeptic dispatch for #$pr — CI not settled (failures=$ci_failures pending=$ci_pending)"
  fi
done
```

**Exit condition**: Stop scheduling wakeups when `gh pr list --repo $GITHUB_REPOSITORY --state open --json number --jq 'length'` returns `0` (all merged).

**CronCreate alternative** (non-interactive / cron-based sessions):
```python
# Guard: create at most ONE cron job per babysit session. Check CronList first.
jobs = CronList()
babysit_jobs = [j for j in jobs if "babysit" in j.get("prompt", "").lower()]
if not babysit_jobs:
    job_id = CronCreate(
        cron="*/5 * * * *",  # every 5 minutes
        # Sweep-only prompt — do NOT use "/babysit" here (that runs full 7-phase audit).
        # This fires the Phase 8 stale-verdict sweep: compare HEAD SHA to last VERDICT: PASS
        # SHA for each open PR; re-dispatch Skeptic Self-Verify only when stale and CI settled.
        prompt="Run /babysit Phase 8 stale-verdict sweep only: for each open PR in $GITHUB_REPOSITORY, compare HEAD SHA to last VERDICT: PASS SHA; re-dispatch Skeptic Self-Verify if stale and CI settled. Skip full Phase 1-7 audit.",
        recurring=True
    )
```
Use CronCreate only when NOT in an interactive `/loop` session. Delete the job with CronDelete once all PRs merge. The guard above prevents duplicate cron jobs from accumulating across repeated babysit invocations.

**Key rule: never sleep-poll inline.** The wakeup fires while the REPL is idle — it cannot interrupt a user conversation or an in-progress tool call. This is safe to leave running.

## Evidence Monitoring Protocol

When babysitting active testing or evidence generation:

1. **Poll evidence traces**: Continuously verify that the testing framework writes traces to `/tmp/.../iteration_XXX`. Confirm `.jsonl` files are non-empty.
2. **Copy to persistent path**: After iteration completes, copy to `docs/evidence/pr-<number>/` (e.g., `docs/evidence/pr-6851/`).
3. **Testing Gap Close Integration**: If evidence bundles fail to generate (empty `.jsonl` files, missing checksums, server timeout errors, or `EvidenceSignatureGuard` rejections), immediately invoke the `/testing-gap-close` skill to harden the server lifecycle and resolve the failure.
4. **Nudge stale processes**: If a background daemon hangs on testing or evidence compilation, use scoped shutdown: (1) SIGTERM to the test-managed PID file, (2) `lsof -ti :<port> | xargs kill` for the bound port, (3) `kill -- -$(ps -o pgid= -p <pid>)` for the process group. Only fall back to `pkill -9 -f gunicorn` as a last resort when all scoped methods fail.

## Anti-Patterns (BANNED)

- Polling CI status in a sleep loop — wait for bots, then check once
- Pushing while Bugbot/CR is still running
- Resolving review threads to trigger auto-approve
- Declaring "7-green" without Green Gate log verification
- Reporting a PR as "looking good" after checking only mergeable + Skeptic SHA — always run statusCheckRollup check first
- Running `gh pr merge` — only skeptic-cron merges
- Calling `sleep` inline to wait for bots — use `ScheduleWakeup` instead
- Exiting babysit after Phase 7 while PRs are still open — must hold until merged
