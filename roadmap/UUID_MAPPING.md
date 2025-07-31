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
- **TASK-156**: Planning Block Choice Buttons (COMPLETED)
- **TASK-157**: AI Realm Evaluation - Research platform for integration/inspiration
- **TASK-158**: MCP Instruction Compliance Tracking - Fork Invariant MCP-scan for automatic CLAUDE.md rule enforcement
- **TASK-159**: Python test audit and redundancy reduction - Analyze 240+ test files and optimize test suite
- **TASK-160**: Hardcoded worktree cleanup implementation - Remove hardcoded paths and implement dynamic resolution
- **TASK-161**: String matching audit and LLM validation replacement - Replace string matching with LLM-based solutions
- **TASK-162**: Main.py world logic diff analysis - Identify critical missing functions in MCP migration
- **TASK-163**: Character creation choices display enhancement - Show user choices after character creation
- **TASK-164**: Memory MCP improvements from PR #1016 - Implement Memory MCP enhancements and 4-phase plan
- **TASK-165**: Roadmap execution summary - Complete project overview and next action priorities
- **TASK-166**: Comment reply system enhancement with commit hash - Include commit hash and handle threaded replies
- **TASK-167**: Schedule branch work script parameter enhancement - Add time, prompt, branch parameters
- **TASK-168**: API compatibility followups documentation - Document compatibility requirements
- **TASK-169**: Planning block missing campaign fix - Fix missing planning block in campaign creation
- **TASK-170**: Fix fake code patterns and individual comment reply - Address fake code and comment issues

### Handoff Tasks (HANDOFF series)
- **HANDOFF-ARCH**: Real AST-based /arch implementation - Ready for handoff
- **HANDOFF-MEMORY-CLEANUP**: Memory system cleanup and migration - Ready for handoff
- **HANDOFF-SELF-CRITICAL**: Self-critical Claude Code CLI - Ready for handoff
- **HANDOFF-SLASH-COMMANDS**: Enhance /handoff + create /commentreply - Ready for handoff
- **HANDOFF-COPILOT-ENHANCEMENTS**: Advanced copilot command features - Ready for handoff
- **HANDOFF-SETTINGS-PAGE**: Settings page with Gemini model selection - Ready for handoff
- **HANDOFF-PUSHL_FIX**: Fix /pushl command context isolation and add branch awareness - Ready for handoff

### Critical Priority Tasks (Additional TASK series)
- **TASK-140**: Hard stop for integrity failures - Critical priority task
- **TASK-142**: Fix send button unclickable - Critical priority task

## Cross-Reference Notes

1. All three roadmap files should use these UUIDs consistently
2. When updating one file, sync the others
3. PR descriptions should reference these UUIDs
4. Scratchpad files use format: `scratchpad_TASK-XXX_description.md`
