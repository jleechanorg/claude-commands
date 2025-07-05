# CLAUDE.md - Primary Rules and Operating Protocol

**This is the primary rules file for AI collaboration on WorldArchitect.AI**

## File Organization
- **CLAUDE.md** (this file): Primary operating protocol and general development rules
- **.cursor/rules/rules.mdc**: Cursor-specific configuration and behavior
- **.cursor/rules/lessons.mdc**: Technical lessons and specific incident analysis

## Meta-Rules

**ANCHORING RULE**: The `.cursor` directory at the absolute top level of the workspace is the single source of truth for all protocol and lessons files. Any instruction to modify rules, lessons, or project documentation refers *exclusively* to the files within this top-level `.cursor` directory. I will not create, read, or write rule files in any other location.

**CRITICAL RULE: NO FALSE GREEN CHECKMARKS**
NEVER use ✅ green checkmarks unless the feature/test/functionality works 100% completely. Green checkmarks indicate FULL COMPLETION AND SUCCESS. If something is partially done, timed out, has errors, or is "ready but not run", use ❌ ⚠️ 🔄 or plain text.

**CRITICAL RULE: NO POSITIVITY - BE EXTREMELY SELF-CRITICAL**
I must be extremely hard on myself and self-critical. No celebration unless things work 100% - not 99%, not 99.9%. No positive language about partial progress, "infrastructure ready", or "almost working". If it doesn't work completely, it's a failure.

**CRITICAL RULE: NEVER SIMULATE ANYTHING**
Never simulate anything. Always ask if you are having trouble. A fake answer is 1000x worse than getting stuck. We need accuracy.

## Claude Code Specific Behavior

When using Claude Code (claude.ai/code):

1. **Directory Context**: Claude Code operates within the specific worktree directory shown in the environment information
2. **Tool Usage**: Claude Code has access to file operations, bash commands, and web tools  
3. **Test Execution**: Use `vpython` with the `TESTING=true` environment variable
4. **File Paths**: Always use absolute paths when referencing files
5. **Gemini SDK**: Always use `from google import genai` (NOT `google.generativeai`)
6. **Path Conventions**: `roadmap/` always means `/roadmap/` from project root

## Project Overview

WorldArchitect.AI is an AI-powered tabletop RPG platform that serves as a digital Game Master for D&D 5e experiences.

### Technology Stack
- **Backend**: Python 3.11 + Flask + Gunicorn
- **AI Service**: Google Gemini API (2.5-flash, 1.5-flash models) via `google` SDK
- **Database**: Firebase Firestore for persistence and real-time sync
- **Frontend**: Vanilla JavaScript (ES6+) + Bootstrap 5.3.2
- **Deployment**: Docker + Google Cloud Run

For complete project details including technology stack, architecture, development commands, and constraints, see `.cursor/rules/project_overview.md`.

### Additional Documentation Resources
- **Documentation Map**: For a visual hierarchy and navigation guide to all documentation, see `.cursor/rules/documentation_map.md`
- **Quick Reference**: For common commands and quick lookups, see `.cursor/rules/quick_reference.md`
- **Progress Tracking Template**: For milestone progress tracking, see `roadmap/templates/progress_tracking_template.md`
- **Directory Structure**: For comprehensive project directory layout and file locations, see `/directory_structure.md`

## Core Principles & Interaction

**Work Approach:**
- Clarify before acting | Ask if unclear
- User instructions = law | Never assume or override  
- Never delete without explicit permission | Default: preserve and add
- Leave working code alone | Don't modify for linters without permission
- Focus on primary goal | Ignore distractions unless instructed
- Propose solutions before implementing | Especially for complex changes
- Summarize key takeaways | Ensure alignment after major steps
- Externalize all knowledge | Rules, lessons, project info must be documented

**Rule Management:**
- "Add to rules" → CLAUDE.md | Technical lessons → .cursor/rules/lessons.mdc
- General principles in rules files | Specific technical details in lessons files
- Ask for clarification if directive is ambiguous

**Development Protocols:**
- Planning methodologies in `.cursor/rules/planning_protocols.md`
- Mode selection: single-agent vs multi-perspective (SUPERVISOR/WORKER/REVIEWER)
- Always indicate current mode when using multi-perspective system

**Edit Verification:**
- Verify every edit with `git diff` or `read_file` before proceeding
- Changes must be additive or surgical | Never delete unrelated code
- Ignore Firebase/Firestore linter errors unless instructed otherwise

