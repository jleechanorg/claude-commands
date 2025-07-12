# Dynamic World State v2 - Implementation Scratchpad

## Executive Summary
A comprehensive event-tracking and state management system that prevents narrative inconsistencies in long-running campaigns by maintaining a versioned, event-sourced world state.

## Problem Statement
Current issues in long campaigns:
- NPCs "forget" past interactions
- World doesn't reflect player actions  
- Contradictions emerge ("Didn't we kill that guy?")
- Static world feels unreactive

## Core Value Proposition

### For Players
- **Living World**: Every action has lasting consequences
- **Perfect Memory**: The GM never forgets what you did
- **Emergent Story**: Minor actions cascade into major plot points
- **Trust Building**: Consistent world enables long-term planning

### Use Case Priority
1. **HIGH VALUE**: Multi-session campaigns (10+ sessions)
2. **MEDIUM VALUE**: Story arcs (3-10 sessions)
3. **LOW VALUE**: One-shots (optional/disabled)

## Current Goal
Implement a comprehensive event-tracking and state management system to prevent narrative inconsistencies in long-running campaigns.

## Four-Layer Architecture Plan

### Layer 1: Domain Layer (Pure Business Logic)
**Start here - no external dependencies, perfect for TDD**

#### Components:
1. **WorldEvent** - Immutable event records
   - Properties: event_id, timestamp, event_type, affected_entities, changes, narrative_ref, cascade_effects
   - Methods: to_dict(), validate(), get_affected_entity_ids()

2. **VersionedEntity** - Entities with version tracking
   - Properties: entity_id, version, current_state, change_history
   - Methods: apply_change(), get_version(), get_changes_since()

3. **InvalidationRule** - Rules for stale data
   - Properties: rule_id, trigger_type, conditions, affected_patterns, priority
   - Methods: matches(), should_trigger(), get_affected_entities()

4. **StateChange** - Version transition records
   - Properties: from_version, to_version, event_id, changes, timestamp
   - Methods: apply_to_state(), reverse_change()

5. **EventType** - Enum of valid event types
   - Values: NPC_DEATH, NPC_STATUS, LOCATION_CHANGE, RESOURCE_DEPLETION, etc.

### Layer 2: Application Layer (Use Cases & Orchestration)
**Depends on Domain Layer only**

#### Services:
1. **EventRecorderService**
   - Methods: record_event(), batch_record(), validate_event_consistency()
   - Tests: Event validation, duplicate detection, batch processing

2. **VersioningService**
   - Methods: version_entity(), get_entity_history(), rollback_to_version()
   - Tests: Version increments, history tracking, rollback accuracy

3. **InvalidationEngine**
   - Methods: process_event(), find_invalidations(), cascade_invalidations()
   - Tests: Rule matching, cascade processing, priority handling

4. **StateReconstructionService**
   - Methods: reconstruct_at_time(), get_current_state(), get_state_diff()
   - Tests: Accuracy, performance (<100ms), consistency

5. **WorldStateOrchestrator**
   - Methods: process_game_update(), get_world_context(), handle_time_passage()
   - Tests: End-to-end workflows, integration scenarios

### Layer 3: Infrastructure Layer (External Dependencies)
**All external integrations - mockable for testing**

#### Components:
1. **EventRepository**
   - Interface: save_event(), get_events_since(), get_events_for_entity()
   - Implementation: FirestoreEventRepository
   - Tests: CRUD operations, query performance, error handling

2. **StateSnapshotCache**
   - Interface: cache_state(), get_cached_state(), invalidate_cache()
   - Implementation: InMemoryCache, RedisCache (future)
   - Tests: Cache hits/misses, TTL, memory limits

3. **EventSerializer**
   - Methods: serialize_event(), deserialize_event(), compress_events()
   - Tests: Round-trip accuracy, compression ratios

4. **CompressionService**
   - Methods: compress_old_events(), summarize_event_batch()
   - Tests: Token reduction, information preservation

5. **FirestoreWorldStateAdapter**
   - Methods: save_world_state(), load_world_state(), migrate_schema()
   - Tests: Integration with existing system, backwards compatibility

### Layer 4: Presentation Layer (AI/User Interface)
**How the system is exposed to prompts and UI**

