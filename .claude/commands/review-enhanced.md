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

**Execution Method**: This command delegates to `/execute` for intelligent workflow orchestration:
```
/execute /reviewe workflow implementation with auto-approval
```

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

**🚨 EXECUTION DELEGATION**: When `/reviewe` is invoked, it delegates to `/execute` for intelligent orchestration:
```markdown
/execute Perform enhanced code review with the following workflow:
1. Call /guidelines for centralized mistake prevention consultation
2. Run official /review command for baseline analysis
3. Execute multi-pass security analysis with code-review subagent (informed by guidelines)
4. Post comprehensive GitHub PR comments with findings
```

### Guidelines Integration Protocol

**Systematic Mistake Prevention**: This command automatically consults the mistake prevention guidelines system through `/guidelines` command composition.

**Execution Flow**:
1. Call `/guidelines` for comprehensive consultation
2. Apply guidelines output to inform review approach and security analysis
3. Proceed with enhanced review workflow using guidelines context

**Guidelines Integration**: The `/guidelines` command provides centralized consultation of CLAUDE.md, base guidelines, and PR-specific guidelines, enhancing the review process with documented patterns and anti-pattern prevention.

### Step 1: Official Review Integration
**Execute built-in `/review` command first** (via /execute orchestration):
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

### Additional Security & Testing Checks:

1. **Subprocess Safety Analysis** 🔴:
   - Flag any `shell=True` usage as CRITICAL security risk
   - Check for missing timeouts in subprocess calls
   - Verify list args instead of string commands
   - Detect command injection vulnerabilities
   - Enforce `check=True` for error handling
   - Pattern violations: `subprocess.run(f"git {cmd}", shell=True)` → Must use list args

2. **Test Pattern Validation** 🔴:
   - **CRITICAL**: Flag any `@unittest.skipIf`, `@pytest.skip()`, `pytest.skip()`
   - Verify mocks replace environment checks
   - Ensure deterministic test behavior (no `try/except ImportError` in tests)
   - Detect environment-dependent execution paths
   - Check for CI/local parity violations
   - Pattern: Tests must behave identically everywhere

3. **Resource Management** 🟡:
   - Check for cleanup in `finally` blocks (Python)
   - Verify temp file cleanup with `trap` (Bash)
   - Flag missing context managers for file operations
   - Detect resource leaks (unclosed files, connections)
   - Verify proper cleanup on error paths

4. **Git Operation Safety** 🟡:
   - Verify PR ref fetching (not raw SHAs)
   - Check for proper ref cleanup in finally blocks
   - Flag dangerous `HEAD` fallback patterns
   - Ensure worktree cleanup after operations
   - Detect unsafe git command construction

5. **Input Validation & Sanitization** 🔴:
   - Whitelist validation patterns (regex) instead of quoting
   - No blind string interpolation in commands
   - Command injection prevention checks
   - SQL injection vulnerability detection
   - XSS and data exposure risks

6. **CI-Specific Concerns** 🔵:
   - Environment variable checks (`CI` detection)
   - Non-interactive operation requirements
   - Token injection patterns (`GH_TOKEN`, `GITHUB_TOKEN`)
   - Timeout enforcement for all operations
   - Feature flag usage for risky operations

7. **Error Handling Specifics** 🟡:
   - Fail fast, fail loud principle enforcement
   - No silent fallbacks or swallowed exceptions
   - Specific exception catching (not bare `except`)
   - Proper error propagation and logging
   - Structured error messages with context

### Pattern Examples to Flag:

**❌ BAD Patterns to Flag:**
```python
# Shell injection risk
subprocess.run(f"git {cmd}", shell=True)  # 🔴 CRITICAL

# Missing timeout
subprocess.run(["git", "fetch"], check=True)  # 🟡 Important

# Test skip pattern
@unittest.skipIf(not redis_available, "Redis not available")  # 🔴 CRITICAL

# Environment-dependent test
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False  # 🔴 CRITICAL - Creates different test paths

# Missing cleanup
temp_file = tempfile.mktemp()
# ... use temp_file
# No cleanup!  # 🟡 Important

# Silent fallback
pr_head_sha = json.get("headRefOid", "HEAD")  # 🔴 CRITICAL
```

**✅ GOOD Patterns to Recommend:**
```python
# Safe subprocess
subprocess.run(["git", "fetch"], shell=False, timeout=30, check=True)

# Comprehensive mocking
@patch('redis.Redis')
def test_with_redis_mock(mock_redis):
    # Test runs identically everywhere

# Resource cleanup
try:
    temp_file = tempfile.mktemp()
    # ... use temp_file
finally:
    os.unlink(temp_file)  # Always cleanup

# Explicit error handling
if not head_oid:
    raise ValueError("Missing PR head SHA")
```

4. **Review Comment Generation**:
   - Create targeted inline comments for specific code locations
   - Generate comprehensive review summary with overall assessment
   - Use `[AI reviewer]` tag for all generated comments with expertise indicators
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

## Implementation Method

**This command uses `/execute` for intelligent workflow orchestration**. When invoked, it automatically:
1. Plans the review workflow based on target (PR, file, or feature)
2. Auto-approves execution (built-in approval for review commands)
3. Executes all review steps with progress tracking
4. Posts results to GitHub PR when applicable

The `/execute` delegation ensures optimal resource usage and parallel execution where possible.

**Subagent Review Comment Protocol**:
- `[AI reviewer] 🔴 **CRITICAL - Security Vulnerability**`: Exploitable security flaws, data corruption risks
- `[AI reviewer] 🔴 **CRITICAL - Runtime Error**`: Code that will crash or fail in production  
- `[AI reviewer] 🟡 **IMPORTANT - Performance**`: Significant inefficiencies affecting user experience
- `[AI reviewer] 🟡 **IMPORTANT - Maintainability**`: Code that's hard to maintain or extend
- `[AI reviewer] 🔵 **SUGGESTION - Optimization**`: Performance improvements, refactoring opportunities
- `[AI reviewer] 🔵 **SUGGESTION - Best Practice**`: Industry standards alignment, documentation
- `[AI reviewer] 🟢 **NITPICK - Style**`: Minor formatting, naming conventions, code consistency
- `[AI reviewer] ✅ **APPROVED**`: Code meets security and quality standards

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
