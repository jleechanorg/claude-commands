# Domain-Driven Design Architecture Refactoring Scratchpad

**Branch**: architecture_refactor_2025  
**Started**: 2025-07-08  
**Goal**: Transform WorldArchitect.AI from a monolithic Flask app to a clean, domain-driven architecture

## 🎯 Executive Summary

This refactoring aims to transform WorldArchitect.AI from its current monolithic structure into a scalable, maintainable architecture based on Domain-Driven Design (DDD) and Clean Architecture principles. The refactoring will be performed incrementally to ensure zero disruption to existing users while preparing the platform for future growth.

## 📊 Current State Analysis

### Architecture Overview
- **Type**: Monolithic Flask application
- **Main Entry**: `main.py` (~2000 lines, handling routing, business logic, and orchestration)
- **Dependencies**: Tightly coupled to Firebase, Gemini AI, and frontend
- **Testing**: 124 tests, but mixed unit/integration without clear boundaries

### Key Components
1. **main.py**: Core application (routes, campaign management, AI orchestration)
2. **game_state.py**: Campaign state management
3. **gemini_service.py**: AI integration
4. **firestore_service.py**: Database operations
5. **Frontend**: Vanilla JS with Bootstrap (tightly coupled to backend structure)

### Current Pain Points
1. **Monolithic Design**: main.py handles too many responsibilities
2. **Tight Coupling**: Business logic mixed with infrastructure concerns
3. **Testing Challenges**: Difficult to test business logic in isolation
4. **Scalability Issues**: Hard to add new features without touching core code
5. **Debug System**: Mixed concerns between display and data storage
6. **AI Integration**: Tightly coupled to specific Gemini implementation
7. **State Management**: No clear separation between domain state and persistence

## 🏗️ Proposed Architecture

### Domain-Driven Design Structure
```
worldarchitect/
├── domain/                 # Core business logic (no dependencies)
│   ├── campaign/          # Campaign aggregate
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── events/
│   │   └── repository.py
│   ├── narrative/         # Narrative generation bounded context
│   ├── combat/           # Combat system bounded context
│   └── player/           # Player management bounded context
├── application/          # Use cases and orchestration
│   ├── commands/
│   ├── queries/
│   └── services/
├── infrastructure/       # External dependencies
│   ├── persistence/     # Database implementations
│   ├── ai/             # AI service implementations
│   └── web/            # Flask/API layer
└── tests/
    ├── unit/           # Pure domain logic tests
    ├── integration/    # Cross-layer tests
    └── e2e/           # End-to-end tests
```

### Key Design Principles

#### 1. Hexagonal Architecture
- Core domain has no external dependencies
- Ports and adapters for all external systems
- Dependency injection for flexibility

#### 2. Bounded Contexts
- **Campaign Context**: Campaign lifecycle, state management
- **Narrative Context**: Story generation, scene management
- **Combat Context**: Combat rules, dice rolling
- **Player Context**: Character management, authentication

#### 3. Event-Driven Design
- Domain events for important state changes
- Eventual consistency between contexts
- Audit trail and replay capability

## 📋 Implementation Phases

### Phase 1: Domain Layer Foundation (Week 1-2)
**Goal**: Extract core business logic into pure domain objects

1. **Campaign Aggregate**
   - Extract Campaign entity from current game_state
   - Create value objects: CampaignId, SceneNumber, TurnNumber
   - Define domain events: CampaignCreated, ScenePlayed, CombatInitiated
   - Create repository interface

2. **Narrative Domain**
   - Extract narrative generation logic
   - Create NarrativeRequest/Response value objects
   - Define NarrativeGenerator interface

3. **Initial Testing**
   - Unit tests for all domain objects
   - No infrastructure dependencies

### Phase 2: Application Layer (Week 3-4)
**Goal**: Implement use cases and orchestration

1. **Command Handlers**
   - CreateCampaignCommand
   - PlayTurnCommand
   - InitiateCombatCommand
   - SaveGameCommand

2. **Query Handlers**
   - GetCampaignQuery
   - ListCampaignsQuery
   - GetCampaignHistoryQuery

3. **Application Services**
   - CampaignOrchestrator
   - NarrativeOrchestrator
   - CombatOrchestrator

### Phase 3: Infrastructure Adapters (Week 5-6)
**Goal**: Implement infrastructure without changing domain

1. **Persistence Adapters**
   - FirestoreCampaignRepository
   - InMemoryCampaignRepository (for testing)
   - Migration scripts for existing data

