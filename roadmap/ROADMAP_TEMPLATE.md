# WorldArchitect.AI Development Roadmap

<!-- 
This is the master roadmap file. All tasks are tracked here.
- sprint_current.md is generated from the "Current Sprint" section
- completed_log.md archives finished tasks
- Use `roadmap next` to get your next task
-->

## Quick Stats
- **Total Tasks**: 54+ (plus future projects)
- **Completed**: 1
- **In Progress**: 0
- **Sprint Progress**: 0%

## Current Sprint (Jan 3-9, 2025)

### Today - Friday, Jan 3 (Holiday - 8 hours)

#### Morning Block (4 hours)
- [ ] **TASK-001a** 🔴 Malformed JSON investigation (1.5 hrs)
  - Track when/where AI responses fail to parse
  - Add robust JSON parsing with fallbacks
  - Create recovery mechanisms
- [ ] **TASK-001b** 🔴 Dragon Knight v3 plot coherence (0.5 hrs)
  - Fix random crypt introduction
  - Add narrative constraints
- [ ] **TASK-002** 🟡 LLM I/O format standardization (2 hrs)
  - Define Scene#, prompts, returns structure
  - Incorporate character_creation_state_tracking_scratchpad.md

#### Afternoon Block (4 hours)
- [ ] **TASK-003** 🟡 State sync validation (2 hrs)
  - Run integration tests
  - Verify master prompt inclusion
  - Update scratchpad_state_sync_entity.md
- [ ] **TASK-004a** 🟡 Continuity testing Phase 1 (2 hrs)
  - Build 10-interaction test program
  - Track entity consistency

### Weekend Tasks

#### Saturday, Jan 4 (8 hours)
- [ ] **TASK-007** 🟡 Four-mode system (4 hrs total)
  - [ ] TASK-007a: Architecture design (0.5 hrs)
  - [ ] TASK-007b: DM mode (1 hr)
  - [ ] TASK-007c: Author mode (1 hr)
  - [ ] TASK-007d: Story mode (0.75 hrs)
  - [ ] TASK-007e: Game mode (0.75 hrs)
- [ ] **TASK-005** 🟢 UI Polish - Small (2 hrs total)
  - [ ] TASK-005a: Campaign click fix (0.5 hrs)
  - [ ] TASK-005b: Loading spinner (1 hr)
  - [ ] TASK-005c: Timestamp sync (0.5 hrs)
- [ ] **TASK-004b** 🟡 Continuity Phase 2 - 20 interactions (2 hrs)

## Backlog (Prioritized)

### High Priority 🟡
- **TASK-006** Campaign improvements
  - TASK-006a: Editable campaign names (0.5 hrs)
  - TASK-006b: Background story pause (0.5 hrs)
  - TASK-006c: Enhanced Ser Arion scenario (2 hrs)
- **TASK-004c** Continuity Phase 3 - 50 interactions (2 hrs)
- **TASK-009** Metrics & Optimization
  - TASK-009a: Token-based logging (1 hr)
  - TASK-009b: Alexiel compression (1 hr)
  - TASK-009c: Parallel optimization (1 hr)

### Medium Priority 🟢
- **TASK-011** UI Major Improvements
  - TASK-011a: Theme system (1 hr)
  - TASK-011b: Figma integration (1.5 hrs)
  - TASK-011c: Responsiveness (1.5 hrs)
  - TASK-011d: Gemini-like speed (1 hr)
- **TASK-014** Navigation & Polish
  - TASK-014a: Homepage navigation (0.5 hrs)
  - TASK-014b: Pagination (1 hr)

### Launch Prep 🟡
- **TASK-010** Launch preparation
  - TASK-010a: Copyright cleanup (1 hr)
  - TASK-010b: Security validation (1 hr)
  - TASK-010c: Documentation (1 hr)
  - TASK-010d: Hide Myers-Briggs (1 hr)

### Combat Integration 🟡
- **TASK-012** Combat system
  - TASK-012a: Review PR #102 (0.5 hrs)
  - TASK-012b: Fix null HP bug (1 hr)
  - TASK-012c: Derek campaign testing (1 hr)
- **TASK-001c** Null HP bug - DEFERRED to TASK-012b

### Derek Feedback 🟢
- **TASK-013** Implement Derek's feedback items (TBD)

### Narrative Enhancements 🟡
- **TASK-015** Dragon knight detailed start (2 hrs)
- **TASK-016** Generate siblings/houses/factions for custom characters (3 hrs)
- **TASK-017** Generate companions system (2 hrs)
- **TASK-018** Alignment change mechanic (1.5 hrs)

