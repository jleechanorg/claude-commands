# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on WorldArchitect.AI**

## 🚨 CRITICAL: MANDATORY BRANCH HEADER PROTOCOL

**EVERY SINGLE RESPONSE MUST START WITH THIS HEADER - NO EXCEPTIONS:**

```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

**Header Generation Methods:**
- **PREFERRED:** Use `/header` command (single command: `./claude_command_scripts/git-header.sh`)
- **Manual:** Run individual commands:
  - `git branch --show-current` - Get local branch
  - `git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "no upstream"` - Get remote
  - `gh pr list --head $(git branch --show-current) --json number,url` - Get PR info

**🎯 Memory Aid:** The `/header` command reduces 3 commands to 1, making compliance effortless and helping build the habit of "header first, then respond".

**Examples:**
- `[Local: main | Remote: origin/main | PR: none]`
- `[Local: feature-x | Remote: origin/main | PR: #123 https://github.com/user/repo/pull/123]`

**❌ NEVER SKIP THIS HEADER - USER WILL CALL YOU OUT IMMEDIATELY**

**🚨 PRE-RESPONSE CHECKPOINT**: Before writing ANY response, ask:
1. "Did I include the mandatory branch header?"
2. "Does this violate any other rules in CLAUDE.md?"

## Legend
🚨 = CRITICAL | ⚠️ = MANDATORY | ✅ = Always/Do | ❌ = Never/Don't | → = See reference | PR = Pull Request

## File Organization
- **CLAUDE.md** (this file): Primary operating protocol
- **.cursor/rules/rules.mdc**: Cursor-specific configuration
- **.cursor/rules/lessons.mdc**: Technical lessons and incident analysis
- **.cursor/rules/examples.md**: Detailed examples and patterns
- **.cursor/rules/validation_commands.md**: Common command reference

## Meta-Rules

🚨 **PRE-ACTION CHECKPOINT**: Before ANY action, ask:
   1. "Does this violate any rules in CLAUDE.md?"
   2. "Should I check my constraints first?"

🚨 **NO FALSE ✅**: Only use ✅ for 100% complete/working. Use ❌ ⚠️ 🔄 or text for partial.

🚨 **NO POSITIVITY**: Be extremely self-critical. No celebration unless 100% working.

🚨 **NO EXCUSES FOR TEST FAILURES**: When asked to fix tests, FIX THEM ALL
   - ❌ NEVER say "pre-existing issues" or "unrelated to our changes"
   - ❌ NEVER settle for partial fixes (97/99 is NOT acceptable)
   - ❌ NEVER blame test expectations - fix the code to meet them
   - ✅ ALWAYS fix ALL failing tests to 100% pass rate
   - ✅ ALWAYS take ownership of test failures, especially in new code


🚨 **EVIDENCE-BASED APPROACH**: Core principles for all analysis
   - ✅ Extract exact error messages/code snippets before analyzing
   - ✅ Show actual output before suggesting fixes
   - ✅ Reference specific line numbers when debugging
   - 🔍 All claims must trace to specific evidence

🚨 **QUICK QUALITY CHECK** (⚡): For debugging/complex tasks, verify:
   - 🔍 Evidence shown? (errors, code, output)
   - ✓ Claims match evidence?
   - ⚠️ Uncertainties marked?
   - ➡️ Next steps clear?

## Self-Learning Protocol

🚨 **AUTO-LEARN**: Document corrections immediately when:
- User corrects a mistake
- Self-realizing "Oh, I should have..."
- Something fails
- Pattern repeats

### Learning Process
1. **Detect** - Recognize correction/mistake (yours or user's)
2. **Analyze** - Understand what went wrong and why
3. **Document** - Update appropriate file:
   - **CLAUDE.md** - Critical rules with 🚨 marker
   - **.claude/learnings.md** - Detailed categorized learnings
   - **.cursor/rules/lessons.mdc** - Technical lessons
4. **Apply** - Use the learning immediately in current session

### /learn Command
- **Usage**: `/learn [optional: specific learning]`
- **Purpose**: Explicitly capture learnings or review recent corrections
- **Example**: `/learn playwright is installed in venv`

## Claude Code Specific Behavior

1. **Directory Context**: Operates in worktree directory shown in environment
2. **Tool Usage**: File ops, bash commands, web tools available
3. **Test Execution**: Use `TESTING=true vpython` from project root
4. **File Paths**: Always absolute paths
5. **Gemini SDK**: `from google import genai` (NOT `google.generativeai`)
6. **Path Conventions**: `roadmap/` = `/roadmap/` from project root
7. 🚨 **DATE INTERPRETATION**: Environment date format is YYYY-MM-DD where MM is the month number (01=Jan, 07=July)
8. 🚨 **BRANCH DISCIPLINE**: ❌ NEVER switch git branches unless user explicitly requests it | Work on current branch only | Ask before any `git checkout` operations
9. 🚨 **DEV BRANCH PROTECTION**: ❌ NEVER make changes in dev[timestamp] branches | These are protective branches only | Always create descriptive branches for actual work
10. 🚨 **PUSH VERIFICATION**: ⚠️ ALWAYS verify push success by querying remote commits after every `git push` | Use `gh pr view` or `git log origin/branch` to confirm changes are on remote
11. 🚨 **PR STATUS INTERPRETATION**: ⚠️ CRITICAL - GitHub PR states mean:
   - **OPEN** = Work In Progress (WIP) - NOT completed
   - **MERGED** = Completed and integrated into main branch  
   - **CLOSED** = Abandoned or rejected - NOT completed
   - ❌ NEVER mark tasks as completed just because PR exists
   - ✅ ONLY mark completed when PR state = "MERGED"
12. 🚨 **PUPPETEER MCP DEFAULT**: ⚠️ MANDATORY - When running in Claude Code CLI:
   - ✅ ALWAYS use Puppeteer MCP for browser automation by default
   - ✅ Automatically add --puppeteer flag to all UI test commands
   - ✅ Use MCP functions instead of Playwright for browser tests
   - ❌ NEVER default to Playwright when MCP tools are available
   - Benefits: No dependencies, real browsers, visual screenshots, Claude Code integration

## Project Overview

WorldArchitect.AI = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack**: Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

**Docs**: → `.cursor/rules/project_overview.md` (full details)
- Documentation map → `.cursor/rules/documentation_map.md`
- Quick reference → `.cursor/rules/quick_reference.md`
- Progress tracking → `roadmap/templates/progress_tracking_template.md`
- Directory structure → `/directory_structure.md`
- **AI Assistant Guide**: → `mvp_site/README_FOR_AI.md` (CRITICAL system architecture for AI assistants)
- **📋 MVP Site Architecture**: → `mvp_site/README.md` (comprehensive codebase overview)
- **📋 Code Review & File Responsibilities**: → `mvp_site/CODE_REVIEW_SUMMARY.md` (detailed file-by-file analysis)
- **Browser Test Mode**: → `mvp_site/testing_ui/README_TEST_MODE.md` (How to bypass auth in browser tests)

## Core Principles & Interaction

**Work Approach**:
Clarify before acting | User instructions = law | ❌ delete without permission | Leave working code alone |
Focus on primary goal | Propose before implementing | Summarize key takeaways | Externalize all knowledge

**Branch Status Protocol**:
🚨 **CRITICAL ENFORCEMENT**: See top of document for mandatory header protocol
- ❌ NEVER start a response without the branch header
- ✅ Header commands and format documented at top of CLAUDE.md
- 🚨 **USER EXPECTATION**: Missing header = immediate callout from user
- ✅ This is the #1 most violated rule - extreme vigilance required

**Response Modes**: 
- Default: Structured analysis with <thinking>, <analysis>, <response> format for complex tasks
- For simple queries: Direct concise answers
- Override to concise: "be brief", "short answer", "concise mode"
- Re-evaluate: Week of July 15, 2025

**Rule Management**:
"Add to rules" → CLAUDE.md | Technical lessons → lessons.mdc | General = rules | Specific = lessons

**Development Protocols**: → `.cursor/rules/planning_protocols.md`

**Edit Verification**: `git diff`/`read_file` before proceeding | Additive/surgical edits only

**Testing**: Red-green methodology | Test truth verification | UI = test experience not code | Use ADTs

**Red-Green Protocol** (`/tdd` or `/rg`):
1. Write failing tests FIRST → 2. Confirm fail (red) → 3. Minimal code to pass (green) → 4. Refactor

🚨 **Test Infrastructure Validation Protocol**:
When working with test runners/harnesses:
1. **Verify Core Function**: Before adding features, verify runner correctly detects PASS vs FAIL
2. **Test Both Paths**: Create one passing test AND one failing test to validate detection
3. **Output Analysis**: If visual output (❌/✅) doesn't match summary, STOP and fix immediately
4. **Exit Code Distrust**: Don't rely solely on process exit codes - parse actual output
5. **Contradiction = Bug**: Any mismatch between test output and summary is CRITICAL bug

🚨 **MANDATORY TEST EXECUTION BEFORE COMPLETION**:
❌ NEVER claim test completion without executing at least ONE test successfully
- Before any ✅ "tests complete", run at least one test to verify framework works
- If dependencies missing (Playwright, etc.), FULL STOP - report "Cannot complete - X not installed"
- Use ⚠️ "Created but unverified" instead of ✅ "Complete" for untested code
- Only use ✅ after seeing actual PASS/FAIL results from real test execution

🚨 **TEST EXECUTION RULES**:
- ✅ Run tests before marking ANY task complete
- ❌ NEVER skip/modify tests without explicit permission
- ❌ NEVER claim "tests complete" without running them
- ✅ Report missing dependencies honestly ("Cannot run - X not installed")
- ✅ Fix ALL failures - no partial success (146/147 = FAILURE)

## Development Guidelines

### Code Standards
- Treat existing code as template | String constants: module-level (>1x) or constants.py (cross-file)
- **SOLID Principles**: Single Responsibility Principle (one reason to change), Open/Closed Principle
- **DRY principle** | Defensive programming: `isinstance()` validation
- **Code Duplication Prevention**: Check for existing similar code before writing new | Extract common patterns to utilities | Audit for unused CSS/imports
- **Constants Over Strings**: Use constants.py for repeated keys/values | Never hardcode 'session_header', 'planning_block' etc. | Module-level constants for >1x usage
- **Extraction Methods**: Create utility functions for duplicate logic | Extract structured field operations | HTML generation helpers for repeated UI patterns
- **Separation of Concerns**: Domain logic separate from data layer, utility functions isolated
- **Import Organization**: All imports at file top, sorted (stdlib → third-party → local)
- **No Inline Imports**: Never import inside functions/methods/classes

### Gemini SDK
✅ `from google import genai` | ✅ `client = genai.Client(api_key=api_key)`
Models: `gemini-2.5-flash` (default), `gemini-1.5-flash` (test)

### Development Practices
`tempfile.mkdtemp()` for test files | Verify before assuming | ❌ unsolicited refactoring |
**Logging**: ✅ `import logging_util` | ❌ `import logging` | Use project's unified logging
Use docstrings, proper JS loading

### Quality & Testing
- File naming: descriptive, ❌ "red"/"green" | Methods <500 lines | Single responsibility
- Integration tests: natural state, flexible assertions | Visual testing required
- Dead code: use `vulture` | Test behavior not strings
- 🚨 **Test Runner Validation**: When modifying test runners, MUST verify both PASS and FAIL detection | Create intentional failure case | Verify output matches actual result
- 🚨 **Output Contradiction Check**: If output shows failure indicators (❌, FAILED, ERROR) but summary shows success (✅, PASSED), STOP immediately and investigate
- ⚠️ **Test Exit Codes**: Don't assume test scripts return proper exit codes | Parse output for success/failure strings | Verify detection logic before trusting results
- ⚠️ **Dynamic Test Discovery**: ❌ NEVER hardcode test file lists in scripts | ✅ Use `find` or glob patterns to discover tests automatically | Update test runners to scan directories (e.g., `find testing_ui -name "test_*.py"`)

### 🚨 MANDATORY TEST EXECUTION PROTOCOL

**CRITICAL**: This protocol is NON-NEGOTIABLE for ALL `/execute` commands and test-related work.

#### Pre-Completion Checklist
Before marking ANY task complete, ALL boxes must be checked:
- [ ] Run `./run_tests.sh` - MUST show "All tests passed! 🎉" (100% pass rate)
- [ ] If browser tests requested - MUST run `./run_ui_tests.sh mock` and show 100% pass
- [ ] If screenshots requested - MUST provide actual system screenshots (NOT mock demos)
- [ ] Run `gh pr view <PR#> --json statusCheckRollup` - ALL checks must show SUCCESS

#### Zero Tolerance Policy
- ❌ **NO dismissing failures as "unrelated"** - Every failure is YOUR responsibility
- ❌ **NO claiming completion with failing tests** - 146/147 is FAILURE, not success
- ❌ **NO mock demos when real screenshots requested** - Fix the system, capture real output
- ❌ **NO partial fixes** - ALL tests must pass, no exceptions
- ❌ **NO "pre-existing issues" excuse** - Fix ALL failures regardless of origin

#### Evidence Requirements
MUST provide concrete evidence:
- Test output showing exact pass/fail counts
- Actual screenshots from running system (with timestamps)
- GitHub checks status output
- Specific error messages for ANY failure

#### Failure Protocol
When ANY test fails:
1. **STOP** - Do not proceed with other tasks
2. **FIX** - Debug and resolve EVERY failure
3. **VERIFY** - Re-run entire test suite after fixes
4. **EVIDENCE** - Show output proving 100% success
5. **ONLY THEN** - Mark task as complete

#### Test Execution Examples
```bash
# Backend tests - MUST show "All tests passed!"
./run_tests.sh

# UI tests - MUST complete without failures
./run_ui_tests.sh mock

# Integration tests - MUST pass if run
TESTING=true python mvp_site/test_integration/test_integration.py

# GitHub checks - MUST all be SUCCESS
gh pr view <PR#> --json statusCheckRollup | jq '.statusCheckRollup[].conclusion'
```

**ENFORCEMENT**: Violating this protocol = immediate task failure. No excuses accepted.

### Safety & Security
❌ Global `document.addEventListener('click')` without approval | Test workflows after modifications |
Document blast radius | Backups → `tmp/` | ❌ commit if "DO NOT SUBMIT" | Analysis + execution required

### File Placement Rules (🚨 HARD RULE)
🚨 **NEVER add new files directly to mvp_site/** without explicit user permission
- ❌ NEVER create test files, documentation, or scripts directly in mvp_site/
- ✅ If unsure, add content to roadmap/scratchpad_[branch].md instead
- ✅ Ask user where to place new files before creating them
- **Exception**: Only when user explicitly requests file creation in mvp_site/

🚨 **MANDATORY: Review codebase documentation before mvp_site/ changes**:
- ✅ ALWAYS check `mvp_site/README.md` for architecture understanding
- ✅ ALWAYS check `mvp_site/CODE_REVIEW_SUMMARY.md` for file responsibilities
- ✅ Understand component responsibilities before modifying existing files
- ✅ Consider impact on related components when making changes

### Browser vs HTTP Testing (🚨 HARD RULE)
**CRITICAL DISTINCTION**: Never confuse browser automation with HTTP simulation
- 🚨 **testing_ui/**: ONLY real browser automation using **Puppeteer MCP** (default) or Playwright | ❌ NEVER use `requests` library here
- 🚨 **testing_http/**: ONLY HTTP requests using `requests` library | ❌ NEVER use browser automation here
- ⚠️ **/testui and /testuif**: MUST use real browser automation (Puppeteer MCP preferred) | NO HTTP simulation
- ⚠️ **/testhttp and /testhttpf**: MUST use HTTP requests | NO browser automation
- ✅ **/testi**: HTTP requests are acceptable (integration testing)
- **Red Flag**: If writing "browser tests" with `requests.get()`, STOP immediately

- **Command Structure** (Claude Code CLI defaults to Puppeteer MCP):
  - `/testui` = Browser (Puppeteer MCP) + Mock APIs
  - `/testuif` = Browser (Puppeteer MCP) + REAL APIs (costs $)
  - `/testhttp` = HTTP + Mock APIs  
  - `/testhttpf` = HTTP + REAL APIs (costs $)


### Browser Test Execution Protocol (🚨 MANDATORY STEPS)

🚨 **PREFERRED**: Use Puppeteer MCP for browser automation in Claude Code CLI!
- ✅ Puppeteer MCP provides real browser automation without dependency issues
- ✅ Built-in screenshot capture and JavaScript execution
- ✅ Direct integration with Claude Code environment
- ❌ NEVER use HTTP simulation when browser automation is requested

🚨 **FALLBACK**: Playwright IS installed in venv if Puppeteer MCP unavailable!
- ✅ Playwright works perfectly when venv is activated
- ❌ NEVER say "Playwright isn't installed"
- ❌ NEVER create simulated tests as a workaround
- ✅ ALWAYS use headless=True for browser tests to avoid UI timeouts
- 🔍 Evidence: Headless mode confirmed working in `/tmp/worldarchitectai/browser/wizard_red_green/`

#### Preferred Method - Using run_ui_tests.sh with Puppeteer MCP
**ALWAYS use Puppeteer MCP in Claude Code CLI:**
```bash
# Default: Run all UI tests with Puppeteer MCP + mock APIs (recommended)
./run_ui_tests.sh mock --puppeteer

# Run with real APIs using Puppeteer MCP (costs money!)
./run_ui_tests.sh real --puppeteer

# Manual Puppeteer MCP test execution (preferred for debugging)
# Start server: ./run_ui_tests.sh mock --puppeteer
# Then use MCP functions in Claude Code CLI for browser automation
```

#### Fallback Method - Using Playwright (when MCP unavailable)
```bash
# Fallback to Playwright if MCP tools not available
./run_ui_tests.sh mock

# Run specific test file with Playwright
TESTING=true vpython testing_ui/test_specific_file.py
```

**Navigate with Test Mode URL Parameters**:
🚨 **CRITICAL**: Browser tests MUST use test mode URL parameters to bypass authentication:
```
http://localhost:6006?test_mode=true&test_user_id=test-user-123
```
- `test_mode=true` - Enables frontend test authentication bypass
- `test_user_id=test-user-123` - Sets the test user ID
- Without these parameters, you'll be stuck at the sign-in page!

**Manual steps**: → `.cursor/rules/test_protocols.md`

### Coverage Analysis Protocol (⚠️)
**MANDATORY**: When analyzing test coverage:
1. **ALWAYS use**: `./run_tests.sh --coverage` or `./coverage.sh` (HTML default)
2. **NEVER use**: Manual `coverage run` commands on individual test files
3. **Verify full test suite**: Ensure all 94+ test files are included in coverage analysis
4. **Report source**: Always mention "Coverage from full test suite via run_tests.sh"
5. **HTML location**: `/tmp/worldarchitectai/coverage/index.html`

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

🚨 **PR Context Management**: ⚠️ MANDATORY before creating new branches/PRs:
1. **Check git status**: `git status` and `git branch` to see current work
2. **Verify PR context**: When user says "push to the PR" without number, ask which PR
3. **Use existing branches**: Check if work should go to existing PR before creating new
4. **Never assume**: If ambiguous, ask for clarification rather than creating duplicate work

🚨 **Branch Protection Rules**:
- ❌ NEVER use dev[timestamp] branches for actual development
- ✅ Create descriptive branches: `feature/task-description`, `fix/issue-name`, `update/component-name`
- ✅ Auto-conflict resolution available: `./resolve_conflicts.sh`

**Commit Format**: → `.cursor/rules/examples.md`

## Environment, Tooling & Scripts

1. **Python venv**: Verify activated before running Python/tests | If missing/corrupted → `VENV_SETUP.md`
2. **Robust Scripts**: Make idempotent, work from any subdirectory
3. **Python Execution**: ✅ Run from project root | ❌ cd into subdirs
4. **vpython Tests**: 
   - ⚠️ "run all tests" → `./run_tests.sh`
   - ⚠️ Test fails → fix immediately or ask user
   - ✅ `TESTING=true vpython mvp_site/test_file.py` (from root)
5. 🚨 **NEVER DISMISS FAILING TESTS**: ❌ "minor failures" or "test expectation updates" | ✅ Fix ALL failing tests systematically | Debug root cause | Real bugs vs test issues | One failure = potential systemic issue
6. 🚨 **NEVER SKIP TESTS WITHOUT EXPLICIT PERMISSION**:
   ❌ NEVER skip or comment out tests without user's explicit agreement
   - If a test is failing, FIX it or ask user for permission to skip
   - ❌ NEVER use `@unittest.skip` or `pytest.mark.skip` without asking
   - ❌ NEVER comment out test methods or assertions without permission
   - ✅ ALWAYS run ALL tests unless user explicitly says to skip specific ones
6. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted
7. **Web Scraping**: Use full-content tools (curl) not search snippets
8. **Log Files Location**: 
   - ✅ Logs are in `/tmp/worldarchitectai_logs/[branch-name].log`
   - ✅ Branch-specific logs: e.g., `/tmp/worldarchitectai_logs/feature-enhanced-character-codesign.log`
   - ✅ Use `strings /tmp/worldarchitectai_logs/[branch].log | grep -i "pattern"` for binary log files
   - ✅ Check current branch with `git branch --show-current` to find correct log file

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
- 🚨 **Trust But Verify**: NEVER assume existing code works | Test core functionality before adding features | Validate success AND failure paths

### Debugging Protocol (🚨 MANDATORY)

**Core Process**: Extract evidence → Analyze → Verify → Fix

**Data Flow Tracing**: Backend → API → Frontend → Display
- ❌ NEVER assume formatting comes from backend without checking
- ✅ ALWAYS check where labels/prefixes are added (often frontend)
- ✅ Search for literal strings in BOTH backend (.py) AND frontend (.js/.html)

**Evidence Classification**:
- 🔍 **Primary**: Actual code/errors/output - "The error shows: `TypeError at line 45`"
- 📚 **Secondary**: Docs/comments - "According to Flask docs..."
- 💡 **General**: Patterns/practices - "This typically indicates..."
- ❓ **Speculation**: Theories - "This might be caused by..."

**Debug Checklist**:
- [ ] Error messages extracted verbatim with context
- [ ] Relevant code shown with file:line references
- [ ] Root cause identified based on evidence (not guessed)
- [ ] Fix tested/verified or marked as "proposed"
- [ ] Edge cases considered ("What if X is null?")

**Details**: → `.cursor/rules/debugging_guide.md`

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

Use `/list` to display all available slash commands with descriptions.

**Command Documentation**: → `.claude/commands/`

🚨 **SLASH COMMAND ENFORCEMENT**: 
- `/e` or `/execute` MUST follow simplified protocol in `.claude/commands/execute.md`
- NEVER treat `/e` as regular request - always use TodoWrite circuit breaker
- MANDATORY: TodoWrite checklist → Present plan → Wait for approval → Execute
- ❌ NEVER skip the TodoWrite circuit breaker

🚨 **EXECUTE COMMAND CIRCUIT BREAKER**: When seeing `/e` or `/execute`:
- ✅ IMMEDIATELY use TodoWrite tool with this EXACT checklist:
  ```
  ## EXECUTE PROTOCOL CHECKLIST
  - [ ] Context check: ___% remaining
  - [ ] Complexity assessment: Low/Medium/High
  - [ ] Subagents needed? Yes/No (Why: ___)
  - [ ] Execution plan presented to user
  - [ ] User approval received: YES/NO
  ```
- ❌ NEVER start ANY work until "User approval received" is checked YES
- ❌ NEVER skip TodoWrite - it's the circuit breaker that prevents premature execution
- ⚠️ Breaking this = bypassing critical safety protocol

**Why This Matters**:
- User may not be ready for immediate execution
- Complex tasks need proper planning
- Context budget must be managed carefully
- Subagents are expensive and should be used judiciously

**Chained Commands Support**:
- `/e /think` - Execute with ultrathink mode enabled
- `/e /think [task]` - Execute task with maximum thinking budget
- Commands can be chained with space separation
- First command determines primary mode, subsequent commands modify behavior

**Command Aliases**:
- `/tddf` - Alias for `/4layer` (Test-Driven Development Four-layer protocol)
- `/nb` - Alias for `/newbranch` (Create new branch from latest main)
- `/plan` - Alias for `/execute` (Consolidated planning and execution workflow)
- All aliases execute identical protocols as their full command names

⚠️ **ENHANCED /learn WORKFLOW**: Flexible branching options for learning capture
   - ✅ Offer choice: "Include in current PR" vs "Clean branch from main"
   - ✅ Bundle related learning changes with current work when contextually appropriate
   - ✅ Create independent learning PRs for isolated improvements
   - 🔍 Evidence: User request for workflow flexibility and clean branch options

**Command Examples**: → `.cursor/rules/examples.md`

## Special Protocols

### GitHub PR Comment Response Protocol (⚠️)
**MANDATORY**: Systematically address ALL PR comments from all sources

#### Comment Sources to Check
1. **Inline Comments**: `gh api repos/owner/repo/pulls/PR#/comments`
2. **General Comments**: `gh pr view PR# --comments`
3. **Review Comments**: `gh api repos/owner/repo/pulls/PR#/reviews`
4. **Copilot Comments**: Include "suppressed" and "low confidence" feedback

#### Response Requirements
- **✅ RESOLVED**: Comment fully addressed with code changes
- **🔄 ACKNOWLEDGED**: Comment noted, will address in follow-up
- **📝 CLARIFICATION**: Need more details from commenter
- **❌ DECLINED**: Won't implement with clear reasoning

**Critical Rule**: ❌ NEVER ignore any comment type, including "suppressed" Copilot feedback

### Import Rules (🚨 CRITICAL)
**ALL imports MUST be at module level with NO try/except wrappers**
- ✅ Top of module only - after docstring, before any code
- ❌ NEVER inside functions, methods, or class definitions
- 🚨 **NEVER inside try/except blocks** - this hides dependency issues
- ❌ NEVER conditional imports inside if statements
- Import once at top, reference throughout module
- For import conflicts: use `as` aliases, not inline imports

🚨 **NO TRY/EXCEPT FOR IMPORTS EVER** - Critical Rule
- ❌ NEVER wrap imports in try/except blocks
- ❌ NEVER use "graceful handling" of missing dependencies
- ✅ ALL dependencies MUST be in requirements.txt and properly installed
- ✅ Import failures should cause immediate, obvious errors

**Why this matters:**
- Try/except imports hide missing dependencies in CI
- Causes silent test failures and deployment issues
- Makes dependency management invisible and unreliable

### API Error Prevention (🚨)
❌ Print code/file content | ✅ Use file_path:line_number | Keep responses concise

### Browser Testing vs HTTP Testing (🚨)
**HARD RULE - NO SIMULATION FOR BROWSER TESTS**:
- 🚨 **NEVER create HTTP simulation tests for `/testuif` or browser automation**
- ✅ `/testi` - HTTP requests are fine (integration testing via API endpoints)
- ✅ `/testuif` - MUST use real browser automation (Puppeteer MCP preferred, Playwright fallback)
- ❌ **STOP SIMULATING** - User explicitly demanded real browsers for UI testing
- **Browser tests require**: Actual page navigation, element clicking, form filling, screenshot capture
- **If auth blocks browser tests**: Implement frontend test mode bypass, NOT HTTP simulation
- **Claude Code CLI**: Automatically use Puppeteer MCP with --puppeteer flag for all browser tests

### PR References (⚠️)
**MANDATORY**: When discussing PRs, ALWAYS include the full GitHub URL
- ✅ Format: "PR #123: https://github.com/jleechan2015/worldarchitect.ai/pull/123"
- ✅ Use `gh pr view <PR#> --web` to get URL quickly
- ❌ Never reference PRs by number only
- **Repository URL**: https://github.com/jleechan2015/worldarchitect.ai




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

## API Timeout Prevention (🚨)

**MANDATORY**: Prevent API timeouts with these strategies:

### Operation Size Management
- **Break large edits**: Use MultiEdit with 3-4 focused edits max
- **Limit sequential thinking**: 5-6 thoughts instead of 8+
- **File reading**: Use offset/limit for huge files

### Response Optimization
- **Concise responses**: Essential with /think mode active
- **Bullet points**: Prefer over verbose paragraphs
- **Minimal output**: Only what's requested

### Tool Call Efficiency
- **Batch operations**: Group related tool calls
- **Avoid redundancy**: Don't re-read unchanged files
- **Smart search**: Use Grep/Glob instead of reading entire directories

### Sequential Thinking Best Practices
- **Start small**: Begin with 4-5 totalThoughts
- **Expand carefully**: Use needsMoreThoughts only if essential
- **Concise thoughts**: Keep each thought focused
- **Avoid branching**: Unless specifically needed

### Edit Strategy
- **MultiEdit**: For large changes, use multiple targeted edits
- **Section targeting**: Modify specific sections, not entire files
- **Incremental updates**: Break massive changes across messages

### Timing Awareness
- **Server load**: Timeouts correlate with system load
- **Complex operations**: /think + sequential thinking adds overhead
- **Work distribution**: Split very large tasks across multiple messages