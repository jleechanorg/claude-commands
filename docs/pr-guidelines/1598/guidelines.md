# PR #1598 Guidelines - CI Timeout Configuration

## 🎯 PR-Specific Principles

**Multi-Level Timeout Architecture**: Implement comprehensive timeout protection at multiple levels (job, suite, individual tests) to prevent CI resource exhaustion and provide fast feedback loops.

**State Tracking Integrity**: When implementing timeout wrappers, ensure state tracking prevents result processing conflicts and maintains accurate statistics.

**Solo Developer Security Context**: Apply trusted source filtering for standard CI utilities while maintaining security vigilance for user input and dynamic command construction.

## 🚫 PR-Specific Anti-Patterns

### ❌ **Function Export Before Definition**
```bash
# WRONG: Export function before it's defined
export -f run_tests_with_timeout  # Function doesn't exist yet
run_tests_with_timeout() {
    # Function definition
}
```

### ✅ **Function Export After Definition**
```bash
# CORRECT: Define function first, then export
run_tests_with_timeout() {
    # Function definition
}
export -f run_tests_with_timeout  # Now function exists
```

### ❌ **Array Export in Bash**
```bash
# WRONG: Cannot export arrays in bash
test_files=("test1.py" "test2.py")
export test_files  # This fails - arrays cannot be exported
```

### ✅ **Direct Array Access in Same Shell**
```bash
# CORRECT: Access arrays directly within same shell context
test_files=("test1.py" "test2.py")
export tmp_dir enable_coverage max_workers  # Only export scalars
# Use test_files array directly without export
```

### ❌ **Timeout State Override**
```bash
# WRONG: Allow result processing to override timeout state
if ! timeout 600 run_tests; then
    failed_tests=$total_tests  # Set timeout state
fi
# Later: process individual results without checking timeout state
for result in results/*; do
    failed_tests=$((failed_tests + failures))  # OVERWRITES timeout state
done
```

### ✅ **Protected Timeout State Tracking**
```bash
# CORRECT: Prevent result processing from overriding timeout status
suite_timed_out=false
if ! timeout 600 run_tests; then
    suite_timed_out=true
    failed_tests=$total_tests
fi

if [ "$suite_timed_out" = true ]; then
    # Skip individual result processing - timeout state preserved
else
    # Normal result processing
fi
```

## 📋 Implementation Patterns for This PR

**Timeout Hierarchy Implementation**:
1. **Job-Level**: GitHub Actions `timeout-minutes: 30`
2. **Suite-Level**: `TEST_SUITE_TIMEOUT=600` (10 minutes)
3. **Individual-Level**: Per-test timeout mechanisms

**State Management Pattern**:
- Use boolean flags (`suite_timed_out=false`) for clear state tracking
- Implement separate processing paths for timeout vs normal completion
- Prevent state override through conditional processing

**Export Safety Pattern**:
- Define all functions before any export statements
- Only export scalar variables, never arrays
- Use direct array access within the same shell context

## 🔧 Specific Implementation Guidelines

**Bash Timeout Wrapper Requirements**:
1. Always define functions before exporting them
2. Never attempt to export array variables
3. Implement timeout state tracking with boolean flags
4. Provide separate processing paths for timeout scenarios
5. Include comprehensive error reporting for debugging

**CI Timeout Configuration**:
1. Implement multi-level timeout protection
2. Use reasonable defaults (10 minutes for test suites)
3. Provide clear error messages when timeouts occur
4. Include system resource guidance in timeout error messages

**Quality Gates**:
- ✅ Function export order verified
- ✅ Array export attempts eliminated
- ✅ Timeout state tracking protected from override
- ✅ Multi-level timeout hierarchy implemented
- ✅ Comprehensive error handling included

## 🔍 Evidence from This PR

**Lines 794-795**: Correct function export placement after definitions
**Line 795**: Only scalar variables exported, arrays accessed directly
**Lines 798, 811, 827**: Boolean flag prevents timeout state override
**Lines 799-812**: Comprehensive timeout error reporting with debugging guidance
**Line 776**: Configurable timeout with reasonable 10-minute default

This PR demonstrates proper implementation of complex bash timeout wrappers with state management and provides a template for similar CI reliability improvements.
