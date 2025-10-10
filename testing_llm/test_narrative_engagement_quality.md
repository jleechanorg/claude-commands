# Test: Narrative Engagement Quality Cross-Validation

> **Execution Command:** `/testllm` - LLM-Driven Test Execution Command  
> **Protocol Notice:** This is an executable test that must be run via the `/testllm` workflow with full agent orchestration.

## Test ID
llm-meta-narrative-quality

## Status
- [ ] RED (failing)
- [ ] GREEN (passing)
- [ ] REFACTORED

## Description
Multi-model assessment of AI-generated narrative responses for engagement, appropriateness, and story progression. This test catches the "technically correct but boring/inappropriate" responses that kill user engagement.

## Pre-conditions
- Flask backend generating AI responses via Gemini
- Access to Claude, GPT-4, and Gemini APIs for cross-validation
- Test scenarios covering major D&D interaction types
- Baseline quality thresholds established from user feedback

## Test Matrix

| Scenario Type | Test Input | Quality Dimensions | Min Score |
|---------------|------------|-------------------|-----------|
| **Combat** | "I attack the dragon with my sword" | Excitement ≥8, D&D accuracy ≥9, Pacing ≥7 | 8.0 avg |
| **Social** | "I try to convince the guard to let us pass" | Dialogue quality ≥8, Character voice ≥8, Believability ≥7 | 7.7 avg |
| **Exploration** | "I examine the mysterious glowing rune" | Descriptive detail ≥8, Atmosphere ≥8, Discovery ≥7 | 7.7 avg |
| **Puzzle** | "I study the ancient mechanism" | Clarity ≥9, Logic ≥8, Intrigue ≥7 | 8.0 avg |
| **Horror** | "I enter the abandoned temple" | Tension ≥8, Atmosphere ≥9, Appropriate fear ≥7 | 8.0 avg |

## Test Steps

### Step 1: Generate Test Scenarios
1. **Combat Scenario**:
   ```json
   {
     "context": "Lvl 3 party facing young red dragon in lair",
     "player_action": "I charge forward and attack with my greatsword",
     "character": "Human Fighter, reckless but brave",
     "stakes": "Dragon has kidnapped village children"
   }
   ```

2. **Social Scenario**:
   ```json
   {
     "context": "Trying to enter restricted noble district",
     "player_action": "I approach the guard with confidence",
     "character": "Half-elf Bard, charming but suspicious past",
     "stakes": "Need to reach the mansion before midnight"
   }
   ```

### Step 2: Generate AI Response
1. **Submit scenario** to your Gemini system
2. **Capture full response** including narrative, dice rolls, state changes
3. **Record response time** and context usage

### Step 3: Multi-LLM Quality Evaluation

#### Claude Evaluation (Engagement Focus)
**Prompt**:
```
You are a professional D&D Dungeon Master reviewer. Rate this AI response:

SCENARIO: {scenario_context}
PLAYER ACTION: {player_action}
AI RESPONSE: {ai_response}

Rate 1-10 for each dimension:

ENGAGEMENT: How exciting/compelling is this for a D&D player?
- Does it make the player want to continue?
- Are there interesting consequences or developments?
- Does it respect player agency?

APPROPRIATENESS: Suitable tone and content for fantasy RPG?
- Age-appropriate content (teen+)?
- Consistent with D&D tone and style?
- Respects table atmosphere?

PROGRESSION: Does this advance the story meaningfully?
- Does it move the narrative forward?
- Are there clear next steps for players?
- Does it build on established story elements?

Provide specific examples for scores <8.
```

#### GPT-4 Evaluation (Technical Quality Focus)
**Prompt**:
```
Evaluate this D&D AI response for technical quality:

{ai_response_data}

Rate 1-10:

RULE ACCURACY: D&D 5e mechanical correctness
- Proper dice notation and calculations
- Correct action economy usage
- Appropriate difficulty classes

NARRATIVE CRAFT: Writing quality and structure
- Clear, engaging prose
- Good pacing and rhythm
- Vivid but not overwrought descriptions

CHARACTER VOICE: NPC and world consistency
- NPCs have distinct personalities
- World feels lived-in and consistent
- Player character agency respected

List specific improvements for scores <8.
```

