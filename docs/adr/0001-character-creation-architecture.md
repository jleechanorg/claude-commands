# ADR-0001: Character Creation Architecture

**Status**: Accepted
**Date**: 2025-07-14
**Participants**: Claude (analysis), Gemini (architecture consultation)

## Context

The character creation system needs reorganization to support three creation paths (AIGenerated, StandardDND, CustomClass) with proper state management and planning block integration. Git history shows repeated refactoring patterns where simple implementations evolve to complex ones (string → JSON migrations).

## Decision

### 1. Temporary Builder Pattern
- Create `CharacterCreationState` as a temporary builder in Firestore collection `character_creation_sessions`
- Include `expires_at` timestamp field for cleanup via scheduled Cloud Function
- Delete after successful character creation

### 2. Strategy Pattern for Creation Paths
```python
class BaseCreationStrategy(ABC):
    # 80% shared logic: ability scores, equipment, etc.

class AIGeneratedStrategy(BaseCreationStrategy):
    # AI-specific logic only

class StandardDNDStrategy(BaseCreationStrategy):
    # Standard D&D specific logic only

class CustomClassStrategy(BaseCreationStrategy):
    # Custom class specific logic only
```

### 3. Planning Block Templates
- Store as `PlanningBlockTemplate` models in Firestore
- Include `template_version` field for future migrations
- Transform older versions on-the-fly in application code

### 4. Character Model Extension
- Extend existing `mvp_site/schemas/entities_pydantic.py::Character` class
- Combat-specific fields marked as `Optional` with sensible defaults
- Single source of truth for character data

### 5. Integration Flow
1. Start: Create document in `character_creation_sessions`
2. Build: Update single Firestore document as user progresses
3. Finalize: Validate and create permanent Character
4. Update: Caller updates GameState.player_character_data
5. Cleanup: Delete temporary session document

### 6. Migration Strategy
- Dedicated Python script using `logging_util`
- Log to `character_migration.log` for audit trail
- Handle failures gracefully with detailed error logging

## Consequences

### Positive
- Avoids data duplication between creation state and final character
- Handles page refreshes and abandoned sessions gracefully
- Extensible for new creation paths without modifying core logic
- Clear separation of concerns
- Audit trail for data migrations

### Negative
- Requires Cloud Function for session cleanup
- More complex than simple if/else for 3 paths
- Template versioning adds complexity

## Alternatives Considered

1. **Single Service with Methods**: Rejected due to violation of Open/Closed Principle
2. **Session Storage**: Rejected due to fragility with refreshes
3. **Separate Character Models**: Rejected due to data synchronization complexity
4. **JSON File Templates**: Rejected in favor of Firestore for consistency

## Implementation Notes

- Use existing `logging_util` for migration script
- Firestore TTL via Cloud Function with daily cleanup
- Planning block templates need initial seed data
- Character version field starts at 2 (current implied version is 1)

## References
- Character Creation Reorganization Plan: `/roadmap/character_creation_reorganization_plan.md`
- Existing Character Model: `/mvp_site/schemas/entities_pydantic.py`
- Architecture Discussion: `/roadmap/scratchpad_architecture_decision_framework.md`
