# Scratchpad: JSON Response Format Reorganization using /tddf

**Branch**: update/json-response-reorganization  
**Goal**: Update all code layers to match the new JSON response format with reordered fields and restructured debug_info

## Understanding the Changes

### 1. Field Order Changes (Player-Centric)
**Old Order**: narrative, session_header, planning_block, dice_rolls, resources, entities_mentioned, location_confirmed, state_updates, debug_info

**New Order** (as specified by user):
```json
{
    "session_header": "The [SESSION_HEADER] block with timestamp, location, status, etc. - ALWAYS VISIBLE TO PLAYERS",
    "resources": "HD: 2/3, Spells: L1 2/2, L2 0/1, Ki: 3/5, Rage: 2/3, Potions: 2, Exhaustion: 0",
    "location_confirmed": "Current location name or 'Unknown' or 'Character Creation'",
    "dice_rolls": ["Perception check: 1d20+3 = 15+3 = 18 (Success)", "Attack roll: 1d20+5 = 12+5 = 17 (Hit)"],
    "narrative": "Your complete narrative response containing ONLY the story text and dialogue that players see",
    "planning_block": "The --- PLANNING BLOCK --- with character options - ALWAYS VISIBLE TO PLAYERS", 
    "god_mode_response": "ONLY for GOD MODE commands - put your response here instead of narrative",
    "debug_info": {
        "dm_notes": ["DM thoughts about the scene", "Rule considerations"],
        "entities_mentioned": ["List", "of", "entity", "names", "mentioned"],
        "state_rationale": "Explanation of why you made certain state changes",
        "state_updates": {
            // Your state changes here following the schema below
            // Empty object {} if no changes, but field MUST be present
        },
    }
}
```

### 2. Major Structural Changes
**CRITICAL**: `entities_mentioned` and `state_updates` are now INSIDE `debug_info`:
```json
"debug_info": {
    "dm_notes": [...],
    "entities_mentioned": [...],  // MOVED HERE
    "state_rationale": "...",
    "state_updates": {...}  // MOVED HERE
}
```

### 3. Key Requirements
- Remove resources from session_header content
- Everything in debug_info sent to LLM but stripped for non-debug users
- Add CamelCase sectionIDs for referencing schema sections
- Comprehensive test coverage at all layers

## Confirmed Requirements

Based on your instructions:

1. **Resources in Header**: 
   - ✅ REMOVE resource tracking from [SESSION_HEADER] text
   - Resources are now a separate field and should not appear in header

2. **Debug Info Visibility**:
   - ✅ Send complete debug_info to LLM always
   - ✅ Strip debug_info from API responses when user not in debug mode
   - ✅ Create/update tests to verify this behavior

3. **State Updates Access**:
   - ✅ Update all code to access via debug_info.state_updates
   - ✅ Fix backward compatibility issues as we find them

4. **CamelCase Section IDs**:
   - ✅ Add section identifiers like `## CharacterEntitySchema`
   - ✅ Reference as "See CharacterEntitySchema section"
   - ✅ Update game_state_instruction.md and other prompts

5. **Frontend Display Order**:
   - ✅ Display fields in the exact order specified
   - ✅ Player experience should follow: header → resources → location → dice → narrative → planning

## /tddf Implementation Plan

### Layer 1: Unit Tests (Isolated Modules)

#### 1.1 Schema Updates
- [ ] Update `narrative_response_schema.py` to match new structure
- [ ] Move entities_mentioned and state_updates into debug_info schema
- [ ] Update field ordering in schema definition

#### 1.2 Response Parser Tests
- [ ] `test_structured_response_parser.py` - Update for new structure
- [ ] `test_narrative_response_extraction.py` - Fix field access
- [ ] `test_gemini_response.py` - Update response creation

#### 1.3 LLM Response Tests  
- [ ] `test_llm_response.py` - Update getters for moved fields
- [ ] Add getter methods for backward compatibility?
- [ ] Test debug_info stripping logic

#### 1.4 Main Route Tests
- [ ] `test_main.py` - Update response building
- [ ] `test_api_routes.py` - Fix JSON structure expectations
- [ ] Test debug mode filtering

### Layer 2: Integration Tests (Python Backend Flow)

#### 2.1 Full Backend Flow
- [ ] `test_integration.py` - Update expected response structure
- [ ] Test that state_updates go through debug_info
- [ ] Verify entities_mentioned in debug_info

#### 2.2 Debug Mode Integration
- [ ] Create new test for debug mode ON/OFF behavior
- [ ] Verify debug_info included in LLM prompts
- [ ] Verify debug_info stripped for non-debug users

