# Architecture Decision Framework with AI Consultation

## Problem Statement
Current development pattern shows repeated refactoring cycles:
- String parsing → JSON schemas → Pydantic models
- Scattered logging → structured logging
- Inline CSS → theme systems
- 1,951 print() statements still in codebase
- Multiple rounds of optimization on same features

## Goal
Establish a framework for making better upfront architecture decisions using both Claude and Gemini in a collaborative discussion format.

## Proposed Framework: Claude-Gemini Architecture Dialogue

### Step 1: Claude Identifies the Pattern
When starting a new feature, Claude should:
1. Analyze similar existing code for patterns
2. Identify potential future refactoring needs
3. Formulate specific architecture questions

### Step 2: Gemini Consultation
Claude asks Gemini for architectural guidance with specific context

### Step 3: Claude Challenges/Refines
Claude should:
- Challenge assumptions
- Point out project-specific constraints
- Suggest alternatives based on codebase patterns
- Ask clarifying questions

### Step 4: Collaborative Decision
Both AIs iterate until reaching a consensus on:
- Data models (existing Pydantic vs new)
- Integration patterns
- Future extensibility
- Migration strategy if needed

## Example Dialogue Template

```
Claude: "For feature X, I see we have similar patterns in Y and Z that evolved from strings to JSON. 
        Should we start with Pydantic models?"

Gemini: "Yes, use Pydantic with versioning..."

Claude: "But we already have entities_pydantic.py with these models. Should we:
        1. Extend existing models?
        2. Create new domain-specific models?
        3. Consider that we have 1,951 print statements - how do we handle logging?"

Gemini: "Given existing models, I recommend..."

Claude: "What about backward compatibility with our current JSON-only NarrativeResponse?"
```

## Specific Architecture Debt to Address

### 1. NarrativeResponse Evolution
- Currently: Custom class with validation
- Has Pydantic models in `schemas/entities_pydantic.py`
- Question: Migrate NarrativeResponse to Pydantic or keep hybrid approach?

### 2. Logging Chaos
- 1,951 print() statements
- Some structured logging exists
- Question: Gradual migration or big-bang refactor?

### 3. Planning Block Format
- History: string → array → JSON
- Multiple CSS commits for same feature
- Question: Version field in data or transformation layer?

### 4. Entity System
- Have: entities_pydantic.py with models
- Also have: entity_*.py utility files
- Question: Consolidate or keep separation of concerns?

## Implementation Plan

### Phase 1: Establish Dialogue Pattern
- Create standard questions for Claude to ask Gemini
- Define when to trigger architecture consultation
- Set up response evaluation criteria

### Phase 2: Test on Next Feature
- Use character creation reorganization as test case
- Document the dialogue
- Measure if it prevents refactoring cycles

### Phase 3: Create Reusable Templates
- Architecture Decision Records (ADRs)
- Standard consultation prompts
- Decision criteria checklist

## Success Metrics
- Reduce "Fix:" commits by 50%
- Reduce refactoring cycles from 3-4 to 1-2
- Complete features in single PR instead of multiple iterations

## Next Steps
1. Test dialogue on character creation feature
2. Create ADR template
3. Establish triggers for architecture consultation
4. Document decisions in codebase