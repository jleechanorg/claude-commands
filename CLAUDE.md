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

## Project Overview

Your Project = [Replace with your project description]

**Stack**: [Replace with your technology stack]

**Docs**: → Project documentation structure (adapt paths to your project)
- Documentation map → Project-specific documentation
- Quick reference → Project quick reference
- Progress tracking → Project progress tracking
- Directory structure → `/directory_structure.md`
- **AI Assistant Guide**: → Project architecture guide
- **📋 Project Architecture**: → Comprehensive codebase overview
- **📋 Code Review & File Responsibilities**: → Detailed file-by-file analysis

## Core Principles & Interaction

**Work Approach**:
Clarify before acting | User instructions = law | ❌ delete without permission | Leave working code alone |
Focus on primary goal | Propose before implementing | Summarize key takeaways | Externalize all knowledge

**Branch Protocol**: → See "Git Workflow" section

**Response Modes**: Default = structured for complex | Direct for simple | Override: "be brief"

**Rule Management**:
"Add to rules" → CLAUDE.md | Technical lessons → lessons.mdc | General = rules | Specific = lessons

**Development Protocols**: → Project-specific planning protocols

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
**Logging**: Use your project's unified logging system
Use docstrings, proper loading patterns

### Quality Standards
**Files**: Descriptive names, <500 lines | **Tests**: Natural state, visual validation, dynamic discovery
**Validation**: Verify PASS/FAIL detection | Parse output, don't trust exit codes | Stop on contradictions

### 🚨 Testing Protocol
**Zero Tolerance**: Run ALL tests before completion | Fix ALL failures | No "pre-existing issues" excuse
**Commands**: Adapt testing commands to your project structure
**Protocol**: STOP → FIX → VERIFY → EVIDENCE → Complete

### Safety & Security
❌ Global event listeners without approval | Test workflows after modifications |
Document blast radius | Backups → `tmp/` | ❌ commit if "DO NOT SUBMIT" | Analysis + execution required

### File Placement Rules (🚨 HARD RULE)
🚨 **NEVER add new files directly to core project directories** without explicit user permission
🚨 **Test File Policy**: Add to existing files, NEVER create new test files

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

1. **Virtual Environment**: Verify activated before running tests | Project-specific setup
2. **Robust Scripts**: Make idempotent, work from any subdirectory
3. **Test Execution**: Adapt to your project structure - `python $PROJECT_ROOT/tests/test_file.py`
4. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted

## Data Integrity & Management

1. **Data Defense**: Assume incomplete/malformed | Use safe access patterns | Validate structures
2. **Critical Logic**: Implement safeguards in code, not just prompts
3. **Single Truth**: One clear way per task | Remove conflicting rules

## Knowledge Management

### File Organization
- **CLAUDE.md**: Primary protocol
- **lessons.mdc**: Technical learnings from corrections
- **project.md**: Repository-specific knowledge base

### Process Improvement
- **5 Whys**: Root cause analysis
- **Proactive Docs**: Update rules/lessons after debugging without prompting

## Slash Commands

**Full Documentation**: → `.claude/commands/` | Use `/list` for available commands

### Command Classification

**🧠 Cognitive Commands** (Semantic Composition):
- `/think`, `/arch`, `/debug` - Modify thinking approach, compose naturally
- `/learn` - Capture structured technical learnings
- `/analyze` - Deep analysis with context enhancement
- `/fix` - Problem resolution with guided solutions

**⚙️ Operational Commands** (Protocol Enforcement):  
- `/headless`, `/handoff`, `/orchestrate` - Modify execution environment

**🔧 Tool Commands** (Direct Execution):
- `/execute`, `/test`, `/pr` - Direct task execution

## Project-Specific Adaptations Required

### Database Configuration
[Replace with your database system configuration]

### Web Framework Setup
[Replace with your web framework configuration]

### Testing Infrastructure
[Adapt testing commands to your project structure]

### Deployment Configuration
[Replace with your deployment system]

## Quick Reference

- **Test**: Adapt to your testing system
- **Integration**: Use your integration test patterns
- **New Branch**: Use your branching workflow
- **All Tests**: Use your test runner
- **Deploy**: Use your deployment system