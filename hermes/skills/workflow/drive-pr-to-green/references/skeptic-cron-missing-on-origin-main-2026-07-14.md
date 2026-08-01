# Pitfall — Skeptic Cron Missing on origin/main (Local Stale-Checkout Trap)

**Discovered:** 2026-07-14, PR #8290 drive.
**Severity:** Drive-blocking. The PR sits at 7-green for hours with no auto-merge, no diagnostic noise.
**File reference:** `references/skeptic-cron-missing-on-origin-main-2026-07-14.md`

## Symptom

A drive that hits 7-green effective (all Green Gate checks PASS, REAL-mode MCP smoke PASS, CodeRabbit commit-status `success`, Evidence Gate PASS, Bugbot clean, no unresolved comments) but:

- `skeptic-cron.yml` workflow_dispatch returns `HTTP 422: Workflow does not have 'workflow_dispatch' trigger`
- The workflow is **not in the GH Actions API workflow list** for the repo (only the local checkout has the file)
- `gh api repos/<owner>/<repo>/actions/workflows` returns 0 skeptic-* workflows
- The launchd Skeptic cron in `jleechanorg/jleechanclaw#779` was mentioned in prior conversations but **is not present locally** (`ls ~/.hermes/launchd/*skept*` returns No such file)
- `crontab -l | grep -i skept` returns nothing

## Root Cause

The local worktree of `$GITHUB_REPOSITORY` at `~/.projects/your-project.com/` is on a **divergent branch** (typically an older feature branch) that has `skeptic-cron.yml`, `skeptic-cron-reusable.yml`, `skeptic-gate.yml`, `skeptic-self-verify.yml` — but the actual `origin/main` does not have these files. The Skeptic system was either removed, never merged, or lives on a different fork.

```
$ git ls-tree origin/main .github/workflows/ | grep skeptic
(empty)
$ ls projects/your-project.com/.github/workflows/skeptic*.yml
skeptic-cron-reusable.yml  skeptic-cron.yml  skeptic-gate-reusable.yml  skeptic-gate.yml  skeptic-self-verify.yml
```

The local files appear "live" because the worktree has them, but the GH Actions API only sees what is on `origin/main` of the default branch.

## Detection (Pre-flight Gate)

Before assuming skeptic-cron.yml will auto-merge, run this 3-step verification:

1. `git -C <repo> ls-tree origin/main .github/workflows/ | grep -i skeptic` — must be NON-empty
2. `gh api repos/<owner>/<repo>/actions/workflows | jq '.workflows[] | select(.name|test("skeptic";"i"))'` — must return at least 1 entry
3. `gh workflow run skeptic-cron.yml --repo <owner>/<repo>` — must NOT return `Workflow does not have 'workflow_dispatch' trigger`

If ANY of the 3 fail, the Skeptic system is not live on this repo.

## Recovery Path

Once detected:

1. **Do NOT wait for auto-merge.** It will not happen.
2. **Post final status to thread** with explicit "MERGE APPROVED required" callout (per `env-preferences.mdc`).
3. **Wait for user's literal `MERGE APPROVED` reply**, then execute `gh pr merge <N> --squash --repo <owner>/<repo>`.
4. **Open followup bead** (`br create`) of type=chore priority=2: "Restore skeptic-cron.yml on origin/main — orphan in local worktree only; merge train silently stalls otherwise."

## Anti-Pattern (don't do this)

Do NOT assume the Skeptic system is live just because:
- The local checkout has `skeptic-cron.yml` (it could be from a stale divergent branch)
- Prior sessions mentioned the launchd Skeptic cron (the cron could have been removed or never existed)
- The PR was 7-green (N-green ≠ auto-merge — auto-merge requires the merge-bot to be live)

## Why This Was a Real Failure Mode

In the 2026-07-14 PR #8290 drive, the agent reached 7-green effective state at ~22:53Z and waited for skeptic-cron.yml to fire. It never did. The agent posted a "ready for merge" status and waited ~30 min before recognizing the Skeptic system wasn't live. Each minute of wasted wait is a minute the user is blocked on a deliverable.

## Pair With

- `references/coderabbit-commit-id-gate3-stale-review-2026-07-14.md` — CodeRabbit stale-review gap (separate but related)
- `references/smoke-gate-real-mode-requirement-2026-07-14.md` — MOCK vs REAL smoke distinction
- `references/evidence-gate-freshness-contract-2026-07-13.md` — Evidence Gate freshness pitfall