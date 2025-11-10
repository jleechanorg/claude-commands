---
description: Red-Green Debug & Fix Command
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### 🔴 Phase 1: RED – Test-First Error Reproduction

**MANDATORY**: Use a test-first approach to catch and reproduce the error before proceeding.

#### Step 1: Error Analysis
1. Parse the exact error message from user input.
2. Identify the file, line number, and error type.
3. Understand the context and conditions that trigger the error.

#### Step 2: Find Existing Tests
1. Search for existing tests that should catch this error.
2. Look for integration (real services), functional (fixtures), and unit tests.
3. Use judgment to determine the most appropriate test type.
4. Document which existing tests are relevant.

#### Step 3: Confirm Tests Reproduce Error
1. Run existing tests to check if they catch the error.
2. Verify the tests fail with the expected error message.
3. Document whether existing tests successfully reproduce the issue.

#### Step 4: Update or Create Tests (If Needed)
1. **ONLY IF** existing tests do not catch the error: update or create new tests.
2. Choose the right level (integration, functional, unit) for the regression test.
3. Create the minimal test case that reproduces the exact error.
4. Use normalized error signatures: `ErrorType | ["key", "tokens"] | file:function`.
5. Document why new or updated tests were needed.

#### Step 5: Confirm Tests Fail
1. Run the tests to confirm they fail with the expected error message.
2. Verify the failure occurs with a deterministic error signature (avoid brittle stack traces).
3. Ensure the test accurately reproduces the issue.
4. Document reproduction steps and environment.

### 🔧 Phase 2: CODE – Fix Implementation

Write the minimal code change required to fix the reproduced error.

#### Step 1: Root Cause Analysis
1. Identify why the error occurs (scope issues, import problems, etc.).
2. Determine the minimal fix approach.
3. Consider side effects and compatibility.

#### Step 2: Code Changes
1. Make the targeted fix that resolves the specific error.
2. Avoid unnecessary changes or refactoring.
3. Maintain existing functionality.

#### Step 3: Implementation Verification
1. Ensure the fix addresses the root cause.
2. Verify no new errors were introduced.
3. Test the fix in isolation when possible.

### 🟢 Phase 3: GREEN – Test-Driven Verification

Confirm the tests pass and the error is completely resolved.

#### Step 1: Confirm Tests Pass
1. **PRIMARY VALIDATION**: Run the tests that were failing in Phase 1.
2. Verify all tests now pass after the fix.
3. Confirm the specific error is no longer occurring.
4. Control randomness/time (fixed seed, frozen time) to ensure determinism.

#### Step 2: Direct Fix Test
1. Run the same scenario that caused the original error.
2. Verify the error no longer occurs.
3. Confirm the expected behavior works.

#### Step 3: Regression Testing
1. Run existing tests to ensure nothing else broke.
2. Test related functionality that could have been affected.
3. Verify broader system stability.
4. Re-run the focused test multiple times to detect flakiness.

#### Step 4: Green Confirmation
1. **CONFIRM ALL TESTS PASS**: primary validation that the fix is complete.
2. Verify the fix resolves the original issue.
3. Document test results and success evidence.

### 🔍 Phase 4: CONSENSUS – Flow Validation

Verify the entire red-green debug flow was legitimate and properly executed.

#### Step 1: Consensus Check
1. Run `/consensus` to validate the debugging approach was sound.
2. Ensure all phases were properly executed with evidence.
3. Confirm the fix addresses the root issue comprehensively.

#### Step 2: Flow Legitimacy
1. Verify the RED → CODE → GREEN flow was followed without shortcuts.
2. Confirm all phases completed with evidence.

### ✅ Phase Completion Checklist
- RED phase: Actual error reproduced with evidence.
- CODE phase: Minimal, targeted fix implemented.
- GREEN phase: Complete resolution verified.

## 📋 REFERENCE DOCUMENTATION

# Red-Green Debug & Fix Command

**Purpose**: Three-phase debugging workflow: Red (reproduce exact error) → Code (fix implementation) → Green (verify working)

**Action**: Systematic debugging with exact error reproduction and fix validation

**Usage**: `/redgreen` or `/rg`

