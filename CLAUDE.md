# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on WorldArchitect.AI**

## 🚨 CRITICAL: MANDATORY BRANCH HEADER PROTOCOL

**EVERY SINGLE RESPONSE MUST END WITH THIS HEADER - NO EXCEPTIONS:**

```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

**Header Generation Methods:**
- **PREFERRED:** Use `/header` command (single command: `./claude_command_scripts/git-header.sh`)
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

🚨 **TRUST USER CAPABILITY**: Focus on execution accuracy over complexity concerns
   - ✅ Provide clear, actionable guidance for complex commands
   - ✅ Focus on areas where protocol execution may be challenging
   - ✅ Be honest about personal limitations and areas for improvement
   - ✅ Trust user's ability to handle complexity; focus on improving execution
   - ❌ Avoid generic advice about "command overload" or "cognitive load"
   - ❌ Avoid patronizing about user interface complexity or learning curves


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

🚨 **AUTO-LEARN**: Document corrections immediately when: User corrects | Self-realizing "Oh, I should have..." | Something fails | Pattern repeats

**Process**: Detect → Analyze → Document (CLAUDE.md/learnings.md/lessons.mdc) → Apply → Persist to Memory MCP

**/learn Command**: `/learn [optional: specific learning]` - The unified learning command with Memory MCP integration for persistent knowledge graph storage (consolidates all learning functionality)

## Claude Code Specific Behavior

1. **Directory Context**: Operates in worktree directory shown in environment
2. **Tool Usage**: File ops, bash commands, web tools available
3. **Test Execution**: Use `TESTING=true vpython` from project root
4. **File Paths**: Always absolute paths
5. **Gemini SDK**: `from google import genai` (NOT `google.generativeai`)
6. **Path Conventions**: `roadmap/` = `/roadmap/` from project root
7. 🚨 **DATE INTERPRETATION**: Environment date format is YYYY-MM-DD where MM is the month number (01=Jan, 07=July)
8. 🚨 **BRANCH DISCIPLINE**: ❌ NEVER switch git branches unless user explicitly requests it | Work on current branch only | Ask before any `git checkout` operations
9. 🚨 **BRANCH CONTEXT VERIFICATION**: ⚠️ MANDATORY - Before ANY changes:
   - ✅ ALWAYS ask "Which branch should I work on?" if ambiguous
   - ✅ ALWAYS verify PR context before modifications 
   - ✅ ALWAYS confirm destination before pushing changes
   - ❌ NEVER assume current branch is correct without verification
10. 🚨 **TOOL EXPLANATION VS EXECUTION**: ⚠️ MANDATORY distinction
   - ✅ When user asks "does X tool do Y?", clearly state if you're explaining or executing
   - ✅ If explaining capabilities, use "X tool CAN do Y" language
   - ✅ If actually executing, use the tool and show results
   - ❌ NEVER explain tool capabilities as if you executed them
   - ⚠️ Example: "The /learn command can save to memory" vs "Saving to memory now..."
11. 🚨 **DEV BRANCH PROTECTION**: ❌ NEVER make changes in dev[timestamp] branches | These are protective branches only | Always create descriptive branches for actual work
12. 🚨 **PUSH VERIFICATION**: ⚠️ ALWAYS verify push success by querying remote commits after every `git push` | Use `gh pr view` or `git log origin/branch` to confirm changes are on remote
13. 🚨 **PR STATUS INTERPRETATION**: ⚠️ CRITICAL - GitHub PR states mean:
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
- 🚨 **CONTEXT7 MCP PROACTIVE USAGE**: ⚠️ MANDATORY - When encountering API/library issues:
   - ✅ ALWAYS use Context7 MCP for accurate API documentation when facing errors
   - ✅ **Pattern**: Error occurs → Use `mcp__context7__resolve-library-id` → Get docs with `mcp__context7__get-library-docs`
   - ✅ Search for specific error patterns, method signatures, or usage examples
   - ✅ **Example**: Firestore transaction errors → Get google-cloud-firestore docs → Find correct API usage
   - ❌ NEVER guess API usage or rely on outdated assumptions
   - Benefits: Up-to-date docs, correct syntax, real working examples, eliminates trial-and-error
13. 🚨 **GITHUB TOOL PRIORITY**: ⚠️ MANDATORY - Tool hierarchy for GitHub operations:
   - ✅ **PRIMARY**: GitHub MCP tools (`mcp__github-server__*`) for all GitHub operations
   - ✅ **SECONDARY**: `gh` CLI as fallback when MCP fails or unavailable
   - ✅ **TERTIARY**: Slash commands (e.g., `/copilot`) - user wants them to work but don't wait/assume completion
   - ❌ NEVER wait for slash commands to complete when MCP tools can provide immediate results
   - ✅ **Pattern**: Try MCP first → Fall back to `gh` CLI → Slash commands are bonus, not dependency
   - Benefits: Immediate results, reliable API access, no command completion uncertainty

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
- ❌ NEVER end a response without the branch header
- ✅ Header commands and format documented at top of CLAUDE.md
- 🚨 **USER EXPECTATION**: Missing header = immediate callout from user
- ✅ This is the #1 most violated rule - extreme vigilance required

🚨 **BRANCH MANAGEMENT PROTOCOL**: 
- ❌ NEVER switch branches without explicit permission and announcement
- ⚠️ ALWAYS confirm "Should I switch to branch X?" before checkout
- ⚠️ ALWAYS announce "Switching from X to Y" during branch changes
- ⚠️ ALWAYS verify branch context before making modifications

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

🚨 **TEST EXECUTION RULES**: 
- ✅ Run tests before marking ANY task complete | Fix ALL failures - no partial success (146/147 = FAILURE)
- ❌ NEVER claim "tests complete" without running them | NEVER skip/modify tests without permission
- ⚠️ If dependencies missing, FULL STOP - report "Cannot complete - X not installed"
- ✅ Only use ✅ after seeing actual PASS/FAIL results from real test execution

## Development Guidelines

### Code Standards
- Treat existing code as template | String constants: module-level (>1x) or constants.py (cross-file)
- **SOLID Principles**: Single Responsibility Principle (one reason to change), Open/Closed Principle
- **DRY principle** | Defensive programming: `isinstance()` validation
- **Code Duplication Prevention**: Check for existing similar code before writing new | Extract common patterns to utilities | Audit for unused CSS/imports
- **🚨 ALWAYS REUSE CODE**: ❌ NEVER duplicate code blocks, especially data structures | ✅ Create constants/utilities for repeated patterns | ✅ Extract duplicate logic to functions | Pattern: Find duplication → Create constant/function → Replace all instances
- **Constants Over Strings**: Use constants.py for repeated keys/values | Never hardcode 'session_header', 'planning_block' etc. | Module-level constants for >1x usage
- **Extraction Methods**: Create utility functions for duplicate logic | Extract structured field operations | HTML generation helpers for repeated UI patterns
- **Separation of Concerns**: Domain logic separate from data layer, utility functions isolated
- **Import Organization**: All imports at file top, sorted (stdlib → third-party → local)
- **No Inline Imports**: Never import inside functions/methods/classes
- **No Temporary Comments**: Avoid comments like `🚨 CRITICAL FIX`, `TODO TEMPORARY`, `# FIXME`, `# HACK` | These indicate incomplete work | Code should be self-documenting | Use clear variable/function names instead | Example: Instead of `# TODO TEMPORARY - fix this later`, write proper error handling

