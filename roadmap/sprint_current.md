# Current Sprint - Jan 3-9, 2025

<!-- Generated from roadmap.md - DO NOT EDIT DIRECTLY -->

## Sprint Overview
- **Duration**: 7 days (Jan 3-9)
- **Total Hours**: 35 (8+8+8+3+3+3+3)
- **Focus**: Critical bugs, state sync, JSON parsing issues

## Today - Saturday, Jan 4 (8 hours) - COMPLETED

### All tasks completed - see Completed Tasks Record section below

## Week Overview

### Sunday, Jan 5 (8 hrs)

### Afternoon (4 hrs)
- [ ] **TASK-130** 🟡 Unit test coverage improvements (2 hrs)
  - [ ] Review current test coverage gaps
  - [ ] Implement tests for gemini_service.py (currently 27% coverage)
  - [ ] Implement tests for firestore_service.py (currently 50% coverage)
  - [ ] Target 85% overall coverage milestone
- [ ] **TASK-121** 🟡 Create LLMResponse class (30 min)
  - [ ] Design class with all identified fields
  - [ ] Implement parsing methods
  - [ ] Refactor gemini_service.py to use class
  - [ ] Update all response handling code

### Evening (4 hrs)
- [ ] **TASK-131** 🟡 Browser-based UI test coverage (2 hrs)
  - [ ] Set up Selenium or Playwright testing framework
  - [ ] Create tests for campaign creation flow
  - [ ] Create tests for game interaction flow
  - [ ] Test cross-browser compatibility

### Monday-Thursday (12 hrs total)
- **TASK-001b** 🔴 Dragon Knight v3 plot fix (0.5 hrs) - MOVED FROM FRIDAY
- **TASK-006c** 🟡 Enhanced combat scenarios (1 hr)
- **TASK-111** 🟡 Subtle alignment and Myers-Briggs narrative handling (1 hr) - MOVED FROM SUNDAY
  - [ ] Hide alignment/MBTI from player-visible narrative while keeping in game state
  - [ ] Improve subtlety in character descriptions
  - [ ] Update prompts to avoid meta-game references
  - [ ] See roadmap/scratchpad_task111_llm_narrative_improvements.md for detailed requirements
- **TASK-005c** 🟡 UI Polish - Timestamp sync (30 min) - MOVED FROM SUNDAY
- **TASK-004b** 🟡 Continuity Phase 2 (1.5 hrs) - MOVED FROM SUNDAY
  - [ ] NOTE: Define requirements before starting - group with other continuity tasks
  - [ ] See continuity testing system in roadmap for related tasks
- **TASK-119** 🟡 Claude-Simone evaluation (30 min) - MOVED FROM SUNDAY
  - [ ] Review https://github.com/Helmi/claude-simone
  - [ ] Assess integration possibilities
  - [ ] Document findings
- **TASK-132** 🟡 GitHub Actions /testi integration (1.5 hrs) - NEW
  - [ ] Create .github/workflows/integration-tests.yml for PR automation
  - [ ] Configure Firebase and Gemini API secrets, use vpython with TESTING=true
  - [ ] Post full test output in PR comments and upload artifacts
  - [ ] See roadmap/scratchpad_task132_github_actions_testi_integration.md for complete requirements
- **TASK-133** 🟡 Universal calendar system (2 hrs) - NEW
  - [ ] Backend uses consistent numbers, LLM handles narrative conversion per universe
  - [ ] Add universe presets: fantasy, modern, starwars, scifi, custom
  - [ ] Campaign creation includes universe selection, DM can infer from setting
  - [ ] See roadmap/scratchpad_task133_universal_calendar_system.md for complete requirements
- **TASK-134** 🟡 Prompt optimization revisit (4 hrs) - NEW
  - [ ] Comprehensive review of all prompts including PR #292 analysis for token reduction and quality
  - [ ] Target 30% token reduction across system instructions while maintaining functionality
  - [ ] See roadmap/scratchpad_task134_prompt_optimization_revisit.md for complete requirements
- **TASK-135** 🟡 Model cycling debug (2.25 hrs) - NEW
  - [ ] Investigate transient errors where retry works, add comprehensive model cycling logging
  - [ ] Fix suspected model switching issues causing failed first attempts
  - [ ] See roadmap/scratchpad_task135_model_cycling_debug.md for complete requirements