### Tech Optimization 🟢
- **TASK-019** Parallel dual pass optimization (`mvp_site/roadmap/scratchpad_parallel_dual_pass_optimization.md`) (2 hrs)
- **TASK-020** Improve rules per ghuntley.com/stdlib (1 hr)
- **TASK-021** SSH into desktop from laptop setup (0.5 hrs)
- **TASK-022** Dev server per PR implementation (2 hrs)
- **TASK-023** Macbook SSH for AI coding (0.5 hrs)
- **TASK-024** Cursor prompts integration (github.com/x1xhlol/system-prompts-and-models-of-ai-tools) (1 hr)
- **TASK-025** Coding/Agent eval setup (1.5 hrs)
- **TASK-026** Backtrack Vagent vs single analysis (1 hr)
- **TASK-027** Mobile phone setup (perplexity.ai/search/what-doe-sthis-mean-i-use-blin-FI3Qns9xSZqFPSKMhg18Cg) (0.5 hrs)
- **TASK-028** Tailscale for open internet (0.5 hrs)

### Core Changes 🟡
- **TASK-029** Perplexity research integration (2 hrs)
- **TASK-030** Fix campaign issues from core ideas tab (2 hrs)
- **TASK-031** Rename story mode vs game mode to narrative mode (0.5 hrs)
- **TASK-032** Implement real story mode with simplified mechanics (4 hrs)

### Personality Core 🟡
- **TASK-033** Ensure PC and NPC have personality types (1 hr)
- **TASK-034** Test different narrative arcs per personality type (3 hrs)
- **TASK-035** Add special command to show hidden myers briggs info (0.5 hrs)

### Core Game Logic 🟡
- **TASK-036** Fix characters not talking/fleshing out enough (2 hrs)
- **TASK-037** Game of Thrones Tywin death bug fix (1 hr)
- **TASK-038** Investigate 20% failure rate with explicit logs (2 hrs)

### Project: User Editable Gamestate 🟡
- **TASK-039** Allow users to edit gamestate (4 hrs)
- **TASK-040** Allow users to edit context (2 hrs)

### Security 🔴
- **TASK-041** Validate all user inputs (2 hrs)
- **TASK-042** Miscellaneous security hardening (3 hrs)

### Polish 🟢
- **TASK-043** Reduce formatting per Stephanie feedback (1 hr)
- **TASK-044** Maximize space for input and reading (1 hr)
- **TASK-045** Design cooler website icon (1 hr)
- **TASK-046** Firebase hosting domain setup (1 hr)
- **TASK-047** Implement nicer titles (0.5 hrs)
- **TASK-048** Add rewind functionality like Dungeon AI (3 hrs)
- **TASK-049** Implement streaming API (2 hrs)
- **TASK-050** Show Gemini thinking process (1 hr)

### Later Promotion 🔵
- **TASK-051** Bigger stabilization with AI coding (4 hrs)
- **TASK-052** Google org setup (1 hr)
- **TASK-053** BookTok promotion strategy (2 hrs)

### External Project 🔵
- **TASK-054** Bring your own API key feature (3 hrs)

### Future Projects 🔵

#### Multi-World Support
- Sci-fi world generation
- Modern day settings
- Ancient Rome campaigns
- GOT/Star Wars templates

#### External Preparation
- Remove D&D references ("5e compatible")
- Open source fork planning
- Rate limits and quotas

#### UI/UX Enhancements
- Download as markdown
- Cancel submission

## Completed Tasks

### January 2025
- [x] **TASK-000** Roadmap reorganization with UUIDs (PR #260)
  - Created UUID system for all tasks
  - Consolidated duplicate items
  - Added daily/weekly schedule
  - Completed: Jan 3, 2025

## Notes

### Time Estimates
- All estimates assume AI-assisted development (50% reduction from traditional)
- Use parallel worktrees for optimization tasks
- Derek feedback items pending receipt

### Commands
- `roadmap next` - Get next task from Current Sprint
- `roadmap finish TASK-XXX` - Mark task complete
- `roadmap status` - Show sprint progress
- `roadmap log` - Show completed tasks

### References
- UUID mappings: UUID_MAPPING.md
- Detailed scratchpads in roadmap/scratchpad_*.md
- Combat PR: https://github.com/jleechan2015/worldarchitect.ai/pull/102