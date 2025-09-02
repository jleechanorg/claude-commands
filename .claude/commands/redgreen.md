# Red-Green Debug & Fix Command

**Purpose**: Three-phase debugging workflow: Red (reproduce exact error) → Code (fix implementation) → Green (verify working)

**Action**: Systematic debugging with exact error reproduction and fix validation

**Usage**: `/redgreen` or `/rg`

## 🔴 Phase 1: RED - Exact Error Reproduction

**MANDATORY**: Must reproduce the EXACT same error the user mentioned before proceeding

### Step 1: Error Analysis
- Parse the exact error message from user input
- Identify the file, line number, and error type
- Understand the context and conditions that trigger the error

### Step 2: Reproduction Setup
- Create minimal test case that reproduces the exact error
- Verify the error occurs with deterministic error signature (not byte-for-byte stack traces)
- Document reproduction steps and environment
- Use normalized error signatures: `ErrorType | ["key", "tokens"] | file:function`

### Step 3: Red Confirmation
```bash
# Must see this exact error before proceeding:
# UnboundLocalError: cannot access local variable 'X' before it is associated with a value
# ImportError: cannot import name 'Y' from 'Z'
# etc.
```

**CRITICAL RULE**: Phase 2 cannot begin until the exact error is reproduced

## 🔧 Phase 2: CODE - Fix Implementation

**Implementation**: Write minimal code change to fix the reproduced error

### Step 1: Root Cause Analysis
- Identify why the error occurs (scope issues, import problems, etc.)
- Determine minimal fix approach
- Consider side effects and compatibility

### Step 2: Code Changes
- Make targeted fix to resolve the specific error
- Avoid unnecessary changes or refactoring
- Maintain existing functionality

### Step 3: Implementation Verification
- Ensure fix addresses root cause
- Verify no new errors introduced
- Test fix in isolation

## 🟢 Phase 3: GREEN - Working Verification

**Validation**: Confirm the fix works and error is completely resolved

### Step 1: Direct Fix Test
- Run the exact same scenario that caused the original error
- Verify error no longer occurs
- Confirm expected behavior works
- Control randomness/time (fixed seed, frozen time) to ensure determinism

### Step 2: Regression Testing
- Run existing tests to ensure no breaks
- Test related functionality
- Verify broader system stability
- Re-run the focused test N times to detect flakiness

### Step 3: Green Confirmation
```bash
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

# Phase 1 (RED):
# Reproduce exact error and capture normalized signature
python3 mvp_site/main.py
# ✅ Signature: UnboundLocalError | ["cannot access local variable", "os"] | mvp_site/main.py:main

# Phase 2 (CODE):
# Add failing test first, then minimal fix for the os import issue

# Phase 3 (GREEN):
python3 mvp_site/main.py
# ✅ Confirmed: Application starts successfully
```

## Integration Points

- **Inherits test patterns from `/tdd`**: Use matrix testing and systematic coverage
- **Focuses on specific bugs**: Unlike `/tdd` which is feature-driven, this is error-driven
- **Minimal fix approach**: Targeted fixes rather than comprehensive refactoring
- **Error reproduction requirement**: Must reproduce exact error before fixing

---

**Key Difference from `/tdd`**: While `/tdd` drives development with failing tests for new features, `/redgreen` starts with reproducing actual bugs/errors and systematically fixing them with verification.
