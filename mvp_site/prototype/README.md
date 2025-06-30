# Prototype Tests

This directory contains all tests related to the validation prototype system.

## Test Files

- `test_word_boundary_bug.py` - Tests for word boundary matching fix
- `test_word_boundary_runner.py` - Runner for word boundary tests from project root
- `test_prototype_integration.py` - Integration tests for validation system
- `test_prototype_simple.py` - Simple direct tests of validators
- `test_prototype_validation.py` - Comprehensive validation tests
- `run_all_tests.py` - Runs all prototype tests
- `run_full_integration_tests.py` - Runs integration test suite

## Running Tests

These tests need to be run from the project root (not from mvp_site) due to import paths:

```bash
# From project root
python3 mvp_site/prototype/test_word_boundary_runner.py
python3 mvp_site/prototype/run_all_tests.py
```

## Note

These tests are for the validation prototype in `/prototype/`. They are kept separate from the main mvp_site tests because they test experimental functionality not yet integrated into the main application.