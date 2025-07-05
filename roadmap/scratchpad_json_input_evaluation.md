# Evaluation: JSON Input Format for System-to-LLM Communication

## Current State
- **Output**: LLM responses use strict JSON format (implemented in this PR)
- **Input**: System sends text-based messages with structured but non-JSON format

## Proposal: Convert System Input to JSON Format

### Example of Current vs Proposed Input Format

**Current (Text-based):**
```
You are in the Tavern of the Silver Moon. 

Current entities: Bartender (Level 3), Guard Captain (Level 5)

Player HP: 15/20
Location: Tavern of the Silver Moon

Player says: "I'd like to speak with the captain"
```

**Proposed (JSON-based):**
```json
{
  "context": {
    "location": "Tavern of the Silver Moon",
    "entities_present": [
      {"name": "Bartender", "level": 3, "status": "friendly"},
      {"name": "Guard Captain", "level": 5, "status": "neutral"}
    ],
    "player_state": {
      "hp_current": 15,
      "hp_max": 20,
      "conditions": []
    }
  },
  "player_action": {
    "type": "dialogue",
    "content": "I'd like to speak with the captain"
  },
  "system_metadata": {
    "turn_number": 42,
    "mode": "STORY_MODE"
  }
}
```

## Pros of Implementing in This PR

### 1. **Complete JSON Symmetry**
- Input and output would both use JSON
- Creates a consistent communication protocol
- Reduces cognitive load for understanding the system

### 2. **Leverages Current Context**
- Team is already deep in JSON-related fixes
- Fresh understanding of JSON parsing/validation
- Natural extension of current work

### 3. **Prevents Future Rework**
- Avoids having to revisit all prompt generation code later
- No risk of introducing new bugs in stable code
- One migration instead of two

### 4. **Better Error Handling**
- JSON schema validation on both ends
- Clear field requirements
- Type safety for all data

### 5. **Improved Testability**
- Easier to mock and validate inputs
- Structured test data generation
- Clear contract between system and LLM

## Cons of Implementing in This PR

### 1. **Scope Creep**
- PR already includes multiple significant changes
- Risk of introducing new bugs
- Harder to review and test comprehensively

### 2. **Time Investment**
- Requires updating all prompt generation code
- Need to modify game_state serialization
- Update all existing tests

### 3. **LLM Context Usage**
- JSON typically uses more tokens than natural text
- Could reduce available context for narrative
- May impact response quality

### 4. **Breaking Change Risk**
- Current prompts are working well
- Risk of degrading LLM understanding
- May need extensive prompt engineering

### 5. **Review Complexity**
- PR becomes much larger
- Harder for reviewers to validate
- Mixes bug fixes with architectural changes

## Pros of Implementing Later

### 1. **Focused PR**
- Current PR stays focused on JSON output fixes
- Easier to review and validate
- Clear separation of concerns

### 2. **Incremental Progress**
- Can test JSON output thoroughly first
- Learn from output implementation
- Apply lessons to input design

### 3. **Performance Baseline**
- Establish metrics with current approach
- Measure JSON output impact first
- Make informed decision on input format

### 4. **Risk Management**
- Smaller, safer changes
- Easier rollback if issues arise
- Preserve working functionality

## Cons of Implementing Later

### 1. **Technical Debt**
- Temporary asymmetry in protocols
- Will need documentation for both formats
- Confusion for new developers

### 2. **Double Migration**
- Touch same code files twice
- Risk of merge conflicts
- More total development time

### 3. **Inconsistent Testing**
- Need different test strategies for input/output
- Harder to create end-to-end tests
- More complex test infrastructure

## Recommendation

**Implement JSON input format in a FUTURE PR** for these reasons:

1. **Current PR Scope**: Already includes JSON output, resource tracking migration, protocol consolidation - adding input format risks making it unwieldy

2. **Risk/Reward**: Current text-based input is working well; changing it now adds risk without urgent benefit

3. **Learning Opportunity**: Can analyze JSON output performance/token usage first to inform input design

4. **Clean Architecture**: Better to have two focused PRs than one mega-PR

5. **Reversibility**: Easier to rollback or adjust approach with separate implementations

## Suggested Future Approach

1. **Phase 1** (This PR): JSON output only
2. **Phase 2** (Next PR): 
   - Design comprehensive input schema
   - Include turn history format
   - Consider compression strategies
3. **Phase 3**: Migration tools and backwards compatibility
4. **Phase 4**: Performance optimization and token reduction

## Technical Considerations for Future Implementation

- Design schema to minimize token usage (short keys, efficient structure)
- Consider hybrid approach (JSON for state, text for narrative context)
- Implement gradual rollout with feature flags
- Create migration tools for existing save games
- Benchmark token usage before/after