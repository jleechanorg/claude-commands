# Test Skip Policy - Middle Ground Approach

## Overview
This policy distinguishes between legitimate environmental skips and inappropriate lazy skips, providing clear guidelines for when and how to use test skipping mechanisms.

## ✅ LEGITIMATE Skip Patterns

### Environmental Unavailability
**When to use**: External dependencies, credentials, or system resources are legitimately unavailable

**Approved patterns**:
```python
# Pattern 1: Missing optional dependencies
if not os.path.exists(font_path):
    self.skipTest(f"Font file not found at {font_path}, skipping PDF generation test")

# Pattern 2: Missing system utilities  
if not shutil.which("git"):
    self.skipTest("Git not available, skipping git-dependent test")

# Pattern 3: Missing credentials/permissions
if not has_firebase_credentials():
    self.skipTest("Firebase credentials not available, skipping integration test")

# Pattern 4: Environment-specific features
if os.environ.get("CI") == "true":
    self.skipTest("Integration tests disabled in CI environment")
```

**Key characteristics**:
- Checks for external dependencies that may legitimately be missing
- Uses `self.skipTest()` method (not `self.fail()`)
- Provides clear reason for skipping
- Cannot be easily mocked or worked around

### CI Environment Limitations
**When to use**: Tests require resources not available in CI (databases, external APIs, etc.)

**Approved patterns**:
```python
# In workflow files
if [[ "$test_file" == *"test_integration"* ]]; then
    echo "Skipping integration test: $test_file"
    continue
fi

# In test code
@unittest.skipIf(os.environ.get("CI") == "true", "Integration test disabled in CI")
def test_external_api_integration(self):
    # Test that requires external API
```

## ❌ FORBIDDEN Skip Patterns

### Lazy Implementation Avoidance
**Never use skips for**:
- Tests that could be fixed with proper mocking
- Tests that fail due to implementation bugs
- Tests that are "too hard" to set up properly
- Tests that depend on internal application state

**Forbidden patterns**:
```python
# ❌ BAD - Can be mocked
self.skipTest("Firebase not configured") # Use mock instead

# ❌ BAD - Should be fixed
self.skipTest("This test sometimes fails") # Fix the test

# ❌ BAD - Can be isolated
self.skipTest("Database not set up") # Use test database
```

### Module Import Issues
**Never skip for**:
- Missing internal modules (indicates broken imports)
- Dependency resolution issues (fix requirements.txt)
- Path configuration problems (fix PYTHONPATH)

## 🔧 REQUIRED Fixes for Current Violations

### Replace `self.fail()` with `self.skipTest()`
Current problematic patterns that need fixing:

```python
# ❌ CURRENT (causes test failure)
self.fail("Font file not found - skipping PDF generation test")

# ✅ FIXED (proper skip)
self.skipTest("Font file not found, skipping PDF generation test")
```

**Files requiring fixes**:
1. `mvp_site/tests/test_generator_isolated.py:69`
2. `mvp_site/tests/test_infrastructure.py:161` 
3. `mvp_site/tests/test_infrastructure.py:210`

### Consolidation Rules
- **One skip check per environmental concern**
- **Skip at test method level, not within test logic**
- **Clear, actionable skip messages**
- **Document skip rationale in test docstrings**

## 🛠️ Implementation Guidelines

### Skip Message Format
```python
self.skipTest("RESOURCE not available: SPECIFIC_REASON, skipping TEST_PURPOSE")
```

Examples:
- `"Git not available: command not found, skipping branch detection test"`
- `"Font file missing: /path/to/font.ttf not found, skipping PDF generation test"`
- `"Firebase credentials unavailable: no auth configured, skipping integration test"`

### Function-Level Skips vs Method-Level Skips
```python
# Preferred: Method-level decorator
@unittest.skipUnless(has_docker(), "Docker required for container tests")
def test_docker_integration(self):
    pass

# Alternative: Early return in setUp
def setUp(self):
    if not has_required_credentials():
        self.skipTest("Credentials required for this test suite")
```

## 📊 Enforcement

### Automated Detection
The enforcement script will flag:
1. Use of `self.fail()` with "skip" in the message
2. Skip patterns that could be mocked instead
3. Missing skip documentation in test docstrings
4. Inconsistent skip message formats

### Code Review Checklist
- [ ] Skip reason is environmental, not implementation laziness
- [ ] Skip could not be reasonably replaced with mocking
- [ ] Skip message clearly identifies missing resource
- [ ] Skip uses proper `self.skipTest()` method
- [ ] Test docstring documents skip conditions

## 📈 Success Metrics
- **Zero tolerance for lazy skips** (implementation avoidance)
- **Environmental skips properly implemented** (don't fail, properly skip)  
- **Clear documentation** of all skip conditions
- **Consistent skip message formatting**

This policy allows necessary environmental skips while eliminating inappropriate lazy implementation avoidance patterns.