#### Gemini Self-Assessment (Meta-Analysis)
**Prompt**:
```
You are reviewing a response from your own model family. Be objectively critical:

ORIGINAL RESPONSE: {ai_response}

Self-evaluate:
1. COHERENCE (1-10): Internal logic and flow
2. CREATIVITY (1-10): Originality and interesting elements
3. PLAYER FOCUS (1-10): Serves player experience over exposition
4. EFFICIENCY (1-10): Conveys information clearly without bloat

What are this response's biggest weaknesses?
How would you rewrite the weakest part?
```

### Step 4: Cross-Validation Analysis
1. **Aggregate scores** across all dimensions and models
2. **Identify consensus issues** (2+ models flag same problem)
3. **Flag high-disagreement cases** (>3 point spread) for human review
4. **Generate improvement prompts** for systematic enhancement

## Expected Results

**PASS Criteria**:
- ✅ Average score ≥7.5 across all dimensions
- ✅ No single dimension scores <6.0
- ✅ Models agree within 2-point range on overall quality
- ✅ Response advances story without railroading player

**FAIL Indicators**:
- ❌ Any dimension scores <5.0 (major quality issue)
- ❌ Average score <7.0 (generally poor quality)
- ❌ Models disagree by >3 points (inconsistent quality)
- ❌ Response fails to respect player agency
- ❌ Inappropriate content or tone for D&D setting

## Bug Analysis

**Quality Issue Categories**:
1. **Generic Responses**: "You swing your sword and hit for damage"
2. **Over-Description**: Purple prose that slows gameplay
3. **Player Agency Violation**: "You decide to..." or railroading
4. **Tone Inconsistency**: Modern language in fantasy setting
5. **Rule Confusion**: Incorrect mechanics or impossibilities

**Root Cause Analysis**:
- **Prompt Design**: System prompts may not emphasize engagement
- **Model Selection**: Gemini variant might not be optimal for creative writing
- **Context Management**: Important story elements getting lost
- **Temperature Settings**: Too low (boring) or too high (incoherent)

**Fix Locations**:
- `mvp_site/prompts/narrative_system_instruction.md`: Enhance engagement guidelines
- `mvp_site/gemini_service.py`: Adjust temperature and top-p parameters
- `mvp_site/game_state.py`: Better context management for story elements

## Implementation Notes

### Automated Quality Pipeline
```python
def evaluate_narrative_quality(scenario, ai_response):
    evaluations = {
        'claude': evaluate_engagement(scenario, ai_response),
        'gpt4': evaluate_technical_quality(scenario, ai_response),
        'gemini': evaluate_self_assessment(scenario, ai_response)
    }

    # Aggregate scores
    dimensions = ['engagement', 'appropriateness', 'progression', 'craft']
    avg_scores = {}

    for dim in dimensions:
        scores = [eval_result[dim] for eval_result in evaluations.values() if dim in eval_result]
        avg_scores[dim] = sum(scores) / len(scores)

    overall_avg = sum(avg_scores.values()) / len(avg_scores)
    disagreement = calculate_model_disagreement(evaluations)

    return {
        'pass': overall_avg >= 7.5 and min(avg_scores.values()) >= 6.0,
        'scores': avg_scores,
        'overall': overall_avg,
        'needs_human_review': disagreement > 3.0,
        'improvement_suggestions': extract_consensus_issues(evaluations)
    }
```

### Quality Gate Integration
- **Pre-Response Validation**: Score responses before serving to users
- **A/B Testing**: Compare quality scores across different prompts/models
- **User Feedback Loop**: Correlate quality scores with user engagement metrics
- **Continuous Improvement**: Update prompts based on systematic quality failures

### Success Metrics
- **Quality Score Trend**: Increasing average scores over time
- **Consistency**: Decreasing disagreement between validators
- **User Correlation**: Quality scores predict user session length
- **Failure Reduction**: Fewer responses requiring human intervention

### Edge Case Scenarios
1. **Player Attempts Impossible Action**: "I try to convince the dragon I'm its mother"
2. **Extremely Creative Solutions**: "I use my bag of holding to create a black hole"
3. **Emotional Moments**: Character death, betrayal, major story reveals
4. **Combat Edge Cases**: Unusual spell combinations, environmental hazards

This test specifically targets the engagement dimension of your quality issues—catching responses that are technically correct but fail to create compelling gameplay experiences.
