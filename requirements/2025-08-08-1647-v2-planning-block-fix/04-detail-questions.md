# Expert Detail Questions

Based on the code analysis, please answer with YES, NO, or IDK (I don't know). If you answer IDK, I'll use the default shown.

## Q1: Should we create a new PlanningBlock.tsx component in frontend_v2/src/components/?
**Default if unknown: YES** - Follows V2's component-based architecture and separation of concerns

## Q2: Should the planning block appear immediately after AI narrative responses (like in V1)?
**Default if unknown: YES** - Maintains consistent UX patterns between versions

## Q3: Should we extend the StoryEntry type to include a 'planning' type with planningData field?
**Default if unknown: YES** - Clean integration with existing V2 message system

## Q4: Should planning blocks use the same blue background (#e7f3ff) as V1 but adapted to V2's dark theme?
**Default if unknown: NO** - V2 should maintain its own design system with theme-appropriate colors

## Q5: Should we add planning_block type definitions to api.types.ts for TypeScript safety?
**Default if unknown: YES** - Ensures type safety and better IDE support

---
Please provide your answers in order (Q1-Q5).