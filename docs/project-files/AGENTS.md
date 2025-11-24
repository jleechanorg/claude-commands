# Repository Guidelines

## Skills System

**Added 2025-11-10** | Last updated: 2025-11-10

**IMPORTANT: Before starting any task, check both skill directories for relevant skill files:**
- **Personal skills**: `~/.claude/skills/` (user-specific, takes precedence)
- **Project skills**: `.claude/skills/` (team-shared, repository-specific)

Skills are modular capabilities that provide specialized knowledge and workflows. Each skill is a markdown file with:
- **Frontmatter**: YAML metadata including `description`, `type`, and `scope`
- **Content**: Instructions, commands, best practices, and guidelines for specific tasks

**Example skill file structure** (`.claude/skills/pr-workflow-manager.md`):

```
---
description: "Create and manage pull requests"
type: "workflow"
scope: "github"
---

## Overview
Summarize the workflow goals and any prerequisites.

## Quick Start
List the core commands (e.g., `/commentreply`, `/pushl`) required for the standard PR path.

## Advanced Patterns
Cover escalation steps, edge cases, and how to coordinate with automation.
```

### How to Use Skills
1. **Automatic Discovery**: Scan both `~/.claude/skills/*.md` and `.claude/skills/*.md` files at the start of each conversation
2. **Priority System**: Personal skills (`~/.claude/skills/`) override project skills (`.claude/skills/`) when names conflict
3. **Match to Context**: When a user request matches a skill's description or activation cues, load and follow that skill's guidelines
4. **Progressive Disclosure**: Skills open with quick-start guidance, then layer in advanced patterns and edge cases so users can reveal detail only when needed
5. **Follow Instructions**: Treat skill content as authoritative guidelines for that domain

### Skill Activation Patterns
- User requests match skill descriptions (e.g., "create a PR" → `pr-workflow-manager.md`)
- Task domain aligns with skill scope (e.g., MCP operations → `mcp-agent-mail.md`)
- Codebase questions match orientation skills (e.g., "where is X?" → `worldarchitect-codebase-sherpa.md`)

See `.claude/` for orchestrator command references and additional skill examples.

**Behavior Standard**: Follow the same skill discovery and activation pattern as the Claude Code CLI: automatically load relevant skills without explicit user invocation, prioritizing personal skills when overlaps occur.

## Project Structure & Module Organization
- `mvp_site/`: Python 3.11 backend (Flask, MCP tooling), tests, templates, and static assets. Frontends live in `mvp_site/frontend_v1/` and `mvp_site/frontend_v2/`.
- `mvp_site/tests/` and `mvp_site/test_integration/`: Unit and integration tests. Additional top‑level tests exist in `tests/`.
- `scripts/` and top‑level `run_*.sh`: Development, CI, and utility commands.
- `.claude/` and related folders: Agent orchestration commands and docs (detailed conventions live in `docs/CLAUDE.md`).
- `docs/`, `roadmap/`, `world/`: Documentation, plans, and content assets.

## Build, Test, and Development Commands
- `./vpython mvp_site/main.py serve`: Run the API locally (auto‑starts MCP in typical workflows). Alt: `./run_local_server.sh`.
- `./run_tests.sh [--full|--integration|--coverage]`: Run Python tests (intelligent selection by default). Use `--integration` for external‑dep tests.
- `./run_tests_with_coverage.sh`: Generate coverage; HTML output under `/tmp/worldarchitectai/coverage/`.
- `./run_ui_tests.sh`: Execute UI/browser tests where applicable.
- `./run_lint.sh` or `pre-commit run -a`: Lint/format (Ruff, isort, Prettier, ESLint). First‑time: `pre-commit install`.

## Coding Style & Naming Conventions
- Python: 4‑space indent, 88‑char lines, double quotes. Lint/format via Ruff; imports via isort; typing with mypy; security scan via bandit (configured in `pyproject.toml`).
- JavaScript/CSS in `mvp_site/static/`: Prettier (2‑space tabs, single quotes) and ESLint.
- Naming: `snake_case` for files/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants. Tests named `test_*.py`.

## Testing Guidelines
- Frameworks: Standard unittest/pytest‑style tests run through `run_tests.sh` (parallel by default). Integration tests live in `mvp_site/test_integration/` and are opt‑in (`--integration`).
- Environment: Default `TEST_MODE=mock`; real integrations may require credentials.
- Conventions: Place feature tests near code in `mvp_site/tests/`; prefer small, deterministic tests. Use `--coverage` before merging substantive changes.

