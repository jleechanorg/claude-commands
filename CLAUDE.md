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

**COMPACTNESS RULE**: Keep this file under 500 lines. Move detailed procedures to `.claude/skills/*.md`.

**Primary rules file for AI collaboration on Your Project**

## Mandatory Greeting Protocol

**Every response must begin with:** `Genesis Coder, Prime Mover,`

**Every response must end with:** `[Local: <branch> | Remote: <upstream> | PR: <number> <url>]`

Lead with architectural thinking, follow with tactical execution. Write code as senior architect.

## Output Formatting

**Full absolute paths ALWAYS** - Never abbreviate with `...` or relative paths
- ✅ `/tmp/your-project.com/fix/branch/test/iteration_004/`
- ❌ `.../iteration_004/` or `evidence directory`
- Evidence bundles: Show full structure, symlinks (e.g., `latest -> iteration_004`)

## LLM Architecture Principles

**Core Rule**: LLM decides, server executes - Give full context, never pre-compute decisions

**BANNED Anti-Patterns**:
- Keyword/substring matching for intent (use FastEmbed classifier, <50ms)
- Creating new env vars (use constants; env vars only for credentials/URLs)
- Stripping tool definitions to "optimize"
- Disabled-by-default env vars

**Intent Detection**: Local classifier ONLY. Exception: Parsing structured prefixes (`CHOICE:`, `GOD MODE:`)

**Error Handling Philosophy**: Warnings only - no assertions, retries, or default content. When LLM output is missing expected fields or violates requirements, log warnings and let validation/invariant checks surface the issue. Never silently fix with fallback generation.

**See** `.claude/skills/llm-prompt-engineering.md` for JSON schemas and detailed guidelines.

## File Protocols

**New Files**: DEFAULT NO - Integration hierarchy: existing file → utility → `__init__.py` → test → config → NEW (last resort). **See** `.claude/skills/file-justification.md`

**Placement**: Python → `$PROJECT_ROOT/` | Scripts → `scripts/` | Tests → `$PROJECT_ROOT/tests/` | No `_v2`, `_new`, `_backup` files

**Deletion**: NEVER delete unrelated content from origin/main
- Task-related only: Integration > Modification > Deletion
- Before deleting: Search imports → Fix references → Verify dependencies → Delete
- NEVER: LLM prompts/schemas, user docs, mass cleanup without approval
- When in doubt: ASK first

## Critical Rules

| Rule | Requirement |
|------|-------------|
| **NO UNRELATED DELETIONS** | **NEVER delete content from origin/main unrelated to current task** |
| **CI test failures are BLOCKERS** | **ALL failing tests in PRs must be fixed - NEVER merge with failing CI checks** |
| **Character creation modal exit** | **User cannot exit character creation until selecting specific planning_block choice** (see `.claude/skills/character-creation-modal-exit.md`) |
| **GEMINI 3 CODE EXECUTION ONLY** | **FORBIDDEN: NEVER suggest switching gemini-3-flash-preview to two-phase strategy or retrying. Code execution mode is REQUIRED. Fix root causes (system instruction size), NOT workarounds.** |
| No false checkmarks | Only for 100% complete |
| Test failures | Fix ALL, no excuses, no "pre-existing" excuses |
| Solo dev context | No enterprise advice |
| Integration verification | Config + Trigger + Log evidence (see `.claude/skills/integration-verification.md`) |
| No fake code | Audit existing first |
| Code centralization | Search existing code before writing new (see `.claude/skills/code-centralization.md`) |
| Timeout integrity | 10min/600s across all layers |
| WorldAI campaign LLM test waits | Default >= 3min/180s; 30s is insufficient |
| PR merges | Never without explicit "MERGE APPROVED" |
| LLM context preservation | Never delete validation protocols from LLM prompts (see File Deletion section) |
| Beads tracking | Always include `.beads/` changes in commits/PRs; never drop or omit beads diffs. **Proactively create beads** (`bd create`) for bugs, regressions, and architectural issues discovered during work - don't wait to be asked. Update existing beads (`bd update`) as issues progress. |
| **No bash arguments** | **NEVER pass bash arguments in commands without explicit user approval** |

## PR & Merge Protocols

- Never merge PRs without explicit "MERGE APPROVED" from user
- **MANDATORY: ALL CI tests must pass before merge** - Any failing test is a blocker, no exceptions
  - `mergeable: "MERGEABLE"` only means no conflicts - does NOT mean tests pass
  - Always check `statusCheckRollup` for failing checks before declaring PR ready
  - If ANY required check shows `conclusion: "FAILURE"`, the PR is NOT ready to merge
