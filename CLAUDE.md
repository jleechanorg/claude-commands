# 📚 Reference Export - Adaptation Guide

**Note**: This is a reference export from a working Claude Code project. You may need to
personally debug some configurations, but Claude Code can easily adjust for your specific needs.

These configurations may include:
- Project-specific paths and settings that need updating for your environment
- Setup assumptions and dependencies specific to the original project
- References to particular GitHub repositories and project structures

Feel free to use these as a starting point - Claude Code excels at helping you adapt and
customize them for your specific workflow.

---

# CLAUDE.md - Primary Rules and Operating Protocol

**COMPACTNESS RULE**: Keep this file under 200 lines. Move detailed procedures to `.claude/skills/*.md`.

**Primary rules file for AI collaboration on Your Project**

## Mandatory Greeting Protocol

**Every response must begin with:** `Genesis Coder, Prime Mover,`

**Every response must end with:** `[Local: <branch> | Remote: <upstream> | PR: <number> <url>]`

Lead with architectural thinking, follow with tactical execution. Write code as senior architect.

## Output Formatting

**Full absolute paths ALWAYS** - Never abbreviate with `...` or relative paths
- ✅ `/tmp/your-project.com/fix/branch/test/iteration_004/`
- ❌ `.../iteration_004/` or "evidence directory"
- Evidence bundles: Show full structure, symlinks (e.g., `latest -> iteration_004`)

## LLM Architecture Principles

**Core Rule**: LLM decides, server executes - Give full context, never pre-compute decisions

**BANNED Anti-Patterns**:
- Keyword/substring matching for intent (use FastEmbed classifier, <50ms)
- Creating new env vars (use constants; env vars only for credentials/URLs)
- Stripping tool definitions to "optimize"
- Disabled-by-default env vars

**Intent Detection**: Local classifier ONLY. Exception: Parsing structured prefixes (`CHOICE:`, `GOD MODE:`)

**Error Handling Philosophy**: Warnings only - no assertions, retries, or default content. Log warnings and let validation surface issues.

## File Protocols

**New Files**: DEFAULT NO - Integration hierarchy: existing file → utility → `__init__.py` → test → config → NEW (last resort)

**Placement**: Python → `$PROJECT_ROOT/` | Scripts → `scripts/` | Tests → `$PROJECT_ROOT/tests/` | No `_v2`, `_new`, `_backup` files

**Deletion**: NEVER delete unrelated content from origin/main. Task-related only: Integration > Modification > Deletion. Before deleting: Search imports → Fix references → Verify dependencies → Delete. When in doubt: ASK first.

## Critical Rules

| Rule | Requirement |
|------|-------------|
| **NO UNRELATED DELETIONS** | Never delete content from origin/main unrelated to current task |
| **CI test failures are BLOCKERS** | ALL failing tests must be fixed - NEVER merge with failing CI |
| Character creation modal exit | User cannot exit until selecting specific planning_block choice |
| GEMINI 3 CODE EXECUTION ONLY | Code execution mode REQUIRED. Fix root causes, NOT workarounds |
| Test failures | Fix ALL, no excuses, no "pre-existing" excuses |
| Beads tracking | Always include `.beads/` changes in commits/PRs |
| No bash arguments | NEVER pass bash arguments without explicit user approval |
| Timeout integrity | 10min/600s across all layers |
| WorldAI campaign LLM waits | Default >= 3min/180s; 30s insufficient |

## PR & Merge Protocols

- Never merge PRs without explicit "MERGE APPROVED" from user
- MANDATORY: ALL CI tests must pass before merge - check `statusCheckRollup`
- `/pr` must create actual PR with working URL - never give manual steps
- Verify agent work: file existence check, `git diff --stat`, `git status`

### PR Description Requirements

**Required sections**: Summary (1-4 bullets) | Production Code Changes (before → now → why) | Test Changes | Known Limitations

## Claude Code Behavior

1. Operates in worktree directory | 2. `TESTING_AUTH_BYPASS=true vpython` for mock mode | 3. `from google import genai` | 4. Use `~` for paths | 5. MCP tools primary, `gh` fallback | 6. No `_v2`, `_new`, `_backup` files | 7. Cross-platform | 8. Use Read tool | 9. Never `exit 1` | 10. Read/Grep → Edit → Bash | 11. TodoWrite for 3+ steps | 12. Slash commands: `.claude/commands/*.md`

## Diagnostic Efficiency

**Config debugging**: Read source code first (Read tool on consuming file), not exploratory Bash. Max 3 diagnostic attempts before reassessing.

