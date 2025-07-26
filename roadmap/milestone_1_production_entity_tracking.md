# Milestone 1: Production Entity Tracking Implementation

## Overview
Implement the proven Combined approach (structured generation + validation) into production to ensure 100% entity tracking in narrative generation.

## Background
Milestone 0.4 proved that the Combined approach achieves 100% entity tracking success rate on both mock scenarios and real campaign interactions. This milestone implements that solution in production.

### Proven Results
- **Mock tests**: 100% success rate (see `test_structured_generation.py`)
- **Real API tests**: 100% success rate for structured approaches
- **Real Sariel campaign**: 100% success tracking all entities including Cassian
- **Test implementation**: `test_real_sariel_campaign.py` shows exact integration
- **Cost**: ~$0.0007 per narrative (negligible)

## Goals
1. Integrate Combined approach into production `gemini_service.py`
2. Implement Entity ID system for better tracking
3. Add monitoring and metrics
4. Ensure backward compatibility

## Implementation Components

### Schema Definition
The complete entity tracking system uses these models:

```python
from typing import List, Dict, Any
from enum import Enum

class EntityStatus(Enum):
    """Common entity statuses"""
    CONSCIOUS = "conscious"
    UNCONSCIOUS = "unconscious"
    HIDDEN = "hidden"
    INVISIBLE = "invisible"

class Visibility(Enum):
    """Entity visibility states"""
    VISIBLE = "visible"
    HIDDEN = "hidden"
    INVISIBLE = "invisible"

class SceneManifest:
    """Complete scene state for validation"""
    def __init__(self, scene_id: str, session_number: int, turn_number: int,
                 current_location: str, player_characters: List[Dict],
                 npcs: List[Dict] = None):
        self.scene_id = scene_id
        self.session_number = session_number
        self.turn_number = turn_number
        self.current_location = current_location
        self.player_characters = player_characters
        self.npcs = npcs or []

    def get_expected_entities(self) -> List[str]:
        """Returns list of entities that MUST appear in narrative"""
        expected = []

        # Add visible, conscious PCs
        for pc in self.player_characters:
            if pc.get('visible', True) and pc.get('conscious', True):
                expected.append(pc['name'])

        # Add visible, conscious NPCs
        for npc in self.npcs:
            if npc.get('visible', True) and npc.get('conscious', True):
                expected.append(npc['name'])

        return expected

    def to_prompt_format(self) -> str:
        """Converts manifest to structured prompt injection format"""
        lines = [
            "=== SCENE MANIFEST ===",
            f"Location: {self.current_location}",
            f"Session: {self.session_number}, Turn: {self.turn_number}",
            "",
            "PRESENT CHARACTERS:"
        ]

        # Add characters with their status
        for pc in self.player_characters:
            if pc.get('present', True):
                lines.append(
                    f"- {pc['name']} (PC): HP {pc.get('hp', '?')}/{pc.get('hp_max', '?')}, "
                    f"Status: {pc.get('status', 'conscious')}, "
                    f"Visibility: {pc.get('visibility', 'visible')}"
                )

        for npc in self.npcs:
            if npc.get('present', True):
                lines.append(
                    f"- {npc['name']} (NPC): HP {npc.get('hp', '?')}/{npc.get('hp_max', '?')}, "
                    f"Status: {npc.get('status', 'conscious')}, "
                    f"Visibility: {npc.get('visibility', 'visible')}"
                )

        lines.append("=== END MANIFEST ===")
        return "\n".join(lines)

def create_from_game_state(game_state: Dict[str, Any], session: int, turn: int) -> SceneManifest:
    """Create a SceneManifest from game state"""
    # Extract player character
    pc_data = game_state.get('player_character_data', {})
    player_characters = [{
        'name': pc_data.get('name', 'Unknown'),
        'hp': pc_data.get('hp', 10),
        'hp_max': pc_data.get('hp_max', 10),
        'status': 'conscious',
        'visibility': 'visible',
        'present': True
    }]

    # Extract NPCs
    npcs = []
    npc_data = game_state.get('npc_data', {})
    for npc_name, npc_info in npc_data.items():
        if npc_info.get('present', True):
            npcs.append({
                'name': npc_name,
                'hp': npc_info.get('hp', 10),
                'hp_max': npc_info.get('hp_max', 10),
                'status': 'conscious' if npc_info.get('conscious', True) else 'unconscious',
                'visibility': 'invisible' if npc_info.get('hidden', False) else 'visible',
                'present': True
            })

    return SceneManifest(
        scene_id=f"scene_s{session}_t{turn}",
        session_number=session,
        turn_number=turn,
        current_location=game_state.get('location', 'Unknown'),
        player_characters=player_characters,
        npcs=npcs
    )
```

### Validator Implementation (from `prototype/validators/narrative_sync_validator.py`)
The validator ensures entities are tracked:

```python
class NarrativeSyncValidator:
    def validate(self, narrative_text: str, expected_entities: List[str]) -> ValidationResult:
        """
        Returns:
        - entities_found: List of entities mentioned
        - entities_missing: List of entities that should have been mentioned
        - all_entities_present: Boolean success indicator
        - confidence: Float 0-1 confidence score
        """
```

## Step 1: Production Implementation (gemini_service.py)

### 1.1 Update Narrative Generation
- [ ] Add the schema code from above to your codebase or import from a new module
- [ ] Import required components:
  ```python
  # If you create a new module for the schema
  from your_module.entity_tracking import SceneManifest, create_from_game_state
  from prototype.validators.narrative_sync_validator import NarrativeSyncValidator
  ```
- [ ] Modify `generate_narrative()` to:
  1. Create manifest: `manifest = create_from_game_state(game_state, session, turn)`
  2. Add to prompt: `prompt += f"\n\n{manifest.to_prompt_format()}"`
  3. Add instruction: "You MUST mention ALL characters listed in the manifest"
- [ ] Implement JSON response parsing for structured output
- [ ] Add fallback to unstructured if JSON parsing fails

### 1.2 Integrate NarrativeSyncValidator
- [ ] Add validation after narrative generation:
  ```python
  validator = NarrativeSyncValidator()
  expected_entities = manifest.get_expected_entities()
  result = validator.validate(narrative, expected_entities)

  if not result.all_entities_present:
      logger.warning(f"Missing entities: {result.entities_missing}")
      # Optional: Regenerate with stronger prompt
  ```
- [ ] Log validation results for monitoring
- [ ] Handle validation failures gracefully

### 1.3 Update Prompt Templates
- [ ] Add structured format to all narrative prompts:
  ```
  [Previous prompt content...]

  === SCENE MANIFEST ===
  Location: The Silver Stag Tavern
  Session: 2, Turn: 15

  PRESENT CHARACTERS:
  - Lyra (PC): HP 28/32, Status: conscious, Visibility: visible
  - Theron (NPC): HP 45/45, Status: conscious, Visibility: visible
  - Marcus (NPC): HP 38/40, Status: conscious, Visibility: visible
  - Elara (NPC): HP 22/25, Status: conscious, Visibility: visible
  === END MANIFEST ===

  IMPORTANT: You must mention ALL characters listed above in your narrative.

  Format your response as JSON:
  {
    "narrative": "Your narrative text here...",
    "entities_mentioned": ["Lyra", "Theron", "Marcus", "Elara"],
    "location_confirmed": "The Silver Stag Tavern"
  }
  ```
- [ ] Ensure all prompts include manifest from game state
- [ ] Test with existing campaigns

### 1.4 Example Complete Implementation
```python
# In gemini_service.py
def generate_narrative_with_tracking(self, prompt, game_state, session, turn):
    """Enhanced narrative generation with entity tracking"""

    # 1. Create entity manifest
    manifest = create_from_game_state(game_state, session, turn)
    expected_entities = manifest.get_expected_entities()

    # 2. Add manifest to prompt
    enhanced_prompt = f"{prompt}\n\n{manifest.to_prompt_format()}"
    enhanced_prompt += """

IMPORTANT: You must mention ALL characters listed in the manifest.
Format your response as JSON with 'narrative', 'entities_mentioned', and 'location_confirmed' fields.
"""

    # 3. Generate with structured output
    response = self.generate_content(
        model=self.model,
        contents=enhanced_prompt,
        generation_config={"response_mime_type": "application/json"}
    )

    # 4. Parse response
    try:
        result = json.loads(response.text)
        narrative = result['narrative']
        entities_mentioned = result.get('entities_mentioned', [])
    except:
        # Fallback to plain text
        narrative = response.text
        entities_mentioned = []

    # 5. Validate
    validator = NarrativeSyncValidator()
    validation = validator.validate(narrative, expected_entities)

    if not validation.all_entities_present:
        logger.warning(f"Entity tracking failed: Missing {validation.entities_missing}")
        # Could regenerate here with stronger prompt

    return narrative, validation
```

### 1.5 Performance Optimization
- [ ] Measure generation time impact (<200ms target)
- [ ] Cache entity manifests where possible
- [ ] Use batch validation for multiple narratives

## Step 2: Entity ID System Implementation

### 2.1 Design Sequence ID Format
- [ ] Implement ID generator (e.g., `npc_cassian_001`)
- [ ] Add ID fields to game state schema
- [ ] Create migration script for existing campaigns
- [ ] Document ID format specification

### 2.2 Update Game State Management
- [ ] Modify entity creation to assign IDs
- [ ] Update entity references to use IDs
- [ ] Ensure IDs persist across sessions
- [ ] Add ID lookup utilities