- `/copilot` commands run autonomously FOR ANALYSIS ONLY
- `/pr` must create actual PR with working URL - never give manual steps
- Verify agent work: file existence check, `git diff --stat`, `git status`
- **See `.claude/skills/pr-workflow-manager.md`** for PR Branch Verification

### PR Description Requirements

**Required sections**: Summary (1-4 bullets, key themes) | Production Code Changes (before → now → why for each file) | Test Changes (results, evidence paths) | Known Limitations (pre-existing issues)

**Format**: `**What changed** - before → now → why` with function/variable names and rule references

**See** `.claude/skills/pr-workflow-manager.md` for complete template and examples.

## Claude Code Behavior

1. **Directory Context:** Operates in worktree directory
2. **Tests:** `TESTING_AUTH_BYPASS=true vpython` from project root (enables mock mode)
3. **Gemini SDK:** `from google import genai` (NOT `google.generativeai`)
4. **Paths:** Use `~` instead of hardcoded user paths
5. **GitHub:** MCP tools primary, `gh` CLI fallback
6. **No `_v2`, `_new`, `_backup` files** - edit existing
7. **Cross-platform:** macOS + Ubuntu compatible
8. **Use Read tool**, not bash cat/head/tail
9. **Never use `exit 1`** that terminates terminal
10. **Tools:** Serena MCP -> Read/Grep -> Edit/MultiEdit -> Bash (OS only)
11. **TodoWrite:** Required for 3+ steps
12. **Slash commands:** `.claude/commands/*.md` - execute immediately

## Diagnostic Efficiency

**Config debugging**: Read source code first (Read tool on consuming file), not exploratory Bash. Max 3 diagnostic attempts before reassessing.

**Env vars**: Set via Cloud Run/Docker/shell profile (NOT `.env` files). Check consuming code for exact names (e.g., `VITE_*` prefix for frontend).

**Grep tool**: Use `Grep` tool for code search, not `grep`/`rg` in Bash (except piping command output).

## Project Overview

Your Project = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack:** Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

**Work Approach:** Clarify before acting | User instructions = law | Focus on primary goal

**Testing Methodology:** Red-green (`/tdd` or `/rg`): Write failing tests -> Confirm fail -> Minimal code to pass -> Refactor

### MCP CLI JSON Piping

**CRITICAL**: Use `printf` or `cat`, NOT `echo` (adds `\n` that breaks parsing)
- ✅ `printf '{"key":"value"}' | mcp-cli call tool -`
- ✅ `cat file.json | mcp-cli call tool -`
- ❌ `echo '{"key":"value"}' | mcp-cli call tool -`

## Development Guidelines

### Code Standards
- **Principles:** SOLID, DRY | **Templates:** Use existing patterns | **Validation:** `isinstance()` checks
- **Constants:** Module-level (>1x) or constants.py (cross-file) | **Imports:** Module-level only, NO inline/try-except
- **Path Computation:** Use `os.path.dirname()`, `os.path.join()`, `pathlib.Path` | NEVER `string.replace()` for paths
- **Comments:** No PR/bead/ticket-specific references in production code comments or docstrings (e.g., "Bead xyz-123", "PR #456"). Write comments that explain *why* for future readers, not *when* or *which ticket*. Ticket references belong in git commit messages and PR descriptions only.

### Security
- **Subprocess:** `shell=False, timeout=30` | Never shell=True with user input
- **GitHub Actions:** SHA-pinned versions only

### Testing & Logging
- **See** `.claude/skills/testing-infrastructure.md` (test utilities, debug protocol, CI/local parity)
- **See** `.claude/skills/unified-logging.md` (logging_util - MANDATORY in `$PROJECT_ROOT/`)
- **Evidence review mandatory**: Read artifacts with skeptical verification, surface warnings/mismatches

**TDD Evidence**: RED (iteration_001, bug present) → GREEN (iteration_002, bug fixed) → REFACTOR (centralize). Compare iterations to verify fix and check regressions.

### Import Standards
**CRITICAL: These are enforced by CI with the `import-validation` check**

- **FORBIDDEN (IMP001)**: try/except around imports
  - ❌ WRONG: `try: import foo except: pass`
  - ✅ CORRECT: `import foo` at module level
  - Reason: Fail fast if dependencies missing

- **FORBIDDEN (IMP002)**: Inline imports inside functions/classes
  - ❌ WRONG: `def test(): from foo import bar`
  - ✅ CORRECT: `from foo import bar` at top of file
  - Reason: Import violations cause CI failures

- **MANDATORY**: All imports at module level - top of file only
  - Standard library imports first
  - Third-party imports second
  - Local/project imports last
  - Alphabetically sorted within each group

**CI Enforcement:** Delta validation checks changed files only. Fix violations before merge.

## Agent Communication (MCP Mail)

**Registration**: `printf '{"project_key":"...","agent_name":"..."}' | mcp-cli call mcp_mail/register_agent -`

