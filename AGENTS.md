# Claude Commands Repository Policy

## Purpose

This repository publishes reusable Claude Code commands, skills, hooks, agents,
and installer tooling. It is an export library, not the WorldArchitect
application. Keep project-specific examples clearly labeled and out of
always-loaded policy files.

## Working Rules

- Read `README.md` and the scoped `CLAUDE.md` nearest the file being changed.
- Preserve unrelated changes, especially `.beads/` state in other worktrees.
- Work on a branch/worktree, never directly on `main`.
- Do not use sparse checkout or remove another user's worktree.
- Prefer editing an existing command or skill over adding a near-duplicate.
- Before modifying a file, record GOAL, MODIFICATION, NECESSITY, and
  INTEGRATION PROOF.
- Use `apply_patch` for focused edits.
- Run targeted tests and repository policy checks before committing.
- Commit messages must name the CLI/model that authored the change.
- Push each green unit and verify the remote SHA before reporting completion.

## Command and Skill Ownership

- Executable commands live in `.claude/commands/<name>.md` and require YAML
  metadata defined by `.claude/commands/CLAUDE.md`.
- Canonical skills live in `.claude/skills/<name>/SKILL.md`.
- A legacy flat `.claude/skills/<name>.md` may exist only as a thin
  compatibility pointer to the canonical `SKILL.md`.
- Every active `SKILL.md` starts with YAML frontmatter containing `name` and a
  trigger-shaped `description` beginning with `Use when`.
- Detailed behavior belongs in the canonical skill; command wrappers stay thin.

## Current Shared Contracts

- `br` is the issue-tracking CLI. Do not introduce `bd` commands.
- A PR is `/green` only when both current-head gates pass:
  1. every required CI check is terminal and successful;
  2. GitHub reports the PR mergeable with no conflicts.
- CodeRabbit and Bugbot are advisory reviewers, never `/green` gates.
- Evidence, review-thread cleanup, and `/advice` are draft-phase quality work,
  not additional `/green` gates.
- Never force-push or merge without the authorization required by the target
  repository's live policy.

## Verification

For Markdown/policy changes, verify:

1. active non-archive stale-gate and `bd` scans;
2. flat-file/SKILL ownership and divergence;
3. YAML frontmatter parsing for active `SKILL.md` files;
4. relative links and named command/skill references;
5. relevant repository tests and loader smoke checks.

Use `git status --short`, `git diff --check`, and `git diff --stat` before
committing.