#### 2.3 State Management Integration
- [ ] Test state updates still work when moved to debug_info
- [ ] Verify game state persistence with new structure

### Layer 3: Browser Tests (Mocked APIs)

#### 3.1 Field Display Order
- [ ] Test session_header appears first
- [ ] Test resources display (not in header)
- [ ] Test narrative appears after dice_rolls
- [ ] Test planning_block appears last

#### 3.2 Debug Mode UI Tests
- [ ] Test debug info hidden when debug OFF
- [ ] Test debug info visible when debug ON
- [ ] Test state updates visible in debug mode

#### 3.3 Response Processing
- [ ] Test frontend handles new JSON structure
- [ ] Test structured fields display correctly
- [ ] Screenshot each display state

### Layer 4: Browser Tests (Real APIs)

#### 4.1 End-to-End Validation
- [ ] Test complete flow with new JSON format
- [ ] Verify Gemini API returns expected structure
- [ ] Test real state persistence

#### 4.2 Debug Mode E2E
- [ ] Test debug parameter propagation
- [ ] Verify sensitive debug info not leaked
- [ ] Screenshot production-like behavior

## Implementation Order

### Phase 1: Schema & Core Updates
1. Update narrative_response_schema.py for new structure
2. Add CamelCase section IDs to game_state_instruction.md:
   - ## JsonResponseFormat
   - ## CharacterEntitySchema  
   - ## StateUpdateFormat
   - ## WorldTimeSchema
   - ## CombatStateSchema
   - ## NPCDataSchema
3. Update prompt references to use CamelCase IDs
4. Remove resources from SESSION_HEADER format

### Phase 2: Backend Updates
1. Update response builders in main.py
2. Update gemini_service.py response handling
3. Fix all response parsers

### Phase 3: Test Updates (Layer 1-2)
1. Update unit tests for new structure
2. Update integration tests
3. Add new debug mode tests

### Phase 4: Frontend Updates
1. Update app.js field processing order
2. Update debug info handling
3. Fix structured field display

### Phase 5: Browser Tests (Layer 3-4)
1. Update mock response structures
2. Fix browser test expectations
3. Add new display order tests

## Risk Assessment

### High Risk Areas
1. **State Updates Access**: Many files directly access response.state_updates
2. **Entities Mentioned**: Used for NPC tracking throughout codebase
3. **Frontend Display**: Major changes to field processing order
4. **Test Fixtures**: Many mock responses need updating

### Mitigation Strategies
1. Add compatibility getters in transition period
2. Search/replace comprehensively 
3. Run full test suite after each phase
4. Keep detailed migration notes

## Future Improvements to Consider

### Mode Name CamelCase Standardization
- Consider changing mode declarations to use CamelCase for consistency:
  - `[Mode: STORY MODE]` → `[Mode: StoryMode]`
  - `[Mode: DM MODE]` → `[Mode: DmMode]`
  - `[Mode: GOD MODE]` → `[Mode: GodMode]`
- This would match the CamelCase pattern used for planning block choices
- Would require careful migration to avoid breaking existing games
- Consider as part of larger JSON standardization effort

## Success Criteria
- [ ] All tests pass with new JSON structure
- [ ] Debug info properly filtered based on mode
- [ ] Frontend displays fields in correct order
- [ ] No resources in session_header text
- [ ] State updates work through debug_info.state_updates
- [ ] Entities mentioned accessed via debug_info.entities_mentioned
- [ ] LLM receives full debug_info in prompts
- [ ] CamelCase section references added throughout prompts
- [ ] Test coverage for debug mode ON/OFF behavior

## Key Code Changes Needed

### 1. Schema Update (narrative_response_schema.py)
```python
class NarrativeResponse(BaseModel):
    session_header: str
    resources: str
    location_confirmed: str
    dice_rolls: List[str] = []
    narrative: str
    planning_block: str
    god_mode_response: Optional[str] = None
    debug_info: DebugInfo  # Now contains entities_mentioned and state_updates
```

### 2. DebugInfo Schema
```python
class DebugInfo(BaseModel):
    dm_notes: List[str] = []
    entities_mentioned: List[str] = []
    state_rationale: str = ""
    state_updates: Dict[str, Any] = {}
```

### 3. Backward Compatibility
Add property methods to maintain existing code:
```python
@property
def state_updates(self):
    return self.debug_info.state_updates if self.debug_info else {}

@property
def entities_mentioned(self):
    return self.debug_info.entities_mentioned if self.debug_info else []
```

### 4. Debug Stripping Logic
```python
def strip_debug_info(response: dict, debug_mode: bool) -> dict:
    if not debug_mode and 'debug_info' in response:
        del response['debug_info']
    return response
```