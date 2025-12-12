# CLAUDE.md - Primary Rules and Operating Protocol

## Mandatory Greeting Protocol
**Every response must begin with:** `Genesis Coder, Prime Mover,`
**Every response must end with:** `[Local: <branch> | Remote: <upstream> | PR: <number> <url>]`

## Cerebras-First Coding Protocol
| Scope | Handler |
|-------|---------|
| Small edits ≤10 lines | Claude directly |
| Larger tasks >10 lines | `/cerebras` command |

**Workflow:** Claude analyzes → `/cerebras` generates → Claude verifies

## File Protocols

**Default: NO NEW FILES** - Prove why integration is impossible.
- Integration hierarchy: existing file → utility → `__init__.py` → test file → LAST RESORT: new file
- Document each PR file: GOAL, MODIFICATION, NECESSITY, INTEGRATION PROOF
- Placement: Python → `mvp_site/`, Scripts → `scripts/`, Tests → `mvp_site/tests/`
- Never gitignore `.beads/` | Never touch `~/.claude/projects/`

## Critical Rules

| Rule | Requirement |
|------|-------------|
| No false ✅ | Only for 100% complete |
| Test failures | Fix ALL, no excuses |
| No "pre-existing" excuses | Fix ALL broken tests vs origin/main |
| No fake code | Audit existing first |
| Timeout integrity | 10min/600s across all layers |
| PR merges | Never without explicit "MERGE APPROVED" |

## No Pre-Existing Issues Policy
**CRITICAL:** Every test failure vs `origin/main` must be fixed. Green CI is a hard requirement. The phrase "pre-existing issue" is BANNED.

## Claude Code Behavior
1. Tests: `TESTING=true vpython` from project root
2. Gemini SDK: `from google import genai`
3. GitHub: MCP tools primary, `gh` CLI fallback
4. No `_v2`, `_new`, `_backup` files - edit existing
5. Cross-platform: macOS + Ubuntu compatible
6. Use Read tool, not bash cat/head/tail
7. Never use `exit 1` that terminates terminal

## Project Overview
WorldArchitect.AI = AI-powered tabletop RPG platform (D&D 5e GM)
**Stack:** Python 3.11/Flask | Gemini API | Firebase | Vanilla JS/Bootstrap | Docker/Cloud Run

## Development Guidelines

**Code:** SOLID, DRY | `isinstance()` validation | Module-level imports only
**Paths:** `os.path.dirname()`, `os.path.join()`, `pathlib.Path` (never string.replace())
**Security:** `shell=False, timeout=30` | Never shell=True with user input
**Testing:** Run ALL tests, fix ALL failures: `./run_tests.sh` | `./run_ui_tests.sh mock`

### MCP Smoke Tests
```bash
MCP_SERVER_URL="https://..." MCP_TEST_MODE=real node scripts/mcp-smoke-tests.mjs
```

## Git Workflow
- Main = Truth | All changes via PRs | Fresh branches from main
- `GITHUB_TOKEN` env var for all operations
- GitHub Actions: SHA-pinned versions only (not `@v4`, `@main`)

## Environment
- GCP: worldarchitecture-ai (754683067800)
- Firebase: `~/serviceAccountKey.json` → `GOOGLE_APPLICATION_CREDENTIALS`
- Hooks: `.claude/settings.json` | Scripts: `.claude/hooks/`
- Python: Verify venv, run with `TESTING=true vpython`
- Temp files: Use `mktemp`, never predictable `/tmp/` names

## Operations Guide

**Tool Hierarchy:** Serena MCP → Read/Grep → Edit/MultiEdit → Bash (OS only)
**TodoWrite:** Required for 3+ steps
**Slash commands:** `.claude/commands/*.md` - execute immediately, never ask permission

## PR Comments
Status: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED
Every comment gets implementation OR explicit "NOT DONE: [reason]"
Labels - Type: bug, feature, improvement | Size: small <100, medium 100-500, large 500-1000, epic >1000

## Quick Reference
```bash
TESTING=true vpython mvp_site/test_file.py  # Single test
./run_tests.sh                               # All tests
/fake3                                       # Pre-commit check
./integrate.sh                               # New branch
./deploy.sh [stable]                         # Deploy
```
