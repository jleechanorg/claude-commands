# Enhanced Code Review Command

**Usage**: `/review-enhanced` or `/reviewe` (alias)

**Command Summary**: Comprehensive code review combining official Claude Code `/review` with advanced multi-pass security analysis

**Purpose**: Perform comprehensive code analysis and post review comments using virtual AI reviewer agent

**Action**: Analyze PR changes, identify issues, and post proactive review comments with `[AI reviewer]` tag for systematic code quality assessment

**Usage**:
- `/review-enhanced` - Enhanced review combining official + advanced analysis
- `/reviewe` - Short alias for `/review-enhanced`
- `/review-enhanced [PR#]` - Analyze specific PR with comprehensive review
- `/reviewe [PR#]` - Short alias with PR specification

**Command Composition**:
`/review-enhanced` = Official `/review` + Advanced Security Analysis + GitHub Integration

**Execution Flow**:
1. **Official Review**: Run built-in Claude Code `/review` command for baseline analysis
2. **Enhanced Analysis**: Multi-pass security and quality analysis with code-review subagent
3. **GitHub Integration**: Automated PR comment posting with categorized findings

**Subagent Integration**: Uses specialized `code-review` subagent that provides expert multi-language code analysis with security focus and actionable feedback

**Subagent Protocol**:
- **code-review**: Specialized subagent for comprehensive security and quality analysis
- **Multi-Pass Analysis**: Security → Bugs → Performance → Quality in systematic phases
- **Context7 Integration**: Uses Context7 MCP for up-to-date API documentation and best practices
- **Expert Categories**: 🔴 Critical, 🟡 Important, 🔵 Suggestions, 🟢 Nitpicks with detailed reasoning
- **Actionable Feedback**: Specific line references, code examples, and improvement recommendations

**Auto-Detection Protocol**:
1. **Current Branch PR Detection**:
   - Use `git branch --show-current` to get current branch
   - Use `gh pr list --head $(git branch --show-current)` to find associated PR
   - If no PR found, report "No PR found for current branch [branch-name]"
   - If multiple PRs found, use the most recent (first in list)

**Enhanced Analysis Implementation**:

### Step 1: Official Review Integration
**Execute built-in `/review` command first**:
```
# Execute official Claude Code /review command
# This provides baseline analysis before our enhanced review
/review [PR_TARGET]
```
- Leverages Claude Code CLI's native review capabilities
- Provides baseline conversational code review
- Establishes context for enhanced analysis
- Uses Claude's built-in PR understanding
- Creates foundation for our advanced security analysis

### Step 2: Advanced Analysis (Our Enhancement)
1. **PR File Analysis** (CRITICAL FIRST STEP):
   - Use GitHub API to get all changed files (see canonical GitHub API documentation)
   - Retrieve diff content for each file to understand changes
   - Analyze code patterns, potential issues, and improvement opportunities
   - Focus on new code additions and significant modifications

2. **Subagent Code Review**:
   - **code-review** subagent performs multi-pass analysis of each file
   - **Pass 1**: Security vulnerabilities, SQL injection, XSS, authentication flaws
   - **Pass 2**: Runtime errors, null pointers, race conditions, resource leaks
   - **Pass 3**: Performance issues, N+1 queries, inefficient algorithms, memory leaks
   - **Pass 4**: Code quality, maintainability, documentation, best practices

3. **Issue Categorization**:
   - **🔴 Critical**: Security vulnerabilities, runtime errors, data corruption risks
   - **🟡 Important**: Performance issues, maintainability problems, architectural concerns
   - **🔵 Suggestion**: Style improvements, refactoring opportunities, optimizations
   - **🟢 Nitpick**: Minor style issues, documentation improvements, conventions

4. **Review Comment Generation**:
   - Create targeted inline comments for specific code locations
   - Generate comprehensive review summary with overall assessment
   - Use `[Code Reviewer]` tag for all generated comments with expertise indicators
   - Provide actionable feedback with suggested improvements

5. **Post Review Comments**:
   **🚨 MANDATORY: You MUST post review comments as described below.**
   - **ALWAYS POST** inline comments using GitHub API (see canonical GitHub API documentation)
   - **ALWAYS POST** general review comment with comprehensive findings summary
   - **ALWAYS POST** file-by-file breakdown with key issues identified
   - **NEVER SKIP** comment posting - this is the primary purpose of the command

6. **Review Completion**:
   - Generate comprehensive review report
   - Provide overall code quality assessment
   - Suggest next steps for addressing identified issues

**Subagent Review Comment Protocol**:
- `[Code Reviewer] 🔴 **CRITICAL - Security Vulnerability**`: Exploitable security flaws, data corruption risks
- `[Code Reviewer] 🔴 **CRITICAL - Runtime Error**`: Code that will crash or fail in production  
- `[Code Reviewer] 🟡 **IMPORTANT - Performance**`: Significant inefficiencies affecting user experience
- `[Code Reviewer] 🟡 **IMPORTANT - Maintainability**`: Code that's hard to maintain or extend
- `[Code Reviewer] 🔵 **SUGGESTION - Optimization**`: Performance improvements, refactoring opportunities
- `[Code Reviewer] 🔵 **SUGGESTION - Best Practice**`: Industry standards alignment, documentation
- `[Code Reviewer] 🟢 **NITPICK - Style**`: Minor formatting, naming conventions, code consistency
- `[Code Reviewer] ✅ **APPROVED**`: Code meets security and quality standards

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
