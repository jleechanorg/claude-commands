# Scratchpad: Consolidate Branch Rules in CLAUDE.md

## Goal
Consolidate all branch-related rules scattered throughout CLAUDE.md into a single, clear section within Git Workflow.

## Current State
Branch rules are scattered in 3+ locations:
1. Claude Code Specific Behavior section (BRANCH DISCIPLINE, BRANCH PROTECTION)
2. Core Principles & Interaction section (Branch Status Protocol)
3. Git Workflow section (main branch rules, PR workflow)

## Plan
1. Create new subsection "Branch & Push Rules" within Git Workflow section
2. Move all branch-related rules there:
   - No pushing to main (except roadmap/sprint files)
   - Branch protection protocol (dev[timestamp] rules)
   - Branch discipline (don't switch unless asked)
   - Branch status protocol (show in every response)
   - Branch creation rules (descriptive names)
   - Branch cleanup protocol
3. Remove duplicates from other sections
4. Add clear 🚨 markers for critical rules
5. Ensure logical flow and easy reference

## Next Steps
- [ ] Read full CLAUDE.md to identify all branch-related content
- [ ] Draft consolidated section
- [ ] Update CLAUDE.md with consolidated rules
- [ ] Remove duplicates from other sections
- [ ] Create PR with clear description