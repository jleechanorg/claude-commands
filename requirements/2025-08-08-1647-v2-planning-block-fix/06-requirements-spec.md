# Requirements Specification: V2 Planning Block Implementation

**Date:** 2025-08-08  
**Time:** 16:57  
**Requirement ID:** 2025-08-08-1647-v2-planning-block-fix

## Problem Statement

The React V2 interface is missing the planning block feature that exists in Flask V1. After campaign creation, users cannot see or interact with character action choices, preventing gameplay progression. This is a critical regression from V1 functionality.

## Solution Overview

Implement planning blocks in V2 by creating a new component that parses and displays AI-generated character choices, maintaining V2's design language while achieving feature parity with V1.

## Functional Requirements

### FR1: Planning Block Display
- **FR1.1**: Planning blocks MUST appear immediately after AI narrative responses
- **FR1.2**: Planning blocks MUST display AI's thinking/reasoning text when present
- **FR1.3**: Planning blocks MUST show 3-5 character action choices
- **FR1.4**: Each choice MUST be clickable and trigger game progression
- **FR1.5**: Planning blocks MUST work with real-time game session updates

### FR2: Data Structure Support
- **FR2.1**: System MUST parse planning_block field from API responses
- **FR2.2**: Planning block data MUST follow JSON structure:
  ```typescript
  {
    thinking?: string
    context?: string
    choices: {
      [key: string]: {
        text: string
        description: string
        risk_level?: 'low' | 'medium' | 'high'
      }
    }
  }
  ```
- **FR2.3**: System MUST handle missing or malformed planning blocks gracefully

### FR3: User Interaction
- **FR3.1**: Users MUST be able to click choice buttons to select actions
- **FR3.2**: Choice selection MUST send appropriate request to backend
- **FR3.3**: UI MUST provide visual feedback on hover/click

## Technical Requirements

### TR1: Component Implementation
- **TR1.1**: Create `PlanningBlock.tsx` in `mvp_site/frontend_v2/src/components/`
- **TR1.2**: Component MUST use existing V2 UI components (Button, Card, etc.)
- **TR1.3**: Component MUST be fully typed with TypeScript
- **TR1.4**: Component MUST follow V2's existing component patterns

### TR2: Type System Extensions
- **TR2.1**: Extend `StoryEntry` interface to include 'planning' type:
  ```typescript
  interface StoryEntry {
    // ... existing fields
    type: 'narration' | 'action' | 'dialogue' | 'system' | 'error' | 'planning'
    planningData?: PlanningBlockData
  }
  ```
- **TR2.2**: Add `PlanningBlockData` type to `api.types.ts`
- **TR2.3**: Ensure all planning block types are exported for reuse

### TR3: API Integration
- **TR3.1**: Modify `api.service.ts` to extract planning_block from responses
- **TR3.2**: Convert planning_block to StoryEntry with type 'planning'
- **TR3.3**: Maintain backward compatibility with responses lacking planning_block

### TR4: Styling Requirements
- **TR4.1**: Use V2's current theme colors (NOT V1's blue #e7f3ff)
- **TR4.2**: Apply consistent spacing and borders with other V2 cards
- **TR4.3**: Support both light and dark themes
- **TR4.4**: Use Tailwind classes consistent with V2 patterns

## Implementation Path

### Step 1: Type Definitions (api.types.ts)
```typescript
export interface PlanningBlockChoice {
  text: string
  description: string
  risk_level?: 'low' | 'medium' | 'high'
}

export interface PlanningBlockData {
  thinking?: string
  context?: string
  choices: Record<string, PlanningBlockChoice>
}
```

### Step 2: Component Creation (PlanningBlock.tsx)
- Import required UI components from './ui'
- Accept PlanningBlockData as props
- Render thinking text if present
- Map choices to Button components
- Handle onClick events for choices

### Step 3: StoryEntry Extension (GameView.tsx)
- Update StoryEntry type definition
- Add case for 'planning' type in render logic
- Import and use PlanningBlock component
- Pass planningData to component

### Step 4: API Service Update (api.service.ts)
- Check for planning_block in API responses
- Create StoryEntry with type 'planning' when present
- Include planningData field with parsed content

## Acceptance Criteria

### AC1: Visual Verification
- [ ] Planning block appears after AI responses
- [ ] Choices are clearly visible and clickable
- [ ] Styling matches V2 theme, not V1 blue
- [ ] No visual glitches or layout issues

### AC2: Functional Testing
- [ ] All choice buttons are clickable
- [ ] Clicking a choice sends correct data to backend
- [ ] Game progresses after choice selection
- [ ] Planning blocks work in both new and existing campaigns

### AC3: Error Handling
- [ ] No console errors when planning_block is missing
- [ ] Graceful fallback for malformed data
- [ ] Clear error messages for users if needed

### AC4: Code Quality
- [ ] All new code is TypeScript with no any types
- [ ] Component is reusable and well-documented
- [ ] No modifications to unrelated V2 features
- [ ] Passes existing test suite

## Files to Modify/Create

### New Files:
1. `mvp_site/frontend_v2/src/components/PlanningBlock.tsx`

### Modified Files:
1. `mvp_site/frontend_v2/src/components/GameView.tsx`
2. `mvp_site/frontend_v2/src/services/api.types.ts`
3. `mvp_site/frontend_v2/src/services/api.service.ts`

## Testing Strategy

### Unit Tests:
- Test PlanningBlock component with various data shapes
- Test parsing logic for planning_block field
- Test error handling for missing/malformed data

### Integration Tests:
- Test full flow from API response to UI display
- Test choice selection and backend communication
- Test with both V1 and V2 API responses

### Visual Testing:
- Compare V2 planning blocks with V1 screenshots
- Verify theme consistency
- Test responsive behavior

## Risk Mitigation

- **Risk**: Breaking existing V2 functionality
  - **Mitigation**: Only additive changes, no modification of existing code paths

- **Risk**: Theme inconsistency
  - **Mitigation**: Use existing V2 component library and theme system

- **Risk**: API compatibility issues
  - **Mitigation**: Graceful handling of missing planning_block field

## Success Metrics

- Planning blocks display correctly in 100% of AI responses that include them
- Zero regression in existing V2 features
- User can complete full game session with planning block interactions
- No increase in error rates or console warnings

## Notes

- V1 implementation reference: `mvp_site/frontend_v1/app.js` lines 565-670
- Existing test documentation: `testing_llm/tdd_planning_block_v1_v2_comparison.md`
- Screenshots of V1 behavior available in `docs/archive_screenshots_20250806_220105/`