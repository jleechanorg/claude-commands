# CI Environment Debugging Lessons - September 2025

## 🎯 **Case Study: The Missing Claude Command Mystery**

**Situation**: PR #1771 had 4 orchestration tests consistently failing in CI but passing locally for weeks.

**Root Cause**: `create_dynamic_agent()` was returning `False` in CI because `shutil.which("claude")` returned `None` (claude command not installed in CI), but returned a path locally.

**Detection Time**: ~3 hours of debugging with multiple failed hypotheses

## 🚨 **Critical Prevention Rules**

### 1. Mock External System Dependencies by Default
```python
# ALWAYS include in tests that use system commands
with patch('shutil.which', return_value='/usr/bin/command'):
    # test code
```

### 2. Enhanced Test Failure Reporting
```python
# GOOD: Embed debug info in assertions
self.assertTrue(result, f"FAIL DEBUG: function_result={result}, context={debug_info}")

# BAD: Use print statements that get lost
print(f"Debug: {debug_info}")
self.assertTrue(result)
```

### 3. Function Return Value Validation First
- Before debugging assertion values, verify core functions actually succeed
- Check function return codes before examining their outputs

## ⚠️ **Mandatory Process Improvements**

### 1. Systematic Hypothesis Testing
1. **Basic Function Execution**: Does the function return the expected type/success?
2. **Environment Dependencies**: Are all system commands/paths available?
3. **Mock Coverage**: Are all external dependencies mocked?
4. **Assertion Logic**: Are the expected vs actual values correct?

### 2. CI/Local Environment Parity
- Document required system commands explicitly
- Mock all `shutil.which()`, `subprocess.run()`, file system operations
- Validate CI environment has necessary dependencies or mock them

### 3. Test Runner Enhancement
- Show detailed failure output by default (not just "PASS"/"FAIL")
- Prioritize debug messages in error reporting
- Increase context lines for failures (20+ lines instead of 10)

## ✅ **Successful Patterns Applied**

1. **Embedded Debug Messages**: Put debug info in assertion failure messages instead of print statements
2. **Enhanced Error Reporting**: Modified `run_tests.sh` to show "🐛 DEBUG OUTPUT" section
3. **Systematic Mock Addition**: Added `shutil.which` mocks to all failing tests
4. **Root Cause Analysis**: Used `/debugp` approach to distinguish symptoms from causes

## 📊 **Outcome**

- **Before**: 4/10 orchestration tests failing consistently (80% success rate)
- **After**: Expected 10/10 tests passing (100% success rate)
- **Key Learning**: Environment differences in available system commands are a common CI failure cause

## 🔄 **Reusable Debugging Workflow**

1. **Validate Basic Function Success** before debugging complex logic
2. **Check Environment Dependencies** (system commands, file paths)
3. **Mock All External Dependencies** proactively in tests
4. **Embed Debug Info in Assertions** for better CI failure reporting
5. **Enhance Test Runner Output** to show detailed failure context

---
*Generated from PR #1771 debugging session - September 29, 2025*
