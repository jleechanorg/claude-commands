# Test Plan: Pydantic vs Simple Entity Validation

## Context
We discovered that all previous "Pydantic" testing was actually testing entities_simple.py. This plan ensures we properly test and compare both approaches to make an informed decision.

## Objective
Determine whether Pydantic validation provides sufficient benefits over simple validation to justify the added dependency.

## Test Criteria

### 1. Validation Effectiveness
- **Malformed Data Detection**: Which approach catches more validation errors?
- **Error Message Quality**: Which provides clearer, more actionable errors?
- **Edge Case Handling**: Test with partial data, extra fields, wrong types

### 2. Performance
- **Object Creation Speed**: Time to create 1000 entity objects
- **Validation Overhead**: Cost of validation vs no validation
- **Memory Usage**: Compare memory footprint

### 3. Developer Experience
- **IDE Support**: Autocomplete, type hints, inline documentation
- **Debugging**: Which is easier to debug when things go wrong?
- **Error Messages**: Which helps developers fix issues faster?

### 4. Desync Prevention (Core Goal)
- **Entity Presence**: Does validation ensure all expected entities appear in narrative?
- **Data Consistency**: Does it prevent state/narrative mismatches?
- **Type Safety**: Does it prevent string/dict/list confusion?

## Test Implementation

### Step 1: Verify Test Truth
```python
def verify_test_module(module_name, module):
    """Ensure we're testing what we claim"""
    print(f"TESTING: {module_name}")
    print(f"  Module: {module.__name__}")
    print(f"  File: {module.__file__}")
    print(f"  Has Pydantic: {'pydantic' in str(module.__dict__)}")
    return True
```

### Step 2: Validation Tests

#### Test 2.1: Basic Validation
```python
# Pydantic approach
try:
    from schemas.entities_pydantic import SceneManifest
    verify_test_module("Pydantic", entities_pydantic)

    # Should fail - bad pattern
    manifest = SceneManifest(scene_id="wrong_format")
except ValidationError as e:
    print(f"Pydantic error: {e}")

# Simple approach
try:
    from schemas.entities_simple import SceneManifest
    verify_test_module("Simple", entities_simple)

    # Should fail - bad pattern
    manifest = SceneManifest(scene_id="wrong_format")
except ValueError as e:
    print(f"Simple error: {e}")
```

#### Test 2.2: Complex Validation
```python
# Test nested data, missing required fields, type coercion
test_cases = [
    {"scene_id": "scene_s1_t1_001", "session_number": "1"},  # String->int coercion
    {"scene_id": "scene_s1_t1_001"},  # Missing required field
    {"scene_id": "scene_s1_t1_001", "extra_field": "ignored?"},  # Extra fields
]
```

#### Test 2.3: Desync Prevention
```python
# The critical test - does validation prevent desync?
game_state = {
    "npc_data": {
        "Cassian": {"hp": 50, "present": True},
        "Guard": {"hp": "twenty"},  # Wrong type - should fail
    }
}

# Which approach catches the type error?
# Which approach ensures Cassian appears in narrative?
```

### Step 3: Performance Tests
```python
import time
import tracemalloc

def benchmark_approach(module_name, create_func, n=1000):
    """Benchmark entity creation"""
    verify_test_module(module_name, module)

    # Time test
    start = time.time()
    for i in range(n):
        obj = create_func(i)
    duration = time.time() - start

    # Memory test
    tracemalloc.start()
    objects = [create_func(i) for i in range(100)]
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "duration": duration,
        "objects_per_second": n / duration,
        "memory_per_100": current / 1024 / 1024  # MB
    }
```

### Step 4: Real LLM Integration Test
This is the critical final test using actual Gemini API and real campaign scenarios to measure desync rates.

#### Test Implementation: test_sariel_integration.py
```python
# Use existing test_sariel_integration.py as the real-world test harness
# This test runs with actual Gemini API and real campaign prompts

def test_entity_desync_prevention(validation_approach):
    """
    Measures entity tracking accuracy with real AI responses
    Uses test_sariel_integration.py patterns for authentic testing
    """
    # Use real Gemini models (not TEST_MODEL)
    # Use real campaign prompts from prompts/
    # Run multiple story turns with entity state changes

    test_scenarios = [
        "multi_character_combat",    # 4+ NPCs in combat scenario
        "npc_state_changes",        # NPCs gaining/losing status effects
        "character_interactions",    # PC-NPC dialogue with state updates
        "cassian_tracking_issue",    # The specific Cassian disappearing problem
        "wounded_recovery",         # Entities with changing HP/status
        "complex_scene_transitions" # Scene changes with entity persistence
    ]

    desync_metrics = {
        "entities_missing_from_narrative": 0,
        "entities_missing_from_state": 0,
        "entity_status_mismatches": 0,
        "entity_hp_inconsistencies": 0,
        "validation_errors_caught": 0,
        "total_entity_state_updates": 0
    }

    # Run each scenario 5 times to get statistical significance
    for scenario in test_scenarios:
        for run in range(5):
            result = run_real_campaign_scenario(scenario, validation_approach)
            update_desync_metrics(desync_metrics, result)

    return calculate_desync_rate(desync_metrics)

def run_real_campaign_scenario(scenario, validation_approach):
    """
    Executes a full campaign scenario with real Gemini API
    - Uses actual system prompts from prompts/
    - Uses production AI models (DEFAULT_MODEL, LARGE_CONTEXT_MODEL)
    - Tracks entity state through multiple story turns
    - Validates narrative-state consistency at each turn
    """
    pass

def measure_entity_tracking_accuracy():
    """
    Compares Pydantic vs Simple validation in preventing:
    1. Cassian disappearing from narrative (the core bug we're fixing)
    2. NPC status effects not updating properly
    3. Combat state becoming inconsistent with narrative
    4. Entity HP/status mismatches between state and story
    """

    pydantic_results = test_entity_desync_prevention("pydantic")
    simple_results = test_entity_desync_prevention("simple")

    # Statistical comparison
    desync_rate_improvement = (
        simple_results.desync_rate - pydantic_results.desync_rate
    ) / simple_results.desync_rate * 100

    return {
        "pydantic_desync_rate": pydantic_results.desync_rate,
        "simple_desync_rate": simple_results.desync_rate,
        "improvement_percentage": desync_rate_improvement,
        "statistical_significance": calculate_significance(pydantic_results, simple_results)
    }
```

