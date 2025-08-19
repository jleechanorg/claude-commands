# /conv - Convergence Alias Command

**Alias for**: `/converge` - Iterative Goal Achievement Command

**Purpose**: Shortened alias for the full convergence system - achieve complex goals through autonomous plan-execute-validate-learn cycles until success criteria are met.

---

## Quick Usage
- `/conv <goal>` - Start converging toward a specific goal  
- `/conv --max-iterations N` - Set custom iteration limit (default: 10)
- `/conv --goal-integration` - Use /goal command for structured goal definition
- `/conv` - Resume previous convergence if interrupted

## Alias Benefits
- **Faster Typing**: `/conv` vs `/converge` (4 vs 9 characters)
- **Quick Access**: Shorter command for frequent convergence operations
- **Same Functionality**: Complete feature parity with `/converge`

## Common Usage Patterns

### Quick Goal Convergence
```bash
/conv "fix all failing tests"
/conv "create user authentication system" 
/conv "process PR comments and update code"
```

### With Configuration
```bash
/conv "complex implementation" --max-iterations 15
/conv "simple task" --goal-integration
```

### Resumption
```bash
/conv  # Auto-resumes interrupted convergence
```

---

## Full Documentation

**For complete documentation, examples, and advanced usage, see**: [/converge command](./converge.md)

The `/conv` command is a direct alias with identical functionality to `/converge`. All features, options, and behaviors are the same:

- ✅ **9-Step Convergence Cycle**: Goal Definition → Planning → Review → Approval → Execution → Validation → Learning → Status Report → Loop Decision
- ✅ **Autonomous Operation**: Zero user intervention after goal statement
- ✅ **Command Integration**: Uses `/goal`, `/plan`, `/reviewe`, `/cerebras`, `/test`, `/orch`, `/guidelines`
- ✅ **Memory MCP Learning**: Persistent pattern recognition and improvement
- ✅ **Resource Management**: Intelligent iteration and resource limits
- ✅ **Progress Tracking**: TodoWrite integration and status reporting

## Implementation Method

This alias command delegates all functionality to the main `/converge` command while providing a convenient shortened interface for frequent users.

---

**Alias Target**: [/converge - Iterative Goal Achievement Command](./converge.md)