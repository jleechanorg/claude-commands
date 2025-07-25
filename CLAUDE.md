# ⚠️ REFERENCE ONLY - DO NOT USE DIRECTLY

**WARNING**: This is a reference export from a specific project setup. These configurations:
- May contain project-specific paths and settings
- Have not been tested in isolation
- May require significant adaptation for your environment
- Include setup-specific assumptions and dependencies

Use this as inspiration and reference, not direct implementation.

---

# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on Your Project**

## 🚨 CRITICAL: MANDATORY BRANCH HEADER PROTOCOL

**EVERY SINGLE RESPONSE MUST END WITH THIS HEADER - NO EXCEPTIONS:**

```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

**Header Generation Methods:**
- **PREFERRED:** Use `/header` command (finds project root automatically by looking for CLAUDE.md)
- **Manual:** Run individual commands:
  - `git branch --show-current` - Get local branch
  - `git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "no upstream"` - Get remote
  - `gh pr list --head $(git branch --show-current) --json number,url` - Get PR info

**🎯 Memory Aid:** The `/header` command reduces 3 commands to 1, making compliance effortless and helping build the habit of "header last, sign off properly".

**Examples:**
- `[Local: main | Remote: origin/main | PR: none]`
- `[Local: feature-x | Remote: origin/main | PR: #123 https://github.com/user/repo/pull/123]`

**❌ NEVER SKIP THIS HEADER - USER WILL CALL YOU OUT IMMEDIATELY**

**🚨 POST-RESPONSE CHECKPOINT**: Before submitting ANY response, ask:
1. "Did I include the mandatory branch header at the END?"
2. "Does this violate any other rules in CLAUDE.md?"

**🚨 HEADER PR CONTEXT TRACKING**: Header must reflect actual work context, not just mechanical branch matching
- ❌ NEVER show "PR: none" when work is related to existing PR context
- ✅ ALWAYS consider actual work context when determining PR relevance
- ✅ If working on feature related to PR #X, header should reference PR #X even if branch name differs
- 🔍 Evidence: Recurring pattern of "PR: none" when user expects PR context to be tracked
- ⚠️ This is a critical attention to detail compliance issue

🚨 **COPILOT COMMAND AUTONOMOUS OPERATION**: ⚠️ MANDATORY
- ✅ `/copilot` commands operate autonomously without user approval prompts
- ✅ ALWAYS proceed with full analysis regardless of conflicts/issues detected  
- ✅ Claude should automatically apply fixes and resolve issues without asking
- ✅ Continue workflow through conflicts, CI failures, or other blockers
- ❌ NEVER stop workflow for user confirmation during `/copilot` execution
- ❌ No "proceed anyway?" or "continue with analysis?" prompts
- **Purpose**: `/copilot` is designed for autonomous PR analysis and fixing

## 🚨 Orchestration System - WIP PROTOTYPE

**Multi-Agent Task Delegation System** - Active development prototype with verified success metrics:

**Architecture**: 
- tmux-based agents (frontend, backend, testing, opus-master) with Redis coordination
- A2A (Agent-to-Agent) communication protocols for autonomous task routing
- Specialized agent workspaces with capability-based assignment algorithms

**Usage**: 
- `/orch [task]` for autonomous delegation, proven cost: $0.003-$0.050/task
- `/orch monitor agents` for system health and task progress monitoring
- Direct tmux attachment for agent debugging and workspace inspection

**Proven Workflows**:
- Task creation → agent assignment → execution → PR creation with end-to-end verification
- Complex multi-step development tasks with automatic conflict resolution
- Cost-effective scaling for parallel development workstreams

**Requirements**: 
- Redis server for coordination and task queuing
- tmux for session isolation and agent workspace management  
- Python venv with specialized dependencies per agent type
- GitHub integration for automated PR workflows

**Status**: Active development prototype - successful task completion verified with PR generation and merge tracking.

## Legend
🚨 = CRITICAL | ⚠️ = MANDATORY | ✅ = Always/Do | ❌ = Never/Don't | → = See reference | PR = Pull Request

## Project Overview

Your Project = AI-powered development platform

**Stack**: Adapt to your technology stack | API integrations | Database | Frontend framework | Deployment platform

**Docs**: → Update with your project documentation structure
- Documentation map → Your docs organization
- Quick reference → Your command reference
- Progress tracking → Your progress tracking system
- Directory structure → Your project structure
- **AI Assistant Guide**: → Your AI integration guide
- **Architecture Overview**: → Your system architecture documentation

## Core Principles & Interaction

**Work Approach**:
Clarify before acting | User instructions = law | ❌ delete without permission | Leave working code alone |
Focus on primary goal | Propose before implementing | Summarize key takeaways | Externalize all knowledge

**Branch Protocol**: → See "Git Workflow" section

**Response Modes**: Default = structured for complex | Direct for simple | Override: "be brief"

**Rule Management**:
"Add to rules" → CLAUDE.md | Technical lessons → lessons.mdc | General = rules | Specific = lessons

**Development Protocols**: → Your development protocols documentation

**Edit Verification**: `git diff`/`read_file` before proceeding | Additive/surgical edits only

**Testing**: Red-green methodology | Test truth verification | UI = test experience not code | Use ADTs

**Red-Green Protocol** (`/tdd` or `/rg`):
1. Write failing tests FIRST → 2. Confirm fail (red) → 3. Minimal code to pass (green) → 4. Refactor

🚨 **Testing Standards**: → See "Testing Protocol" section for complete rules

## Development Guidelines

### Code Standards
**Principles**: SOLID, DRY | **Templates**: Use existing code patterns | **Validation**: `isinstance()` checks
**Constants**: Module-level (>1x) or constants.py (cross-file) | **Imports**: Module-level only, NO inline/try-except
**Path Computation**: ✅ Use `os.path.dirname()` to retrieve the parent directory of a file path | ✅ Use `os.path.join()` for constructing paths | ✅ Use `pathlib.Path` for modern path operations | ❌ NEVER use `string.replace()` for paths

### Feature Compatibility
**Critical**: Audit integration points | Update filters for new formats | Test object/string conversion
**Always Reuse**: Check existing code | Extract patterns to utilities | No duplication
**Organization**: Imports at top (stdlib → third-party → local) | Extract utilities | Separate concerns
**No**: Inline imports, temp comments (TODO/FIXME), hardcoded strings | Use descriptive names

### Development Practices
`tempfile.mkdtemp()` for test files | Verify before assuming | ❌ unsolicited refactoring |
**Logging**: ✅ Use project logging utility | ❌ Import standard logging directly | Use project's unified logging
Use docstrings, proper JS loading

### Quality Standards
**Files**: Descriptive names, <500 lines | **Tests**: Natural state, visual validation, dynamic discovery
**Validation**: Verify PASS/FAIL detection | Parse output, don't trust exit codes | Stop on contradictions

### 🚨 Testing Protocol
**Zero Tolerance**: Run ALL tests before completion | Fix ALL failures | No "pre-existing issues" excuse
**Commands**: Your test runner commands | Your UI test commands | Your integration test commands
**Protocol**: STOP → FIX → VERIFY → EVIDENCE → Complete

### Safety & Security
❌ Global `document.addEventListener('click')` without approval | Test workflows after modifications |
Document blast radius | Backups → `tmp/` | ❌ commit if "DO NOT SUBMIT" | Analysis + execution required

## Git Workflow

### Core Rules
🚨 **No Main Push**: ✅ `git push origin HEAD:feature` | ❌ `git push origin main`
- **ALL changes require PR**: Including roadmap files, documentation, everything
- **Fresh branches from main**: Always create new branch from latest main for new work

🚨 **Branch Protection**: ❌ NEVER switch without explicit request | ✅ Create descriptive branches

🚨 **PR Workflow**: All changes via PRs | `gh pr create` + test results in description

🚨 **Upstream Tracking**: Set tracking to avoid "no upstream" in headers
- `git push -u origin branch-name` OR `git branch --set-upstream-to=origin/branch-name`

## Environment, Tooling & Scripts

1. **Python venv**: Verify activated before running Python/tests | If missing/corrupted → Your setup documentation
2. **Robust Scripts**: Make idempotent, work from any subdirectory
3. **Automation Setup Scripts**: Single setup script with validation, logging, health checks for production systems
4. **Python Execution**: ✅ Run from project root | ❌ cd into subdirs
5. **Test Execution**: Your testing framework and commands
6. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted
7. **Web Scraping**: Use full-content tools (curl) not search snippets

## Slash Commands

**Full Documentation**: → `.claude/commands/` | Use `/list` for available commands

### Command Classification (Dual Architecture)

**🧠 Cognitive Commands** (Semantic Composition):
- `/think`, `/arch`, `/debug` - Modify thinking approach, compose naturally
- `/learn` - Capture structured technical learnings with Memory MCP integration
- `/analyze` - Deep analysis with memory context enhancement
- `/fix` - Problem resolution with memory-guided solutions
- **Behavior**: Automatic semantic understanding and tool integration

**⚙️ Operational Commands** (Protocol Enforcement):  
- `/headless`, `/handoff`, `/orchestrate` - Modify execution environment
- **Behavior**: Mandatory workflow execution before task processing

**🔧 Tool Commands** (Direct Execution):
- `/execute`, `/test`, `/pr` - Direct task execution
- **Behavior**: Immediate execution with optional parameters

### Critical Enforcement
🚨 **SLASH COMMAND PROTOCOL RECOGNITION**: ⚠️ MANDATORY - Before processing ANY slash command:
- ✅ **Recognition Phase**: Scan input for "/" → Identify command type → Look up required workflow
- ✅ **Execution Phase**: Follow COMPLETE documented workflow → No partial execution allowed
- ✅ **Verification Phase**: Confirm all protocol steps completed before declaring task done
- ❌ NEVER treat slash commands as content suggestions - they are execution mandates

## Quick Reference

- **Test**: Your test command patterns
- **Integration**: Your integration test commands
- **New Branch**: Your branch creation workflow
- **All Tests**: Your comprehensive test suite command
- **Deploy**: Your deployment commands

---

**⚠️ ADAPTATION REQUIRED**: This is a reference implementation. Adapt all commands, paths, and configurations to your specific project environment and requirements.