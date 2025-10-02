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

### 🔴 Phase 1: RED - Exact Error Reproduction

**Action Steps:**
**MANDATORY**: Must reproduce the EXACT same error the user mentioned before proceeding

### Phase 2: Step 1: Error Analysis

**Action Steps:**
1. Parse the exact error message from user input
2. Identify the file, line number, and error type
3. Understand the context and conditions that trigger the error

### Phase 3: Step 2: Reproduction Setup

**Action Steps:**
1. Create minimal test case that reproduces the exact error
2. Verify the error occurs with deterministic error signature (not byte-for-byte stack traces)
3. Document reproduction steps and environment
4. Use normalized error signatures: `ErrorType | ["key", "tokens"] | file:function`

### Phase 4: Step 3: Red Confirmation

**Action Steps:**
1. Confirm test fails with expected error message
2. Verify test accurately reproduces the issue

### 🔧 Phase 2: CODE - Fix Implementation

**Action Steps:**
**Implementation**: Write minimal code change to fix the reproduced error

### Phase 6: Step 1: Root Cause Analysis

**Action Steps:**
1. Identify why the error occurs (scope issues, import problems, etc.)
2. Determine minimal fix approach
3. Consider side effects and compatibility

### Phase 7: Step 2: Code Changes

**Action Steps:**
1. Make targeted fix to resolve the specific error
2. Avoid unnecessary changes or refactoring
3. Maintain existing functionality

### Phase 8: Step 3: Implementation Verification

**Action Steps:**
1. Ensure fix addresses root cause
2. Verify no new errors introduced
3. Test fix in isolation

### 🟢 Phase 3: GREEN - Working Verification

**Action Steps:**
**Validation**: Confirm the fix works and error is completely resolved

### Phase 10: Step 1: Direct Fix Test

**Action Steps:**
1. Run the exact same scenario that caused the original error
2. Verify error no longer occurs
3. Confirm expected behavior works
4. Control randomness/time (fixed seed, frozen time) to ensure determinism

### Phase 11: Step 2: Regression Testing

**Action Steps:**
1. Run existing tests to ensure no breaks
2. Test related functionality
3. Verify broader system stability
4. Re-run the focused test N times to detect flakiness

### Phase 12: Step 3: Green Confirmation

**Action Steps:**
1. Confirm all tests pass after implementation
2. Verify fix resolves the original issue

### Phase 1 (RED):

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

### Phase 2 (CODE):

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

### Phase 3 (GREEN):

**Action Steps:**
python3 $PROJECT_ROOT/main.py

### 🔍 Phase 4: CONSENSUS - Flow Validation

**Action Steps:**
**Validation**: Verify the entire red-green debug flow was legitimate and properly executed

### Phase 17: Step 1: Consensus Check

**Action Steps:**
1. Run `/consensus` to validate the debugging approach was sound
2. Ensure all phases were properly executed with evidence
3. Confirm the fix addresses the root issue comprehensively

### Phase 18: Step 3: Flow Legitimacy

**Action Steps:**
1. Verify proper RED-GREEN-REFACTOR flow was followed
2. Confirm all phases completed with evidence

### ✅ RED phase: Actual error reproduced with evidence

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

### ✅ CODE phase: Minimal, targeted fix implemented

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

### ✅ GREEN phase: Complete resolution verified

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps.

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

**RULE 1**: Cannot proceed to CODE phase without exact error reproduction in RED
**RULE 2**: Cannot proceed to GREEN phase without implementing a fix in CODE
**RULE 3**: Must verify exact same error is resolved, not just "similar" behavior
**RULE 4**: Fix must be minimal and targeted to the specific error
**RULE 5**: Green phase must demonstrate working functionality, not just absence of error

## Example Workflow

```bash

# User reports: "UnboundLocalError: cannot access local variable 'os'"

# Reproduce exact error and capture normalized signature

python3 $PROJECT_ROOT/main.py

# ✅ Signature: UnboundLocalError | ["cannot access local variable", "os"] | $PROJECT_ROOT/main.py:main

# Add failing test first, then minimal fix for the os import issue

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

**Key Difference from `/tdd`**: While `/tdd` drives development with failing tests for new features, `/redgreen` starts with reproducing actual bugs or errors. It then systematically fixes them with verification, concluding with `/consensus` validation of the entire debugging flow.
