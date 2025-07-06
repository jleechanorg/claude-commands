# Test Scripts

This directory contains various test scripts for browser and integration testing.

## Categories

### Combat Testing
- `capture_combat_error.py` - Captures combat-related errors
- `test_combat_bug_directly.py` - Direct combat bug testing
- `test_combat_bug_final.py` - Final combat bug verification
- `complete_combat_test.py` - Comprehensive combat testing
- `trigger_combat_error.py` - Triggers specific combat errors

### Authentication Testing
- `real_test_with_auth_working.py` - Working authentication test
- `test_with_auth_enabled.py` - Tests with auth enabled

### General Testing
- `check_500_error.py` - Checks for 500 server errors
- `comprehensive_real_test.py` - Comprehensive browser test
- `final_working_test.py` - Final working test case
- `test_with_debug_server.py` - Tests using debug server
- `run_real_integration_test.py` - Runs real integration tests

### Task-Specific Tests (Task 091)
- `task_091_backend_test.py` - Backend functionality test
- `task_091_simple_test.py` - Simple test case
- `task_091_unchecked_checkboxes_test.py` - UI checkbox testing

## Usage

These scripts are standalone test files that can be run directly:
```bash
python3 test_scripts/script_name.py
```

Most require a test server to be running on port 8086.