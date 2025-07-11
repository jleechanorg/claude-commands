# GitHub Copilot Comments Command

**Purpose**: Focus exclusively on GitHub Copilot bot suggestions and automated code review comments

**Usage**: `/copilot [PR#]`

**Action**: Extract and address only GitHub Copilot automated suggestions

**Implementation**:
1. **Extract Copilot Comments Only**:
   - Filter for comments from `github-actions[bot]` or `copilot[bot]`
   - Include both high and low confidence suggestions
   - Include "suppressed" suggestions that are normally hidden
   - Focus on automated code quality suggestions

2. **Categorize Copilot Suggestions**:
   - **Security**: Potential security vulnerabilities
   - **Performance**: Code optimization suggestions
   - **Style**: Code formatting and consistency
   - **Logic**: Potential bugs or logic errors
   - **Best Practices**: Language-specific improvements

3. **Display Format**:
   ```
   COPILOT SUGGESTION #1 (High Confidence)
   File: main.py:655
   Type: Logic Error
   Suggestion: Consider simplifying the guard by treating all non-positive hp_max values
   Status: ❌ Not addressed
   ```

4. **Quick Fix Protocol**:
   - Apply obvious improvements immediately
   - Flag complex suggestions for discussion
   - Skip style-only changes unless critical
   - Focus on security and logic fixes first

5. **Response Format**:
   - ✅ **APPLIED**: Suggestion implemented as recommended
   - 🔄 **MODIFIED**: Implemented with adjustments
   - ❌ **SKIPPED**: Not applicable or intentionally ignored
   - 🤔 **NEEDS REVIEW**: Requires human decision

**Key Differences from /review**:
- Only processes automated bot suggestions
- Faster, focused on quick wins
- No manual review comments
- No comprehensive code review
- Emphasis on automated tooling feedback

**Example Output**:
```
Found 5 GitHub Copilot suggestions:

1. [SECURITY] File: auth.py:45
   "Potential SQL injection vulnerability"
   → ✅ APPLIED: Switched to parameterized queries

2. [STYLE] File: utils.js:120
   "Use const instead of let for immutable variable"
   → ❌ SKIPPED: Minor style issue, not critical

3. [LOGIC] File: game_state.py:255
   "Division by zero possible when hp_max is 0"
   → ✅ APPLIED: Added guard clause for hp_max > 0
```

**For Full PR Review**: Use `/review [PR#]` for comprehensive review including all comments, tests, and systematic fixes.