#### Components:
1. **WorldStatePromptFormatter**
   - Methods: format_for_prompt(), include_relevant_events(), add_version_context()
   - Tests: Token efficiency, context relevance

2. **EventContextProvider**
   - Methods: get_events_for_scene(), get_entity_history(), get_recent_changes()
   - Tests: Relevance filtering, performance

3. **StateUpdateParser**
   - Methods: extract_events_from_response(), validate_state_changes()
   - Tests: Parse accuracy, error handling

4. **PromptIntegrationAdapter**
   - Methods: enhance_prompt(), process_ai_response()
   - Tests: Integration with game_state_instruction.md

5. **DebugVisualizationService**
   - Methods: generate_timeline_view(), show_state_diff(), export_history()
   - Tests: Accuracy, usability

## /4layer + /tdd Execution Plan

### Week 1: Domain Layer Foundation
**Using /tdd for each component**

```bash
# Day 1-2: WorldEvent
/tdd --component "WorldEvent" --tests "creation, validation, serialization"

# Day 3-4: VersionedEntity  
/tdd --component "VersionedEntity" --tests "versioning, history, state_retrieval"

# Day 5: Core Types
/tdd --component "InvalidationRule,StateChange,EventType" --tests "basic_operations"
```

### Week 2: Domain Layer Completion + Application Layer Start
```bash
# Day 1-2: Complete Domain Layer
/tdd --component "Domain Integration" --tests "cross_component_interactions"

# Day 3-5: EventRecorderService
/tdd --component "EventRecorderService" --tests "recording, validation, batching"
```

### Week 3-4: Application Layer Services
```bash
# Using /4layer to maintain clean architecture
/4layer --layer "application" --component "VersioningService"
/tdd --component "VersioningService" --tests "version_management"

/4layer --layer "application" --component "InvalidationEngine"
/tdd --component "InvalidationEngine" --tests "rule_processing, cascades"

/4layer --layer "application" --component "StateReconstructionService"
/tdd --component "StateReconstructionService" --tests "reconstruction, performance"
```

### Week 5-6: Infrastructure Layer
```bash
# Mock-first approach for external dependencies
/4layer --layer "infrastructure" --component "EventRepository"
/tdd --component "EventRepository" --mocks "firestore" --tests "CRUD, queries"

/4layer --layer "infrastructure" --component "StateSnapshotCache"
/tdd --component "StateSnapshotCache" --tests "caching, invalidation"
```

### Week 7-8: Presentation Layer + Integration
```bash
# Presentation layer with focus on AI integration
/4layer --layer "presentation" --component "WorldStatePromptFormatter"
/tdd --component "PromptFormatter" --tests "formatting, token_efficiency"

# Integration testing
/tdd --integration --tests "end_to_end_workflows"
```

### Week 9: Polish + Performance
```bash
# Performance optimization
/tdd --performance --component "StateReconstruction" --target "<100ms for 1000 events"

# Final integration
/4layer --integration --all-layers
```

## TDD Implementation Plan

### Phase 1: Event Recording System (Week 1-2)

#### Red Phase - Write Failing Tests

**Test File: `test_world_events.py`**

```python
def test_create_world_event():
    """Test that WorldEvent captures all required fields"""
    event = WorldEvent(
        event_type="npc_death",
        affected_entities=["npc_guard_001"],
        changes={"hp_current": 0, "status": "deceased"},
        narrative_reference="seq_142"
    )
    assert event.event_id is not None
    assert event.timestamp is not None
    assert event.event_type == "npc_death"
    assert "npc_guard_001" in event.affected_entities
    assert event.changes["status"] == "deceased"
    assert event.narrative_reference == "seq_142"

def test_event_cascade_tracking():
    """Test that events can track cascade effects"""
    event = WorldEvent(
        event_type="king_death",
        affected_entities=["npc_king_001"],
        changes={"status": "deceased"},
        cascade_effects=["succession_crisis", "alliance_shift"]
    )
    assert len(event.cascade_effects) == 2
    assert "succession_crisis" in event.cascade_effects

def test_event_serialization():
    """Test event can be serialized/deserialized for storage"""
    event = WorldEvent(...)
    json_data = event.to_json()
    restored = WorldEvent.from_json(json_data)
    assert restored.event_id == event.event_id
```

