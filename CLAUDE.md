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

🚨 **PRE-ACTION CHECKPOINT**: Before ANY action, ask:
   1. "Can I actually do this or am I about to simulate?"
   2. "Does this violate any rules in CLAUDE.md?"
   3. "Should I check my constraints first?"

🚨 **NO FALSE ✅**: Only use ✅ for 100% complete/working. Use ❌ ⚠️ 🔄 or text for partial.

🚨 **NO POSITIVITY**: Be extremely self-critical. No celebration unless 100% working.

🚨 **NEVER SIMULATE**: Ask if stuck. Fake answer = 1000x worse than getting help.
   - ❌ NEVER create fake files pretending to be real output (e.g., text files named .png)
   - ❌ NEVER show "simulated" test results when real tests fail
   - ❌ NEVER create workarounds that hide actual failures
   - ✅ ALWAYS say "I cannot do X because Y" when facing limitations
   - ✅ ALWAYS show actual error messages instead of hiding them
   - ❌ NEVER pretend to run separate agents or workers when you can't
   - ❌ NEVER simulate what "would happen" - test it or admit you can't

🚨 **ANTI-HALLUCINATION MEASURES**: Extract evidence before making claims
   - ✅ ALWAYS extract direct quotes/code/errors before analysis
   - ✅ State "I don't have enough information" when uncertain
   - ✅ Base all conclusions on extracted evidence, not assumptions
   - ❌ NEVER fabricate information, statistics, or outputs
   - ❌ NEVER guess at error messages or code behavior
   - ⚠️ If uncertain about any aspect, explicitly acknowledge it

🚨 **UNCERTAINTY ACKNOWLEDGMENT**: You are explicitly permitted to:
   - ✅ Say "I don't know" when information is uncertain
   - ✅ Admit limitations in your knowledge or access
   - ✅ Request clarification when instructions are ambiguous
   - ✅ Decline tasks outside your capabilities
   - ✅ Ask for help rather than attempting impossible tasks

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

🚨 **MANDATORY**: Continuously learn from corrections and self-realizations:

### Automatic Learning Triggers
1. **User corrections** - When user corrects a mistake, immediately document it
2. **Self-corrections** - When you realize "Oh, I should have...", document it
3. **Failed attempts** - When something doesn't work, learn why
4. **Pattern recognition** - When you repeat a mistake, create a rule

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

### Self-Correction Indicators
When you say these, ALWAYS document the learning:
- "Let me correct that..." / "Let me fix that..."
- "Oh, I should have..." / "Actually, I need to..."
- "My mistake..." / "I was wrong about..."
- "I see the issue..." / "The problem is..."

### Error Recovery Protocol
When mistakes occur:
1. **Immediately acknowledge** the error without excuses
2. **Explain what went wrong** with specific details
3. **Provide corrected information** based on evidence
4. **Document the learning** via /learn or file updates
5. **Implement additional verification** to prevent recurrence

**Learning Categories** → `.claude/learnings.md`

## Claude Code Specific Behavior

1. **Directory Context**: Operates in worktree directory shown in environment
2. **Tool Usage**: File ops, bash commands, web tools available
3. **Test Execution**: Use `source venv/bin/activate && python` with `TESTING=true` (NOT vpython)
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
🚨 **MANDATORY**: Always include complete git status header in every response
- ✅ Format: `[Local: branch-name | Remote: origin/branch-name | PR: #123 https://github.com/jleechan2015/worldarchitect.ai/pull/123]`
- ✅ Use `git branch --show-current` for local branch
- ✅ Use `git rev-parse --abbrev-ref @{upstream}` for remote branch (if exists)
- ✅ Use `gh pr view --json number,url` to get PR info (if exists)
- ✅ If no PR exists, show `PR: none`
- ✅ Essential for complete context awareness and avoiding branch confusion

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
- 🚨 **testing_ui/**: ONLY real browser automation using Playwright | ❌ NEVER use `requests` library here
- 🚨 **testing_http/**: ONLY HTTP requests using `requests` library | ❌ NEVER use Playwright here
- ⚠️ **/testui and /testuif**: MUST use real Playwright browser automation | NO HTTP simulation
- ⚠️ **/testhttp and /testhttpf**: MUST use HTTP requests | NO browser automation
- ✅ **/testi**: HTTP requests are acceptable (integration testing)
- **Red Flag**: If writing "browser tests" with `requests.get()`, STOP immediately
- **Command Structure**:
  - `/testui` = Browser + Mock APIs
  - `/testuif` = Browser + REAL APIs (costs $)
  - `/testhttp` = HTTP + Mock APIs  
  - `/testhttpf` = HTTP + REAL APIs (costs $)
