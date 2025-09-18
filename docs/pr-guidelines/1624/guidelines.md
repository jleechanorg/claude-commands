# PR #1624 Guidelines - feat: Worktree backup system with automatic Claude data protection

**PR**: #1624 - feat: Worktree backup system with automatic Claude data protection
**Created**: 2025-09-17
**Purpose**: Specific guidelines for shell script security and system integration patterns

## 🎯 PR-Specific Principles

### System Integration Security
- Shell scripts must validate all dynamic paths before execution
- Wildcard expansions require bounded scope and validation
- Cron job setup needs absolute paths and environment variable validation
- Process management should use atomic operations to prevent race conditions

### Solo Developer Security Focus
- Focus on real vulnerabilities: command injection, path traversal, resource exhaustion
- Filter enterprise paranoia: excessive validation for trusted system paths
- Balance security with development velocity for solo/small team contexts

## 🚫 PR-Specific Anti-Patterns

### ❌ **Unsafe Wildcard Path Expansion**
```bash
# WRONG: Unbounded wildcard that could include malicious directories
for wt in "$HOME/projects/worktree_"*; do
    exec "$wt/scripts/backup.sh"
done
```

**Problem**: Wildcard expansion could include directories like `worktree_../../etc/passwd`

### ✅ **Safe Path Validation with Bounds Checking**
```bash
# CORRECT: Validate paths and use realpath for security
for wt_pattern in "$HOME/projects/worktree_"*; do
    # Validate the path is within expected directory
    if [[ "$wt_pattern" =~ ^$HOME/projects/worktree_[a-zA-Z0-9_-]+$ ]]; then
        wt=$(realpath "$wt_pattern" 2>/dev/null)
        if [[ "$wt" == "$HOME/projects/"* && -d "$wt" ]]; then
            exec "$wt/scripts/backup.sh"
        fi
    fi
done
```

### ❌ **Race Condition in Process Detection**
```bash
# WRONG: Time-of-check vs time-of-use vulnerability
if pgrep -f "agent_monitor.py" > /dev/null 2>&1; then
    startup_success=true
    # Process could exit here before next operation
fi
```

### ✅ **Atomic Process Management**
```bash
# CORRECT: Use file locks or atomic operations
local LOCK_FILE="/tmp/orchestration.lock"
if (set -C; echo $$ > "$LOCK_FILE") 2>/dev/null; then
    trap 'rm -f "$LOCK_FILE"' EXIT
    if pgrep -f "agent_monitor.py" > /dev/null 2>&1; then
        startup_success=true
    fi
else
    echo "Orchestration already starting (locked by PID $(cat "$LOCK_FILE" 2>/dev/null))"
fi
```

### ❌ **Cron Environment Variable Injection Risk**
```bash
# WRONG: Direct environment variable usage in cron
echo '0 */4 * * * $HOME/.local/bin/backup.sh' | crontab -
```

### ✅ **Absolute Paths in Cron Jobs**
```bash
# CORRECT: Use absolute paths and validate environment
HOME_DIR="$(echo ~)" # Expand to absolute path
echo "0 */4 * * * $HOME_DIR/.local/bin/backup.sh" | crontab -
```

## 📋 Implementation Patterns for This PR

### Shell Script Security Patterns
1. **Path Validation**: Always use `realpath` and bounds checking for dynamic paths
2. **Process Management**: Use file locks for atomic operations and race condition prevention
3. **Cron Security**: Use absolute paths and validate environment variables before cron setup
4. **Resource Cleanup**: Implement comprehensive cleanup with validation in trap handlers

### System Integration Best Practices
1. **Graceful Degradation**: Continue operation when optional components fail
2. **Platform Compatibility**: Detect OS-specific paths and handle multiple platforms
3. **Logging Strategy**: Log security-relevant operations for audit trail
4. **Error Boundaries**: Isolate failures to prevent cascade effects

## 🔧 Specific Implementation Guidelines

### Security Validation Checklist
- [ ] All dynamic paths validated with `realpath` and bounds checking
- [ ] Wildcard expansions use pattern matching for safety
- [ ] Process operations use atomic mechanisms (file locks, etc.)
- [ ] Cron entries use absolute paths and validated environment variables
- [ ] Resource cleanup includes validation and error handling

### Code Quality Standards
- [ ] Consistent error handling with `set -euo pipefail`
- [ ] Comprehensive logging for security-relevant operations
- [ ] Platform detection consolidated into reusable functions
- [ ] All external command calls include timeout mechanisms

### Solo Developer Security Focus
- [ ] Real vulnerabilities addressed: command injection, path traversal, resource exhaustion
- [ ] Enterprise paranoia filtered: no excessive validation for trusted system operations
- [ ] Practical security balance maintained for development velocity

---
**Status**: Guidelines created from /reviewdeep analysis - comprehensive security and architectural review completed
**Last Updated**: 2025-09-17
