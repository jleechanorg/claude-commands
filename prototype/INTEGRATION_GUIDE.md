# Validation System Integration Guide

## Overview

This guide documents how to integrate the validation prototype into the WorldArchitect.AI codebase. The system is designed to prevent narrative desynchronization by validating AI-generated content against the current game state.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  llm_service │────▶│ Validation Layer │────▶│   game_state    │
│                 │◀────│                  │◀────│                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         ▼                       ▼                         ▼
   [AI Narrative]        [Valid/Invalid]          [Entity Manifest]
```

## Integration Points

### 1. GameState Class Enhancement

**File**: `mvp_site/game_state.py`

```python
class GameState:
    # Add these methods to the existing GameState class

    def get_active_entity_manifest(self) -> Dict[str, Any]:
        """
        Generate manifest of all active entities in current scene.
        """
        manifest = {
            "location": self.current_location,
            "entities": [],
            "timestamp": datetime.now().isoformat(),
            "entity_count": 0
        }

        # Populate from party_members and other relevant state
        for member in self.party_members:
            entity = {
                "id": f"{member['name'].lower()}_001",
                "name": member['name'],
                "type": "player_character",
                "status": self._get_entity_status(member),
                "descriptors": self._get_entity_descriptors(member)
            }
            manifest["entities"].append(entity)

        manifest["entity_count"] = len(manifest["entities"])
        return manifest

    def validate_narrative_consistency(self, narrative_text: str,
                                     strictness: str = "normal") -> Dict[str, Any]:
        """
        Validate narrative against current entity manifest.
        """
        from prototype.validators.fuzzy_token_validator import FuzzyTokenValidator
        # Implementation as shown in prototype
```

### 2. Gemini Service Integration

**File**: `mvp_site/llm_service.py`

```python
# Add to existing generate_narrative method

def generate_narrative(self, game_state, prompt, **kwargs):
    # Step 1: Get entity manifest
    manifest = game_state.get_active_entity_manifest()

    # Step 2: Enhance prompt with manifest (SANITIZED)
    enhanced_prompt = self._inject_manifest(prompt, manifest)

    # Step 3: Generate narrative
    narrative = self._call_llm_api(enhanced_prompt)

    # Step 4: Validate result
    validation = game_state.validate_narrative_consistency(narrative)

    # Step 5: Handle validation failure
    if not validation["is_valid"]:
        narrative = self._handle_validation_failure(
            narrative, validation, game_state
        )

    return narrative

def _inject_manifest(self, prompt: str, manifest: Dict) -> str:
    """Safely inject entity manifest into prompt."""
    # Sanitize entity names to prevent injection
    safe_entities = [
        self._sanitize_for_prompt(e["name"])
        for e in manifest["entities"]
    ]

    manifest_prompt = f"""
[SYSTEM: Current Scene State]
Location: {self._sanitize_for_prompt(manifest["location"])}
Characters Present: {", ".join(safe_entities)}
IMPORTANT: All characters listed above MUST be acknowledged in the narrative.

"""
    return manifest_prompt + prompt

def _handle_validation_failure(self, narrative: str, validation: Dict,
                              game_state: GameState) -> str:
    """Handle validation failures with retry logic."""
    if validation["confidence"] < 0.5:
        # Low confidence - regenerate with stronger constraints
        self.logger.warning(
            f"NARRATIVE_DESYNC: Missing {validation['missing_entities']}"
        )
        # Retry logic here
    return narrative
```

### 3. Configuration

**File**: `mvp_site/config.py`

```python
# Validation configuration
VALIDATION_CONFIG = {
    "enabled": True,
    "default_validator": "FuzzyTokenValidator",
    "strictness_levels": {
        "strict": {"validator": "HybridValidator", "strategy": "unanimous"},
        "normal": {"validator": "FuzzyTokenValidator", "threshold": 0.8},
        "lenient": {"validator": "TokenValidator", "threshold": 0.6}
    },
    "caching": {
        "enabled": True,
        "ttl_seconds": 60,
        "max_size": 1000
    },
    "performance": {
        "timeout_ms": 100,
        "max_retries": 2,
        "fallback_validator": "SimpleTokenValidator"
    }
}
```

### 4. Monitoring and Logging

**File**: `mvp_site/monitoring.py`

```python
# Add validation metrics
VALIDATION_METRICS = {
    "validation_attempts": Counter(),
    "validation_successes": Counter(),
    "validation_failures": Counter(),
    "validation_duration": Histogram(),
    "desync_prevented": Counter(),
}