- 🚨 **Screenshot Rule**: Real screenshots are PNG/JPG images taken by browsers
  - ❌ NEVER create text files and name them .png
  - ❌ NEVER simulate screenshots with text descriptions
  - ✅ If browser tests can't run, say "Cannot take screenshots - Playwright not installed"

### Browser Test Execution Protocol (🚨 MANDATORY STEPS)

🚨 **CRITICAL**: Playwright IS installed in venv! Stop assuming it isn't!
- ✅ Playwright works perfectly when venv is activated
- ❌ NEVER say "Playwright isn't installed"
- ❌ NEVER create simulated tests as a workaround

#### Preferred Method - Using run_ui_tests.sh
**ALWAYS use the test runner script when available:**
```bash
# Run all UI tests with mock APIs (recommended for testing)
./run_ui_tests.sh mock

# Run all UI tests with real APIs (costs money!)
./run_ui_tests.sh

# Run specific test file
TESTING=true vpython testing_ui/test_specific_file.py
```

**The run_ui_tests.sh script handles:**
- ✅ Virtual environment activation
- ✅ Playwright installation verification
- ✅ Browser dependency checks
- ✅ Test server startup with proper ports
- ✅ Parallel test execution
- ✅ Proper cleanup on exit
- ✅ Screenshot directory setup
- ✅ Comprehensive result reporting

#### Manual Method (if script unavailable)
When asked to run browser tests manually, follow these steps IN ORDER:

1. **Check Playwright Installation**
   ```bash
   vpython -c "import playwright" || echo "STOP: Playwright not installed"
   ```
   - ✅ Continue only if import succeeds
   - ❌ FULL STOP if not installed - report: "Cannot run browser tests - Playwright not installed"

2. **Verify Browser Dependencies**
   ```bash
   vpython -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(headless=True); p.stop()" || echo "STOP: Browser deps missing"
   ```
   - ✅ Continue only if browser launches
   - ❌ FULL STOP if fails - report: "Cannot launch browsers - missing system dependencies"

3. **Start Test Server**
   ```bash
   TESTING=true PORT=6006 vpython mvp_site/main.py serve &
   sleep 3
   curl -s http://localhost:6006 || echo "STOP: Server not running"
   ```
   - ✅ Continue only if server responds
   - ❌ FULL STOP if fails - report: "Cannot start test server"

4. **Navigate with Test Mode URL Parameters**
   🚨 **CRITICAL**: Browser tests MUST use test mode URL parameters to bypass authentication:
   ```
   http://localhost:6006?test_mode=true&test_user_id=test-user-123
   ```
   - `test_mode=true` - Enables frontend test authentication bypass
   - `test_user_id=test-user-123` - Sets the test user ID (optional, defaults to 'test-user')
   - Without these parameters, you'll be stuck at the sign-in page!
   - The frontend detects these parameters and adds test headers to all API calls
   - See `mvp_site/testing_ui/README_TEST_MODE.md` for complete details

5. **Run Browser Test**
   ```bash
   TESTING=true vpython testing_ui/test_name.py
   ```
   - ✅ Report actual results/errors
   - ❌ NEVER create fake output

**GOLDEN RULE**: Stop at first failure. Never proceed to simulate missing components.

### HTTP Test Execution Protocol (⚠️ MANDATORY STEPS)
When asked to run HTTP tests, follow these steps IN ORDER:

1. **Verify Test Environment**
   ```bash
   vpython -c "import requests" || echo "STOP: requests library not installed"
   ```
   - ✅ Continue only if import succeeds
   - ❌ FULL STOP if not installed

2. **Start Test Server (if needed)**
   ```bash
   TESTING=true PORT=8086 python mvp_site/main.py serve &
   sleep 3
   curl -s http://localhost:8086 || echo "Note: Using different port or external server"
   ```
   - ✅ Continue even if local server fails (tests may use different setup)

3. **Run HTTP Test**
   ```bash
   TESTING=true python testing_http/test_name.py
   ```
   - ✅ Report actual HTTP responses/errors
   - ❌ NEVER pretend requests succeeded

### General Test Protocol (🚨 APPLIES TO ALL TESTS)
1. **Environment Check First**: Verify ALL dependencies before attempting test
2. **Fail Fast**: Stop at first missing dependency
3. **Honest Reporting**: State exactly what failed and why
4. **No Workarounds**: Don't create alternatives that hide the real issue

