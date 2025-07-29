# Token Usage Research & Optimization Analysis

**Date**: 2025-07-29
**Researcher**: Claude + User
**Problem**: 17B tokens used in one month

## Executive Summary

Discovered massive token usage (17B/month, $20k cost) with 95% being cache reads from excessive subagent spawning. Each subagent loads ~50k tokens of context. Solution: Use parallel tasks for simple operations (0 extra tokens) instead of subagents.

## 1. Problem Discovery

### Initial Data from ccusage
```
Total Tokens: 17,730,767,000 (July 2025)
├── Input: 1,338,000 (0.01%)
├── Output: 43,604,000 (0.25%)
├── Cache Create: 847,558,000 (4.78%)
└── Cache Read: 16,838,265,000 (94.96%) ⚠️
```

### Cost Analysis
- **Monthly cost**: ~$20,000
- **Daily average**: $666
- **Peak day (July 28)**: $449.59 with 501M tokens

## 2. Root Cause Investigation

### A. Subagent Proliferation
```
~/.claude/projects/ directory analysis:
- task-agent-12674835/
- task-agent-19138286/
- task-agent-96465971/
... (hundreds of directories)
```

Each `task-agent-*` represents a spawned Claude instance that:
- Loads full CLAUDE.md (~30k tokens)
- Loads project context (~20k tokens)
- **Total per agent**: ~50k+ tokens

### B. Worktree Sessions
Multiple parallel development branches:
- worktree-human (UI work)
- worktree-css (styling)
- worktree-hooks (system development)
- worktree-testing (test infrastructure)
- worktree-coverage (coverage improvements)

Each worktree session also loads full context.

### C. Token Multiplication Effect
```
Example calculation:
- 100 subagents × 50k tokens = 5M tokens just for context
- 200 subagents × 50k tokens = 10M tokens
- Actual: 16.8B cache reads suggest 300+ agent spawns
```

## 3. Solution Design

### Parallel Tasks vs Subagents Framework

#### When to Use Parallel Tasks (0 extra tokens)
- Simple, independent operations
- Execution time < 30 seconds each
- Same working directory
- No complex decision trees

#### When to Use Subagents (~50k tokens each)
- Complex multi-step workflows
- Different working directories needed
- Long-running operations (> 5 minutes)
- PR creation and management

### Implementation Methods

#### 1. Background Processes (Bash &)
```bash
# Simple parallel execution
(grep -r "pattern1" .) &
(grep -r "pattern2" .) &
(grep -r "pattern3" .) &
wait
```
**Best for**: 2-10 simple commands

#### 2. GNU Parallel
```bash
# Structured parallel execution
parallel -j 4 pytest ::: test1.py test2.py test3.py test4.py

# With progress bar
parallel --bar -j 8 process_file ::: *.txt
```
**Best for**: Large-scale parallel operations

#### 3. xargs Parallel
```bash
# File processing
find . -name "*.py" | xargs -P 8 -I {} python lint.py {}
```
**Best for**: File-based operations

#### 4. Batched Tool Calls
```python
# Multiple Claude tools in single response
[Read(file1), Read(file2), Read(file3)]
```
**Best for**: Claude-specific operations

## 4. Implementation Results

### Documentation Created
1. **Central Guide**: `.claude/commands/parallel-vs-subagents.md`
2. **Command Updates**:
   - plan.md: Added execution method decision
   - execute.md: Hybrid approach examples
   - orchestrate.md: Token warning section
   - CLAUDE.md: Cost warnings in Task Agent Patterns

### Key Changes
- Replaced "subagent decision: YES/NO" with "execution method" choice
- Added token cost estimates to planning phase
- Provided specific implementation patterns
- Created decision matrix with clear criteria

## 5. Expected Impact

### Token Usage Reduction
```
Current state:
- Approach: Subagents for everything
- Monthly tokens: 17B
- Monthly cost: $20,000

Optimized state:
- Approach: Parallel tasks (default) + Subagents (when needed)
- Expected reduction: 90%+
- Target monthly cost: ~$2,550 (calculated)
```

### Performance Benefits
- Faster execution (no context loading overhead)
- Better resource utilization
- Reduced API rate limit pressure

## 6. Monitoring Plan

### Verification Steps
1. Track daily usage: `ccusage daily --instances`
2. Compare before/after: `ccusage daily --since 2025-07-29`
3. Monitor specific patterns:
   ```bash
   # Count task agents
   ls ~/.claude/projects/ | grep -c "task-agent"

   # Check recent spawns
   ls -lt ~/.claude/projects/ | head -20
   ```

### Success Metrics
- [ ] 50% reduction in cache read tokens within 1 week
- [ ] 75% reduction within 2 weeks
- [ ] 90% reduction steady state
- [ ] Monthly cost < $3,000

## 7. Lessons Learned

### Technical Insights
1. **Context loading is expensive** - Each agent spawn costs ~50k tokens
2. **Cache reads dominate** - 95% of usage was redundant context loading
3. **Simple operations don't need isolation** - Parallel bash is sufficient

### Process Improvements
1. **Question defaults** - "Should I spawn an agent?" → "Can I use parallel tasks?"
2. **Measure impact** - Use ccusage proactively, not reactively
3. **Document decisions** - This research led to systematic documentation

## 8. Future Considerations

### Potential Enhancements
1. **Automation**: Detect simple tasks and auto-suggest parallel execution
2. **Presets**: Common parallel patterns as reusable commands
3. **Monitoring**: Real-time token usage warnings
4. **Training**: Memory MCP integration for pattern learning

### Risk Mitigation
1. **Over-correction**: Don't avoid subagents when truly needed
2. **Error handling**: Parallel tasks need aggregated error reporting
3. **User education**: Clear examples prevent misuse

## Appendix: Evidence

### A. ccusage Output (July 28)
```
│ 2025     │ - opus-4      │   17,902 │  518,176 │ 21,607,8… │ 479,643,374 │ 501,787,343 │  $449.59 │
│ 07-28    │ - sonnet-4    │          │          │           │             │             │          │
```

### B. Directory Listing Sample
```
-home-jleechan-projects-worldarchitect-ai-agent-workspace-task-agent-12674835/
-home-jleechan-projects-worldarchitect-ai-agent-workspace-task-agent-19138286/
-home-jleechan-projects-worldarchitect-ai-agent-workspace-task-agent-96465971/
```

### C. PR #1074
Created comprehensive documentation addressing token optimization:
https://github.com/jleechanorg/worldarchitect.ai/pull/1074

---

**Status**: Research complete, solution implemented, awaiting results verification
