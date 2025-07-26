# GeminiResponse Architecture Refactor Scratchpad

## Current State Analysis

### Problems with Current Architecture:
1. **Scattered Parsing Logic**:
   - `narrative_response_schema.py`: parse_structured_response()
   - `gemini_service.py`: _parse_gemini_response(), _process_structured_response()
   - `robust_json_parser.py`: parse_llm_json_response()
   - Planning block parsing in _validate_and_enforce_planning_block()

2. **Multiple API Calls**:
   - First call: Get story response
   - Second call (conditional): Generate planning block if missing
   - This is inefficient and increases latency/cost

3. **Inconsistent Response Handling**:
   - Different parsing strategies in different places
   - No single source of truth
   - Hard to maintain and debug

## Proposed Architecture

### Core Design Principles:
1. **Single Source of Truth**: GeminiResponse owns ALL response parsing
2. **Single API Call**: Planning blocks requested in initial prompt
3. **Clear Separation**: Parser logic separate from business logic
4. **Robust Error Handling**: Specific exceptions, graceful fallbacks

### Class Structure:

```python
# constants.py (or gemini_constants.py)
class GeminiConstants:
    # Response types
    RESPONSE_TYPE_STORY = "story"
    RESPONSE_TYPE_INITIAL = "initial"
    RESPONSE_TYPE_GOD_MODE = "god_mode"

    # JSON field names
    FIELD_NARRATIVE = "narrative"
    FIELD_STATE_UPDATES = "state_updates"
    FIELD_ENTITIES_MENTIONED = "entities_mentioned"
    FIELD_LOCATION_CONFIRMED = "location_confirmed"
    FIELD_DEBUG_INFO = "debug_info"
    FIELD_GOD_MODE_RESPONSE = "god_mode_response"

    # Planning block
    PLANNING_BLOCK_HEADER = "--- PLANNING BLOCK ---"
    PLANNING_BLOCK_PATTERN = r'\n\n--- PLANNING BLOCK ---\n(.*?)$'

    # Debug tags
    DEBUG_TAG_DM_NOTES = "dm_notes"
    DEBUG_TAG_DICE_ROLLS = "dice_rolls"
    DEBUG_TAG_RESOURCES = "resources"
    DEBUG_TAG_STATE_RATIONALE = "state_rationale"

# response_parser.py
class ResponseParser:
    """Handles all response parsing logic"""

    def parse_raw_response(self, raw_text: str) -> ParsedResponse:
        """Main entry point for parsing any response"""
        # 1. Try JSON parsing first
        # 2. Fall back to text parsing
        # 3. Extract components

    def _parse_json_response(self, text: str) -> Optional[dict]:
        """Parse JSON with all our fallback strategies"""
        # Use robust_json_parser logic here

    def _extract_planning_block(self, text: str) -> tuple[str, Optional[str]]:
        """Extract planning block from narrative"""
        # Returns (narrative_without_block, planning_block)

    def _detect_debug_tags(self, debug_info: dict) -> dict[str, bool]:
        """Detect which debug tags have content"""

# gemini_response.py
class GeminiResponse:
    """Public API for Gemini responses"""

    def __init__(self):
        self._parser = ResponseParser()
        self._raw_response = None
        self._parsed_data = None
        self._response_type = None

    @classmethod
    def create(cls, raw_response_text: str, response_type: str = None) -> 'GeminiResponse':
        """Factory method - single way to create responses"""

    def get_narrative(self) -> str:
        """Get clean narrative text (no JSON, no planning block)"""

    def get_planning_block(self) -> Optional[str]:
        """Get planning block if present"""

    def get_full_narrative(self) -> str:
        """Get narrative + planning block (for story display)"""
```

## Implementation Steps

### Phase 1: Prompt Modification
1. Update `game_state_instruction.txt`:
   ```
   IMPORTANT: For all story mode responses, you MUST end with a planning block:

   [Your narrative response here]

   --- PLANNING BLOCK ---
   What would you like to do?
   1. **[Action1_1]:** Description
   2. **[Action2_2]:** Description
   3. **[Other_3]:** Describe a different action
   ```