#### Green Phase - Minimal Implementation

```python
# world_events.py
from datetime import datetime
import json
import uuid

class WorldEvent:
    def __init__(self, event_type, affected_entities, changes, 
                 narrative_reference=None, cascade_effects=None):
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.event_type = event_type
        self.affected_entities = affected_entities
        self.changes = changes
        self.narrative_reference = narrative_reference
        self.cascade_effects = cascade_effects or []
    
    def to_json(self):
        return json.dumps({
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'affected_entities': self.affected_entities,
            'changes': self.changes,
            'narrative_reference': self.narrative_reference,
            'cascade_effects': self.cascade_effects
        })
```

#### Refactor Phase
- Add validation for event types
- Create EventRecorder service to manage event storage
- Add event compression for similar events

### Phase 2: State Versioning (Week 3-4)

#### Red Phase - Write Failing Tests

```python
def test_entity_versioning():
    """Test that entities get version numbers"""
    entity = VersionedEntity("npc_guard_001", {"name": "Guard"})
    assert entity.version == 1
    assert entity.entity_id == "npc_guard_001"

def test_version_increment_on_change():
    """Test version increments with changes"""
    entity = VersionedEntity("npc_guard_001", {"hp": 20})
    entity.update({"hp": 15}, event_id="evt_001")
    assert entity.version == 2
    assert entity.current_state["hp"] == 15

def test_retrieve_historical_version():
    """Test retrieving entity at specific version"""
    entity = VersionedEntity("npc_guard_001", {"hp": 20})
    entity.update({"hp": 15}, event_id="evt_001")
    entity.update({"hp": 10}, event_id="evt_002")
    
    state_v2 = entity.get_version(2)
    assert state_v2["hp"] == 15
```

#### Green Phase - Implementation

```python
# versioned_entities.py
class VersionedEntity:
    def __init__(self, entity_id, initial_state):
        self.entity_id = entity_id
        self.version = 1
        self.current_state = initial_state.copy()
        self.change_history = []
        self.last_modified = datetime.now()
    
    def update(self, changes, event_id):
        change_record = StateChange(
            from_version=self.version,
            to_version=self.version + 1,
            event_id=event_id,
            changes=changes
        )
        self.change_history.append(change_record)
        self.current_state.update(changes)
        self.version += 1
        self.last_modified = datetime.now()
```

### Phase 3: Invalidation Rules Engine (Week 5-6)

#### Red Phase - Write Failing Tests

```python
def test_time_based_invalidation():
    """Test that time-based rules expire data"""
    rule = InvalidationRule(
        trigger_type="time_based",
        conditions={"days_elapsed": 30},
        affected_patterns=["merchant_gratitude_*"]
    )
    
    event = WorldEvent(
        event_type="merchant_saved",
        affected_entities=["npc_merchant_001"],
        changes={"gratitude": "high"}
    )
    
    # 31 days later...
    assert rule.should_invalidate(event, days_elapsed=31) == True

def test_event_based_invalidation():
    """Test that specific events trigger invalidation"""
    rule = InvalidationRule(
        trigger_type="event_based",
        conditions={"event_type": "attack_ally"},
        affected_patterns=["alliance_*"]
    )
    
    trigger_event = WorldEvent(event_type="attack_ally", ...)
    assert rule.should_trigger(trigger_event) == True

def test_cascade_invalidation():
    """Test cascade effects propagate"""
    rules_engine = InvalidationEngine()
    rules_engine.add_rule(...)
    
    king_death_event = WorldEvent(event_type="king_death", ...)
    cascaded_events = rules_engine.process_cascades(king_death_event)
    
    assert len(cascaded_events) > 0
    assert any(e.event_type == "succession_crisis" for e in cascaded_events)
```

### Phase 4: State Reconstruction (Week 7-8)

#### Red Phase - Write Failing Tests