**Env vars**: Set via Cloud Run/Docker/shell profile (NOT `.env` files). Check consuming code for exact names (e.g., `VITE_*` prefix for frontend).

**Grep tool**: Use `Grep` tool for code search, not `grep`/`rg` in Bash (except piping command output).

## Project Overview

Your Project = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack:** Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

**Testing Methodology:** Red-green (`/tdd` or `/rg`): Write failing tests → Confirm fail → Minimal code → Refactor

### MCP CLI JSON Piping

**CRITICAL**: Use `printf` or `cat`, NOT `echo` (adds `\n` that breaks parsing)
- ✅ `printf '{"key":"value"}' | mcp-cli call tool -`
- ✅ `cat file.json | mcp-cli call tool -`
- ❌ `echo '{"key":"value"}' | mcp-cli call tool -`

## Development Guidelines

**Code Standards**: SOLID, DRY, use existing patterns. Constants: Module-level or constants.py. Path Computation: Use `os.path.dirname()`, `os.path.join()`, `pathlib.Path` - NEVER `string.replace()`.

**Comments**: No PR/bead/ticket references in production code. Write comments that explain *why* for future readers, not *when* or *which ticket*. Ticket references belong in commit messages only.

**Security**: `shell=False, timeout=30`. GitHub Actions: SHA-pinned versions only.

### Import Standards (CI Enforced)

- **FORBIDDEN**: try/except around imports (`try: import foo except: pass`)
- **FORBIDDEN**: Inline imports inside functions (`def test(): from foo import bar`)
- **MANDATORY**: All imports at module level - top of file only
  - Order: Standard library → third-party → local (alphabetically sorted within each group)

## Testing & Evidence

- Run specific tests: `./run_tests.sh $PROJECT_ROOT/tests/test_feature.py` (not all)
- testing_mcp: Run directly with `vpython`, NOT pytest
- testing_ui: Run via `python3 $PROJECT_ROOT/main.py testui` with `TESTING_AUTH_BYPASS=true`
- Evidence path: `/tmp/your-project.com/<branch>/<test_name>/latest/`
- TDD: RED (bug) → GREEN (fix) → REFACTOR

**Context Limits:** 500K (Enterprise) / 200K (Paid) | Health: Green (0-30%) | Yellow (31-60%) | Orange (61-80%) | Red (81%+)

## Orchestration

- tmux sessions with dynamic task agents
- Never execute orchestration tasks yourself - delegate to agents
- `/orch` prefix → immediate tmux delegation | `/converge` → autonomous until goal achieved

## Git Workflow

- Main = Truth | All changes via PRs | Fresh branches from main
- **FORBIDDEN**: Merging directly to main without PR | `git sparse-checkout`

## Environment

- Firebase: `~/serviceAccountKey.json` → `GOOGLE_APPLICATION_CREDENTIALS`
- Python: Verify venv, run with `vpython`
- Temp files: Use `mktemp`, never predictable `/tmp/` names

## Operations Guide

**Tool Hierarchy**: Serena MCP → Read/Grep → Edit → Bash (OS only)

**Test Execution**: DO NOT run `./run_tests.sh` without arguments. Use CI for full regression. Print evidence bundle path after testing_mcp tests.

**Data defense**: Use `dict.get()` and validate all data structures before use.

## Slash Commands

- `/fake3` - Runs pre-commit check pipeline
- **Architecture:** `.claude/commands/*.md` = executable prompt templates

## Dangerous Command Safety

**NEVER suggest:** `sudo chown -R $USER:$(id -gn) $(npm -g config get prefix)` or recursive chown on system directories.

**Safe npm fix:** `mkdir ~/.npm-global && npm config set prefix ~/.npm-global`

## Quick Reference

```bash
vpython $PROJECT_ROOT/test_file.py              # Single test
./run_tests.sh $PROJECT_ROOT/tests/test_app.py  # Specific tests
/fake3                                     # Pre-commit check
./integrate.sh                             # New branch
./deploy.sh [stable]                       # Deploy
```

## Skill Files Reference

See `.claude/skills/`: `agents.md`, `llm-prompt-engineering.md`, `file-justification.md`, `code-centralization.md`, `integration-verification.md`, `testing-infrastructure.md`, `unified-logging.md`, `github-cli-reference.md`, `pr-workflow-manager.md`, `dice-authenticity-standards.md`

## Meta-Rules

**Pre-action checkpoint:** Does this violate CLAUDE.md rules?
**Write gate:** Search existing files → Attempt integration → Document why impossible
