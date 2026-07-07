---
name: repro
description: Thin pointer — canonical /repro workflow lives in WorldArchitect repo at .claude/skills/repro-twin-clone-evidence/SKILL.md. File gh issue, create draft PR, copy campaign, reproduce, verdict.
---

# /repro (Hermes pointer)

This skill is a **thin pointer**. The canonical source of truth is:

**`/Users/$USER/projects/your-project.com/.claude/skills/repro-twin-clone-evidence/SKILL.md`**

Always read and execute the canonical skill. Do not duplicate logic here.

## When this skill is used

- A Hermes session (Slack, cron, gateway) receives a `/repro` request
- The WorldArchitect repo is available at the path above

## Firestore credential requirements

All WorldArchitect scripts (`copy_campaign.py`, `download_campaign.py`, etc.) require:
```bash
GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json"
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json"
WORLDAI_DEV_MODE=true
```
`WORLDAI_DEV_MODE=true` is mandatory — scripts raise `ValueError` without it.

## Hard gates (MUST execute, in order, before anything else)

**1. `gh issue create`** — File the GitHub issue immediately. No env setup, no scripts, no copying until this succeeds. See canonical skill Step 0 for the exact command + template.

**2. `gh pr create --draft`** — Precreate the draft PR immediately, linked to the issue. See canonical skill Step 1 for the exact command.

**Both gates must complete before proceeding to Step 0.75 (bug phenotype capture) or any other step.**

## Bug phenotype capture (Step 0.75)

After gates are confirmed, capture the structured bug phenotype from the user's description before running any repro scripts. Ask targeted clarification questions if the description is vague. See canonical skill Step 0.75.

## Git worktree pitfall

When creating a branch for the draft PR, `git checkout main` may fail if `main` is already checked out at another worktree (error: `fatal: 'main' is already checked out at '/path/to/worktree'`).

**Fix:** Use `git worktree add <path> -b <branch> HEAD` to create a new worktree on a fresh branch. This avoids disturbing the existing main checkout and is the standard pattern for repro branches:

```bash
cd /Users/$USER/projects/your-project.com
git worktree add /Users/$USER/projects/worktree_<slug> -b fix/<descriptive-branch>-<issue-number> HEAD
# Work in the worktree for PR commits
# Clean up with: git worktree remove /Users/$USER/projects/worktree_<slug>
```

## Failure handling

- GH auth fails → report `SLACK_MCP_XOXB_TOKEN may be expired` and stop
- Issue creation fails → stop entirely, do not proceed
- Draft PR creation fails → stop (issue exists as record)
- `git checkout main` blocked by existing worktree → use `git worktree add` instead
- Never skip gates to "save time"

## Reference

- `references/architecture-decision.md` — why canonical lives in repo, file location map, hard-gate rationale, verdict branches
- `references/god-mode-directive-enforcement.md` — god-mode directives are advisory-only (no runtime enforcement); `_should_reject_directive` filter patterns; investigation pattern for god-mode bugs
- `references/evidence-extraction-patterns.md` — how to extract directive violations from exported campaign data (game state JSON + story text search, scene mapping, correction detection)