```python
def test_reconstruct_world_state():
    """Test reconstructing state from base + events"""
    base_state = {
        "npc_data": {
            "Guard": {"hp": 20, "status": "alive"}
        }
    }
    
    events = [
        WorldEvent(
            event_type="combat_damage",
            affected_entities=["Guard"],
            changes={"hp": 15}
        ),
        WorldEvent(
            event_type="npc_death",
            affected_entities=["Guard"],
            changes={"hp": 0, "status": "dead"}
        )
    ]
    
    reconstructed = reconstruct_world_state(base_state, events, target_time=events[1].timestamp)
    assert reconstructed["npc_data"]["Guard"]["status"] == "dead"
    assert reconstructed["npc_data"]["Guard"]["hp"] == 0

def test_reconstruction_performance():
    """Test performance with many events"""
    base_state = create_large_world()
    events = generate_events(count=1000)
    
    start_time = time.time()
    reconstructed = reconstruct_world_state(base_state, events)
    elapsed = time.time() - start_time
    
    assert elapsed < 0.1  # Must be under 100ms
```

### Phase 5: Integration (Week 9)

#### Integration Tests

```python
def test_game_state_with_events():
    """Test that game state updates generate events"""
    game_state = GameState()
    
    # Simulate state update
    update = {
        "npc_data": {
            "Guard": {"hp": 0, "status": "dead"}
        }
    }
    
    game_state.apply_update(update)
    
    # Check event was recorded
    events = game_state.get_events()
    assert len(events) == 1
    assert events[0].event_type == "npc_death"

def test_prompt_integration():
    """Test that AI prompts include event context"""
    prompt = generate_game_prompt(include_events=True)
    assert "world_events" in prompt
    assert "version" in prompt
```

## Implementation Status

### Week 1-2: Event Recording ⬜
- [ ] WorldEvent class implementation
- [ ] EventRecorder service
- [ ] Event serialization
- [ ] Integration with game state updates

### Week 3-4: State Versioning ⬜
- [ ] VersionedEntity wrapper
- [ ] VersionManager service  
- [ ] Change history tracking
- [ ] Historical state retrieval

### Week 5-6: Invalidation Rules ⬜
- [ ] InvalidationRule class
- [ ] Rules engine implementation
- [ ] Time-based invalidation
- [ ] Event-based triggers
- [ ] Cascade processing

### Week 7-8: State Reconstruction ⬜
- [ ] Reconstruction algorithm
- [ ] Performance optimization
- [ ] Caching layer
- [ ] Rollback capability

### Week 9: Integration & Testing ⬜
- [ ] Modify game_state_instruction.md
- [ ] Update state format
- [ ] End-to-end testing
- [ ] Performance benchmarks

## Key Design Decisions

1. **Event-First Architecture**: All changes go through events
2. **Immutable Events**: Events cannot be modified after creation
3. **Lazy Reconstruction**: Only rebuild state when needed
4. **Compression Strategy**: Similar events batch together
5. **Token Optimization**: Old events compressed/summarized

## Performance Targets

- Event creation: <5ms
- State reconstruction (1000 events): <100ms  
- Memory usage: <1MB per 1000 events
- Token usage: <100 tokens per event batch

## Architecture Benefits

### Why Four Layers?
1. **Testability**: Each layer can be tested in isolation
2. **Maintainability**: Clear separation of concerns
3. **Flexibility**: Easy to swap implementations (e.g., Firestore → PostgreSQL)
4. **Scalability**: Can optimize each layer independently
5. **Team Development**: Different developers can work on different layers

### Development Order Strategy
1. **Domain First**: Pure logic, no dependencies, 100% testable
2. **Application Second**: Use cases with mocked infrastructure
3. **Infrastructure Third**: Real implementations with integration tests
4. **Presentation Last**: UI/AI interface once core is solid

### Testing Strategy by Layer
- **Domain**: Pure unit tests, no mocks needed
- **Application**: Unit tests with mocked repositories
- **Infrastructure**: Integration tests with real/test databases
- **Presentation**: Contract tests with AI prompt system

## Coding Execution Plan

### Step 1: Project Setup
```bash
# Create directory structure
mkdir -p mvp_site/world_state/{domain,application,infrastructure,presentation}
mkdir -p mvp_site/tests/world_state/{domain,application,infrastructure,presentation,integration}

# Create __init__.py files
touch mvp_site/world_state/__init__.py
touch mvp_site/world_state/{domain,application,infrastructure,presentation}/__init__.py

# Create base test file
touch mvp_site/tests/world_state/test_base.py
```

