# /fixpr Command - Intelligent PR Fix Analysis

**Usage**: `/fixpr <PR_NUMBER> [--auto-apply]`

**Purpose**: Analyze CI failures and merge conflicts using GitHub MCP tools and existing commands, then intelligently determine and apply fixes.

## Description

The `/fixpr` command is a pure markdown orchestrator that leverages Claude's intelligence and existing tools to analyze and fix PR issues. It uses GitHub MCP tools, git commands, and Claude Code CLI capabilities directly without requiring external Python scripts.

## Workflow

### Step 1: Data Collection (Using GitHub MCP & Git Commands)

Automatically collect PR data using existing tools:

```bash
# Get PR details using GitHub MCP
mcp__github-server__get_pull_request(owner="jleechan2015", repo="worldarchitect.ai", pull_number=PR_NUMBER)

# Get PR files and status
mcp__github-server__get_pull_request_files(owner="jleechan2015", repo="worldarchitect.ai", pull_number=PR_NUMBER)
mcp__github-server__get_pull_request_status(owner="jleechan2015", repo="worldarchitect.ai", pull_number=PR_NUMBER)

# Get comments and reviews for analysis
mcp__github-server__get_pull_request_comments(owner="jleechan2015", repo="worldarchitect.ai", pull_number=PR_NUMBER)
mcp__github-server__get_pull_request_reviews(owner="jleechan2015", repo="worldarchitect.ai", pull_number=PR_NUMBER)

# Check local branch status and conflicts
git status
git diff --check
git merge-tree $(git merge-base HEAD main) HEAD main
```

### Step 2: Intelligent Analysis (Direct Claude Analysis)

Claude analyzes the collected data directly using natural language understanding:

**CI Status Analysis**:
- GitHub CI vs local test discrepancies
- Failure pattern recognition (timeouts, imports, assertions)
- Environment-specific issues identification

**Merge Conflict Analysis**:
- Conflict complexity assessment
- Auto-resolvable vs manual review categorization
- Risk level evaluation for each conflict

**Bot Comment Analysis**:
- Extract actionable suggestions from code review bots
- Identify implementable fixes (imports, formatting, patterns)
- Prioritize by criticality and safety

### Step 3: Fix Strategy Determination

Based on analysis, determine appropriate fixes:

**For CI Failures**:
1. **Test Environment Issues**:
   - Missing dependencies: Update requirements
   - Environment variables: Check .env configuration
   - Race conditions: Add proper wait conditions

2. **Code Issues**:
   - Import errors: Fix import statements
   - Assertion failures: Fix logic or update tests
   - Type errors: Add proper type annotations

**For Merge Conflicts**:
1. **Safe Auto-Resolution**:
   - Import statement reordering
   - Whitespace/formatting conflicts
   - Non-functional comment conflicts

2. **Manual Review Required**:
   - Business logic conflicts
   - Database schema changes
   - Security-related modifications

### Step 4: Execute Fixes

Apply fixes using existing Claude Code CLI tools:

**For Code Changes**:
```bash
# Use Edit or MultiEdit tools to apply specific fixes
# Example: Fix import statements
Edit(file_path="path/to/file.py", old_string="old import", new_string="new import")

# Example: Resolve simple merge conflicts
Edit(file_path="conflicted_file.py", old_string="<<<<<<< HEAD\ncode1\n=======\ncode2\n>>>>>>> branch", new_string="merged_code")
```

**For Environment Issues**:
```bash
# Update configuration files
Edit(file_path=".env", old_string="OLD_VAR=value", new_string="NEW_VAR=new_value")

# Update dependencies
Edit(file_path="requirements.txt", old_string="package==1.0", new_string="package==1.1")
```

**For Test Fixes**:
```bash
# Run tests locally to verify fixes
./run_tests.sh

# Run specific test files
TESTING=true vpython mvp_site/test_specific.py
```

### Step 5: Verification & Re-analysis

After applying fixes:

```bash
# Check git status
git status
git diff

# Re-run local tests
./run_tests.sh

# Check if conflicts resolved
git merge-tree $(git merge-base HEAD main) HEAD main

# Re-fetch PR status if needed
mcp__github-server__get_pull_request_status(owner="jleechan2015", repo="worldarchitect.ai", pull_number=PR_NUMBER)
```

## Auto-Apply Mode

When `--auto-apply` is specified:

1. **Safe Fixes Only**: Only apply fixes that are low-risk:
   - Import statement cleanup
   - Whitespace/formatting fixes
   - Obvious typo corrections
   - Bot-suggested code improvements

2. **Validation Required**: Always verify before applying:
   - Preserve existing functionality
   - Don't modify business logic
   - Keep security-related code unchanged

3. **Incremental Application**: Apply one fix at a time and test:
   - Apply fix
   - Run relevant tests
   - Verify no new issues
   - Continue to next fix

## Intelligence Guidelines

### Pattern Recognition for CI Failures

**Timeout Patterns** → Likely flaky tests:
- Network timeouts in API tests
- Database connection timeouts
- External service unavailability

**Import/Environment Patterns** → Configuration issues:
- ModuleNotFoundError
- Missing environment variables
- Path resolution failures

**Assertion Patterns** → Logic bugs:
- Unexpected values in tests
- Changed API responses
- Modified business logic

### Conflict Resolution Principles

**Preservation Priority**:
1. Never lose functionality from either branch
2. Combine features when possible
3. Prefer bug fixes over new features
4. Maintain security and stability

**Risk Assessment**:
- **Low Risk**: Comments, documentation, formatting
- **Medium Risk**: Non-critical features, UI changes
- **High Risk**: Authentication, payments, data handling

### Communication and Documentation

For all fixes applied:
1. Document the reasoning behind each resolution
2. Add comments explaining complex merges
3. Flag high-risk changes for human review
4. Provide clear commit messages

## Example Usage

```bash
# Basic analysis
/fixpr 1234

# With auto-apply for safe fixes
/fixpr 1234 --auto-apply
```

## Integration with Other Commands

This command works seamlessly with:
- `/copilot` - For comprehensive PR review
- `/commentreply` - For responding to review comments
- `/push` - For creating and updating PRs
- `/test` - For running validation tests

## Error Recovery

If analysis encounters issues:
1. Fall back to manual analysis prompts
2. Use partial data collection if MCP tools fail
3. Provide clear error messages with next steps
4. Suggest alternative approaches

## Architecture Benefits

**Pure Orchestration**: No custom Python scripts needed
**Tool Integration**: Leverages existing GitHub MCP and CLI tools
**Intelligence Focus**: Claude provides the analysis and decision-making
**Maintainability**: Uses established patterns from other .md commands
**Reliability**: Depends on proven tools rather than custom data collectors

Remember: This command focuses on intelligent analysis and safe automation. Complex conflicts and high-risk changes should always be flagged for human review.
