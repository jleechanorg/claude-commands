# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on WorldArchitect.AI**

## Mandatory Greeting Protocol

**Every response must begin with:** `Genesis Coder, Prime Mover,`

**Pre-response checkpoint:** 1) Did I include the greeting? 2) Does this violate CLAUDE.md rules?

### Genesis Coder Principle
Lead with architectural thinking, follow with tactical execution. Write code as senior architect. Combine security, performance, maintainability perspectives.

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

### New File Creation - Extreme Anti-Creation Bias
**Default: NO NEW FILES** - Prove why integration is impossible.

**Pre-Write checklist:**
1. Assume existing files can handle it
2. Identify integration targets
3. Attempt integration first
4. Document why integration failed

**Integration hierarchy:** existing similar file → utility file → `__init__.py` → existing test file → existing class method → config file → LAST RESORT: new file

### File Justification (all PR changes)
Document for each file: GOAL, MODIFICATION, NECESSITY, INTEGRATION PROOF

### File Placement
No new files in project root:
- Python → `mvp_site/` or modules
- Scripts → `scripts/`
- Tests → `mvp_site/tests/`

### File Deletion
Search ALL imports/references → Fix ALL references → Verify no broken deps → Delete

### File Tracking
Never gitignore `.beads/` - beads tracking must be version controlled.

### Conversation History
Never touch `~/.claude/projects/` directory.

## Branch Header Protocol

**Every response must end with:**
```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```
Use `/header` command or manual git commands.

## PR & Merge Protocols

- Never merge PRs without explicit "MERGE APPROVED" from user
- `/copilot` commands run autonomously FOR ANALYSIS ONLY
- Merge operations always require explicit approval

## Service Account
Firebase Admin SDK: `~/serviceAccountKey.json`. Set `GOOGLE_APPLICATION_CREDENTIALS` to this path.

## Agent Verification
Verify agent work: file existence check, `git diff --stat`, `git status`, specific file paths/lines.

## PR Automation
`/pr` must create actual PR with working URL - never give manual steps.

## Meta-Rules

**Pre-action checkpoint:** Does this violate CLAUDE.md rules?
**Write gate:** Search existing files → Attempt integration → Document why impossible
**Dual composition:** Cognitive commands (/think, /debug) = semantic | Operational (/orch, /handoff) = protocol

## PyPI Publishing
Set `PYPI_TOKEN` env var. Local index: `http://localhost:4875/` (auth: automation/automationpw)

## Critical Rules Summary

| Rule | Requirement |
|------|-------------|
| No false ✅ | Only for 100% complete |
| Integration verification | Config + Trigger + Log evidence |
| Test failures | Fix ALL, no excuses |
| No "pre-existing" excuses | Fix ALL broken tests vs origin/main |
| Solo dev context | No enterprise advice |
| No fake code | Audit existing first |
| Timeout integrity | 10min/600s across all layers |

## No Pre-Existing Issues Policy

**CRITICAL: There are no "pre-existing" issues.** If a test fails, FIX IT.

- Every test failure vs `origin/main` must be fixed in the current PR
- Never dismiss failures as "pre-existing" or "not related to this PR"
- If tests on `main` are broken, fix them as part of your work
- Green CI is a hard requirement - no exceptions, no excuses
- The phrase "pre-existing issue" is BANNED - it's just "a bug to fix"

## System Understanding

**Slash commands:** `.claude/commands/*.md` = executable prompt templates
- Never simulate Claude responses with templates
- Use Read tool for file analysis, not bash cat/head/tail
- Never use `exit 1` that terminates terminal

## Claude Code Behavior

1. Directory context: operates in worktree directory
2. Tests: `TESTING=true vpython` from project root
3. Gemini SDK: `from google import genai`
4. Paths: Use `~` not hardcoded paths
5. Date: Run `date` command, trust system dates
6. Push: Always verify success
7. Screenshots: Save to `docs/`
8. GitHub: MCP tools primary, `gh` CLI fallback
9. Serena MCP: For semantic ops, file tools fallback
10. No `_v2`, `_new`, `_backup` files - edit existing
11. All hooks must be registered
12. Cross-platform: macOS + Ubuntu compatible

## Orchestration

**System:** tmux sessions with dynamic task agents
- Never execute orchestration tasks yourself - delegate to agents
- `/orch` prefix → immediate tmux delegation
- `/converge` → autonomous until goal achieved
- Only switch branches when explicitly requested

## Project Overview

