# Implementation Plan: Enhanced State Synchronization Protocol

## 1. Overview

This document outlines the comprehensive implementation plan for enhancing WorldArchitect.AI's state synchronization system. The plan addresses a recurring `Narrative Desynchronization Error` where narrative output fails to accurately reflect the presence of all characters as defined in the `CURRENT GAME STATE`.

The implementation is structured in two phases:
- **Phase 1**: AI Token Audit and Validation Infrastructure (Foundation)
- **Phase 2**: Core State Synchronization Protocol (Patch 1.1)

This ordering ensures we understand all AI output patterns before implementing the synchronization logic.

## 2. Core Problem

The root cause of the fault was identified as the **absence of a strict, automated "Party State Synchronization" protocol that runs before every narrative generation.** The narrative engine was prioritizing cached narrative context over the canonical `game_state`, leading to inconsistencies.

Additionally, the system lacks:
- Comprehensive understanding of all AI-generated tokens and their expected handlers
- Validation layer to catch format mismatches before they corrupt state
- Pattern detection to identify systematic integration gaps

## 3. Implementation Timeline

**CRITICAL: Phase Dependencies**
- Phase 2 implementation is blocked until Phase 1 delivers concrete token schemas
- No Phase 2 work can begin without understanding AI output formats from Phase 1
- Security review must be completed before any prompt injection implementation

### Phase 1: AI Token Audit and Validation Infrastructure (Weeks 1-2)
**Must complete before Phase 2 - Deliverables required for Phase 2 design**

#### Milestone 1.1: AI Token Audit & Registry
- **PR #1:** Create comprehensive AI token registry and audit
- **Deliverables:**
  - Complete audit of all AI-generated tokens in prompts/ directory
  - Token registry mapping AI instructions → code handlers
  - Gap analysis report identifying missing implementations
  - Document all current AI→Code integration points
- **Files:** docs/ai-token-registry.md, audit scripts
- **Acceptance:** All AI tokens documented with handler status

#### Milestone 1.2: Validation Infrastructure
- **PR #2:** Add AI output validation layer
- **Deliverables:**
  - Schema definitions for all AI output formats
  - Validation functions that catch format mismatches
  - Logging for validation failures and unknown tokens
  - Integration points for state update pipeline
- **Files:** ai_validation.py, schema definitions
- **Acceptance:** All AI outputs validated before processing

#### Milestone 1.3: Pattern Detection
- **PR #3:** Systematic corruption pattern detection
- **Deliverables:**
  - Scripts to detect similar corruption patterns across codebase
  - Automated checks for "Two Source of Truth" problems
  - CI/CD pipeline integration
  - Documentation of detected patterns
- **Files:** scripts/pattern_detection.py, CI integration
- **Acceptance:** Automated detection of integration gaps

### Phase 2: Core State Synchronization Protocol (Patch 1.1) (Week 3)

## 4. `Patch 1.1` Implementation Details

### 4.1. Codebase Integration & Architecture
*   **Action:** The new methods (`get_active_entity_manifest`, `validate_narrative_consistency`) will be implemented directly within the `GameState` class in `mvp_site/game_state.py`.
*   **Rationale:** This centralizes state-related logic and validation within the primary `GameState` object, adhering to existing architectural patterns for better maintainability.

### 4.2. Integration with Existing Validation
*   **Action:** Extend the existing `validate_checkpoint_consistency()` method to call the new validation functions
*   **Integration:** The new methods will work alongside existing HP, location, and mission validation
*   **Data Flow:** AI Output → Token Validation (Phase 1) → State Manifest → Narrative Validation → Final Output

### 4.3. Edge Case Handling
*   **Action:** The `get_active_entity_manifest()` method will be enhanced to parse the `status` array for each entity (e.g., `status: ['hidden']`, `status: ['unconscious']`).
*   **Combat State:** Special handling for combat participants with dedicated validation
*   **Rationale:** This allows the system to accurately track and describe characters who are present in a scene but not immediately visible or active, preventing logical errors in the narrative (e.g., an unconscious character performing an action).

