# Slash Command Architecture Plan

## Executive Summary

Based on comprehensive analysis of 61 slash commands, best practices research, and current implementation patterns, this plan proposes a **hybrid architecture** that optimizes for both performance and maintainability while preserving the strengths of the current system.

## Current State Analysis

### Implementation Breakdown
- **40 implemented commands** (38 Python, 2 Shell)
- **21 markdown-only commands** (documentation/guidance)
- **Well-structured Python modules** with shared utilities
- **Inconsistent patterns** between similar commands

### Key Findings

1. **Over-engineering in some areas**: Complex command composition system that duplicates Claude's natural language capabilities
2. **Under-implementation in critical areas**: Core workflow commands like `/execute` are markdown-only
3. **Good modularization**: Existing Python commands demonstrate solid architecture patterns
4. **Testing gaps**: Many commands lack proper test coverage

## Proposed Architecture

### 1. Hybrid Command Structure

```
.claude/
├── commands/
│   ├── core/              # High-frequency, performance-critical
│   │   ├── header.sh      # Shell: Fast startup (measured: ~400ms baseline)
│   │   ├── integrate.sh   # Shell: Git operations chain
│   │   └── quick.sh       # Shell: Other fast operations
│   │
│   ├── complex/           # Python implementations
│   │   ├── __init__.py
│   │   ├── cli.py         # Click-based main entry
│   │   ├── execute.py     # Core workflow command
│   │   ├── test.py        # Unified test runner
│   │   └── orchestrate.py # Agent coordination
│   │
│   ├── lib/               # Shared libraries (existing)
│   │   ├── __init__.py
│   │   ├── git_utils.py
│   │   ├── test_utils.py
│   │   └── ai_utils.py
│   │
│   └── docs/              # Markdown documentation
│       ├── think.md       # Behavior modifiers
│       ├── aliases.md     # Command aliases
│       └── examples.md    # Usage examples
│
└── claude.sh              # Master dispatcher (enhanced)
```

### 2. Implementation Priorities

#### Phase 1: Critical Commands (Week 1)
1. **Convert `/execute` to Python**
   - Currently markdown-only despite being core workflow
   - Implement with Click for proper argument handling
   - Include TodoWrite integration for circuit breaker

2. **Unify test commands**
   - Consolidate 14 test variants into single runner
   - Shared configuration and options
   - Maintain backward compatibility with aliases

3. **Enhance `/header`**
   - Keep as shell for performance
   - Add caching for PR lookups
   - Integrate with Memory MCP for persistence

#### Phase 2: Consolidation (Week 2)
1. **Command groups with Click**
   ```python
   @cli.group()
   def test():
       """Testing commands"""
   
   @test.command()
   def ui():
       """Run UI tests"""
   
   @test.command()
   def http():
       """Run HTTP tests"""
   ```

2. **Deprecate over-engineered systems**
   - Remove complex command composition
   - Trust Claude's NLP instead of building parsers
   - Simplify to direct command execution

3. **Standardize patterns**
   - Consistent error handling
   - Unified logging approach
   - Shared configuration management

#### Phase 3: Enhancement (Week 3)
1. **Add proper testing**
   - pytest fixtures for command testing
   - Integration tests for shell scripts
   - Coverage requirements (>80%)

2. **Performance optimization**
   - Lazy imports for Python commands
   - Command discovery caching
   - Parallel execution where beneficial

3. **Documentation generation**
   - Auto-generate `/list` from implementations
   - Include examples in help text
   - Version tracking for changes

## Technical Decisions

### Shell vs Python Guidelines

**Use Shell Scripts When:**
- Startup time matters (<100ms requirement)
- Simple Git/system command chains
- No complex logic or error handling
- Universal compatibility needed

**Use Python When:**
- Complex business logic
- Multiple options/arguments
- API integrations
- Testing requirements
- Error handling critical

### Framework Choice: Click

**Rationale:**
- Decorator-based matches existing patterns
- Excellent command grouping support
- Strong testing utilities
- Active maintenance and community
- Used by major Python projects

**Implementation Pattern:**
```python
import click
from ..lib import git_utils, ai_utils

@click.command()
@click.option('--verbose', is_flag=True)
@click.option('--subagents/--no-subagents', default=True)
@click.argument('task')
def execute(verbose, subagents, task):
    """Execute tasks with optional subagent coordination."""
    # Implementation
```

### Testing Strategy

1. **Unit tests** for individual commands
2. **Integration tests** for command chains
3. **Smoke tests** for shell scripts
4. **Performance benchmarks** for critical paths

## Migration Plan

### Week 1: Foundation
- [ ] Set up Click framework structure
- [ ] Convert `/execute` to Python
- [ ] Create unified test runner
- [ ] Update master dispatcher

### Week 2: Migration
- [ ] Migrate complex commands by priority
- [ ] Deprecate redundant commands
- [ ] Update documentation
- [ ] Add comprehensive tests

### Week 3: Polish
- [ ] Performance optimization
- [ ] Documentation generation
- [ ] User migration guide
- [ ] Monitoring and metrics

## Success Metrics

1. **Performance**: Header command <50ms, others <200ms startup
   - Measurement: Use `time` command for 10 consecutive runs
   - Target: Mean startup time with 95% confidence interval
   - Baseline: Current performance benchmarks recorded
2. **Reliability**: >95% test coverage for Python commands
   - Measurement: Coverage reports via pytest-cov
   - Target: Line coverage percentage
3. **Usability**: Reduced command variants by 40%
   - Measurement: Count of command files before/after
   - Target: From 61 total commands to ~35-40 meaningful variants
4. **Maintainability**: Clear separation of concerns
   - Measurement: Cyclomatic complexity analysis
   - Target: Average complexity <10 per function

## Risk Mitigation

1. **Backward Compatibility**
   - Keep aliases for deprecated commands
   - Gradual deprecation with warnings
   - Clear migration documentation

2. **Performance Regression**
   - Benchmark before/after each change
   - Keep shell scripts for critical paths
   - Profile Python startup optimization

3. **User Disruption**
   - Communicate changes clearly
   - Provide migration period
   - Maintain old commands temporarily

## Recommendations

### Immediate Actions
1. **Stop** adding new markdown-only commands for executable functionality
2. **Stop** building complex parsing systems - trust Claude's NLP
3. **Start** implementing critical commands properly
4. **Start** consolidating related commands

### Long-term Vision
1. **Modular architecture** with clear boundaries
2. **Performance-first** for high-frequency commands
3. **Maintainability** through consistent patterns
4. **User experience** with unified interfaces

## Conclusion

This architecture plan balances pragmatism with best practices. The hybrid approach leverages shell scripts for performance-critical operations while using Python's Click framework for complex command logic. By focusing on real user needs rather than over-engineering, we can create a more maintainable and efficient command system.

The key insight is to **trust Claude's intelligence** rather than building inferior parsing systems. Commands should be simple executors of Claude's plans, not trying to replicate natural language understanding.