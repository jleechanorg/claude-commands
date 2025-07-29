# Parallel Tasks vs Subagents Decision Framework

**Branch**: parallel-vs-subagents
**Created**: 2025-07-29
**Purpose**: Document when to use parallel tasks vs subagents to optimize token usage and performance

## Executive Summary

After analyzing token usage showing 17B tokens (16.8B cache reads) in a month, the primary cause is identified as excessive subagent spawning. Each subagent loads the full context (~50k+ tokens), creating massive multiplication effects. This guide provides a decision framework for choosing between parallel tasks and subagents.

## Token Cost Analysis

### Parallel Tasks (Same Session)
- **Additional tokens**: ~0 (reuses existing context)
- **Execution**: Background processes, GNU parallel, or batched tool calls
- **Best for**: Simple, independent operations

### Subagents (New Claude Instances)
- **Additional tokens**: ~50k+ per agent
  - **Breakdown**:
    - **CLAUDE.md size**: ~35k tokens (based on current documentation size)
    - **Project context size**: ~15k tokens (configuration files, code snippets, and metadata)
  - These values are approximate and may vary depending on specific project state
- **Example**: 10 subagents ≈ 500k+ tokens just for context loading
- **Cost multiplier**: 100x or more vs parallel tasks

## Decision Matrix

### Use PARALLEL TASKS When:

1. **Simple, Independent Operations**
   - File searches across directories
   - Data gathering and aggregation
   - Running multiple tests in parallel
   - Checking multiple git branches

2. **Same Working Directory/Context**
   - Operations in current branch
   - No conflicting file modifications
   - Shared environment variables

3. **Short Execution Time**
   - Each task < 30 seconds
   - Total completion < 2 minutes
   - No long-running processes

4. **Examples from Codebase**:
   ```bash
   # Search for import violations
   find . -name "*.py" -print0 | xargs -0 -P 8 grep "import logging"

   # Run multiple test files
   parallel pytest ::: test_file1.py test_file2.py test_file3.py

   # Check multiple PR statuses
   for pr in 123 456 789; do
     (gh pr view $pr --json state,mergeable > /tmp/pr_$pr.json) &
   done
   wait
   ```

### Use SUBAGENTS When:

1. **Complex Multi-Step Workflows**
   - Feature implementation
   - Architectural changes
   - Complex bug fixes requiring analysis
   - Tasks needing decision trees

2. **Different Working Directories**
   - Multiple branch operations
   - Isolated git worktrees
   - Conflicting file modifications

3. **Long-Running Operations**
   - Tasks > 5 minutes
   - Operations requiring monitoring
   - Multi-stage workflows

4. **Isolation Requirements**
   - Different permissions/contexts
   - Potential conflicts
   - Independent failure handling
   - PR creation and management

## Implementation Patterns

### Parallel Bash Patterns

```bash
# Pattern 1: Background processes
(task1) &
(task2) &
(task3) &
wait

# Pattern 2: GNU Parallel
parallel -j 4 ::: "cmd1" "cmd2" "cmd3" "cmd4"

# Pattern 3: xargs parallel
find . -name "*.py" | xargs -P 8 -I {} python process.py {}

# Pattern 4: Process with error handling
pids=()
(task1 && echo "Task 1 success" || echo "Task 1 failed") & pids+=($!)
(task2 && echo "Task 2 success" || echo "Task 2 failed") & pids+=($!)
for pid in ${pids[@]}; do
    wait $pid
done
```

### Monitoring Parallel Tasks

```bash
# Check running jobs
jobs -l

# Wait for specific PID
wait $PID

# Aggregate results
for f in /tmp/result_*.txt; do
    cat "$f"
done > combined_results.txt
```

## Real-World Decision Examples

| Task | Approach | Reasoning |
|------|----------|-----------|
| Search for pattern across 100 files | Parallel grep | Simple, independent, fast |
| Fix failing tests in 10 modules | Parallel if simple fix, Subagent if complex | Depends on interdependencies |
| Implement new /command | Subagent | Complex workflow, PR needed |
| Check status of 20 PRs | Parallel gh commands | Independent API calls |
| Update documentation across branches | Subagents | Different worktrees needed |
| Run full test suite | Parallel pytest | Independent test execution |
| Refactor with dependencies | Sequential or Subagent | Needs careful coordination |

## Cost Optimization Guidelines

1. **Default to Parallel Tasks**
   - Start with parallel approach
   - Only escalate to subagents if needed
   - Monitor with `ccusage` to validate

2. **Batch Similar Operations**
   - Group related tasks together
   - Use single context load
   - Aggregate results efficiently

3. **Document Decision Rationale**
   - Include in commit messages
   - Note why subagents were needed
   - Track token usage patterns

4. **Token Usage Monitoring**
   ```bash
   # Before optimization
   ccusage daily --instances

   # After implementing parallel tasks
   ccusage daily --instances --since [date]
   ```

## Expected Savings

- **Current**: 17B tokens/month (mostly cache reads from subagents)
- **Optimized**: 90%+ reduction possible
- **Cost Impact**: From $20k+ to ~$2.6k/month
  - **Derivation**: Assuming Claude API pricing of ~$0.0015 per 1,000 tokens, 17B tokens/month equates to $25,500/month. Optimizing to reduce token usage by 90% (to 1.7B tokens/month) would lower costs to approximately $2,550/month.
  - **Reference**: Token pricing based on current Claude API rates as of 2025.

## Implementation Checklist

- [ ] Audit current Task/subagent usage
- [ ] Identify operations suitable for parallelization
- [ ] Update CLAUDE.md with new guidelines
- [ ] Create parallel execution utilities
- [ ] Monitor token usage reduction
- [ ] Document patterns that work well

## Implementation Next Steps

1. Review existing orchestration patterns
2. Create parallel execution helper scripts
3. Update documentation with examples
4. Train on new patterns via Memory MCP
5. Monitor and refine based on results

---

**References**:
- ccusage documentation
- GNU Parallel manual
- Bash job control
- CLAUDE.md orchestration guidelines

---

## Project Goal

Optimize token usage by providing a clear decision framework for choosing between parallel tasks and subagents, addressing the 17B tokens/month usage identified in cost analysis.

## Implementation Plan

1. ✅ Create comprehensive decision matrix documentation
2. ✅ Update command documentation to use new framework
3. ✅ Add token cost analysis and breakdown
4. ✅ Provide implementation patterns and examples
5. ✅ Respond to PR review comments
6. ⏳ Update monitoring guidelines based on feedback

## Current State

- **Documentation Complete**: Parallel vs subagents reference guide created
- **Command Updates**: Updated /execute, /plan, /orchestrate to use new framework
- **Cost Analysis**: Added detailed token breakdown and cost projections
- **Review Status**: Addressed all 5 inline comments from Copilot and CodeRabbit with detailed responses and fixes

## Follow-up Actions

1. Complete PR comment responses with technical fixes
2. Push changes and verify CI passes
3. Monitor token usage after implementation
4. Create follow-up improvements based on real-world usage

## Key Context

- **Problem**: 17B tokens/month with 16.8B from cache reads due to excessive subagent spawning
- **Solution**: Decision framework defaulting to parallel tasks for simple operations
- **Expected Impact**: 90%+ token reduction (from ~$25k to ~$2.5k/month)
- **Integration**: Updates CLAUDE.md, command docs, and provides reference guide

## Branch Info

Branch: parallel-vs-subagents
Status: 🔄 IN PROGRESS - Addressing PR review comments
PR: #1074 https://github.com/jleechanorg/worldarchitect.ai/pull/1074
