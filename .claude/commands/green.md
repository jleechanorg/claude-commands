---
description: Check PR green status for a PR, including lite-green for docs/tests-only changes and full 7-green for runtime changes
type: verification
execution_mode: immediate
---

## EXECUTION INSTRUCTIONS

When invoked as `/green <PR#>` or `/green` (auto-detect from current branch), execute the verification procedure from `~/.claude/skills/pr-green-definition.md`.

First classify the PR:

- **lite-green** if the diff is docs-only or tests-only
- **7-green** otherwise

**Skill reference**: `~/.claude/skills/pr-green-definition.md` — "Verification Procedure (Mandatory)" section.

### Step 1 — Resolve PR number

If no PR number given, detect from current branch:
```bash
gh pr list --head "$(git branch --show-current)" --json number --jq '.[0].number'
```

Resolve OWNER/REPO from the git remote.

### Step 2 — Determine green mode

Inspect changed files and choose one mode:

- **Lite-green**: docs-only or tests-only PR
- **7-green**: any runtime / production / workflow-safety affecting PR

### Step 3 — Run gate-by-gate verification

Execute ALL of these in parallel where possible:

1. **Get branch name**: `gh pr view N --json headRefName --jq '.headRefName'`
2. **Get PR state**: `gh pr view N --json state,merged --jq '{state,merged}'`
   - If merged or closed: report status and stop
3. **Green Gate log**: `gh run list --workflow green-gate.yml --branch BRANCH -L 1` → read gate-by-gate PASS/FAIL lines
4. **Skeptic Gate log**: `gh run list --workflow skeptic-gate.yml --branch BRANCH -L 1` → read VERDICT line
5. **CR review state**: `gh pr view N --json reviews` — find latest non-COMMENTED review from coderabbitai
6. **Mergeability**: `gh pr view N --json mergeable --jq '.mergeable'`

For **lite-green** PRs, verify only:

1. **CI green**
2. **Mergeable**
3. **CodeRabbit APPROVED**

Skip skeptic/evidence/bugbot/comment-resolution gates for lite-green PRs.

### Step 4 — Report

Output one of these tables.

```
## Lite-Green Status: PR #N

| Gate | Status | Detail |
|------|--------|--------|
| 1. CI green | PASS/FAIL | CI=success / CI=pending |
| 2. No conflicts | PASS/FAIL | mergeable=true / mergeable=false |
| 3. CR APPROVED | PASS/FAIL | CR=APPROVED / CR=none |

**Verdict**: LITE-GREEN / NOT LITE-GREEN (Gates X, Y failing)
```

or

```
## 7-Green Status: PR #N

| Gate | Status | Detail |
|------|--------|--------|
| 1. CI green | PASS/FAIL | CI=success / CI=pending |
| 2. No conflicts | PASS/FAIL | mergeable=true / mergeable=false |
| 3. CR APPROVED | PASS/FAIL | CR=APPROVED / CR=none |
| 4. Bugbot clean | PASS/FAIL | conclusion=success / none |
| 5. Comments resolved | PASS/FAIL | 0 unresolved / N unresolved |
| 6. Evidence review | PASS/FAIL | evidence-gate passed / missing |
| 7. Skeptic PASS | PASS/FAIL | VERDICT: PASS / no verdict |

**Verdict**: 7-GREEN / NOT 7-GREEN (Gates X, Y failing)
```

### Critical Rules

- **NEVER** use `gh pr checks` output to determine gate status
- **ALWAYS** report which mode you used: lite-green or 7-green
- **ALWAYS** read the Green Gate workflow log for actual gate results when the PR requires 7-green
- **DO NOT** require Green Gate or Skeptic verification for a valid lite-green PR
- "Green Gate: pass" in `gh pr checks` means the workflow ran, NOT that gates passed
- "CodeRabbit: pass" means the webhook responded, NOT an APPROVED review
