# PR #1382 Guidelines - Improvement/type safety foundation

**PR**: #1382 - [Improvement/type safety foundation](https://github.com/jleechanorg/worldarchitect.ai/pull/1382)
**Created**: August 18, 2025
**Purpose**: Specific guidelines for type safety foundation development and review

## Scope
- This document contains PR-specific deltas, evidence, and decisions for PR #1382.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### Type Safety Foundation Focus
- **Python 3.9+ Compatibility**: Ensure all isinstance syntax works across CI environments
- **Real Flask Testing**: Replace mock testing with actual Flask application validation
- **Firebase Config Detection**: Use canonical property names (apiKey, authDomain, projectId)
- **CI Environment Robustness**: Handle import path differences between local and CI

### Test Quality Standards
- Replace MockApiService fake implementations with real Flask test_client testing
- Use proper HTTP status assertions instead of NotImplementedError in tests
- Move all imports to module level for better structure
- Ensure tests validate actual functionality, not fake implementations

## 🚫 PR-Specific Anti-Patterns

### Syntax Compatibility Issues
- ❌ **PEP 604 Union Syntax**: Using `isinstance(data, list | dict)` - incompatible with Python 3.9
- ✅ **Tuple Syntax**: Use `isinstance(data, (list, dict))` for backward compatibility
- ❌ **Inline Imports**: Importing modules inside test methods
- ✅ **Module-Level Imports**: All imports at top of file

### Test Implementation Problems
- ❌ **MockApiService Testing**: Testing fake local stub instead of real Flask app
- ✅ **Real Flask Testing**: Using test_client fixture for actual HTTP validation
- ❌ **False Firebase Detection**: Searching lowercase env vars against original JS
- ✅ **Canonical Property Search**: Using regex with proper Firebase property names

### CI Environment Issues
- ❌ **Import Path Assumptions**: Hardcoded import paths that break in CI
- ✅ **Robust Import Handling**: Try/catch with sys.path manipulation for environment differences

## 📋 Implementation Patterns for This PR

### Python Compatibility Pattern
```python
# ❌ Python 3.10+ only
isinstance(data, list | dict)

# ✅ Python 3.9+ compatible  
isinstance(data, (list, dict))
```

### Real Flask Testing Pattern
```python
# ❌ Testing fake implementation
class MockApiService:
    def get_health_status():
        raise NotImplementedError()

# ✅ Testing real Flask app
def test_health_endpoint(client):
    response = client.get('/api/health')
    assert response.status_code == 200
```

### Firebase Config Detection Pattern
```python
# ❌ False negatives
if var_name.replace('FIREBASE_', '').lower() in js_content:

# ✅ Canonical property detection
prop_map = {
    'FIREBASE_API_KEY': 'apiKey',
    'FIREBASE_AUTH_DOMAIN': 'authDomain',
    'FIREBASE_PROJECT_ID': 'projectId'
}
has_config = any(re.search(rf'\b{re.escape(prop)}\b', js_content) 
                for prop in prop_map.values())
```

## 🔧 Specific Implementation Guidelines

### Code Review Focus Areas
1. **Python Syntax**: Check all isinstance calls for PEP 604 compatibility
2. **Test Implementations**: Verify tests use real Flask app, not mock implementations
3. **Import Structure**: Ensure all imports are at module level
4. **CI Compatibility**: Verify robust import handling for different environments

### Testing Requirements
- All tests must pass in both local and CI environments
- No fake implementations or placeholder code
- Real HTTP status code validation instead of exception testing
- Proper Firebase configuration detection using canonical properties

### Performance Considerations
- Use Cerebras for well-defined test generation with clear specifications
- Apply tool selection hierarchy: Serena MCP → Read tool → Bash commands
- Implement targeted fixes rather than bulk operations

---
**Status**: Template created by /guidelines command - enhanced with type safety foundation patterns
**Last Updated**: August 18, 2025