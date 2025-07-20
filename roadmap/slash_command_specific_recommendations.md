# Slash Command Specific Recommendations

## Commands to Keep as Shell Scripts

### 1. `/header` (git-header.sh)
- **Reason**: High-frequency compliance command needs <50ms response
- **Current**: 185 lines of bash with git operations
- **Recommendation**: Keep as shell, add PR lookup caching
- **Enhancement**: Consider simple file cache for PR info (5-minute TTL)

### 2. `/integrate` 
- **Reason**: Chains multiple git commands efficiently
- **Recommendation**: Keep as shell wrapper around integrate.sh
- **Note**: Shell is perfect for sequential git operations

### 3. `/resolve_conflicts`
- **Reason**: Simple git operation wrapper
- **Recommendation**: Keep as shell for direct git access

## Commands to Convert to Python

### 1. `/execute` (HIGH PRIORITY)
- **Current**: Markdown-only despite being core workflow
- **Recommendation**: Implement in Python with Click
- **Features needed**:
  - TodoWrite integration for circuit breaker
  - Subagent decision logic
  - Progress tracking
  - Proper argument parsing

### 2. Test Command Suite (HIGH PRIORITY)
- **Current**: 14 variants (testui, testuif, testhttp, testi, etc.)
- **Recommendation**: Single unified test runner
- **Implementation**:
  ```python
  @cli.group()
  def test():
      """Run tests"""
  
  @test.command()
  @click.option('--mock/--real', default=True)
  @click.option('--browser/--http', default=True)
  def run(mock, browser):
      """Execute test suite with specified environment and browser options.
      
      Runs UI tests with Puppeteer or HTTP tests with requests library.
      Mock mode uses test doubles, real mode hits actual APIs.
      """
  ```

### 3. `/context`
- **Current**: Markdown-only
- **Recommendation**: Implement context tracking with Memory MCP
- **Features**: Store/retrieve context across sessions

### 4. `/plan`
- **Current**: Markdown-only variant of execute
- **Recommendation**: Extend execute.py with approval flag
- **Reuse**: Same logic as execute but with user approval step

## Commands to Deprecate/Simplify

### 1. Command Composition System
- **Files**: composition_hook.py, combinations.md
- **Issue**: Over-engineered NLP parsing
- **Recommendation**: Remove entirely, trust Claude's intelligence
- **Replacement**: Simple command chaining in shell

### 2. Enhanced Variants
- **Files**: execute-enhanced.md, ENHANCED_ALIASES.md
- **Issue**: Duplicate functionality
- **Recommendation**: Merge useful features into main commands

### 3. Test Variants Consolidation
- **Deprecate**: Individual test command files
- **Keep**: Unified test runner with clear options
- **Aliases**: Maintain for backward compatibility

## Commands to Leave as Markdown

### 1. Thinking Modifiers
- `/think`, `/thinku`, `/debug`
- **Reason**: Modify Claude's behavior, not executable
- **Keep as**: Documentation/guidance

### 2. Documentation Commands
- `/arch`, `/review`, `/roadmap`
- **Reason**: Pure guidance for Claude
- **Keep as**: Structured templates

### 3. Meta Commands
- `/list` - Auto-generate from actual implementations
- `/combo-help` - Document command combinations

## New Commands to Add

### 1. `/validate`
- **Purpose**: Pre-flight checks before operations
- **Implementation**: Python with comprehensive checks
- **Features**: Test status, git state, dependencies

### 2. `/rollback`
- **Purpose**: Quick rollback for failed operations
- **Implementation**: Shell for speed
- **Features**: Git reset, cleanup, state restoration

### 3. `/monitor`
- **Purpose**: Real-time operation monitoring
- **Implementation**: Python with streaming output
- **Features**: Progress tracking, resource usage, alerts

## Implementation Priority Matrix

| Priority | Command | Type | Complexity | Impact |
|----------|---------|------|------------|--------|
| 1 | `/execute` | Convert to Python | High | Critical |
| 2 | Test suite | Unify in Python | High | High |
| 3 | `/header` | Enhance shell | Low | High |
| 4 | `/context` | New Python | Medium | Medium |
| 5 | Composition | Deprecate | Low | Medium |
| 6 | `/plan` | Extend execute | Low | Medium |
| 7 | Enhanced variants | Deprecate | Low | Low |

## Migration Strategy

### Phase 1 (Immediate)
1. Implement `/execute` in Python
2. Create unified test runner
3. Set up Click framework structure

### Phase 2 (Week 1-2)
1. Migrate high-impact commands
2. Deprecate redundant variants
3. Update documentation

### Phase 3 (Week 2-3)
1. Add new utility commands
2. Optimize performance
3. Complete test coverage

## Key Principles

1. **Performance First**: Keep shell for <100ms operations
2. **Complexity Needs Python**: Error handling, options, logic
3. **Trust Claude**: No fake NLP, Claude provides intelligence
4. **User Experience**: Fewer commands, clearer purpose
5. **Maintainability**: Consistent patterns, good tests

## File Structure After Migration

```
commands/
├── core/
│   ├── execute.py      # Main workflow (new)
│   ├── test.py         # Unified runner (new)
│   ├── context.py      # Context tracking (new)
│   └── header.sh       # Fast git info (keep)
├── lib/
│   ├── command_base.py # Shared Click patterns
│   ├── git_utils.py    # Git operations
│   └── test_utils.py   # Test helpers
├── deprecated/         # Gradual removal
│   └── *.md           # Old variants
└── docs/              # Pure documentation
    └── *.md           # Behavior modifiers
```

This approach creates a cleaner, more maintainable command system while preserving performance for critical operations.