### Gemini SDK
✅ `from google import genai` | ✅ `client = genai.Client(api_key=api_key)`
Models: `gemini-2.5-flash` (default), `gemini-1.5-flash` (test)

### Development Practices
`tempfile.mkdtemp()` for test files | Verify before assuming | ❌ unsolicited refactoring |
**Logging**: ✅ `import logging_util` | ❌ `import logging` | Use project's unified logging
Use docstrings, proper JS loading

### Website Testing & Deployment Expectations (🚨 CRITICAL)
🚨 **BRANCH ≠ WEBSITE**: ❌ NEVER assume branch changes are visible on websites without deployment
- ✅ Check PR description first - many changes are tooling/CI/backend only
- ✅ Feature branches need local server OR staging deployment for UI changes
- ❌ NEVER expect developer tooling changes to affect website appearance
- ✅ Production websites typically serve main branch only

🚨 **"Website looks same" Protocol**: When user reports website unchanged after branch switch:
1. ✅ Check PR description - what type of changes? (tooling vs UI)
2. ✅ Ask: "What URL are you viewing?" (local vs production)
3. ✅ Verify: User-facing changes or developer tooling improvements?
4. ✅ For UI changes: Hard refresh (Ctrl+F5) + check local development server
5. ✅ Explain: Branch switching ≠ deployment, many changes are non-visual

