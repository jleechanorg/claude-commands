# PR #1599 Guidelines - Fix CI test hangs: Add 45-minute memory monitor timeout

> This supplements docs/pr-guidelines/README.md; authoritative rules live there.

## 🎯 PR-Specific Principles

### **Infrastructure Reliability First**
- **Timeout Protection**: Multi-layer timeout strategy preventing infinite hangs at CI job, step, and subprocess levels
- **Resource Management**: Proper async context lifecycle management to prevent resource leaks
- **Security Hardening**: Comprehensive subprocess security with `shell=False, timeout=30` pattern

### **Technical Debt Reduction Excellence**
- **Code Consolidation**: Significant reduction through elimination of duplicate functionality
- **File Organization**: Strategic removal of redundant implementations
- **Security Standardization**: Consistent application of security patterns across codebase

## 🚫 PR-Specific Anti-Patterns

### ❌ **Timeout Configuration Mismatch**
**Problem Found**: CI job timeout (15 min) matching step timeout (15 min)
```yaml
# WRONG - Timeout mismatch creates race condition
jobs:
  test:
    timeout-minutes: 15  # Job level
    steps:
    - name: Run tests
      timeout-minutes: 15  # Step level - same as job!
```

**Impact**: Steps could timeout before job cleanup, leaving orphaned processes

### ✅ **Correct Timeout Hierarchy**
```yaml
# RIGHT - Proper timeout cascade
jobs:
  test:
    timeout-minutes: 60  # Job level - buffer above step (monitor=45 -> step=50 -> job=60)
    steps:
    - name: Run tests
      timeout-minutes: 50  # Step level - must exceed 45-min monitor with buffer
```

### ❌ **Async Resource Leak Pattern**
**Problem Found**: Multiple HTTP clients without proper cleanup
```python
# WRONG - Resource leak risk
async def test_function():
    client1 = httpx.AsyncClient()
    client2 = httpx.AsyncClient()
    # No cleanup - connection pool exhaustion
```

### ✅ **Proper Async Context Management**
```python
# RIGHT - Proper resource lifecycle
async def test_function():
    async with httpx.AsyncClient() as client1:
        async with httpx.AsyncClient() as client2:
            # Automatic cleanup on context exit
```

### ❌ **Security Pattern Inconsistency**
**Problem Found**: Mixed subprocess security patterns
```python
# WRONG - Inconsistent security
subprocess.run(cmd)  # Missing security parameters
subprocess.run(cmd, timeout=30)  # Partial security
subprocess.run(cmd, shell=False, timeout=30, check=True)  # Complete security
```

### ✅ **Comprehensive Security Standard**
```python
# RIGHT - Consistent security pattern
subprocess.run(
    cmd,
    shell=False,      # Prevent injection
    timeout=30,       # Prevent DoS
    check=True,       # Explicit error handling
    capture_output=True  # Secure output capture
)
```

**Additional Security Guidelines**:
- Prefer argv lists: cmd = ["git", "diff", "--name-only"] (never strings).
- Pass env={...} explicitly when needed; avoid inheriting sensitive vars.
- Log sanitized command and duration; never log secrets or full stdout on failure.

## 📋 Implementation Patterns for This PR

### **Multi-Layer Timeout Strategy**
1. **System Level**: 45-minute memory monitor timeout for long-running operations
2. **CI Job Level**: 15-20 minute job execution limits
3. **CI Step Level**: 15-minute individual step timeouts
4. **Subprocess Level**: 30-300 second operation-specific timeouts
5. **Dependency Install**: 300-600 second package installation timeouts

#### Reference: Memory monitor snippets (recommended)

Python:
```python
import os, sys, time
max_monitor_time = 2700  # 45 minutes
cleanup_file = os.environ.get("CLEANUP_FILE", "/tmp/cleanup.done")
start = time.monotonic()
while not os.path.exists(cleanup_file) and (time.monotonic() - start) < max_monitor_time:
    time.sleep(6)
if not os.path.exists(cleanup_file):
    print("Monitor timeout reached (45m); exiting status 2", file=sys.stderr)
    raise SystemExit(2)
```

Bash:
```bash
set -euo pipefail
: "${CLEANUP_FILE:=/tmp/cleanup.done}"
max_monitor_time=2700  # 45 minutes
SECONDS=0  # bash monotonic counter
while [ ! -f "$CLEANUP_FILE" ] && [ "$SECONDS" -lt "$max_monitor_time" ]; do
  sleep 6
done
if [ ! -f "$CLEANUP_FILE" ]; then
  printf '%s\n' "Monitor timeout reached (45m); exiting status 2" >&2
  exit 2
fi
```

