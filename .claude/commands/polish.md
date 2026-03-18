---
description: /polish - Iterative PR Green Loop (up to N iterations)
type: llm-orchestration
execution_mode: immediate
---

## EXECUTION INSTRUCTIONS FOR CLAUDE

**When /polish is invoked, YOU (Claude) must execute ALL steps below directly.**

**Usage:** `/polish [N] [PR_NUMBER]`
- `N` = max iterations (default: 5)
- `PR_NUMBER` = target PR (default: auto-detect from current branch)

**Goal:** Drive the PR to all 6 green conditions, looping up to N times.

---

### 6 Green Conditions (all must hold to stop)

1. **CI passing** — all statusCheckRollup checks show SUCCESS/NEUTRAL/SKIPPED (no FAILURE)
2. **No merge conflicts** — `mergeable: MERGEABLE`
3. **CodeRabbit APPROVED** — latest CR verdict is APPROVE or LGTM
4. **Cursor Bugbot finished** — conclusion neutral/success, no blocking findings
5. **All inline comments resolved** — Major/Critical from any bot/human are blockers
6. **Evidence review passed** — `/er` returns PASS (skip if no evidence bundle)

---

### Loop Algorithm

```
for iteration in 1..N:
  1. Run /copilot <PR_NUMBER>   # fetch + triage all comments, fix blocking issues
  2. Run /fixpr <PR_NUMBER>     # fix any remaining inline PR blockers
  3. Run /er                    # check evidence bundle (skip if none present)
  4. Evaluate 6 green conditions:
     - gh pr view <PR> --json statusCheckRollup,mergeable,reviewDecision
     - Check CI: no FAILURE conclusions
     - Check mergeable: MERGEABLE
     - Check CodeRabbit: APPROVE/LGTM in latest review
     - Check Bugbot: NEUTRAL/SUCCESS
     - Check inline comments: no unresolved Major/Critical
     - Check evidence: /er PASS or no bundle
  5. If ALL 6 green → STOP, report success
  6. If changes made → commit + push with /pushl
  7. Wait for CI to settle (gh run watch or poll statusCheckRollup)
  8. Continue to next iteration
```

### After Loop Completes

Report final status:
- Which conditions are green ✅
- Which conditions are still red ❌ (with specific blockers)
- What was fixed across iterations
- Whether PR is ready to merge

---

### Step 1: Identify PR and Parse Args

```bash
# Parse N (first numeric arg) and PR_NUMBER (second arg or auto-detect)
gh pr view --json number,title,url,headRefName --jq '{number, title, url, headRefName}'
```

### Step 2: Execute Loop

Run the loop algorithm above up to N times (default 5).

Apply intelligence: if /copilot finds no blocking issues and CI is already green, skip to evaluation immediately rather than making unnecessary changes.

### Step 3: Report

Print a final status table with all 6 conditions and their current state.