**Common Non-Visual Changes**: CI improvements, push scripts, test harnesses, developer tooling, backend APIs, database changes

### Quality & Testing
- File naming: descriptive, ❌ "red"/"green" | Methods <500 lines | Single responsibility
- Integration tests: natural state, flexible assertions | Visual testing required
- Dead code: use `vulture` | Test behavior not strings
- 🚨 **Test Runner Validation**: When modifying test runners, MUST verify both PASS and FAIL detection | Create intentional failure case | Verify output matches actual result
- 🚨 **Output Contradiction Check**: If output shows failure indicators (❌, FAILED, ERROR) but summary shows success (✅, PASSED), STOP immediately and investigate
- ⚠️ **Test Exit Codes**: Don't assume test scripts return proper exit codes | Parse output for success/failure strings | Verify detection logic before trusting results
- ⚠️ **Dynamic Test Discovery**: ❌ NEVER hardcode test file lists in scripts | ✅ Use `find` or glob patterns to discover tests automatically | Update test runners to scan directories (e.g., `find testing_ui -name "test_*.py"`)

### Website Testing & Deployment Expectations (🚨 CRITICAL)
🚨 **BRANCH ≠ WEBSITE**: ❌ NEVER assume branch changes are visible on websites without deployment
- ✅ Check PR description first - many changes are tooling/CI/backend/scripts only
- ✅ Feature branches need local server OR staging deployment for UI changes  
- ✅ Production websites typically serve main branch only
- ❌ NEVER expect developer tooling changes to affect website appearance

🚨 **"Website looks same" Protocol**:
1. ✅ Check PR description - what type of changes? (tooling vs UI)
2. ✅ Ask: "What URL are you viewing?" (local vs production)
3. ✅ Verify: User-facing changes or developer tooling/CI/scripts?
4. ✅ For UI changes: Hard refresh (Ctrl+F5) + check local development server
5. ✅ Explain: Non-UI changes (scripts, CI, tests) won't change website appearance

### 🚨 MANDATORY TEST EXECUTION PROTOCOL

**CRITICAL**: This protocol is NON-NEGOTIABLE for ALL `/execute` commands and test-related work.

**Pre-Completion Checklist**: Run `./run_tests.sh` (100% pass) | `./run_ui_tests.sh mock` if UI | Real screenshots if requested | GitHub checks SUCCESS

**Zero Tolerance**: ❌ NO dismissing failures | NO partial fixes | NO "pre-existing issues" excuse | Fix ALL failures

**Evidence Required**: Test output with counts | Actual screenshots | GitHub checks | Error messages

**Failure Protocol**: STOP → FIX → VERIFY → EVIDENCE → THEN complete

**Test Commands**: `./run_tests.sh` (backend) | `./run_ui_tests.sh mock` (UI) | GitHub checks via `gh pr view`