### 4.4. Performance Optimization
*   **Action:** The generated Scene Manifest will be cached using a per-request, in-memory cache suitable for stateless environments.
*   **Implementation Details:**
     - Cache stored as instance attributes on GameState object (e.g., `self._manifest_cache`, `self._manifest_timestamp`)
     - Cache lifecycle limited to single API request duration
     - No external dependencies (Redis, etc.) required
     - Cache invalidated when `last_state_update_timestamp` changes
*   **Performance Targets:** 
     - Manifest generation: < 50ms for scenes with < 20 entities
     - Validation check: < 10ms per narrative generation
*   **Rationale:** This approach prevents redundant manifest generation within the same request while maintaining simplicity in our stateless Cloud Run environment.

### 4.5. Flexible Narrative Validation with Performance Optimization
*   **Action:** The `validate_narrative_consistency()` method will use an optimized matching algorithm.
*   **Implementation Details:**
     - Build entity presence index during manifest generation for O(1) lookups
     - Use set-based operations for descriptor matching instead of substring searches
     - Consider Bloom filters for fast negative matching on large entity sets
     - Optimized approach:
       ```python
       # Build index once
       entity_index = {descriptor.lower(): entity_id 
                       for entity in manifest["entities"] 
                       for descriptor in entity["descriptors"]}
       
       # Fast lookup during validation
       narrative_tokens = set(narrative_text.lower().split())
       matched_entities = {entity_index[token] 
                          for token in narrative_tokens 
                          if token in entity_index}
       ```
     - Configurable strictness levels (strict/normal/lenient)
*   **Performance Note:** Avoid O(n*m) substring searches; use indexed lookups for scalability

### 4.6. Graceful Error Recovery Protocol with Error Handling
*   **Action:** Implement comprehensive error handling with timeouts and circuit breakers.
*   **Error Handling Specifications:**
     - Set timeout for AI regeneration attempts: 30 seconds max
     - Implement exponential backoff: 1s, 2s, 4s between retries
     - Circuit breaker: After 3 consecutive failures, enter safe mode
     - Rate limiting: Max 5 fallback triggers per game session
     - Error boundaries for each component:
       ```python
       try:
           manifest = game_state.get_active_entity_manifest()
       except Exception as e:
           logger.error(f"Manifest generation failed: {e}")
           manifest = {"entities": [], "error": "manifest_generation_failed"}
       ```
*   **Fallback Procedure:**
    1.  Log a `CRITICAL_NARRATIVE_DESYNC` error with full context
    2.  Check if state itself is corrupted (validate against schema)
    3.  Output user-facing message: `[SYSTEM WARNING: Re-synchronizing scene state...]`
    4.  Execute "safe mode" render with location data from last known good state
    5.  If safe mode fails, return minimal response: "An error occurred. Please try again."
*   **Prevention:** Monitor fallback frequency; if > 5% of requests, disable feature

### 4.7. Concrete Integration Points
*   **Primary Integration:** Modifications to `gemini_service.py` to enforce state synchronization
*   **Integration Sequence:**
     1. **Before AI Call:** After loading GameState, call `game_state.get_active_entity_manifest()`
     2. **Prompt Injection with Security:** 
        - **CRITICAL SECURITY**: Sanitize all entity names/descriptions before injection
        - Use structured prompt with placeholders instead of string concatenation
        - Example secure format:
        ```
        [SYSTEM: Scene Manifest - Characters present: {sanitized_entities}]
        ... [USER PROMPT]
        ```
     3. **After AI Call:** Call `game_state.validate_narrative_consistency(response_text)`
     4. **Error Handling:** Trigger recovery protocol if validation fails
*   **Security Note:** All user-controllable data must be sanitized to prevent prompt injection attacks

### 4.8. Implementation Details and Specifications

#### Function Signatures
```python
class GameState:
    def get_active_entity_manifest(self) -> Dict[str, Any]:
        """
        Generate manifest of all active entities in current scene.
        Returns:
            {
                "location": str,
                "entities": [
                    {
                        "id": str,
                        "name": str,
                        "type": str,
                        "status": List[str],
                        "descriptors": List[str]  # For matching
                    }
                ],
                "timestamp": str,
                "entity_count": int
            }
        """
        pass
    
    def validate_narrative_consistency(self, narrative_text: str, 
                                     strictness: str = "normal") -> Dict[str, Any]:
        """
        Validate narrative against current entity manifest.
        Args:
            narrative_text: The AI-generated narrative
            strictness: "strict" | "normal" | "lenient"
        Returns:
            {
                "is_valid": bool,
                "missing_entities": List[str],
                "extra_entities": List[str],
                "validation_errors": List[str]
            }
        """
        pass
```

