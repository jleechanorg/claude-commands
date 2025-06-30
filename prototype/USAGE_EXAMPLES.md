# Validation System Usage Examples

## Quick Start

### Basic Usage

```python
from prototype.validators.fuzzy_token_validator import FuzzyTokenValidator

# Create validator
validator = FuzzyTokenValidator()

# Validate narrative
result = validator.validate(
    narrative_text="Gideon raised his sword while the healer chanted.",
    expected_entities=["Gideon", "Rowan"],
    location="Combat Arena"
)

# Check results
if result["all_entities_present"]:
    print("✓ All characters accounted for")
else:
    print(f"✗ Missing: {result['entities_missing']}")
print(f"Confidence: {result['confidence']:.2%}")
```

## Common Use Cases

### 1. Simple Validation

```python
from prototype.validators.token_validator import SimpleTokenValidator

validator = SimpleTokenValidator()

# Fast validation for explicit names
narrative = "Gideon and Rowan entered the chamber."
result = validator.validate(narrative, ["Gideon", "Rowan"])
# Result: ✓ Valid (both names found)
```

### 2. Descriptor-Based Validation

```python
from prototype.validators.token_validator import TokenValidator

validator = TokenValidator()

# Handles titles and descriptors
narrative = "The knight stood guard while the healer tended wounds."
result = validator.validate(narrative, ["Gideon", "Rowan"])
# Result: ✓ Valid (knight→Gideon, healer→Rowan)
```

### 3. Fuzzy Matching

```python
from prototype.validators.fuzzy_token_validator import FuzzyTokenValidator

validator = FuzzyTokenValidator(fuzzy_threshold=0.8)

# Handles variations and partial matches
narrative = "Gid-- The warrior's cry was cut short. Row-- The cleric gasped."
result = validator.validate(narrative, ["Gideon", "Rowan"])
# Result: ✓ Valid (partial names matched)
```

### 4. LLM-Based Validation

```python
from prototype.validators.llm_validator import LLMValidator
from prototype.gemini_service_wrapper import get_gemini_service

# With real API
service = get_gemini_service("path/to/api_key.txt")
validator = LLMValidator(gemini_service=service)

# Or with mock for testing
validator = LLMValidator()  # Uses mock service

# Semantic understanding
narrative = "He raised his shield as she began the incantation."
result = validator.validate(narrative, ["Gideon", "Rowan"])
# Result: ✓ Valid (pronouns resolved contextually)
```

### 5. Hybrid Validation

```python
from prototype.validators.hybrid_validator import HybridValidator

# Maximum accuracy with multiple strategies
validator = HybridValidator(combination_strategy="weighted_vote")

narrative = "Someone moved in the shadows - friend or foe?"
result = validator.validate(narrative, ["Gideon", "Rowan"])
# Combines results from all validators for best accuracy
```

## Integration Examples

### Game State Integration

```python
from prototype.game_state_integration import MockGameState

# In your game code
class GameState:
    def validate_narrative_consistency(self, narrative: str) -> dict:
        from prototype.validators.fuzzy_token_validator import FuzzyTokenValidator
        
        # Get current party members
        manifest = self.get_active_entity_manifest()
        expected = [e["name"] for e in manifest["entities"]]
        
        # Validate
        validator = FuzzyTokenValidator()
        result = validator.validate(narrative, expected, self.current_location)
        
        # Convert to game format
        return {
            "is_valid": result["all_entities_present"],
            "missing_entities": result["entities_missing"],
            "confidence": result["confidence"]
        }
```

### Narrative Service Integration

```python
class NarrativeService:
    def generate_with_validation(self, prompt: str, game_state):
        # Get expected entities
        manifest = game_state.get_active_entity_manifest()
        
        # Generate narrative
        narrative = self.generate_narrative(prompt)
        
        # Validate
        validation = game_state.validate_narrative_consistency(narrative)
        
        # Retry if needed
        if not validation["is_valid"] and validation["confidence"] < 0.7:
            enhanced_prompt = f"{prompt}\nInclude: {validation['missing_entities']}"
            narrative = self.generate_narrative(enhanced_prompt)
            
        return narrative
```

## Advanced Features

### Custom Confidence Thresholds

```python
# Strict validation for important scenes
validator = FuzzyTokenValidator(fuzzy_threshold=0.9)
result = validator.validate(narrative, entities)

if result["confidence"] < 0.8:
    # Fall back to more expensive validator
    llm_validator = LLMValidator()
    result = llm_validator.validate(narrative, entities)
```