### **Security Hardening Approach**
1. **Subprocess Security**: Universal `shell=False, timeout=N` pattern
2. **SHA-Pinned Actions**: Commit hash pins prevent supply chain attacks
3. **Resource Protection**: Async context managers for all external clients
4. **Error Handling**: Explicit exception handling with proper cleanup

### **Code Consolidation Strategy**
1. **Duplicate Elimination**: Remove redundant memory backup scripts (11 files → unified system)
2. **Pattern Standardization**: Apply consistent patterns across similar functionality
3. **Configuration Consolidation**: Reduce configuration sprawl through centralization
4. **Test Organization**: Strategic test file organization and categorization

**Reference Implementation Examples**:
- Reference script: scripts/run_tests.sh (memory monitor section).
- Subprocess hardening example: scripts/memory_sync/backup_memory_enhanced.py (TIMEOUT_SEC, TimeoutExpired handling).
- Tests validating monitor behavior: scripts/tests/test_unified_memory_backup.py.

## 🔧 Specific Implementation Guidelines

### **CI Timeout Configuration**
- **Job Timeout**: Set ≥10-minute buffer above step timeout for cleanup (e.g., step=50 → job=60)
- **Step Timeout**: Set ≥5-minute buffer above monitor timeout (e.g., monitor=45 → step=50)
- **Subprocess Timeout**: 30 seconds for quick operations, 300+ for complex operations
- **Dependency Install**: 300-600 seconds based on package complexity

**Follow-ups Checklist**:
- [ ] Set step timeout to 50m and job timeout to 60m in .github/workflows/test.yml.
- [ ] Confirm org‑level job timeout isn't overriding repo settings.
- [ ] Document where to change these in GitHub UI if managed centrally.

### **Async Resource Management**
- **Always use context managers** for HTTP clients, file operations, database connections
- **Implement proper cleanup** in finally blocks and exception handlers
- **Monitor resource usage** in long-running operations
- **Test resource cleanup** with explicit leak detection

### **Security Implementation**
- **Apply subprocess security** universally across all script files
- **Use SHA-pinned Actions** for all GitHub workflow dependencies
- **Implement timeout protection** for all external operations
- Prioritize concrete, validated risks and document trade‑offs explicitly

### **Code Quality Gates**
- Significant code reduction demonstrates successful consolidation approach
- **Zero test failures** requirement maintained through comprehensive testing
- **Security pattern consistency** applied across entire codebase
- **Performance optimization** through intelligent resource usage

## 🎯 Success Metrics for This PR Type

### **Infrastructure Reliability**
- ✅ **Eliminates known infinite hang class**: Multi-layer timeout protection prevents CI failures; residual risks are monitored. Track with CI job max duration SLO and alert if exceeded.
- ✅ **Resource leak prevention**: Proper async context management
- ✅ **Security hardening**: Universal subprocess security implementation
- ✅ **Performance**: Reduced code surface area via consolidation

### **Technical Debt Reduction**
- ✅ **Duplicate elimination**: 11 redundant scripts consolidated
- ✅ **Pattern standardization**: Consistent security and timeout patterns
- ✅ **Configuration optimization**: Streamlined CI configuration
- ✅ **Test infrastructure**: Maintained 100% test pass rate

### **Security Enhancement**
- ✅ **Command injection prevention**: Complete subprocess security
- ✅ **DoS attack mitigation**: Comprehensive timeout protection
- ✅ **Supply chain security**: SHA-pinned GitHub Actions
- ✅ **Resource exhaustion prevention**: Proper async lifecycle management

## 🔄 Future PR Considerations

### **Based on This PR's Success**
1. **Apply multi-layer timeout strategy** to other infrastructure components
2. **Extend consolidation approach** to other areas with duplicate functionality
3. **Implement async context patterns** consistently across async operations
4. **Use SHA-pinning strategy** for all external dependencies

### **Lessons Learned**
1. **Infrastructure optimization** can achieve significant code reduction while improving reliability
2. **Security pattern consistency** prevents vulnerability introduction through partial implementation
3. **Timeout hierarchy** requires careful consideration of cleanup requirements
4. **Solo developer security focus** balances real protection with development velocity

---

**Updated:** 2025-09-12 — via comprehensive multi-perspective review
**Evidence**: PR #1599 analysis (files changed and LOC deltas per current PR diff)
**Review Type**: Solo Developer Security Focus with Enterprise Paranoia Filtering