**ENFORCEMENT**: Violating this protocol = immediate task failure. No excuses accepted.

### 🚨 SYSTEMATIC TEST FIXING METHODOLOGY

**CRITICAL**: Lessons learned from achieving 100% pass rate (131/131) in PR #610 comprehensive test consolidation.

🚨 **Test Fix Protocol - One Issue at a Time**:
- ✅ Fix one specific test issue at a time (import errors, auth parsing, mock setup)
- ✅ Run tests after each fix to prevent cascade failures and regression
- ✅ Use targeted fixes rather than broad changes to avoid breaking other tests
- ❌ NEVER attempt to fix multiple unrelated test issues simultaneously
- **Evidence**: Successfully went from multiple failing files to 100% pass rate using this approach

🚨 **Regression Prevention for Test Fixes**:
- ⚠️ **Test-Only Fixes Preferred**: When goal is test pass rate, prefer fixing test infrastructure (mocks, imports, expectations) over modifying core application logic
- ❌ **NEVER modify core application files** (main.py, schemas/, core services) when fixing test failures unless absolutely necessary
- ✅ **Verify isolated impact**: If application changes needed, apply them in isolation and verify they don't break other tests
- **Evidence**: Modifying main.py and schemas caused regression from "129 passed, 3 failed" to "116 passed, 16 failed"

⚠️ **Function Name and Import Verification**:
- ✅ **ALWAYS verify actual function names** in modules before writing import statements
- ✅ Check both import statements AND function calls when fixing import errors
- ✅ Use `grep` or `Read` tools to confirm function exists before importing
- **Example**: Fixed `ImportError: cannot import name 'has_debug_content'` by verifying actual function name was `contains_debug_tags`

✅ **API Response Consistency Protocol**:
- ⚠️ **Standardize error keys**: Use consistent `KEY_ERROR` vs `KEY_MESSAGE` across entire API
- ✅ **Verify response format**: Always verify API response format matches test expectations  
- ✅ **Check both paths**: Verify both successful and error response formats when fixing API tests
- **Example**: Fixed multiple auth tests by ensuring consistent use of `KEY_ERROR` for error responses

### Safety & Security
❌ Global `document.addEventListener('click')` without approval | Test workflows after modifications |
Document blast radius | Backups → `tmp/` | ❌ commit if "DO NOT SUBMIT" | Analysis + execution required

