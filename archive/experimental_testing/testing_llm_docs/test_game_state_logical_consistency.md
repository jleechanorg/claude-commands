# Test: Game State Logical Consistency Validation

## Test ID
llm-meta-game-state-consistency

## Status
- [ ] RED (failing)
- [ ] GREEN (passing)
- [ ] REFACTORED

## Description
Multi-LLM validation that game state transitions maintain logical consistency and D&D rule compliance. This test catches semantic errors that traditional unit tests miss—when the code works but the content doesn't make sense.

## Pre-conditions
- Flask backend server running on `http://localhost:5005`
- Test mode enabled with bypass authentication
- Access to Claude, GPT-4, and Gemini APIs for cross-validation
- Sample game states with established facts, character stats, and world rules

## Test Matrix

| Scenario Type | Test Complexity | Validation Focus |
|---------------|----------------|------------------|
| **Combat** | Simple attack → damage calculation | Stat consistency, rule compliance |
| **Social** | NPC interaction → relationship change | Character consistency, world logic |
| **Magic** | Spell casting → world effect | Rule adherence, consequence logic |
| **Exploration** | Location change → new discoveries | World coherence, continuity |

## Test Steps

### Step 1: Generate Test Game State
1. **Create baseline state**:
   ```json
   {
     "character": {
       "name": "Lyra",
       "class": "Wizard",
       "level": 3,
       "hp": 18,
       "max_hp": 18,
       "spell_slots": {"1st": 4, "2nd": 2},
       "known_spells": ["Magic Missile", "Shield", "Misty Step"]
     },
     "world_facts": [
       "The Crystal Tower is sealed by ancient magic",
       "Lord Vex rules the northern territories",
       "Magic is forbidden in the city of Ironhold"
     ],
     "current_location": "Crystal Tower entrance",
     "active_effects": ["Mage Armor (AC 13+Dex)"]
   }
   ```

### Step 2: Execute Player Action
1. **Submit action**: "I cast Magic Missile at the tower's seal"
2. **Get AI response** from your Gemini system
3. **Capture state changes** in the response

### Step 3: Multi-LLM Cross-Validation

#### Claude Validation
**Prompt**:
```
You are a D&D 5e rules expert. Analyze this game state transition:

BEFORE: {previous_state}
ACTION: {player_action}
AI RESPONSE: {ai_response}
AFTER: {new_state}

Rate logical consistency 1-10 and answer:
1. Does the response contradict any established world facts?
2. Are character stat changes mathematically correct?
3. Does the magical effect follow D&D 5e rules?
4. Are there any logical contradictions?

Provide specific examples of any issues found.
```

#### GPT-4 Validation
**Prompt**:
```
Check this D&D game sequence for rule compliance:

{game_sequence_data}

Validate:
- Spell slot usage (did it decrement correctly?)
- Damage calculations (if any)
- Action economy (bonus actions, reactions)
- Save DC calculations
- Range and targeting rules

Rate rule compliance 1-10. List specific rule violations.
```

#### Gemini Cross-Check
**Prompt**:
```
Review this response from your own model family:

{ai_response_to_validate}

As an objective evaluator:
1. Rate world coherence 1-10
2. Check for internal contradictions
3. Verify cause-and-effect logic
4. Assess narrative quality

What would you improve about this response?
```

### Step 4: Consensus Analysis
1. **Aggregate scores** from all three LLMs
2. **Flag disagreements** >2 points between models
3. **Generate improvement suggestions** for failed validations
4. **Log patterns** for systematic improvement

## Expected Results

**PASS Criteria**:
- ✅ All LLMs score consistency ≥8/10 OR provide actionable feedback
- ✅ No rule violations detected by any validator
- ✅ World facts remain consistent after state transition
- ✅ Mathematical calculations are correct (HP, spell slots, etc.)

**FAIL Indicators**:
- ❌ Any LLM detects logical contradictions
- ❌ Rule violations found (spell slots, damage calculations)
- ❌ Character stats inconsistent with actions taken
- ❌ World facts contradicted by AI response
- ❌ Consensus score <7/10 average

## Bug Analysis

**Root Cause Categories**:
1. **Prompt Engineering**: System prompts don't enforce consistency
2. **State Management**: Game state not properly passed to AI
3. **Rule Knowledge**: AI model lacks D&D 5e expertise
4. **Context Window**: Long sessions lose important details

**Fix Locations**:
- `mvp_site/prompts/`: Update system prompts with consistency rules
- `mvp_site/game_state.py`: Enhance state validation before AI calls
- `mvp_site/gemini_service.py`: Add rule compliance checks

## Implementation Notes

### Execution Protocol
```python
# Run validation on every AI response
def validate_game_state_consistency(before_state, action, ai_response, after_state):
    validators = {
        'claude': validate_with_claude,
        'gpt4': validate_with_gpt4,
        'gemini': validate_with_gemini
    }

    scores = {}
    issues = {}

    for validator_name, validator_func in validators.items():
        result = validator_func(before_state, action, ai_response, after_state)
        scores[validator_name] = result.score
        issues[validator_name] = result.issues

    avg_score = sum(scores.values()) / len(scores)
    disagreement = max(scores.values()) - min(scores.values())

    return {
        'pass': avg_score >= 8 and disagreement < 3,
        'scores': scores,
        'issues': issues,
        'needs_review': disagreement >= 2
    }
```

### Integration Points
- **Pre-serve validation**: Run before sending AI response to user
- **Batch validation**: Run on stored game sessions for pattern analysis
- **Real-time feedback**: Improve prompts based on validation failures

### Success Metrics
- **Consistency Score**: Average validator rating ≥8.0
- **Disagreement Rate**: <10% of responses flagged for review
- **Issue Detection**: Catch rule violations before users see them
- **Learning Loop**: Validation failures improve system prompts

This test specifically targets the semantic dimension of your 83.6% failure rate—catching when responses are syntactically correct but semantically nonsensical or rule-breaking.
