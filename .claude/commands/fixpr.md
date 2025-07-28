# /fixpr Command - Intelligent PR Fix Analysis

**Usage**: `/fixpr <PR_NUMBER> [--auto-apply]`

**Purpose**: Make GitHub PRs mergeable by analyzing and fixing CI failures, merge conflicts, and bot feedback - without merging.

## Description

The `/fixpr` command leverages Claude's natural language understanding to analyze PR blockers and fix them. The goal is to get the PR into a mergeable state (all checks passing, no conflicts) but **never actually merge it**. It orchestrates GitHub tools and git commands through intent-based descriptions rather than explicit syntax.

## Workflow

### Step 1: Gather Repository Context

Dynamically detect repository information from the git environment:
- Extract the repository owner and name from git remote (handling both HTTPS and SSH URL formats)
- Determine the default branch without assuming it's 'main' (could be 'master', 'develop', etc.)
- Validate the extraction succeeded before proceeding
- Store these values for reuse throughout the workflow

💡 **Implementation hints**:
- Repository URLs come in formats like `https://github.com/owner/repo.git` or `git@github.com:owner/repo.git`
- Default branch detection should have fallbacks for fresh clones
- Always quote variables in bash to handle spaces safely

### Step 2: Fetch Critical GitHub PR Data

**MANDATORY**: Fetch these specific items from GitHub to understand what's blocking mergeability:

1. **CI State & Test Failures**:
   - Get all CI check results from GitHub (passing/failing/pending)
   - For any failing checks, fetch the specific error messages and logs
   - Identify which tests are broken and their failure reasons
   - Distinguish between required checks and optional ones

2. **Merge Conflicts**:
   - Check GitHub's mergeable status (MERGEABLE/CONFLICTING/UNKNOWN)
   - If conflicting, identify exactly which files have conflicts
   - Fetch the conflict markers and understand what's clashing
   - Determine if conflicts are with the base branch or other PRs

3. **Bot Feedback & Review Comments**:
   - Fetch all automated bot comments (Copilot, CodeRabbit, etc.)
   - Get human reviewer comments and requested changes
   - Identify which feedback is blocking vs suggestions
   - Check if any reviews have "Request Changes" status

4. **PR Metadata**:
   - Current PR state (open/closed/merged)
   - Which branch it's targeting
   - Protection rules that might block merging
   - Any failing status checks beyond CI

The goal is to gather everything that GitHub shows as preventing the green "Merge" button from being available.

### Step 3: Analyze Issues with Intelligence

Examine the collected data to understand what needs fixing:

**CI Status Analysis**:
- Distinguish between flaky tests (timeouts, network issues) and real failures
- Identify patterns in failures (missing imports, assertion errors, environment issues)
- Compare GitHub CI results with local test runs to spot environment-specific problems

**Merge Conflict Analysis**:
- Assess conflict complexity - are they simple formatting issues or complex logic changes?
- Categorize conflicts by risk level (low risk: comments/formatting, high risk: business logic)
- Determine which conflicts can be safely auto-resolved vs requiring human review

**Bot Feedback Processing**:
- Extract actionable suggestions from automated code reviews
- Prioritize fixes by impact and safety
- Identify quick wins vs changes requiring careful consideration

### Step 4: Apply Fixes Intelligently

Based on the analysis, apply appropriate fixes:

**For CI Failures**:
- **Environment issues**: Update dependencies, fix missing environment variables, adjust timeouts
- **Code issues**: Correct import statements, fix failing assertions, add type annotations
- **Test issues**: Update test expectations, fix race conditions, handle edge cases

**For Merge Conflicts**:
- **Safe resolutions**: Combine imports from both branches, merge non-conflicting configuration
- **Function signatures**: Preserve parameters from both versions when possible
- **Complex conflicts**: Flag for human review with clear explanation of the conflict

**For Bot Suggestions**:
- Apply formatting and style fixes
- Implement suggested error handling improvements
- Add missing documentation or type hints

### Step 5: Verify Mergeability Status

After applying fixes, verify progress toward mergeability:

1. **Re-fetch GitHub Status**:
   - Check if CI checks are now passing
   - Verify mergeable status changed from CONFLICTING to MERGEABLE
   - Confirm no new test failures were introduced
   - Ensure bot feedback has been addressed

2. **Local Verification**:
   - Run tests locally to confirm fixes work
   - Check git status for uncommitted changes
   - Verify no conflicts remain with the base branch

3. **Push and Monitor**:
   - Push fixes to the PR branch
   - Wait for GitHub to re-run CI checks
   - Monitor the PR page to see blockers clearing

4. **Success Criteria**:
   - All required CI checks show green checkmarks
   - GitHub shows "This branch has no conflicts"
   - No "Changes requested" reviews blocking merge
   - The merge button would be green (but we don't click it!)

If blockers remain, iterate through the analysis and fix process again until the PR is fully mergeable.

## Auto-Apply Mode

When `--auto-apply` is specified, the command operates more autonomously:

**Safe Fixes Only**:
- Import statement corrections
- Whitespace and formatting cleanup
- Documentation updates
- Bot-suggested improvements that don't change logic

**Always Preserve**:
- Existing functionality from both branches
- Business logic integrity
- Security-related code patterns

**Incremental Approach**:
- Apply one category of fixes at a time
- Test after each change
- Stop if tests fail unexpectedly

## Intelligence Guidelines

### CI Failure Patterns

**Flaky Test Indicators**:
- Timeouts in external API calls
- Intermittent database connection failures
- Time-dependent test failures

**Real Issues Requiring Fixes**:
- Import errors (ModuleNotFoundError)
- Assertion failures with consistent patterns
- Type errors and missing dependencies

### Merge Conflict Resolution Strategy

**Preservation Priority**:
1. Never lose functionality - combine features when possible
2. Prefer bug fixes over new features in conflicts
3. Maintain backward compatibility
4. Keep security improvements from both branches

**Risk-Based Approach**:
- **Low Risk**: Documentation, comments, formatting, test additions
- **Medium Risk**: UI changes, non-critical features, configuration updates
- **High Risk**: Authentication, data handling, payment processing, API changes

### Fix Documentation

For every fix applied:
- Document why the specific resolution was chosen
- Add comments for complex merge decisions
- Create clear commit messages explaining changes
- Flag any high-risk modifications for review

## Example Usage

```bash
# Analyze and show what would be fixed
/fixpr 1234

# Analyze and automatically apply safe fixes
/fixpr 1234 --auto-apply
```

## Integration Points

This command works naturally with:
- `/copilot` - For comprehensive PR workflow orchestration
- `/commentreply` - To respond to review feedback
- `/pushl` - To push fixes to remote
- Testing commands - To verify fixes work correctly

## Error Recovery

When issues arise:
- Gracefully handle missing tools by trying alternatives
- Provide clear explanations of what failed and why
- Suggest manual steps when automation isn't possible
- Maintain partial progress rather than failing completely

## Natural Language Advantage

This approach leverages Claude's understanding to:
- Adapt to different repository structures
- Handle edge cases without explicit programming
- Provide context-aware solutions
- Explain decisions in human terms

The focus is on describing intent and letting Claude determine the best implementation, making the command more flexible and maintainable than rigid scripted approaches.

## Important Notes

**🚨 NEVER MERGE**: This command's job is to make PRs mergeable, not to merge them. The user retains control over when/if to actually merge.

**📊 Success Metric**: A successful run means GitHub would show a green merge button with no blockers - all CI passing, no conflicts, no blocking reviews.
