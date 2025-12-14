# CLAUDE.md - Primary Rules and Operating Protocol

## Mandatory Greeting Protocol
**Every response must begin with:** `Genesis Coder, Prime Mover,`
**Every response must end with:** `[Local: <branch> | Remote: <upstream> | PR: <number> <url>]`

**Pre-response checkpoint:** 1) Did I include the greeting? 2) Does this violate CLAUDE.md rules?

### Genesis Coder Principle
Lead with architectural thinking, follow with tactical execution. Write code as senior architect. Combine security, performance, maintainability perspectives.

## LLM Architecture Principles

### Core Rule: LLM Decides, Server Executes
For any AI-driven feature (dice rolls, game decisions, content generation):
- **LLM gets full context** - Never strip information to "optimize"
- **LLM makes decisions** - Don't pre-compute what the LLM should decide
- **Server executes actions** - Tools, dice rolls, state changes happen server-side
- **LLM incorporates results** - Final output uses real data from tool execution

### Anti-Patterns (BANNED)
- Keyword-based intent detection to bypass LLM judgment
- Stripping tool definitions based on predicted need
- Pre-computing results the LLM should request
- "Optimizations" that reduce information available to the LLM

### Session Context Evaluation
When resuming from prior sessions or inheriting TODOs:
- **Evaluate inherited work** against these principles before executing
- "Not implemented" ≠ "should be implemented"
- Ask: Does this make the LLM smarter or dumber?
- Challenge assumptions from summaries - they may contain bad ideas

## Cerebras-First Coding Protocol

**Default for all coding: Use Cerebras API for most tasks**

| Scope | Handler |
|-------|---------|
| Small edits ≤10 lines | Claude directly |
| Larger tasks >10 lines | `/cerebras` command |
| New features/classes | Cerebras |
| File creation | Cerebras |

**Workflow:** Claude analyzes → Claude creates specs → `/cerebras` generates → Claude verifies

## File Protocols

**Default: NO NEW FILES** - Prove why integration is impossible.
- Integration hierarchy: existing file → existing class method → utility file → config file → `__init__.py` → test file → LAST RESORT: new file
- Document each PR file: GOAL, MODIFICATION, NECESSITY, INTEGRATION PROOF
- Placement: Python → `mvp_site/`, Scripts → `scripts/`, Tests → `mvp_site/tests/`
- Never gitignore `.beads/` | Never touch `~/.claude/projects/`

### Critical File Deletion Protocol
**MANDATORY:** Before deleting any file, you MUST:
1. **Search ALL imports/references** to the file throughout the codebase.
2. **Fix ALL references** (update, remove, or refactor as needed).
3. **Verify no broken dependencies** (run tests, check for errors).
4. **Delete** the file ONLY after all above steps are complete.
Skipping any step is strictly prohibited.

## Critical Rules

| Rule | Requirement |
|------|-------------|
| No false ✅ | Only for 100% complete |
| Test failures | Fix ALL, no excuses |
| No "pre-existing" excuses | Fix ALL broken tests vs origin/main |
| Solo dev context | No enterprise advice |
| Integration verification | Config + Trigger + Log evidence |
| No fake code | Audit existing first |
| Timeout integrity | 10min/600s across all layers |
| PR merges | Never without explicit "MERGE APPROVED" |

**Enforcement:** Phrase "pre-existing issue" is banned; fix all failures relative to `origin/main`.

## Claude Code Behavior
1. Tests: `TESTING=true vpython` from project root
2. Gemini SDK: `from google import genai`
3. GitHub: MCP tools primary, `gh` CLI fallback
4. No `_v2`, `_new`, `_backup` files - edit existing
5. Cross-platform: macOS + Ubuntu compatible
6. Use Read tool, not bash cat/head/tail
7. Never use `exit 1` that terminates terminal
8. Run `date`; trust system time
9. Always verify success after push
10. All hooks must be registered
11. **Tools:** Serena MCP → Read/Grep → Edit/MultiEdit → Bash (OS only)
12. **TodoWrite:** Required for 3+ steps
13. **Slash commands:** `.claude/commands/*.md` - execute immediately

## Project Overview
WorldArchitect.AI = AI-powered tabletop RPG platform (D&D 5e GM)
**Stack:** Python 3.11/Flask/Gunicorn | Gemini API | Firebase | Vanilla JS/Bootstrap | Docker/Cloud Run

## Development Guidelines

**Code:** SOLID, DRY | `isinstance()` validation | Module-level imports only
**Paths:** `os.path.dirname()`, `os.path.join()`, `pathlib.Path` (never string.replace())
**Security:** `shell=False, timeout=30` | Never shell=True with user input
**Testing:** Run ALL tests, fix ALL failures: `./run_tests.sh` | `./run_ui_tests.sh mock`
**CI/Local Parity:** Mock external deps (`shutil.which()`, `subprocess.run()`, file ops); never rely on system state.

## Debug Protocol
- **Embed debug info in assertions, not print statements.**
- **Debugging order:** Environment → Function → Logic → Assertions

### MCP Smoke Tests
```bash
MCP_SERVER_URL="https://..." MCP_TEST_MODE=real node scripts/mcp-smoke-tests.mjs
```
- **Script hard-fails on any non-200 response**
- **Runs full campaign workflows in real mode**
- **Results saved to `/tmp/repo/branch/smoke_tests/`**

## Git Workflow
- Main = Truth | All changes via PRs | Fresh branches from main
- Push: `git push origin HEAD:branch-name` (branch-name = feature/topic branch from main)
- `GITHUB_TOKEN` env var | GitHub Actions: SHA-pinned versions only

## Environment
- Firebase: `~/serviceAccountKey.json` → `GOOGLE_APPLICATION_CREDENTIALS`
- Hooks: `.claude/settings.json` | Scripts: `.claude/hooks/`
- Python: Verify venv, run with `TESTING=true vpython`
- Logs: All logs stored at `project_root/tmp/worldarchitect.ai/[branch]/[service].log`
- GitHub CLI (`gh`): Installed at `~/.local/bin/gh`; verify with `which gh` or `~/.local/bin/gh --version`
- Temp files: Use `mktemp`, never predictable `/tmp/` names

## Operations Guide
**Tool Hierarchy:** Serena MCP → Read/Grep → Edit/MultiEdit → Bash (OS only)

**Context Limits:**
- Limits: 500K (Enterprise) / 200K (Paid)
- Health: Green (0-30%) | Yellow (31-60%) | Orange (61-80%) | Red (81%+)

- **Data defense:** Use `dict.get()` and validate all data structures before use.
- **MultiEdit constraint:** Limit MultiEdit operations to a maximum of 3-4 edits per call.

## PR Comments
Status: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED
Every comment gets implementation OR explicit "NOT DONE: [reason]"

## Slash Commands
- `/cerebras <task>` — Primary codegen command for tasks >10 lines; runs the Cerebras workflow.
- `/fake3` — Runs the pre-commit check pipeline.

All slash commands execute from `.claude/commands/*.md`; use that directory for full parameter and behavior details.

## Quick Reference
```bash
TESTING=true vpython mvp_site/test_file.py  # Single test
./run_tests.sh                               # All tests
/fake3                                       # Pre-commit check
./integrate.sh                               # New branch
./deploy.sh [stable]                         # Deploy
```

## Related Documentation
- Extended workflows, deployment details, and troubleshooting live in the `docs/` directory; update or add focused guides there to keep this file concise.
