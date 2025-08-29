# Roadmap Tests Fix Plan
**Created**: 2025-08-27  
**Context**: Continuing test fixes from previous session - roadmap directory tests failing

## Current Status Summary
- ✅ Fixed external dependency issues (venv tests filtered out)  
- ✅ Fixed Cerebras command test failures (echo statements, input validation)
- ✅ Fixed MVP site integration authentication headers
- ✅ Installed redis dependency for orchestration tests
- ⚠️ Orchestration tests partially working (some import/fixture issues remain)
- 🔄 **Next Focus**: roadmap/ directory tests

## Roadmap Test Analysis

### 1. Test Files Identified
```
roadmap/tests/test_ai_content_personalization_fix.py
roadmap/tests/test_firebase_authentication_fix.py  
roadmap/cognitive_enhancement/test_framework.py
roadmap/command_comp_data/test_case_debugging_task.py
roadmap/command_comp_data/test_case_group_b_solution.py
```

### 2. Primary Issues Found

#### A. Module Import Failures
**Problem**: `ModuleNotFoundError: No module named 'world_logic'`
- **File**: `test_ai_content_personalization_fix.py` line 17
- **Root Cause**: Test tries to import from `world_logic` but path setup is incorrect
- **Current Import**: `from world_logic import create_campaign_unified`  
- **Path Addition**: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mvp_site'))`

#### B. Import Path Resolution Issues  
**Problem**: Tests in roadmap/ directory cannot find mvp_site modules
- **Symptom**: Path calculations assume mvp_site is relative to test file
- **Reality**: mvp_site is at project root level, not inside roadmap/tests/

#### C. Service Integration Dependencies
**Problem**: Tests expect running services (frontend/backend)
- **test_firebase_authentication_fix.py**: Expects localhost:3002, localhost:5005
- **Integration Level**: End-to-end tests requiring full stack

## Step-by-Step Fix Plan

### Phase 1: Fix Module Import Paths (30 minutes)

#### Step 1.1: Fix test_ai_content_personalization_fix.py
```python
# CURRENT (incorrect):
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mvp_site'))

# FIX TO:
import os
import sys
# Get project root - go up from roadmap/tests/ to project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
mvp_site_path = os.path.join(project_root, 'mvp_site')
sys.path.insert(0, mvp_site_path)
sys.path.insert(0, project_root)
```

#### Step 1.2: Verify world_logic module exists
- **Location Check**: Confirm `mvp_site/world_logic.py` or `mvp_site/world_logic/__init__.py` exists
- **Function Check**: Verify `create_campaign_unified` function exists in world_logic
- **Action**: Update import statement if function name/location has changed

#### Step 1.3: Fix other roadmap test imports
- Apply same path fix pattern to all roadmap test files
- Add project root and mvp_site to Python path consistently

### Phase 2: Fix Integration Test Dependencies (45 minutes)

#### Step 2.1: Mock External Service Dependencies
**For test_firebase_authentication_fix.py**:
- Mock HTTP requests to localhost:3002, localhost:5005  
- Use `requests-mock` or `unittest.mock` to simulate service responses
- Convert end-to-end test to integration test with mocked backends

#### Step 2.2: Environment Variable Setup
```python
# Add to all roadmap tests:
os.environ["TESTING"] = "true"
os.environ["MOCK_SERVICES_MODE"] = "true"
os.environ["TEST_MODE"] = "mock"
```

#### Step 2.3: Test Data Isolation
- Ensure tests use temporary directories for any file operations
- Mock Firebase/Firestore calls to avoid external dependencies
- Use in-memory data structures instead of persistent storage

### Phase 3: Fix Cognitive Enhancement Tests (20 minutes)

#### Step 3.1: Fix test_framework.py imports
- Same path resolution fixes as above
- Verify all local imports resolve correctly:
  ```python
  from enhanced_learn import EnhancedLearner, LearningPattern
  from memory_integration import ConversationMemoryManager  
  from query_patterns import PatternQueryEngine
  ```

#### Step 3.2: Temporary directory cleanup
- Ensure `tempfile.mkdtemp()` directories are properly cleaned up
- Add proper exception handling with cleanup in finally blocks

### Phase 4: Fix Command Composition Data Tests (15 minutes)

#### Step 4.1: Update test file permissions/setup
- Verify test files in `command_comp_data/` are properly structured
- Fix any import issues similar to other roadmap tests

#### Step 4.2: Data dependency validation  
- Ensure test data files exist and are accessible
- Mock any external data sources

### Phase 5: Test Execution & Validation (30 minutes)

#### Step 5.1: Run individual test files
```bash
# Test each file individually to isolate issues:
TESTING=true python3 -m pytest roadmap/tests/test_ai_content_personalization_fix.py -v
TESTING=true python3 -m pytest roadmap/tests/test_firebase_authentication_fix.py -v  
TESTING=true python3 -m pytest roadmap/cognitive_enhancement/test_framework.py -v
TESTING=true python3 -m pytest roadmap/command_comp_data/ -v
```

#### Step 5.2: Run full roadmap test suite
```bash
# After individual fixes, run complete roadmap tests:
TESTING=true python3 -m pytest roadmap/ -v --tb=short
```

#### Step 5.3: Update run_tests.sh integration
- Ensure roadmap tests are included in main test runner
- Add any necessary exclusions for tests requiring manual setup

## Implementation Commands

### Quick Start Commands (copy-paste ready):
```bash
# 1. Navigate to project and activate environment  
cd /Users/jleechan/projects/worldarchitect.ai/worktree_tests2

# 2. Test current roadmap failures
TESTING=true python3 -m pytest roadmap/ -v --tb=short | head -50

# 3. Fix the main import issue first
# Edit roadmap/tests/test_ai_content_personalization_fix.py
# Replace lines 8-10 with proper path resolution

# 4. Test the fix  
TESTING=true python3 -m pytest roadmap/tests/test_ai_content_personalization_fix.py -v

# 5. Apply same pattern to other test files
# Continue with test_firebase_authentication_fix.py, etc.
```

## Success Criteria
- [ ] All roadmap test files run without import errors
- [ ] Tests pass with proper mocking of external dependencies  
- [ ] Integration with main test suite (`./run_tests.sh`) works
- [ ] No remaining "ModuleNotFoundError" issues in roadmap/

## Time Estimate
**Total**: ~2.5 hours
- Path fixes: 30 min
- Service mocking: 45 min  
- Cognitive tests: 20 min
- Command data tests: 15 min
- Validation: 30 min
- Buffer: 20 min

## Follow-up Tasks
1. Add roadmap tests to CI pipeline
2. Consider converting end-to-end tests to proper integration test suite
3. Document roadmap test structure for future development

---
**Note**: This plan assumes the main test framework fixes from the previous session (venv exclusion, Cerebras fixes, etc.) are already in place.