### Step 2: Domain Layer Implementation Order
1. **EventType Enum** (30 min)
   - Define all event types
   - No tests needed for enum

2. **WorldEvent Class** (2 hours)
   - Test: Creation with required fields
   - Test: Validation of event types
   - Test: Immutability
   - Test: Serialization

3. **StateChange Class** (1 hour)
   - Test: Record changes
   - Test: Apply to state
   - Test: Reverse changes

4. **VersionedEntity Class** (2 hours)
   - Test: Version increments
   - Test: History tracking
   - Test: State retrieval at version

5. **InvalidationRule Class** (2 hours)
   - Test: Pattern matching
   - Test: Condition evaluation
   - Test: Priority comparison

### Step 3: Key Integration Points

#### With Existing Game State
```python
# Adapter pattern for current game state
class GameStateEventAdapter:
    def convert_state_update_to_events(self, state_update):
        """Convert current state update format to events"""
        
    def enhance_state_with_versions(self, game_state):
        """Add version info to existing state"""
```

#### With AI Prompts
```python
# Enhance prompts with event context
class PromptEnhancer:
    def add_event_context(self, prompt, current_scene):
        """Add relevant historical events to prompt"""
        
    def format_world_version(self, entities):
        """Include version numbers in entity descriptions"""
```

## Next Steps

1. Start with Event Recording System tests
2. Set up test framework and CI
3. Create development branch
4. Begin red-green-refactor cycle

## Branch: feature/dynamic-world-state-v2
## PR: #501 - https://github.com/jleechan2015/worldarchitect.ai/pull/501

## Current UI Integration Strategy (Based on Codebase Analysis)

### Discovered Architecture
- **SPA with API**: Single-page app using vanilla JS + Flask API
- **No Templates**: All rendering happens client-side in JavaScript
- **Story Display**: Content shown in `#story-content` div
- **appendToStory()**: Main function that adds narrative to UI

### Integration Points Identified

#### 1. Story Entry Enhancement
```javascript
// app.js - Extend existing appendToStory function
function appendToStory(content, isUser = false) {
    const storyEntry = document.createElement('div');
    storyEntry.className = 'story-entry ' + (isUser ? 'user-entry' : 'ai-entry');
    
    // ... existing narrative rendering ...
    
    // NEW: Add world event indicators
    if (content.world_events && content.world_events.length > 0) {
        const indicator = document.createElement('div');
        indicator.className = 'world-event-indicator';
        indicator.innerHTML = `
            <i class="fas fa-globe"></i>
            <span>${content.world_events.length} world change${content.world_events.length > 1 ? 's' : ''}</span>
        `;
        indicator.onclick = () => showEventDetails(content.world_events);
        storyEntry.appendChild(indicator);
    }
    
    document.getElementById('story-content').appendChild(storyEntry);
}
```

#### 2. API Response Enhancement
```python
# main.py - Minimal change to interaction endpoint
@app.route('/api/campaigns/<campaign_id>/interaction', methods=['POST'])
def handle_interaction(user_id, campaign_id):
    # ... existing code through AI response generation ...
    
    # NEW: Extract world events if feature enabled
    campaign_settings = campaign_data.get('settings', {})
    if campaign_settings.get('dynamic_world_state', {}).get('enabled', False):
        from world_state.application import event_recorder
        events = event_recorder.extract_events_from_interaction(
            user_input=user_input,
            ai_response=ai_response,
            game_state=game_state,
            story_context=story
        )
        # Add to response
        structured_fields['world_events'] = [e.to_dict() for e in events]
        # Store events
        event_recorder.store_events(campaign_id, events)
    
    return jsonify(response_data)
```

#### 3. CSS for World State Elements
```css
/* style.css additions */
.world-event-indicator {
    margin-top: 0.5rem;
    padding: 0.25rem 0.5rem;
    background: rgba(99, 102, 241, 0.1);
    border-radius: 4px;
    font-size: 0.875rem;
    color: #6366f1;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}

.world-event-indicator:hover {
    background: rgba(99, 102, 241, 0.2);
}

/* Post-session recap overlay */
.session-recap-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}
```

### Four-Layer Implementation Plan

