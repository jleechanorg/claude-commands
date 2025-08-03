# Subagent Strategy Guide for WorldArchitect.AI

**Evidence-based recommendations for optimal Task tool delegation in mvp_site**

## Executive Summary

Based on comprehensive research and project-specific evidence (PR #1062), the optimal strategy is **"Pragmatic Direct Execution with Exception-Based Delegation"**:
- **Default**: Direct execution (80% of tasks)
- **Exception**: Strategic delegation when ALL criteria are met (20% of tasks)

## Performance Evidence

### Real-World Measurements
- **PR #1062**: Direct execution completed in 2 minutes vs 5+ minute timeout for delegation
- **Performance penalty**: 2.5x slower for inappropriate delegation
- **Token cost**: Each subagent consumes 50k+ tokens with independent context

### When Delegation Excels
- **Multi-agent research**: 90.2% performance improvement for breadth-first queries
- **Parallel operations**: Near-linear speedup for truly independent tasks
- **Specialized domains**: Better results when agents focus on specific expertise

## Delegation Decision Framework

### The 5-Test Criteria (ALL must pass)

```python
def should_delegate(task):
    """
    Returns True only if ALL delegation criteria are met.
    Based on CLAUDE.md Delegation Decision Matrix.
    """
    # Test 1: Parallelism
    if not task.can_run_in_parallel():
        return False  # Sequential tasks perform better directly

    # Test 2: Resource Availability
    if system.memory_usage_percent > 50 or active_claude_instances >= 3:
        return False  # Avoid resource exhaustion

    # Test 3: Overhead vs Benefit
    # Example: Define task.estimated_duration and agent_startup_time
    task.estimated_duration = task.get_estimated_duration()  # Replace with actual method to estimate duration
    agent_startup_time = 5  # Example: Assume agent startup time is 5 seconds
    
    # Example: estimated_duration_seconds and agent_startup_seconds
    if task.estimated_duration_seconds < agent_startup_seconds:
        return False  # Overhead exceeds benefit

    # Test 4: Specialization Need
    if not task.requires_different_expertise():
        return False  # Current instance can handle it

    # Test 5: Independence
    if task.requires_frequent_coordination():
        return False  # Coordination overhead kills performance

    return True  # Delegate only when ALL tests pass
```

## Practical Implementation Guide

### Direct Execution Patterns (Default Mode)

Use direct execution for:

#### 1. Code Comprehension
```bash
# Good - Direct execution
Read mvp_site/routes/game.py
Grep "def create_campaign" --type py
Glob "**/test_*.py"

# Bad - Unnecessary delegation
Task: "Read the game routes file"
```

#### 2. Small-Scale Changes
```python
# Good - Direct execution
MultiEdit mvp_site/services/campaign_service.py:
  - Fix import order
  - Add type hints to create_campaign
  - Update docstring

# Bad - Over-delegation
Task: "Fix imports in campaign_service.py"
```

#### 3. Script Execution
```bash
# Good - Direct execution
Bash: ./run_tests.sh
Bash: ./integrate.sh
Bash: TESTING=true vpython mvp_site/test_game.py

# Bad - Wrapping scripts in tasks
Task: "Run the test suite"
```

#### 4. Sequential Workflows
```python
# Good - Direct execution
1. Read the error log
2. Identify the failing function
3. Fix the bug
4. Run tests to verify

# Bad - Artificial parallelization
Task: "Debug and fix the authentication error"
```

### Strategic Delegation Patterns (Exceptions)

Reserve delegation for high-value parallel work:

#### 1. Multi-Layer Feature Implementation
```python
# Good - Natural parallelism across layers
Task: """
Implement complete product catalog feature:
- Frontend: Create product listing and detail pages
- Backend: Build CRUD API endpoints
- Database: Design product model with categories
- Tests: Full coverage for all components
- Documentation: Update API docs

Success criteria:
- All endpoints return correct status codes
- Frontend displays products correctly
- Tests pass with 100% coverage
- Follows existing patterns in codebase
"""
```

#### 2. Parallel Analysis Tasks
```python
# Good - Independent analysis domains
Task: """
Perform security and performance audit:

Security Agent:
- Scan for SQL injection vulnerabilities
- Check for XSS in templates
- Verify authentication on all endpoints
- Review permission checks

Performance Agent:
- Profile database queries
- Identify N+1 problems
- Check for missing indexes
- Analyze response times

Deliver findings in roadmap/audit_results.md
"""
```

#### 3. Browser Test Suites
```python
# Good - Natural test parallelism
Task: """
Run comprehensive browser tests:
- Execute all Playwright tests in testing_ui/
- Capture screenshots for failures
- Generate coverage report
- Create summary of any flaky tests

Use test_mode=true and mock data
"""
```

#### 4. Cross-Cutting Refactoring
```python
# Good - Coordinated multi-file changes
Task: """
Migrate authentication from sessions to JWT:
- Update login/logout endpoints
- Create JWT service and middleware
- Modify all protected routes
- Update frontend auth handling
- Migrate existing sessions
- Full test coverage

Maintain backward compatibility during transition
"""
```

## Project-Specific Patterns

### Use mvp_site Structure as Natural Boundaries

```
mvp_site/
├── routes/      # Delegate route-focused tasks
├── services/    # Delegate service layer tasks
├── models/      # Delegate data model tasks
├── static/      # Delegate frontend tasks
├── templates/   # Delegate template tasks
└── tests/       # Delegate test suite tasks
```

### Leverage Existing Scripts

Your scripts are perfect delegation boundaries:

```bash
# These scripts encapsulate complex workflows
./run_tests.sh          # Full test suite
./run_ui_tests.sh mock  # Browser tests
./integrate.sh          # Branch integration
./deploy.sh            # Deployment pipeline
./run_ci_replica.sh    # Complete CI simulation
```

## Anti-Patterns to Avoid

### ❌ Over-Delegation
```python
# Bad - Simple task that takes < 2 minutes
Task: "Add a print statement to debug the login function"

# Bad - Sequential workflow
Task: "Read file, then based on content, modify another file"

# Bad - Requires constant coordination
Task: "Incrementally refactor with my feedback at each step"
```

### ❌ Artificial Task Splitting
```python
# Bad - Creating fake parallelism
Task 1: "Read all Python files"
Task 2: "Read all JavaScript files"
Task 3: "Read all templates"
# (When you actually need them all for one analysis)
```

### ❌ Delegation Without Clear Success Criteria
```python
# Bad - Vague outcomes
Task: "Improve the codebase"

# Good - Specific, measurable criteria
Task: """
Improve API response times:
- Profile all endpoints
- Optimize queries reducing time by 50%
- Add caching where appropriate
- Verify with before/after benchmarks
"""
```

## Solo Developer Best Practices

### 1. Start with Direct Execution
- Assume direct execution unless proven otherwise
- Measure actual task duration before delegating
- Track which patterns work best for your workflow

### 2. Document Successful Patterns
```markdown
# In .claude/learnings.md
- Multi-file feature implementation: delegation saves 60% time
- Single-file debugging: direct execution 2.5x faster
- Browser test suites: parallel execution worth token cost
```

### 3. Monitor Resource Usage
```bash
# Before delegation, check:
- Current memory usage: ps aux | grep claude-code | awk '{print $4}' # % of memory
- Active Claude instances: ps aux | grep -c "claude-code.*Task"
- Token consumption rate: Check Claude Code usage dashboard or logs
- Time of day (API limits): Consider peak/off-peak hours for your plan
```

### 4. Iterate Based on Results
- Track delegation success rates
- Note patterns that consistently fail
- Adjust criteria based on evidence
- Update this guide with findings

## Quick Decision Matrix

| Task Type | Duration | Parallelizable | Dependencies | Coordination | Decision |
|-----------|----------|----------------|--------------|--------------|----------|
| Bug fix | < 2 min | No | Sequential | High | **Direct** |
| Feature | > 10 min | Yes | Independent | Low | **Delegate** |
| Refactor | > 5 min | Maybe | Some | Medium | **Evaluate** |
| Analysis | > 5 min | Yes | None | None | **Delegate** |
| Script | Varies | No | Sequential | None | **Direct** |

## Conclusion

For WorldArchitect.AI, optimize for:
1. **Simplicity**: Direct execution as default
2. **Performance**: 2.5x faster for most tasks
3. **Strategic Delegation**: High-value parallel work only
4. **Evidence**: Track and adjust based on results

Remember: You're a solo developer. Claude is your smart intern, not a team to manage. Use delegation to multiply your effectiveness, not to create complexity.

## References

- PR #1062: Direct execution performance comparison
- CLAUDE.md: Delegation Decision Matrix
- Multi-agent research: 90.2% improvement for breadth-first queries
- Token costs: 50k+ per subagent with independent context