**Messaging**: Use `cat /tmp/msg.json | mcp-cli call mcp_mail/send_message -` (prepare JSON file first)

**Use cases**: TDD validation, code review, evidence validation, multi-agent collaboration

**Best practices**: Use `cat`/`printf` (not `echo`), include PR#/commits/beads, set `ack_required: true` for critical validations

## Git Workflow

- Main = Truth | All changes via PRs | Fresh branches from main
- Push: `git push -u origin branch-name`
- `GITHUB_TOKEN` env var | GitHub Actions: SHA-pinned versions only
- **FORBIDDEN:** Merging any branch directly to main without a PR
- **FORBIDDEN:** `git sparse-checkout` commands — never enable sparse checkout on any branch or worktree

## GitHub CLI (gh) - Quick Install

**If gh CLI not installed**, download from GitHub releases:
```bash
curl -sL https://github.com/cli/cli/releases/download/v2.40.1/gh_2.40.1_linux_amd64.tar.gz | tar -xz -C /tmp
mkdir -p ~/.local/bin && cp /tmp/gh_2.40.1_linux_amd64/bin/gh ~/.local/bin/
~/.local/bin/gh auth status  # Verify (uses GITHUB_TOKEN automatically)
```
**See `.claude/skills/github-cli-reference.md`** for full command reference.

## Environment

- Firebase: `~/serviceAccountKey.json` -> `GOOGLE_APPLICATION_CREDENTIALS`
- Hooks: `.claude/settings.json` | Scripts: `.claude/hooks/`
- Python: Verify venv, run with `vpython`
- Temp files: Use `mktemp`, never predictable `/tmp/` names

## Operations Guide

**Tool Hierarchy:** Serena MCP -> Read/Grep -> Edit/MultiEdit -> Bash (OS only)

**Test Execution:**
- **DO NOT** run `./run_tests.sh` without arguments (runs ALL tests = too slow).
- **ALWAYS** run specific test files: `./run_tests.sh $PROJECT_ROOT/tests/test_feature.py`
- **Use CI** for full regression testing.
- **ALWAYS print evidence bundle path** after running `testing_mcp/` tests:
  - Path pattern: `/tmp/your-project.com/<branch>/<test_name>/latest/`
  - Example: `/tmp/your-project.com/fix/faction-settings-persistence/faction_settings_real/latest/`
- **testing_mcp and testing_ui tests:** Run directly with `python3 testing_mcp/...` or `python3 testing_ui/...`, NOT via pytest. Use `python3 $PROJECT_ROOT/main.py testui` for browser tests. These test classes have `if __name__ == "__main__"` blocks for standalone execution.

**Context Limits:** 500K (Enterprise) / 200K (Paid) | Health: Green (0-30%) | Yellow (31-60%) | Orange (61-80%) | Red (81%+)

**Data defense:** Use `dict.get()` and validate all data structures before use.

## Orchestration

- tmux sessions with dynamic task agents
- Never execute orchestration tasks yourself - delegate to agents
- `/orch` prefix -> immediate tmux delegation | `/converge` -> autonomous until goal achieved

## Slash Commands

- `/fake3` - Runs pre-commit check pipeline
- **Architecture:** `.claude/commands/*.md` = executable prompt templates

## Dangerous Command Safety

**NEVER suggest:** `sudo chown -R $USER:$(id -gn) $(npm -g config get prefix)` or recursive chown on system directories.

**Safe npm fix:** `mkdir ~/.npm-global && npm config set prefix ~/.npm-global`

## Quick Reference

```bash
vpython $PROJECT_ROOT/test_file.py               # Single test
./run_tests.sh $PROJECT_ROOT/tests/test_app.py   # Run specific tests
/fake3                                       # Pre-commit check
./integrate.sh                               # New branch
./deploy.sh [stable]                         # Deploy
```

## Meta-Rules

**Pre-action checkpoint:** Does this violate CLAUDE.md rules?
**Write gate:** Search existing files -> Attempt integration -> Document why impossible

## Skill Files Reference

For detailed procedures, see `.claude/skills/`:
- `agents.md` - Agent routing, modal locks, stale flag guards
- `llm-prompt-engineering.md` - LLM prompt guidelines, JSON schemas
- `file-justification.md` - File creation/modification protocol
- `code-centralization.md` - Code reuse and centralization
- `integration-verification.md` - Three Evidence Rule
- `testing-infrastructure.md` - Test utilities, debug protocol, CI/local parity
- `unified-logging.md` - logging_util usage
- `github-cli-reference.md` - gh CLI installation and commands
- `pr-workflow-manager.md` - PR workflows, branch verification
- `dice-authenticity-standards.md` - Code execution evidence fields, Firestore queries