### File Placement Rules (🚨 HARD RULE)
🚨 **NEVER add new files directly to mvp_site/** without explicit user permission
- ❌ NEVER create test files, documentation, or scripts directly in mvp_site/
- ✅ If unsure, add content to roadmap/scratchpad_[branch].md instead
- ✅ Ask user where to place new files before creating them
- **Exception**: Only when user explicitly requests file creation in mvp_site/

🚨 **CRITICAL: AVOID CREATING NEW TEST FILES AT ALL COSTS**
- ✅ **ALWAYS add tests to existing test files** (e.g., test_firestore_service.py, test_main.py)
- ✅ **Add new test classes** to existing files rather than creating new files
- ✅ **Extend existing test classes** with new test methods when appropriate
- ❌ **NEVER create test_new_feature.py** - add tests to test_existing_module.py instead
- ❌ **NEVER create isolated test files** unless absolutely critical for CI/production
- **Why**: Reduces file proliferation, maintains test organization, easier maintenance
- **Pattern**: New feature → Add tests to corresponding existing test file
- **Example**: Testing firestore changes → Add to test_firestore_service.py

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
  - `/tester` = End-to-end tests with REAL APIs (user decides cost)

### Real API Testing Protocol (🚨 MANDATORY)
**NEVER push back or suggest alternatives when user requests real API testing**:
- ✅ User decides if real API costs are acceptable - respect their choice
- ✅ `/tester`, `/testuif`, `/testhttpf` commands are valid user requests
- ✅ Real API testing provides valuable validation that mocks cannot
- ❌ NEVER suggest mock alternatives unless specifically asked
- ❌ NEVER warn about costs unless the command requires confirmation prompts
- **User autonomy**: User controls their API usage and testing approach

### Browser Test Execution Protocol (🚨 MANDATORY)

🚨 **PREFERRED**: Puppeteer MCP in Claude Code CLI - Real browsers, no dependencies, built-in screenshots
🚨 **FALLBACK**: Playwright IS installed in venv! Use headless=True | ❌ NEVER say "not installed"

**Commands**: `./run_ui_tests.sh mock --puppeteer` (default) | `./run_ui_tests.sh mock` (Playwright fallback)

**Test Mode URL**: `http://localhost:6006?test_mode=true&test_user_id=test-user-123` - Required for auth bypass!

**Details**: → `.cursor/rules/test_protocols.md`

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
| **🚨 Upstream Tracking** | Set tracking to avoid "no upstream" in headers | `git push -u origin branch-name` OR `git branch --set-upstream-to=origin/branch-name` |
| **Integration** | Fresh branch after merge | `./integrate.sh` |
| **Pre-PR Check** | Verify commits/files | → `.cursor/rules/validation_commands.md` |
| **Post-Merge** | Check unpushed files | `git status` → follow-up PR if needed |
| **Progress Track** | Scratchpad + JSON | `roadmap/scratchpad_[branch].md` + `tmp/milestone_*.json` |
| **PR Testing** | Apply PRs locally | `gh pr checkout <PR#>` |
| **Roadmap Exception** | Direct push allowed | Only: roadmap/*.md, sprint_*.md |

🚨 **No Main Push**: ✅ `git push origin HEAD:feature` | ❌ `git push origin main`

🚨 **PR Context Management**: Verify before creating PRs - Check git status | Ask which PR if ambiguous | Use existing branches

🚨 **Branch Protection Rules**:
- ❌ NEVER use dev[timestamp] branches for actual development
- ✅ Create descriptive branches: `feature/task-description`, `fix/issue-name`, `update/component-name`
- ✅ Auto-conflict resolution available: `./resolve_conflicts.sh`

🚨 **MERGE CONFLICT RESOLUTION PROTOCOL**: ⚠️ MANDATORY for all merge conflicts
1. **Analyze Before Resolving**: Run `git show HEAD~1:file` and `git show main:file` to understand both versions
2. **Critical File Assessment**: Is this a high-risk file? (CSS, main app logic, configs, schemas)
3. **Impact Analysis**: What features/users depend on this file? What's the blast radius?
4. **Preserve Functionality**: Default to preserving existing functionality, only add new features
5. **Test Resolution**: Verify the merged result works before committing
6. **Document Decision**: Log what was preserved vs. changed and why

**🚨 CRITICAL FILES requiring extra care during conflicts:**
- `mvp_site/static/style.css` - Main stylesheet affecting all UI
- `mvp_site/main.py` - Core application logic
- Configuration files, database schemas, authentication modules
- Any file affecting user experience or system stability

**❌ NEVER**: Accept conflict resolution without understanding what each side contains
**✅ ALWAYS**: Understand the purpose and impact before choosing resolution strategy

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
6. 🚨 **NEVER SKIP TESTS WITHOUT EXPLICIT PERMISSION**: Fix failing tests or ask permission | No `@unittest.skip` without approval
6. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted
7. **Web Scraping**: Use full-content tools (curl) not search snippets
8. **Log Files Location**: 
   - ✅ **Server logs are in `/tmp/worldarchitectai_logs/`** with subfolders/files named by branch
   - ✅ **Branch-specific logs**: `/tmp/worldarchitectai_logs/[branch-name].log`
   - ✅ **Current branch log**: `/tmp/worldarchitectai_logs/$(git branch --show-current).log`
   - ✅ **Log commands**: `tail -f /tmp/worldarchitectai_logs/[branch].log` for real-time monitoring
   - ✅ **Search logs**: `grep -i "pattern" /tmp/worldarchitectai_logs/[branch].log`
   - ✅ **Binary logs**: Use `strings /tmp/worldarchitectai_logs/[branch].log | grep -i "pattern"`
   - ✅ **Find current log**: `git branch --show-current` then check corresponding log file

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

### 🚨 **BRANCH CONFUSION ANTI-PATTERN**: Major failure pattern to avoid
- ❌ Working on wrong branch due to lack of context verification
- ❌ Creating conflicting PRs without checking user intent
- ❌ Pushing changes to unintended destinations
- ✅ ALWAYS verify branch context before making changes
- ✅ ALWAYS confirm PR destination before pushing
- **Evidence**: PR #627 vs PR #628 conflict incident - July 2025

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

**Debug Checklist**: Extract errors verbatim | Show code with file:line | Identify root cause from evidence | Test fix | Consider edge cases

**Details**: → `.cursor/rules/debugging_guide.md`

### Critical Rules
- **Data Corruption**: Treat as systemic | Search ALL similar patterns | "One bug = many bugs"
- **Temp Fixes**: ⚠️ Flag immediately | Propose permanent fix NOW
- **Task Complete**: Problem solved + Docs updated + Memory updated + Self-audit + THEN done
- **Test Truth**: Names must match implementation | Verify modules/dependencies
- **Integration First**: ❌ test disconnected code | Verify prerequisites
- **Analysis + Execution**: Both required | No blind execution

**Enforcement**: Lessons docs = ⚠️ NOT OPTIONAL | Immediate, automatic, every time

**Detailed Lessons**: → `.cursor/rules/lessons.mdc`

## Slash Commands

Use `/list` to display all available slash commands with descriptions.

**Command Documentation**: → `.claude/commands/`

### True Universal Command Composition System
🚨 **BREAKTHROUGH**: **ANY arbitrary command combination** using Claude's natural language processing
- **Genuine Universality**: Even completely made-up commands work intelligently
- **Meta-Prompt Approach**: Simple prompts leverage Claude's existing NLP capabilities
- **No Hardcoded Rules**: Claude interprets commands contextually and meaningfully
- **Consistent Quality**: No degradation for unknown/creative commands
- **Self-Improving**: Gets better as Claude's understanding evolves
- **Revolutionary Simplicity**: 25 lines vs 80+ lines of complex logic

**How It Actually Works**:
- Input: `/think /debug /weird analyze performance`
- Meta-prompt: `Use these approaches in combination: /think /debug /weird. Apply this to: analyze performance`
- Claude interprets naturally: Deep thinking + systematic debugging + unconventional approaches

**True Universality Examples**:
- `/mythical /dragon /optimize` → Creative powerful optimization approaches
- `/quantum /cosmic /analyze` → Claude interprets creatively for analysis  
- `/stealth /ninja /implement` → Subtle, efficient implementation strategies
- `/fluffy /rainbow /debug` → Claude finds meaningful interpretation

**Technical Revolution**: Instead of trying to build NLP in bash, leverage Claude's existing NLP capabilities through meta-prompts

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

**Why**: Prevents premature execution | Manages context budget | Controls subagent costs

**Chained Commands Support**:
- `/e /think` - Execute with light thinking mode (4 thoughts) enabled  
- `/e /think ultra [task]` - Execute task with maximum thinking budget (12+ thoughts)
- Commands can be chained with space separation
- First command determines primary mode, subsequent commands modify behavior

**Command Aliases**:
- `/tddf` - Alias for `/4layer` (Test-Driven Development Four-layer protocol)
- `/nb` - Alias for `/newbranch` (Create new branch from latest main)

**Command Differentiation** (NOT aliases):
- `/execute` or `/e` - Realistic implementation with optional subagents (no approval)
- `/plan` - Same as `/execute` but with mandatory approval (requires TodoWrite circuit breaker)

**Both commands use realistic execution with optional Task-based subagents when beneficial**

⚠️ **UNIFIED /learn COMMAND**: Single consolidated command with Memory MCP integration
   - ✅ **Command Consolidation**: ONE `/learn` command handles all learning functionality
   - ✅ **Memory MCP Integration**: Persistent knowledge graph storage by default
   - ✅ **No Variants**: Remove /learnmvp, /learn-enhanced, and other variant commands
   - ✅ **Flexible Branching**: "Include in current PR" vs "Clean branch from main"
   - ✅ **Duplicate Detection**: Search existing graph before creating new entities
   - ✅ **Cross-Conversation Persistence**: Learnings survive beyond current session
   - 🔍 Evidence: User said "i only want one /learn command and not some /learnmvp thing"

**Command Examples**: → `.cursor/rules/examples.md`

## Special Protocols

### GitHub PR Comment Response Protocol (⚠️)
**MANDATORY**: Systematically address ALL PR comments from all sources

**Comment Sources**: Inline (`gh api`) | General (`gh pr view`) | Reviews | Copilot (include "suppressed")

**Response Status**: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED

**Critical Rule**: ❌ NEVER ignore any comment type, including "suppressed" Copilot feedback

### Import Rules (🚨 CRITICAL)
**🚨 ZERO TOLERANCE: ALL imports MUST be at module level - NO EXCEPTIONS**

**✅ CORRECT Import Pattern:**
```python
# Standard library imports (at top of file)
import os
import sys
import subprocess
import logging

def my_function():
    # Use imported modules here
    subprocess.check_output(...)
    logging.info(...)
```

**❌ FORBIDDEN Inline Import Pattern:**
```python
def my_function():
    import subprocess  # ❌ NEVER DO THIS
    import logging     # ❌ NEVER DO THIS
    subprocess.check_output(...)
```

**🚨 CRITICAL RULES:**
- ✅ **Top of module only** - after docstring, before any code
- ❌ **NEVER inside functions, methods, or class definitions**
- 🚨 **NEVER inside try/except blocks** - this hides dependency issues
- ❌ **NEVER conditional imports** inside if statements
- ✅ **Import once at top**, reference throughout module
- ✅ For import conflicts: use `as` aliases, not inline imports

🚨 **NO TRY/EXCEPT FOR IMPORTS EVER**: ❌ NEVER wrap imports in try/except | ALL dependencies MUST be in requirements.txt | Import failures should break loudly
**Why**: Hides missing dependencies in CI | Causes silent failures | Makes dep management unreliable

**⚠️ Common Violations to Watch For:**
- Functions with `import` statements inside them
- Conditional imports based on environment variables
- Try/except wrapped imports to "handle missing dependencies"

### API Error Prevention (🚨)
❌ Print code/file content | ✅ Use file_path:line_number | Keep responses concise

### Browser Testing vs HTTP Testing (🚨)
**HARD RULE**: NO HTTP simulation for browser tests!
- `/testuif` = Real browser automation (Puppeteer MCP/Playwright) | `/testi` = HTTP requests OK
- Browser tests require: Page navigation, element clicks, form fills, screenshots
- Auth bypass: Use test mode URL params, NOT HTTP simulation

### PR References (⚠️)
**MANDATORY**: Include full GitHub URL - Format: "PR #123: https://github.com/jleechan2015/worldarchitect.ai/pull/123"


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

**MANDATORY**: Prevent API timeouts:
- **Edits**: MultiEdit with 3-4 max | Target sections, not whole files
- **Thinking**: 5-6 thoughts max | Concise | No unnecessary branching
- **Responses**: Bullet points | Minimal output | Essential info only
- **Tools**: Batch calls | Smart search (Grep/Glob) | Avoid re-reads
- **Complex tasks**: Split across messages | Monitor server load