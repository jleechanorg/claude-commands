# API Test Consolidation Summary

## Completed Actions

### 1. Removed Redundant Tests (saved ~108 API calls)
- ✅ `test_sariel_single_campaign_full.py` - 21 API calls
- ✅ `test_sariel_with_prompts.py` - 11 API calls
- ✅ `test_sariel_production_validation.py` - 8 API calls
- ✅ `test_sariel_production_flow.py` - 10 API calls

### 2. Moved to Manual Testing (saved ~130 API calls from regular runs)
- ✅ `test_sariel_full_validation.py` - 110 API calls
- ✅ `test_sariel_exact_production.py` - ~20 API calls

### 3. Kept Essential Tests
- ✅ `test_sariel_consolidated.py` - Configurable (3-10 API calls)
- ✅ `test_sariel_production_methods.py` - 2-3 API calls
- ✅ `test_sariel_entity_debug.py` - 2 API calls
- ✅ `test_integration.py` - Variable API calls

## API Call Reduction

### Before Consolidation
- Regular test runs: ~178 API calls
- With full validation: ~288 API calls

### After Consolidation
- Regular test runs: ~10-20 API calls (94% reduction)
- Full test (SARIEL_FULL_TEST=true): ~30 API calls
- Manual tests available when needed

## Configuration Options

### test_sariel_consolidated.py
```bash
# Basic test (3 interactions)
TESTING=true vpython tests/test_sariel_consolidated.py

# Full test (10 interactions)
SARIEL_FULL_TEST=true TESTING=true vpython tests/test_sariel_consolidated.py

# Debug prompts
SARIEL_DEBUG_PROMPTS=true TESTING=true vpython tests/test_sariel_consolidated.py

# Multiple replays
SARIEL_REPLAYS=5 TESTING=true vpython tests/test_sariel_consolidated.py
```

## Other Real API Tests Still Active
These tests also make real API calls but are kept for specific purposes:
- `test_integration.py` - Core integration testing through Flask app
- `test_state_updates_generation.py` - State update validation
- `test_initial_entity_tracking.py` - Entity tracking validation

Note: `test_gemini_model_fallback.py` and `test_end_to_end_entity_tracking.py` were incorrectly identified as making real API calls - they actually use mocks.
