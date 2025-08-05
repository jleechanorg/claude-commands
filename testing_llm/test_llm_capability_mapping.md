# Test: LLM Capability Mapping and Boundary Discovery

## Test ID
llm-capability-mapping-research

## Status
- [ ] RED (failing)
- [ ] GREEN (passing)
- [ ] REFACTORED

## Description
Systematic exploration of LLM capabilities and limitations using progressively complex D&D scenarios. This test serves Goal 1 (personal learning about LLM capabilities) by mapping the exact boundaries of different LLMs' reasoning, creativity, and domain knowledge.

## Pre-conditions
- Access to Claude, GPT-4, and Gemini APIs
- D&D 5e rule reference materials
- Capability testing framework
- Data collection system for cross-model comparison

## Research Questions
1. **Reasoning Depth**: Where does each LLM's logical reasoning break down?
2. **Creative Coherence**: How long can each LLM maintain narrative consistency?
3. **Domain Expertise**: How deep is each LLM's D&D knowledge vs general creativity?
4. **Failure Modes**: What are the systematic ways each LLM fails?
5. **Collaborative Synergy**: Do multiple LLMs together outperform single LLMs?

## Test Matrix: Progressive Complexity Ladder

### Level 1: Basic D&D Mechanics
**Test Scenario**: Simple combat with standard rules
```
"A level 3 fighter attacks a goblin with a longsword.
Roll to hit: 15 vs AC 15. Damage roll: 8.
Describe the attack and its effects."
```

**Capability Assessment**:
- Rule accuracy (damage calculation, AC mechanics)
- Narrative coherence (description quality)
- Appropriate tone (fantasy combat feel)

### Level 2: Complex Rule Interactions
**Test Scenario**: Multi-layered spell effects
```
"A wizard casts Web (saves failed) then Fireball through the web.
The rogue has Evasion. The fighter has Protection fighting style.
Resolve all interactions and describe the scene."
```

**Capability Assessment**:
- Rule complexity handling (multiple simultaneous effects)
- Systematic thinking (order of operations)
- Creative problem solving (unusual combinations)

### Level 3: Ambiguous Situations
**Test Scenario**: Rules edge cases requiring interpretation
```
"A polymorph spell ends mid-flight 200 feet above ground.
The character was enlarged before polymorph.
Multiple concentration spells are involved.
Rule on the situation and describe what happens."
```

**Capability Assessment**:
- Interpretive reasoning (ambiguous rules)
- Consistency maintenance (previous decisions)
- Creative problem solving (novel situations)

### Level 4: Narrative Coherence Marathon
**Test Scenario**: Multi-session story consistency
```
"Continue this campaign from Session 1 through Session 10:
- Session 1: Party discovers ancient tower
- [Provide 10 sessions of escalating complexity]
- Session 10: Resolution requires remembering details from Session 1"
```

**Capability Assessment**:
- Long-term memory consistency
- Character development tracking
- Plot thread management
- Creative evolution vs consistency balance

### Level 5: Cross-Domain Knowledge Transfer
**Test Scenario**: D&D principles applied to other systems
```
"Adapt this D&D combat encounter for:
1. Call of Cthulhu (horror investigation)
2. Cyberpunk 2020 (futuristic action)
3. Original game system (your design)
Maintain core challenge and player agency."
```

**Capability Assessment**:
- Domain adaptation flexibility
- Core principle extraction
- Creative system design
- Thematic consistency

## Multi-LLM Collaboration Experiment

### Experiment 1: Sequential Improvement
1. **Claude**: Creates initial response
2. **GPT-4**: Reviews and improves Claude's response
3. **Gemini**: Synthesizes final version from both

### Experiment 2: Parallel Generation + Synthesis
1. **All LLMs**: Generate independent responses
2. **Meta-LLM**: Combines best elements from all three
3. **Human**: Evaluates combined vs individual quality

### Experiment 3: Specialized Roles
1. **Claude**: Narrative and creativity focus
2. **GPT-4**: Rules accuracy and logic focus
3. **Gemini**: Player psychology and engagement focus
4. **Combined**: Create collaborative response

## Data Collection Framework

