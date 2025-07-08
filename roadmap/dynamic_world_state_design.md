# Dynamic World State Design (TASK-100)

## Problem Statement
As campaigns progress, world information becomes stale:
- Initial world state doesn't reflect story developments
- NPCs remain static despite narrative changes
- Locations don't update based on events
- World facts become inconsistent with story progression

## Solution: Dynamic World State System

### Core Components

#### 1. World State Versioning
- **Version tracking** for all world elements
- **Change history** for locations, NPCs, and facts
- **Timestamp-based** state retrieval
- **Differential updates** to minimize token usage

#### 2. Event Tracking System
```python
class WorldEvent:
    event_id: str
    timestamp: datetime
    event_type: str  # "location_change", "npc_update", "fact_revision"
    affected_entities: List[str]
    changes: Dict[str, Any]
    narrative_reference: str  # Links to story content
```

#### 3. Automatic Invalidation Rules
- **Time-based**: Events expire after certain duration
- **Event-based**: Specific events invalidate related facts
- **Dependency-based**: Changes cascade to related entities
- **Priority-based**: Critical facts persist longer

### Implementation Strategy

#### Phase 1: Event Recording
1. Capture all world-changing events from narrative
2. Store in structured format with timestamps
3. Link events to affected entities

#### Phase 2: State Reconstruction
1. Start with base world state
2. Apply events chronologically
3. Generate current world view
4. Cache for performance

#### Phase 3: Intelligent Updates
1. Detect stale information during generation
2. Flag inconsistencies automatically
3. Prompt for world state refresh
4. Update only changed elements

### Data Structures

#### World State Snapshot
```python
class WorldStateSnapshot:
    version: int
    timestamp: datetime
    base_state: Dict[str, Any]
    applied_events: List[WorldEvent]
    invalidation_rules: List[InvalidationRule]
    
    def get_current_state(self) -> Dict[str, Any]:
        """Reconstruct current state from base + events"""
        pass
```

#### Invalidation Rule
```python
class InvalidationRule:
    rule_id: str
    rule_type: str  # "time", "event", "dependency"
    conditions: Dict[str, Any]
    affected_keys: List[str]
    priority: int
```

### Integration Points

#### 1. Narrative Generation
- Check world state version before generation
- Flag potential inconsistencies
- Request updated state if needed

#### 2. Game State Updates
- Record world-changing events
- Update version number
- Trigger invalidation checks

#### 3. AI Instructions
- Include current world state version
- Provide recent events context
- Flag known inconsistencies

### Benefits

1. **Narrative Consistency**: World evolves with story
2. **Reduced Contradictions**: Automatic inconsistency detection
3. **Performance**: Only update changed elements
4. **Flexibility**: Easy to add new invalidation rules
5. **Debugging**: Clear event history for troubleshooting

### Example Use Cases

#### NPC Status Changes
- NPC dies in battle → Mark as deceased
- NPC changes allegiance → Update faction
- NPC gains power → Adjust capabilities

#### Location Updates
- Town destroyed → Update description
- New building constructed → Add to location
- Weather changes → Temporary state update

#### World Facts Evolution
- Political alliance shifts → Update relationships
- Technology discovered → Enable new options
- Resource depleted → Remove availability

### Technical Considerations

1. **Storage**: Efficient event storage with compression
2. **Performance**: Cached state reconstruction
3. **Concurrency**: Handle simultaneous updates
4. **Rollback**: Ability to revert changes
5. **Validation**: Ensure event consistency

### Migration Strategy

1. **Baseline**: Capture current world state
2. **Instrumentation**: Add event recording
3. **Gradual rollout**: Start with critical entities
4. **Full deployment**: Enable for all world elements

## Next Steps

1. Implement event recording system
2. Create invalidation rule engine
3. Build state reconstruction logic
4. Integrate with narrative generation
5. Add performance monitoring