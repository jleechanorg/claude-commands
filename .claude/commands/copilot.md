# GitHub Copilot Comments Command

**Purpose**: Make PR mergeable by resolving ALL GitHub comments and fixing ALL failing tests

**Usage**: `/copilot [PR#]`

**Action**: Comprehensive PR cleanup - address ALL automated suggestions, bot comments, and test failures

**Implementation**:
1. **Extract ALL Bot Comments**:
   - Filter for comments from `github-actions[bot]`, `copilot[bot]`, and other bots
   - Include both high and low confidence suggestions
   - Include "suppressed" suggestions that are normally hidden
   - Extract inline code review comments AND general PR comments
   
2. **Check Test Status**:
   - Run `gh pr checks <PR#>` to see failing tests
   - Identify specific test failures from CI/CD output
   - Track both unit test and integration test failures
   - Note any linting or type checking errors

3. **Categorize ALL Issues**:
   - **Test Failures**: Unit tests, integration tests, UI tests
   - **Build Errors**: Compilation, linting, type checking
   - **Security**: Potential security vulnerabilities
   - **Performance**: Code optimization suggestions
   - **Style**: Code formatting and consistency
   - **Logic**: Potential bugs or logic errors
   - **Best Practices**: Language-specific improvements

4. **Display Format**:
   ```
   TEST FAILURE #1
   Test: test_game_state.py::test_invalid_hp
   Error: AssertionError: Expected exception not raised
   Status: ❌ Not fixed
   
   COPILOT SUGGESTION #2 (High Confidence)
   File: main.py:655
   Type: Logic Error
   Suggestion: Consider simplifying the guard by treating all non-positive hp_max values
   Status: ❌ Not addressed
   ```

5. **Fix Priority Order**:
   1. **Failing Tests** - MUST fix ALL to make PR mergeable
   2. **Build/Lint Errors** - Required for CI to pass
   3. **Security Issues** - Critical vulnerabilities
   4. **Logic Errors** - Bugs that affect functionality
   5. **Performance** - Optimization opportunities
   6. **Style/Best Practices** - Nice to have but not blocking

6. **Response Format**:
   - ✅ **FIXED**: Test now passes / Issue resolved
   - 🔄 **MODIFIED**: Implemented with adjustments
   - ❌ **BLOCKED**: Cannot fix due to external dependency
   - 🤔 **NEEDS DISCUSSION**: Requires design decision

**🚨 GOAL: Make PR Mergeable**:
- ALL tests must pass (100% success rate)
- ALL CI/CD checks must be green
- ALL critical bot suggestions addressed
- NO blocking issues remaining

**Key Differences from /review**:
- Focused on making PR mergeable, not comprehensive review
- Prioritizes test failures and CI/CD blockers
- Addresses ALL automated feedback (not just Copilot)
- Faster turnaround for getting PR ready to merge
- No manual review comments unless blocking merge

**Example Output**:
```
PR #523 Mergeability Report:

❌ FAILING TESTS (3):
1. test_game_state.py::test_invalid_hp - AssertionError
   → ✅ FIXED: Added validation for negative HP values
2. test_integration.py::test_api_auth - 401 Unauthorized
   → ✅ FIXED: Updated test headers with proper auth tokens
3. test_ui_login.py::test_signin_flow - Timeout
   → ✅ FIXED: Increased wait time for page load

⚠️ GITHUB BOT SUGGESTIONS (5):
1. [SECURITY] auth.py:45 - "Potential SQL injection"
   → ✅ FIXED: Switched to parameterized queries
2. [LOGIC] game_state.py:255 - "Division by zero possible"
   → ✅ FIXED: Added guard clause for hp_max > 0
3. [STYLE] utils.js:120 - "Use const instead of let"
   → ❌ SKIPPED: Non-blocking style issue
4. [DUPLICATION] execute.md:82 - "Redundant checkpoint info"
   → ✅ FIXED: Consolidated duplicate sections
5. [PERFORMANCE] main.py:340 - "Inefficient loop"
   → 🔄 MODIFIED: Optimized with list comprehension

✅ PR STATUS: All blockers resolved - ready to merge!
```

**For Comprehensive Code Review**: Use `/review [PR#]` for detailed analysis beyond merge requirements.