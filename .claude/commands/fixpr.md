# /fixpr Command - Intelligent PR Fix Analysis

**Usage**: `/fixpr <PR_NUMBER> [--comments FILE] [--auto-apply]`

**Purpose**: Analyze CI failures and merge conflicts, then intelligently determine fixes. With `--auto-apply`, automatically implement fixes based on bot suggestions.

## Description

The `/fixpr` command is a hybrid Python + Markdown command that leverages Claude's intelligence to analyze and fix PR issues. The Python component (fixpr.py) collects data, while this Markdown component provides the intelligence for analysis and decision-making.

## Workflow

### Step 1: Data Collection (Automated by fixpr.py)

The Python component automatically:
1. Runs three-layer CI verification (local, GitHub, merge-tree)
2. Detects merge conflicts
3. Compares CI results to find discrepancies
4. Outputs comparison data to `/tmp/copilot_${SANITIZED_BRANCH}/`
5. **NEW**: With `--auto-apply`, extracts and applies fixes from bot comments
6. **NEW**: Re-runs CI after applying fixes to verify success

### Step 2: Intelligent Analysis (This Document)

Read the collected data:
```bash
# Check what fixpr.py collected (using PR #941 standard)
BRANCH=$(git branch --show-current)
SANITIZED_BRANCH=$(echo "$BRANCH" | sed 's/[^a-zA-Z0-9._-]/_/g' | sed 's/^[.-]*//g')
cat /tmp/copilot_${SANITIZED_BRANCH}/fixes.json
cat /tmp/copilot_${SANITIZED_BRANCH}/comparison.json
cat /tmp/copilot_${SANITIZED_BRANCH}/conflicts.json
# NEW: Check applied fixes if --auto-apply was used
cat /tmp/copilot_${SANITIZED_BRANCH}/applied_fixes.json
```

**Auto-Fix Mode**: When `--auto-apply` is enabled:
- Bot comments are analyzed for actionable fixes
- Code suggestions (```suggestion blocks) are automatically applied
- Pattern-based fixes (pagination, imports) are implemented
- CI is re-run to verify fixes worked
- Results are saved to `applied_fixes.json`

### Step 3: Analyze CI Discrepancies

**Key Intelligence Required**: When GitHub CI and local CI disagree, determine why:

1. **GitHub FAIL, Local PASS**:
   - Possible flaky test (network timeouts, race conditions)
   - Environment differences (missing env vars, different OS)
   - External dependencies (API rate limits, service availability)
   - **Action**: Suggest retry or environment fix

2. **GitHub PASS, Local FAIL**:
   - Outdated local branch
   - Missing local dependencies
   - Configuration differences
   - **Action**: Update branch or fix local setup

3. **Different Test Counts**:
   - Test discovery issues
   - Conditional test execution
   - **Action**: Investigate test configuration

### Step 4: Conflict Resolution Strategy

Analyze conflict patterns from conflicts.json:

**Safe to Auto-Resolve**:
- Import statement conflicts (usually just ordering)
- Whitespace/formatting conflicts
- Comment-only conflicts
- Version number conflicts in expected files

**Requires Manual Review**:
- Logic conflicts in critical files
- Database schema changes
- API contract modifications
- Security-related code

### Step 5: Generate Fix Plan

Based on analysis, create actionable fix plan:

1. **For CI Failures**:
   ```python
   # If test failure is environment-related
   - Update test configuration
   - Add missing environment variables
   - Fix import paths

   # If test failure is code-related
   - Fix the actual bug
   - Update test expectations
   - Add error handling
   ```

2. **For Merge Conflicts**:
   ```python
   # For each conflict in conflicts.json
   - Determine if auto-resolvable
   - Preserve functionality from both branches
   - Prefer incoming changes for features
   - Prefer current changes for bug fixes
   ```

### Step 6: Execute Fixes

After analysis, use appropriate tools to apply fixes:

1. **For Auto-Resolvable Conflicts**:
   ```bash
   # Use Edit tool to resolve specific conflicts
   # Preserve functionality from both sides
   ```

2. **For CI Fixes**:
   ```bash
   # Apply specific fixes based on failure type
   # Update configuration files
   # Fix failing tests
   ```

3. **For Environment Issues**:
   ```bash
   # Update .env files
   # Fix dependency versions
   # Add missing configuration
   ```

### Step 7: Verification

After applying fixes:
1. Re-run fixpr.py to verify fixes worked
2. Check that CI would now pass
3. Ensure no new issues introduced

### Step 8: Auto-Fix Results Analysis (When --auto-apply Used)

Review the `applied_fixes.json` to understand what was automatically fixed:

```json
{
  "applied": [
    {
      "type": "code_suggestion",
      "path": "file.py",
      "line": 123,
      "comment_id": "123456"
    }
  ],
  "failed": [],
  "total": 1
}
```

**Success Criteria**:
- All bot suggestions successfully applied
- CI status improved after fixes
- No new failures introduced
- Code still follows project standards

**Common Auto-Fix Patterns**:
1. **Import Cleanup**: Removes unused imports flagged by linters
2. **Pagination Handling**: Adds empty result checks
3. **Type Annotations**: Adds missing type hints
4. **Error Handling**: Adds try-except blocks where suggested
5. **Code Formatting**: Applies style suggestions

## Intelligence Guidelines

### When Analyzing CI Failures

1. **Pattern Recognition**:
   - Look for timeout patterns → Likely flaky test
   - Import errors → Missing dependencies
   - Permission errors → Environment issue
   - Assertion failures → Real bug

2. **Context Integration**:
   - Check comment_context for user concerns
   - Consider PR description for intent
   - Review recent changes for cause

3. **Risk Assessment**:
   - High risk: Core business logic, auth, payments
   - Medium risk: UI, non-critical features
   - Low risk: Tests, documentation, formatting

### When Resolving Conflicts

1. **Preservation Principle**:
   - Never lose functionality
   - Combine changes when possible
   - Document resolution rationale

2. **Priority Rules**:
   - Security fixes > Feature additions
   - Bug fixes > Refactoring
   - User-facing > Internal changes

3. **Communication**:
   - Add comments explaining resolution
   - Flag complex merges for review
   - Document assumptions made

## Example Analysis

```json
// Given comparison.json showing discrepancy:
{
  "github_ci": {"status": "FAILURE", "test_results": {"failed": 2}},
  "local_ci": {"status": "SUCCESS", "test_results": {"failed": 0}},
  "discrepancies": [{"type": "status_mismatch"}]
}

// Intelligence Applied:
// - GitHub shows 2 failures that local doesn't
// - Likely environment-specific (API keys, network)
// - Check failed test names for "api" or "integration"
// - If true, suggest environment configuration fix
// - If false, investigate test isolation issues
```

## Error Recovery

If analysis fails:
1. Check all JSON files were created
2. Verify fixpr.py completed successfully
3. Fall back to manual analysis mode
4. Report specific failure point

## Integration with Orchestrator

This command is designed to work with `/copilot` orchestrator:
- Receives PR number and optional context
- Outputs actionable fixes
- Can be called multiple times
- Maintains state through JSON files

Remember: The goal is intelligent analysis that a mechanical Python script cannot provide. Use Claude's understanding of code, context, and intent to make smart decisions about fixes.
