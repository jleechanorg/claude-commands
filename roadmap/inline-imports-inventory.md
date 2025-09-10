# Inline Import Inventory - Codebase Wide Analysis

**Generated**: 2025-09-09
**Analysis Scope**: Entire codebase excluding `mvp_site/` (already cleaned in Phases 1-4)

## Summary Statistics

- **Total Files with Inline Imports**: 35 files
- **Total Directories Affected**: 13 directories
- **Estimated Cleanup Effort**: 12-17 hours across 3-4 phases

## Directory Breakdown (by file count)

| Directory | File Count | Priority | Notes |
|-----------|------------|----------|-------|
| `.claude/scripts/` | 4 | HIGH | Core infrastructure scripts |
| `scripts/` | 4 | HIGH | Utility and analysis scripts |
| `.claude/commands/` | 4 | HIGH | Command system core |
| `testing_mcp/utils/` | 2 | MEDIUM | Test infrastructure utilities |
| `orchestration/` | 2 | MEDIUM | Agent orchestration system |
| `archive/experimental_testing/.../utils/` | 2 | LOW | Archived experimental code |
| `.claude/hooks/tests/` | 2 | MEDIUM | Hook testing infrastructure |
| `.claude/commands/tests/` | 2 | MEDIUM | Command testing |
| `.claude/commands/lib/` | 2 | HIGH | Shared command libraries |
| `.claude/commands/_copilot_modules/` | 2 | HIGH | Copilot system modules |
| `testing_mcp/performance/` | 1 | MEDIUM | Performance testing |
| `testing_mcp/integration/` | 1 | MEDIUM | Integration testing |
| `testing_mcp/deployment/` | 1 | MEDIUM | Deployment testing |
| `mcp_servers/slash_commands/tests/` | 1 | MEDIUM | MCP server tests |
| `mcp_servers/slash_commands/` | 1 | HIGH | MCP server implementation |
| `archive/experimental_testing/.../performance/` | 1 | LOW | Archived performance tests |
| `archive/experimental_testing/.../integration/` | 1 | LOW | Archived integration tests |
| `archive/experimental_testing/.../deployment/` | 1 | LOW | Archived deployment tests |
| `.claude/hooks/` | 1 | HIGH | Core hook implementation |

## Priority Classification

### HIGH Priority (15 files) - Core Production Code
**Impact**: Direct effect on system functionality and user workflows
- `.claude/commands/` directory (6 files)
- `scripts/` directory (4 files)
- `.claude/scripts/` directory (4 files)
- `.claude/hooks/` (1 file)

### MEDIUM Priority (13 files) - Test & Infrastructure
**Impact**: Affects testing reliability and development workflows
- `testing_mcp/` directory (5 files)
- `.claude/commands/tests/` (2 files)
- `.claude/hooks/tests/` (2 files)
- `orchestration/` (2 files)
- `mcp_servers/` (2 files)

### LOW Priority (7 files) - Archived Code
**Impact**: Minimal to no production impact
- `archive/experimental_testing/` directory (7 files)

## Common Inline Import Patterns Found

### Pattern 1: Performance-Critical Imports
```python
# scripts/memory_backup_crdt.py
def backup_function():
    import psutil  # Should be module-level for performance
```

### Pattern 2: Optional Dependencies
```python
# testing_mcp/deployment/health_checks.py
def check_redis():
    import redis  # May be intentionally optional
```

### Pattern 3: System Utilities
```python
# .claude/commands/exportcommands.py
def file_operation():
    import shutil  # Standard library, should be top-level
```

### Pattern 4: Test Isolation
```python
# .claude/hooks/tests/hook_test_green.py
def test_database():
    import psycopg2  # May be intentional test isolation
```

## Cleanup Strategy Summary

1. **Phase 5A**: High-priority infrastructure files (Week 1, 4-6 hours)
2. **Phase 5B**: Test infrastructure assessment (Week 2, 6-8 hours)
3. **Phase 5C**: MCP server evaluation (Week 3, 2-3 hours)
4. **Phase 5D**: Archive cleanup (Optional, 2-4 hours or deletion)

## Tools Available

- `scripts/detect_inline_imports.py` - Existing detection tool
- `scripts/validate_imports_delta.sh` - Pre-commit validation
- `/fake3` command - Placeholder code detection

## Expected Outcome

- **Before**: 35 files with inline imports across codebase
- **After**: ~7 files with documented legitimate inline imports
- **Reduction**: ~80% cleanup rate while preserving intentional patterns

---

**Status**: Planning complete, ready for implementation
**Next Step**: Begin Phase 5A with core infrastructure cleanup
**Dependencies**: MVP development priorities, testing environment availability