#### Layer 1: Domain Layer
```python
# mvp_site/world_state/domain/__init__.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any
import uuid

@dataclass
class WorldEvent:
    event_type: str  # NPC_DEATH, ALLIANCE_FORMED, etc.
    affected_entities: List[str]
    changes: Dict[str, Any]
    narrative_reference: str  # Links to story entry
    cascade_effects: List[str] = None
    event_id: str = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self):
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'affected_entities': self.affected_entities,
            'changes': self.changes,
            'timestamp': self.timestamp.isoformat()
        }
```

#### Layer 2: Application Layer
```python
# mvp_site/world_state/application/event_recorder.py
from typing import List
import re
from ..domain import WorldEvent

class EventRecorderService:
    def extract_events_from_interaction(self, user_input, ai_response, game_state, story_context):
        """Extract world events from gameplay interaction"""
        events = []
        
        # Extract from narrative
        narrative = ai_response.get('narrative', '')
        
        # Death detection
        death_patterns = [
            r'(\w+) (?:dies|is killed|perishes|falls)',
            r'You (?:kill|slay|defeat) (\w+)',
            r'(\w+) is (?:dead|deceased|no more)'
        ]
        
        for pattern in death_patterns:
            matches = re.findall(pattern, narrative, re.IGNORECASE)
            for match in matches:
                entity = match[0] if isinstance(match, tuple) else match
                if entity in game_state.get('npc_data', {}):
                    events.append(WorldEvent(
                        event_type='NPC_DEATH',
                        affected_entities=[entity],
                        changes={'status': 'deceased'},
                        narrative_reference=f"scene_{len(story_context)}"
                    ))
        
        # Alliance/relationship changes
        alliance_patterns = [
            r'(\w+) (?:joins your party|becomes your ally)',
            r'alliance with (\w+)',
            r'(\w+) pledges loyalty'
        ]
        
        for pattern in alliance_patterns:
            matches = re.findall(pattern, narrative, re.IGNORECASE)
            for match in matches:
                entity = match[0] if isinstance(match, tuple) else match
                events.append(WorldEvent(
                    event_type='ALLIANCE_FORMED',
                    affected_entities=[entity, 'player'],
                    changes={'relationship': 'allied'},
                    narrative_reference=f"scene_{len(story_context)}"
                ))
        
        return events
```

#### Layer 3: Infrastructure Layer
```python
# mvp_site/world_state/infrastructure/firestore_repository.py
from ..domain import WorldEvent
from firestore_service import db

class FirestoreEventRepository:
    def __init__(self):
        self.collection = 'world_events'
    
    def save_events(self, campaign_id: str, events: List[WorldEvent]):
        """Save events to Firestore"""
        batch = db.batch()
        
        for event in events:
            doc_ref = db.collection(self.collection).document()
            batch.set(doc_ref, {
                'campaign_id': campaign_id,
                **event.to_dict()
            })
        
        batch.commit()
    
    def get_events_for_recap(self, campaign_id: str, session_num: int):
        """Get events for session recap"""
        # Query events for this session
        return db.collection(self.collection).where(
            'campaign_id', '==', campaign_id
        ).where(
            'session_num', '==', session_num
        ).get()
```

#### Layer 4: Presentation Layer
```javascript
// mvp_site/static/js/world-state-ui.js
class WorldStateUI {
    constructor() {
        this.events = [];
    }
    
    showEventDetails(events) {
        // Simple modal for phase 1
        const modal = document.createElement('div');
        modal.className = 'world-event-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>World Changes</h3>
                <ul>
                    ${events.map(e => `
                        <li>
                            <i class="fas fa-${this.getEventIcon(e.event_type)}"></i>
                            ${this.formatEvent(e)}
                        </li>
                    `).join('')}
                </ul>
                <button onclick="this.parentElement.parentElement.remove()">Close</button>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    getEventIcon(eventType) {
        const icons = {
            'NPC_DEATH': 'skull',
            'ALLIANCE_FORMED': 'handshake',
            'LOCATION_DISCOVERED': 'map-marker',
            'ITEM_ACQUIRED': 'gem'
        };
        return icons[eventType] || 'circle';
    }
    
    formatEvent(event) {
        const formatters = {
            'NPC_DEATH': e => `${e.affected_entities[0]} has died`,
            'ALLIANCE_FORMED': e => `Alliance formed with ${e.affected_entities[0]}`,
            'LOCATION_DISCOVERED': e => `Discovered ${e.affected_entities[0]}`,
            'ITEM_ACQUIRED': e => `Acquired ${e.affected_entities[0]}`
        };
        return formatters[event.event_type]?.(event) || event.event_type;
    }
}

// Initialize
const worldStateUI = new WorldStateUI();
window.showEventDetails = (events) => worldStateUI.showEventDetails(events);
```

