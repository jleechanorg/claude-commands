# JSON Input Schema Implementation Milestones

## Context & Learning from PR #565

**Core Concept is Valuable**: The idea of structured JSON input to LLMs is sound - we already specify structured output formats successfully, so structured input follows the same logical pattern.

**Previous Implementation Issues**:
- ❌ **Too complex upfront**: 1165 lines of implementation + 1343 lines of tests (117% test coverage)
- ❌ **Mixed concerns**: Combined schema implementation with test fixes and GitHub Actions changes
- ❌ **No value validation**: Built complete abstraction before proving basic concept
- ❌ **Feature flag hell**: Created permanent dual code paths without clear migration strategy
- ❌ **Standards violations**: Added non-essential files to main branch, violated file addition protocol

**Key Learning**: Prove value incrementally before building complexity.

## Problem Statement

**Current State**: Text-based prompts with inconsistent GameState serialization
- Prompt building concatenates strings with ad-hoc formatting
- GameState data serialized differently across interaction types
- No standardized context delivery to LLM

**Opportunity**: Structured JSON input like structured JSON output
- More predictable LLM processing of context
- Consistent data delivery format
- Easier debugging and monitoring
- Better context organization

**Success Pattern**: Our structured output formats (narrative responses, planning blocks) work well
**Logical Extension**: Apply same structure to input side

## Staged Implementation Plan

### Milestone 1: Research & Baseline (1-2 days)

**Objective**: Establish baseline metrics for current prompt effectiveness and document specific improvement opportunities.

**Deliverables**:
- Metrics document showing current LLM response consistency, quality, processing time
- Specific examples of prompt formatting inconsistencies
- Clear success criteria for structured input

**Technical Approach**:
- Use existing logging/analytics to measure current system
- No code changes, pure measurement and analysis
- Focus on "continue story" interaction as primary use case

**Success Criteria**:
- Baseline metrics established with concrete numbers
- Specific problems documented with examples
- Clear improvement targets defined (e.g., 10% better consistency)

**Failure Criteria**: If no measurable problems exist, stop here - don't solve non-problems.

**Time Limit**: 2 days maximum

---

### Milestone 2: MVP Schema (2-3 days)

**Objective**: Implement minimal viable structured input for single interaction type and measure improvement.

**Deliverables**:
- Simple function: `gamestate_to_structured_input(game_state, story_context, user_input) -> dict`
- A/B test setup for "continue story" interaction
- Metrics showing improvement vs baseline

**Technical Approach**:
- Single 30-50 line function, no complex schemas
- Feature flag: `USE_STRUCTURED_INPUT_CONTINUE_STORY = True`
- A/B test: 25% users get structured input, 75% get current prompts
- JSON structure with **8 core fields** from existing prompt data

**Required JSON Schema Fields** (matching current prompt components):
1. **`checkpoint`**: Extract from existing checkpoint_block (sequence_id, location, missions)
2. **`core_memories`**: Use existing core_memories_summary array
3. **`reference_timeline`**: Convert existing sequence_id_list_string to array
4. **`current_game_state`**: Use existing GameState.to_dict() serialization
5. **`entity_manifest`**: Use existing entity tracking data (present_entities, required_mentions, location)
6. **`timeline_log`**: Convert existing timeline_log_string to structured array
7. **`current_input`**: Structure user_input with actor/mode/text fields
8. **`system_context`**: Add meta info (mode, debug_enabled, session_number, turn_number)

**Implementation Guidelines**:
- Use existing patterns (Pydantic/dict, not TypedDict)
- No separate schema files - add to existing modules
- No builder patterns - simple serialization only
- Leverage ALL current prompt components in structured format

**Success Criteria**:
- ≥10% improvement in response consistency or quality
- No degradation in response time
- No user experience issues

**Failure Criteria**: No measurable improvement → investigate or abandon

**Rollback Plan**: Remove feature flag, delete function

**Time Limit**: 3 days maximum
**Size Limit**: 50 lines of implementation code maximum

---

### Milestone 3: Selective Expansion (3-5 days)

**Conditional**: Only proceed if Milestone 2 shows clear value

**Objective**: Expand structured input to 2-3 additional interaction types where Milestone 2 showed benefit.

**Deliverables**:
- Expand structured input to character creation, god mode interactions
- Refined JSON structure based on Milestone 2 learnings
- Consistent improvement metrics across interaction types

**Technical Approach**:
- Enhance existing function with additional context types
- Gradual rollout: 25% → 50% → 75% user adoption
- Focus only on interaction types where improvement was proven

**Field Adaptations by Interaction Type**:
- **Character Creation**: `current_game_state` simplified, `timeline_log` minimal, `entity_manifest` empty
- **God Mode**: Enhanced `system_context` with debug info, `current_input` with special god mode fields
- **Campaign Setup**: Different `checkpoint` structure, `core_memories` from previous sessions

