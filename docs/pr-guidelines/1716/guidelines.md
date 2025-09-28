# PR #1716 Guidelines - Genesis Self-Determination with Rigorous Completion Detection

**PR**: #1716 - [feat(genesis): Enhanced self-determination with rigorous completion detection](https://github.com/jleechanorg/worldarchitect.ai/pull/1716)
**Created**: 2025-09-24
**Purpose**: Specific guidelines for Genesis self-determination correctness and completion detection patterns

## Scope
- This document contains PR #1716-specific correctness patterns, evidence, and solutions for Genesis self-determination implementation.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### Genesis Self-Determination Core Principles
1. **Observer-Only Monitoring**: External observers NEVER make completion decisions - only Genesis decides
2. **Rigorous Completion Detection**: Multiple validation layers prevent false positives
3. **Search-First Validation**: Always validate necessity before implementing
4. **No-Placeholders Policy**: Full implementations only, reject all TODO/FIXME patterns
5. **Subagent Delegation**: Use claude -p subagents for expensive operations (max 5)
6. **Context-Aware Progress**: Distinguish positive progress from negative progress statements

## 🚫 PR-Specific Anti-Patterns

### ❌ **False Positive Progress Detection**
**Problem Found**: Regex pattern matching progress percentages without context validation
```python
# WRONG - Will incorrectly match "We need 95% more work toward completion"
matches = re.findall(r"(\d+)%.*?toward.*?complet", response_lower)
if matches:
    progress = int(matches[0])
    if progress >= 95:  # FALSE POSITIVE!
        return True
```

### ✅ **Context-Aware Progress Validation**
```python
# CORRECT - Validate context to distinguish positive vs negative progress
matches = re.findall(r"(\d+)%.*?toward.*?complet", response_lower)
if matches:
    progress = int(matches[0])
    if progress >= 95:
        # Check for negative context indicators
        context_window = response_lower[max(0, match_start-100):match_end+100]
        negative_indicators = ['need', 'require', 'missing', 'lacking', 'want', 'short']
        if not any(indicator in context_window for indicator in negative_indicators):
            return True
```

### ❌ **Unsanitized Prompt Construction**
**Problem Found**: User-controlled goal text inserted directly into prompts
```python
# WRONG - Command injection vulnerability
prompt = f"""GENESIS EXECUTION - SEARCH-FIRST WITH SUBAGENTS
GOAL: {refined_goal}  # <-- Unsanitized user input
EXECUTION STRATEGY:
{execution_strategy}  # <-- Also unsanitized
"""
```

### ✅ **Sanitized Prompt Construction**
```python
# CORRECT - Sanitize all user inputs before prompt construction
def sanitize_prompt_input(text, max_length=2000):
    """Sanitize user input for safe prompt construction."""
    if not isinstance(text, str):
        return str(text)[:max_length]

    # Remove potential injection patterns
    sanitized = re.sub(r'[`${}\\;|&<>]', '', text)
    # Limit length to prevent excessive context usage
    return sanitized[:max_length].strip()

prompt = f"""GENESIS EXECUTION - SEARCH-FIRST WITH SUBAGENTS
GOAL: {sanitize_prompt_input(refined_goal)}
EXECUTION STRATEGY:
{sanitize_prompt_input(execution_strategy)}
"""
```

### ❌ **Self-Defeating Error Recovery**
**Problem Found**: Quality retry logic makes prompts longer, increasing timeout risk
```python
# WRONG - Retry with even longer prompt
if not is_quality:
    retry_prompt = f"""{prompt}  # Original long prompt
QUALITY REJECTION: Previous output contained placeholders.  # + Even more text
"""
    result = execute_claude_command(retry_prompt, timeout=600)  # Same timeout!
```

### ✅ **Smart Error Recovery**
```python
# CORRECT - Analyze root cause and use targeted retry
if not is_quality:
    # Identify specific placeholder patterns found
    placeholder_found = validate_implementation_quality(result)[1]

    # Use shorter, focused retry prompt
    retry_prompt = f"""GENESIS QUALITY RETRY
TASK: {refined_goal[:500]}  # Truncated for focus
ISSUE: {placeholder_found}
REQUIREMENT: Provide complete implementation, no {placeholder_found.split('(')[1].split(')')[0]} patterns
"""
    # Use longer timeout for retry
    result = execute_claude_command(retry_prompt, timeout=900)
```

### ❌ **Race Condition File Operations**
**Problem Found**: Multiple Genesis instances could corrupt shared files
```python
# WRONG - No locking for concurrent file access
def update_progress_file(progress_data):
    with open("progress.json", "w") as f:
        json.dump(progress_data, f)
```

### ✅ **Atomic File Operations with Locking**
```python
# CORRECT - Use atomic operations with proper locking
import fcntl
import tempfile
import os