## Commit & Pull Request Guidelines
- Commits: Imperative mood with optional scope, e.g., `Context Optimization: Reduce token usage` (see `git log`).
- PRs: Clear description, linked issues, screenshots for UI changes, and a test plan (e.g., commands run: `./run_tests.sh --full --coverage`). Ensure CI passes and lint is clean.

## Security & Configuration Tips
- Never commit secrets. Copy `.env.example` to `.env` and populate locally.
- Firebase `serviceAccountKey.json` and `GEMINI_API_KEY` must be set as documented in `README.md`.
- Prefer local mocks for tests; guard credentials with environment variables.
- WorldArchitecture.AI Firebase Admin key lives at `~/serviceAccountKey.json` (duplicate: `~/serviceAccountKey-firebase.json`). Set `GOOGLE_APPLICATION_CREDENTIALS` to that path when running this repo locally.

### Beads Issue Tracking
- **NEVER gitignore `.beads/`**: Issue tracking database MUST be version controlled and tracked in git.
- The `.beads/` directory contains project issue tracking shared across the team.

### GitHub Token Access
**Available for all agents and automation:**

**⚠️ Security Note**: This documents the current token storage approach. For production use, consider more secure alternatives like `gh auth login` (uses OS credential manager) or environment-only token management.

- **Token Location**: User's GitHub token is currently accessible at `~/.token`
  - **Security**: Plain text storage - ensure proper file permissions (`chmod 600 ~/.token`)
  - **Alternative**: Use `gh auth login` for secure OS keychain/credential manager storage
- **GitHub CLI (local)**: Use `GITHUB_TOKEN=$(cat ~/.token)` for gh CLI authentication
  - **Recommended**: After `gh auth login`, use `gh` commands directly without manual token management
- **GitHub Actions**: Use `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}` environment variable (automatically provided by GitHub Actions)
- **Agent Usage**: All agents can read from `~/.token` and set `GITHUB_TOKEN` environment variable for local operations
- **Scope Coverage**: Current token has admin scopes (admin:org) which encompass read scopes (read:org)
  - **Best Practice**: Use minimum required scopes (e.g., `repo`, `read:org`) for production tokens
  - **Note**: Admin scopes should only be used when necessary for specific operations
- **Usage Examples**:
  - Local session: `export GITHUB_TOKEN=$(cat ~/.token)`
  - Inline command: `GITHUB_TOKEN=$(cat ~/.token) gh pr list`
  - Agent scripts: Read from `~/.token` and set as environment variable
  - GitHub Actions workflow: `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}` as environment variable in workflow steps

## Git Workflow & Rebase Best Practices

### Rebase Hook Awareness
Git hooks (including pre-commit) run during `git rebase --continue`. If hooks fail (lint/type-check), the rebase appears to "hang."

### Mandatory Pre-Rebase-Continue Checklist
Before `git rebase --continue`:

```bash
# 1. Check for conflict markers
rg '<<<<<<<|=======|>>>>>>>' --type-add 'code:*.{js,jsx,ts,tsx}' --type code

# 2. Run lint (fix all errors)
npm run lint  # or: cd mvp_site/frontend_v2 && npm run lint

# 3. Run type-check (TypeScript)
npm run type-check  # or: tsc --noEmit

# 4. Stage and verify
git add <resolved-files>
git status

# 5. Continue rebase
git rebase --continue
```

### Troubleshooting Blocked Rebases
**Symptom**: `git rebase --continue` hangs.

**Quick Fix**:
```bash
# Ctrl+C to interrupt
rg '<<<<<<<'           # Find conflict markers
npm run lint           # See actual errors
# Fix all errors
git rebase --continue  # Retry
```

**Abort if stuck**: `git rebase --abort`

**Key Rules**:
- ✅ Always check for conflict markers before continuing
- ✅ Run lint/type-check manually during rebase
- ❌ Never continue with lint/type errors present

## Agent‑Specific Notes
- Prefer edits under `mvp_site/` and existing scripts. Follow formatting via `pre-commit` before proposing changes. See `.claude/`, `CLAUDE.md`, and `QWEN.md` for orchestration conventions.