**Schema Consistency**:
- All 8 fields present in every interaction (may be empty/null)
- Field structure remains consistent across interaction types
- Only field contents vary, not field names or types

**Success Criteria**:
- Consistent improvement across multiple interaction types
- No technical debt or complexity creep
- Clear user benefit measurable

**Failure Criteria**: Mixed results → focus only on what works, abandon what doesn't

**Time Limit**: 5 days maximum
**Size Limit**: Additional 50-100 lines maximum

---

## Implementation Guidelines

### Code Standards
1. **No complex schemas**: Use simple dict structures or existing Pydantic
2. **No TypedDict**: Avoid new validation frameworks when Pydantic exists
3. **No builder patterns**: Simple serialization functions only
4. **Single responsibility**: Each function does one thing
5. **Feature flags for rollout**: Not for permanent dual paths

### Required JSON Schema Implementation
**All implementations must include these 8 fields**:

```python
def create_structured_input(game_state, story_context, user_input, mode):
    return {
        "checkpoint": {
            "sequence_id": extract_current_sequence_id(),
            "location": game_state.world_data.get('current_location_name'),
            "missions": extract_active_missions()
        },
        "core_memories": extract_core_memories_array(),
        "reference_timeline": convert_sequence_ids_to_array(),
        "current_game_state": game_state.to_dict(),
        "entity_manifest": {
            "present_entities": get_present_entities(),
            "required_mentions": get_required_mentions(),
            "location": current_location
        },
        "timeline_log": convert_timeline_to_structured_array(),
        "current_input": {
            "actor": "player",
            "mode": mode,
            "text": user_input
        },
        "system_context": {
            "mode": mode,
            "debug_enabled": is_debug_mode(),
            "session_number": get_session_number(),
            "turn_number": get_turn_number()
        }
    }
```

**Field Mapping from Current System**:
- `checkpoint` ← existing `checkpoint_block` parsing
- `core_memories` ← existing `core_memories_summary`
- `reference_timeline` ← existing `sequence_id_list_string` conversion
- `current_game_state` ← existing `GameState.to_dict()`
- `entity_manifest` ← existing entity tracking data
- `timeline_log` ← existing `timeline_log_string` parsing
- `current_input` ← wrap existing user input with metadata
- `system_context` ← new meta information aggregation

### File Organization
1. **No separate schema files**: Put functions in existing modules (gemini_service.py)
2. **No documentation pollution**: Keep planning docs in roadmap/ until code is ready
3. **Proportional testing**: 30-50% test coverage, not 117%
4. **Integration over unit**: Test behavior, not structure

### Review Gates
1. **Size limits enforced**: Hard stop at line count limits
2. **Value validation required**: Metrics must show improvement
3. **Standards compliance**: Follow CLAUDE.md file addition protocol
4. **Clean git history**: Single-purpose commits, no merge noise

## Risk Mitigation

### Risk: No Measurable Improvement
- **Detection**: Clear metrics and A/B testing at each stage
- **Response**: Immediate stop, investigate or abandon
- **Prevention**: Conservative success criteria

### Risk: Complexity Creep
- **Detection**: Hard line limits (50 lines per milestone)
- **Response**: Rollback to previous milestone
- **Prevention**: Code review requirements, size gates

### Risk: User Experience Degradation
- **Detection**: A/B testing with small user percentages
- **Response**: Immediate rollback, fix, or abandon
- **Prevention**: Gradual rollout, monitoring

### Risk: Technical Debt
- **Detection**: Code review for abstraction levels
- **Response**: Simplify or rollback
- **Prevention**: Simple implementation patterns, no complex abstractions

## Metrics & Measurement

### Baseline Metrics (Milestone 1)
- Response consistency score (human evaluation)
- Response quality metrics (relevance, coherence)
- Processing time (API call to response)
- Context understanding accuracy

### Success Metrics (Milestones 2-3)
- ≥10% improvement in consistency
- No degradation in response time
- No increase in user-reported issues
- Maintainable code complexity

### Monitoring
- A/B test statistical significance
- User feedback sentiment
- System performance impact
- Development velocity impact

## Decision Framework

### Go/No-Go Criteria
Each milestone ends with explicit decision:
- **GO**: Clear metrics improvement + no major issues
- **NO-GO**: No improvement OR significant issues OR excessive complexity

### Stakeholder Alignment
- Technical lead approval for each milestone
- Product owner sign-off on success criteria
- Clear escalation path for disputes

### Documentation Requirements
- Decision rationale documented
- Metrics and learnings captured
- Next milestone planning or project closure

---

## Timeline & Resources

**Total Estimated Time**: 6-10 days across 3 milestones
**Resource Requirement**: Single developer, part-time
**Dependencies**: Analytics/logging access for baseline metrics

**Critical Success Factors**:
1. Strict adherence to milestone gates
2. Clear go/no-go decision making
3. Simple implementation approach
4. Value validation before complexity

This staged approach ensures we either build something valuable or learn quickly why structured input isn't needed - both are good outcomes.