def update_progress_file(progress_data, file_path="progress.json"):
    """Atomically update progress file with proper locking."""
    lock_file = f"{file_path}.lock"

    with open(lock_file, "w") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Write to temporary file first
            temp_file = f"{file_path}.tmp.{os.getpid()}"
            with open(temp_file, "w") as f:
                json.dump(progress_data, f, indent=2)

            # Atomic move to final location
            os.rename(temp_file, file_path)

        except IOError:
            raise Exception(f"Could not acquire lock for {file_path}")
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
```

## 📋 Implementation Patterns for This PR

### Genesis Completion Detection Pattern
1. **Multi-Layer Validation**: Check explicit signals, progress percentages, gap analysis, and criteria satisfaction
2. **Context Window Analysis**: Examine surrounding text for negative indicators before accepting positive signals
3. **Threshold Configuration**: Make completion thresholds configurable per goal complexity
4. **Signal Prioritization**: Explicit completion statements take precedence over inferred progress

### Observer-Only Monitoring Pattern
1. **Read-Only Operations**: Observer scripts only read state, never modify completion decisions
2. **Non-Interfering Logging**: Log observations without affecting Genesis execution
3. **Session Lifecycle Tracking**: Monitor session existence without determining completion
4. **Graceful Degradation**: Continue observing even if individual checks fail

### Subagent Delegation Pattern
1. **Expense-Based Delegation**: Delegate costly operations (code gen, testing, file ops) to subagents
2. **Pool Size Limits**: Enforce maximum of 5 concurrent subagents to prevent resource exhaustion
3. **Context Management**: Keep primary context focused on scheduling, not implementation details
4. **Quality Gates**: Validate subagent output before accepting results

## 🔧 Specific Implementation Guidelines

### Completion Detection Implementation
```python
def robust_check_goal_completion(consensus_response, exit_criteria, config=None):
    """Enhanced completion detection with context awareness and configuration."""
    if not consensus_response or not isinstance(consensus_response, str):
        return False, "Invalid response"

    # Configurable thresholds based on goal complexity
    completion_threshold = config.get('completion_threshold', 95) if config else 95
    max_response_size = config.get('max_response_size', 50000) if config else 50000

    # Size limiting with intelligent truncation
    if len(consensus_response) > max_response_size:
        # Keep end of response where completion signals most likely appear
        consensus_response = consensus_response[-max_response_size:]

    response_lower = consensus_response.lower()

    # Multi-layer completion validation
    explicit_signals = check_explicit_completion_signals(response_lower)
    if explicit_signals[0]:
        return True, f"Explicit completion: {explicit_signals[1]}"

    progress_signals = check_progress_with_context(response_lower, completion_threshold)
    if progress_signals[0]:
        return True, f"High progress: {progress_signals[1]}"

    gap_analysis = check_critical_gaps(response_lower)
    if gap_analysis[0]:
        return True, f"No critical gaps: {gap_analysis[1]}"

    criteria_check = check_exit_criteria_satisfaction(response_lower, exit_criteria)
    if criteria_check[0]:
        return True, f"Exit criteria satisfied: {criteria_check[1]}"

    return False, "Completion criteria not met"
```

### Error Recovery Implementation
```python
def smart_quality_retry(original_prompt, failed_result, max_retries=2):
    """Implement smart error recovery with root cause analysis."""
    for attempt in range(max_retries):
        # Analyze failure reason
        quality_result = validate_implementation_quality(failed_result)
        if quality_result[0]:
            return failed_result  # Actually successful

        failure_reason = quality_result[1]

        # Create focused retry prompt
        retry_prompt = create_focused_retry_prompt(original_prompt, failure_reason)

        # Progressive timeout increase
        timeout = 600 * (1.5 ** attempt)

        retry_result = execute_claude_command(retry_prompt, timeout=timeout)
        if retry_result:
            failed_result = retry_result
        else:
            break  # Don't retry on execution failure

    return failed_result
```

### Input Validation Implementation
```python
def validate_genesis_inputs(refined_goal, iteration_num, execution_strategy, plan_context=""):
    """Comprehensive input validation for Genesis functions."""
    errors = []

    # Goal validation
    if not isinstance(refined_goal, str) or len(refined_goal.strip()) == 0:
        errors.append("refined_goal must be non-empty string")
    elif len(refined_goal) > 10000:
        errors.append("refined_goal exceeds maximum length (10000 chars)")

    # Iteration validation
    if not isinstance(iteration_num, int) or iteration_num < 1:
        errors.append("iteration_num must be positive integer")
    elif iteration_num > 1000:
        errors.append("iteration_num exceeds reasonable maximum (1000)")

    # Strategy validation
    if not isinstance(execution_strategy, str):
        errors.append("execution_strategy must be string")
    elif len(execution_strategy) > 20000:
        errors.append("execution_strategy exceeds maximum length (20000 chars)")

    # Context validation
    if not isinstance(plan_context, str):
        errors.append("plan_context must be string")
    elif len(plan_context) > 5000:
        errors.append("plan_context exceeds maximum length (5000 chars)")

    if errors:
        raise ValueError(f"Genesis input validation failed: {'; '.join(errors)}")

    return True
```

## Quality Gates and Validation Steps

### Pre-Implementation Validation
1. **Input Sanitization Check**: All user inputs properly sanitized before use
2. **Context Size Validation**: Total prompt context stays within API limits
3. **Parameter Type Checking**: All function parameters validated for correct types and ranges
4. **Concurrency Safety Review**: File operations use atomic patterns with proper locking

### Post-Implementation Validation
1. **Completion Logic Testing**: Test with edge cases like negative progress statements
2. **Security Penetration Testing**: Test prompt injection and command injection vectors
3. **Concurrency Testing**: Test multiple Genesis instances with shared resources
4. **Error Recovery Testing**: Test retry logic with various failure scenarios

### Production Readiness Checklist
- [ ] ✅ False positive completion detection fixed
- [ ] ✅ Command injection vulnerability patched
- [ ] ✅ Race condition file operations resolved
- [ ] ✅ Input validation implemented
- [ ] ✅ Smart error recovery deployed
- [ ] ✅ Comprehensive logging added
- [ ] ✅ Observer-only monitoring verified
- [ ] ✅ Concurrency testing passed

---
**Status**: Implementation guidelines created based on comprehensive correctness review
**Last Updated**: 2025-09-24
**Review Type**: Correctness-focused with security and edge case analysis
**Critical Issues Identified**: 7 critical, 5 important correctness issues requiring fixes before production deployment
