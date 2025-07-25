# Sariel Test Suite Consolidation

## Overview
The Sariel test suite was consolidated from 7 redundant test files into 3 focused tests to reduce API calls and improve maintainability.

## Consolidated Tests

### 1. `test_sariel_consolidated.py` (Main Test)
**Replaces**:
- `test_sariel_single_campaign_full.py`
- `test_sariel_with_prompts.py`
- `test_sariel_production_validation.py`

**Features**:
- Configurable via environment variables:
  - `SARIEL_DEBUG_PROMPTS=true` - Enable prompt logging
  - `SARIEL_FULL_TEST=true` - Run 10 interactions (default: 3)
  - `SARIEL_REPLAYS=5` - Run 5 campaigns (default: 1)
- Comprehensive entity tracking validation
- Game state field counting
- Detailed results export in debug mode

**Usage**:
```bash
# Quick test (3 interactions)
TESTING=true vpython -m unittest tests.test_sariel_consolidated

# Full test with debug
SARIEL_FULL_TEST=true SARIEL_DEBUG_PROMPTS=true TESTING=true vpython -m unittest tests.test_sariel_consolidated

# Multiple replays
SARIEL_REPLAYS=10 TESTING=true vpython -m unittest tests.test_sariel_consolidated
```

### 2. `test_sariel_production_methods.py`
**Unique Value**: Tests `get_initial_story` and `continue_story` methods directly

**Features**:
- Direct method testing without API layer
- Focused on entity tracking in production flow
- Minimal API calls (2-3 total)

### 3. `test_sariel_entity_debug.py` (Keep Original)
**Unique Value**: Specialized debugging for entity disappearance issues

**Features**:
- Prompt interception
- Detailed debugging output
- Minimal API calls (2 total)

## Deprecated Tests
The following tests should be removed or moved to a manual test suite:

1. **Remove** (redundant with consolidated test):
   - `test_sariel_single_campaign_full.py`
   - `test_sariel_with_prompts.py`
   - `test_sariel_production_validation.py`

2. **Move to manual/benchmark suite**:
   - `test_sariel_full_validation.py` (60 API calls - too expensive for regular CI)
   - `test_sariel_exact_production.py` (specialized auto-choice logic)

## API Call Reduction

| Test File | Before | After | Savings |
|-----------|--------|-------|---------|
| Regular test run | 11-60 calls | 3 calls | 73-95% |
| Full test run | 60+ calls | 10 calls | 83% |
| Debug session | 22+ calls | 2-10 calls | 55-91% |

## Migration Guide

1. **For basic testing**: Use `test_sariel_consolidated.py` with default settings
2. **For debugging entity issues**: Use `test_sariel_entity_debug.py`
3. **For testing production methods**: Use `test_sariel_production_methods.py`
4. **For benchmarking**: Use environment variables on consolidated test

## Benefits

1. **Reduced API costs**: 73-95% fewer API calls in typical usage
2. **Faster test execution**: 3-10 API calls vs 11-60
3. **Better maintainability**: 3 focused tests vs 7 overlapping ones
4. **Configurable depth**: Run quick or comprehensive tests as needed
5. **Clearer purpose**: Each test has a specific, non-overlapping goal