### Progressive Rollout Plan

#### Week 1: Foundation
1. Create domain models
2. Basic event extraction
3. Simple UI indicators

#### Week 2: Storage & Retrieval  
1. Firestore integration
2. Event querying
3. Session detection

#### Week 3: Post-Session Recap
1. Detect session end
2. Generate recap data
3. Display recap overlay

#### Week 4: World History Tab
1. Add tab to UI
2. Event timeline view
3. Basic filtering

### Feature Flags
```python
# Campaign settings structure
{
    "dynamic_world_state": {
        "enabled": false,  # Master switch
        "features": {
            "event_indicators": true,
            "post_session_recap": false,
            "world_history_tab": false,
            "relationship_graph": false
        },
        "event_retention_days": 90,
        "max_events_per_session": 100
    }
}
```

## UI/UX Design and Placement

### UI Features Overview

#### Player-Facing Features
1. **Campaign Timeline View** - Interactive timeline of major events
2. **Consequence Tracker** - Visual flow charts showing cause → effect
3. **NPC Relationship Map** - Network graph with trust indicators
4. **World State Comparison** - Before/after slider views
5. **Personal Impact Dashboard** - Stats and achievements

#### GM/Debug Features
1. **Event Inspector** - Real-time event stream with filtering
2. **State Time Machine** - Scrub through any timestamp
3. **Rule Configuration UI** - Visual invalidation rule editor

### UI Placement Strategy

#### 1. During Gameplay (Minimal)
- **Collapsible Side Panel**: Shows last 5 events, quick stats
- **Inline Notifications**: Subtle toasts for world updates
- **Design Principle**: Enhance, don't distract

#### 2. Post-Session Summary (Primary)
- **Automatic Recap Screen**: Shows session impact
- **Shareable Summary**: Social media integration
- **Key Events Timeline**: Visual cause/effect for session

#### 3. Campaign Dashboard (Deep Dive)
- **New "World History" Tab**: Full visualization suite
- **Between Sessions**: Explore at leisure
- **Export Options**: Download timeline, share states

#### 4. Mobile Companion
- **Quick Event Swipe View**
- **Push Notifications**: "Your rival made a move!"
- **Offline History Access**

### Implementation Phases

#### UI Phase 1: Post-Session Summary (Week 10-11)
```typescript
// React components
interface SessionRecap {
  events: WorldEvent[];
  consequences: ConsequenceChain[];
  stats: ImpactStats;
}

<SessionRecapScreen
  session={currentSession}
  onShare={handleSocialShare}
  onViewFullHistory={navigateToDashboard}
/>
```

#### UI Phase 2: Dashboard Integration (Week 12-13)
```typescript
// New route: /campaign/:id/history
<WorldHistoryDashboard>
  <TimelineView events={allEvents} />
  <RelationshipGraph entities={npcs} />
  <ConsequenceExplorer root={selectedEvent} />
</WorldHistoryDashboard>
```

#### UI Phase 3: In-Game Panel (Week 14)
```typescript
// Minimal real-time view
<CollapsibleWorldPanel
  recentEvents={last5Events}
  quickStats={reputationChanges}
  isCollapsed={userPreference}
/>
```

### Technical Stack for UI

#### Frontend Libraries
- **React/Vue**: Component framework
- **D3.js**: Timeline and graph visualizations
- **React Flow**: Consequence flow charts
- **Framer Motion**: State change animations

#### Performance Optimization
- Virtual scrolling for event lists
- Progressive data loading
- Client-side visualization caching
- WebSocket for real-time updates

### URL Structure
```
/campaign/{id}/play                    # Main game
/campaign/{id}/history                 # World state dashboard
/campaign/{id}/history/timeline        # Timeline view
/campaign/{id}/history/relationships   # NPC relationships
/campaign/{id}/recap/{session}         # Session summary
```

