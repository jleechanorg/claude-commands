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

```text
for iteration in 1..N:
  1. Run /copilot <PR_NUMBER>   # fetch + triage all comments, fix blocking issues
  2. Run /fixpr <PR_NUMBER>     # fix any remaining inline PR blockers
  3. Run /er                    # check evidence bundle (skip if none present)
  4. If changes made → commit + push with /pushl
  5. Wait for CI to settle (gh run watch or poll statusCheckRollup)
  6. Evaluate 6 green conditions:
     # Fetch CI status and mergeability
     gh pr view <PR_NUMBER> --json statusCheckRollup,mergeable,mergeStateStatus
     # Use GraphQL to get bot-specific reviews and thread resolution
     gh api graphql -f query='
       query($owner:String!, $name:String!, $pr:Int!) {
         repository(owner:$owner, name:$name) {
           pullRequest(number:$pr) {
             reviews(last:100) { nodes { author { login } state bodyText } }
             reviewThreads(first:100) { nodes { isResolved comments(last:20) { nodes { author { login } body } } } }
           }
         }
       }
     '
     - Check CI: statusCheckRollup shows no FAILURE
     - Check mergeable: MERGEABLE (handle UNKNOWN state)
     - Filter reviews by author.login for "coderabbitai" → verify state is APPROVED/LGTM
     - Filter reviews by author.login for "bugbot" or "cursor[bot]" → verify state is NEUTRAL/SUCCESS
     - Check reviewThreads: verify no unresolved Major/Critical comments
     - Check evidence: /er PASS or no bundle
  7. If ALL 6 green → STOP, report success
  8. Continue to next iteration
```

**Note on CI evaluation timing**: Step 6 evaluates CI AFTER the push (step 5), so each iteration's fix will be reflected in the next iteration's evaluation. With N=1, if fixes are needed, the PR won't report green until a second run.

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
