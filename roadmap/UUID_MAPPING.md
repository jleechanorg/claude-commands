# UUID Mapping for WorldArchitect.AI Roadmap

## Task UUID Reference

### Critical Bugs & Investigation (TASK-001 series)
- **TASK-001**: Critical bugs investigation & fixes
  - **TASK-001a**: Malformed JSON response investigation
  - **TASK-001b**: Dragon Knight v3 plot coherence fix
  - **TASK-001c**: Null HP bug (deferred to combat PR #102)

### State Sync & LLM I/O (TASK-002-003 series)
- **TASK-002**: LLM I/O format standardization
- **TASK-003**: State sync validation & testing

### Continuity Testing (TASK-004 series)
- **TASK-004**: Continuity testing Phase 1 (10 interactions)
- **TASK-004b**: Continuity testing Phase 2 (20 interactions)
- **TASK-004c**: Continuity testing Phase 3 (50 interactions)

### UI Polish - Small (TASK-005 series)
- **TASK-005**: UI Polish - Small tasks bundle
  - **TASK-005a**: Fix campaign list click registration
  - **TASK-005b**: Loading spinner with messages
  - **TASK-005c**: Fix timestamp/narrative mismatch

### Campaign Improvements (TASK-006 series)
- **TASK-006**: Campaign improvements bundle
  - **TASK-006a**: Editable campaign names
  - **TASK-006b**: Let player read background story
  - **TASK-006c**: Enhanced Ser Arion scenario with combat

### Four-Mode System (TASK-007 series)
- **TASK-007**: Four-mode system implementation
  - **TASK-007a**: Mode architecture design
  - **TASK-007b**: DM/System Admin mode
  - **TASK-007c**: Author mode
  - **TASK-007d**: Story mode
  - **TASK-007e**: Game mode

### UI Polish - Major (TASK-008 series)
- **TASK-008**: UI/UX major improvements
  - **TASK-008a**: Theme/skin system architecture
  - **TASK-008b**: Figma integration
  - **TASK-008c**: UI responsiveness improvements
  - **TASK-008d**: Gemini-like snappiness

### Metrics & Optimization (TASK-009 series)
- **TASK-009**: Metrics & optimization bundle
  - **TASK-009a**: Token-based logging
  - **TASK-009b**: Alexiel book compression
  - **TASK-009c**: Parallel dual-pass optimization

### Launch Preparation (TASK-010 series)
- **TASK-010**: Launch preparation bundle
  - **TASK-010a**: Copyright cleanup
  - **TASK-010b**: Security validation
  - **TASK-010c**: Documentation update
  - **TASK-010d**: Myers-Briggs hiding

### Navigation & Polish (TASK-011 series)
- **TASK-011**: Navigation & final polish
  - **TASK-011a**: Homepage navigation (WorldArchitect.AI clickable)
  - **TASK-011b**: Pagination implementation
  - **TASK-011c**: Combat PR #102 review

### Combat System (TASK-012 series)
- **TASK-012**: Combat system integration
  - **TASK-012a**: Review PR #102
  - **TASK-012b**: Fix null HP bug
  - **TASK-012c**: Test Derek's campaign issues

### Derek Feedback (TASK-013)
- **TASK-013**: Derek feedback implementation

### Tech Optimization (TASK-072)
- **TASK-072**: Evaluate CodeRabbit AI Code Review Tool (Scheduled: July 19, 2025)

### New Infrastructure & Optimization Tasks (TASK-146 to TASK-154)
- **TASK-146**: Firebase Write/Read Verification
- **TASK-147**: Browser Test Mock Mode Support
- **TASK-148**: Game State Debug Tool
- **TASK-149**: Browser Test Cron with Email
- **TASK-150**: Rename vpython to vpython.sh
- **TASK-151**: Claude Best Practices Integration
- **TASK-152**: Single Source of Truth Analysis
- **TASK-153**: Pydantic Version Upgrade
- **TASK-154**: Campaign Tuning via God Mode
- **TASK-155**: Evaluate Alignment Change Mechanic

## Cross-Reference Notes

1. All three roadmap files should use these UUIDs consistently
2. When updating one file, sync the others
3. PR descriptions should reference these UUIDs
4. Scratchpad files use format: `scratchpad_TASK-XXX_description.md`