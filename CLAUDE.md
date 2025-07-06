# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on WorldArchitect.AI**

## Legend
🚨 = CRITICAL | ⚠️ = MANDATORY | ✅ = Always/Do | ❌ = Never/Don't | → = See reference | PR = Pull Request

## File Organization
- **CLAUDE.md** (this file): Primary operating protocol
- **.cursor/rules/rules.mdc**: Cursor-specific configuration
- **.cursor/rules/lessons.mdc**: Technical lessons and incident analysis
- **.cursor/rules/examples.md**: Detailed examples and patterns
- **.cursor/rules/validation_commands.md**: Common command reference

## Meta-Rules

**ANCHORING**: `.cursor` directory at workspace root = single source of truth for all protocol files.

🚨 **NO FALSE ✅**: Only use ✅ for 100% complete/working. Use ❌ ⚠️ 🔄 or text for partial.

🚨 **NO POSITIVITY**: Be extremely self-critical. No celebration unless 100% working.

🚨 **NEVER SIMULATE**: Ask if stuck. Fake answer = 1000x worse than getting help.

## Claude Code Specific Behavior

1. **Directory Context**: Operates in worktree directory shown in environment
2. **Tool Usage**: File ops, bash commands, web tools available
3. **Test Execution**: Use `vpython` with `TESTING=true`
4. **File Paths**: Always absolute paths
5. **Gemini SDK**: `from google import genai` (NOT `google.generativeai`)
6. **Path Conventions**: `roadmap/` = `/roadmap/` from project root
7. 🚨 **BRANCH DISCIPLINE**: ❌ NEVER switch git branches unless user explicitly requests it | Work on current branch only | Ask before any `git checkout` operations
8. 🚨 **PUSH VERIFICATION**: ⚠️ ALWAYS verify push success by querying remote commits after every `git push` | Use `gh pr view` or `git log origin/branch` to confirm changes are on remote

## Project Overview

WorldArchitect.AI = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack**: Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

**Docs**: → `.cursor/rules/project_overview.md` (full details)
- Documentation map → `.cursor/rules/documentation_map.md`
- Quick reference → `.cursor/rules/quick_reference.md`
- Progress tracking → `roadmap/templates/progress_tracking_template.md`
- Directory structure → `/directory_structure.md`

## Core Principles & Interaction

**Work Approach**:
Clarify before acting | User instructions = law | ❌ delete without permission | Leave working code alone |
Focus on primary goal | Propose before implementing | Summarize key takeaways | Externalize all knowledge

**Rule Management**:
"Add to rules" → CLAUDE.md | Technical lessons → lessons.mdc | General = rules | Specific = lessons

**Development Protocols**: → `.cursor/rules/planning_protocols.md`

**Edit Verification**: `git diff`/`read_file` before proceeding | Additive/surgical edits only

**Testing**: Red-green methodology | Test truth verification | UI = test experience not code | Use ADTs

**Red-Green Protocol** (`/tdd` or `/rg`):
1. Write failing tests FIRST → 2. Confirm fail (red) → 3. Minimal code to pass (green) → 4. Refactor

## Development Guidelines

### Code Standards
- Treat existing code as template | String constants: module-level (>1x) or constants.py (cross-file)
- **SOLID Principles**: Single Responsibility Principle (one reason to change), Open/Closed Principle
- **DRY principle** | Defensive programming: `isinstance()` validation
- **Separation of Concerns**: Domain logic separate from data layer, utility functions isolated
- **Import Organization**: All imports at file top, sorted (stdlib → third-party → local)
- **No Inline Imports**: Never import inside functions/methods/classes

### Gemini SDK
✅ `from google import genai` | ✅ `client = genai.Client(api_key=api_key)`
Models: `gemini-2.5-flash` (default), `gemini-1.5-flash` (test)

### Development Practices
`tempfile.mkdtemp()` for test files | Verify before assuming | ❌ unsolicited refactoring |
Use logging module, docstrings, proper JS loading

### Quality & Testing
- File naming: descriptive, ❌ "red"/"green" | Methods <500 lines | Single responsibility
- Integration tests: natural state, flexible assertions | Visual testing required
- Dead code: use `vulture` | Test behavior not strings

### Safety & Security
❌ Global `document.addEventListener('click')` without approval | Test workflows after modifications |
Document blast radius | Backups → `tmp/` | ❌ commit if "DO NOT SUBMIT" | Analysis + execution required