2. **AI Adapters**
   - GeminiNarrativeGenerator
   - OpenAINarrativeGenerator (future)
   - MockNarrativeGenerator (for testing)

3. **Web Adapters**
   - RESTful API controllers
   - WebSocket support for real-time features
   - GraphQL endpoint (future)

### Phase 4: API Layer Refactoring (Week 7-8)
**Goal**: Clean REST API with proper versioning

1. **API Design**
   ```
   /api/v2/campaigns          # List campaigns
   /api/v2/campaigns/{id}     # Get campaign
   /api/v2/campaigns/{id}/play # Play turn
   /api/v2/campaigns/{id}/history # Get history
   ```

2. **Backwards Compatibility**
   - Maintain v1 endpoints during transition
   - Adapter layer to translate between versions

### Phase 5: Frontend Decoupling (Week 9-10)
**Goal**: Separate frontend from backend structure

1. **API Client Library**
   - JavaScript SDK for API communication
   - Type definitions for all API contracts
   - Offline support with local storage

2. **State Management**
   - Introduce proper frontend state management
   - Remove direct coupling to backend models

### Phase 6: Migration and Deployment (Week 11-12)
**Goal**: Safe migration with zero downtime

1. **Data Migration**
   - Scripts to transform existing campaign data
   - Validation tools to ensure data integrity
   - Rollback procedures

2. **Deployment Strategy**
   - Feature flags for gradual rollout
   - A/B testing between old and new architecture
   - Performance monitoring

## 🔄 Migration Strategy

### Strangler Fig Pattern
1. New features built in new architecture
2. Gradually migrate existing features
3. Old code removed once fully migrated

### Data Migration
1. **Dual Write**: New code writes to both old and new structure
2. **Background Migration**: Scripts to migrate historical data
3. **Validation**: Automated checks for data consistency

### Risk Mitigation
1. **Feature Flags**: Toggle between old and new implementations
2. **Comprehensive Testing**: Each phase fully tested before proceeding
3. **Rollback Plan**: Quick reversion capability at each phase

## 📈 Success Metrics

1. **Code Quality**
   - Reduced coupling (measured by dependency graphs)
   - Increased test coverage (target: 90% for domain layer)
   - Reduced main.py size (from 2000 to <500 lines)

2. **Performance**
   - API response time improvement (target: 20% faster)
   - Reduced memory usage
   - Better caching strategies

3. **Developer Experience**
   - Faster feature development
   - Easier onboarding for new developers
   - Better debugging capabilities

## 🚧 Current Progress

### Completed
- [x] Architecture analysis and planning
- [x] Created refactoring scratchpad
- [x] Created domain layer package structure
- [x] Implemented Campaign aggregate root with:
  - Value objects: CampaignId, SceneNumber, TurnNumber
  - Entity: Campaign with full business logic
  - Events: CampaignCreated, SceneStarted, TurnPlayed, etc.
  - Repository interface: CampaignRepository
- [x] Created comprehensive unit tests (37 tests, all passing)

### In Progress
- [ ] Designing application layer (use cases and commands)

### Next Steps
1. Create command handlers for campaign operations
2. Create query handlers for retrieving campaign data
3. Design application services for orchestration

## 📝 Technical Decisions Log

### 2025-07-08: Architecture Style Decision
**Decision**: Hexagonal Architecture with DDD
**Reasoning**: 
- Clear separation of concerns
- Testability of business logic
- Flexibility for future changes
- Industry standard for complex domains

### 2025-07-08: Event Sourcing Consideration
**Decision**: Event-driven but not full event sourcing
**Reasoning**:
- Events for important state changes
- Traditional state storage for simplicity
- Can migrate to event sourcing later if needed

### 2025-07-08: Domain Model Implementation
**Decision**: Pure domain entities with no framework dependencies
**Reasoning**:
- Domain logic completely isolated from infrastructure
- Value objects ensure type safety and validation
- Events enable decoupled integration
- Repository pattern allows flexible persistence

## 🔗 References

1. **Domain-Driven Design** by Eric Evans
2. **Clean Architecture** by Robert C. Martin
3. **Implementing Domain-Driven Design** by Vaughn Vernon
4. **Building Microservices** by Sam Newman (for future considerations)

## 📋 Next Actions

1. Start extracting Campaign entity from game_state.py
2. Create value objects for core concepts
3. Write comprehensive tests for domain objects
4. Document domain model with diagrams

---

**Status**: 🟢 Active Development  
**Last Updated**: 2025-07-08 20:55 UTC