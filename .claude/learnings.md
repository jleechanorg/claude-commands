# Claude's Learning Log

This file tracks all learnings from corrections, mistakes, and self-realizations. Referenced by CLAUDE.md.

## Command Execution

### Python/venv
- ✅ **ALWAYS** use `source venv/bin/activate && python`, never `vpython`
- ✅ Playwright IS installed in venv - activate venv to use it
- ✅ Run Python scripts from project root, not subdirectories

### Testing
- ✅ Browser tests: Use `source venv/bin/activate && python testing_ui/test_*.py`
- ✅ All tests: Prefix with `TESTING=true` environment variable
- ✅ Playwright can take real screenshots - no simulation needed
- ✅ Some test scripts handle TESTING=true internally, but always better to be explicit
- ✅ Correct format: `source venv/bin/activate && TESTING=true python testing_ui/test_*.py`

## Common Misconceptions

### Tools Available
- ❌ "Playwright not installed" - It IS installed, just needs venv
- ❌ "Can't run browser tests" - Can run them with proper setup
- ❌ "Need to simulate" - Real tools are available
- ❌ "Firebase not available" - Firebase IS available for testing
- ❌ "Gemini API not available" - Gemini API IS available for testing
- ❌ "Real APIs cost too much" - Testing with real APIs is permitted
- ⚠️ **PATTERN**: I keep assuming tools aren't available when they are!

### File Paths
- ✅ Always use absolute paths from project root
- ✅ Run commands from project root, not subdirectories

## Self-Correction Patterns

When I say these phrases, I'm recognizing a mistake:
- "Let me correct that..." → Document the correction
- "Oh, I should have..." → Add as rule
- "Actually, I need to..." → Update relevant section
- "My mistake..." → Learn and document

## Code Quality & Duplication

### Import Statement Patterns
- ❌ **REPEATED MISTAKE**: Using modules without importing them (e.g., `os` and `sys`)
- ✅ **FIX**: Always verify imports at top of file before using modules
- 🚨 **CRITICAL**: This pattern appears in multiple test files across PRs
- **Example**: `test_think_block_protocol.py` uses `os.path` without `import os`

### CSS/Styling Duplication
- ❌ **REPEATED MISTAKE**: Defining unused CSS selectors (e.g., `.planning-block-header` never used)
- ❌ **REPEATED MISTAKE**: Hardcoding inline styles in JavaScript instead of CSS classes
- ✅ **FIX**: Audit CSS files for unused selectors before PR submission
- ✅ **FIX**: Move inline styles to CSS classes for maintainability
- **Example**: `app.js` line 118 uses inline styles instead of CSS classes

### DRY Principle Violations
- ❌ **PATTERN**: Code duplication across similar functions/files
- ❌ **PATTERN**: Copy-paste code without consolidating common logic
- ❌ **SPECIFIC MISTAKES**: Hardcoded dictionary keys instead of constants (e.g., 'session_header', 'planning_block')
- ❌ **SPECIFIC MISTAKES**: Duplicate structured fields extraction code in multiple places
- ❌ **SPECIFIC MISTAKES**: Duplicate HTML generation logic instead of helper functions
- ❌ **SPECIFIC MISTAKES**: Duplicate documentation/schemas instead of single source of truth
- ✅ **FIX**: Extract common patterns into utility functions
- ✅ **FIX**: Use module-level constants for repeated strings
- ✅ **FIX**: Create extraction methods for structured fields
- ✅ **FIX**: Create HTML generation helpers for UI components
- 🚨 **ENFORCEMENT**: Always check for similar existing code before writing new

### File Organization Anti-Patterns
- ❌ **REPEATED MISTAKE**: Creating test files without checking existing test structure
- ❌ **REPEATED MISTAKE**: Adding files to wrong directories (especially mvp_site/)
- ❌ **SPECIFIC MISTAKE**: Creating random directories (e.g., worldarchitect/) without justification
- ✅ **FIX**: Follow existing project structure patterns
- ✅ **FIX**: Ask user for file placement when uncertain
- ✅ **FIX**: Remove unnecessary directory structures before PR submission

