# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on WorldArchitect.AI**

## Mandatory Greeting Protocol

**Every response must begin with:** `Genesis Coder, Prime Mover,`

**Pre-response checkpoint:** 1) Did I include the greeting? 2) Does this violate CLAUDE.md rules?

**Every response must end with:**
```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

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
- **Disabled-by-default environment variables** - If a feature is useful, enable it by default. Never add `if os.getenv("FEATURE") == "true"` guards that require manual activation. Features requested by the user must work out of the box.

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

### Critical File Deletion Protocol
**MANDATORY:** Before deleting any file, you MUST:
1. **Search ALL imports/references** to the file throughout the codebase.
2. **Fix ALL references** (update, remove, or refactor as needed).
3. **Verify no broken dependencies** (run tests, check for errors).
4. **Delete** the file ONLY after all above steps are complete.
Skipping any step is strictly prohibited.

### File Tracking
- Never gitignore `.beads/` - beads tracking must be version controlled.
- Never touch `~/.claude/projects/` directory.

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

### No Pre-Existing Issues Policy
**CRITICAL: There are no "pre-existing" issues.** If a test fails, FIX IT.
- Every test failure vs `origin/main` must be fixed in the current PR
- Never dismiss failures as "pre-existing" or "not related to this PR"
- Green CI is a hard requirement - no exceptions, no excuses

### Integration Verification Protocol
**Three Evidence Rule** (MANDATORY for ANY integration claim):
1. **Configuration Evidence**: Show actual config file entries enabling the behavior
2. **Trigger Evidence**: Demonstrate automatic trigger mechanism (not manual execution)
3. **Log Evidence**: Timestamped logs from automatic behavior (not manual testing)

## PR & Merge Protocols

- Never merge PRs without explicit "MERGE APPROVED" from user
- `/copilot` commands run autonomously FOR ANALYSIS ONLY
- Merge operations always require explicit approval

### Agent Verification Protocol
Verify agent work: file existence check, `git diff --stat`, `git status`, specific file paths/lines.

### PR Automation
`/pr` must create actual PR with working URL - never give manual steps.

## Claude Code Behavior

1. **Directory Context:** Operates in worktree directory
2. **Tests:** `TESTING=true vpython` from project root
3. **Gemini SDK:** `from google import genai` (NOT `google.generativeai`)
4. **Paths:** Use `~` instead of hardcoded user paths
5. **GitHub:** MCP tools primary, `gh` CLI fallback
6. **Serena MCP:** For semantic ops, file tools fallback
7. **No `_v2`, `_new`, `_backup` files** - edit existing
8. **Cross-platform:** macOS + Ubuntu compatible
9. **Use Read tool**, not bash cat/head/tail
10. **Never use `exit 1`** that terminates terminal
11. **Run `date`**; trust system time
12. **Always verify success after push**
13. **All hooks must be registered**
14. **Tools:** Serena MCP → Read/Grep → Edit/MultiEdit → Bash (OS only)
15. **TodoWrite:** Required for 3+ steps
16. **Slash commands:** `.claude/commands/*.md` - execute immediately

## Project Overview

WorldArchitect.AI = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack:** Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

### Core Principles
**Work Approach:** Clarify before acting | User instructions = law | Focus on primary goal

**User Suggestion Testing:** When user suggests a solution and says "it should work", test their suggestion immediately rather than theorizing about potential issues.

**Testing Methodology:** Red-green (`/tdd` or `/rg`): Write failing tests → Confirm fail → Minimal code to pass → Refactor

## Development Guidelines

### Code Standards
**Principles:** SOLID, DRY | **Templates:** Use existing patterns | **Validation:** `isinstance()` checks
**Constants:** Module-level (>1x) or constants.py (cross-file) | **Imports:** Module-level only, NO inline/try-except
**Path Computation:** ✅ `os.path.dirname()`, `os.path.join()`, `pathlib.Path` | ❌ NEVER `string.replace()` for paths

### Security
- **Subprocess:** `shell=False, timeout=30` | Never shell=True with user input
- **GitHub Actions:** SHA-pinned versions only (❌ `@v4`, `@main` | ✅ Full SHA)

### CI/Local Parity
- Mock external deps (`shutil.which()`, `subprocess.run()`, file ops)
- Never rely on system state in tests
- Test pattern for system dependencies:
```python
with patch('shutil.which', return_value='/usr/bin/command'):
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # test code here
```

### Testing Protocol
**ZERO TOLERANCE:** Run ALL tests, fix ALL failures
```bash
./run_tests.sh            # All tests
./run_ui_tests.sh mock    # UI tests
```

### Import Standards
- ❌ **FORBIDDEN**: try/except around imports (ANY context)
- ❌ **FORBIDDEN**: inline imports inside functions
- ✅ **MANDATORY**: All imports at module level - fail fast if missing

### Gemini SDK
✅ `from google import genai` | ✅ `client = genai.Client(api_key=api_key)`

### Unified Logging (MANDATORY)
All Python files in `mvp_site/` MUST use the unified logging module. Never use `import logging` directly.

```python
# ❌ FORBIDDEN - Direct logging module
import logging
logger = logging.getLogger(__name__)
logger.info("message")

# ✅ MANDATORY - Unified logging_util
from mvp_site import logging_util
logging_util.info("message")
logging_util.warning("something concerning")
logging_util.error("something failed")
logging_util.debug("debug info")
```

**Benefits of logging_util:**
- Unified output to both GCP Cloud Logging (stdout) and local file
- Automatic log file path: `/tmp/<repo>/<branch>/<service>.log`
- Consistent emoji formatting for errors (🔥🔴) and warnings (⚠️)
- Single initialization point - no duplicate handlers

**Exceptions:** Test files (`mvp_site/tests/*`) may use direct logging.

## Debug Protocol

- **Embed debug info in assertions, not print statements.**
- **Debugging order:** Environment → Function → Logic → Assertions
- **Hypothesis testing:** Test most basic assumption first: "Does the function actually work?"

### Test Failure Debug Protocol
- ❌ NEVER use print statements for debug info (lost in CI)
- ✅ ALWAYS embed debug info in assertion messages:
```python
debug_info = f"function_result={result}, context={context}"
self.assertTrue(result, f"FAIL DEBUG: {debug_info}")
```

### MCP Smoke Tests
```bash
MCP_SERVER_URL="https://..." MCP_TEST_MODE=real node scripts/mcp-smoke-tests.mjs
```
- Script hard-fails on any non-200 response
- Runs full campaign workflows in real mode
- Results saved to `/tmp/repo/branch/smoke_tests/`

## Git Workflow

- Main = Truth | All changes via PRs | Fresh branches from main
- Push: `git push origin HEAD:branch-name` (branch-name = feature/topic branch from main)
- `GITHUB_TOKEN` env var | GitHub Actions: SHA-pinned versions only
- ❌ FORBIDDEN: Merging any branch directly to main without a PR

## GitHub CLI (gh) - Direct Binary Installation

**CRITICAL:** If gh CLI is not installed, download the precompiled binary directly from GitHub releases.

### Installation Method
```bash
# Download and extract gh CLI binary to /tmp
curl -sL https://github.com/cli/cli/releases/download/v2.40.1/gh_2.40.1_linux_amd64.tar.gz | tar -xz -C /tmp

# Verify installation
/tmp/gh_2.40.1_linux_amd64/bin/gh --version

# Authenticate using existing GitHub token
/tmp/gh_2.40.1_linux_amd64/bin/gh auth status

# Use in commands
/tmp/gh_2.40.1_linux_amd64/bin/gh pr list
/tmp/gh_2.40.1_linux_amd64/bin/gh issue list
```

### Why This Works
- GitHub releases are not blocked by container security (unlike cloud provider binaries)
- Direct binary extraction to /tmp avoids permission issues
- No package manager required (works in restricted environments)
- Fully functional with existing GITHUB_TOKEN environment variable

### Usage Pattern
```bash
# Set up alias for convenience
export GH_CLI="/tmp/gh_2.40.1_linux_amd64/bin/gh"

# Use in scripts
$GH_CLI pr create --title "Feature" --body "Description"
$GH_CLI issue create --title "Bug" --body "Details"
```

### Why Binary Downloads Don't Work
```bash
# ❌ This fails (HTTP 403):
curl https://dl.google.com/.../google-cloud-cli-linux-x86_64.tar.gz

# ✅ This works:
npm install -g @google-cloud/storage
```
**Security Reason:** The container blocks binary downloads from cloud provider domains for multi-tenant security, but trusts package registries (npm, PyPI).

### GitHub Authentication
- **GitHub CLI (local)**: Automatically uses `GITHUB_TOKEN` environment variable
- **GitHub Actions**: Use `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}`
- **Agent Access**: All agents can access `GITHUB_TOKEN` directly

## Environment

- Firebase: `~/serviceAccountKey.json` → `GOOGLE_APPLICATION_CREDENTIALS`
- Hooks: `.claude/settings.json` | Scripts: `.claude/hooks/`
- Python: Verify venv, run with `TESTING=true vpython`
- Logs: All logs stored at `project_root/tmp/worldarchitect.ai/[branch]/[service].log`
- GitHub CLI (`gh`): Check `~/.local/bin/gh` or install to `/tmp` (see above)
- Temp files: Use `mktemp`, never predictable `/tmp/` names

## Operations Guide

**Tool Hierarchy:** Serena MCP → Read/Grep → Edit/MultiEdit → Bash (OS only)

**Context Limits:**
- Limits: 500K (Enterprise) / 200K (Paid)
- Health: Green (0-30%) | Yellow (31-60%) | Orange (61-80%) | Red (81%+)

**Data defense:** Use `dict.get()` and validate all data structures before use.
**MultiEdit constraint:** Limit MultiEdit operations to a maximum of 3-4 edits per call.

## Orchestration

**System:** tmux sessions with dynamic task agents
- Never execute orchestration tasks yourself - delegate to agents
- `/orch` prefix → immediate tmux delegation
- `/converge` → autonomous until goal achieved
- Only switch branches when explicitly requested

## PR Comments

Status: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED
Every comment gets implementation OR explicit "NOT DONE: [reason]"

## Slash Commands

- `/cerebras <task>` — Primary codegen command for tasks >10 lines; runs the Cerebras workflow.
- `/fake3` — Runs the pre-commit check pipeline.

**Architecture:** `.claude/commands/*.md` = executable prompt templates
**Flow:** User types `/pushl` → Claude reads `pushl.md` → Executes implementation

All slash commands execute from `.claude/commands/*.md`; use that directory for full parameter and behavior details.

## PyPI Publishing Reference

- Set `PYPI_TOKEN` env var for `jleechanorg-pr-automation` releases
- Local private index: `http://localhost:4875/` (auth: `automation` / `automationpw`)
- Install: `pip install --index-url http://automation:automationpw@localhost:4875/simple <package>`

## Dangerous Command Safety

**❌ NEVER suggest these system-destroying commands:**
```bash
sudo chown -R $USER:$(id -gn) $(npm -g config get prefix)  # Can expand to: sudo chown -R user /usr
sudo chown -R user:group /usr /bin /sbin /lib /etc        # Makes sudo/su unusable
```

**✅ Safe npm fix:** `mkdir ~/.npm-global && npm config set prefix ~/.npm-global`
**✅ Safe file ownership:** Check first with `ls -la`, then target specific files only

## Quick Reference

```bash
TESTING=true vpython mvp_site/test_file.py  # Single test
./run_tests.sh                               # All tests
/fake3                                       # Pre-commit check
./integrate.sh                               # New branch
./deploy.sh [stable]                         # Deploy
```

## Meta-Rules

**Pre-action checkpoint:** Does this violate CLAUDE.md rules?
**Write gate:** Search existing files → Attempt integration → Document why impossible
**Dual composition:** Cognitive commands (/think, /debug) = semantic | Operational (/orch, /handoff) = protocol

## Related Documentation

- Extended workflows, deployment details, and troubleshooting live in the `docs/` directory
- Update or add focused guides there to keep this file concise
