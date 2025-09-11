# PR #1514 Guidelines - Backup Fix: Restore and Optimize Memory Management

**PR**: #1514 - [Backup Fix: Restore and Optimize Memory Management](https://github.com/jleechanorg/worldarchitect.ai/pull/1514)
**Created**: September 10, 2025
**Purpose**: Guidelines for conditional import patterns and testing framework architecture

## Scope
This document contains PR-specific patterns, evidence, and decisions for PR #1514 addressing import dependency issues in testing framework.

## 🎯 PR-Specific Principles

### Conditional Import Architecture
- **Graceful Degradation**: Import failures should not prevent module loading
- **Lazy Loading**: Import dependencies only when actually needed, not at module level
- **Clean Fallbacks**: Provide stub implementations for missing dependencies
- **Path Safety**: sys.path modifications must be scoped and validated

### Testing Framework Design
- **Service Provider Pattern**: Clean abstraction between test implementations and service implementations
- **Dual-Mode Testing**: Support both mock and real service testing with runtime switching
- **Resource Cleanup**: All test providers must implement proper cleanup mechanisms

## 🚫 PR-Specific Anti-Patterns

### ❌ **Unconditional Module-Level Imports**
```python
# WRONG - Hard dependency at module level
import main
from database import Database
```

**Problem**: Creates hard dependencies that prevent module loading if imports fail

### ✅ **Conditional Import Within Functions**
```python
# CORRECT - Conditional import where needed
def create_test_app(self):
    try:
        import main
    except ImportError as e:
        raise ImportError(f"Failed to import main module: {e}")
    return main.create_app(testing=True)
```

### ❌ **sys.path After Imports**
```python
# WRONG - Path manipulation after imports
import unittest
from testing_framework.framework_core import TestingFramework

# Too late - imports already resolved
sys.path.insert(0, project_root)
```

### ✅ **sys.path Before Imports**
```python
# CORRECT - Path setup before imports
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now imports will work
from testing_framework.framework_core import TestingFramework
```

### ❌ **Global State Without Cleanup**
```python
# WRONG - Global state that persists across tests
_global_provider = SomeProvider()
```

**Problem**: Creates test isolation issues and resource leaks

### ✅ **Context Manager Pattern**
```python
# CORRECT - Scoped resource management
@contextmanager
def test_service_provider(mode="mock"):
    provider = get_service_provider(mode)
    try:
        yield provider
    finally:
        if hasattr(provider, 'cleanup'):
            provider.cleanup()
```

## 📋 Implementation Patterns for This PR

### Service Provider Architecture
```python
# Clean factory pattern with mode detection
def get_service_provider(mode="auto"):
    if mode == "auto":
        mode = "real" if os.getenv("TEST_REAL_MODE") == "1" else "mock"
    return _get_provider_class(mode)()
```

### Decorator-Based Test Configuration
```python
# Composable test decorators
@dual_mode_test
@skip_in_real_mode("Uses hardcoded test data")
def test_something(self):
    pass
```

### Import Error Handling
```python
# Graceful import with specific error messages
try:
    from ..test_integration.integration_test_lib import IntegrationTestSetup
except ImportError:
    class IntegrationTestSetup:  # Fallback stub
        def __init__(self):
            self.setup_complete = False
```

## 🔧 Specific Implementation Guidelines

### sys.path Manipulation Security
1. **Timing is Critical**: Always modify sys.path BEFORE any imports that depend on it
2. **Path Validation**: Only add absolute, read-only paths to sys.path
3. **Scope Limitation**: Consider using context managers for temporary path modifications
4. **Logging**: Log sys.path modifications for debugging and security auditing

### Conditional Import Best Practices
1. **Function-Level Imports**: Move imports into functions where they're actually needed
2. **Specific Error Handling**: Provide meaningful error messages for import failures
3. **Fallback Implementations**: Create stub classes for optional dependencies
4. **Module Loading Validation**: Test all import paths and failure scenarios

### Testing Framework Patterns
1. **Provider Abstraction**: Use factory pattern for service provider instantiation
2. **Mode Detection**: Environment variable-based mode switching (TEST_REAL_MODE)
3. **Resource Cleanup**: Implement cleanup methods for all providers
4. **Test Isolation**: Avoid global state that persists across test runs

## 🔒 Security Considerations

### Import Security
- **Path Traversal**: Validate all sys.path additions to prevent malicious module loading
- **Module Validation**: Whitelist allowed modules for dynamic imports
- **Environment Isolation**: Ensure test-mode changes don't affect production imports

### Runtime Safety
- **Exception Handling**: All conditional imports must handle ImportError gracefully
- **Fallback Security**: Stub implementations should fail safely if misused
- **Resource Leaks**: Clean up all providers to prevent resource exhaustion

---

**Status**: Production-ready - Import dependency issues resolved with clean architecture
**Last Updated**: September 10, 2025
**Commit**: 8ff5cca1 - Fixed unconditional imports and sys.path timing issues
