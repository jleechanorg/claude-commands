# Manual Tests

This directory contains tests that make extensive API calls and should only be run manually when needed.

## Running Manual Tests

There are several ways to run these tests:

### Method 1: Using the run_manual_test.py script (Recommended)
```bash
cd mvp_site
TESTING=true python run_manual_test.py tests/manual_tests/test_sariel_exact_production.py
```

### Method 2: As Python modules
```bash
cd mvp_site
TESTING=true python -m tests.manual_tests.test_sariel_exact_production
```

### Method 3: Using vpython (legacy)
```bash
cd mvp_site
TESTING=true vpython tests/manual_tests/test_sariel_exact_production.py
```

## Tests in this directory:

### test_sariel_full_validation.py
- **API Calls**: 110 (10 complete campaigns × 11 calls each)
- **Purpose**: Statistical validation across multiple campaign runs
- **When to run**: Before major releases or when validating entity tracking improvements
- **Command**: `cd mvp_site && TESTING=true vpython tests/manual_tests/test_sariel_full_validation.py`

### test_sariel_exact_production.py  
- **API Calls**: ~15-20
- **Purpose**: Tests exact production flow with auto-selection of choices
- **When to run**: When debugging specific production scenarios
- **Command**: `cd mvp_site && TESTING=true vpython tests/manual_tests/test_sariel_exact_production.py`

## Why these are manual:

These tests were moved from the regular test suite because:
1. They make many API calls which costs money
2. They take a long time to run (several minutes)
3. They're not needed for regular development iterations
4. Their functionality is partially covered by the consolidated tests

## Regular test alternatives:

For regular testing, use:
- `test_sariel_consolidated.py` - Default 3 interactions, configurable up to 10
- `test_sariel_production_methods.py` - Direct method testing
- `test_sariel_entity_debug.py` - Debugging entity tracking issues