#### Critical Measurements
- **Entity Presence Rate**: % of expected entities that appear in AI narrative
- **State Consistency Rate**: % of entity states that match between game state and narrative
- **Validation Effectiveness**: % of corrupted data caught before reaching AI
- **Error Recovery Rate**: % of validation errors that lead to successful fixes

#### Real Campaign Testing Protocol
1. **Load Production Prompts**: Use actual prompts from `prompts/` directory
2. **Use Production Models**: DEFAULT_MODEL and LARGE_CONTEXT_MODEL (not TEST_MODEL)
3. **Multi-Turn Testing**: Run 10+ story turns per scenario to catch desync patterns
4. **Statistical Validation**: 5 runs per scenario for significance testing
5. **Edge Case Focus**: Specifically test known problem areas (Cassian tracking, combat state)

#### Success Threshold
For Pydantic to justify the dependency, it must achieve:
- **>20% reduction in desync rate** compared to Simple validation
- **>90% entity presence rate** in complex scenarios
- **<5% false positive validation errors** that block valid data

## Success Criteria

### Pydantic Wins If:
1. Catches significantly more validation errors (>50% more)
2. Performance overhead is acceptable (<2x slower)
3. Prevents entity desync issues that Simple misses
4. Error messages lead to faster debugging

### Simple Wins If:
1. Catches all critical validation errors
2. Significantly faster (>2x)
3. No meaningful difference in desync prevention
4. Easier to maintain and debug

## Timeline
1. **Day 1**: Implement validation comparison tests (Steps 1-3)
   - Verify test truth (ensure we're testing correct modules)
   - Basic validation comparison
   - Complex validation edge cases
   - Negative testing (validation rejection)

2. **Day 2**: Performance benchmarking and basic integration
   - Object creation speed tests
   - Memory usage comparison
   - Initial integration with gemini_service.py

3. **Day 3**: Real-world integration testing with test_sariel_integration.py
   - Setup production-like test scenarios
   - Run multi-turn campaign scenarios with real Gemini API
   - Measure entity desync rates across both approaches
   - Focus on Cassian tracking and combat state consistency

4. **Day 4**: Statistical analysis and final decision
   - Compile desync rate statistics
   - Performance vs accuracy trade-off analysis
   - Final recommendation with supporting data
   - Implementation plan for winning approach

## Decision Framework

The decision should be based on:
1. **Primary Goal**: Does it prevent entity desync better?
2. **Cost/Benefit**: Is the added complexity worth the benefits?
3. **Maintenance**: Which is easier to maintain long-term?
4. **Performance**: Is the overhead acceptable for production?

## Expected Outcomes

### If Pydantic Wins:
- Add pydantic to requirements.txt
- Migrate entity_tracking.py to use entities_pydantic.py
- Remove entities_simple.py
- Document migration guide

### If Simple Wins:
- Remove entities_pydantic.py
- Document why Simple is sufficient
- Add comprehensive tests for Simple validation
- Consider adding specific validation where needed

## Appendix: Benefits Summary

### Pydantic Benefits
1. **Automatic Validation**: Validates on object creation
2. **Type Coercion**: Converts "1" to 1 automatically
3. **Clear Errors**: `ValidationError: scene_id: string does not match regex pattern`
4. **JSON Schema**: Can generate OpenAPI schemas
5. **IDE Support**: Better autocomplete and type checking
6. **Serialization**: Built-in `.dict()` and `.json()` methods

### Simple Benefits
1. **No Dependencies**: Works with standard library only
2. **Full Control**: Custom validation logic
3. **Lightweight**: Minimal memory overhead
4. **Transparent**: Easy to debug and understand
5. **Stable**: No version compatibility issues
6. **Flexible**: Can add validation only where needed

## Note on Previous Testing
All previous tests (PR #180) were flawed because they tested entities_simple.py while claiming to test Pydantic. This plan ensures we actually test what we claim to test.