## Recent Self-Learnings

### 2025-01-09
- ✅ **REPEATED MISTAKES IN PR #447**: Import statements, unused CSS, inline styles
- ✅ **PATTERN**: Same types of mistakes appear across multiple files in single PR
- ✅ **LEARNING**: Need systematic code quality checklist before PR submission
- ✅ **LEARNING**: Copilot reviewer identifies patterns I should catch proactively
- ✅ **USER COMMENTS SHOW MORE DUPLICATION**: Constants vs strings, extraction methods, duplicate docs
- ✅ **PATTERN**: I create duplicated code across files instead of extracting utilities
- ✅ **PATTERN**: I hardcode strings instead of using constants
- ✅ **PATTERN**: I create mysterious directories without user approval

### 2025-01-08
- ✅ Created overly complex Python-based self-learning system when simple documentation updates work better
- ✅ Should focus on real, immediate documentation updates rather than elaborate frameworks
- ✅ /learn command implementation should be simple and direct
- ✅ Tried `vpython` again despite knowing it doesn't exist - muscle memory from other projects
- ✅ Keep trying to `cd` into directories instead of running from project root
- ✅ **PATTERN**: Default to changing directories is wrong - always run from root!
- ✅ I tend to simulate mistakes for demonstration rather than making real ones
- ✅ Real learning comes from actual command execution, not simulated scenarios

### 2025-01-09
- ✅ User preemptively corrected me about Firebase/Gemini availability before I made the mistake
- ✅ **PATTERN**: I tend to say APIs "cost too much" or "aren't available" when they actually are
- ✅ Similar to Playwright pattern - assuming tools aren't available when they are
- ✅ Firebase and Gemini APIs ARE available for testing and should be used
- ✅ Need to stop using cost as an excuse to avoid real API testing
- ✅ **VERIFIED**: Successfully tested Firebase campaign creation and Gemini story generation
- ✅ **REAL RESULTS**: Firebase stored campaign `dss3zJKUrBAnOOwPZqPw`, Gemini generated full story response with game mechanics

### 2025-07-09 - Git Merge Conflict Resolution
- ✅ **CRITICAL**: GitHub shows conflicts when your branch is behind the latest main, even if local merge seems clean
- ✅ **BRANCH AWARENESS**: Always verify which branch your PR is associated with - was on wrong branch initially
- ✅ **REBASE > MERGE**: For PRs, `git rebase origin/main` provides cleaner history than merge commits
- ✅ **FORCE PUSH SAFETY**: Use `--force-with-lease` instead of `--force` to prevent overwriting others' work
- ✅ **CONFLICT RESOLUTION**: Understand what each side represents (HEAD vs incoming commit)
- ✅ **DIVERGENCE PATTERNS**: "Your branch and 'origin/branch' have diverged" means rebase/merge needed
- ✅ **GITHUB BEHAVIOR**: GitHub compares against current main, not main at time of branching

### 2025-07-09 - Test Failure Patterns and Mock Service Updates
- ✅ **MOCK SERVICE EVOLUTION**: When adding new parameters to service methods, ALL mock services must be updated
- ✅ **SIGNATURE MISMATCH**: Tests fail when mock functions don't match production signatures
- ✅ **MODULE-LEVEL FUNCTIONS**: Some tests import mock services as modules, requiring module-level delegation functions
- ✅ **TEST ISOLATION**: Tests need proper setup - campaigns must exist before adding story entries
- ✅ **ASSERTION PATTERNS**: Use `assert_called()` + `call_args` instead of `assert_called_with()` for flexible parameter checking
- ✅ **SIDE EFFECT FUNCTIONS**: Mock side_effect functions must match the exact signature of the real function
- ✅ **BACKWARDS COMPATIBILITY**: When adding optional parameters, ensure they're truly optional with defaults
- ✅ **CI vs LOCAL**: Tests passing locally doesn't guarantee CI success - always push and verify GitHub Actions

## What Actually Works (Proven by Tests)

