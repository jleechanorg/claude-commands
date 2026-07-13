---
description: Check PR green status — production green (7-green + /er PASS) vs non-production green (lite-green + /er PARTIAL-OK). Embeds /er requirement.
type: verification
execution_mode: immediate
---

# /green — PR Green Status Check (Two-Tier)

**`/green` is now an evidence-gated check.** A PR is "green" only when both
the workflow gates (CI, CR, Skeptic, etc.) pass **AND** the `/er` evidence
verdict meets the tier-appropriate threshold.

**Two-tier standard** (added 2026-07-02, per user's request):

| Tier | Applies to | Gates | /er verdict required |
|------|------------|-------|----------------------|
| **PRODUCTION green** | `$PROJECT_ROOT/**` (excl. `$PROJECT_ROOT/tests/**` + `$PROJECT_ROOT/test_integration/**`), any prompt/instruction file fed to a model, any CI/workflow/safety file, any backend service or schema | 7-green (CI, conflicts, CR APPROVED, Bugbot, comments, evidence review, Skeptic) | `/er` **PASS** with real-LLM/real-BigQuery evidence |
| **NON_PRODUCTION green** | docs-only, tests-only, tooling-only, roadmap/design changes, repo-hygiene, prompt-template work that doesn't change runtime behavior | lite-green (CI, conflicts, CR APPROVED) | `/er` **PARTIAL** or better (PARTIAL with explicit waiver OK) |

A change is **production** by **effect, not file extension**. A `.md` file in
`$PROJECT_ROOT/prompts/**` is production. A `.py` file that only contains type
hints and comments is non-production.

## EXECUTION INSTRUCTIONS

When invoked as `/green <PR#>` or `/green` (auto-detect from current branch):

### Step 1 — Resolve PR number

```bash
gh pr list --head "$(git branch --show-current)" --json number --jq '.[0].number'
```

Resolve OWNER/REPO from the git remote.

### Step 2 — Classify the PR (production vs non-production)

Inspect changed files via `gh pr view N --json files --jq '.files[].path'` and
apply this rule:

- **PRODUCTION** if any changed file matches:
  - `$PROJECT_ROOT/**` excluding `$PROJECT_ROOT/tests/**`, `$PROJECT_ROOT/test_integration/**`
  - `$PROJECT_ROOT/prompts/**` (prompt files are production LLM behavior)
  - any `.yaml`/`.yml`/`.json`/`.toml` under `.github/workflows/`, `.github/actions/`
  - any file that changes a model prompt, system instruction, or agent template
  - any file that changes CI gate, deploy, or merge-safety behavior
  - any `migrations/` or DB schema file
- **NON_PRODUCTION** otherwise (docs, tests, tooling, roadmap, repo-hygiene)

When in doubt → classify **PRODUCTION** (the stricter tier).

### Step 3 — Run gate-by-gate verification

For **PRODUCTION** PRs, execute ALL of these in parallel:

1. Get branch: `gh pr view N --json headRefName --jq '.headRefName'`
2. Get PR state: `gh pr view N --json state,merged --jq '{state,merged}'` — if merged/closed, stop
3. Green Gate log: `gh run list --workflow green-gate.yml --branch BRANCH -L 1` → read gate-by-gate PASS/FAIL lines
4. Skeptic Gate log: `gh run list --workflow skeptic-gate.yml --branch BRANCH -L 1` → read VERDICT line
5. CR review state: `gh pr view N --json reviews` → latest non-COMMENTED from `coderabbitai` must be `APPROVED`
6. Bugbot: `gh pr view N --json reviews` → cursor[bot] must have zero error-severity comments
7. Comment resolution: `gh api repos/OWNER/REPO/pulls/N/comments?per_page=100` + GraphQL `isResolved` — zero unresolved
8. Mergeable: `gh pr view N --json mergeable --jq '.mergeable'` must be `true`

**`/er` invocation (MANDATORY for production):** run `/er <PR_NUMBER>` to get
the evidence verdict. The PR is **NOT** green if `/er` does not return
**PASS**. To invoke `/er` programmatically:

```bash
# Inline /er verdict from the most recent evidence-gate workflow run
gh run list --workflow evidence-gate.yml --branch BRANCH -L 1 --json databaseId --jq '.[0].databaseId' \
  | xargs -I{} gh run view {} --log 2>/dev/null | grep -E "VERDICT|EVIDENCE"
# OR invoke the /er slash command on the PR (preferred):
gh pr comment N --body "/er"
# Then wait for the evidence-review-bot reply with the PASS/PARTIAL/FAIL verdict.
```

For **NON_PRODUCTION** PRs, verify only:

1. CI green
2. Mergeable
3. CodeRabbit APPROVED
4. `/er` returns PARTIAL or better (run `/er` or check `evidence-gate` workflow verdict)

Skip skeptic, evidence-gate, bugbot, comment-resolution gates.

### Step 4 — Report

Output one of these tables.

For PRODUCTION PRs:

```
## Production-Green Status: PR #N

| Gate | Status | Detail |
|------|--------|--------|
| 1. CI green | PASS/FAIL | CI=success / CI=pending |
| 2. No conflicts | PASS/FAIL | mergeable=true / mergeable=false |
| 3. CR APPROVED | PASS/FAIL | CR=APPROVED / CR=CHANGES_REQUESTED |
| 4. Bugbot clean | PASS/FAIL | cursor[bot] error-severity=0 |
| 5. Comments resolved | PASS/FAIL | unresolved=0 / N unresolved |
| 6. Evidence review | PASS/FAIL | /er=PASS / /er=PARTIAL / /er=FAIL |
| 7. Skeptic PASS | PASS/FAIL | VERDICT: PASS / no verdict |

**Verdict**: PRODUCTION-GREEN / NOT PRODUCTION-GREEN (Gates X, Y failing)
```

For NON_PRODUCTION PRs:

```
## Non-Production-Green Status: PR #N

| Gate | Status | Detail |
|------|--------|--------|
| 1. CI green | PASS/FAIL | CI=success / CI=pending |
| 2. No conflicts | PASS/FAIL | mergeable=true / mergeable=false |
| 3. CR APPROVED | PASS/FAIL | CR=APPROVED / CR=CHANGES_REQUESTED |
| 4. /er PARTIAL+ | PASS/FAIL | /er=PARTIAL+ / /er=FAIL |

**Verdict**: NON-PRODUCTION-GREEN / NOT NON-PRODUCTION-GREEN (Gates X, Y failing)
```

### Critical Rules

- **NEVER** use `gh pr checks` output to determine gate status (it always
  reports Green Gate as "pass" when the workflow runs, regardless of individual
  gate outcomes).
- **ALWAYS** report which tier was used: PRODUCTION or NON_PRODUCTION.
- **ALWAYS** run `/er` (or check evidence-gate verdict) before declaring green
  — `/green` is no longer just a workflow check, it is also an evidence check.
- "Green Gate: pass" in `gh pr checks` means the workflow ran, NOT that gates passed.
- "CodeRabbit: pass" means the webhook responded, NOT an APPROVED review.

### Where this rule lives

The two-tier rule is mirrored in:
- `~/.hermes/workspace/SOUL.md` → `## COMMIT: green-implies-er` (policy commit)
- `~/.claude/skills/pr-green-definition.md` (canonical 7-green table) — extended
  with a tier-overlay note pointing back to this file
- `~/.claude/commands/fullrun.md` — `/fullrun` invocations of `/green` now use
  the tier classifier
- `~/.claude/commands/er.md` — `/er` returns the verdict format this command consumes