### Coverage Analysis Protocol (⚠️)
**MANDATORY**: When analyzing test coverage:
1. **ALWAYS use**: `./run_tests.sh --coverage` or `./coverage.sh` (HTML default)
2. **NEVER use**: Manual `coverage run` commands on individual test files
3. **Verify full test suite**: Ensure all 94+ test files are included in coverage analysis
4. **Report source**: Always mention "Coverage from full test suite via run_tests.sh"
5. **Expected timing**: ~10 seconds total (6s tests + 4s report generation)
6. **HTML location**: `/tmp/worldarchitectai/coverage/index.html`
7. **Usage patterns**:
   - `./coverage.sh` - Unit tests with HTML report (default)
   - `./coverage.sh --integration` - Include integration tests
   - `./coverage.sh --no-html` - Text report only
   - `./run_tests.sh --coverage` - Use existing test runner with coverage

### Current Coverage Baseline (January 2025)
**Last Accurate Measurement**: 67% overall coverage (21,031 statements, 6,975 missing)
- `main.py`: 74% (550 statements, 144 missing)
- `firestore_service.py`: 64% (254 statements, 91 missing)
- `gemini_service.py`: 70% (594 statements, 178 missing)
- `game_state.py`: 90% (169 statements, 17 missing - excellent!)
- **Integration tests**: 0% (not run by default - use --integration flag)
- **Mock services**: 32-36% (expected for mock objects)

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

🚨 **Auto-Conflict Resolution**: ⚠️ AUTOMATIC conflict resolution available:
1. **GitHub Actions**: Automatically runs on PR creation/push and resolves common conflicts
2. **Manual script**: Use `./resolve_conflicts.sh` to resolve conflicts for current PR
3. **Smart resolution**: Preserves learning content, handles common patterns in learnings.md and CLAUDE.md
4. **Fallback**: If auto-resolution fails, manual intervention required

🚨 **BRANCH PROTECTION PROTOCOL**: ⚠️ MANDATORY branch usage rules:
1. **dev[timestamp] branches**: ❌ NEVER make changes directly in these branches
   - These are protective branches to prevent accidental main pushes
   - Used ONLY for initial isolation from main branch
   - If found on one, immediately create new descriptive branch for actual work
   - Clean up by deleting after switching to proper branch

2. **Branch Creation Rules**:
   - ✅ ALWAYS create descriptive branches: `feature/task-description`, `fix/issue-name`, `update/component-name`
   - ✅ Use existing feature branches when continuing related work
   - ❌ NEVER use dev[timestamp] branches for actual development
   - ❌ NEVER make commits directly in dev[timestamp] branches

3. **Branch Cleanup Protocol**:
   - When leaving a dev[timestamp] branch: delete it immediately
   - Use `git branch -D dev[timestamp]` to clean up
   - Only keep meaningful, descriptive branches

**Commit Format**: → `.cursor/rules/examples.md`

## Environment, Tooling & Scripts

1. **Python venv**: Verify activated before running Python/tests
2. **Robust Scripts**: Make idempotent, work from any subdirectory
3. **Python Execution**: ✅ Run from project root | ❌ cd into subdirs
4. **vpython Tests**: 
   - ⚠️ "run all tests" → `./run_tests.sh`
   - ⚠️ Test fails → fix immediately or ask user
   - ✅ `TESTING=true vpython mvp_site/test_file.py` (from root)
5. 🚨 **NEVER DISMISS FAILING TESTS**: ❌ "minor failures" or "test expectation updates" | ✅ Fix ALL failing tests systematically | Debug root cause | Real bugs vs test issues | One failure = potential systemic issue
6. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted
7. **Web Scraping**: Use full-content tools (curl) not search snippets

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
- 🚨 **Fake Results = Instant Failure**: Creating fake test output violates core trust
  - Examples: Text files named .png, "simulated" results when real tests fail
  - Correct response: "Cannot run X because Y is not installed/available"

### Debugging Protocol (🚨 MANDATORY)
When debugging display/output issues:
1. **Trace Complete Data Flow**: Backend → API → Frontend → Display
   - ❌ NEVER assume formatting comes from backend without checking
   - ✅ ALWAYS check where labels/prefixes are added (often frontend)
   - ✅ Search for literal strings in BOTH backend (.py) AND frontend (.js/.html)
