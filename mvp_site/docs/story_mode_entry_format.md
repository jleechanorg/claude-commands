# Story Mode Entry Format Specification (TASK-101)

## Overview
Standardize the format for story mode entries to ensure consistency across the application, improve parsing reliability, and enable better feature development.

## Current State Analysis

### Existing Formats
Currently, story entries exist in multiple formats:
1. **Plain text narratives**
2. **JSON with mixed structure**
3. **HTML-formatted content**
4. **Markdown-style formatting**

### Issues with Current Approach
- Inconsistent parsing requirements
- Difficult to extract metadata
- No standard for planning blocks
- Mixed content types in single entry

## Standardized Schema

### Story Entry Structure
```typescript
interface StoryEntry {
  id: string;                    // Unique identifier
  sessionId: string;             // Campaign session reference
  turnNumber: number;            // Sequential turn counter
  timestamp: string;             // ISO 8601 timestamp
  type: StoryEntryType;          // Entry categorization
  content: StoryContent;         // Main content
  metadata: StoryMetadata;       // Additional information
  planningBlock?: PlanningBlock; // Optional choices
  stateChanges?: StateChange[];  // Game state updates
}
```

### Entry Types
```typescript
enum StoryEntryType {
  NARRATIVE = "narrative",       // Story progression
  DIALOGUE = "dialogue",         // Character conversation
  ACTION = "action",            // Player/NPC actions
  SYSTEM = "system",            // Game mechanics
  PLANNING = "planning",        // Think/plan responses
  TRANSITION = "transition"     // Scene changes
}
```

### Content Structure
```typescript
interface StoryContent {
  text: string;                 // Plain text narrative
  formatted?: string;           // HTML/Markdown formatted
  speaker?: string;             // For dialogue entries
  tokens?: number;              // Token count
  highlights?: Highlight[];     // Important phrases
}

interface Highlight {
  start: number;               // Character position
  end: number;                 // Character position
  type: "keyword" | "entity" | "action" | "emotion";
  value: string;               // Highlighted text
}
```

### Planning Block Structure
```typescript
interface PlanningBlock {
  type: "deep_think" | "standard_choice";
  prompt: string;              // Question to player
  options: PlanningOption[];   // Available choices
  characterThoughts?: string;  // Internal monologue
}

interface PlanningOption {
  id: string;                  // [DescriptiveName_#]
  label: string;               // Display text
  description: string;         // Full description
  pros?: string[];            // For deep think
  cons?: string[];            // For deep think
  confidence?: string;        // Subjective assessment
}
```

### Metadata Structure
```typescript
interface StoryMetadata {
  author: "player" | "ai" | "system";
  aiModel?: string;           // Model used
  temperature?: number;       // Generation temperature
  debugMode?: boolean;        // Debug content included
  rollResults?: DiceRoll[];   // Dice roll data
  combatRound?: number;       // Combat tracking
}
```

## Migration Strategy

### Phase 1: Compatibility Layer
1. Create parser for all existing formats
2. Convert to new schema on read
3. Store new entries in standard format
4. Maintain backward compatibility

### Phase 2: Batch Migration
1. Identify all story entries
2. Parse and validate content
3. Convert to new schema
4. Update database in batches
5. Verify data integrity

### Phase 3: Deprecation
1. Remove old format parsers
2. Update all code to use new schema
3. Archive migration code
4. Document breaking changes

## Implementation Details

### Parser Implementation
```python
class StoryEntryParser:
    def parse(self, raw_content: str, entry_type: str) -> StoryEntry:
        """Parse raw content into standardized format"""
        parsers = {
            'json': self._parse_json,
            'text': self._parse_text,
            'html': self._parse_html,
            'markdown': self._parse_markdown
        }
        
        # Detect format and parse
        format_type = self._detect_format(raw_content)
        return parsers[format_type](raw_content, entry_type)
```

### Validation Rules
1. **Required fields**: id, sessionId, turnNumber, timestamp, type, content
2. **Content.text**: Must be non-empty string
3. **Planning blocks**: Must have at least 2 options
4. **Timestamps**: Must be valid ISO 8601
5. **Turn numbers**: Must be sequential

### Storage Optimization
1. **Compress formatted content** if identical to text
2. **Store highlights separately** for search indexing
3. **Index by sessionId and turnNumber**
4. **Archive old entries** after 6 months

## Benefits

### Consistency
- Single source of truth for entry structure
- Predictable parsing and validation
- Easier testing and debugging

### Features Enabled
- Advanced search across entries
- Story replay functionality
- Analytics and insights
- Export in multiple formats

### Performance
- Optimized storage format
- Efficient querying
- Reduced parsing overhead
- Better caching strategies

## Example Entry

```json
{
  "id": "entry_20250705_123456",
  "sessionId": "campaign_abc123",
  "turnNumber": 42,
  "timestamp": "2025-07-05T12:34:56Z",
  "type": "narrative",
  "content": {
    "text": "The ancient door creaks open, revealing a dimly lit chamber...",
    "tokens": 127,
    "highlights": [
      {
        "start": 4,
        "end": 16,
        "type": "entity",
        "value": "ancient door"
      }
    ]
  },
  "metadata": {
    "author": "ai",
    "aiModel": "gemini-2.5-flash",
    "temperature": 0.9,
    "debugMode": false
  },
  "planningBlock": {
    "type": "standard_choice",
    "prompt": "What would you like to do next?",
    "options": [
      {
        "id": "EnterChamber_1",
        "label": "Enter the chamber",
        "description": "Step through the doorway into the dimly lit room"
      },
      {
        "id": "ExamineDoor_2",
        "label": "Examine the door",
        "description": "Take a closer look at the ancient door mechanism"
      }
    ]
  }
}
```

## Testing Strategy

### Unit Tests
- Schema validation
- Parser accuracy
- Migration correctness
- Edge case handling

### Integration Tests
- Full entry lifecycle
- Database operations
- API endpoints
- UI rendering

### Migration Tests
- Data integrity
- Performance benchmarks
- Rollback procedures
- Compatibility verification

## Rollout Plan

1. **Week 1**: Implement schema and parsers
2. **Week 2**: Add compatibility layer
3. **Week 3**: Begin migration testing
4. **Week 4**: Deploy to staging
5. **Week 5**: Production rollout
6. **Week 6**: Monitor and optimize

## Conclusion

The standardized story entry format provides a solid foundation for current features and future enhancements. The migration strategy ensures smooth transition without disrupting existing functionality.