**Testing Requirements:**
- Red-green methodology: Write failing test first, then implement
- Propose failing tests for uncovered bugs before adding to code
- Test truth verification: Verify tests actually test what they claim
- UI features: Test user experience, not just code functionality
- Architecture Decision Tests (ADTs) for validating architectural choices

**Red-Green Testing Protocol:**
- **TDD Command**: When user says "tdd", use Test-Driven Development:
  1. Write comprehensive failing tests FIRST
  2. Run tests to confirm they fail  
  3. Implement minimal code to make tests pass
  4. Refactor while keeping tests green
- **For UI Features**: Create functional tests that reproduce specific user issues, run tests to confirm they FAIL (red state), then fix implementation to make tests PASS (green state)
- **Critical Mindset**: "I haven't seen it work with my own eyes yet" - Never claim features work based on code alone. Must validate actual user experience

## Development Guidelines

### Development, Coding & Architecture

**Code Standards:**
- Treat existing code as fixed template | Only surgical edits
- String constants: Module-level if used >1x, global constants.py if cross-file
- DRY principle: Refactor shared code into helper functions
- Defensive programming: Validate data types with `isinstance()` before operations

**Gemini SDK & Models:**
- Always use `from google import genai` (NOT google.generativeai)
- Initialize: `client = genai.Client(api_key=api_key)`
- Models: `gemini-2.5-flash` (default), `gemini-1.5-flash` (test) - never change without authorization

**Development Practices:**
- Use temporary directories for test files (`tempfile.mkdtemp()`)
- Verify before assuming: Check API signatures, library versions
- No unsolicited refactoring: Get explicit approval first
- Professional standards: logging module, docstrings, proper JS loading

**Quality & Testing:**
- File naming: Use descriptive names, avoid "red"/"green" in filenames
- Method length: <500 lines, single responsibility, extract helpers
- Integration tests: Natural state, flexible assertions, temp directories
- Visual testing: Comprehensive validation required before claiming UI works
- Dead code detection: Use `vulture` tool, not grep searches
- Unit tests: Test behavior not exact strings | User screenshots override code analysis

**Safety & Security:**
- Global events: Never `document.addEventListener('click')` without approval
- Workflow protection: Test core workflows after ANY modification
- Cross-cutting analysis: Document blast radius for infrastructure changes  
- Backup management: All backup files go in `tmp/` directory
- Security markers: Never commit if "DO NOT SUBMIT" present
- Execution mindset: Analysis AND execution required, never pure execution mode

### Git Workflow
1. **Main Branch is Source of Truth:**
   - Use `git show main:<file>` to retrieve original versions
   - Never push directly to main (except roadmap/sprint files)

