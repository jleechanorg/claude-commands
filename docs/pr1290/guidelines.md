# PR #1290 Guidelines - Universal command composition hook with security fixes

**PR**: #1290 - [fix: Universal command composition hook with JSON stdin parsing and comprehensive tests](https://github.com/jleechanorg/worldarchitect.ai/pull/1290)
**Created**: 2025-08-13
**Purpose**: Document critical security patterns and anti-patterns discovered during hook development

## Scope
- This document contains PR-specific security vulnerabilities, evidence, and fixes for PR #1290.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### Security-First Shell Script Development
- **Principle**: Every shell script that processes user input is a potential attack vector
- **Application**: Treat all external input as potentially malicious, especially in hook systems
- **Validation**: Use proper escaping, input validation, and safe command construction patterns

### Comprehensive Test-Driven Security (TDD-S)
- **Principle**: Security vulnerabilities must be caught by automated tests, not manual review
- **Application**: Create specific regression tests for each vulnerability class discovered
- **Validation**: 100% test coverage for security-critical code paths

### Evidence-Based Vulnerability Assessment
- **Principle**: Document specific attack vectors with concrete examples and test cases
- **Application**: Each security fix must include reproduction test case and validation test
- **Validation**: Security claims must be backed by executable proof

## 🚫 PR-Specific Anti-Patterns

### ❌ **Inconsistent Command Counting Logic**
**Problem**: Using different counting mechanisms for filtering decisions vs execution strategy
```bash
# WRONG: Mixed counting sources causing strategy inconsistency
cmd_count_in_input=5  # Initial detection count
command_count=2       # Post-filtering count  
if [[ $cmd_count_in_input -le 2 ]]; then  # ❌ Using wrong variable
    strategy="simple"
fi
```

### ✅ **Consistent Command Count Tracking**
**Solution**: Single source of truth for command counts throughout filtering pipeline
```bash
# CORRECT: Consistent counting from filtering loop
actual_cmd_count=0
for cmd in $raw_commands; do
    if valid_command_detected; then
        commands="$commands$cmd "
        actual_cmd_count=$((actual_cmd_count + 1))  # ✅ Track actual count
    fi
done
command_count=$actual_cmd_count  # ✅ Use consistent count
```

### ❌ **Regex Injection in Shell Scripts**
**Problem**: Using unescaped variables in regex patterns allowing injection attacks
```bash
# WRONG: Direct variable interpolation in regex (EXPLOITABLE)
if echo "$input" | grep -qE "(^|[[:space:]])$cmd([[:space:]]|$)"; then
    # $cmd could contain: .*|rm -rf / 
    # Causing regex to match everything and execute dangerous patterns
fi
```

### ✅ **Proper Regex Escaping**
**Solution**: Escape all user-controlled content before using in regex patterns
```bash
# CORRECT: Proper sed escaping for regex safety
escaped_cmd=$(printf '%s' "$cmd" | sed 's/[]\[\(\)\{\}\*\+\?\^\$\|\\]/\\&/g')
if echo "$input" | grep -qE "(^|[[:space:]])$escaped_cmd([[:space:]]|$)"; then
    # ✅ Safe: $escaped_cmd cannot break regex pattern
fi
```

### ❌ **Unsafe Boundary Detection**
**Problem**: Using regex patterns for literal string searches in security contexts
```bash
# WRONG: Regex pattern matching for boundary detection (vulnerable)
if echo "$input_start" | grep -q "$cmd"; then
    # $cmd with special chars can break grep or match unintended content
fi
```

### ✅ **Safe Literal String Matching**
**Solution**: Use fixed-string matching for security-critical boundary detection
```bash
# CORRECT: Literal string matching prevents pattern injection
if echo "$input_start" | grep -qF "$cmd"; then
    # ✅ Safe: -F flag forces literal string matching
fi
```

## 📋 Implementation Patterns for This PR

### Hook System Security Architecture
- **JSON Input Validation**: Always validate JSON structure before processing
- **Command Extraction**: Use allowlist patterns for command detection (`/[a-zA-Z][a-zA-Z0-9_-]*`)
- **Context-Aware Filtering**: Distinguish pasted content from intentional commands using heuristics
- **Secure Text Processing**: Escape all user input before regex operations

### Test-Driven Security Development
- **Security Regression Tests**: 4 specific tests for vulnerability classes discovered
- **Attack Vector Coverage**: Test malicious regex chars, boundary injection, count manipulation
- **Evidence-Based Validation**: Each fix includes before/after test demonstrating vulnerability closure

### Error Handling and Logging
- **Optional Debug Logging**: Configurable via `COMPOSE_DEBUG` environment variable
- **Secure Log File Handling**: PID suffix and configurable paths to prevent symlink attacks
- **Graceful Degradation**: Hook continues functioning even with malformed input

## 🔧 Specific Implementation Guidelines

### Security Test Implementation
**Pattern**: For each vulnerability class, implement triplet tests:
1. **Exploit Test**: Verify vulnerability exists (should fail before fix)
2. **Fix Verification**: Verify fix prevents exploitation (should pass after fix)  
3. **Regression Protection**: Ensure fix doesn't break legitimate functionality

**Example from PR #1290**:
```bash
# Test 48: Regex injection prevention with special chars
run_test "Security: Regex injection prevention with special chars" \
    '{"prompt": "/test[0-9]+ /analysis* some normal text"}' \
    "🔍 Detected slash commands:/test /analysis"  # ✅ Special chars removed safely
```

### Shell Script Security Checklist
For any shell script processing external input:
- [ ] All variables used in regex patterns are properly escaped
- [ ] Command counting logic uses single source of truth
- [ ] Boundary detection uses literal string matching (`grep -qF`)
- [ ] Input validation rejects obviously malicious patterns
- [ ] Comprehensive test coverage for attack vectors
- [ ] Debug logging is optional and secure

### Command Composition Hook Patterns
- **Multi-Command Detection**: Use regex `/[a-zA-Z][a-zA-Z0-9_-]*` for comprehensive command support
- **Context Awareness**: Detect pasted content using GitHub-specific patterns and excessive slash heuristics
- **Intelligent Filtering**: Position-based filtering for commands in pasted content
- **Consistent Processing**: Same regex patterns for detection and cleanup operations

## 🔒 Security Validation Evidence

### Vulnerability Discovery Timeline
- **2025-08-13 20:50:19Z**: Cursor bot identifies "Command Filtering Flaw and Regex Injection Vulnerability"
- **2025-08-13 20:56:00Z**: Comprehensive security fixes applied
- **2025-08-13 20:56:30Z**: All 52 tests passing including security regression tests

### Attack Vector Analysis
**Confirmed Vulnerabilities (Fixed)**:
1. **CVE-Level Regex Injection**: Unescaped command variables in grep patterns
2. **Logic Bypass**: Command count inconsistency allowing wrong filtering strategy
3. **Boundary Detection Weakness**: Regex patterns vulnerable to pattern injection

**Security Test Coverage**:
- 4 specific security regression tests
- 52 total tests including edge cases and attack scenarios
- 100% pass rate after security fixes

### Fix Validation Commits
- **0ba6fdf6b**: Security fixes with regex escaping and count consistency
- **52 passing tests**: Including new security regression test suite
- **Zero false positives**: Legitimate commands still work correctly

---

**Status**: Complete security analysis and pattern documentation
**Last Updated**: 2025-08-13
**Security Level**: Production-ready with comprehensive vulnerability closure