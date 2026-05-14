---
description: Babysit — orchestration loop to monitor PRs, CI, and test evidence generation
type: orchestration
execution_mode: immediate
---

# /babysit

Alias to invoke the babysit orchestration and monitoring loop.

**Usage**: `/babysit [target PR, branch, or test suite]`

## Action

Execute these steps in order:

Read `.claude/skills/babysit/SKILL.md` for the full protocol, 7-gate criteria, and anti-patterns.

**Testing Gap Integration**: If at any point the target tests fail to produce compliant `/es` evidence bundles, immediately load and execute `.claude/commands/testing-gap-close.md` to identify and resolve the failure.

### Step 2: Discover All Open PRs

```bash
gh pr list --state open --json number,title,headRefName,headRefOid,mergeable \
  --jq '.[] | "\(.number)|\(.title)|\(.headRefName)|\(.headRefOid[:12])|\(.mergeable)"'
```

### Step 3: Audit 7-Gate Status for Each PR

For each PR, check all 7 gates (see SKILL.md for exact commands). Categorize:
- **RED** (3+ gates failing): needs code fixes → dispatch copilot-fixpr subagents
- **YELLOW** (1-2 gates failing): needs bot triggers or comment resolution → fix inline
- **GREEN** (6/7 gates): only Skeptic missing → trigger `/smoke` and `/skeptic`

### Step 4: Dispatch Subagents to Fix RED PRs

Use Agent tool with `subagent_type: copilot-fixpr`, one per PR (or group related PRs).
Run in parallel using `run_in_background: true`.

Each agent must:
1. Read the Green Gate log to find the exact failing gate
2. Fix the root cause (code, design doc, evidence, rebase)
3. Push the fix
4. Trigger bot re-reviews (`@coderabbitai all good?`)

### Step 5: Fix YELLOW PRs Inline

- Gate 3: Comment `@coderabbitai all good?` on PR
- Gate 5: Resolve review threads via GitHub API
- Gate 6: Add evidence or N/A justification to PR body
- Gate 4: Bugbot errors → fix code, push

### Step 6: Trigger Skeptic + Smoke on 6/7 GREEN PRs

```bash
# Trigger smoke
gh pr comment <NUM> --body "/smoke"

# Green Gate re-run (if no recent run)
gh workflow run green-gate.yml --ref <branch> -f pr_number=<NUM>
```

### Step 7: Report Final Status

Print a table for ALL open PRs:

```
PR #<N> — <title> — status: <RED|YELLOW|GREEN|7-GREEN>
  Gates: 1=✓ 2=✓ 3=✗ 4=✓ 5=✓ 6=✓ 7=✗
  Action: <what was done or what's pending>
```

### Step 8: Hold Loop — Stay Alive Until All PRs Merge

After Step 7, if any PRs are still open:

**In `/loop` mode** (user ran `/loop /babysit`): call `ScheduleWakeup` so the next iteration fires while the REPL is idle — never during an active conversation.

```python
ScheduleWakeup(
    delaySeconds=180,  # 3 min — within cache window, catches Design Doc bot commits quickly
    prompt="<<autonomous-loop-dynamic>>",
    reason="babysit hold: re-checking stale Skeptic verdicts"
)
```

**In one-shot mode** (user ran just `/babysit`): set up a `CronCreate` job for the same re-check and tell the user it's running. Delete it with `CronDelete` once all PRs merge.

Each wakeup iteration runs only a **lightweight stale-verdict sweep** (see Phase 8 in SKILL.md) — not a full re-audit. Re-dispatch Skeptic only when both are true:
- PR HEAD doesn't match the latest `VERDICT: PASS` SHA, and
- CI is fully settled (`ci_failures == 0` and `ci_pending == 0` from `statusCheckRollup`).

**Exit**: Stop scheduling when no open PRs remain.

## KEY RULES

- **PR Green Loop Protocol**: Never push during active bot review. Batch fixes, push once, freeze.
- **Never dismiss** CR CHANGES_REQUESTED — wait for re-review APPROVED
- **Never merge** — only skeptic-cron merges when all 7 gates pass
- **7-green verification**: Must read Green Gate gate-by-gate log, not just `gh pr checks`
- **Evidence required** for non-docs PRs touching `$PROJECT_ROOT/**`
