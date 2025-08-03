# Code Review Command

**Command Summary**: Systematic PR comment processing with virtual [AI reviewer] agent for comprehensive code quality analysis

**Purpose**: Perform comprehensive code analysis and post review comments using virtual AI reviewer agent

**Action**: Analyze PR changes, identify issues, and post proactive review comments with `[AI reviewer]` tag for systematic code quality assessment

**Usage**:
- `/review` - Perform code review analysis on current branch PR
- `/review [PR#]` - Analyze and review specific PR number
- (automatically enables virtual agent mode for comprehensive code analysis)

**Virtual Agent Integration**: Uses `[AI reviewer]` virtual agent that provides specialized code review expertise with proactive analysis and professional comment generation

**Virtual Agent Protocol**:
- **[AI reviewer]**: Specialized virtual agent for comprehensive code analysis
- **Code Analysis**: Identify bugs, security issues, performance problems, and best practice violations
- **Review Comments**: Generate insightful comments with `[AI reviewer]` tag
- **Impact Assessment**: Consider architectural implications and code quality impact
- **Best Practices**: Ensure adherence to coding standards and project conventions

**Auto-Detection Protocol**:
1. **Current Branch PR Detection**:
   - Use `git branch --show-current` to get current branch
   - Use `gh pr list --head $(git branch --show-current)` to find associated PR
   - If no PR found, report "No PR found for current branch [branch-name]"
   - If multiple PRs found, use the most recent (first in list)

**Code Analysis Implementation**:
1. **PR File Analysis** (CRITICAL FIRST STEP):
   - Use GitHub API to get all changed files (see canonical GitHub API documentation)
   - Retrieve diff content for each file to understand changes
   - Analyze code patterns, potential issues, and improvement opportunities
   - Focus on new code additions and significant modifications

2. **Virtual Agent Code Review**:
   - **[AI reviewer]** performs systematic analysis of each file
   - Identify: security vulnerabilities, performance issues, code smells, bugs
   - Check: coding standards compliance, best practices, architecture patterns
   - Evaluate: error handling, edge cases, maintainability, testability

3. **Issue Categorization**:
   - **🔴 Critical**: Security vulnerabilities, runtime errors, data corruption risks
   - **🟡 Important**: Performance issues, maintainability problems, architectural concerns
   - **🔵 Suggestion**: Style improvements, refactoring opportunities, optimizations
   - **🟢 Nitpick**: Minor style issues, documentation improvements, conventions

4. **Review Comment Generation**:
   - Create targeted inline comments for specific code locations
   - Generate comprehensive review summary with overall assessment
   - Use `[AI reviewer]` tag for all generated comments
   - Provide actionable feedback with suggested improvements

5. **Post Review Comments**:
   - Post inline comments using GitHub API (see canonical GitHub API documentation)
   - Post general review comment with overall findings summary
   - Include file-by-file breakdown with key issues identified

6. **Review Completion**:
   - Generate comprehensive review report
   - Provide overall code quality assessment
   - Suggest next steps for addressing identified issues

**Virtual Agent Review Comment Protocol**:
- `[AI reviewer] 🔴 **CRITICAL**`: Security vulnerabilities, runtime errors, data corruption risks
- `[AI reviewer] 🟡 **IMPORTANT**`: Performance issues, maintainability problems, architectural concerns
- `[AI reviewer] 🔵 **SUGGESTION**`: Style improvements, refactoring opportunities, optimizations
- `[AI reviewer] 🟢 **NITPICK**`: Minor style issues, documentation improvements, conventions
- `[AI reviewer] ✅ **APPROVED**`: Code meets quality standards with no significant issues identified

**Review Features**:
- Generate comprehensive review report in `tmp/review_analysis_PR#.md`
- Provide file-by-file analysis with issue breakdown
- Track code quality metrics and improvement suggestions
- Create actionable feedback with specific line references

**Branch Integration**:
- Automatically analyzes current working branch and its associated PR
- No need to remember or look up PR numbers for current work
- Seamlessly integrates with branch-based development workflow
- Falls back to manual PR specification when needed
- Focuses on changes introduced in the PR vs base branch