### API Endpoints for UI
```python
# Minimal during gameplay
GET /api/campaign/{id}/events/recent?limit=5

# Post-session summary
GET /api/campaign/{id}/session/{num}/recap

# Full dashboard access
GET /api/campaign/{id}/events?from={date}&to={date}
GET /api/campaign/{id}/relationships
GET /api/campaign/{id}/consequences/{event_id}
```

### Progressive Feature Disclosure
- **Free Tier**: Basic recap, last 10 events
- **Premium**: Full timeline, interactive visualizations
- **GM Tier**: Debug tools, event injection, rule config

## Success Metrics

- **Narrative consistency score**: <5% contradictions reported
- **Player satisfaction**: "World remembers my actions" feedback
- **Performance**: <100ms state reconstruction for 1000 events
- **Storage**: <1MB per 20-session campaign
- **Engagement**: 60%+ of players view post-session recaps
- **Retention**: 25% higher campaign completion rate

## Marketing Angle

"The AI GM with Perfect Memory - Your choices echo through time"

- **Key Message**: Every action matters, every choice remembered
- **Target Audience**: Serious tabletop players who value immersion
- **Differentiator**: Only platform with true persistent world state
- **Social Proof**: Shareable timeline/consequence visualizations

## Configuration Options

```python
campaign_settings = {
    "dynamic_world_state": {
        "enabled": True,
        "event_retention_days": 90,
        "max_events_per_session": 100,
        "invalidation_aggressiveness": "medium",
        "cascade_depth_limit": 3
    }
}
```

## UI Mockups Created (PR #504)

### Interactive HTML/CSS Prototypes
Complete mockups demonstrating all UI integration patterns:

1. **Campaign Integration** (`/tmp/worldarchitectai/mocks/world_mocks/campaign_real_ui.html`)
   - World event indicators inline with story
   - Floating widget showing recent events
   - Mini timeline visualization
   - Non-intrusive design matching actual UI

2. **Session Recap** (`/tmp/worldarchitectai/mocks/world_mocks/session_recap_real.html`)
   - Post-session overlay with dark theme
   - Session statistics and achievements
   - Major world changes highlighted
   - Consequence tracking visualization

3. **World History Tab** (`/tmp/worldarchitectai/mocks/world_mocks/world_history_tab.html`)
   - Full timeline with filtering and search
   - Event categorization (Combat, Social, Discovery)
   - Statistics dashboard (147 events, 23 major changes, etc.)
   - Session separation markers

4. **Timeline Integration** (`/tmp/worldarchitectai/mocks/world_mocks/timeline_integration.html`)
   - Two-column layout: story + live timeline
   - Interactive highlighting between timeline and story
   - Sticky sidebar that follows scroll
   - Bi-directional navigation

5. **Mobile Responsive** (`/tmp/worldarchitectai/mocks/world_mocks/mobile_responsive.html`)
   - Floating action button (FAB) for world state
   - Bottom slide-up panel
   - Touch-optimized timeline
   - Responsive layout for all screen sizes

6. **Component Library**
   - Timeline View (`timeline_view.html`) - Zoomable timeline component
   - Relationships Graph (`relationships.html`) - NPC network visualization
   - In-Game Panel (`ingame_panel.html`) - Collapsible side panel

### Mockup Index
- Main index: `/tmp/worldarchitectai/mocks/world_mocks/index.html`
- Links to all mockups with descriptions
- Technical implementation notes
- Integration strategy overview

### Key Design Decisions from Mockups
- **Progressive Enhancement**: Works without JavaScript, enhanced with it
- **Non-intrusive**: Features don't disrupt core gameplay
- **Multiple Access Patterns**: Widget, tab, sidebar, overlay approaches
- **Responsive**: Mobile-first design considerations
- **Dark Theme Support**: Overlays use dark theme for immersion

## Context Links
- Original design: PR #294
- Complete specification: This document (scratchpad)
- Player benefits analysis: Complete
- Technical architecture: Defined
- Four-layer plan: Complete
- TDD approach: Detailed
- UI/UX design: Complete with HTML mockups
- Interactive mockups: PR #504 (MERGED)
- Marketing & metrics: Defined