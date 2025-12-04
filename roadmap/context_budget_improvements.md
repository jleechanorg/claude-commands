# Context Budget System - Improvement Roadmap

**Created**: 2025-12-04
**PR**: #2311 (Initial Implementation)
**Status**: Phase 1 Complete, Phase 2 Planned

---

## Executive Summary

The context budget system was implemented to solve `ContextTooLargeError` for users with long campaigns. Multi-model review (Gemini 2.5 Pro, Perplexity Sonar) confirmed the design is sound with recommendations for future enhancements.

---

## Phase 1: Core Implementation (COMPLETE)

### Delivered in PR #2311

| Feature | Status | Description |
|---------|--------|-------------|
| Percentage-Based Allocation | Done | 25% start / 70% end / 5% reserved |
| Adaptive Reduction Loop | Done | Iteratively reduces turns until fit |
| Minimum Turn Guarantees | Done | 3 start + 5 end minimum |
| Budget Logging | Done | Detailed token budget diagnostics |

### Test Coverage

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_adaptive_truncation.py` | 6 | Passing |
| `test_context_truncation.py` | 3 | Passing |
| `test_output_token_budget_regression.py` | 9 | Passing |

### Documentation

- `docs/context_budget_design.md` - Complete design document
- `tmp/secondo_analysis_20251204_1217.md` - Multi-model review report

---

## Phase 2: Semantic Prioritization (PLANNED)

**Goal**: Improve truncation quality by considering narrative importance, not just position.

### 2.1 Importance Scoring System

Add importance scores to story turns:

```python
class TurnImportance:
    PLOT_CRITICAL = 1.0    # Major story beats, reveals
    CHARACTER_DEFINING = 0.8  # Character development moments
    MECHANICAL_STATE = 0.6   # Combat results, item acquisition
    FLAVOR = 0.3            # Ambient description, filler
```

**Implementation**:
1. LLM tags turns with importance during generation
2. Store importance in turn metadata
3. Truncation prioritizes low-importance turns for removal

### 2.2 Hierarchical Memory

Replace simple truncation with tiered compression:

```
Tier 1: Raw recent turns (last 5-10)
Tier 2: Summarized sessions ("Session 5: Party defeated dragon, gained artifact")
Tier 3: Static world state (character sheets, quest log, NPC relationships)
```

**Benefits**:
- Preserves critical context even in long campaigns
- Reduces token usage while maintaining coherence
- Enables "memory recall" for forgotten plot points

---

## Phase 3: Per-Model Tuning (PLANNED)

**Goal**: Optimize percentages for each model's characteristics.

### 3.1 Model-Specific Configurations

| Model | Start % | End % | Notes |
|-------|---------|-------|-------|
| Cerebras 131K | 20% | 75% | Smaller context, prioritize recency |
| Gemini 1M | 25% | 70% | Default balanced allocation |
| OpenRouter 32K | 15% | 80% | Very small, maximize recency |

### 3.2 Scene-Type Configurations

| Scene Type | Start % | End % | Notes |
|------------|---------|-------|-------|
| Combat | 10% | 85% | Recent actions critical |
| Roleplay | 30% | 65% | Character history matters |
| Exploration | 25% | 70% | Balanced |
| Mystery | 35% | 60% | Past clues important |

---

## Phase 4: Observability & Tuning (PLANNED)

**Goal**: Build feedback loops for continuous improvement.

### 4.1 Metrics Dashboard

Track in GCP logs:
- Truncation events per model
- Average turns dropped per request
- ContextTooLargeError frequency
- User narrative coherence ratings (future)

### 4.2 A/B Testing Framework

Test different configurations:
```python
CONTEXT_EXPERIMENTS = {
    "control": {"start": 0.25, "end": 0.70},
    "recency_heavy": {"start": 0.15, "end": 0.80},
    "balanced": {"start": 0.30, "end": 0.65},
}
```

### 4.3 Automated Eval Suite

Create test campaigns with known "important" moments:
- Verify important turns are preserved
- Measure narrative coherence scores
- Track cost per request

---

## Risk Mitigation

### Known Risks

| Risk | Mitigation | Owner |
|------|------------|-------|
| Important context dropped | Phase 2 importance scoring | AI Team |
| Legacy 20-cap conflicts | Evaluate removal in Phase 3 | Dev |
| Excessive truncation | Monitor truncation severity | DevOps |

### Monitoring Alerts

1. **Truncation Severity**: Alert if average truncation >80%
2. **Error Rate**: Alert on any `ContextTooLargeError`
3. **Model Context Usage**: Track % of context window used

---

## Success Criteria

### Phase 1 (Current)
- [x] Zero `ContextTooLargeError` in production logs
- [x] All existing tests passing
- [x] Design document approved by multi-model review

### Phase 2
- [ ] Importance tagging for 100% of new turns
- [ ] 20% reduction in tokens while maintaining coherence
- [ ] User satisfaction maintained or improved

### Phase 3
- [ ] Per-model configs deployed
- [ ] Scene-type detection implemented
- [ ] A/B test framework operational

### Phase 4
- [ ] Metrics dashboard live
- [ ] Eval suite with 50+ test cases
- [ ] Automated weekly reports

---

## Timeline Considerations

Implementation order based on impact and complexity:

1. **Phase 1** - Complete (PR #2311)
2. **Phase 2.1** - Importance scoring (medium complexity, high impact)
3. **Phase 3.1** - Model configs (low complexity, medium impact)
4. **Phase 2.2** - Hierarchical memory (high complexity, high impact)
5. **Phase 4** - Observability (medium complexity, ongoing value)

---

## References

- Design Doc: `docs/context_budget_design.md`
- Second Opinion: `tmp/secondo_analysis_20251204_1217.md`
- Related PRs: #2284, #2294, #2201, #2311

---

## Appendix: Multi-Model Review Summary

### Gemini 2.5 Pro Verdict
> "Well-structured and thoughtful design... The defense-in-depth approach is particularly strong."

### Perplexity Sonar Verdict
> "Close to production best practices... ratios are reasonable starting heuristic."

### Key Recommendations Incorporated
1. Consider semantic importance scoring (Phase 2)
2. Make percentages configurable per model (Phase 3)
3. Add monitoring for truncation metrics (Phase 4)
