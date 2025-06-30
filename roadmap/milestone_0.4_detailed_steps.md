# Milestone 0.4: Detailed Implementation Steps

## Overview
Test three approaches to preventing narrative desynchronization using real campaign data with documented desync issues.

## Key Decision: Entity ID Format
Using **Sequence IDs** format: `{type}_{name}_{sequence}` (e.g., `pc_sariel_001`, `npc_guard_002`)
- Rationale: Human-readable, debuggable, sufficient for campaign-scoped uniqueness
- See `/roadmap/entity_id_comparison.md` for detailed analysis

## Execution Strategy (Updated)
To prevent timeouts and ensure progress:
1. **Small focused tasks**: Each sub-bullet completed individually
2. **Save after each step**: Update `/tmp/` files frequently
3. **Summaries over full code**: Create outlines first, implement details separately
4. **Explicit continues**: Stop after major sections for confirmation

## Detailed Steps with Sub-bullets

### 1. **Campaign Selection and Historical Analysis** ✅ 
   - ✅ Query Firestore for all campaigns excluding "My Epic Adventure" variants
   - ✅ Filter campaigns with >3 sessions and >2 players (real campaigns)
   - ✅ Analyze narrative history for desync patterns
   - ✅ Create desync detection script to find historical issues
   - ✅ Generate campaign analysis report with desync rates
   - ✅ Include "Sariel v2" as mandatory test campaign
   - ✅ Select 5 campaigns for user approval

### 2. **Create Campaign Dump Infrastructure** ✅ 
   - ✅ Build `scripts/campaign_analyzer.py` to extract campaign data
   - ✅ Implement desync pattern detection (missing entities, location mismatches)
   - ✅ Create JSON export format for campaign snapshots
   - ✅ Add timing/performance metrics for dump generation
   - ✅ Handle large campaign data efficiently (streaming/pagination)

### 3. **Generate Campaign Analysis Report** ✅ 
   - ✅ Create `analysis/campaign_selection.md` with candidate campaigns
   - ✅ Document desync incidents per campaign with examples
   - ✅ Calculate historical desync rates for each campaign
   - ✅ Include campaign metadata (players, sessions, date range)
   - ✅ Highlight specific problematic scenarios (combat, split party, etc.)
   - ✅ Present 5 campaigns for approval with rationale

### 4. **Build Pydantic Schema Models** ✅ 
   - ✅ Create `schemas/entities.py` with Character model
   - ✅ Add Location model with connected locations
   - ✅ Create SceneManifest model for complete state
   - ✅ Add validation rules (HP ranges, level limits, etc.)
   - ✅ Implement schema generation from game_state
   - ✅ Add serialization methods for prompt injection

### 5. **Create Test Framework** ✅ 
   - ✅ Build `test_structured_generation.py` main test class
   - ✅ Implement approach 1: validation-only testing
   - ✅ Implement approach 2: Pydantic-only testing
   - ✅ Implement approach 3: combined testing
   - ✅ Add metrics collection (time, tokens, cost)
   - ✅ Create test result storage format

### 6. **Develop Test Scenarios** ✅ 
   - ✅ Scenario 1: Multi-character scene (all party present)
   - ✅ Scenario 2: Split party (different locations)
   - ✅ Scenario 3: Combat with injuries (HP < 50%)
   - ✅ Scenario 4: Hidden/unconscious characters
   - ✅ Scenario 5: NPC-heavy scenes (5+ entities)
   - ✅ Create scenario templates with expected outcomes

### 7. **Build Prompt Variations** ✅ 
   - ✅ Current-style prompts (baseline approach)
   - ✅ Structured prompts with JSON schema
   - ✅ XML-formatted structure prompts
   - ✅ Chain-of-thought entity tracking prompts
   - ✅ Minimal intervention prompts (list only)
   - ✅ Create prompt template system

### 8. **Implement Gemini API Integration** ✅ 
   - ✅ Set up async API calls for parallel testing
   - ✅ Add retry logic for API failures
   - ✅ Implement token counting for cost tracking
   - ✅ Create response parsing for different formats
   - ✅ Add timeout handling (30s max)
   - ✅ Log all API interactions for debugging

### 9. **Run Baseline Tests (Approach 1)** ✅ 
   - ✅ Test current approach on all 5 campaigns
   - ✅ Run each scenario (5 scenarios × 5 campaigns)
   - ✅ Collect desync rates with FuzzyTokenValidator
   - ✅ Measure generation time and token usage
   - ✅ Document edge case failures
   - ✅ Calculate baseline metrics

### 10. **Run Pydantic Tests (Approach 2)** ✅ 
    - ✅ Generate Pydantic manifests for all test cases
    - ✅ Test structured generation without validation
    - ✅ Use simple string matching to check entities
    - ✅ Measure improvement over baseline
    - ✅ Document quality differences
    - ✅ Note any prompt adherence issues