# Must see this exact error before proceeding:

# UnboundLocalError: cannot access local variable 'X' before it is associated with a value

# ImportError: cannot import name 'Y' from 'Z'

# etc.

```

**CRITICAL RULE**: Phase 2 cannot begin until the exact error is reproduced

# Must see successful execution:

# ✅ Original error scenario now works

# ✅ No new errors introduced

# ✅ Expected functionality confirmed

```

## 🧪 Test Creation Guidelines

**Reference `/tdd` command for test writing style and patterns**

### Test Structure

Use the comprehensive matrix testing approach from `/tdd`:
- Create failing tests that reproduce the exact error
- Write minimal code to make tests pass
- Ensure test coverage for the specific bug scenario

### Test Categories

1. **Error Reproduction Tests**: Verify the bug can be triggered
2. **Fix Validation Tests**: Confirm the fix resolves the issue
3. **Regression Tests**: Ensure no new problems introduced
- Name tests with a regression prefix and identifier, e.g., `test_regression_<issue-id>_<behavior>()`

## 🚨 Critical Rules

**RULE 1**: Must search for existing tests BEFORE attempting to reproduce error manually
**RULE 2**: Cannot proceed to CODE phase without failing tests that reproduce the error
**RULE 3**: Cannot proceed to GREEN phase without implementing a fix in CODE
**RULE 4**: Must verify the same error is resolved via passing tests
**RULE 5**: Fix must be minimal and targeted to the specific error
**RULE 6**: Green phase must demonstrate all tests pass, not just absence of error
**RULE 7**: Consider test types: integration tests (real services), functional tests (fixtures), unit tests - use judgment

## Example Workflow

```bash

# User reports: "UnboundLocalError: cannot access local variable 'os'"

# Step 1: Search for existing tests
# Look for tests in $PROJECT_ROOT/tests/ that test main.py functionality

# Step 2: Run existing tests to see if they catch the error
TESTING=true python $PROJECT_ROOT/tests/test_main.py

# Step 3: If tests don't exist or don't catch it, create/update tests
# Consider: integration test (real service), functional test (fixtures), or unit test

# Step 4: Confirm tests fail
TESTING=true python $PROJECT_ROOT/tests/test_main.py
# ✅ Signature: UnboundLocalError | ["cannot access local variable", "os"] | $PROJECT_ROOT/main.py:main

# Step 5: Implement minimal fix for the os import issue

# Step 6: Confirm tests pass
TESTING=true python $PROJECT_ROOT/tests/test_main.py
# ✅ All tests pass
# ✅ Confirmed: Application starts successfully

```

### Step 2: Documentation Review

- Validate that error reproduction was genuine and accurate
- Confirm the fix is minimal and targeted as required
- Verify testing demonstrates complete resolution

# Must confirm legitimate debugging process:

# ✅ CONSENSUS: Flow integrity validated

```

**CRITICAL RULE**: Phase 4 provides final validation that the red-green process was executed with integrity and produces genuine bug fixes, not superficial changes.

## Integration Points

- **Inherits test patterns from `/tdd`**: Use matrix testing and systematic coverage
- **Focuses on specific bugs**: Unlike `/tdd` which is feature-driven, this is error-driven
- **Minimal fix approach**: Targeted fixes rather than comprehensive refactoring
- **Error reproduction requirement**: Must reproduce exact error before fixing
- **Flow validation via `/consensus`**: Ensures debugging integrity and legitimacy

---

**Key Difference from `/tdd`**: While `/tdd` drives development with failing tests for new features, `/redgreen` takes a test-first approach to debugging actual bugs or errors:

1. **Search existing tests first** - Check if tests already catch the error
2. **Run tests to confirm reproduction** - Verify tests fail with the error
3. **Create/update tests only if needed** - Don't duplicate existing test coverage
4. **Confirm tests fail** - Ensure error is reproduced
5. **Fix** - Implement minimal fix
6. **Confirm tests pass** - Primary validation of fix

The workflow emphasizes finding and using existing tests before creating new ones, and uses test types (integration/functional/unit) based on judgment. It concludes with `/consensus` validation of the entire debugging flow.
