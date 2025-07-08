# WorldArchitect.AI Development Roadmap

<!-- Merged from sprint_current.md and roadmap.md - Sprint current takes precedence -->
<!-- UUID Reference: See UUID_MAPPING.md for task identifier consistency across all roadmap files -->

## 🎯 WHAT TO DO NOW (Quick Navigation)

### Active WIP Tasks (Check PR status)
- **TASK-001a** 🔴 Malformed JSON investigation - PR #296 OPEN
- **TASK-006a** 🟡 Editable campaign names - PR #301 OPEN  
- **TASK-006b** 🟡 Background story pause button - PR #323 OPEN
- **TASK-140** 🔴 Hard stop for integrity failures - PR #336 OPEN
- **TASK-142** 🔴 Fix send button unclickable - PR #338 OPEN

### Next Priority Tasks (Ready to Start)
- **TASK-133** 🟡 Universal calendar system (2 hrs) - PR #403 OPEN
- **TASK-139** 🟡 Restore Dragon Knight character start (1.5 hrs)
- **TASK-137** 🟡 Move download/share story buttons (30 min) - PR #396 OPEN
- **TASK-145** 🟡 Consolidate roadmap files into single source (1 hr) - PR #377 OPEN

### 📋 Quick Links
- [Current Work](#current-work---active-development-priority-section) - Active development items
- [WIP Tasks](#currently-in-progress-wip) - Work in progress with PR links
- [Recently Completed](#recently-completed-tasks-last-7-days) - This week's accomplishments
- [Planning Horizon](#planning-horizon) - Future work organization
- [Archive References](#planning--archive-references) - Detailed milestone planning

---

## Current Work - Active Development (PRIORITY SECTION)

### Current Focus
- **Duration**: Ongoing development cycle
- **Focus**: Critical bugs, state sync, JSON parsing issues

### Active Work Items

#### Afternoon (4 hrs)
- [x] **TASK-130** ✅ Unit test coverage improvements (30 min) - COMPLETED (PR #400)
  - [x] Review current test coverage gaps
  - [x] Implement tests for token_utils.py (0% → 100% coverage)
  - [x] Implement tests for entity_tracking.py (88% → 100% coverage)
  - [x] 11 new test cases added
- [x] **TASK-121** ✅ Create LLMResponse class (30 min) - COMPLETED (PR #398)
  - [x] Design class with all identified fields
  - [x] Implement parsing methods
  - [x] Refactor gemini_service.py to use class
  - [x] Update all response handling code

#### Evening (4 hrs)
- [ ] **TASK-139** 🟡 Restore Dragon Knight character start (1.5 hrs) - PRIORITY
  - [ ] Review PR #325 to understand previous Dragon Knight implementation
  - [ ] Create improved version with enhanced functionality
  - [ ] Restore as character creation option
- [ ] **TASK-137** 🟡 Move download/share story buttons (30 min) - PR #396 OPEN ✅ Tests Passing
  - [ ] Review existing PR, potentially merge if ready
- [ ] **TASK-133** 🟡 Universal calendar system (2 hrs) - PR #403 OPEN ✅ Tests Passing
  - [ ] Review existing PR, potentially merge if ready

### Monday-Thursday (12 hrs total) - REORGANIZED BY PRIORITY

#### Group A: Critical Fixes (4.5 hrs)
- **TASK-001b** 🔴 Dragon Knight v3 plot fix (0.5 hrs)
- **TASK-142** 🔴 Fix send button unclickable (45 min) - MOVED FROM SUNDAY
  - [ ] Investigate campaign send button appearing in progress state and becoming unresponsive
  - [ ] Check for console errors, fix button state management to prevent stuck states
  - [ ] Ensure button properly resets after response or errors, test across browsers
- **TASK-140** 🔴 Hard stop for integrity failures (2.5 hrs) - HIGH PRIORITY - MOVED FROM SUNDAY
  - [ ] Detect when LLM doesn't generate state updates, halt game progression immediately
  - [ ] Show detailed traceback in debug mode, user-friendly error in normal mode
  - [ ] Provide retry/reload/abort recovery options in separate error modal
  - [ ] See roadmap/scratchpad_task140_integrity_failure_hard_stop.md for complete requirements
- **TASK-006c** 🟡 Enhanced combat scenarios (45 min) - REDUCED SCOPE

#### Group B: Infrastructure & Features (8 hrs) - MANUAL TASKS ADDED
- **TASK-132** ✅ GitHub Actions /testi integration (1.5 hrs) - COMPLETED (PR #402, #412)
  - [x] Create .github/workflows/integration-tests.yml for PR automation
  - [x] Configure Firebase and Gemini API secrets, use vpython with TESTING=true
  - [x] Post full test output in PR comments and upload artifacts
  - [x] Enable Gemini API key in GitHub Actions - PR #412
- **TASK-143** 🟡 Context7 MCP integration with Claude Code CLI (1 hr) - MANUAL - MOVED FROM SUNDAY
  - [ ] Set up Context7 MCP server for Claude Code CLI integration
  - [ ] Configure context management for all development workflows
  - [ ] Test context retention across planning, coding, and debugging sessions
  - [ ] Document setup and usage patterns for ongoing development
- **TASK-144** 🟡 Sequential Thinking MCP integration with Claude Code CLI (1 hr) - MANUAL - MOVED FROM SUNDAY
  - [ ] Set up Sequential Thinking MCP server for Claude Code CLI integration
  - [ ] Configure step-by-step reasoning for complex development decisions
  - [ ] Test on planning workflows, debugging processes, and architectural decisions
  - [ ] Document integration benefits and recommended usage scenarios
- **TASK-133** 🟡 Universal calendar system (2 hrs) - PR #403 OPEN ✅ Tests Passing
  - [ ] Backend uses consistent numbers, LLM handles narrative conversion per universe
  - [ ] Add universe presets: fantasy, modern, starwars, scifi, custom
  - [ ] Campaign creation includes universe selection, DM can infer from setting
- **TASK-139** 🟡 Restore Dragon Knight character start (1.5 hrs) - MOVED TO SUNDAY EVENING
  - [ ] Review PR #325 to understand previous Dragon Knight implementation, create improved version
  - [ ] Restore as character creation option with enhanced functionality
- **TASK-136** 🟡 Requirements builder evaluation (30 min) - REDUCED SCOPE
  - [ ] Quick evaluation of https://github.com/rizethereum/claude-code-requirements-builder

#### Group C: UI Polish (2 hrs)
- **TASK-137** 🟡 Move download/share story buttons (30 min) - PR #396 OPEN
  - [ ] Relocate existing download and share buttons to top of campaign page below campaign title
- **TASK-138** 🟡 Stacktrace in debug mode (45 min)
  - [ ] Add separate debug section to display full Python stacktraces when debug mode toggle is enabled
- **TASK-005c** 🟡 UI Polish - Timestamp sync (45 min)

#### Deferred Tasks (Move to separate sessions)
- **TASK-135** 🟡 Model cycling debug (2.25 hrs) - MOVED TO OPTIMIZATION PHASE
  - [ ] Complex debugging task, better grouped with other optimization work

### Optimization Phase (Separate dedicated session)
#### CONSOLIDATED: Token/Prompt Optimization (6-8 hrs)
- **TASK-141+134+099+092** 🟢 Comprehensive token/prompt optimization - GROUPED
  - [ ] **Phase 1 (TASK-141):** Token measurement and caching (2 hrs)
    - Stop sending world content with every request, implement session-level caching
    - Verify token measurements match actual prompt sizes sent to LLM in gemini_service.py
  - [ ] **Phase 2 (TASK-134+099):** Prompt optimization (3 hrs)
    - Comprehensive review of all prompts including PR #292 analysis for token reduction
    - Trim initial prompts for better performance
  - [ ] **Phase 3 (TASK-092):** System instructions optimization (2 hrs)
    - Include assiah prompt once in campaign creation vs system instructions
    - Evaluate if all prompts need to be system instructions
  - [ ] **Target:** 30-50% token reduction while maintaining narrative quality

### Continuity Testing Phase (Separate dedicated session)
#### CONSOLIDATED: Sequential Testing (6 hrs)
- **TASK-004+004b+004c** 🟡 Complete continuity testing pipeline - GROUPED
  - [ ] **Phase 1:** 10 interactions automated testing (2 hrs)
  - [ ] **Phase 2:** 20 interactions with failure analysis (2 hrs) 
  - [ ] **Phase 3:** 50 interactions stress test (2 hrs)

### Research Tasks (Lower Priority)
- **TASK-123** 🔵 Traycer planning tool evaluation (1.5 hrs)
- **TASK-124** 🔵 Research Claude best practices (1 hr)

### Recently Completed Tasks (Last 7 Days)
- [x] **TASK-074** 🔴 Unit test coverage improvements - Phase 5 COMPLETED (PR #413)
  - [x] Phase 1: main.py route handler tests (33% → 45% coverage) - PR #401
  - [x] Phase 2: main.py auth & state management tests (45% → 55% coverage) - PR #401
  - [x] Phase 3: main.py error handling tests (55% → 65% coverage) - PR #409
  - [x] Phase 4: firestore_service.py tests - PR #411
  - [x] Phase 5: firestore_service.py state helpers tests - PR #413
  - [x] Coverage infrastructure fix (0% → 67% overall) - PR #407
- [x] **TASK-132** 🟡 GitHub Actions /testi integration - COMPLETED (PR #402, #412)
  - [x] Enable Gemini API key in GitHub Actions - PR #412
- [x] **TASK-130** 🔴 Unit test coverage for utility modules - COMPLETED (PR #400)
  - [x] token_utils.py: 0% → 100% coverage (11 test cases)
  - [x] entity_tracking.py: 88% → 100% coverage
- [x] **TASK-121** 🔴 Create LLMResponse class - COMPLETED (PR #398)
- [x] **Browser Test Suite Cleanup** - COMPLETED (PR #414)
  - [x] Comprehensive browser test consolidation and cleanup from PR #248
- [x] **Roadmap Optimization** - COMPLETED (PR #393)
- [x] **Cloud Run Load Balancer Timeout Fix** - COMPLETED (PR #408)
- [x] **TASK-111** ✅ **COMPLETED** Zen MCP evaluation - COMPLETED (PR #346/#364/#367)
- [x] **TASK-112** ✅ **COMPLETED** Context7 MCP evaluation - COMPLETED (PR #347/#362/#368)
- [x] **TASK-113** ✅ **COMPLETED** Sequential Thinking MCP evaluation - COMPLETED (PR #348/#365/#369)
- [x] **TASK-119** ✅ **COMPLETED** Claude-Simone evaluation - COMPLETED (PR #349/#361/#372)
- [x] **TASK-120** ✅ **COMPLETED** MCP servers general evaluation - COMPLETED (PR #350/#363/#374)
- [x] **TASK-122** ✅ **COMPLETED** Migrate Claude commands to slash - COMPLETED (PR #318)
- [x] **TASK-125** ✅ **COMPLETED** Standardize logging to logging_util - COMPLETED (PR #309)
- [x] **TASK-143** 🔴 Luke Campaign Fixes - COMPLETED (PR #351)
- [x] **TASK-126** 🔴 Debug raw JSON display in campaigns - COMPLETED (PR #321)
- [x] **TASK-116** 🟢 Show DC in dice rolls - COMPLETED (PR #313)
- [x] **TASK-117** 🟢 Move default fantasy world checkbox - COMPLETED (PR #313)
- [x] **TASK-118** 🟢 Move generate companions checkbox - COMPLETED (PR #313)
- [x] **TASK-128** 🟢 Create long integration test - COMPLETED (PR #313)
- [x] **TASK-114** 🟢 Cache all file reads - COMPLETED (PR #319)
- [x] **TASK-115** 🟢 Document LLM input structure - COMPLETED (PR #314)
- [x] **TASK-110** 🟡 Trim CLAUDE.md file (1 hr) - COMPLETED (PR #305)
- [x] **TASK-002** ❌ LLM I/O format standardization - CLOSED (PR #272 - session tracking doesn't improve LLM accuracy)
- [x] **TASK-002a** ✅ Scene number increment-by-2 fix - COMPLETED (PR #281)
- [x] **TASK-014a** 🟢 Homepage navigation improvements (PR #266)
- [x] **TASK-009a** 🟢 Token logging implementation (PR #264)
- [x] **TASK-005a** 🟢 Campaign click fix - Merged to main
- [x] **TASK-005b** 🟢 Loading spinner messages - Merged to main
- [x] **TASK-088** 🟢 Remove Myers-Briggs references - COMPLETED (PR #287)
- [x] **Slash Commands Implementation** - COMPLETED (PR #307)

### Currently In Progress (WIP)
- [ ] **TASK-140** 🔴 Hard stop for integrity failures - WIP (PR #406 OPEN)
- [ ] **TASK-001a** 🔴 Malformed JSON investigation - WIP (PR #405 OPEN) 
- [ ] **TASK-133** 🟡 Universal calendar system - WIP (PR #403 OPEN)
- [ ] **TASK-137** 🟡 Move download/share story buttons - WIP (PR #396 OPEN)
- [ ] **TASK-145** 🟡 Consolidate roadmap files - WIP (PR #377 OPEN)
- [ ] **TASK-142** 🔴 Fix send button unclickable - WIP (PR #338 OPEN)
- [ ] **TASK-006b** 🟡 Background story pause button - WIP (PR #323 OPEN)
- [ ] **TASK-006a** 🟡 Editable campaign names - WIP (PR #301 OPEN)
- [ ] **TASK-102** 🟡 Slim mode design - WIP (PR #303 OPEN)
- [ ] **TASK-101** 🟡 Story mode entry format - WIP (PR #297 OPEN)
- [ ] **TASK-001a** 🔴 Malformed JSON investigation - WIP (PR #296 OPEN)
- [ ] **TASK-089** 🟡 Planning block IDs format - WIP (PR #295 OPEN)
- [ ] **TASK-100** 🟡 Dynamic world state design - WIP (PR #294 OPEN)
- [ ] **TASK-092** 🟡 System instructions optimization - WIP (PR #293 OPEN)
- [ ] **TASK-090** 🟡 Remove legacy migration code - WIP (PR #288 OPEN)

### Blocked Items
- TASK-001c: Null HP bug (waiting for combat PR review)

## Active Development Plan

### Daily Schedule
- **Monday-Friday**: 3 hours/day (15 hours/week)
- **Saturday-Sunday**: 8 hours/day (16 hours/week)
- **Total**: 31 hours/week

### Priority System
- 🔴 **Critical**: Bugs affecting users, broken functionality
- 🟡 **High**: Core features, major improvements
- 🟢 **Medium**: Polish, optimization, nice-to-have
- 🔵 **Low**: Future considerations, research

### Notes
- All times adjusted for AI-assisted development
- Use `roadmap next` for next task
- Update with `roadmap finish TASK-XXX`

### PR Status Legend
🚨 **CRITICAL**: GitHub PR states mean:
- **OPEN** = Work In Progress (WIP) - NOT completed
- **MERGED** = Completed and integrated into main branch  
- **CLOSED** = Abandoned or rejected - NOT completed
- ❌ Tasks are NOT completed just because PR exists
- ✅ Tasks are ONLY completed when PR state = "MERGED"

## Planning Horizon

### Current Sprint Goals
- **Critical Fixes**: Resolve integrity failures, malformed JSON, send button issues
- **Infrastructure**: GitHub Actions integration, universal calendar system
- **Testing**: Unit test coverage improvements, continuity testing phases
- **UI Polish**: Timestamp sync, button placement, debug mode improvements

### Next Sprint Preparation
- **Token Optimization**: Consolidate TASK-141, TASK-134, TASK-099, TASK-092 into optimization phase
- **Continuity Testing**: Sequential phases (10 → 20 → 50 interactions)
- **Four-Mode System**: Complete implementation of DM/Author/Story/Game modes
- **Combat System**: Integration with existing PR #102

### Research & Future Items
- **MCP Integration**: Context7 and Sequential Thinking setup for Claude Code CLI
- **Optimization Tools**: Traycer evaluation, Claude best practices research
- **Advanced Features**: Demo site branch, advanced state exploration
- **Launch Preparation**: Copyright cleanup, security validation, documentation

### Risk & Dependency Tracking
- **Blocked**: TASK-001c (Null HP) waiting for combat PR #102 review
- **Dependencies**: Token optimization should precede prompt optimization work
- **Resource Constraints**: 11+ WIP tasks may need prioritization
- **Technical Debt**: Legacy migration code cleanup needed

## Parallel Work Opportunities

For different worktrees:
1. **Main worktree**: Core bug fixes and state sync
2. **Parallel worktree 1**: Token optimization and compression
3. **Parallel worktree 2**: UI improvements and themes

## Development Notes

### AI-Assisted Development
- All time estimates reduced by 50% for AI-assisted development
- Use `roadmap next` command to get next task
- Use `roadmap finish [UUID]` to mark complete
- Each PR must reference task UUIDs
- Update scratchpads with detailed progress

## Unit test scratchpad followups

### Core integrity
*   [TASK-099] **Trim Initial Prompts** 🟡 - Optimize initial prompt size for better performance - PR #292
*   [TASK-092] **System Instructions Optimization** 🟡 - Just include assiah prompt once in campaign creation vs system instructions, evaluate if all prompts need to be system instructions - PR #293
*   [TASK-100] **Dynamic World State** 🟡 - Handle stale world info as game progresses (e.g., faction leader dies) - PR #294
*   [TASK-002] **LLM I/O Format Standardization** - Define explicit input/output formats including Scene#, prompts, returns, debug data, game state updates
*   [TASK-101] **Story Mode Entry Format** 🟡 - Define proper format for story mode entries - PR #297
*   [TASK-102] **Slim Mode Design** 🟡 - Design lightweight mode for reduced token usage - PR #303
*   [TASK-003] **Character Creation State Tracking** - Implement tracking per `character_creation_state_tracking_scratchpad.md`
*   [TASK-103] **Prompt Quality Review** - Have LLM review and provide feedback on new prompts
*   [TASK-104] **Prompt Optimization** - Optimize prompts based on `roadmap/scratchpad_8k_optimization.md`

### General Tasks & Integration
*   [TASK-105] **Integration Test for Prompts** - Run integration test to verify all proper prompts and master prompt are included
*   [TASK-106] **Parallel Processing Setup** - Implement parallel processing for improved performance
*   [TASK-009b] **Alexiel Book Compression** - Further compression integrate alexiel book: `roadmap/alexiel_book_token_reduction_scratchpad.md`
*   [TASK-009a] ✅ **COMPLETED** Logging make it all tokens vs characters (token-based logging instead of character counts) - PR #264
*   [TASK-107] ✅ **COMPLETED** Claude Directory Navigation - Fix Claude's directory navigation issues - PR #290
*   [TASK-005a] ✅ **COMPLETED** Clicking on a campaign doesn\'t show spinner loading and seems to not always register clicks (issue is about the campaign list) - PR #267
*   [TASK-005b] ✅ **COMPLETED** Loading spinner with messages during campaign continue - PR #268
*   [TASK-014a] ✅ **COMPLETED** WorldArchitect.AI make this clickable to homepage - PR #266
*   [TASK-002] ❌ **CLOSED** LLM I/O format standardization - PR #272 (Closed - session tracking doesn't improve LLM accuracy)
*   [TASK-002a] ✅ **COMPLETED** Fix scene number increment-by-2 display issue - PR #281

### Bugs
*   [TASK-001c] **Null HP during combat** - Happens during combat, defer to combat system revamp (see PR #102: https://github.com/jleechan2015/worldarchitect.ai/pull/102)
*   [TASK-001a] 🔄 **IN PROGRESS** Malformed JSON investigation - PR #296 (OPEN)
*   [TASK-126] ✅ **COMPLETED** Debug raw JSON display in campaigns - Fixed god mode JSON display issue - PR #321
*   [TASK-001b] ✅ **COMPLETED** Dragon Knight v3 plot coherence - AI introduced unrelated plot element (randomly introduced crypt element), need stronger narrative constraints
*   Stable?

## Detailed Task Specifications

### Critical Bug Fixes
- **Null HP during combat** - DEFERRED to combat system revamp (see PR #102: https://github.com/jleechan2015/worldarchitect.ai/pull/102)
- **Malformed JSON response from AI** - ✅ COMPLETED - Fixed god mode JSON display issue (PR #321)
- **Dragon Knight v3 plot coherence** - ✅ COMPLETED - Fixed AI introducing unrelated plot elements

### LLM I/O Format Standardization
**❌ CLOSED (PR #272) - Session tracking doesn't improve LLM accuracy**
- ❌ Scene # tracking system (S{session}_SC{scene} format) - Not needed for LLM accuracy

### Scene Number Display Fix
**✅ COMPLETED (PR #281)**
- ✅ Fixed increment-by-2 display issue where scene numbers appeared to jump
- ✅ Added user_scene_number that only increments for AI responses
- ✅ Maintains backward compatibility with fallback to sequence_id

### Continuity Testing System
**Automated program specifications:**
- Use planning block responses from game
- Track entity consistency (ensure fields remain consistent)
- Track narrative coherence
- Test both game state consistency and story flow
- Phase 1: 10 interactions
- Phase 2: 20 interactions
- Phase 3: 50 interactions

### UI Improvements
- **Campaign list click issues** - ✅ COMPLETED (PR #267) - Doesn't show spinner, clicks don't always register
- **Loading spinner with messages** - ✅ COMPLETED (PR #268) - During campaign continue, add random hardcoded messages like creation
- **Homepage navigation** - ✅ COMPLETED (PR #266) - Make "WorldArchitect.AI" text clickable to return to homepage
- **Timestamp/narrative mismatch** - 🟡 IN PROGRESS (PR #269) - Sync timestamps with story events
- **Let player read background story** - Currently scrolls past too quickly, add pause/continue button
- **Pagination** - Add for story content with "load more" functionality

### Four-Mode System Implementation
- **DM/System Admin mode:** Full game state editing within game mechanics (NOT unrestricted Gemini access)
- **Author mode:** God-like powers but bound by game universe laws, for book writing assistance
- **Story mode:** Use same D&D ruleset but HIDE mechanics, players can query if curious, NOT 100% success rate
- **Game mode:** Full ruleset visibility with real dice rolls explicitly shown

### Campaign & Combat Improvements
- **Editable campaign names** - Allow inline editing on campaign page
- **Enhanced Ser Arion scenario** - Demo all GenAI RPG features:
  - Add 2-3 smaller combat encounters before main assault
  - Build narrative tension toward Ashwood Keep
  - Balance combat and story elements
- **Combat system integration** - Review PR #102, plan null HP fix integration

### Metrics & Optimization
- **Token-based logging** - Convert all character counts to token counts in logs
- **Alexiel book compression** - Implement `roadmap/alexiel_book_token_reduction_scratchpad.md`
- **Parallel dual-pass optimization** - Implement `mvp_site/roadmap/scratchpad_parallel_dual_pass_optimization.md`
- **Prompt optimization** - Review `System instructions roadmap/scratchpad_8k_optimization.md`

### Launch Preparation
- **Copyright cleanup** - Remove D&D references, use "5e compatible"
- **Security validation** - Validate all user inputs, review API key protection
- **Myers-Briggs hiding** - Hide personality types in UI but keep for internal use, special command to reveal
- **Documentation** - Update user guides, API docs

### Narrative
*   [TASK-079] **Trim Default Start Backstory** - Reduce amount of backstory exposed to player during default campaign start
*   [TASK-093] **Dragon Knight Detailed Start** - Create detailed narrative start for Dragon Knight character class
*   [TASK-094] **Generate Custom Character Background** - Generate siblings/houses/factions etc if they pick a custom character even in default world
*   [TASK-095] **Generate Companions System** - Create system to generate appropriate companions based on character and story
*   [TASK-155] **Evaluate Alignment Change Mechanic** - Review current implementation and assess if alignment shifts are working correctly during gameplay

### UI
*   [TASK-096] **Third Checkbox for Ruleset** - Add third checkbox to replace ruleset option
*   [TASK-097] **UI Size Optimization** - Make UI elements smaller for better space usage
*   [TASK-098] **Campaign Metrics Script** - Create script to report number of campaigns and size per user
*   [TASK-006b] Let player read background story (currently scrolls too fast, need pause button)

### Combat
*   [TASK-012a] Combat system PR revisit
*   [TASK-012c] Derek campaign issues combat, replay campaign
*   [TASK-006c] Default scenario add some guaranteed combat

### Feedback
*   [TASK-013] Derek feedback
*   Evernote
*   Ensure god mode and questions don’t progress narrative
*   Metrics for me and other users
*   [TASK-004] **Project:** Continuity load test - 10 interactions (should track entity consistency and narrative coherence)
*   [TASK-003] `roadmap/scratchpad_state_sync_entity.md` followups
*   `test_sariel_consolidated.py`
*   [TASK-083] Ensure it does real sariel test and ask for proof real gemini and real pydantic were used.
*   `Scratchpad_prompt_optimization.md`
*   **Project:** Brand new frontend
*   [TASK-008b] Figma integration
*   Fix wizard
*   Fix themes?
*   Nicer spinner when continuing story
*   Campaign default starts?
*   Default character starts like
    *   Sariel: intrigue/research
    *   Host: combat?
    *   Shadow faction: stealth/assassination
    *   Merc? Maybe define a new merc faction
*   [TASK-055] Game thrones Ned stark choice - Create campaign scenario where player faces moral dilemma similar to Ned Stark's honor vs pragmatism choices
*   [TASK-056] Luke join Vader choice - Implement Star Wars-inspired campaign with pivotal dark side temptation decision

## [TASK-057] Project: Demo site branch
*   Create separate branch for demonstration/showcase version of the site
*   Implement reduced feature set for public demo
*   Add guided tutorial flow for new users

## Project: Continuity - 50 interactions
*   Custom program to run N interactions and randomly pick planning block response
*   [TASK-004b] 20 interactions
*   [TASK-004c] 50 interactions

## Cleanup
*   [TASK-058] CI integration dead code: `roadmap/scratchpad_worktree_dead_code.md` - Remove unused CI/CD integration code identified in worktree analysis

## [TASK-059] Project: advanced state exploration
*   `roadmap/state_consistency_adanvanced_v2.md` - Implement advanced state consistency using SCORE framework, MemLLM, and hierarchical memory systems
*   [TASK-060] Double check on ROI - Analyze return on investment for advanced state management implementation
*   [TASK-061] `business_plan_v1.md` - Create comprehensive business plan with financial projections and market strategy

## Tech optimization
*   [TASK-009c] `mvp_site/roadmap/scratchpad_parallel_dual_pass_optimization.md`
*   [TASK-072] **Evaluate CodeRabbit AI Code Review Tool** (Scheduled: July 19, 2025) 🟢
    *   Install and configure CodeRabbit on the repository
    *   Test automated PR review capabilities
    *   Evaluate quality of suggestions and false positive rate
    *   Compare with manual code review process
    *   Decision: Adopt for all PRs or remove
    *   Enable "copilot ping" command if adopted
*   [TASK-075] **Laptop SSH Setup** - Configure SSH access from laptop to development environment for remote coding
*   [TASK-076] **Cost Savings Plan** - Analyze Gemini API usage costs using exported CSV data to identify optimization opportunities
*   [TASK-077] **Generic D&D Setting Adaptation** - Create flexible prompt system that adapts D&D mechanics to any fictional universe (e.g., Star Wars: Jedi Knight vs Paladin, Force Lightning vs Lightning Bolt)
*   [TASK-078] **GitHub Actions Unit Test Coverage** - Set up automated unit test coverage reporting in CI/CD pipeline
*   [TASK-146] **Firebase Write/Read Verification** - Implement mechanism to write data to Firebase and read it back to verify persistence
*   [TASK-147] **Browser Test Mock Mode Support** - Add support for mock mode in browser tests to enable faster testing without real APIs
*   [TASK-148] **Game State Debug Tool** - Create debug tool to print full game state for any campaign for troubleshooting
*   [TASK-149] **Browser Test Cron with Email** - Set up browser tests to run every 6 hours via crontab and email results
*   [TASK-150] **Rename vpython to vpython.sh** - Rename vpython command to vpython.sh for clarity
*   [TASK-151] **Claude Best Practices Integration** - Evaluate and integrate relevant practices from https://www.anthropic.com/engineering/claude-code-best-practices
*   [TASK-152] **Single Source of Truth Analysis** - Address duplications: 1) entities in Python code vs prompts, 2) GeminiResponse object consistency
*   [TASK-153] **Pydantic Version Upgrade** - Evaluate and migrate to Pydantic v2 or v3 for better performance and features
*   [TASK-154] **Campaign Tuning via God Mode** - Use god mode to analyze past campaigns and improve prompt quality based on learnings
*   Improve rules? https://ghuntley.com/stdlib/
*   Ssh into desktop from laptop?
*   https://www.reddit.com/r/ClaudeAI/s/EtrZt0B9nE
*   Macbook SSH: AI coding
*   Coding or Agent eval
*   Backtrack Vagent vs single
*   [TASK-084] **Dev Server per PR** - Set up preview deployment URLs for each pull request for easier testing and review
*   [TASK-085] **Cursor AI Prompts Research** - Research and integrate Cursor AI prompts from https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools
*   [TASK-086] **Mobile SSH Access** - Configure SSH access from mobile phone to development PC when not on home WiFi using the Perplexity guide
*   [TASK-087] **Tailscale VPN Setup** - Set up Tailscale for secure development environment networking and remote access
*   [TASK-114] ✅ **COMPLETED** Cache All File Reads - Implement in-memory caching for all file reads to improve performance - PR #319
*   [TASK-115] ✅ **COMPLETED** Document LLM Input Structure - Create formal documentation of exact JSON/data structures sent to LLM - PR #314
*   [TASK-116] ✅ **COMPLETED** Show DC in Dice Rolls - Display Difficulty Class values in dice roll results (e.g., "Success vs DC 15") - PR #313
*   [TASK-117] ✅ **COMPLETED** Move Default Fantasy World Checkbox - Relocate "Use default fantasy world" option to campaign creation screen - PR #313
*   [TASK-118] ✅ **COMPLETED** Move Generate Companions Checkbox - Move "Generate default companions" from wizard last step to narrative/mechanics section - PR #313
*   [TASK-119] ✅ **COMPLETED** Claude-Simone Evaluation - Evaluated https://github.com/Helmi/claude-simone for potential integration - PR #349/#372
*   [TASK-120] ✅ **COMPLETED** MCP Servers General Evaluation - Surveyed and compared available MCP servers beyond those already scheduled - PR #350
*   [TASK-121] 🔴 **Create LLMResponse Class** - HIGH PRIORITY - Implement structured class to handle all LLM responses instead of raw strings/JSON
*   [TASK-143] 🟡 **Context7 MCP Integration with Claude Code CLI** - MANUAL - Set up Context7 MCP server for Claude Code CLI integration across all development workflows
*   [TASK-144] 🟡 **Sequential Thinking MCP Integration with Claude Code CLI** - MANUAL - Set up Sequential Thinking MCP server for Claude Code CLI integration for complex development decisions
*   [TASK-122] **Migrate Claude Commands to Slash Format** - Convert all claude.md commands to slash commands and document on GitHub
*   [TASK-123] **Traycer Planning Tool Evaluation** - Evaluate Traycer for architecture planning and development workflow
*   [TASK-124] **Research Claude Best Practices** - Investigate other users' Claude configurations and compile useful patterns
*   [TASK-125] ✅ **COMPLETED** Standardize Logging to logging_util - Replace all usage of standard logging module with logging_util for consistency - PR #319

## Optimization
*   Start generating the world after user first choice?
*   [TASK-062] Generate ahead for planning blocks to reduce latency? Maybe a premium feature - Pre-generate common planning block responses to improve response times
*   [TASK-080] **Firebase Collection Group Optimization** - Migrate from individual collections to collection groups for better query performance
*   [TASK-081] **Firestore Query Optimization** - Ensure all queries use proper indexes and fetch only single-user data
*   [TASK-082] **Firestore Auth Setup** - Complete authentication configuration by July 13 using AI coding assistance

## Core changes
*   Perplexity research and feed back into my project
*   Fix campaign issues from core ideas tab
*   Rename story mode vs game mode (maybe call it narrative mode?)
*   Implement real story mode with simplified mechanics and more like choose your own adventure

## Stable milestone - game state seems mostly ok?
*   UI portraits: Character gen: https://airealm.com/user/newChat
*   https://bg3.wiki/wiki/Category:Character_Portraits

## Tweaks / small
*   [TASK-011b] Pagination
*   Give the user back input in sections so they can see the narrative and read it during creation
*   Download as markdown
*   [TASK-010d] Hide myers briggs D&D alignment (but keep internally)
*   Proper domain name maybe with firebase domains

## Campaigns
*   Other worlds
    *   Sci fi, modern, rome
*   [TASK-063] GOT - Arthur Dayne campaign - Create Game of Thrones campaign playing as legendary knight Arthur Dayne
*   [TASK-064] GOT - Tywin campaign to test character agency - Implement Tywin Lannister campaign focused on political maneuvering and character autonomy
*   [TASK-065] Rome campaign - Develop Ancient Rome setting with political intrigue and military conquest
*   [TASK-066] Celestial wars - Create high fantasy campaign with divine conflicts and cosmic stakes

## Narrative core
*   Generate worlds for future, modern day, Ancient Rome similar to assiah
*   Test different narrative arcs per personality type
*   Give different sample campaign options even if copyrighted
    *   [TASK-067] Star wars - Sample campaign in Star Wars universe with Force powers and galactic conflict
    *   [TASK-068] Game thrones - Sample campaign in Westeros with political intrigue and house dynamics
    *   [TASK-069] Baldurs gate - Sample campaign in Forgotten Realms setting with D&D mechanics
    *   [TASK-070] Modern day - Sample campaign in contemporary setting with realistic scenarios
    *   [TASK-071] Ancient rome - Sample campaign in historical Rome with authentic period details

## Personality core
*   Make sure PC and npc have one
*   [TASK-010d] Hide myers briggs even in DM mode (but keep internally)
*   Only a special command can show the info

## Core game logic
*   Characters don’t flesh themselves out enough or talk enough? Need a different character where I do more social stuff
*   Game thrones tywin - didn't die
*   20% failure rate show explicit logs for now

## Project: Allow users to edit gamestate and context

## UI core
*   Skins/themes - nicer UI
*   Continue button
*   Delete campaign
*   Erase functionality

## Security
*   [TASK-010b] Validate all user inputs
*   [TASK-010b] Misc security stuff

## Polish
*   stephanie - too much formatting. Hard to know what to do next. Too many stars ie. look at
*   Maximize space for input and reading
*   Cooler website icon
*   [TASK-006a] Edit campaign name on campaign page
*   Cancel submission
*   Firebase hosting domain?
*   Nicer titles
*   Rewind like dungeon AI
*   Streaming API
*   Also show gemini thinking
*   [TASK-011b] Add pagination for the story box or a “load more” thing like if they keep scrolling up in the past load older content in the story

## Later promotion
*   Bigger stabilization: AI coding
*   Google org?
*   booktok?

## External prep
*   [TASK-010a] The names "Dungeons & Dragons" and "D&D": Third-party creators cannot use these names on their products. Instead, they often say "Compatible with the world's most popular roleplaying game" or "5e compatible.
*   [TASK-010a] Copyright cleanup
*   Cleanup code
*   Metrics
*   Open source a prototype fork
    *   Remove game state
    *   Remove personality stuff
    *   Reduce LLM input/output
    *   Game state deltas only?
    *   Is Game state truly needed? LLM seems to handle things fine maybe because game state is explicit in the convo now?
*   Cost estimates
*   God mode changes
    *   Don’t let others steal prompts or have full gemini access
    *   Make an admin mode with full access
*   [TASK-006a] Let me edit the name of the campaign on campaign page
*   Mailing list permission
*   Newer onboarding flow and do hand holding
*   Customer observation sessions
*   Themes
*   Image gen
*   [TASK-010a] D&D copyright double check
*   [TASK-010a] Check for any other copyright issues
*   [TASK-010a] Double check any copyright issues scraping myers briggs personalities from the webpages

## External project
*   Bring your own key allow users to input their own API key

## Full external prep
*   Images and map are cool from friend and fables. consider
*   Gemini nano?
*   Tweaks to hide DM mode stuff
*   Tell user if using Jeff special prompts
*   [TASK-007] Multiple modes: story, game, god etc. Make four modes with specific behaviors:
    *   **DM or system admin mode:** lets you change everything. Like you’re talking to real gemini agent. You can do anything or change anything you want.
    *   I can say DM note: to make an adjustment but stay in whatever mode I am in
    *   If I say “enter DM mode” then I say there until I say “back to mode X” or “leave DM mode”
    *   **Author mode:** You’re like a god but still bound by the laws of the game universe. This mode is to help people who are writing a book and making their own story.
    *   **Story mode:** everything the player does always succeeds. The game should explicitly tell you this for each decision
    *   **Game mode:** use the ruleset to see if the player succeeds. Game should be explicit its using a realset, roll real dice etc.
*   Multi player
*   chatGpt and deepseek support? Support other models
*   Make domain name nicer
*   Don’t show stacktrace to internal ppl
*   Setup VSCode for local dev
*   Make UI nicer and snappy like Gemini chat or AIDungeon
*   Erase functionality

## Bigger launch
*   Rate limits
*   Quota etc

## Prototype limited alpha

## 📚 Planning & Archive References

### Detailed Milestone Planning
**Archived**: Complete milestone breakdown with 10 detailed phases moved to preserve all content  
**Location**: [roadmap_archive_milestone_breakdown.md](./roadmap_archive_milestone_breakdown.md)  
**Contents**: All milestone details, Derek feedback implementation, development schedules

### Future Planning & Ideas  
**Location**: Various sections above contain long-term planning items
**Categories**: Campaign worlds, narrative systems, technical optimization, launch preparation

---

**Note**: All detailed milestone planning has been archived to keep this roadmap focused on current actionable work. No tasks were deleted - only reorganized for better navigation.