2. Update other prompts to ensure planning blocks are included

### Phase 2: Constants Definition
1. Create `gemini_constants.py` with all string constants
2. Update all files to use constants instead of hardcoded strings

### Phase 3: ResponseParser Implementation
1. Move all parsing logic from:
   - `narrative_response_schema.parse_structured_response()`
   - `robust_json_parser.parse_llm_json_response()`
   - Planning block extraction logic

2. Implement specific exception handling:
   ```python
   try:
       return json.loads(text)
   except json.JSONDecodeError as e:
       # Handle malformed JSON
   except ValueError as e:
       # Handle value errors
   except (KeyError, TypeError) as e:
       # Handle missing/wrong type fields
   ```

### Phase 4: GeminiResponse Refactor
1. Remove `_parse_gemini_response()` from gemini_service
2. Update GeminiResponse.create() to handle all parsing
3. Ensure backward compatibility with existing code

### Phase 5: Simplify gemini_service.py
1. Remove parsing logic
2. Keep only:
   - API calling
   - Entity validation
   - Retry logic
   - Business logic

## Benefits of This Architecture

1. **Single API Call**: Planning blocks included in first response
2. **Maintainability**: All parsing in one place
3. **Testability**: ResponseParser can be unit tested independently
4. **Flexibility**: Easy to add new response types
5. **Performance**: Fewer API calls, consistent parsing

## Potential Challenges

1. **Prompt Reliability**: Need to ensure LLM consistently includes planning blocks
2. **Backward Compatibility**: Existing data might not have planning blocks
3. **Testing**: Need comprehensive tests for all parsing edge cases

## Migration Strategy

1. **Parallel Implementation**: Build new classes without breaking existing code
2. **Gradual Migration**: Update one response type at a time
3. **Feature Flag**: Could use a flag to switch between old/new parsing
4. **Comprehensive Testing**: Test with real API responses

## Questions to Resolve

1. **Planning Block Format**: Should we enforce a specific format/structure?
2. **Error Response**: How should GeminiResponse handle complete parsing failures?
3. **Caching**: Should parsed responses be cached within GeminiResponse?
4. **Validation**: Should schema validation be part of ResponseParser?

## Additional Considerations

### Response Versioning
- Consider adding a version field to track response format changes
- Helps with backward compatibility

### Performance Optimization
- ResponseParser will be called frequently
- Need efficient parsing strategies
- Consider caching compiled regexes

### Logging Strategy
- Maintain operational logging without debug noise
- Log parsing failures and recovery attempts
- Make logging level configurable

### Error Recovery
- What if LLM doesn't include planning block despite instructions?
- Graceful fallback to current behavior (generate separately)
- Clear error messages for debugging

### Comprehensive Testing
Test cases needed:
- Perfect JSON with planning block
- JSON without planning block (fallback test)
- Malformed JSON (various types)
- Plain text responses
- Responses with embedded JSON in narrative
- Mixed format responses
- Empty responses
- Very large responses

### Response Type Detection
Options:
1. Always require explicit response_type parameter
2. Auto-detect based on content patterns
3. Hybrid: default type with auto-detection override

Recommendation: Explicit types for clarity

## Next Steps

1. Get approval on overall architecture
2. Create gemini_constants.py
3. Implement ResponseParser with comprehensive tests
4. Update prompts to include planning blocks
5. Refactor GeminiResponse
6. Update gemini_service.py
7. Run comprehensive tests
8. Update documentation

## Code Review Checklist
- [ ] All hardcoded strings moved to constants
- [ ] Specific exception handling (no broad catches)
- [ ] Comprehensive unit tests
- [ ] Performance benchmarks
- [ ] Backward compatibility verified
- [ ] Documentation updated
- [ ] No excessive logging
