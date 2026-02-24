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
- Never delete/remove the worktree directory you are currently operating in (or the user's stated active worktree) unless explicitly asked.
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
- "Optimization" that removes required context.
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

## Python Logging & Imports
- In `$PROJECT_ROOT/`, use unified logger: `from mvp_site import logging_util`.
- Keep imports module-level (no inline function imports outside tests).

## Skills Discovery
Before starting work, check relevant skills in:
- Personal: `~/.claude/skills/`
- Project: `.claude/skills/`

When conflicts exist, personal skills win.
Use matching skills automatically based on request context.

## Project Structure & Module Organization
- `$PROJECT_ROOT/`: Python 3.11 backend (Flask, MCP tooling), tests, templates, and static assets. Frontends live in `$PROJECT_ROOT/frontend_v1/` and `$PROJECT_ROOT/frontend_v2/`.
- `$PROJECT_ROOT/tests/` and `$PROJECT_ROOT/test_integration/`: Unit and integration tests. Additional top‑level tests exist in `tests/`.
- `scripts/` and top‑level `run_*.sh`: Development, CI, and utility commands.
- `.claude/` and related folders: Agent orchestration commands and docs (detailed conventions live in `docs/CLAUDE.md`).
- `docs/`, `roadmap/`, `world/`: Documentation, plans, and content assets.

## Build, Test, and Development Commands
- `./vpython $PROJECT_ROOT/main.py serve`: Run the API locally. Alt: `./run_local_server.sh`.
- `./run_tests.sh [--full|--integration|--coverage]`: Run Python tests.
- `./run_tests_with_coverage.sh`: Generate coverage; HTML output under `/tmp/$PROJECT_NAME/coverage/`.
- `./run_ui_tests.sh`: Execute UI/browser tests.
- `./run_lint.sh` or `pre-commit run -a`: Lint/format.

### testing_mcp and testing_ui execution policy
- Do not use pytest collection for script-style `testing_mcp/` suites. Run directly with `vpython`.
- Canonical: `cd testing_mcp && ../vpython test_<name>.py --server http://127.0.0.1:8001`
- Browser tests: Start server with `TESTING_AUTH_BYPASS=true`, navigate with `?test_mode=true&test_user_id=<id>`.
- For these suites, run with real services only. Mock toggles (`MCP_TEST_MODE`, `MOCK_SERVICES_MODE`, `USE_MOCK_*`) are intentionally not used here.
- `testing_mcp/` and `testing_ui/` scripts must never use mock mode paths. This is a hard policy for smoke/integration and evidence-bearing runs.

## Coding Style
- Python: 4‑space indent, 88‑char lines, double quotes. Lint/format via Ruff; imports via isort.
- JavaScript/CSS: Prettier (2‑space tabs, single quotes).
- Naming: `snake_case` for files/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.

## Testing Guidelines
- Frameworks: unittest/pytest via `run_tests.sh`. Integration tests opt‑in (`--integration`).
- Environment: Default `TEST_MODE=mock`.
- For `testing_mcp/` and `testing_ui/`, do not use mock mode. These suites should validate real MCP/UI behavior with real services.
- Conventions: Feature tests near code in `$PROJECT_ROOT/tests/`; prefer small, deterministic tests.

## Commit & Pull Request Guidelines
- Commits: Imperative mood, e.g., `Context Optimization: Reduce token usage`.
- After completing work, push commits to the PR remote branch so CI and reviewers see the latest state.
- PRs: Clear description, linked issues, screenshots for UI changes, test plan. Ensure CI passes and lint is clean.

## Security & Configuration
- Never commit secrets. Copy `.env.example` to `.env` and populate locally.
- Firebase `serviceAccountKey.json` and `GEMINI_API_KEY` must be set as documented in `README.md`.
- WorldArchitecture.AI Firebase Admin key at `~/serviceAccountKey.json`. Set `GOOGLE_APPLICATION_CREDENTIALS`.

## Timeout Guardrail
Keep all request-handling layers at **600 seconds (10 minutes)**. Use `scripts/timeout_config.sh` with `WORLDARCH_TIMEOUT_SECONDS`. WorldAI campaign LLM/browser waits should default to at least **180 seconds (3 minutes)**.

## Beads Issue Tracking
- **NEVER gitignore `.beads/`** - Must be version controlled.
- Always include `.beads/` changes in PRs - do not drop, revert, or omit beads diffs.

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
  1. Check conflict markers: `rg '<<<<<<<|=======|>>>>>>>'`
  2. Run lint/type-check.
  3. Stage resolved files and verify `git status`.
- If rebase appears stuck, inspect lint/type errors first. Abort if needed: `git rebase --abort`.

## GitHub CLI Protocol
- Verify branch names via `gh pr view <num> --json headRefName` (never guess).
- Use HEREDOCs for multi-line `gh` bodies.
- Task completion: Always push to remote before reporting done.

## Agent-Specific Notes
- Run the `/header` command (`$(git rev-parse --show-toplevel)/.claude/hooks/git-header.sh --with-api`) and append its output as the final element in every reply, after all other text and code blocks.

## Landing the Plane
When ending a coding session:
1. Create/update beads for remaining work.
2. Run quality gates relevant to changed code.
3. Update bead statuses.
4. `git pull --rebase` then `git push`.
5. Confirm branch is up to date.
6. Hand off with context and artifact paths.

## Agent‑Specific Notes

- Run the `/header` command (`$(git rev-parse --show-toplevel)/.claude/hooks/git-header.sh --with-api`) and append its output as the final element in every reply, after all other text and code blocks.

## References
- Detailed workflows: `CLAUDE.md`, `docs/CLAUDE.md`
- Skills: `.claude/skills/`, `.codex/skills/`
- Modal lock patterns: `$PROJECT_ROOT/agents.py`, `$PROJECT_ROOT/world_logic.py`
- Beads usage: `docs/beads_creation_manual.md`
