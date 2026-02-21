# 📚 Reference Export - Agents Configuration

**Note**: This is a reference export from a working Claude Code project. These agent
configurations and guidelines may contain project-specific references that need adaptation.

Customize the following for your project:
- Project-specific paths ($PROJECT_ROOT/ → your main source directory)
- Repository and domain references
- CI commands and test runner paths

---

# Repository Guidelines (Compact Core)

## Purpose
This is the enforceable core contract for agents working in this repo. Keep this file concise; place detailed procedures in `.claude/skills/` or `.codex/skills/` and link them here.

## Non-Negotiables
- Preserve existing `GITHUB_TOKEN=...` lines in the user's real crontab unless explicitly asked to modify them.
- Do not use sparse checkout in this repository.
- Keep `.beads/` tracked and include beads changes in PRs.
- Use `gh` for GitHub operations (PRs/issues/checks/releases).
- At session end: quality checks + push branch updates; work is not complete until push succeeds.

## LLM Architecture Principles
### Core rule
- LLM decides, server executes.
- Provide full context to the LLM for decision-making.
- Execute tools/state changes server-side.
- Incorporate actual tool results in final output.

### Banned patterns
- Keyword intent bypasses that skip LLM judgment.
- Stripping tool definitions based on predicted need.
- Pre-computing results the LLM should request.
- “Optimization” that removes required context.
- Requested features hidden behind disabled-by-default flags.

### Prefer schemas
- Prefer structured JSON input/output schemas over prose templates.

## File Protocol (Required)
Before touching any file, document:
- GOAL
- MODIFICATION
- NECESSITY
- INTEGRATION PROOF

Default to integrating into existing files. New file creation is last resort.
Integration order:
1. Existing similar file
2. Existing utility
3. Existing `__init__.py`
4. Existing test file
5. Existing class method
6. Config file
7. New file only if justified

## Testing & CI Expectations
- Keep CI green against `origin/main`.
- Run targeted local tests; CI handles broad coverage.
- Evidence bundles are not success by themselves; inspect artifacts skeptically.
- Always report evidence directory paths in summaries.

### CI failure triage sequence
1. `git fetch` and verify local head against branch remote.
2. Reproduce exact failing test first.
3. Pull full CI logs immediately.

## Python Logging & Imports
- In `$PROJECT_ROOT/`, use unified logger: `from mvp_site import logging_util`.
- Keep imports module-level (no inline function imports outside tests).

## Skills Discovery (Mandatory)
Before starting work, check relevant skills in:
- Personal: `~/.claude/skills/`
- Project: `.claude/skills/`

When conflicts exist, personal skills win.
Use matching skills automatically based on request context.

## Key Project Conventions
- Main code: `$PROJECT_ROOT/`
- Tests: `$PROJECT_ROOT/tests/`, top-level `tests/`, `testing_mcp/`, `testing_ui/`
- Commands:
  - `./run_tests.sh`
  - `./run_lint.sh`
  - `./run_ui_tests.sh`

## Timeout Guardrail
Keep all request-handling layers at 600s (10 min) unless coordinated stack-wide.
Use `scripts/timeout_config.sh` with `WORLDARCH_TIMEOUT_SECONDS`.
WorldAI campaign LLM/browser waits should default to at least 180s.

## Modal Routing Reference (Critical)
Routing order in `$PROJECT_ROOT/agents.py:get_agent_for_input()`:
1. God mode prefix
2. Character creation completion override
3. Modal locks (character creation / level-up)
4. Campaign upgrade
5. Character creation state
6. Combat state
7. Semantic intent classifier
8. Explicit mode override
9. Story mode fallback

Use stale-flag guards for level-up:
- Explicit `level_up_in_progress=False` blocks stale reactivation.
- Explicit `level_up_pending=False` blocks stale reactivation unless in-progress is true.

Finish choice injection in `$PROJECT_ROOT/world_logic.py` must use pre-update state and preserve injected choice in structured fields.

## Git & Rebase Rules
- Before `git rebase --continue`, always:
  1. Check conflict markers.
  2. Run lint/type-check.
  3. Stage resolved files and verify `git status`.
- If rebase appears stuck, inspect lint/type errors first.

## GitHub CLI Protocol
- Verify branch names via `gh pr view <num> --json headRefName` (never guess).
- Use HEREDOCs for multi-line `gh` bodies.
- If available, use Codex Web bootstrap markers under `/tmp/codex_web_setup_status.env`.

## Landing the Plane
When ending a coding session:
1. Create/update beads for remaining work.
2. Run quality gates relevant to changed code.
3. Update bead statuses.
4. `git pull --rebase` then `git push`.
5. Confirm branch is up to date.
6. Hand off with context and artifact paths.

## References
- Detailed workflows: `CLAUDE.md`, `docs/CLAUDE.md`
- Skills: `.claude/skills/`, `.codex/skills/`
- Modal lock patterns: `$PROJECT_ROOT/agents.py`, `$PROJECT_ROOT/world_logic.py`
- Beads usage: `docs/beads_creation_manual.md`
