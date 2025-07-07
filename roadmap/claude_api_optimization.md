# Claude API Optimization Guide

## Overview
This document outlines strategies for using multiple Claude Code processes effectively while avoiding API timeouts and rate limiting issues.

## Problem Analysis
- Multiple concurrent Claude processes cause API timeouts
- Rate limiting triggers retry loops (1s, 1s, 2s, 5s)
- Resource contention between sessions
- Session state conflicts

## Claude API Limits & Constraints

### Rate Limiting
- **~12 concurrent requests** maximum across all processes
- **Pro Plan**: ~10-40 prompts every 5 hours per session
- **Max Plan**: ~200-800 prompts every 5 hours (20x more)
- **Session Windows**: Reset every 5 hours from first message
- **Usage Sharing**: Claude Desktop + Claude Code share the same quotas

### Session Management
- 50 sessions per month guideline (flexible)
- Context window fills with conversation history
- Memory usage: 200-500MB per Claude process

## Strategic Multi-Process Architecture

### 1. Git Worktree Strategy (Recommended)
```bash
# Create isolated worktrees for different contexts
git worktree add ../worktree_feature1 feature-branch
git worktree add ../worktree_bugfix main
git worktree add ../worktree_docs documentation

# Run Claude in each worktree for parallel development
cd ../worktree_feature1 && claude  # Context: New feature
cd ../worktree_bugfix && claude    # Context: Bug fixes  
cd ../worktree_docs && claude      # Context: Documentation
```

### 2. Context-Based Process Allocation
```bash
# Process 1: Interactive Development (Primary)
claude --session-name "dev-primary"

# Process 2: Research/Analysis (Secondary)
claude --session-name "research" 

# Process 3: Testing/Automation (Headless)
claude -p "Run tests and analyze results" --output-format stream-json

# Process 4: Documentation (Batch)
claude --session-name "docs"
```

### 3. Session Window Management
```bash
# Stagger sessions to avoid quota conflicts
# Session 1: 9:00 AM - 2:00 PM (5 hours)
# Session 2: 11:00 AM - 4:00 PM (5 hours) 
# Session 3: 1:00 PM - 6:00 PM (5 hours)
# Session 4: 3:00 PM - 8:00 PM (5 hours)
```

## Practical Implementation Guide

### Priority-Based Process Management
```bash
# High Priority (Active Development)
export CLAUDE_PRIORITY=1  # Get 50% of quota allocation
claude --max-requests-per-hour 20

# Medium Priority (Research/Analysis)  
export CLAUDE_PRIORITY=2  # Get 30% of quota allocation
claude --max-requests-per-hour 12

# Low Priority (Documentation/Batch)
export CLAUDE_PRIORITY=3  # Get 20% of quota allocation
claude --max-requests-per-hour 8
```

### Context Optimization Per Process
```bash
# Process 1: Development (Full Context)
claude --context-size large

# Process 2: Research (Minimal Context)
claude --context-size small
# Use /clear frequently

# Process 3: Testing (No Context Retention)
claude --headless --no-context-retention

# Process 4: Documentation (Project-Specific Context)
claude --context-filter "*.md,*.txt,README*"
```

## Advanced Coordination Strategies

### 1. Queue-Based Request Management
```bash
# Create request coordination script
cat > claude_coordinator.sh << 'EOF'
#!/bin/bash
ACTIVE_REQUESTS=0
MAX_CONCURRENT=8  # Under the 12 limit

function request_slot() {
    while [ $ACTIVE_REQUESTS -ge $MAX_CONCURRENT ]; do
        sleep 1
    done
    ACTIVE_REQUESTS=$((ACTIVE_REQUESTS + 1))
}

function release_slot() {
    ACTIVE_REQUESTS=$((ACTIVE_REQUESTS - 1))
}
EOF
```

### 2. Session State Synchronization
```bash
# Share session state between processes
export CLAUDE_SESSION_DIR="/tmp/claude_sessions"
mkdir -p $CLAUDE_SESSION_DIR

# Process 1: Primary (Read/Write)
claude --session-file "$CLAUDE_SESSION_DIR/primary.json"

# Process 2: Secondary (Read-Only)
claude --session-file "$CLAUDE_SESSION_DIR/primary.json" --read-only

# Process 3: Isolated (Separate state)
claude --session-file "$CLAUDE_SESSION_DIR/research.json"
```

### 3. Workload Distribution
```bash
# Heavy Operations (Single Process)
claude --session-name "heavy" --max-context 100000
# Use for: Large file analysis, complex refactoring

# Light Operations (Multiple Processes)
claude --session-name "light1" --max-context 10000
claude --session-name "light2" --max-context 10000
# Use for: Quick fixes, documentation, small edits

# Batch Operations (Headless)
claude --headless --batch-size 5 --delay 2
# Use for: Testing, linting, automated tasks
```

## Monitoring and Optimization

### 1. Resource Monitoring
```bash
# Monitor Claude processes
watch -n 5 'ps aux | grep claude | grep -v grep'

# Monitor API usage
curl -s "https://api.anthropic.com/v1/usage" -H "Authorization: Bearer $CLAUDE_API_KEY"

# Monitor memory usage
free -h && echo "Claude Memory:" && ps aux | grep claude | awk '{sum+=$4} END {print sum "%"}'
```

### 2. Performance Optimization
```bash
# Optimize context per process
# Process 1: Full project context
claude --context-includes "src/,docs/,tests/" --context-excludes "node_modules/,venv/"

# Process 2: Focused context
claude --context-includes "src/auth/" --max-files 20

# Process 3: No file context
claude --no-file-context --prompt-only

# Process 4: Cached context
claude --context-cache-ttl 3600 --context-cache-size 50MB
```

## Troubleshooting Common Issues

### Timeout Patterns
- **1s, 1s, 2s, 5s retries**: Rate limiting or concurrent request overflow
- **Connection timeout**: Network or API endpoint issues
- **Session timeout**: Context window overflow or memory pressure

### Solutions
1. **Reduce concurrent processes**: Keep under 8 active Claude sessions
2. **Clear context frequently**: Use `/clear` command between tasks
3. **Stagger session starts**: Avoid simultaneous session creation
4. **Monitor resource usage**: Check memory and CPU consumption
5. **Use headless mode**: For automation and batch processing

## Best Practices Summary

1. **Use Git Worktrees** for truly parallel development
2. **Stagger Session Windows** to avoid quota conflicts
3. **Implement Request Queuing** to stay under 12 concurrent requests
4. **Clear Context Frequently** with `/clear` command
5. **Use Headless Mode** for automation and CI/CD
6. **Monitor Resource Usage** and adjust allocation
7. **Coordinate API Calls** between processes

## Implementation Checklist

- [ ] Set up git worktrees for parallel development
- [ ] Implement request queuing system
- [ ] Configure session staggering
- [ ] Set up resource monitoring
- [ ] Create context optimization scripts
- [ ] Test concurrent session limits
- [ ] Document process allocation strategy
- [ ] Monitor API usage patterns

## Future Enhancements

- Automated session management
- Dynamic quota allocation
- Context caching system
- Load balancing between processes
- Integration with CI/CD pipelines
- Performance metrics dashboard

---

*Created: 2025-07-07*
*Last Updated: 2025-07-07*
*Status: Active*