### 2.3 Validator Enhancement
- [ ] Update validator to track by ID
- [ ] Add fuzzy matching for names to IDs
- [ ] Implement ID-based presence detection
- [ ] Create ID mismatch reports

### 2.4 Migration Strategy
- [ ] Create backup of all campaigns
- [ ] Run migration script on test data
- [ ] Migrate production campaigns
- [ ] Verify ID assignments

## Step 3: Monitoring and Metrics

### 3.1 Entity Tracking Metrics
- [ ] Track entity mention rate per narrative
- [ ] Monitor validation success/failure rates
- [ ] Log entities missed vs found
- [ ] Create daily tracking reports

### 3.2 Performance Metrics
- [ ] Measure generation time with structured prompts
- [ ] Track API costs with new approach
- [ ] Monitor token usage increase
- [ ] Set up performance alerts

### 3.3 Player Experience Metrics
- [ ] Track narrative coherence scores
- [ ] Monitor player complaints about missing NPCs
- [ ] Measure engagement with entity-rich narratives
- [ ] A/B test if needed

## Step 4: Rollout Plan

### 4.1 Testing Phase
- [ ] Deploy to development environment
- [ ] Test with QA campaigns
- [ ] Run parallel comparison tests
- [ ] Fix any edge cases

### 4.2 Gradual Rollout
- [ ] Enable for 10% of new campaigns
- [ ] Monitor metrics for 1 week
- [ ] Increase to 50% if stable
- [ ] Full rollout after 2 weeks

### 4.3 Rollback Plan
- [ ] Feature flag for quick disable
- [ ] Fallback to original generation
- [ ] Keep unstructured prompts available
- [ ] Document rollback procedure

## Success Criteria
- 95%+ entity tracking success rate in production
- <200ms additional latency
- No increase in player complaints
- Successful migration of all existing campaigns

## Timeline
- Week 1-2: Production implementation
- Week 3: Entity ID system
- Week 4: Monitoring setup
- Week 5-6: Testing and rollout

## Dependencies
- Completed Milestone 0.4 test results
- Access to production gemini_service.py
- Ability to modify game state schema
- Monitoring infrastructure

## Risks
- Performance impact on generation time
- Backward compatibility issues
- Increased API costs
- Player perception of changes

## Notes
- Start with gemini_service.py changes as they provide immediate value
- Entity ID system can be implemented incrementally
- Monitor closely during rollout for any issues
- Keep validation-only as emergency fallback

---

## Appendix: Original Phase 1 (AI Token Audit)

*Note: This phase was originally planned but is no longer needed given the success of the structured generation approach. Kept here for reference.*

### Original Phase 1: AI Token Audit and Validation Infrastructure
**Originally planned for Weeks 3-4**

#### Milestone 1.1: AI Token Audit & Registry
- Create comprehensive AI token registry and audit
- Complete audit of all AI-generated tokens in prompts/ directory
- Token registry mapping AI instructions → code handlers
- Gap analysis report identifying missing implementations
- Document all current AI→Code integration points

#### Milestone 1.2: Validation Infrastructure
- Add AI output validation layer
- Schema definitions for all AI output formats
- Validation functions that catch format mismatches
- Logging for validation failures and unknown tokens
- Integration points for state update pipeline

#### Milestone 1.3: Pattern Detection
- Systematic corruption pattern detection
- Scripts to detect similar corruption patterns across codebase
- Automated checks for "Two Source of Truth" problems
- CI/CD pipeline integration
- Documentation of detected patterns

### Why This Phase Was Skipped
The structured generation approach (Milestone 0.4) proved so effective at 100% entity tracking that the complex token audit became unnecessary. Instead of trying to catch and validate all possible AI outputs, we now guide the AI to produce structured, predictable outputs that inherently track entities correctly.

---

## Key Implementation Files Reference

### Core Components
1. **Entity Schema**: Included inline in this document
   - `SceneManifest` class - Complete scene state
   - `create_from_game_state()` - Converts game state to manifest
   - Entity types and validation logic

2. **Validator**: `prototype/validators/narrative_sync_validator.py`
   - `NarrativeSyncValidator` class
   - `validate()` method returns ValidationResult
   - Advanced presence detection patterns

3. **Test Framework**: `prototype/tests/milestone_0.4/test_structured_generation.py`
   - Shows how to integrate all components
   - Example prompt templates
   - Success metrics

4. **Real Implementation**: `prototype/tests/milestone_0.4/test_real_sariel_campaign.py`
   - Production-ready integration example
   - Exact prompt format that achieved 100% success
   - Error handling and fallbacks

5. **API Client**: `prototype/tests/milestone_0.4/gemini_client.py`
   - Structured output parsing
   - Response handling patterns

### Results Documentation
- `REAL_SARIEL_CAMPAIGN_RESULTS.md` - Proof of 100% success on real campaign
- `REAL_API_RESULTS.md` - Comparison of all approaches with real API
