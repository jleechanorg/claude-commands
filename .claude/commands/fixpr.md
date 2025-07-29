# /fixpr Command - Intelligent PR Fix Analysis

**Usage**: `/fixpr <PR_NUMBER> [--auto-apply]`

**Purpose**: Make GitHub PRs mergeable by analyzing and fixing CI failures, merge conflicts, and bot feedback - without merging.

## 🚨 FUNDAMENTAL PRINCIPLE: GITHUB IS THE AUTHORITATIVE SOURCE

**CRITICAL RULE**: GitHub PR status is the ONLY source of truth. Local conditions (tests, conflicts, etc.) may differ from GitHub's reality.

**MANDATORY APPROACH**:
- ✅ **ALWAYS start by fetching fresh GitHub PR status**
- ✅ **ALWAYS display GitHub status inline for transparency**
- ✅ **ALWAYS verify fixes against GitHub, not local assumptions**
- ❌ **NEVER assume local tests/conflicts match what GitHub sees**
- ❌ **NEVER fix local issues without confirming they block the GitHub PR**

**WHY THIS MATTERS**: GitHub uses different CI environments, merge algorithms, and caching than local development. A PR may be mergeable locally but blocked on GitHub, or vice versa.

## Description

The `/fixpr` command leverages Claude's natural language understanding to analyze PR blockers and fix them. The goal is to get the PR into a mergeable state (all checks passing, no conflicts) but **never actually merge it**. It orchestrates GitHub tools and git commands through intent-based descriptions rather than explicit syntax.

## 🚀 Enhanced Execution

**Enhanced Universal Composition**: `/fixpr` now uses `/e` (execute) for intelligent optimization while preserving its core universal composition architecture.

### Execution Strategy

**Default Mode**: Uses `/e` to determine optimal approach
- **Trigger**: Simple PRs with ≤10 issues or straightforward CI failures
- **Behavior**: Standard universal composition approach with direct Claude analysis
- **Benefits**: Fast execution, minimal overhead, reliable for common cases

**Parallel Mode** (Enhanced):
- **Trigger**: Complex PRs with >10 distinct issues, multiple conflict types, or extensive CI failures
- **Behavior**: Spawn specialized analysis agents while Claude orchestrates integration
- **Benefits**: Faster processing of complex scenarios, parallel issue resolution

### Agent Types for PR Analysis

1. **CI-Analysis-Agent**: Specializes in GitHub CI failure analysis and fix recommendations
2. **Conflict-Resolution-Agent**: Focuses on merge conflict analysis and safe resolution strategies
3. **Bot-Feedback-Agent**: Processes automated bot comments and implements applicable suggestions
4. **Verification-Agent**: Validates fix effectiveness and re-checks mergeability status

**Coordination Protocol**: Claude maintains overall workflow control, orchestrating agent results through natural language understanding integration.

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

### Step 2: Fetch Critical GitHub PR Data - **GITHUB IS THE AUTHORITATIVE SOURCE**

🚨 **CRITICAL PRINCIPLE**: GitHub PR status is the ONLY authoritative source of truth. NEVER assume local conditions match GitHub reality.

**MANDATORY GITHUB FIRST APPROACH**:
- ✅ **ALWAYS fetch fresh GitHub status** before any analysis or fixes
- ✅ **NEVER assume local tests/conflicts match GitHub**
- ✅ **ALWAYS print GitHub status inline** for full transparency
- ❌ **NEVER fix local issues without confirming they exist on GitHub**
- ❌ **NEVER trust cached or stale GitHub data**

**EXPLICIT GITHUB STATUS FETCHING** - Fetch these specific items from GitHub to understand what's blocking mergeability:

1. **CI State & Test Failures** (GitHub Authoritative):
   - **MANDATORY**: `gh pr view <PR> --json statusCheckRollup` - Get ALL CI check results
   - **DISPLAY INLINE**: Print exact GitHub CI status: `❌ FAILING: test-unit (exit code 1)`
   - **FETCH LOGS**: For failing checks, get specific error messages from GitHub
   - **VERIFY AUTHORITY**: Cross-check GitHub vs local - local is NEVER authoritative
   - **EXAMPLE OUTPUT**:
     ```
     🔍 GITHUB CI STATUS (Authoritative):
     ❌ test-unit: FAILING (required) - TypeError: Cannot read property 'id' of undefined
     ✅ test-lint: PASSING (required)
     ⏳ test-integration: PENDING (required)
     ```

2. **Merge Conflicts** (GitHub Authoritative):
   - **MANDATORY**: `gh pr view <PR> --json mergeable,mergeableState` - Get GitHub merge status
   - **DISPLAY INLINE**: Print exact GitHub merge state: `❌ CONFLICTING: 3 files have conflicts`
   - **FETCH DETAILS**: `gh pr diff <PR>` - Get actual conflict content from GitHub
   - **NEVER ASSUME LOCAL**: Local git status may not match GitHub's merge analysis
   - **EXAMPLE OUTPUT**:
     ```
     🔍 GITHUB MERGE STATUS (Authoritative):
     ❌ mergeable: false
     ❌ mergeableState: CONFLICTING
     📄 Conflicting files: src/main.py, tests/test_main.py, README.md
     ```

3. **Bot Feedback & Review Comments** (GitHub Authoritative):
   - **MANDATORY**: `gh pr view <PR> --json reviews,comments` - Get ALL review data from GitHub
   - **DISPLAY INLINE**: Print blocking reviews: `❌ CHANGES_REQUESTED by @reviewer`
   - **FETCH COMMENTS**: Get all bot and human feedback directly from GitHub API
   - **EXAMPLE OUTPUT**:
     ```
     🔍 GITHUB REVIEW STATUS (Authoritative):
     ❌ @coderabbit: CHANGES_REQUESTED - Fix security vulnerability in auth.py
     ✅ @teammate: APPROVED
     ⏳ @senior-dev: REVIEW_REQUESTED
     ```

4. **PR Metadata & Protection Rules** (GitHub Authoritative):
   - **MANDATORY**: `gh pr view <PR> --json state,mergeable,requiredStatusChecks` - Get current GitHub PR state
   - **DISPLAY INLINE**: Print exact GitHub merge button status and blocking factors
   - **FETCH PROTECTION**: Get branch protection rules that may prevent merging
   - **EXAMPLE OUTPUT**:
     ```
     🔍 GITHUB PR METADATA (Authoritative):
     📄 State: OPEN | Mergeable: false
     🛡️ Required checks: [test-unit, test-lint, security-scan]
     🚫 Blocking factors: 1 failing check, 1 requested change
     ```

🎯 **THE GOAL**: Gather everything that GitHub shows as preventing the green "Merge" button from being available - NEVER assume, ALWAYS verify with fresh GitHub data.

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

### Step 5: Verify Mergeability Status - **MANDATORY GITHUB RE-VERIFICATION**

🚨 **CRITICAL**: After applying fixes, ALWAYS re-fetch fresh GitHub status. NEVER assume fixes worked without GitHub confirmation.

**MANDATORY GITHUB RE-VERIFICATION PROTOCOL**:

1. **Re-fetch Fresh GitHub Status** (Wait for CI to complete):
   - **WAIT**: Allow 30-60 seconds for GitHub CI to register changes after push
   - **RE-FETCH**: `gh pr view <PR> --json statusCheckRollup,mergeable,mergeableState`
   - **DISPLAY**: Print updated GitHub status inline with before/after comparison
   - **EXAMPLE**:
     ```text
     🔄 GITHUB STATUS VERIFICATION (After Fixes):

     BEFORE:
     ❌ test-unit: FAILING - TypeError in auth.py
     ❌ mergeable: false

     AFTER (Fresh from GitHub):
     ✅ test-unit: PASSING - All tests pass
     ✅ mergeable: true

     📊 RESULT: PR is now mergeable on GitHub
     ```
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
