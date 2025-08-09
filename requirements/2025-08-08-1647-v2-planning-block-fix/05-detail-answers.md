# Expert Detail Answers

**Date:** 2025-08-08
**Time:** 16:56

## User Responses

**Q1: Should we create a new PlanningBlock.tsx component in frontend_v2/src/components/?**
Answer: **YES** (if nothing else exists)

**Q2: Should the planning block appear immediately after AI narrative responses (like in V1)?**
Answer: **YES** (user confirmed)

**Q3: Should we extend the StoryEntry type to include a 'planning' type with planningData field?**
Answer: **YES**

**Q4: Should planning blocks use the same blue background (#e7f3ff) as V1 but adapted to V2's dark theme?**
Answer: **NO** - Make it match current V2 theme

**Q5: Should we add planning_block type definitions to api.types.ts for TypeScript safety?**
Answer: **YES**

## Summary of Decisions
- Create new component if none exists
- Position planning blocks after AI narrative
- Extend existing type system for clean integration
- Use V2's current theme/styling (not V1's blue)
- Add proper TypeScript definitions