# Implement JSON Input Format for System-to-LLM Communication

## Task Metadata
- **Status**: not_started
- **Priority**: high
- **Estimated Hours**: 4-6
- **Dependencies**:
  - PR: Implement JSON output format for narrative and planning systems (must be merged first)
  - Current narrative system implementation
  - Current planning system implementation

## Objective
Implement structured JSON input format for system-to-LLM communication to replace the current unstructured text-based approach. This will provide a consistent, machine-readable format for passing context, state, and instructions to the LLM.

## Background
Currently, the system passes information to the LLM using unstructured text in system prompts. This approach is prone to parsing errors, inconsistent formatting, and makes it difficult to maintain complex state. A structured JSON input format will provide:
- Consistent data structure
- Type safety and validation
- Easier state management
- Better debugging capabilities
- Foundation for more complex interactions

## Acceptance Criteria
1. [ ] Define JSON schema for input format supporting:
   - Game state (turn number, active players, resources)
   - Previous actions and their outcomes
   - Available actions and constraints
   - Context from previous turns
   - System instructions and parameters

2. [ ] Implement JSON input formatting in narrative system:
   - Convert current text-based prompts to JSON structure
   - Maintain backward compatibility during transition
   - Add validation for input structure

3. [ ] Implement JSON input formatting in planning system:
   - Structure planning context and constraints as JSON
   - Include action history and outcomes
   - Add validation for planning-specific fields

4. [ ] Update system prompts to parse JSON input:
   - Modify prompts to expect and parse JSON structure
   - Ensure LLM understands the schema
   - Add examples in prompts

5. [ ] Add comprehensive testing:
   - Unit tests for JSON formatting
   - Integration tests with LLM
   - Validation tests for schema compliance
   - Error handling tests

6. [ ] Update documentation:
   - Document JSON schema
   - Provide migration guide
   - Update API documentation

## Technical Details

### Proposed JSON Schema Structure
```json
{
  "version": "1.0",
  "system": {
    "mode": "narrative|planning",
    "instructions": "...",
    "parameters": {}
  },
  "game_state": {
    "turn": 1,
    "phase": "planning|narrative",
    "active_player": "player_id",
    "resources": {},
    "flags": {}
  },
  "context": {
    "previous_actions": [],
    "narrative_history": [],
    "current_objectives": []
  },
  "request": {
    "type": "generate_narrative|create_plan|evaluate_action",
    "parameters": {},
    "constraints": []
  }
}
```

### Implementation Approach
1. Start with narrative system as proof of concept
2. Extend to planning system
3. Gradual migration with feature flags
4. Maintain backward compatibility during transition

## Success Metrics
- All tests passing
- No regression in system functionality
- JSON validation success rate > 99%
- LLM response quality maintained or improved
- Clear documentation and examples

## Notes
- Coordinate with JSON output format implementation for consistency
- Consider using JSON Schema for validation
- Plan for gradual rollout to minimize disruption
- Ensure prompts are updated to handle both formats during transition
