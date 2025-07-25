# Universal Timeout Mitigation Implementation Plan

**Goal**: Apply timeout mitigation to ALL commands system-wide, not just the 3 tools currently protected.

**Current Status**: Foundation built, but only `/reviewdeep`, `arch.py`, and `think.py` are protected. Most commands still vulnerable to timeouts.

## 🎯 **Scope: Make EVERY Command Timeout-Resistant**

### ✅ **Already Protected (3/30+ tools)**
- `/reviewdeep` - Full size limits, retry logic, performance monitoring
- `arch.py` - Complete timeout mitigation with smart sampling
- `think.py` - Basic fake detection and size awareness

### ❌ **Still Vulnerable (25+ tools)**
Commands that need timeout mitigation applied:

**Critical Priority:**
- `pr.py` - Creates PRs, likely makes large Git operations
- `push.py` - Git operations that can timeout
- `learn.py` - File analysis operations
- `handoff.py` - Code analysis and file operations
- `execute.py` (if exists) - Task execution commands

**Medium Priority:**
- All `.py` files in `.claude/commands/`
- Any command that reads files, makes API calls, or runs subprocess operations
- Commands that use MultiEdit or other tool calls

**Low Priority:**
- Simple markdown commands (`.md` files)
- Pure documentation commands without file operations

## 🛠️ **Implementation Strategy**

### Phase 1: Audit All Commands
1. **Scan all `.py` files** in `.claude/commands/`
2. **Identify timeout risk factors** in each:
   - File read operations
   - Subprocess calls (git, gh, etc.)
   - API calls to external services
   - MultiEdit operations
   - Large context operations

### Phase 2: Apply Universal Pattern
For each vulnerable command, systematically add:

```python
# Standard imports for ALL commands
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
from request_optimizer import optimize_file_read, check_request_size, handle_timeout, optimizer

# Replace ALL file reads
# OLD: with open(filepath, 'r') as f: content = f.read()
# NEW:
read_params = optimize_file_read(filepath)
with open(filepath, 'r') as f:
    if 'limit' in read_params:
        content = ''.join(f.readlines()[:read_params['limit']])
    else:
        content = f.read()

# Wrap ALL subprocess calls with timeout handling
# OLD: subprocess.run(cmd, capture_output=True, text=True)
# NEW:
attempt = 1
while attempt <= max_attempts:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        break
    except subprocess.TimeoutExpired:
        should_retry, delay = handle_timeout(operation_name, attempt)
        if should_retry: time.sleep(delay); attempt += 1; continue
        else: handle_final_timeout(); break

# Add size checking before large operations
# Before MultiEdit, large context operations, etc.
ok, message = check_request_size(tools, context)
if not ok: print(f"⚠️ {message}"); return

# Add performance monitoring
start_time = time.time()
# ... operation ...
duration = time.time() - start_time
optimizer.record_success(operation_type, int(duration * 1000), context_size)
```

### Phase 3: Testing Strategy
1. **Test each modified command** with known large operations
2. **Verify timeout handling** works correctly
3. **Ensure functionality preserved** while adding protection
4. **Monitor performance impact** of optimization overhead

## 📋 **Detailed Command Analysis**

### High-Risk Commands (Immediate Priority)

**`pr.py`**:
- Likely reads multiple files for PR creation
- Git operations that can timeout
- Potential large context when analyzing changes
- **Risk**: High - Core workflow command

**`push.py`**:
- Git push operations can timeout
- File status checking operations
- **Risk**: High - Critical deployment command

**`learn.py`**:
- File reading for learning capture
- Potential analysis of large codebases
- **Risk**: Medium - Analysis intensive

**`handoff.py`**:
- Code review and analysis operations
- Multi-file reading likely
- **Risk**: Medium - Analysis intensive

### Medium-Risk Commands

Any `.py` file that:
- Uses `subprocess.run()` without timeouts
- Reads files with `open()` without size limits
- Makes external API calls
- Uses `MultiEdit` with large operations
- Processes multiple files in loops

### Implementation Template

```python
#!/usr/bin/env python3
"""
[Command Name] with Timeout Mitigation
"""

import os
import sys
import time
import subprocess
from typing import Any, Dict, List, Optional

# UNIVERSAL TIMEOUT PROTECTION - Add to ALL commands
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
from request_optimizer import (
    optimize_file_read,
    optimize_multiedit,
    check_request_size,
    handle_timeout,
    optimizer
)

def protected_file_read(filepath: str) -> Optional[str]:
    """Read file with timeout protection"""
    read_params = optimize_file_read(filepath)
    try:
        with open(filepath, 'r') as f:
            if 'limit' in read_params:
                lines = f.readlines()[:read_params['limit']]
                content = ''.join(lines)
                if len(lines) >= read_params['limit']:
                    content += f"\n... [Truncated at {read_params['limit']} lines to prevent timeout]"
                return content
            else:
                return f.read()
    except Exception as e:
        return None

def protected_subprocess(cmd: List[str], operation_name: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run subprocess with timeout protection"""
    attempt = 1
    max_attempts = 3

    while attempt <= max_attempts:
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
        except subprocess.TimeoutExpired:
            should_retry, delay = handle_timeout(operation_name, attempt)
            if should_retry and attempt < max_attempts:
                print(f"⏱️ {operation_name} timeout (attempt {attempt}), retrying in {delay}s...")
                time.sleep(delay)
                attempt += 1
                continue
            else:
                raise
        except Exception:
            raise

def main():
    start_time = time.time()

    # Command logic here with protected operations

    # Performance monitoring
    duration = time.time() - start_time
    print(f"\n⏱️ Command completed in {duration:.1f}s")

    # Show optimization report if issues occurred
    opt_report = optimizer.get_optimization_report()
    if "No timeouts recorded" not in opt_report:
        print("\n📊 Performance Report:")
        print(opt_report)

if __name__ == "__main__":
    main()
```

## 🎯 **Success Metrics**

**Before Universal Implementation:**
- Timeout rate: ~60% for large operations
- Average retry attempts: 6+
- User frustration: High

**After Universal Implementation:**
- Timeout rate: <10% system-wide
- Average retry attempts: <2
- All commands have consistent timeout behavior
- No more endless retry cycles in ANY tool

## 🗓️ **Implementation Timeline**

**Week 1**: Audit all commands, categorize by risk level
**Week 2**: Implement protection for high-risk commands (pr.py, push.py, etc.)
**Week 3**: Apply template to medium-risk commands
**Week 4**: Testing, refinement, and performance validation

## 📝 **Notes**

- **Foundation is solid**: `request_optimizer.py` provides all necessary utilities
- **Pattern is proven**: Works well in the 3 commands already protected
- **Main work is systematic application**: Copy/paste the protection pattern to all commands
- **Low risk**: Adding protection shouldn't break existing functionality
- **High value**: Eliminates timeout frustration across entire system

**Next Action**: Choose a high-priority command (like `pr.py`) and apply the universal timeout protection pattern as a proof of concept.