2. **Pull Request Workflow:**
   - All changes go through PRs
   - Create with `gh pr create`
   - Include test results in PR description
   - Exception: Direct push allowed for roadmap/*.md and sprint_*.md files

3. **Branch Safety:**
   - Always verify branch before pushing
   - Use explicit push: `git push origin HEAD:branch-name`
   - Run `./integrate.sh` after merges for fresh branch
   - Check current branch: `git branch --show-current`
   - Verify tracking: `git branch -vv`

4. **Pre-PR Verification:**
   - Check commits: `git log main..HEAD --oneline`
   - Verify files: `git diff main...HEAD --name-only`
   - Count commits: `git rev-list --count main..HEAD`
   - Warn if unrelated commits found

5. **Post-PR Merge Protocol:**
   - **CRITICAL**: Always check for unpushed local files after merge
   - Run `git status` immediately after PR merge
   - List any modified/untracked files
   - Create follow-up PR if important files were missed

6. **Detailed Progress Tracking:**
   - Main plan in `roadmap/scratchpad_[branch_name].md`
   - Granular tracking with `tmp/milestone_X.Y_progress.json`
   - One sub-bullet = one commit
   - Force add ignored files: `git add -f tmp/*.json`
   - Atomic commits with descriptive messages:
     ```
     M{milestone} Step {step}.{sub_bullet}: {Brief description}
     
     - {Implementation detail 1}
     - {Key result or finding}
     - Saved progress to tmp/milestone_{milestone}_step_{step}.{sub_bullet}_progress.json
     
     🤖 Generated with [Claude Code](https://claude.ai/code)
     Co-Authored-By: Claude <noreply@anthropic.com>
     ```

7. **Applying Pull Requests for Testing:**
   - Prefer GitHub CLI: `gh pr checkout <PR_NUMBER>`
   - Alternative: `git fetch origin pull/<PR_NUMBER>/head:<branch_name>`
   - Provides convenient workflow and reduces manual errors

8. **Merge Protocol and Branch Management:**
   * **CRITICAL**: Always use the `integrate` alias pattern for updating from main: `git checkout main && git pull && git branch -D dev && git checkout -b dev`
   * **Main Branch Protection**: Never work directly on `main` - always use a local `dev` branch for protection
   * **After Merges**: Always run the integrate pattern to get latest changes and create fresh dev branch
   * **PR Creation Process**:
     1. Create feature branch from latest main using integrate pattern
     2. Make changes and commit with descriptive messages
     3. **MANDATORY**: Run `./run_tests.sh` and include test results in PR description
     4. Push branch and create PR with comprehensive description using `gh pr create`
     5. Provide clickable PR URL for user review
     6. After merge, immediately run integrate pattern before next PR
     7. **CRITICAL**: Never use 'dev' as a remote branch for PRs - always use descriptive feature branch names
   * **PR Descriptions**: Always include Summary, Changes, Benefits, and Usage sections
   * **Commit Messages**: Use descriptive titles with bullet points and Claude Code attribution

9. **GitHub CLI Preference for PR Operations:**
   * Always use GitHub CLI (`gh`) commands for creating and managing pull requests when available
   * This ensures proper authentication and streamlined workflow

10. **Branch Safety and Push Verification Protocol:**
    * **CRITICAL**: Never accidentally push to main/master branch. Always verify branch and tracking before any push operation.
    * **Pre-Push Checklist** (MANDATORY before every push):
      1. Check current branch: `git branch --show-current`
      2. Verify branch tracking: `git branch -vv`
      3. Confirm push target: Use explicit syntax `git push origin HEAD:branch-name`
      4. Test with dry-run first: `git push --dry-run`
    * **Safe Branch Creation Pattern**: Always use this sequence to avoid tracking issues:
      ```bash
      git checkout main
      git pull origin main
      git checkout -b feature-branch-name
      # This creates an untracked branch, forcing explicit remote setup
      ```
    * **NEVER use**: `git checkout origin/main -b branch-name` as it sets tracking to main
    * **Push Safety**: Always use explicit push syntax: `git push origin HEAD:branch-name` instead of relying on `-u` or default tracking
    * **Recovery Protocol**: If accidental main push is detected, immediately notify user and provide recovery options

11. **No Direct Push to Main Branch Protocol:**
    * **ABSOLUTE PROHIBITION**: NEVER push directly to main/master branch under any circumstances
    * **Git Push Commands**: When pushing, ALWAYS specify the target branch explicitly:
      - ✅ CORRECT: `git push origin HEAD:feature-branch-name`
      - ✅ CORRECT: `git push origin feature-branch:feature-branch`
      - ❌ FORBIDDEN: `git push origin main` or any variant that targets main
      - ❌ FORBIDDEN: `git push` without explicit branch specification if tracking main
    * **Accidental Push Prevention**:
      1. Always verify current branch before pushing: `git branch --show-current`
      2. Always use explicit branch syntax in push commands
      3. If a push accidentally goes to main, immediately alert the user
    * **PR-Only Workflow**: All changes to main must go through pull requests - no exceptions
    * **Recovery**: If accidental push to main occurs, immediately:
      1. Stop all operations
      2. Alert user with: "⚠️ CRITICAL: Accidentally pushed to main branch!"
      3. Provide revert instructions if needed

12. **Pull Request Workflow for All Changes:**
    * **MANDATORY**: ALL changes to main branch must go through pull requests, including:
      - Code changes
      - Documentation updates
      - Configuration modifications
    * **ROADMAP AND SPRINT PLANNING EXCEPTION**: Direct pushes to main are ALLOWED for these specific files only:
      - `roadmap/roadmap.md`
      - `roadmap/sprint_current.md`
      - `roadmap/sprint_*.md` (any sprint planning files)
      - Rationale: Frequent small updates for task tracking and planning should not require PR overhead
      - **Process for roadmap/sprint files**:
        1. Make changes directly on main branch
        2. Commit with descriptive message: "Update roadmap: [brief description]"
        3. Push directly to main: `git push origin main`
      - **Restriction**: This exception applies ONLY to roadmap and sprint files, not any other documentation
    * **Workflow Process for Non-Roadmap Changes**:
      1. Make changes on feature/dev branch
      2. Commit changes with descriptive messages
      3. Create pull request using `gh pr create`
      4. Review and merge PR (do not merge directly to main)
      5. Run `./integrate.sh` to create fresh clean branch
    * **No Direct Main Merges**: Never merge directly to main branch, except for roadmap/sprint files
    * **Visibility**: PRs provide visibility, review history, and proper change tracking
   - List any modified/untracked files
   - Create follow-up PR if important files were missed

6. **Detailed Progress Tracking:**
   - Main plan in `roadmap/scratchpad_[branch_name].md`
   - Granular tracking with `tmp/milestone_X.Y_progress.json`
   - One sub-bullet = one commit
   - Force add ignored files: `git add -f tmp/*.json`
   - Atomic commits with descriptive messages:
     ```
     M{milestone} Step {step}.{sub_bullet}: {Brief description}
     
     - {Implementation detail 1}
     - {Key result or finding}
     - Saved progress to tmp/milestone_{milestone}_step_{step}.{sub_bullet}_progress.json
     
     🤖 Generated with [Claude Code](https://claude.ai/code)
     Co-Authored-By: Claude <noreply@anthropic.com>
     ```

7. **Applying Pull Requests for Testing:**
   - Prefer GitHub CLI: `gh pr checkout <PR_NUMBER>`
   - Alternative: `git fetch origin pull/<PR_NUMBER>/head:<branch_name>`
   - Provides convenient workflow and reduces manual errors

8. **Merge Protocol and Branch Management:**
   - Use `integrate` pattern: `git checkout main && git pull && git branch -D dev && git checkout -b dev`
   - Main branch protection: Never work directly on main, use local dev branch
   - After merges: Run integrate pattern for fresh dev branch
   - PR process: Feature branch → descriptive commits → test results → `gh pr create`
   - Never use 'dev' as remote branch name for PRs

## Environment, Tooling & Scripts

1. **Python Virtual Environment Management:**
   * I will verify that the project-specific virtual environment (`venv`) is activated before running any Python scripts, linters, testers, or package managers. If it's not active, I will attempt to activate it or inform you if I cannot.

2. **Write Robust & Context-Aware Scripts:**
   * Automation scripts (e.g., `deploy.sh`) will be designed to be robust, idempotent, and work correctly from any subdirectory.

3. **Python Execution Protocol:** Always run from project root (Python imports require consistent context)
   ```bash
   # Correct - from project root
   python3 prototype/some_file.py
   vpython mvp_site/test_file.py
   TESTING=true vpython mvp_site/test_integration.py
   
   # Incorrect - from subdirectories
   cd prototype && python3 file.py  # ❌ Breaks imports
   cd mvp_site && python3 test.py   # ❌ Breaks imports
   ```

4. **Use `vpython` for Tests - Consistent Execution Pattern:**
   * Always use `vpython` to run tests when available. If `vpython` is not available, use `python3` but ALWAYS from project root.
   * **CRITICAL: When user says "run all tests", always use `./run_tests.sh` script from project root instead of manual unittest commands.**
   * **CRITICAL: When ANY test fails, I must either fix it immediately or explicitly ask the user if it should be fixed. I must highlight the entire line of failing test output in red for visibility.**
   * **UPDATED Directory Navigation for `vpython`:**
     - **ALWAYS from project root**: `TESTING=true vpython mvp_site/test_file.py`
     - **NEVER cd into subdirectories** for Python execution
     - If unsure of location: Use `pwd` first, then navigate to project root
     - For prototype tests: `vpython test_prototype_working.py` (from root)
   * **Correct Test Commands:** 
     - Integration tests: `TESTING=true vpython mvp_site/test_integration.py`
     - Specific tests: `vpython -m unittest mvp_site.test_module.TestClass.test_method`
     - Prototype tests: `python3 test_prototype_working.py`

5. **Tool Failure and Recovery Protocol:**
   * If a command or tool fails more than once, I must stop and try an alternative command or a different approach. I will not repeatedly attempt the same failing action. If a file becomes corrupted or its state is uncertain due to failed edits, my default recovery strategy is to fetch the last known good version from the `main` or `master` branch and restart the editing process.

6. **Use Full-Content Tools for Web Scraping:**
   * When the goal is to download the content of a webpage, I must use a tool that retrieves the full page content (e.g., `curl`). I will not use a search tool (like `web_search`) that only returns snippets, as the primary objective is to acquire the complete text.

## Data Integrity and AI Management

1. **Prioritize Data Integrity:**
   - Assume data may be incomplete or malformed
   - Use defensive access (e.g., `dict.get()`)
   - Validate data structures before processing

2. **Enforce Critical Logic in Code:**
   - Implement safeguards in application code
   - Don't rely solely on AI prompts for data integrity

3. **Single Source of Truth:**
   - Ensure one clear way to perform tasks in AI instructions
   - Remove conflicting examples or rules

## Knowledge Management & Process Improvement

### Scratchpad Protocol
**MANDATORY**: Maintain work-in-progress plans in `roadmap/scratchpad_[remote_branch_name].md` containing:
- Project Goal: Clear statement of branch purpose
- Implementation Plan: Step-by-step with milestones  
- Current State: What's completed, in progress, blocked
- Next Steps: Specific actionable items
- Key Context: Important decisions and findings
- Branch Info: Remote branch name, PR number, merge target

This protocol uses a set of files to manage our workflow. The primary tracking happens in `roadmap/scratchpad_[remote_branch_name].md` as defined in the Scratchpad Protocol above. Additional files in the `.cursor` directory at the project's root provide supplementary tracking. If they don't exist, I will create them. I will review them before each interaction and update them after.

### File Organization
1. **CLAUDE.md** - Primary operating protocol (this file)

2. **.cursor/rules/lessons.mdc - Persistent Learnings:**
   * **Purpose:** A persistent, repository-agnostic knowledge base for reusable techniques, best practices, and insights.
   * **Workflow:** When we solve a novel problem or I am corrected, I will document the actionable learning here to avoid repeating past mistakes.

3. **.cursor/project.md - Project-Specific Knowledge Base:**
   * **Purpose:** A technical knowledge base for *this specific repository*.
   * **Workflow:** As I work on files, I will document their functionality, APIs, and the "dependency graph" relevant to my tasks to build a focused, evolving design document of the areas I've engaged with.

4. **.cursor/rules/rules.mdc** - Cursor-specific configuration

### "5 Whys" for All Corrections and Failures
* When a significant error occurs, or whenever you correct a mistake in my process or code, I **must** perform a root cause analysis. The resulting "Actionable Lesson" **must** be documented in `.cursor/rules/lessons.mdc` to prevent that class of error in the future.

### Synchronize with Cursor Settings
* After we modify this `CLAUDE.md` file, I will remind you to copy its contents into the "Edit an AI Rule" section of the Cursor settings to ensure my behavior reflects the most current protocol.

### Proactive Rule and Lesson Documentation
* After completing any significant debugging session, integration test work, or bug fixes, I must proactively update both `CLAUDE.md` and `.cursor/rules/lessons.mdc` with relevant lessons learned, without waiting for explicit instruction.
* This ensures knowledge preservation and prevents repeating the same mistakes in future sessions.


## Critical Lessons

### Code Review and Integration
- **Validate AI Instructions Have Implementation**: Always verify documented AI capabilities have code
- **Trace Data Flow End-to-End**: Follow complete pipeline from AI → parsing → state → storage
- **Never Assume Documentation Equals Implementation**: Always verify with actual code
- **Integration Testing Over Syntax**: Treat reviews as functional tests, not just code quality
- **Search for Missing Implementations**: Search codebase for referenced tokens/features

### Validation Commands
```bash
# Search for documented features in prompts
grep -r "__DELETE__" prompts/
grep -r "special_token" prompts/

# Verify implementation exists
grep -r "__DELETE__" *.py
grep -r "process.*special_token" *.py

# Check for dynamic usage
grep -r "json.dumps.*default=" *.py
grep -r "getattr" *.py
```

### Code Review Analysis Completeness
**MANDATORY**: Extract ALL comments from any code review
- Never assume "suppressed" means unimportant
- If user quotes specific text you haven't mentioned, acknowledge immediately
- Complete analysis format:
  - Total comments: X (Y visible, Z suppressed)
  - List EVERY comment with status (Addressed/Pending)
  - Explicitly search for hidden/suppressed comments
- Cross-file consistency verification

### Common Pitfalls
- **Empty String Handling**: Use `if value is not None:` not `if value:`

### AI Instruction Priority and Ordering
**CRITICAL RULE**: When AI systems have multiple competing instructions, instruction ORDER determines compliance:
- **Most critical instructions MUST be loaded first** (e.g., state management, core protocols)
- Later instructions can override or distract from earlier ones
- Long instruction sets suffer from "instruction fatigue" where later rules are ignored
- Always prioritize core functionality over stylistic preferences in prompt ordering

**Lesson**: AI was ignoring state update requirements because game state instructions were loaded LAST after lengthy narrative instructions. Moving them FIRST fixed the core state update failure.

### Data Corruption Pattern Analysis
**CRITICAL RULE**: When encountering ANY data corruption bug, treat it as a systemic issue requiring comprehensive pattern analysis:
- Search for ALL similar corruption patterns across the codebase (e.g., `str()` conversions, type changes)
- Identify ALL code paths that process the same data structures
- Apply the principle: "If there's one bug of this type, there are likely others"
- Create data integrity audit checklists for similar data structures

**Lesson**: Missed NPC data corruption because I focused on isolated `__DELETE__` bug without auditing all `str()` conversions that could corrupt structured data.

### Temporary Fix Protocol - NEVER GLOSS OVER
**CRITICAL RULE**: When implementing ANY temporary fix or workaround:
1. **IMMEDIATELY flag it** - "⚠️ TEMPORARY FIX: This will break when [specific scenario]"
2. **PROPOSE permanent solution in same message** - Don't wait to be asked
3. **Run the checklist**:
   - [ ] Will this work from a fresh clone?
   - [ ] Will this work in CI/CD?
   - [ ] Will this work for other developers?
   - [ ] Will this work next week/month?
   - [ ] What are ALL the failure scenarios?
4. **Create the permanent fix NOW** - Not "we could fix it" but actually implement it
5. **Document assumptions** - "This assumes [X] which will fail if [Y]"

**Example**: When copying files manually for deployment:
- ❌ BAD: "I copied the files, deployment works now"
- ✅ GOOD: "⚠️ TEMPORARY FIX: I manually copied world/ to fix deployment. This WILL BREAK on next deploy from fresh clone. Creating permanent fix to deploy.sh now..."

**Lesson**: Manually copied world directory for deployment without immediately fixing deploy.sh, causing future deployment failures. Always think about sustainability, not just immediate success.

### Task Completion Protocol (December 2024)
**CRITICAL REDEFINITION**: Task completion is NOT just solving the user's immediate problem. Task completion includes all mandatory follow-up actions as core requirements.

**NEW TASK COMPLETION DEFINITION**: A task is only complete when ALL of the following steps are finished:
1. ✅ **Solve user's immediate problem** (the obvious part)
2. ✅ **Update CLAUDE.md or .cursor/rules/lessons.mdc** (for any error resolution, bug fix, or correction)
3. ✅ **Update memory with lesson learned** (to prevent immediate recurrence)
4. ✅ **Self-audit compliance with all documented procedures** (verify I followed all protocols)
5. ✅ **Consider task truly complete** (only after all above steps)

**MANDATORY COMPLETION CHECKLIST**: For every error resolution, bug fix, or user correction, I MUST follow this checklist:
- [ ] Problem solved to user satisfaction
- [ ] Lessons documented in .cursor/rules/lessons.mdc
- [ ] Memory updated with prevention strategy  
- [ ] Self-audit: "Did I follow all mandatory procedures?"
- [ ] Task marked complete only after ALL steps finished

**SELF-AUDITING REQUIREMENT**: At the end of every significant interaction, I must explicitly ask myself: "Did I follow all mandatory procedures?" This is not optional - it's part of systematic process discipline.

**ENFORCEMENT PRINCIPLE**: Documentation is part of the solution, not administrative overhead. Any error resolution that doesn't include lessons capture is an incomplete solution that increases the risk of recurrence.

### Codebase Exploration Protocol
When working with any codebase, ALWAYS:
1. **Run tests FIRST** - Establish baseline of what works/breaks
2. **Read project documentation** - CLAUDE.md, README, etc.
3. **Investigate specific issues** - Only then dive into code

### Test Truth and Architectural Validation
**CRITICAL RULE**: Test names and claims MUST match what is actually being tested:
- **Import Verification**: Always verify and log which module is being imported in tests
- **Dependency Presence**: Check that required dependencies exist before claiming approach works
- **Negative Testing**: Test validation REJECTION cases, not just success cases
- **Test-First Architecture**: Write validation tests BEFORE making architectural decisions

**Enforcement**:
1. Add module verification assertions: `assert 'pydantic' in str(Model.__module__)`
2. Log test metadata: what's being tested, which modules, what dependencies
3. Create Architecture Decision Tests (ADTs) that verify decisions remain valid
4. Never trust test names - verify the implementation matches the claim

**Lesson**: We made critical architectural decisions based on "Pydantic" tests that were actually testing a non-Pydantic implementation, leading to a cascade of errors.

### Integration Before Testing
When asked to test features:
1. **STOP and verify prerequisites** - Is feature integrated?
2. **Question test readiness** - "Is this connected to main flow?"
3. **Propose integration first** if components aren't wired up
4. **Never test disconnected code** - Wastes time, gives false results

### Task Analysis Protocol
**CRITICAL RULE**: When receiving any user request:
1. **Analyze before executing** - Understand the full context and purpose
2. **Check assumptions** - "What needs to be true for this task to be meaningful?"
3. **Identify dependencies** - "What other components must be working?"
4. **Communicate gaps** - Immediately inform user of missing prerequisites
5. **Propose correct sequence** - Suggest the right order of operations

**Example**: User says "run tests" → Check if feature is integrated → If not, say "The feature needs integration first. Should I integrate it before testing?"

### Execution Mode vs Analysis Mode
**CRITICAL RULE**: Never let "execution mode" override critical thinking:
- **Red flags that you're in pure execution mode**:
  - Implementing exactly what's asked without questioning feasibility
  - Continuing despite discovering blockers
  - Prioritizing "showing progress" over "achieving goals"
  - Running tests that you know will fail
- **Required mindset**: Every task requires both analysis AND execution
- **Recovery**: If you catch yourself in pure execution mode, STOP and reassess

**Lesson**: Blindly executed test comparisons without integrating the code being tested, wasting time on meaningless results. Discovered entity tracking modules weren't connected but continued testing anyway.

### Data Structure Schema Enforcement
When AI systems generate structured data:
- **Schema Definition**: Clearly define expected structures (lists vs dicts)
- **Remove Contradictions**: Remove conflicting examples that confuse AI
- **Type Validation**: Add explicit rules forbidding type changes
- **Example Clarity**: Provide concrete correct vs incorrect examples

### Meta-Rule Violations
**Documentation Failure**: Failure to document lessons after mistakes compounds the original problem
- Lessons documentation is NOT OPTIONAL
- Must happen immediately, automatically, every time
- Without user prompting

**CRITICAL RULE VIOLATION DOCUMENTED (December 2024)**: After completing a full 10 Whys analysis of the enhanced components failure, I initially failed to automatically update lessons.mdc as required. This is a **direct violation** of the core Automatic Rule Updates mandate.

**ROOT CAUSE**: Lack of systematic process discipline - I operate without internal mechanisms to ensure compliance with documented procedures, leading to selective rule following and task completion blindness.

**ENFORCEMENT**: Failure to document lessons after mistakes is itself a critical failure that compounds the original problem. The lessons documentation requirement is **NOT OPTIONAL** and must happen immediately, automatically, every time - without user prompting.

### Code Review Blind Spots
**Empty String Handling**:
- ❌ BAD: `if value:` - Skips empty strings which may be valid
- ✅ GOOD: `if value is not None:` - Preserves empty strings
- Add specific tests for empty string cases when refactoring

### Configuration Synchronization
When creating related files with similar settings:
1. Add sync comments: `# Keep in sync with other_file.py`
2. Consider extracting to shared configuration file
3. Verify lists/constants match across files

### AI-Assisted Development Time
- **Code Generation**: 1-10 minutes by AI
- **Review and Integration**: 5-15 minutes
- **Testing and Iteration**: 15-45 minutes
- **Documentation**: 5-10 minutes
- Never estimate based on manual coding time

## User Command Shortcuts

### Context Estimation
**Triggers**: "est", "estimate context", "context usage", "how much context left"

**Response Format**: When user requests context estimation, provide:
1. **Session Context Usage**: Estimated percentage of my context window used
2. **Breakdown by Category**:
   - System messages & instructions: ~X%
   - File reading operations: ~X%
   - Conversation history: ~X%
   - Tool outputs & responses: ~X%
3. **Remaining Capacity**: Percentage and practical limitations
4. **Usage Indicators**: What suggests approaching limits
5. **Recommendations**: Whether to continue or start fresh session

**Example Response**:
```
Session Context Usage: ~75-85% used
- System messages: ~10-15%
- File operations: ~30-40%  
- Conversation: ~25-35%
- Tool outputs: ~10-15%

Remaining: ~15-25% (good for a few more operations)
Recommendation: Approaching limits, consider fresh session for major work
```

### Milestone Commands
**Triggers**: "milestones N", "milestones suggest"

**Command: `milestones N`**
- Break current work into N specific milestones
- After completing each milestone:
  - Update scratchpad file (`roadmap/scratchpad_[branch_name].md`)
  - Commit and push to GitHub to save state
  - Provide status update before proceeding
- Each milestone should be independently valuable and testable

**Command: `milestones suggest`**
- Analyze task complexity and dependencies
- Suggest optimal number of milestones (typically 3-7)
- Provide rationale for suggested breakdown
- List each milestone with:
  - Clear objective
  - Estimated effort/complexity
  - Dependencies on other milestones
  - Success criteria

Example Response:
```
Based on task complexity, I suggest 4 milestones:

Milestone 1: Foundation Setup (Low complexity)
- Set up base infrastructure
- Create initial test framework
- Success: Basic tests passing

Milestone 2: Core Implementation (High complexity)
- Implement main feature logic
- Add error handling
- Success: Feature works end-to-end

Milestone 3: Integration (Medium complexity)
- Connect to existing systems
- Update documentation
- Success: Feature integrated with main app

Milestone 4: Polish & Deploy (Low complexity)
- Add edge case handling
- Performance optimization
- Success: Production-ready code
```

### Copilot Review
**Trigger**: "copilot review"
- List all open PRs with CodeRabbit comments
- For each PR with feedback:
  - Fetch and display suggestions using `gh pr view [PR_NUMBER] --comments`
  - Filter comments from 'coderabbitai' user
  - Analyze each suggestion and determine action:
    - Implemented (make the suggested change)
    - Explained (provide rationale for not implementing)
  - Apply accepted changes to codebase
  - Add explanatory comments for rejected suggestions
- Create commits addressing feedback
- Update PR with summary of changes made
- Push updates to respective PR branches

### GitHub Copilot Comment Response Protocol
**MANDATORY**: Reply to every individual GitHub Copilot comment on PRs
- Address each line-level comment with specific acknowledgment
- Status updates: Clearly indicate Fixed/Acknowledged/Future
- Implementation details: Explain how issues were resolved
- Follow-up actions: Document any remaining work
- Never ignore "suppressed" or "low confidence" comments

### Import Statement Rules
**MANDATORY**: All imports at top of module, never inline
- **NO INLINE IMPORTS**: Never inside functions, methods, or test methods
- **Module-Level Only**: After docstring, before any code
- **Shared Imports**: Import once at top, reference throughout
- **Example Violation**: `import constants` inside test method
- **Correct Pattern**: `import constants` at module top

## API Error Prevention

**CRITICAL**: Do Not Print Code or File Content
- Never include actual code text or long blocks in responses
- Use file_path:line_number references instead
- Provide concise status updates only
- Large text blocks cause "empty message" API errors

## Project-Specific Lessons

### Flask & Web Development
- **Flask SPA Routing**: Must have catch-all route to serve `index.html` for non-API paths
- **CSS/JS Caching**: Restart dev server and hard refresh to avoid stale assets
- **Cache-busting**: Use query params in production

### Python Environment
- **venv & PEP 668**: Always work in project virtual environment
- **Shell Config**: Changes to `.bashrc` require sourcing or new session
- **Package Installation**: May need `python3-venv` via system package manager

### AI & LLM
- **System Prompts**: Detailed, explicit, well-structured prompts crucial for AI performance
- **Instruction Priority**: Most critical instructions must be loaded first
- **Instruction Fatigue**: Long prompts cause later rules to be ignored

### Development Workflow
- **Simple-First Approach**: Always evaluate simplest solution before complex refactoring
- **Tool Failure Recovery**: If command fails twice, try alternative approach
- **File Corruption Recovery**: Fetch from main branch and restart

### Testing Best Practices
- Always offer to run tests after implementing features
- Use faster AI models for integration tests
- Create tests that verify behavior, not exact content

## User Communication

### Markdown Output
When asked for "markdown format", provide raw unrendered text in code block:
```markdown
# Example PR Description
- Change 1
- Change 2
```


## Additional Documentation

### Technical Lessons
For specific technical failures, code patterns, and detailed incident analysis, see:
- **.cursor/rules/lessons.mdc** - Detailed technical lessons and incident analysis

### Cursor Integration
For Cursor-specific configuration and behavior, see:
- **.cursor/rules/rules.mdc** - Cursor editor specific settings

### Quick Reference
- **Test Commands**: `TESTING=true vpython mvp_site/test_file.py` (from project root)
- **New Branch**: `./integrate.sh`
- **Run All Tests**: `./run_tests.sh`
- **Deploy**: `./deploy.sh` or `./deploy.sh stable`

### Lessons Archive Process
**When to Archive**:
- Archive lessons quarterly (January, April, July, October)
- Archive when lessons.mdc exceeds 2500 lines
- Archive when switching to new major version or year

**Archive Process**:
1. Create archive file: `lessons_archive_YYYY.mdc`
2. Move all lessons older than 30 days to archive
3. Keep CRITICAL patterns as generalized rules in main file
4. Add reference in lessons.mdc header pointing to archive

**Archive Structure**:
```
lessons_archive_YYYY.mdc
├── Q1 (January-March)
├── Q2 (April-June)
├── Q3 (July-September)
└── Q4 (October-December)
```

**Referencing Archived Content**:
- Add "See also: lessons_archive_YYYY.mdc#section" for related patterns
- Maintain searchability across all archive files
- Never delete archives - they contain valuable historical context