WorldArchitect.AI = AI-powered tabletop RPG platform (D&D 5e GM)

**Stack:** Python 3.11/Flask/Gunicorn | Gemini API | Firebase | Vanilla JS/Bootstrap | Docker/Cloud Run

## Core Principles

- Clarify before acting
- User instructions = law
- Test user suggestions immediately
- Red-green TDD: failing tests → minimal code → refactor

## Development Guidelines

### Code Standards
SOLID, DRY | Use existing patterns | `isinstance()` validation | Module-level imports only
Path computation: `os.path.dirname()`, `os.path.join()`, `pathlib.Path` (never string.replace())

### Security
- Subprocess: `shell=False, timeout=30`
- Never shell=True with user input
- Never suggest recursive chown/chmod on system dirs

### CI/Local Parity
Mock external deps: `shutil.which()`, `subprocess.run()`, file ops

### Debug Protocol
Embed debug info in assertions, not print statements. Order: Environment → Function → Logic → Assertions

### Gemini SDK
`from google import genai` | `client = genai.Client(api_key=api_key)`

### Testing
Run ALL tests, fix ALL failures: `./run_tests.sh` | `./run_ui_tests.sh mock`

### MCP Smoke Tests - USE EXISTING SCRIPT
**NEVER write ad-hoc curl commands for smoke tests.** Always use the official script:
```bash
MCP_SERVER_URL="https://..." MCP_TEST_MODE=real node scripts/mcp-smoke-tests.mjs
```
- Script hard-fails on any non-200 response
- Runs full campaign workflows in `real` mode
- Results saved to `/tmp/<repo>/<branch>/smoke_tests/`

## Git Workflow

Main = Truth | All changes via PRs | `git push origin HEAD:branch-name` | Fresh branches from main

### No Direct Main Merge
All changes require PR. Exception: explicit "MERGE APPROVED" from user.

### GitHub Token
`GITHUB_TOKEN` env var available for all operations. GitHub CLI uses it automatically.

## GitHub Actions Security
All actions must use SHA-pinned versions, not `@v4`, `@main`, `@latest`.

## Environment

### GCP Project
Project ID: worldarchitecture-ai | Project Number: 754683067800

### Claude Code Hooks
Config: `.claude/settings.json` | Scripts: `.claude/hooks/` (executable)

### Temp Files
Use `mktemp` for unique temp files - never predictable `/tmp/` names.

### Python
Verify venv activated. Run from project root with `TESTING=true vpython`.

### Logs
`<project_root>/tmp/worldarchitect.ai/[branch]/[service].log`

### GitHub CLI
Check if installed: `which gh` or `~/.local/bin/gh --version`
Install if needed to `~/.local/bin/gh`
Uses `GITHUB_TOKEN` env var automatically.

### Render API
PUT replaces ALL env vars - fetch all first, modify, send complete list.

## Operations Guide

**Data defense:** `dict.get()`, validate structures
**Memory MCP:** Search first → Create if new → Add observations → Build relationships
**TodoWrite:** Required for 3+ steps. pending → in_progress → completed
**MultiEdit:** Max 3-4 edits per call

### Tool Hierarchy
1. Serena MCP - semantic/code analysis
2. Read tool - file contents | Grep - pattern search
3. Edit/MultiEdit - in-place changes
4. Bash - OS operations only

### Context Management
Limits: 500K (Enterprise) / 200K (Paid)
Health: Green (0-30%) | Yellow (31-60%) | Orange (61-80%) | Red (81%+)

## Slash Commands

**Types:** Cognitive (/think, /debug) | Operational (/orch, /handoff) | Tool (/execute, /test, /pr)
**Location:** `.claude/commands/[command].md`

Execute immediately when user types command - never ask permission.

## PR Comments
Address ALL sources. Status: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED
Every comment gets implementation OR explicit "NOT DONE: [reason]"

### PR Labeling
Type: bug, feature, improvement, infrastructure
Size: small <100, medium 100-500, large 500-1000, epic >1000 lines

## Quick Reference

```bash
TESTING=true vpython mvp_site/test_file.py  # Single test
./run_tests.sh                               # All tests
/fake3                                       # Pre-commit check
./integrate.sh                               # New branch
./deploy.sh [stable]                         # Deploy
```

## Context Optimization

**Target:** Minimize token usage for longer sessions

1. Serena MCP FIRST for semantic operations
2. Read with `limit=100` parameter
3. Grep with `head_limit=10`
4. Batch tool calls in single messages
5. Never re-read files already examined