2. **Question Assumptions**:
   - "Is this one string or multiple parts combined?"
   - "Where is formatting added - data layer or presentation layer?"
   - "What does the raw API response actually look like?"
3. **Verify Before Fixing**:
   - ✅ Use browser DevTools Network tab to see actual API responses
   - ✅ Add logging at multiple points to trace data transformation
   - ✅ Test hypothesis with minimal changes first
   - ❌ NEVER implement complex fixes based on assumptions
4. **Common Patterns**:
   - Frontend often adds labels/prefixes for display
   - "Scene #", "Turn:", "Player:" etc. are usually UI additions
   - Raw data rarely contains display formatting
5. **Document Analysis Protocol**:
   - ✅ Extract exact error messages/code snippets FIRST
   - ✅ Analyze ONLY based on extracted evidence
   - ✅ Cite specific line numbers and file paths
   - ✅ Each debugging claim must reference actual output
   - ✅ Base all debugging claims on actual behavior, not theory
   - ❌ NEVER skip the extraction step
   - ❌ NEVER analyze what you haven't seen
   - ❌ NEVER suggest fixes without understanding the actual error

### Evidence Classification
When presenting information, classify sources:
1. **Primary** (🔍): Actual code/errors/output - "The error shows: `TypeError at line 45`"
2. **Secondary** (📚): Docs/comments - "According to Flask docs..."
3. **General** (💡): Patterns/practices - "This typically indicates..."
4. **Speculation** (❓): Theories - "This might be caused by..."

### Debugging Validation Checklist
For all debugging sessions:
- [ ] Error messages extracted verbatim with context
- [ ] Relevant code shown with file:line references
- [ ] Root cause identified based on evidence (not guessed)
- [ ] Fix tested/verified or marked as "proposed"
- [ ] Edge cases considered ("What if X is null?")
- [ ] Rollback plan provided if fix might break things

### Iterative Debugging Method
When fixes aren't working:
1. 🔍 **Minimal case** - Reproduce with simplest example
2. 🔧 **Simple first** - Try easiest fix before complex ones
3. ✅ **Verify broadly** - Test fix in multiple scenarios
4. 🔄 **Refine** - Adjust based on edge cases
5. 📝 **Document** - Record what worked and why

### Reasoning Transparency
When debugging/analyzing:
- Show the "why": "This error typically appears when..."
- Connect dots: "Since X shows Y, this indicates Z"
- Mark assumptions: "Assuming standard Flask setup..."

### Complex Problem Breakdown
For multi-faceted issues:
1. **Decompose**: Break into smaller sub-problems
2. **Prioritize**: Address most likely/impactful first
3. **Validate**: Test each assumption explicitly
4. **Synthesize**: Combine findings into solution

### Handling Information Conflicts
When sources disagree:
- 🔍 **Code wins**: Implementation trumps documentation
- 📚 **Version check**: "Docs for v2.0, but code uses v1.5"
- 🤝 **Show both**: "Docs say X, but code does Y"
- ❓ **Flag uncertainty**: "Conflicting info about..."
- 🔬 **Test to verify**: "Let me check which is correct"

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
- `/e` or `/execute` MUST follow exact protocol in `.claude/commands/execute.md`
- NEVER treat `/e` as regular request - always use milestone protocol
- MANDATORY steps: Context check → Subagent analysis → User approval → Milestone execution
- ❌ NEVER skip protocol steps or treat as normal task execution

**Chained Commands Support**:
- `/e /think` - Execute with ultrathink mode enabled
- `/e /think [task]` - Execute task with maximum thinking budget
- Commands can be chained with space separation
- First command determines primary mode, subsequent commands modify behavior

**Command Aliases**:
- `/tddf` - Alias for `/4layer` (Test-Driven Development Four-layer protocol)
- Both commands execute identical four-layer TDD testing protocol

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

### Browser Testing vs HTTP Testing (🚨)
**HARD RULE - NO SIMULATION FOR BROWSER TESTS**:
- 🚨 **NEVER create HTTP simulation tests for `/testuif` or browser automation**
- ✅ `/testi` - HTTP requests are fine (integration testing via API endpoints)
- ✅ `/testuif` - MUST use real Playwright browser automation (NO HTTP simulation)
- ❌ **STOP SIMULATING** - User explicitly demanded real browsers for UI testing
- **Browser tests require**: Actual page navigation, element clicking, form filling, screenshot capture
- **If auth blocks browser tests**: Implement frontend test mode bypass, NOT HTTP simulation

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