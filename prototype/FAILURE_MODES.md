# Validation Prototype: Failure Modes and Limitations

## Overview

This document details the known failure modes and limitations of each validator type based on comprehensive testing with edge cases and real-world scenarios.

## Validator-Specific Limitations

### SimpleTokenValidator

**Accuracy**: 70% on edge cases, F1 score: 0.444

**Failure Modes**:
1. **No Descriptor Matching**: Only matches exact entity names
   - Misses "the knight" → "Gideon" 
   - Misses "healer" → "Rowan"
   
2. **No Pronoun Resolution**: Cannot handle pronoun-only references
   - "He raised his shield" → Cannot identify as Gideon
   
3. **No Partial Name Matching**: Fails on interrupted names
   - "Gid--" → Cannot match to Gideon
   
4. **Case Sensitivity Issues**: While case-insensitive, compound names may fail

**Best Use Cases**: 
- Quick validation when entities are explicitly named
- Performance-critical applications with simple narratives

### TokenValidator

**Accuracy**: 80% on edge cases, F1 score: 0.833

**Failure Modes**:
1. **Limited Pronoun Handling**: Still struggles with pronoun-only text
   
2. **No Fuzzy Matching**: Cannot handle typos or variations
   - "Gidoen" → Would not match "Gideon"
   
3. **Partial Names**: Cannot match interrupted names
   
4. **Context-Free**: Doesn't consider narrative context

**Improvements over Simple**:
- Descriptor matching ("knight" → "Gideon")
- Better coverage of entity references

### FuzzyTokenValidator

**Accuracy**: 90% on edge cases, F1 score: 1.0 on standard tests

**Failure Modes**:
1. **Action-Only Inference**: Cannot reliably infer entities from actions alone
   - "A sword struck the wall" → Cannot definitively identify Gideon
   
2. **Over-Matching Risk**: Fuzzy threshold may cause false positives
   - Similar names might be confused
   
3. **Performance Overhead**: Pattern matching is slower than simple tokens

**Strengths**:
- Handles partial names ("Gid--" → "Gideon")
- Pronoun resolution with context
- Name variation tolerance

### LLMValidator

**Accuracy**: 80% on edge cases, F1 score: 1.0 on standard tests

**Failure Modes**:
1. **API Dependency**: Requires external service (or mock)
   
2. **Latency**: ~100ms overhead regardless of text length
   
3. **Over-Interpretation**: May infer entities not actually present
   - Generic "party" → might assume specific characters
   
4. **Cost**: Real API usage has token costs

**Strengths**:
- Understands context and semantics
- Handles complex references
- Can identify entity states

### HybridValidator

**Accuracy**: Varies by strategy, generally highest overall

**Failure Modes**:
1. **Slowest Performance**: Limited by slowest component (usually LLM)
   
2. **Complexity**: More points of failure
   
3. **Configuration Sensitivity**: Performance depends on weights/strategy

**Strengths**:
- Best overall accuracy
- Combines strengths of all approaches
- Configurable for different use cases

## Common Failure Patterns Across All Validators

### 1. Ambiguous References
**Pattern**: "Someone moved in the darkness"
- Cannot determine if this refers to expected entities
- Conservative validators mark as absent
- Aggressive validators may false positive

### 2. Negation Handling
**Pattern**: "Gideon was nowhere to be found"
- Some validators detect "Gideon" without considering negation
- Requires semantic understanding

### 3. Temporal References
**Pattern**: "Gideon had been there yesterday"
- Past tense may confuse presence detection
- Memory vs. current presence distinction

### 4. Collective References Without Individuals
**Pattern**: "The group pressed forward"
- Individual entities not mentioned
- Inference required to map to specific characters

## Performance Limitations

### Scaling Characteristics

| Validator | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| SimpleToken | O(n) | O(1) |
| Token | O(n*m) | O(m) |
| Fuzzy | O(n²) | O(n) |
| LLM | O(1)* | O(1) |
| Hybrid | O(max) | O(sum) |

*LLM has constant time but high baseline (~100ms)

### Text Length Impact

- **Token-based**: Linear scaling with narrative length
- **Fuzzy**: Super-linear due to pattern complexity
- **LLM**: Constant until token limit (~4000 tokens)
- **Hybrid**: Dominated by slowest component

## Mitigation Strategies

### 1. Cascading Validation
```python
# Use simple validator first, escalate if uncertain
if simple_validator.confidence < 0.8:
    result = fuzzy_validator.validate(...)
```

### 2. Context Enrichment
- Prepend entity manifest to narrative
- Include recent entity states
- Add location context

### 3. Result Caching
- Cache validation results for repeated narratives
- Use content hashing for cache keys
- TTL based on game state changes

### 4. Confidence Thresholds
- Set minimum confidence levels
- Use different thresholds for different game phases
- Allow manual override for edge cases

## Recommendations by Use Case

### Real-Time Validation
**Recommended**: TokenValidator or FuzzyTokenValidator
- Avoid LLM due to latency
- Cache results aggressively

### Accuracy-Critical
**Recommended**: HybridValidator with weighted_vote strategy
- Combines all approaches
- Highest overall accuracy

### High-Volume Processing
**Recommended**: SimpleTokenValidator with caching
- Fastest processing
- Acceptable accuracy for explicit names

### Complex Narratives
**Recommended**: LLMValidator or HybridValidator
- Handles context and semantics
- Worth the performance cost

## Future Improvements

1. **Coreference Resolution**: Better pronoun handling
2. **Negation Detection**: Understand "not present" patterns
3. **Temporal Awareness**: Distinguish past/present/future
4. **Entity State Tracking**: Maintain entity state across validations
5. **Confidence Calibration**: Better confidence scoring

---

*Last updated: 2025-01-29*
*Based on testing with 20 standard narratives and 10 edge cases*