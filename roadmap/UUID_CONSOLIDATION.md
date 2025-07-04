# UUID Consolidation Report

## Conflicts Found

### 1. Token Optimization
- roadmap.md: TASK-009a,b,c
- roadmap_detailed.md: TASK-300
- roadmap_expanded.md: TASK-300a,b,c
**Resolution:** Keep TASK-009a,b,c

### 2. Continuity Testing Phases
- roadmap.md: TASK-004, TASK-004b, TASK-004c
- roadmap_detailed.md: TASK-004, TASK-008, TASK-010
- roadmap_expanded.md: TASK-004, TASK-008, TASK-010
**Resolution:** Use TASK-004a (10), TASK-004b (20), TASK-004c (50)

### 3. Combat System
- roadmap.md: TASK-012a (PR review), TASK-012c (Derek campaign)
- roadmap_detailed.md: TASK-013 (combat integration)
- roadmap_expanded.md: TASK-503 (combat PR review)
**Resolution:** Keep TASK-012 series for combat

### 4. UI Major Improvements
- roadmap.md: Missing sub-tasks
- roadmap_detailed.md: TASK-011 (single)
- roadmap_expanded.md: TASK-011a,b,c,d (detailed)
**Resolution:** Use expanded version TASK-011a,b,c,d

### 5. Navigation Items
- roadmap.md: TASK-011a,b (homepage, pagination)
- roadmap_expanded.md: TASK-501, TASK-502
**Resolution:** Renumber to TASK-014a,b

## Master UUID List (Consolidated)

### Critical Bugs (TASK-001)
- TASK-001a: Malformed JSON investigation
- TASK-001b: Dragon Knight v3 plot fix
- TASK-001c: Null HP bug (defer to combat)

### State Sync & Testing (TASK-002-003)
- TASK-002: LLM I/O format standardization
- TASK-003: State sync validation & testing

### Continuity Testing (TASK-004)
- TASK-004a: Phase 1 - 10 interactions
- TASK-004b: Phase 2 - 20 interactions
- TASK-004c: Phase 3 - 50 interactions

### UI Polish - Small (TASK-005)
- TASK-005a: Campaign list click fix
- TASK-005b: Loading spinner messages
- TASK-005c: Timestamp/narrative sync

### Campaign Improvements (TASK-006)
- TASK-006a: Editable campaign names
- TASK-006b: Background story pause
- TASK-006c: Enhanced Ser Arion scenario

### Four-Mode System (TASK-007)
- TASK-007a: Mode architecture
- TASK-007b: DM/System Admin mode
- TASK-007c: Author mode
- TASK-007d: Story mode
- TASK-007e: Game mode

### Metrics & Optimization (TASK-009)
- TASK-009a: Token-based logging
- TASK-009b: Alexiel book compression
- TASK-009c: Parallel dual-pass

### Launch Preparation (TASK-010)
- TASK-010a: Copyright cleanup
- TASK-010b: Security validation
- TASK-010c: Documentation update
- TASK-010d: Myers-Briggs hiding

### UI Major Improvements (TASK-011)
- TASK-011a: Theme/skin system
- TASK-011b: Figma integration
- TASK-011c: UI responsiveness
- TASK-011d: Gemini-like speed

### Combat System (TASK-012)
- TASK-012a: PR #102 review
- TASK-012b: Fix null HP bug
- TASK-012c: Derek campaign testing

### Derek Feedback (TASK-013)
- TASK-013: Implement feedback items

### Navigation & Polish (TASK-014)
- TASK-014a: Homepage navigation
- TASK-014b: Pagination implementation

### Additional Items from roadmap.md without UUIDs
- Multiple project-level items
- Tech optimization tasks
- External prep items
- Launch considerations

## Next Steps
1. Update all files to use this consolidated list
2. Add UUIDs to items currently missing them
3. Remove duplicate/conflicting IDs