- **TASK-136** 🟡 Requirements builder evaluation (1 hr) - NEW
  - [ ] Test https://github.com/rizethereum/claude-code-requirements-builder on 2 new tasks (132,133) and 2 completed tasks, evaluate for workflow integration and provide assessment with integration recommendations
- **TASK-137** 🟡 Move download/share story buttons (30 min) - NEW
  - [ ] Relocate existing download and share buttons from current location to top of campaign page below campaign title, maintain exact same functionality and behavior
- **TASK-138** 🟡 Stacktrace in debug mode (45 min) - NEW
  - [ ] Add separate debug section to display full Python stacktraces when debug mode toggle is enabled, show complete tracebacks for debugging purposes
- **TASK-139** 🟡 Restore Dragon Knight character start (1.5 hrs) - NEW
  - [ ] Review PR #325 to understand previous Dragon Knight implementation, create improved version that works properly, restore as character creation option with enhanced functionality
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
- All Saturday tasks completed - see Completed Tasks Record section below

### Already Done/In Progress (WIP)
- [x] **TASK-006a** 🟡 Editable campaign names - WIP (PR #301)
- [x] **TASK-006b** 🟡 Background story pause button - WIP (PR #299)
- [x] **TASK-122** 🟡 Migrate Claude commands to slash - COMPLETED (PR #318)
- [x] **TASK-120** 🟢 MCP servers general evaluation - WIP (PR #314)

### Blocked Items
- TASK-001c: Null HP bug (waiting for combat PR review)

### Notes
- All times adjusted for AI-assisted development
- Use `roadmap next` for next task
- Update with `roadmap finish TASK-XXX`

## Completed Tasks Record

### Saturday, Jan 4 - COMPLETED
- [x] **TASK-126** 🔴 Debug raw JSON display in campaigns - COMPLETED (PR #321)
- [x] **TASK-116** 🟢 Show DC in dice rolls - COMPLETED (PR #313)
- [x] **TASK-117** 🟢 Move default fantasy world checkbox - COMPLETED (PR #313)
- [x] **TASK-118** 🟢 Move generate companions checkbox - COMPLETED (PR #313)
- [x] **TASK-128** 🟢 Create long integration test - COMPLETED (PR #313)
- [x] **TASK-114** 🟢 Cache all file reads - COMPLETED (PR #319)
- [x] **TASK-115** 🟢 Document LLM input structure - COMPLETED (PR #314)
- [x] **TASK-110** 🟡 Trim CLAUDE.md file (1 hr) - COMPLETED (PR #305)
- [x] **TASK-125** 🟢 Standardize logging to logging_util (1 hr) - COMPLETED (PR #309)

### Friday, Jan 3 (Holiday - 8 hours) - COMPLETED
- [x] **TASK-001a** 🔴 Malformed JSON investigation (1.5 hrs) - COMPLETED (PR #310)
- [x] **TASK-002** ❌ LLM I/O format standardization (2 hrs) - CLOSED (PR #272 - session tracking doesn't improve LLM accuracy)
- [x] **TASK-002a** ✅ Scene number increment-by-2 fix - COMPLETED (PR #281)
- [x] **TASK-014a** 🟢 Homepage navigation improvements (PR #266)
- [x] **TASK-009a** 🟢 Token logging implementation (PR #264)
- [x] **TASK-005a** 🟢 Campaign click fix - Merged to main
- [x] **TASK-005b** 🟢 Loading spinner messages - Merged to main
- [x] **TASK-110** 🟡 Trim CLAUDE.md file (1 hr) - COMPLETED (PR #305)
- [x] **TASK-125** 🟢 Standardize logging to logging_util (1 hr) - COMPLETED (PR #309)
- [x] **TASK-088** 🟢 Remove Myers-Briggs references - COMPLETED (PR #287)
- [x] **Slash Commands Implementation** - COMPLETED (PR #307)

### Incomplete Tasks from Previous Days (moved to appropriate days)
- [ ] **TASK-001b** 🔴 Dragon Knight v3 plot fix (0.5 hrs) - MOVED TO MONDAY
- [ ] **TASK-073** 🟡 Default campaign prompt update (Ser Arion scenario) - ACTIVE (PR #246)
- [ ] **TASK-003** 🟡 State sync validation (if time permits)
- [ ] **TASK-004a** 🟡 Continuity testing Phase 1 (if time permits)