### Quantitative Metrics
- **Success Rate**: Percentage of scenarios handled correctly at each level
- **Failure Point**: Exact complexity level where each LLM breaks down
- **Consistency Score**: Narrative coherence across multi-part scenarios
- **Rule Accuracy**: Percentage of D&D mechanics handled correctly
- **Collaboration Benefit**: Quality improvement from multi-LLM approaches

### Qualitative Analysis
- **Failure Mode Patterns**: Common ways each LLM fails
- **Strength Profiles**: What each LLM excels at
- **Creative Signatures**: Distinctive creative patterns per LLM
- **Reasoning Styles**: How each LLM approaches problem-solving
- **Domain Knowledge Gaps**: Specific areas where each LLM lacks expertise

## Expected Results

**Hypothesis: LLM Capability Hierarchy**
- **Level 1-2**: All LLMs perform well (>90% success)
- **Level 3**: Differentiation begins (70-90% success)
- **Level 4**: Major divergence (30-70% success)
- **Level 5**: Individual strengths emerge (<30% universal success)

**Collaboration Hypothesis**:
- Sequential improvement: 15-25% quality increase
- Parallel synthesis: 20-30% quality increase
- Specialized roles: 25-40% quality increase

## Implementation Protocol

### Phase 1: Individual LLM Testing
```python
def test_llm_capability_level(llm_name, scenario_level, scenario_data):
    """Test single LLM against specific capability level"""
    response = call_llm_api(llm_name, scenario_data)

    # Evaluate multiple dimensions
    scores = {
        'rule_accuracy': evaluate_rule_compliance(response),
        'narrative_quality': evaluate_storytelling(response),
        'logical_consistency': evaluate_reasoning(response),
        'creativity': evaluate_originality(response)
    }

    # Determine pass/fail for this level
    passes_level = all(score >= LEVEL_THRESHOLDS[scenario_level][dim]
                      for dim, score in scores.items())

    return {
        'llm': llm_name,
        'level': scenario_level,
        'passes': passes_level,
        'scores': scores,
        'response': response
    }
```

### Phase 2: Collaboration Testing
```python
def test_collaborative_capability(scenario_data, collaboration_mode):
    """Test multi-LLM collaboration approaches"""

    if collaboration_mode == 'sequential':
        response1 = call_llm_api('claude', scenario_data)
        response2 = call_llm_api('gpt4', f"Improve this response: {response1}")
        final_response = call_llm_api('gemini', f"Synthesize: {response1} + {response2}")

    elif collaboration_mode == 'parallel':
        responses = [call_llm_api(llm, scenario_data) for llm in ['claude', 'gpt4', 'gemini']]
        final_response = call_llm_api('claude', f"Combine best elements: {responses}")

    elif collaboration_mode == 'specialized':
        narrative = call_llm_api('claude', f"Focus on story: {scenario_data}")
        rules = call_llm_api('gpt4', f"Focus on mechanics: {scenario_data}")
        engagement = call_llm_api('gemini', f"Focus on player experience: {scenario_data}")
        final_response = synthesize_specialized_responses(narrative, rules, engagement)

    return evaluate_response_quality(final_response)
```

### Phase 3: Longitudinal Analysis
- Track capability changes over time (model updates)
- Identify learning patterns in multi-session scenarios
- Map domain knowledge evolution
- Document systematic improvement strategies

## Success Metrics

**Research Output Goals**:
- **Capability Map**: Detailed profile of each LLM's strengths/weaknesses
- **Collaboration Patterns**: Proven methods for multi-LLM coordination
- **Failure Mode Catalog**: Systematic understanding of LLM limitations
- **Optimization Strategies**: Data-driven approaches for LLM task assignment

**Learning Objectives**:
- Understand which LLMs excel at which types of creative tasks
- Discover novel applications for multi-LLM collaboration
- Identify systematic approaches to LLM workflow optimization
- Build foundation knowledge for Goals 2 and 3

This test transforms from "checking quality" to "systematically exploring the boundaries of AI creativity and reasoning" - providing foundational knowledge for building better AI-driven development workflows and GenAI RPG features.
