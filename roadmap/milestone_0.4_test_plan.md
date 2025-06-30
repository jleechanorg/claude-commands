# Milestone 0.4: Real-World Testing Plan

## Overview
Test three approaches using real Gemini API calls with actual campaign data to determine the best solution for preventing narrative desynchronization.

## Test Approaches

### 1. Original Validation (Baseline)
- Generate narrative with current prompts
- Use FuzzyTokenValidator from Milestone 0.3
- Measure desync rate and catch effectiveness

### 2. Pydantic-Only (Prevention)
- Create structured manifest with Pydantic
- Inject schema into prompt
- Generate narrative with explicit requirements
- NO post-validation

### 3. Combined (Belt & Suspenders)
- Use Pydantic structured generation
- PLUS validation layer as safety net
- Measure both prevention and detection rates

## Campaign Selection Criteria

```python
# Select real campaigns for testing
def select_test_campaigns(all_campaigns):
    valid_campaigns = []
    
    for campaign in all_campaigns:
        # Exclude test campaigns
        if "my epic adventure" in campaign.name.lower():
            continue
            
        # Require meaningful data
        if campaign.player_count < 2:
            continue
            
        # Need actual narrative history
        if campaign.session_count < 3:
            continue
            
        valid_campaigns.append(campaign)
    
    return valid_campaigns[:10]  # Use 10 real campaigns
```

## Test Scenarios per Campaign

### Scenario 1: Multi-Character Scene
```python
{
    "description": "All party members in same location",
    "complexity": "medium",
    "expected_entities": ["all_party_members"],
    "edge_cases": []
}
```

### Scenario 2: Split Party
```python
{
    "description": "Party split across 2 locations",
    "complexity": "high",
    "expected_entities": ["group_1", "group_2"],
    "edge_cases": ["location_transitions"]
}
```

### Scenario 3: Combat with Status Effects
```python
{
    "description": "Active combat with injured/unconscious",
    "complexity": "high",
    "expected_entities": ["all_combatants"],
    "edge_cases": ["hp_states", "unconscious", "hidden"]
}
```

### Scenario 4: NPC Heavy Scene
```python
{
    "description": "Party + 3-5 NPCs interaction",
    "complexity": "very_high",
    "expected_entities": ["party", "npcs"],
    "edge_cases": ["npc_names", "crowd_scenes"]
}
```

## Implementation Structure

### Test Framework
```python
# test_structured_generation.py
import asyncio
from typing import List, Dict
import google.generativeai as genai
from pydantic import BaseModel

class TestResult(BaseModel):
    approach: str
    campaign_id: str
    scenario: str
    narrative: str
    expected_entities: List[str]
    found_entities: List[str]
    missing_entities: List[str]
    desync_rate: float
    generation_time: float
    token_count: int
    
class StructuredGenerationTest:
    def __init__(self):
        self.client = genai.Client()
        self.validator = FuzzyTokenValidator()
        
    async def test_approach_1_validation_only(self, game_state):
        """Current approach: Generate then validate"""
        # Use existing prompt style
        prompt = self.build_current_prompt(game_state)
        
        # Generate narrative
        start_time = time.time()
        response = await self.client.models.generate_content_async(
            model="gemini-2.5-flash",
            contents=prompt
        )
        generation_time = time.time() - start_time
        
        # Validate with our system
        validation = self.validator.validate(
            response.text,
            expected_entities=self.extract_entities(game_state)
        )
        
        return TestResult(
            approach="validation_only",
            narrative=response.text,
            missing_entities=validation.entities_missing,
            desync_rate=len(validation.entities_missing) / len(expected_entities)
        )
        
    async def test_approach_2_pydantic_only(self, game_state):
        """Structured generation without validation"""
        # Create Pydantic manifest
        manifest = self.create_manifest(game_state)
        
        # Build structured prompt
        prompt = f"""
        You are a D&D Game Master. Generate a narrative for this EXACT scene:
        
        {manifest.json(indent=2)}
        
        REQUIREMENTS:
        1. You MUST mention every character listed by name
        2. You MUST set the scene in the specified location
        3. You MUST reflect character HP states (injured if <50%)
        
        Characters that MUST appear: {', '.join(manifest.get_all_character_names())}
        """
        
        # Generate
        response = await self.client.models.generate_content_async(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Check entities WITHOUT validation layer
        found = self.simple_check_entities(response.text, manifest.get_all_character_names())
        
        return TestResult(
            approach="pydantic_only",
            narrative=response.text,
            missing_entities=[e for e in expected if e not in found]
        )
        
    async def test_approach_3_combined(self, game_state):
        """Pydantic + Validation"""
        # Generate with structure
        manifest = self.create_manifest(game_state)
        structured_prompt = self.build_structured_prompt(manifest)
        
        response = await self.client.models.generate_content_async(
            model="gemini-2.5-flash",
            contents=structured_prompt
        )
        
        # Also validate
        validation = self.validator.validate(
            response.text,
            expected_entities=manifest.get_all_character_names()
        )
        
        return TestResult(
            approach="combined",
            narrative=response.text,
            missing_entities=validation.entities_missing,
            prevented_by_structure=len(validation.entities_missing) == 0
        )
```

### Pydantic Models
```python
# schemas/test_entities.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Character(BaseModel):
    name: str
    hp: int = Field(ge=0)
    max_hp: int = Field(ge=1)
    status: List[str] = []  # ["conscious", "injured", "hidden"]
    
    @property
    def is_injured(self) -> bool:
        return self.hp < (self.max_hp * 0.5)
        
class Location(BaseModel):
    name: str
    description: str
    characters_present: List[str]
    
class SceneManifest(BaseModel):
    location: Location
    player_characters: List[Character]
    npcs: List[Character] = []
    combat_active: bool = False
    
    def get_all_character_names(self) -> List[str]:
        names = [pc.name for pc in self.player_characters]
        names.extend([npc.name for npc in self.npcs])
        return names
```

## Metrics to Collect

### Primary Metrics
1. **Desync Rate** - % of narratives missing entities
2. **False Positive Rate** - Validation catching non-issues
3. **Generation Time** - Response latency
4. **Token Usage** - Cost per generation

### Secondary Metrics
1. **Narrative Quality** - Subjective scoring
2. **Edge Case Handling** - Hidden/unconscious characters
3. **Prompt Complexity** - Lines of prompt needed
4. **Retry Rate** - How often we need to regenerate

## Test Execution Plan

### Week 1: Setup and Baseline
1. Implement test framework
2. Create Pydantic models
3. Select 10 real campaigns
4. Run Approach 1 (validation only) baseline
5. Document current desync rates

### Week 2: Structured Generation Testing
6. Run Approach 2 (Pydantic only)
7. Run Approach 3 (Combined)
8. Collect all metrics
9. Generate comparison report
10. Make recommendation

## Expected Outcomes

### Hypothesis
- **Approach 1**: ~5% desync (proven in 0.3)
- **Approach 2**: 2-8% desync (unknown)
- **Approach 3**: <2% desync (best of both)

### Decision Matrix
| If... | Then... |
|-------|---------|
| Pydantic alone achieves <2% | Consider removing validation |
| Pydantic alone >5% | Keep validation layer |
| Combined significantly better | Use both in production |
| No significant difference | Keep simpler approach |

## Cost Analysis
```python
# Estimate API costs
test_runs = 10 campaigns * 4 scenarios * 3 approaches = 120 API calls
approx_cost = 120 * $0.000175 = $0.021 (very affordable)
```

## Success Criteria
1. Complete test data from 10 real campaigns
2. Statistical significance in results
3. Clear recommendation with data backing
4. Implementation guide for chosen approach