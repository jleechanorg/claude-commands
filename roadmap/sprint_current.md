# Current Sprint - Jan 3-9, 2025

<!-- Generated from roadmap.md - DO NOT EDIT DIRECTLY -->

## Sprint Overview
- **Duration**: 7 days (Jan 3-9)
- **Total Hours**: 35 (8+8+8+3+3+3+3)
- **Focus**: Critical bugs, state sync, four-mode system

## Today - Friday, Jan 3 (Holiday - 8 hours)

### ⏰ Morning Block (9am-1pm) - NOT COMPLETED
- [x] **TASK-001a** 🔴 Malformed JSON investigation (1.5 hrs) - PAUSED
- [ ] **TASK-001b** 🔴 Dragon Knight v3 plot fix (0.5 hrs) - PAUSED

### ⏰ Evening Block (6pm-8pm) - Current Time: 6pm  
- [x] **TASK-002** 🟡 LLM I/O format standardization (2 hrs) - COMPLETED (PR #272)
- [ ] **TASK-073** 🟡 Default campaign prompt update (Ser Arion scenario) - ACTIVE (PR #246)
- [ ] **TASK-003** 🟡 State sync validation (if time permits)
- [ ] **TASK-004a** 🟡 Continuity testing Phase 1 (if time permits)

### ⏰ Late Evening Block (8pm-10pm) - Simple Tasks
- [ ] **TASK-114** 🟢 Cache all file reads (30 min)
  - [ ] Implement in-memory cache for world content files
  - [ ] Cache system instruction files beyond session
  - [ ] Add cache invalidation mechanism
- [ ] **TASK-115** 🟢 Document LLM input structure (45 min)
  - [ ] Create docs/llm_io_specification.md
  - [ ] Document exact JSON structures sent to LLM
  - [ ] Include all prompt templates and formats
- [ ] **TASK-116** 🟢 Show DC in dice rolls (45 min)
  - [ ] Update LLM prompts to specify DC values
  - [ ] Parse DC from dice roll results
  - [ ] Display as "(Success vs DC 15)"

### ⏰ Completed Tasks (Based on PR History)
- [x] **TASK-014a** 🟢 Homepage navigation improvements (PR #266)
- [x] **TASK-009a** 🟢 Token logging implementation (PR #264)
- [x] **TASK-005a** 🟢 Campaign click fix - Merged to main
- [x] **TASK-005b** 🟢 Loading spinner messages - Merged to main

## Tomorrow - Saturday, Jan 4 (8 hours)

### Morning (4 hrs)
- [ ] **TASK-110** 🟡 Trim CLAUDE.md file (1 hr)
  - [ ] Remove redundancy and consolidate rules
  - [ ] Archive outdated sections
  - [ ] Improve organization
- [ ] **TASK-007** 🟡 Four-mode system implementation
  - [ ] TASK-007a: Architecture (30 min)
  - [ ] TASK-007b: DM mode (45 min)
  - [ ] TASK-007c: Author mode (45 min)
  - [ ] TASK-007d: Story mode (30 min)
  - [ ] TASK-007e: Game mode (30 min)

### Afternoon (4 hrs)
- [ ] **TASK-111** 🟡 LLM narrative improvements (1 hr)
  - [ ] Fix direct alignment mentions in narrative
  - [ ] Improve subtlety in character descriptions
  - [ ] Update prompts to avoid meta-game references
- [ ] **TASK-005** 🟢 UI Polish - Small tasks
  - [x] TASK-005a: Campaign clicks (30 min) - COMPLETED
  - [x] TASK-005b: Loading spinner (1 hr) - COMPLETED
  - [ ] TASK-005c: Timestamp sync (30 min)
- [ ] **TASK-004b** 🟡 Continuity Phase 2 (1.5 hrs)

## Week Overview

### Sunday, Jan 5 (8 hrs)

### Morning (4 hrs)
- [ ] **TASK-117** 🟢 Move default fantasy world checkbox (30 min)
  - [ ] Move from current location to campaign creation screen
  - [ ] Update UI flow and state management
- [ ] **TASK-118** 🟢 Move generate companions checkbox (30 min)
  - [ ] Move from wizard last step to narrative/mechanics section
  - [ ] Update campaign creation flow
- [ ] **TASK-119** 🟢 Claude-Simone evaluation (30 min)
  - [ ] Review https://github.com/Helmi/claude-simone
  - [ ] Assess integration possibilities
  - [ ] Document findings
- [ ] **TASK-120** 🟢 MCP servers general evaluation (45 min)
  - [ ] Survey available MCP servers beyond scheduled ones
  - [ ] Create comparison matrix
  - [ ] Recommend top candidates for deeper evaluation
- [ ] **TASK-006** 🟡 Campaign improvements (1.5 hrs)
  - [ ] TASK-006a: Editable campaign names
  - [ ] TASK-006b: Background story pause button
  - [ ] TASK-006c: Enhanced combat scenarios

### Afternoon (4 hrs)
- [ ] **TASK-121** 🟡 Create LLMResponse class (2 hrs)
  - [ ] Design class with all identified fields
  - [ ] Implement parsing methods
  - [ ] Refactor gemini_service.py to use class
  - [ ] Update all response handling code
- [ ] **TASK-122** 🟡 Migrate Claude commands to slash (2 hrs)
  - [ ] Convert roadmap commands to slash format
  - [ ] Create /milestones command
  - [ ] Create /copilot command
  - [ ] Document all commands in GitHub

### Monday-Thursday (12 hrs total)
- **TASK-001b** 🔴 Dragon Knight v3 plot fix (0.5 hrs) - MOVED FROM FRIDAY
- **TASK-123** 🔵 Traycer planning tool evaluation (1.5 hrs)
  - Install and configure Traycer
  - Test on architecture planning tasks
  - Compare with current planning workflow
  - Document pros/cons and recommendations
- **TASK-124** 🔵 Research Claude best practices (1 hr)
  - Investigate other users' slash commands
  - Review public claude.md files
  - Compile list of useful patterns
  - Create recommendations document
- Complete continuity testing Phase 3
- Metrics & optimization
- Launch preparation
- Navigation fixes

## Progress Tracking

### Completed Today
- **TASK-014a** 🟢 Homepage navigation improvements (PR #266)
- **TASK-009a** 🟢 Token logging implementation (PR #264)
- **TASK-001a** 🔴 Malformed JSON investigation (PAUSED - mostly complete)

### Blocked Items
- TASK-001c: Null HP bug (waiting for combat PR review)

### Notes
- All times adjusted for AI-assisted development
- Use `roadmap next` for next task
- Update with `roadmap finish TASK-XXX`