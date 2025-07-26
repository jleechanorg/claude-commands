# TASK-141: Token Optimization & Verification - Requirements & Implementation

## Task Overview
Optimize world content sending (currently sent with every request) and verify token measurements match actual prompts sent to LLM, with goal to reduce tokens without compromising quality.

## Current Problem Analysis
- **World Content Redundancy**: All world files sent in system instructions with every LLM request
- **Token Waste**: Same world content repeated unnecessarily across requests
- **Measurement Uncertainty**: Token counts may not reflect actual prompt sizes sent to LLM
- **Quality Concern**: Optimization must not reduce narrative quality or game functionality

## Autonomous Implementation Requirements

### Phase 1: Current State Analysis (45 min)
1. **World Content Audit:**
   - Identify all world files currently sent (world_assiah_compressed.md, etc.)
   - Measure token usage of world content vs total prompt
   - Document when/how world content is included in requests
   - Map world content inclusion patterns

2. **Token Measurement Verification:**
   - Compare estimated token counts vs actual prompt sizes in `gemini_service.py`
   - Log actual bytes/characters sent to Gemini API
   - Verify token counting algorithms match reality
   - Identify discrepancies in measurement

3. **Request Pattern Analysis:**
   - Document how often world content is sent (every request confirmed)
   - Identify which requests truly need world content
   - Map dependencies between world content and response quality

### Phase 2: World Content Optimization (1 hr)
1. **Caching Strategy Implementation:**
   - **Session-Level Caching**: Send world content only once per campaign session
   - **Context Awareness**: Include world content only when contextually relevant
   - **Smart Inclusion**: Send world sections based on current story context

2. **Content Segmentation:**
   - Break world files into logical sections (geography, history, factions, etc.)
   - Send only relevant sections based on current story context
   - Maintain world context without full content redundancy

3. **Cache Management:**
   ```python
   class WorldContentCache:
       def __init__(self):
           self.session_cache = {}
           self.sent_content = set()

       def should_include_world_content(self, session_id, content_type):
           return content_type not in self.sent_content.get(session_id, set())
   ```

### Phase 3: Token Verification System (30 min)
1. **Actual vs Estimated Logging:**
   - Log estimated token count before sending
   - Log actual characters/bytes sent to Gemini API
   - Calculate actual token usage from API response
   - Compare and report discrepancies

2. **Verification Implementation:**
   ```python
   def verify_token_measurements(prompt, estimated_tokens):
       actual_size = len(prompt.encode('utf-8'))
       api_response_tokens = response.get('usage', {}).get('prompt_tokens', 0)

       logging.info(f"Token Verification - Estimated: {estimated_tokens}, "
                   f"Actual bytes: {actual_size}, API reported: {api_response_tokens}")
   ```

3. **Measurement Accuracy:**
   - Use Gemini API's actual token reporting
   - Cross-reference with internal token counting
   - Adjust token estimation algorithms if needed

### Phase 4: Quality Preservation (45 min)
1. **Quality Metrics:**
   - Baseline response quality before optimization
   - Test narrative coherence with reduced world content
   - Verify game mechanics still function properly
   - Monitor for any degradation in AI responses

2. **Smart World Content Inclusion:**
   - **Campaign Start**: Full world content for context establishment
   - **Story Progression**: Relevant sections only
   - **Location Changes**: Geographic content when needed
   - **NPC Interactions**: Faction/character content when relevant

3. **Fallback Mechanism:**
   - Option to include full world content if quality drops
   - Dynamic content inclusion based on context complexity
   - User/admin toggle for full vs optimized content

## Implementation Strategy

### Token Reduction Approaches:
1. **Session Caching**: Send world content once per session (highest impact)
2. **Contextual Inclusion**: Only send relevant world sections
3. **Progressive Loading**: Build world context incrementally
4. **Compression**: Use more efficient world content encoding

### Verification Points:
1. **Pre-Request**: Log estimated tokens and prompt size
2. **Post-Request**: Log actual tokens from API response
3. **Comparison**: Calculate and report measurement accuracy
4. **Trending**: Track token usage patterns over time

### Files to Modify:
1. **`mvp_site/gemini_service.py`** - Add caching and verification
2. **World content inclusion logic** - Optimize sending patterns
3. **Logging systems** - Add token verification
4. **Session management** - Track world content sent per session

## Implementation Details

### World Content Caching:
```python
class OptimizedWorldContent:
    def __init__(self):
        self.session_world_content = {}

    def get_world_content_for_request(self, session_id, context):
        if session_id not in self.session_world_content:
            # First request - send full world content
            self.session_world_content[session_id] = True
            return get_full_world_content()
        else:
            # Subsequent requests - minimal or contextual content
            return get_contextual_world_content(context)
```

### Token Verification:
```python
def send_request_with_verification(prompt, estimated_tokens):
    # Log before sending
    actual_prompt_size = len(prompt.encode('utf-8'))
    log_token_comparison("pre_request", estimated_tokens, actual_prompt_size)

    # Send to API
    response = gemini_api.call(prompt)

    # Log actual usage
    api_reported_tokens = response.usage.prompt_tokens
    log_token_comparison("post_request", estimated_tokens, api_reported_tokens)

    return response
```

## Success Criteria
- [ ] World content sent only once per session (or contextually)
- [ ] Token usage reduced by 30-50% without quality loss
- [ ] Token measurements match actual prompt sizes sent to LLM
- [ ] Verification logging shows actual vs estimated token usage
- [ ] Narrative quality maintained at baseline levels
- [ ] Game mechanics function correctly with optimized content
- [ ] Session-based caching works reliably
- [ ] Fallback to full content available if needed

## Measurement Targets
- **Token Reduction**: 30-50% reduction in total tokens per session
- **Measurement Accuracy**: <5% difference between estimated and actual tokens
- **Quality Maintenance**: No degradation in narrative coherence or game functionality
- **Performance**: No increase in response latency

## Dependencies
- Session management system
- World content file structure
- Gemini API token reporting
- Logging infrastructure

## Estimated Time: 3 hours
- Current state analysis: 45 minutes
- Optimization implementation: 1 hour
- Verification system: 30 minutes
- Quality preservation: 45 minutes

## Testing Plan
1. **Baseline Measurement**: Document current token usage and quality
2. **Optimization Testing**: Verify reduced token usage maintains quality
3. **Verification Testing**: Confirm token measurements are accurate
4. **Session Testing**: Test caching across multiple requests
5. **Quality Testing**: Compare response quality before/after optimization
6. **Edge Case Testing**: Test with complex scenarios and world interactions

## Risk Mitigation
1. **Quality Monitoring**: Continuous comparison with baseline quality
2. **Gradual Rollout**: Test optimization on subset of requests first
3. **Rollback Plan**: Ability to revert to full world content if needed
4. **User Feedback**: Monitor for any reported quality degradation
