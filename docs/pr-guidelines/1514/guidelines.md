# PR #1514 Guidelines - Backup Fix: Restore and Optimize Memory Management

**PR**: #1514 - [Backup Fix: Restore and Optimize Memory Management](https://github.com/jleechanorg/worldarchitect.ai/pull/1514)
**Created**: September 9, 2025
**Purpose**: Security-focused PR involving memory backup script fixes with hardcoded URL to environment variables and cross-platform compatibility improvements

## Scope
- This document contains PR-specific guidelines for security vulnerability fixes and cross-platform compatibility improvements
- Security patterns: Environment variable migration, hardcoded credential removal, secure script practices
- Compatibility patterns: bc/python3 to awk migration, portable shell scripting
- Canonical protocols are in docs/pr-guidelines/base-guidelines.md

## 🎯 PR-Specific Security Principles

### 1. **Environment Variable Migration Pattern**
- **Critical**: Replace ALL hardcoded URLs/credentials with environment variables
- **Pattern**: `REPO_URL="https://hardcoded.com"` → `REPO_URL="${BACKUP_REPO_URL:-default}"`
- **Validation**: Scan scripts for hardcoded URLs, tokens, paths that could be configured
- **Documentation**: Update setup instructions to specify required environment variables

### 2. **Cross-Platform Compatibility Pattern**  
- **Critical**: Replace GNU-specific tools with portable POSIX alternatives
- **Pattern**: `bc`, `python3` → `awk` for mathematical operations
- **Pattern**: GNU-specific flags → POSIX-compliant alternatives
- **Testing**: Verify scripts work on macOS, Linux, and minimal shell environments

### 3. **Secure Defaults Pattern**
- **Critical**: Environment variables MUST have secure defaults or fail gracefully
- **Pattern**: `${VAR:-}` checks for empty values before proceeding
- **Pattern**: Explicit error messages when required environment variables missing
- **Validation**: Test scripts with missing/empty environment variables

## 🚫 PR-Specific Security Anti-Patterns

### 1. **Hardcoded Security Information**
```bash
# WRONG - Hardcoded URLs that could change or contain sensitive info
REPO_URL="https://github.com/user/repo.git"
API_ENDPOINT="https://api.private-service.com"

# WRONG - Hardcoded paths that may not exist across systems
BACKUP_DIR="/Users/specific-user/backups"
```

### 2. **Platform-Specific Dependencies**
```bash  
# WRONG - GNU-specific tools not available on all systems
echo "3.14159 * 2" | bc -l  # bc not available on minimal systems
python3 -c "print(3.14159 * 2)"  # python3 may not be available

# WRONG - GNU-specific flags
grep -P "pattern" file  # -P (Perl regex) not POSIX compliant
```

### 3. **Insecure Environment Variable Handling**
```bash
# WRONG - No validation of environment variables  
REPO_URL="$BACKUP_REPO_URL"  # Could be empty/undefined

# WRONG - Exposing sensitive values in logs
echo "Connecting to $SECRET_URL"  # Logs sensitive information
```

## 📋 Implementation Patterns for This PR

### 1. **Environment Variable Security Pattern**
```bash
# RIGHT - Secure environment variable usage with validation
REPO_URL="${BACKUP_REPO_URL:-}"
if [ -z "$REPO_URL" ]; then
    echo "Error: BACKUP_REPO_URL environment variable not set"
    echo "Please set: export BACKUP_REPO_URL='https://github.com/user/repo.git'"
    return 1
fi

# RIGHT - Logging without exposing sensitive data
echo "Connecting to backup repository..."  # No URL in logs
```

### 2. **Cross-Platform Mathematical Operations**
```bash
# RIGHT - Use awk for portable mathematical operations
result=$(echo "3.14159 2" | awk '{print $1 * $2}')

# RIGHT - POSIX-compliant pattern matching
grep -E "pattern" file  # Extended regex is POSIX-compliant
```

### 3. **Secure File Path Handling** 
```bash
# RIGHT - Use relative paths or configurable base paths
BACKUP_DIR="${BACKUP_BASE_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

# RIGHT - Validate directories exist before operations
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory $BACKUP_DIR does not exist"
    return 1
fi
```

## 🔧 Specific Implementation Guidelines

### 1. **Security Review Checklist**
- [ ] Scan all scripts for hardcoded URLs, tokens, credentials
- [ ] Replace with environment variables using `${VAR:-default}` pattern
- [ ] Add validation for required environment variables
- [ ] Update documentation with required environment setup
- [ ] Test scripts with missing environment variables to ensure graceful failures

### 2. **Cross-Platform Testing Checklist**
- [ ] Test scripts on macOS and Linux
- [ ] Replace GNU-specific tools (bc, python3) with POSIX alternatives (awk)
- [ ] Use POSIX-compliant flags for common tools (grep -E vs grep -P)
- [ ] Verify mathematical operations work without external dependencies
- [ ] Test in minimal shell environments (dash, ash)

### 3. **File Justification Protocol Compliance**
- [ ] Document why each modified file requires changes vs integration
- [ ] Ensure script improvements stay within existing files (no new script creation)
- [ ] Justify environment variable setup location (existing config vs new files)
- [ ] Verify merge conflict resolution preserves security improvements

### 4. **Merge Conflict Resolution Strategy**
- [ ] Security changes ALWAYS take precedence over convenience patterns
- [ ] Environment variable patterns take precedence over hardcoded values
- [ ] Cross-platform compatibility takes precedence over system-specific optimizations
- [ ] Preserve existing functionality while adding security layers

---
**Status**: Template created by /guidelines command for security-focused PR with environment variable migration and cross-platform compatibility
**Last Updated**: September 9, 2025