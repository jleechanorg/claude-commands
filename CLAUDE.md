# Claude Commands Maintainer Guide

This repository exports reusable Claude Code commands, skills, hooks, agents,
and installation tooling. It is not an application checkout; do not assume
WorldArchitect source paths, services, credentials, test runners, or deployment
commands exist here.

## Maintain the Export Contract

- Keep root guidance short and repository-specific.
- Commands are executable prompt templates under `.claude/commands/`.
- Canonical skills are `.claude/skills/<name>/SKILL.md`.
- Legacy flat skill files are compatibility pointers, not second authorities.
- Prefer one canonical implementation plus pointers over duplicated prose.
- Keep examples portable: use placeholders for repo names, paths, domains,
  credentials, PRs, and issue IDs.
- Preserve compatibility deliberately; inspect installers and consumers before
  removing a path or alias.

## Change Workflow

1. Read the nearest scoped policy and inspect current consumers.
2. Record file justification before editing.
3. For behavior-shaping skill changes, capture a failing RED contract first.
4. Make the smallest change in the canonical owner.
5. Re-run the same contract for GREEN, then run frontmatter, link, and loader
   checks.
6. Commit and push each green unit from an isolated branch/worktree.

Do not edit directly on `main`, discard unrelated changes, prune worktrees,
force-push, or merge without target-repository authorization.

## Shared Policy

- Issue tracking uses `br`, never `bd`.
- `/green` has exactly two current-head gates: all required CI successful and
  mergeable/no conflicts.
- CodeRabbit and Bugbot are advisory only.
- Evidence, `/advice`, and review-thread resolution remain draft-phase quality
  work and do not redefine `/green`.
- Commands should point to canonical skills instead of restating long
  procedures.

## Verification

Run the repository's targeted tests plus:

```bash
git diff --check
git status --short
```

For skill work, also validate YAML frontmatter and smoke native discovery with
`codex debug prompt-input` when available. Before reporting a push, compare
`git rev-parse HEAD` with `git ls-remote origin <branch>`.

Detailed command metadata rules live in `.claude/commands/CLAUDE.md`.
