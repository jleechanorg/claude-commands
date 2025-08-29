# Enhanced Test Command

**Purpose**: Intelligent test execution with PR-based test selection and modifiers

**Action**: Execute tests intelligently based on PR changes or with custom modifiers

**Usage**: 
- `/test` - Run tests for files changed in current PR (default)
- `/test [pattern]` - Run tests matching pattern (e.g. `/test testsABC`)
- `/test --full` - Run complete test suite
- `/test --integration` - Include integration tests

**Implementation**:

## Phase 1: Intelligent Test Selection (Default Behavior)
1. **PR Change Analysis**:
   - Get current branch: `git branch --show-current`
   - Find changed files: `git diff --name-only origin/main...HEAD`
   - Map changed files to relevant test files using intelligent heuristics
   - Select subset of tests that should run based on changes

2. **Test Mapping Logic**:
   - Python file changes → corresponding test files
   - Frontend changes → frontend/UI test files  
   - Config changes → integration test files
   - If >20 files changed → fall back to full suite

## Phase 2: Test Execution with Modifiers
1. **Parse Command Modifiers**:
   - Extract test pattern from command (e.g. `testsABC` from `/test testsABC`)
   - Support flags: `--full`, `--integration`, `--coverage`
   - Default to intelligent selection if no modifiers

2. **Execute Tests with Output Logging**:
   - Run `./run_tests.sh` with appropriate flags
   - Output automatically saved to `/tmp/{branch_name}/run_tests_{timestamp}.txt`
   - Show real-time output to user
   - Parse results for pass/fail analysis

## Phase 3: Pattern Matching (When Pattern Specified)
1. **Test File Discovery**:
   - Find all test files matching pattern: `find . -name "*{pattern}*" -path "*/test*" -name "test_*.py"`
   - Validate test files exist and are executable
   - Run specific test subset

2. **Execution Command Building**:
   - Build command: `./run_tests.sh {matched_files}`
   - Handle multiple matches appropriately
   - Provide feedback on which tests are being run

## Phase 4: Results Analysis & CI Check
1. **Local Test Analysis**:
   - Parse test output for pass/fail counts
   - Identify failing tests and root causes
   - Fix any failing tests immediately

2. **GitHub CI Status Check**:
   - Check current PR/branch status with `gh pr checks [PR#]`
   - If GitHub tests failing, download logs and fix issues
   - Verify GitHub tests pass after fixes
   - Commands: `gh pr checks`, `gh run view --log-failed`

## Phase 5: Completion Criteria
- All selected tests pass (local)
- All GitHub CI checks pass
- Never dismiss failing tests as "minor"  
- Debug root causes of failures
- Both local and CI must be green before completing
- Provide summary of test execution and results

## Smart Test Selection Examples:
- Changes to `mvp_site/main.py` → Run `test_main*.py` files
- Changes to `mvp_site/gemini_service.py` → Run `test_gemini*.py` files  
- Changes to frontend files → Run frontend test suite
- Changes to > 20 files → Full test suite
- No changes detected → Run minimal smoke test suite