def log_validation_event(result: Dict, duration: float):
    """Log validation metrics."""
    VALIDATION_METRICS["validation_attempts"].inc()

    if result["is_valid"]:
        VALIDATION_METRICS["validation_successes"].inc()
    else:
        VALIDATION_METRICS["validation_failures"].inc()
        if result["confidence"] > 0.7:
            VALIDATION_METRICS["desync_prevented"].inc()

    VALIDATION_METRICS["validation_duration"].observe(duration)
```

## API Design

### Validation Result Schema

```typescript
interface ValidationResult {
  is_valid: boolean;
  missing_entities: string[];
  extra_entities: string[];
  confidence: number;  // 0.0 to 1.0
  validation_errors: string[];
  warnings: string[];
  metadata?: {
    validator_used: string;
    processing_time_ms: number;
    cached: boolean;
  };
}
```

### Entity Manifest Schema

```typescript
interface EntityManifest {
  location: string;
  entities: Entity[];
  timestamp: string;  // ISO 8601
  entity_count: number;
}

interface Entity {
  id: string;
  name: string;
  type: "player_character" | "npc" | "creature";
  status: string[];  // ["conscious", "armed", etc.]
  descriptors: string[];  // ["knight", "warrior", etc.]
}
```

## Implementation Checklist

### Phase 1: Core Integration (Week 1)
- [ ] Add manifest generation to GameState
- [ ] Implement basic validation method
- [ ] Integrate FuzzyTokenValidator
- [ ] Add caching layer
- [ ] Unit tests for manifest generation

### Phase 2: Service Integration (Week 2)
- [ ] Modify llm_service.py
- [ ] Add prompt injection logic
- [ ] Implement retry mechanism
- [ ] Add monitoring/metrics
- [ ] Integration tests

### Phase 3: Production Rollout (Week 3)
- [ ] Feature flags for gradual rollout
- [ ] Performance monitoring
- [ ] A/B testing setup
- [ ] Documentation updates
- [ ] Team training

## Testing Strategy

### Unit Tests
```python
def test_manifest_generation():
    """Test entity manifest is correctly generated."""
    game_state = GameState()
    game_state.party_members = ["Gideon", "Rowan"]

    manifest = game_state.get_active_entity_manifest()

    assert manifest["entity_count"] == 2
    assert any(e["name"] == "Gideon" for e in manifest["entities"])

def test_validation_accuracy():
    """Test validation catches missing entities."""
    narrative = "The knight stood alone."
    result = validate_narrative(narrative, ["Gideon", "Rowan"])

    assert not result["is_valid"]
    assert "Rowan" in result["missing_entities"]
```

### Integration Tests
- Test with real Gemini API
- Measure end-to-end latency
- Verify retry logic
- Test cache behavior

### Load Tests
- 1000 concurrent validations
- Measure 95th percentile latency
- Monitor memory usage
- Test cache eviction

## Security Considerations

### Prompt Injection Prevention
```python
def _sanitize_for_prompt(text: str) -> str:
    """Remove characters that could break prompt structure."""
    # Remove quotes, backslashes, newlines
    sanitized = text.replace('"', '').replace("'", '')
    sanitized = sanitized.replace('\\', '').replace('\n', ' ')

    # Limit length
    return sanitized[:50]
```

### Rate Limiting
- Implement per-user validation limits
- Circuit breaker for API failures
- Graceful degradation to simple validator

## Rollback Plan

1. **Feature Flag Control**
   ```python
   if FEATURE_FLAGS.get("narrative_validation", False):
       result = validate_narrative(text)
   ```

2. **Monitoring Triggers**
   - Validation latency > 200ms
   - Error rate > 5%
   - Memory usage spike

3. **Rollback Steps**
   - Disable feature flag
   - Clear validation cache
   - Monitor error rates
   - Notify team

## Success Metrics

- **Desync Rate**: Target < 5% (from 68% baseline)
- **Validation Latency**: p95 < 50ms
- **Cache Hit Rate**: > 30%
- **API Cost**: < $500/month
- **User Satisfaction**: No increase in complaints

---

*Last updated: 2025-01-29*
*Version: 1.0*
