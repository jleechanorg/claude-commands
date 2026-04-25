---
description: /polish - Iterative PR Green Loop (up to N iterations)
type: llm-orchestration
execution_mode: immediate
---

## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE

**When this command is invoked, YOU (Claude) must execute these steps immediately.**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

**Usage:** `/polish [N] [PR_NUMBER]`
- `N` = max iterations (default: 5)
- `PR_NUMBER` = target PR (default: auto-detect from current branch)

**Goal:** Drive the PR to all 6 green conditions, looping up to N times.

---

### 6 Green Conditions (all must hold to stop)

1. **CI passing** — all statusCheckRollup checks show SUCCESS/NEUTRAL/SKIPPED (no FAILURE, ERROR, TIMED_OUT, CANCELLED, ACTION_REQUIRED). If any check has `status: IN_PROGRESS` → not pass — poll/retry until all are COMPLETED, then verify conclusions.
2. **No merge conflicts** — `mergeable: MERGEABLE` (handle UNKNOWN by retrying/poll)
3. **CodeRabbit APPROVED** — `coderabbitai[bot]` has a passing review state per **skeptic-cron** Gate 3 logic: **any** APPROVED review counts, even if a later CHANGES_REQUESTED exists (DISMISSED doesn't erase older approval). This is intentionally more permissive than `green-gate.yml` which requires the *latest* non-COMMENTED review to be APPROVED. If the latest substantive review is **CHANGES_REQUESTED**, that blocks until addressed.
4. **Cursor Bugbot finished** — prefer **check-run** conclusion on the PR head commit (same as skeptic-cron Gate 4). If Bugbot is absent from `statusCheckRollup` → acceptable (not configured). If present: conclusion `SUCCESS`/`NEUTRAL`/`SKIPPED` → pass. If present with `conclusion: null` and `status: IN_PROGRESS` → poll/retry until complete. Treat `FAILURE`, `ERROR`, `TIMED_OUT`, `CANCELLED`, `ACTION_REQUIRED` as red, consistent with condition 1.
5. **All inline comments resolved** — Major/Critical from any bot/human are blockers
6. **Evidence review passed (fail-closed)** — **No silent skip.** When the PR touches evidence-bearing paths (MCP/UI per repo policy), resolve the canonical evidence bundle path under `/tmp/worldarchitect.ai/.../latest/` **before** `/er`. Pass only when **`/er` returns PASS** *and* automation would pass Gate 6: **`evidence-review-bot` APPROVED on current HEAD** and/or **Evidence Gate / Evidence Review** check-runs succeeded on that HEAD. If evidence is required but missing or stale for the current SHA, treat as **red** until fixed (aligns with skeptic-cron posting an evidence-request comment when Gate 6 fails).

---

### Loop Algorithm

```text
# Derive repo context once before the loop
REPO_FULL="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
OWNER="${REPO_FULL%%/*}"
NAME="${REPO_FULL##*/}"
PR="<PR_NUMBER>"

for iteration in 1..N:
  1. Run /copilot <PR_NUMBER>   # fetch + triage all comments, fix blocking issues
  2. Run /fixpr <PR_NUMBER>     # fix any remaining inline PR blockers
  3. Resolve evidence bundle path when applicable; run /er  # fail-closed — do not skip required evidence
  4. If changes made → commit + push with /pushl
  5. Wait for CI to settle (gh run watch or poll statusCheckRollup)
  6. Evaluate 6 green conditions:
     # Fetch CI status and mergeability
     gh pr view <PR_NUMBER> --json statusCheckRollup,mergeable,mergeStateStatus
     # Use GraphQL to get bot-specific reviews and thread resolution.
     # Paginate reviewThreads: real PRs can exceed 100 threads (see automation/jleechanorg_pr_automation).
     # reviewThreads uses cursor-based pagination: on first call omit cursor entirely (pass no cursor param — not even empty string);
     # read pageInfo { hasNextPage endCursor }; if hasNextPage is true, re-run with -f cursor=<endCursor>,
     # accumulating all nodes until hasNextPage is false. Do NOT pass cursor="" — GitHub GraphQL rejects empty string cursors.
     # If any thread may have >20 comments, page through that thread's comments connection using its pageInfo until all comments are collected.
     # Note: the reviews connection uses last:100 ordered chronologically by submittedAt — sufficient for most PRs; if CR has >100 reviews, accumulate in reverse order. Add pageInfo to all paginated connections for cursor-based navigation.
     gh api graphql \
       -f query='
         query($owner:String!, $name:String!, $pr:Int!, $cursor:String) {
           repository(owner:$owner, name:$name) {
             pullRequest(number:$pr) {
               reviews(last:100) {
                 pageInfo { hasNextPage endCursor }
                 nodes { author { login } state bodyText submittedAt }
               }
               reviewThreads(first:100, after:$cursor) {
                 pageInfo { hasNextPage endCursor }
                 nodes {
                   isResolved
                   comments(last:20) {
                     pageInfo { hasNextPage endCursor }
                     nodes { author { login } body }
                   }
                 }
               }
             }
           }
         }
       ' \
       -f owner="$OWNER" -f name="$NAME" -F pr="$PR"
     - Check CI: statusCheckRollup shows no FAILURE/ERROR/TIMED_OUT/CANCELLED/ACTION_REQUIRED
     - Check mergeable: MERGEABLE (handle UNKNOWN state by polling)
     - Filter reviews by author.login matching "coderabbitai" (GitHub GraphQL may return bot logins with or without the `[bot]` suffix — test both `coderabbitai` and `coderabbitai[bot]`) → sort chronologically using `submittedAt`, find most recent APPROVED. If the most recent CR review is NOT APPROVED, fail. Additionally: if the most recent APPROVED has a more recent CHANGES_REQUESTED or COMMENTED after it, the APPROVED is stale — fail in that case too. Only pass when the latest CR review IS APPROVED and no newer CHANGES_REQUESTED/COMMENTED exists after it.
     - Filter statusCheckRollup by name containing "Bugbot" → if absent from statusCheckRollup entirely → acceptable (Bugbot not configured for this repo). If present with conclusion SUCCESS/NEUTRAL/SKIPPED → pass. If present with conclusion null AND status IN_PROGRESS → poll/retry (not pass). Treat FAILURE, ERROR, TIMED_OUT, CANCELLED, ACTION_REQUIRED as red.
     - Check reviewThreads: verify no unresolved Major/Critical comments
     - Check evidence (fail-closed): /er PASS when a bundle applies; bot APPROVED @ HEAD or evidence checks green on HEAD when automation enforces Gate 6
  7. If ALL 6 green → STOP, report success
  8. Continue to next iteration
```

**Note on CI evaluation timing**: Each iteration pushes (step 4) then waits for CI to settle (step 5), so fixes land before the next iteration's evaluation. With N=1 and fixes needed, CI must complete and re-run before the loop can report green.

---

### Step 1: Identify PR and Parse Args

Use TodoWrite to track progress through each iteration.

```bash
# Parse N (first numeric arg) and PR_NUMBER (second arg or auto-detect)
gh pr view --json number,title,url,headRefName --jq '{number, title, url, headRefName}'
```

---

### Step 2: Execute Loop

Run the loop algorithm above up to N times (default 5).

Apply intelligence: if /copilot finds no blocking issues and CI is already green, skip to evaluation immediately rather than making unnecessary changes.

**IMPORTANT — Uncommitted changes guard**: Before evaluating green conditions (Step 6), verify there are no uncommitted changes with `git status --porcelain` (covers staged, unstaged, AND untracked files). If any output exists, do NOT report the PR as green — commit first with `/pushl` before Step 7 evaluation.

---

### Step 3: After Loop Completes

Report final status:
- Which conditions are green
- Which conditions are still red (with specific blockers)
- What was fixed across iterations
- Whether PR is ready to merge

Print a final status table with all 6 conditions and their current state.
