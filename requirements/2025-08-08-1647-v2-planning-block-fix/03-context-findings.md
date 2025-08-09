# Technical Context Findings

**Date:** 2025-08-08
**Time:** 16:54

## V1 Planning Block Implementation Analysis

### Location and Structure
- **Primary File**: `mvp_site/frontend_v1/app.js`
- **CSS Styling**: `mvp_site/frontend_v1/styles/planning-blocks.css`
- **Test File**: `mvp_site/frontend_v1/js/test_planning_block_parsing.js`

### Key Functions in V1:
1. **`parsePlanningBlocks(input)`** (line 565)
   - Entry point for planning block parsing
   - Only accepts JSON format (string format deprecated)
   - Calls `parsePlanningBlocksJson()` for actual parsing

2. **`parsePlanningBlocksJson(planningBlock)`** (line 609)
   - Validates structure: requires `choices` object
   - Renders thinking text if present
   - Creates interactive choice buttons
   - Each choice has: text, description, risk_level

3. **Display Location** (line 336-350)
   - Planning blocks appear after main narrative
   - Background color: `#e7f3ff`
   - Contained in `div.planning-block`
   - Error handling with fallback display

### V1 Data Structure:
```javascript
{
  thinking: "AI's reasoning about choices",
  context: "Optional context",
  choices: {
    choice_a: {
      text: "Action text",
      description: "What happens",
      risk_level: "low|medium|high"
    },
    choice_b: { /* similar */ },
    choice_c: { /* similar */ }
  }
}
```

## V2 Current Architecture Analysis

### Game View Component
- **File**: `mvp_site/frontend_v2/src/components/GameView.tsx`
- **Story Display**: Lines 512-527
- **Entry Types**: narration, action, dialogue, system, error
- **Missing**: No planning block type or rendering logic

### Story Entry Structure in V2:
```typescript
interface StoryEntry {
  id: string
  type: 'narration' | 'action' | 'dialogue' | 'system' | 'error'
  content: string
  timestamp: string
  author?: 'player' | 'ai' | 'system'
  isError?: boolean
  isRetryable?: boolean
  originalInput?: string
}
```

### Key Gap Identified:
- V2 has no planning block handling in StoryEntry type
- No parsing logic for planning_block field from API
- No UI components for rendering choice buttons

## API Integration Points

### V1 API Response Processing:
- Receives `planning_block` in response data
- Parsed in `generateStructuredFieldsPostNarrative()`
- Displayed as part of AI responses

### V2 API Service:
- **File**: `mvp_site/frontend_v2/src/services/api.service.ts`
- Currently processes narrative responses
- Missing planning_block field extraction

## Implementation Requirements

### Components Needed in V2:
1. **PlanningBlock Component**:
   - Parse planning_block JSON structure
   - Render thinking text
   - Display choice buttons with V2 styling
   - Handle choice selection events

2. **StoryEntry Type Extension**:
   - Add 'planning' type
   - Include planningData field for structured data

3. **API Response Processing**:
   - Extract planning_block from API responses
   - Convert to V2 component format
   - Add to story stream

### V2 Design Constraints:
- Must use V2's Tailwind-based styling
- Follow shadcn/ui component patterns
- Maintain dark theme compatibility
- Integrate with real-time update system

## Testing Evidence:
- Previous TDD test created: `testing_llm/tdd_planning_block_v1_v2_comparison.md`
- Screenshots exist showing V1 working: `docs/archive_screenshots_20250806_220105/`
- V2 missing planning block documented: `docs/tdd_evidence_20250806_182705/`

## Critical Files to Modify:
1. `GameView.tsx` - Add planning block rendering
2. `api.types.ts` - Add planning block types
3. `api.service.ts` - Extract planning_block from responses
4. New file: `PlanningBlock.tsx` - Component implementation

## Risk Assessment:
- No breaking changes to existing V2 features
- Addition only - no modification of existing code paths
- Can be tested in isolation before integration