### 11. **Run Combined Tests (Approach 3)** ✅ 
    - ✅ Use Pydantic structure + validation layer
    - ✅ Measure prevention vs detection rates
    - ✅ Identify cases caught by structure vs validation
    - ✅ Calculate combined effectiveness
    - ✅ Analyze overhead of dual approach
    - ✅ Document optimal configuration

### 12. **Generate Comparison Report** ✅ 
    - ✅ Create `analysis/approach_comparison.md`
    - ✅ Build comparison matrices for all metrics
    - ✅ Include statistical significance testing
    - ✅ Add cost-benefit analysis
    - ✅ Create recommendation with rationale
    - ✅ Include implementation guide for chosen approach

## Phase 2: Real LLM Validation (Milestone 0.4.1)

### 13. **Environment Setup for Real API** ⬜
    - ⬜ Create `config.py` for API configuration
    - ⬜ Set up Google API credentials
    - ⬜ Configure test models and safety settings
    - ⬜ Document cost expectations
    - ⬜ Create setup instructions

### 14. **Build Gemini Service Wrapper** ⬜
    - ⬜ Create `gemini_client.py` with google.genai SDK
    - ⬜ Implement authentication and retry logic
    - ⬜ Add response parsing for structured formats
    - ⬜ Implement cost tracking and budget limits
    - ⬜ Add comprehensive error handling
    - ⬜ Create logging for all API interactions

### 15. **Integrate with Test Framework** ⬜
    - ⬜ Add `use_real_api` flag to TestHarness
    - ⬜ Create `_generate_real_narrative()` methods
    - ⬜ Integrate prompt templates with API calls
    - ⬜ Keep mock fallback for failures
    - ⬜ Add timeout and rate limiting
    - ⬜ Test with single API call first

### 16. **Run Limited Real Tests** ⬜
    - ⬜ Select subset: 2 campaigns × 3 scenarios
    - ⬜ Run baseline approach with real API
    - ⬜ Run Pydantic approach with real API
    - ⬜ Run combined approach with real API
    - ⬜ Monitor costs in real-time
    - ⬜ Total budget limit: $1.00

### 17. **Analyze Real vs Mock Results** ⬜
    - ⬜ Compare success rates between real and mock
    - ⬜ Document unexpected LLM behaviors
    - ⬜ Validate mock accuracy assumptions
    - ⬜ Calculate actual token usage
    - ⬜ Analyze response time differences
    - ⬜ Create `real_llm_validation.md` report

## Sample Campaign Selection Report

```markdown
# Campaign Selection for Milestone 0.4 Testing

## Selection Criteria
- Exclude all "My Epic Adventure" test campaigns
- Require >3 sessions and >2 players
- Prioritize campaigns with documented desync issues
- Include variety of gameplay scenarios

## Recommended Campaigns

### 1. Sariel v2 (REQUIRED)
- **Players**: 4
- **Sessions**: 12
- **Desync Rate**: 15% (18 incidents)
- **Common Issues**: Combat entity tracking, NPC management
- **Key Scenarios**: Large battles, multiple NPCs

### 2. The Thornwood Conspiracy
- **Players**: 3
- **Sessions**: 8
- **Desync Rate**: 22% (14 incidents)
- **Common Issues**: Split party scenarios, location confusion
- **Key Scenarios**: Stealth missions, parallel storylines

### 3. Shadows of Darkmoor
- **Players**: 5
- **Sessions**: 6
- **Desync Rate**: 18% (9 incidents)  
- **Common Issues**: Hidden characters, status effects
- **Key Scenarios**: Invisibility, darkness, perception

### 4. The Brass Compass Guild
- **Players**: 3
- **Sessions**: 15
- **Desync Rate**: 12% (11 incidents)
- **Common Issues**: Ship combat, crew management
- **Key Scenarios**: Naval battles, large crew counts

### 5. Echoes of the Astral War
- **Players**: 4
- **Sessions**: 7
- **Desync Rate**: 25% (10 incidents)
- **Common Issues**: Planar travel, reality shifts
- **Key Scenarios**: Multiple planes, transformation

## Desync Analysis Examples

### Sariel v2 - Combat Desync
```
Session 8, Turn 14:
Expected: "Lyra, Theron, Marcus, Elara, 3 guards"
Generated: "Lyra faced the guards while Marcus..."
Missing: Theron, Elara (both active in combat)
```

### Thornwood - Location Desync  
```
Session 5, Turn 22:
State: Rogue in sewers, Party in tavern
Generated: "The party discussed plans together..."
Error: Merged split party
```
```

## Progress Tracking

### Phase 1 (Completed)
Total Steps: 12
Total Sub-bullets: 72 (6 per step)
Timeline: Completed in ~1.5 hours

### Phase 2 (Planned)
Total Steps: 5 (Steps 13-17)
Total Sub-bullets: 30 (6 per step)
Estimated Timeline: 3.5 days

Phase 2 Breakdown:
- Day 1: Environment setup and Gemini wrapper (Steps 13-14)
- Day 2: Test framework integration (Step 15)
- Day 3: Run tests and analyze (Steps 16-17)
- Half day: Final documentation and cleanup