### Browser Testing Capabilities
- ✅ **Flask server management** - Tests can start/stop servers automatically
- ✅ **Real browser automation** - Playwright controls actual Chrome browser
- ✅ **Screenshot capture** - Real PNGs saved to `/tmp/worldarchitectai/browser/`
- ✅ **Test authentication** - `?test_mode=true&test_user_id=X` bypasses auth
- ✅ **Multi-step workflows** - Can navigate wizards, fill forms, click buttons
- ✅ **DOM inspection** - Can check element visibility, classes, content

### Stop Saying These Things
- ❌ "Can't run browser tests" → YES WE CAN
- ❌ "Playwright not installed" → IT IS INSTALLED
- ❌ "Need to simulate" → NO, USE REAL BROWSER
- ❌ "Can't take screenshots" → REAL SCREENSHOTS WORK
- ❌ "Can't use real Firebase" → FIREBASE IS AVAILABLE FOR TESTING
- ❌ "Can't use real Gemini" → GEMINI API IS AVAILABLE FOR TESTING
- ❌ "Costs too much money" → TESTING WITH REAL APIS IS PERMITTED
- ❌ "Conflicts are resolved locally" → CHECK GITHUB FOR REAL STATUS
- ❌ "Local merge worked" → GITHUB MIGHT STILL SHOW CONFLICTS

## Coverage Analysis

### 2025-01-08 Coverage Findings
- ✅ Coverage improved from 59% to 67% since last measurement
- ✅ Use `./coverage.sh` for unit tests only (default, fast ~76s)
- ✅ Use `./coverage.sh --integration` to include integration tests
- ✅ HTML report saved to `/tmp/worldarchitectai/coverage/index.html`
- ✅ Integration tests show 0% coverage when not included (by design)
- ✅ 124 unit tests all passing, excellent test suite health

### Coverage Discrepancies
- ⚠️ CLAUDE.md had outdated coverage numbers (showed 85% for files that are 70-74%)
- ✅ Updated CLAUDE.md with actual current measurements
- ✅ Coverage has more total statements now (21k vs 16k) indicating codebase growth

## Categories for Future Learning

1. **Command Syntax** - Correct usage of commands
2. **Tool Availability** - What's actually installed/available
3. **Path Management** - Where to run commands from
4. **Environment Setup** - venv, TESTING=true, etc.
5. **API/SDK Usage** - Correct imports and methods
6. **Git Workflow** - Branch management, PR process
7. **Testing Protocols** - How to properly run tests
8. **Merge Conflict Resolution** - Proper rebase/merge techniques

## Git Merge Conflict Resolution Protocol

### Quick Reference Commands
```bash
# 1. Verify correct branch
git branch --show-current
gh pr list --state open --author @me

# 2. Check for divergence
git fetch origin
git status
git log --oneline origin/main ^HEAD | head -5

# 3. Rebase against main
git rebase origin/main
# (resolve conflicts manually)
git add <resolved_files>
git rebase --continue

# 4. Force push safely
git push origin <branch> --force-with-lease

# 5. Verify on GitHub
gh pr view <number>
```

### Conflict Resolution Strategy
1. **Identify the conflict sections**: Look for `<<<<<<< HEAD`, `=======`, `>>>>>>> commit`
2. **Understand what each side represents**: HEAD = your branch, commit = incoming changes
3. **Make informed decisions**: Don't just pick one side - often need to combine both
4. **Test the resolution**: Ensure functionality still works after resolving
5. **Remove all conflict markers**: No `<<<<<<<`, `=======`, or `>>>>>>>` should remain

### When to Rebase vs Merge
- **Rebase**: For PRs, cleaner history, when you want to "replay" your changes on top of main
- **Merge**: When you want to preserve the branching history, for feature branches

### GitHub Behavior Understanding
- GitHub always compares your PR branch against the **current** main branch
- Even if your local branch merges cleanly with your local main, GitHub might show conflicts
- This happens when main has moved forward since you last synced
- The solution is to rebase/merge against the latest main and force push

---
*Auto-updated when Claude learns from corrections*