## Git Workflow

| Rule | Description | Commands/Actions |
|------|-------------|------------------|
| **Main = Truth** | Use `git show main:<file>` for originals | ❌ push to main (except roadmap/sprint files) |
| **PR Workflow** | All changes via PRs | `gh pr create` + test results in description |
| **Branch Safety** | Verify before push | `git push origin HEAD:branch-name` |
| **Integration** | Fresh branch after merge | `./integrate.sh` |
| **Pre-PR Check** | Verify commits/files | → `.cursor/rules/validation_commands.md` |
| **Post-Merge** | Check unpushed files | `git status` → follow-up PR if needed |
| **Progress Track** | Scratchpad + JSON | `roadmap/scratchpad_[branch].md` + `tmp/milestone_*.json` |
| **PR Testing** | Apply PRs locally | `gh pr checkout <PR#>` |
| **Roadmap Exception** | Direct push allowed | Only: roadmap/*.md, sprint_*.md |

🚨 **No Main Push**: ✅ `git push origin HEAD:feature` | ❌ `git push origin main`

**Commit Format**: → `.cursor/rules/examples.md`

## Environment, Tooling & Scripts

1. **Python venv**: Verify activated before running Python/tests
2. **Robust Scripts**: Make idempotent, work from any subdirectory
3. **Python Execution**: ✅ Run from project root | ❌ cd into subdirs
4. **vpython Tests**: 
   - ⚠️ "run all tests" → `./run_tests.sh`
   - ⚠️ Test fails → fix immediately or ask user
   - ✅ `TESTING=true vpython mvp_site/test_file.py` (from root)
5. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted
6. **Web Scraping**: Use full-content tools (curl) not search snippets

**Test Commands**: → `.cursor/rules/validation_commands.md`

## Data Integrity & AI Management

1. **Data Defense**: Assume incomplete/malformed | Use `dict.get()` | Validate structures
2. **Critical Logic**: Implement safeguards in code, not just prompts
3. **Single Truth**: One clear way per task | Remove conflicting rules

## Knowledge Management

### Scratchpad Protocol (⚠️)
`roadmap/scratchpad_[branch].md`: Goal | Plan | State | Next | Context | Branch info

### File Organization
- **CLAUDE.md**: Primary protocol
- **lessons.mdc**: Technical learnings from corrections
- **project.md**: Repository-specific knowledge base
- **rules.mdc**: Cursor configuration

### Process Improvement
- **5 Whys**: Root cause → lessons.mdc
- **Sync Cursor**: Copy CLAUDE.md to Cursor settings after changes
- **Proactive Docs**: Update rules/lessons after debugging without prompting

## Critical Lessons (Compressed)

### Core Patterns
- **Validate Implementation**: Docs ≠ code | Trace data flow end-to-end
- **Code Reviews**: Extract ALL comments | ❌ assume "suppressed" = unimportant
- **Empty Strings**: ✅ `if value is not None:` | ❌ `if value:`
- **AI Instructions**: Critical first, style last | Order determines compliance

### Critical Rules
- **Data Corruption**: Treat as systemic | Search ALL similar patterns | "One bug = many bugs"
- **Temp Fixes**: ⚠️ Flag immediately | Propose permanent fix NOW | Run sustainability checklist
- **Task Complete**: Problem solved + Docs updated + Memory updated + Self-audit + THEN done
- **Test Truth**: Names must match implementation | Verify modules/dependencies | Test rejection cases
- **Integration First**: ❌ test disconnected code | Verify prerequisites | Propose correct sequence
- **Analysis + Execution**: Both required | Red flags: blind execution, ignoring blockers

### Enforcement
- **Meta-Rules**: Lessons docs = ⚠️ NOT OPTIONAL | Immediate, automatic, every time
- **Schema**: Clear structures | Remove contradictions | Type validation | Concrete examples

**Detailed Lessons**: → `.cursor/rules/lessons.mdc`

## Slash Commands

| Command | Purpose | Action |
|---------|---------|--------|
| `/context` `/est` | Context estimation | Show % used, breakdown, recommendations |
| `/milestones N` | Break into N phases | Create milestones, update scratchpad, commit each |
| `/milestones suggest` | Suggest optimal count | Analyze complexity, suggest 3-7 with rationale |
| `/list` | List all commands | Display all slash commands with descriptions |
| `/tdd` `/rg` | Test-driven dev | Red → Green → Refactor workflow |
| `/review` `/copilot` | Process ALL PR comments | List EVERY comment individually, apply changes, commit |
| `/optimize` | Improve code/files | Remove dupes, improve efficiency |
| `/test` | Run full test suite | `./run_tests.sh` + fix failures |
| `/testi` | Integration test | `source venv/bin/activate && TESTING=true python3 mvp_site/test_integration/test_integration.py` |
| `/integrate` | Fresh branch | Run `./integrate.sh` script |
| `/push` | Pre-push review | Virtual agent review → push if clean |
| `/scratchpad` | Update planning | Create/update scratchpad_[branch].md |
| `/roadmap` `/r` | Update roadmap files | Commit local changes, switch to main, update roadmap/*.md, push to origin, switch back |
| `/execute` `/e` | Execute task with context management | Check context, warn if ≤25%, consider subagents, execute task |

**Command Examples**: → `.cursor/rules/examples.md`

## Special Protocols

### GitHub Copilot Comments (⚠️)
Reply to EVERY comment | Status: Fixed/Acknowledged/Future | ❌ ignore "suppressed"

### Code Review Protocol (`/review` `/copilot`) (⚠️)
**MANDATORY**: When reviewing PRs, list EVERY SINGLE comment explicitly:
1. Use `gh pr view <PR#> --comments` to get ALL comments
2. Use `gh api repos/owner/repo/pulls/<PR#>/comments` for inline comments
3. List each comment with:
   - Author (user vs bot)
   - File:Line if applicable
   - Full comment text
   - Status: ✅ Addressed / ❌ Not addressed / 🔄 Partially addressed
4. Include "suppressed" and "low confidence" comments
5. Extract comments from ALL sources:
   - PR review comments
   - Inline code comments
   - Issue comments
   - Bot suggestions

### Import Rules (⚠️)
**CRITICAL**: ALL imports MUST be at module level (top of file)
- ✅ Top of module only - after docstring, before any code
- ❌ NEVER inside functions, methods, or class definitions
- ❌ NEVER inside try/except blocks (except for import fallbacks)
- ❌ NEVER conditional imports inside if statements
- Import once at top, reference throughout module
- For import conflicts: use `as` aliases, not inline imports

### API Error Prevention (🚨)
❌ Print code/file content | ✅ Use file_path:line_number | Keep responses concise

### PR References (⚠️)
**MANDATORY**: When discussing PRs, ALWAYS include the full GitHub URL
- ✅ Format: "PR #123: https://github.com/jleechan2015/worldarchitect.ai/pull/123"
- ✅ Use `gh pr view <PR#> --web` to get URL quickly
- ❌ Never reference PRs by number only
- **Repository URL**: https://github.com/jleechan2015/worldarchitect.ai

### Roadmap Updates (`/roadmap` `/r`) (⚠️)
**MANDATORY**: When using `/roadmap` command, follow this exact sequence:
1. **Autonomy-Focused Task Clarification**: Ask detailed clarifying questions with the explicit goal of making tasks as autonomous as possible. Gather all necessary context, constraints, and requirements upfront.
2. **Task Classification**: Suggest classifications prioritizing autonomy:
   - **Small & LLM Autonomous**: LLM can complete independently with minimal guidance (PREFERRED)
   - **Small & Human-Guided**: Needs human oversight but straightforward
   - **Medium**: Requires detailed planning
   - **Large**: Requires comprehensive scratchpad
3. **Comprehensive Requirements Definition**: Based on classification:
   - **Small & LLM Autonomous**: Add complete 1-2 sentence requirements with all context needed
   - **Small & Human-Guided**: Add detailed 3-5 sentence requirements covering edge cases
   - **Medium**: ALWAYS create detailed `roadmap/scratchpad_task[NUMBER]_[brief-description].md` with implementation plan
   - **Large**: ALWAYS create comprehensive `roadmap/scratchpad_task[NUMBER]_[brief-description].md` with architecture and phases
   - **Any Detailed Task**: If defining tasks to a detailed degree during planning, ALWAYS create scratchpad files regardless of classification
4. **Autonomy Validation**: Before finalizing, verify each task has sufficient detail for independent execution
5. Record current branch name
6. If not on main branch:
   - Check for uncommitted changes with `git status`
   - If changes exist, commit them with descriptive message
7. Switch to main branch: `git checkout main`
8. Pull latest changes: `git pull origin main`
9. Make requested changes to:
   - `roadmap/roadmap.md` (main roadmap file)
   - `roadmap/sprint_current.md` (current sprint status)
   - `roadmap/scratchpad_task[NUMBER]_[description].md` (if applicable)
10. Commit changes with format: `docs(roadmap): [description]`
11. Push directly to main: `git push origin main`
12. Switch back to original branch: `git checkout [original-branch]`
13. **MANDATORY**: Explicitly report merge status: "✅ MERGED" or "❌ NOT MERGED" with explanation

**Files Updated**: `roadmap/roadmap.md`, `roadmap/sprint_current.md`, and task scratchpads as needed
**Exception**: This is the ONLY case where direct push to main is allowed

### Task Execution (`/execute` `/e`) (⚠️)
**MANDATORY**: When using `/execute` command, follow this exact sequence:
1. **Branch Creation**: ALWAYS create new branch first using `./integrate.sh` (NEVER work on main)
2. **Context Assessment**: Run `/est` equivalent to check context usage percentage
3. **Context Warning**: If ≤25% context remaining:
   - ⚠️ **WARN USER**: "Context critically low (X% remaining). Task may be truncated or fail."
   - **Ask for confirmation**: "Proceed anyway? (y/n)"
   - **If user says no**: Stop execution and suggest context optimization
4. **Subagent Analysis**: Evaluate if task should use subagents:
   - **Use subagents if**: Complex task, multiple files, requires research, or context-heavy
   - **Direct execution if**: Simple task, single file focus, or context sufficient
5. **Subagent Planning**: If using subagents:
   - **Estimate subagent count**: Based on task complexity and scope
   - **Define subagent roles**: Specific responsibilities for each subagent
   - **Report to user**: "Using X subagents: [role descriptions]"
6. **Execution Method Declaration**: 
   - **If subagents**: "Executing with X subagents for [reasons]"
   - **If direct**: "Executing directly (sufficient context/simple task)"
7. **Task Execution**: Proceed with chosen execution method
8. **Commit Changes**: Commit all changes with descriptive commit messages
9. **Push Branch**: Push branch to GitHub using `git push origin HEAD:branch-name`
10. **Create PR**: ALWAYS create PR using `gh pr create` with test results and description
11. **Result Reporting**: Summarize completion status, PR URL, and any issues

**Subagent Decision Criteria**:
- ✅ **Use subagents for**: Multi-file changes, research tasks, complex debugging, large refactoring
- ❌ **Direct execution for**: Single file edits, simple fixes, quick tests, small changes

**Context Thresholds**:
- **>50% remaining**: Proceed normally
- **26-50% remaining**: Consider subagents for complex tasks
- **≤25% remaining**: Warn user and strongly recommend subagents or context optimization

**CRITICAL REQUIREMENT**: `/execute` MUST ALWAYS create PRs, never work directly on main branch. This ensures:
- ✅ **Code review** through GitHub PR process
- ✅ **GitHub Actions** run tests automatically  
- ✅ **Proper workflow** follows branch → PR → merge pattern
- ❌ **NO direct main changes** except for roadmap files via `/roadmap`

## Project-Specific

### Flask: SPA route for index.html | Hard refresh for CSS/JS | Cache-bust in prod
### Python: venv required | Source .bashrc after changes | May need python3-venv
### AI/LLM: Detailed prompts crucial | Critical instructions first | Long prompts = fatigue
### Workflow: Simple-first | Tool fail = try alternative | Main branch = recovery source

## Quick Reference

- **Test**: `TESTING=true vpython mvp_site/test_file.py` (from root)
- **Integration**: `TESTING=true python3 mvp_site/test_integration/test_integration.py`
- **New Branch**: `./integrate.sh`
- **All Tests**: `./run_tests.sh`
- **Deploy**: `./deploy.sh` or `./deploy.sh stable`

## Additional Documentation

- **Technical Lessons**: → `.cursor/rules/lessons.mdc`
- **Cursor Config**: → `.cursor/rules/rules.mdc`
- **Examples**: → `.cursor/rules/examples.md`
- **Commands**: → `.cursor/rules/validation_commands.md`

### Archive Process
Quarterly/2500 lines/new year → `lessons_archive_YYYY.mdc` | Keep critical patterns | Reference archives