#### Scene Manifest Schema
```json
{
    "location": "Kaelan's Cell",
    "entities": [
        {
            "id": "gideon_001",
            "name": "Gideon",
            "type": "player_character",
            "status": ["conscious", "armed"],
            "descriptors": ["gideon", "ser vance", "knight", "warrior"]
        },
        {
            "id": "rowan_001",
            "name": "Rowan",
            "type": "player_character", 
            "status": ["conscious", "healing"],
            "descriptors": ["rowan", "healer", "cleric"]
        }
    ],
    "timestamp": "2024-01-01T12:00:00Z",
    "entity_count": 2
}
```

## 5. Risk Mitigation Strategies

### 5.1. Performance Risks
*   **Risk:** Scene Manifest generation could degrade performance for large entity counts
*   **Mitigation:** 
     - Implement lazy loading for entity details
     - Add circuit breaker for scenes > 50 entities
     - Profile and optimize hot paths
     - Consider read-through cache with TTL

### 5.2. False Positive Risks
*   **Risk:** Overly strict validation could block valid narratives
*   **Mitigation:**
     - Implement configurable validation levels
     - Start in "warning mode" - log but don't block
     - Collect metrics on validation failures before enforcing
     - Allow manual override for edge cases

### 5.3. User Experience Risks
*   **Risk:** "Safe mode" fallback might break immersion
*   **Mitigation:**
     - A/B test different fallback message styles
     - Make fallback descriptions contextually appropriate
     - Limit fallback frequency with exponential backoff
     - Track user engagement metrics during fallbacks

### 5.4. Integration Complexity Risks
*   **Risk:** Multiple validation layers could create maintenance burden
*   **Mitigation:**
     - Clear separation of concerns between layers
     - Comprehensive integration tests
     - Well-documented API contracts
     - Regular code reviews focusing on complexity

### 5.5. Security Risks
*   **Risk:** Prompt injection through unsanitized entity names/descriptions
*   **Mitigation:**
     - Input sanitization layer before any prompt construction
     - Allowlist approach for entity name characters
     - Escape special characters in prompts
     - Use structured prompts with placeholders
     - Regular security audits of prompt construction
*   **Risk:** Sensitive game data exposure in logs
*   **Mitigation:**
     - Implement log sanitization
     - Use structured logging with PII filtering
     - Separate debug logs from production logs
     - Regular audit of log contents
*   **Risk:** DOS through validation abuse
*   **Mitigation:**
     - Rate limiting per user/session
     - Circuit breakers for expensive operations
     - Caching to prevent repeated calculations

## 6. Testing Strategy

### 6.1. Test-Driven Development Approach
*   **Test Class:** Create `TestStateSynchronization` in `mvp_site/test_game_state.py`
*   **TDD Process:** Write failing tests first, then implement to make them pass

### 6.2. Core Test Cases
1. **test_manifest_creation()**
   - Assert `get_active_entity_manifest` correctly lists characters and statuses
   - Test hidden, unconscious, and active states
   - Verify manifest format and completeness

2. **test_manifest_caching()**
   - Assert cache is used when timestamp unchanged
   - Assert cache invalidated when timestamp updated
   - Verify performance improvement with caching

3. **test_narrative_validation_success()**
   - Provide matching narrative
   - Assert `validate_narrative_consistency` returns no discrepancies
   - Test various valid narrative variations

4. **test_narrative_validation_failure()**
   - Provide mismatched narrative (missing characters)
   - Assert function correctly identifies desync
   - Verify specific error details returned

### 6.3. Additional Test Coverage
- Edge cases: empty state, malformed data, null values
- Performance benchmarks for manifest generation
- Integration tests with actual gemini_service.py flow
- Stress testing with 50+ entities
- **Security Testing:**
  - Prompt injection tests with malicious entity names
  - Test sanitization of all user-controllable inputs
  - Verify no sensitive data in logs