### Caching Results

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_validate(narrative_hash: str, entities_tuple: tuple):
    validator = FuzzyTokenValidator()
    return validator.validate(narrative, list(entities_tuple))

# Usage
narrative_hash = hashlib.md5(narrative.encode()).hexdigest()
entities_tuple = tuple(sorted(entities))
result = cached_validate(narrative_hash, entities_tuple)
```

### Batch Processing

```python
from prototype.tests.test_harness import TestHarness

# Process multiple narratives
harness = TestHarness()
harness.register_validator("fuzzy", FuzzyTokenValidator())

narratives = load_narratives_from_database()
results = []

for narrative in narratives:
    result = harness.run_single_test("fuzzy", narrative)
    results.append(result)

# Analyze results
accuracy = sum(1 for r in results if r["all_entities_present"]) / len(results)
print(f"Batch accuracy: {accuracy:.2%}")
```

### Performance Monitoring

```python
from prototype.logging_config import metrics_collector
import time

# Wrap validation with timing
def validate_with_metrics(validator, narrative, entities):
    start = time.time()
    result = validator.validate(narrative, entities)
    duration = time.time() - start
    
    # Log metrics
    print(f"Validation took {duration*1000:.1f}ms")
    
    # Get accumulated metrics
    metrics = metrics_collector.get_metrics(validator.name)
    print(f"Average time: {metrics['validators'][validator.name]['avg_duration']:.3f}s")
    
    return result
```

## Error Handling

```python
def safe_validate(narrative: str, entities: List[str]) -> dict:
    """Validate with fallback on errors."""
    try:
        # Try fuzzy validator first
        validator = FuzzyTokenValidator()
        return validator.validate(narrative, entities)
    except Exception as e:
        print(f"Fuzzy validation failed: {e}")
        
        try:
            # Fall back to simple validator
            validator = SimpleTokenValidator()
            return validator.validate(narrative, entities)
        except Exception as e2:
            print(f"Simple validation failed: {e2}")
            
            # Return safe default
            return {
                "all_entities_present": False,
                "entities_found": [],
                "entities_missing": entities,
                "confidence": 0.0,
                "errors": [str(e), str(e2)]
            }
```

## Configuration Options

```python
# Validator-specific configuration
config = {
    "SimpleTokenValidator": {
        # No configuration needed
    },
    "TokenValidator": {
        # Uses EntityManifest for descriptors
    },
    "FuzzyTokenValidator": {
        "fuzzy_threshold": 0.8,  # 0.0-1.0, higher = stricter
    },
    "LLMValidator": {
        "api_key_path": "keys/gemini_api_key.txt",
        "timeout": 30.0,  # seconds
        "max_retries": 3,
        "retry_delay": 1.0,  # seconds
        "use_simple_prompt": False
    },
    "HybridValidator": {
        "combination_strategy": "weighted_vote",  # or "unanimous", "majority", "confidence_based"
        "validator_weights": {
            "token": 0.3,
            "fuzzy": 0.4,
            "llm": 0.3
        }
    }
}
```

## Testing Your Integration

```python
def test_validation_integration():
    """Test validators with your game's narratives."""
    
    # Load test cases
    test_narratives = [
        {
            "narrative": "Your actual game narrative here",
            "expected_entities": ["Gideon", "Rowan"],
            "location": "Current Location"
        }
    ]
    
    # Test each validator
    validators = [
        SimpleTokenValidator(),
        TokenValidator(),
        FuzzyTokenValidator(),
        LLMValidator(),
        HybridValidator()
    ]
    
    for validator in validators:
        print(f"\nTesting {validator.name}:")
        
        for test in test_narratives:
            result = validator.validate(
                test["narrative"],
                test["expected_entities"],
                test["location"]
            )
            
            print(f"  Valid: {result['all_entities_present']}")
            print(f"  Confidence: {result['confidence']:.2%}")
            print(f"  Time: {result.get('elapsed_time', 0)*1000:.1f}ms")
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```python
   # Run from prototype directory
   import sys
   sys.path.append('/path/to/prototype')
   ```

2. **Low Confidence Results**
   ```python
   # Check what was actually found
   print(f"Found: {result['entities_found']}")
   print(f"Missing: {result['entities_missing']}")
   print(f"References: {result.get('entity_references', {})}")
   ```

3. **Performance Issues**
   ```python
   # Use simpler validators for real-time
   if response_time_critical:
       validator = SimpleTokenValidator()
   else:
       validator = FuzzyTokenValidator()
   ```

---

*For more examples, see the test files in `prototype/tests/`*