- **Load Testing:**
  - Concurrent requests with different game states
  - Performance under 100+ simultaneous validations
  - Memory usage profiling
- **Failure Testing:**
  - Corrupt game state handling
  - Network timeout scenarios
  - AI service unavailability

### 6.4. Acceptance Criteria
- All TDD tests passing
- 100% code coverage for new methods
- < 1% false positive rate on validation
- Performance targets met (see section 4.4)
- Zero unhandled exceptions in error paths
- No security vulnerabilities in penetration testing
- Load tests pass with < 5% error rate at peak load

## 7. Monitoring and Observability

### 7.1. Metrics to Track
- Validation success/failure rates by type
- Performance metrics (p50, p95, p99 latencies)
- Cache hit rates for Scene Manifests
- Fallback frequency and user impact
- Unknown token encounters

### 7.2. Logging Strategy
- Structured logging for all validation failures
- Contextual information (game state, AI output, expected vs actual)
- Correlation IDs for tracing issues
- Log levels: DEBUG for development, INFO for production

### 7.3. Alerting
- Alert on validation failure rate > 5%
- Alert on performance degradation > 20%
- Alert on unknown token frequency spike
- Daily reports on validation patterns

## 8. Rollback Strategy

### 8.1. Feature Flags
- `ENABLE_AI_TOKEN_VALIDATION`: Toggle Phase 1 validation
- `ENABLE_STATE_SYNC`: Toggle Patch 1.1 synchronization
- `VALIDATION_STRICTNESS`: Configure validation levels (per-user granularity)
- `ENABLE_SAFE_MODE_FALLBACK`: Toggle fallback behavior
- `VALIDATION_SAMPLING_RATE`: Percentage of requests to validate (for gradual rollout)
- `USER_ALLOWLIST`: Enable for specific users/games first

### 8.2. Rollback Procedures
1. Disable feature flags in production
2. Monitor error rates and user impact
3. Hotfix critical issues if needed
4. Re-enable with fixes after testing

### 8.3. Data Preservation
- Keep validation logs even when disabled (with retention policy)
- Maintain token registry updates
- Preserve performance baselines
- Document lessons learned
- Backward compatibility for existing game states
- Data migration strategy if schema changes

### 8.4. Operational Considerations
- **GDPR Compliance:** 30-day retention for validation logs containing game data
- **Backward Compatibility:** Support v1 game states during transition
- **Versioning:** Token schema versioning for future updates
- **Capacity Planning:** Estimate additional compute/memory requirements
- **SLA Impact:** Ensure < 50ms latency addition to maintain SLAs

## 9. New Core Directive

*   **Directive 77.1: State-First Narrative Generation.**
*   **Description:** The canonical `CURRENT GAME STATE` is the only source of truth. It must be queried and validated against before any environmental or character state is rendered in the narrative. Narrative continuity is subordinate to state accuracy.

## 10. Deployment Plan

### 10.1. Phase 1 Deployment (Weeks 1-2)
1. Deploy AI token audit scripts in development
2. Generate token registry and gap analysis
3. Deploy validation infrastructure with feature flags disabled
4. Deploy pattern detection in CI/CD pipeline
5. Run in "shadow mode" collecting metrics

### 10.2. Phase 2 Deployment (Week 3)
1. Deploy Patch 1.1 with feature flags disabled
2. Enable in development environment first
3. Run comprehensive test suite
4. Enable in staging with monitoring
5. Gradual production rollout (10% → 50% → 100%)

### 10.3. Success Criteria
- Zero increase in error rates
- Performance within defined targets
- < 1% validation false positive rate
- Positive user engagement metrics

## 11. Ownership and Maintenance

### 11.1. Ownership Model
- **Token Registry:** AI/Prompt Engineering Team
- **Validation Infrastructure:** Backend Engineering Team
- **State Synchronization:** Game Engine Team
- **Monitoring:** DevOps/SRE Team

### 11.2. Maintenance Schedule
- Weekly review of validation failure patterns
- Monthly token registry updates
- Quarterly performance optimization review
- Ad-hoc updates for critical issues

## 12. Deployment Status

Phase 1 and Phase 2 are pending implementation. This document serves as the authoritative implementation guide for the enhanced state synchronization system. 