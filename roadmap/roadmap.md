# WorldArchitect.AI Development Roadmap

<!-- UUID Reference: See UUID_MAPPING.md for task identifier consistency across all roadmap files -->

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

## Today's Focus - Time Blocks

### Morning Block (4 hours)
1. **[TASK-001a] Investigate Malformed JSON** 🟡 (1.5 hrs) - PR #296
   - Investigate malformed JSON from AI responses
   - Add robust error handling and recovery
2. **[TASK-002] State Sync Testing Setup** 🟡 (2.5 hrs)
   - Define exact LLM I/O format with Scene#, prompts, returns
   - Create test framework for continuity

### Afternoon Block (4 hours)
3. **[TASK-003] Complete State Sync Testing** 🟡 (2 hrs)
   - Run integration tests for proper prompts
   - Verify master prompt inclusion
   - Document in `roadmap/scratchpad_state_sync_entity.md`
4. **[TASK-004] Start Continuity Testing Phase 1** 🟡 (2 hrs)
   - Build automated program for 10 interactions
   - Use planning block responses

### Evening Block (2 hours)
5. **[TASK-073] Comprehensive Hand Testing** 🟢 (30 min)
   - **Test Instructions:**
     - Create new campaign with default character
     - Test 5-10 story interactions focusing on:
       - Combat encounters (damage, HP tracking, enemy defeat)
       - NPC interactions (dialogue, relationship tracking)
       - State persistence (save/load, continue campaign)
       - UI responsiveness (loading spinners, click registration)
       - Error handling (refresh page, invalid inputs)
     - Test both Story Mode and Game Mode
     - Document any bugs or UX issues found
     - Focus on user experience, not just functionality
6. **[TASK-074] Unit Test Coverage Review** 🟡 (1.5 hrs)
   - **Review Current State:**
     - Analyze PR #238 (test fixtures) and PR #239 (GameState tests)
     - Check status of unit test coverage milestones (see `roadmap/scratchpad_unit_test_coverage_milestones.md`)
     - Review existing test infrastructure and identified gaps
     - Assess progress toward 85% coverage goal
   - **Next Actions:**
     - Identify which milestone to tackle next (likely Milestone 3: Service Layer)
     - Review gaps in gemini_service.py (27% coverage) and firestore_service.py (50% coverage)
     - Plan integration of existing test fixtures with new tests
     - Update test coverage improvement plan based on current progress
7. **[TASK-091] Test Campaign with Unchecked Checkboxes** 🟡 (30 min)
   - **Test Instructions:**
     - Create new campaign with default settings
     - Uncheck both mechanics and narrative checkboxes
     - Test 5-10 interactions to ensure:
       - No crashes or errors occur
       - Game continues functioning properly
       - UI remains responsive
       - State persists correctly
     - Document any issues or unexpected behavior
     - Verify that unchecked options properly disable their respective features
8. **[TASK-126] Improve Character Creation Flow - Ask Who/What** 🟡 (45 min)
   - **Implementation Details:**
     - During character creation, explicitly ask user:
       - "Who is your character?" (name, background, personality)
       - "What scenario/campaign do you want to play?"
     - Improve the initial character creation flow to be more guided
     - Add specific questions at the beginning of character creation
     - Ensure user provides context before proceeding
9. **[TASK-127] Add Missing Planning Block After Campaign Start** 🟡 (45 min)
   - **Implementation Details:**
     - Planning block should appear immediately after campaign is started
     - Default text should include: "OK to proceed or changes requested"
     - Currently missing during character creation flow
     - Ensure planning block appears at the right time
     - Test that it properly waits for user confirmation
10. **[TASK-128] Create Long Integration Test - Option 1 Repeated** ✅ **COMPLETED** (PR #313)
    - **Test Details:**
      - ✅ Create new test file: `test_integration_long.py`
      - ✅ Test choosing option 1 (planning block option) repeatedly
      - ✅ Run 10-20 iterations of selecting option 1
      - ✅ Focus on state consistency throughout the interactions
      - ✅ Verify no state corruption or drift over many turns
      - ✅ Ensure game remains stable with repeated planning choices
11. **[TASK-129] Implement Hard Stop on Integrity Failures** 🔴 (1 hr)
    - **Implementation Details:**
      - Add module-level boolean constant `STRICT_INTEGRITY_MODE = True` for toggling
      - Detect integrity failures: missing state updates, malformed responses, validation errors
      - On integrity failure: hard stop gameplay, warn user with clear explanation
      - Provide correction options: retry, manual fix, or abort session
      - Review all current warnings to determine which should be upgraded to errors
      - Focus on non-recoverable failures (vs recoverable ones like dual-pass validation)
      - Create obvious early indicator when playing in broken state
      - Ensure user never continues with corrupted game state unknowingly

### Tonight's Work Block (Small LLM Tasks)
8. **[TASK-088] Remove Direct Myers-Briggs References in Narrative** ✅ **COMPLETED** (PR #287)
   - ✅ Already properly implemented - Myers-Briggs types are internal-only, never displayed to users
   - System correctly uses personality types for AI behavior while keeping them invisible in narration
9. **[TASK-089] Planning Block IDs** ✅ **COMPLETED** (PR #295 - In Progress)
   - ✅ Already using consistent camelCase-compatible format (`[Word_Number]`)
   - Planning block IDs are consistent across the codebase
10. **[TASK-090] Remove Legacy Migration Code** ✅ **COMPLETED** (PR #288, PR #343)
    - ✅ Removed obsolete test files explicitly marked for removal
    - Additional migration system evaluation can be done separately if needed

### Tomorrow's Tasks
11. **[TASK-108] Remove Word/Character Counts from Logs** ✅ **COMPLETED** (PR #289)
    - ✅ Converted all logging to use token counts exclusively
    - ✅ Removed character/word metrics from logging utilities
12. **[TASK-109] Fix ChoiceIDs Planning Block Formatting** 🟡 (30 min) - PR #295
    - Investigate and fix ChoiceIDs not correctly formatted in planning blocks
    - Ensure consistent formatting across all planning block responses
    - Update any parsing logic if needed

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
*   [TASK-001a] ✅ **COMPLETED** Malformed JSON response from AI - Fixed god mode JSON display issue - PR #321
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
*   [TASK-072] **Next Saturday** Evaluate alignment change mechanic - Review current implementation and assess if alignment shifts are working correctly during gameplay

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
*   [TASK-072] **Evaluate CodeRabbit AI Code Review Tool** (Scheduled: January 19, 2025) 🟢
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
*   [TASK-119] **Claude-Simone Evaluation** - Evaluate https://github.com/Helmi/claude-simone for potential integration
*   [TASK-120] **MCP Servers General Evaluation** - Survey and compare available MCP servers beyond those already scheduled
*   [TASK-121] 🔴 **Create LLMResponse Class** - HIGH PRIORITY - Implement structured class to handle all LLM responses instead of raw strings/JSON
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

## Detailed Milestone Breakdown

### Milestone 1: Critical Bug Fixes & Investigation (4 hrs)
- **TASK-001a** 🟡 **IN PROGRESS** Investigate malformed JSON responses - PR #296
  - Currently being worked on
  - Analyze when/where AI responses fail to parse
  - Add robust JSON parsing with fallbacks
  - Log all malformed responses for pattern analysis
  - Implement recovery mechanism
- **TASK-001b** ✅ **COMPLETED** Dragon Knight v3 plot coherence
  - Fixed issue with AI introducing random plot elements
  - Added stronger narrative constraints
- **TASK-001c** 🟡 Defer null HP bug to combat revamp (0 hrs)
  - Document issue for PR #102 integration
  - Link to combat system overhaul

### Milestone 2: LLM I/O Format Standardization (3 hrs)
- **TASK-002** 🟡 Define exact LLM input/output format (1.5 hrs)
  - Scene # tracking system
  - Prompt structure template
  - Return data format specification
  - Debug data sections
  - Game state update format
  - Incorporate `character_creation_state_tracking_scratchpad.md`
- **TASK-003** 🟡 State sync validation framework (1.5 hrs)
  - Create test harness for prompt validation
  - Verify all prompts include master prompt
  - Document in `roadmap/scratchpad_state_sync_entity.md`
  - Run integration tests on real campaigns

### Milestone 3: Continuity & State Integrity System (8 hrs)
- **TASK-004** 🟡 Phase 1 - 10 interactions (2 hrs)
  - Build automated interaction program
  - Random planning block response selection
  - Track entity consistency metrics
  - Monitor narrative coherence
- **TASK-004b** 🟡 Phase 2 - 20 interactions (2 hrs) - MOVED TO MONDAY-THURSDAY
  - NOTE: Define requirements before starting
  - Extend test framework
  - Analyze patterns in failures
  - Generate detailed reports
- **TASK-004c** 🟡 Phase 3 - 50 interactions (2 hrs)
  - Full continuity stress test
  - Compile comprehensive metrics
  - Identify breaking points
- **TASK-129** 🔴 Implement Hard Stop on Integrity Failures (1 hr)
  - Add STRICT_INTEGRITY_MODE toggle
  - Detect integrity failures and halt gameplay
  - Provide correction options
- **TASK-003** 🟡 State sync validation (1 hr)
  - Implement tracking per character_creation_state_tracking_scratchpad.md
  - Validate all user inputs and state transitions

### Milestone 4: UI Polish - Small Tasks (2 hrs)
- **TASK-005a** 🟢 Fix campaign list click registration (0.5 hrs)
  - Debug event handlers
  - Ensure all campaigns clickable
  - Add visual feedback
- **TASK-005b** 🟢 Loading spinner with messages (1 hr)
  - Create message pool like creation
  - Implement rotation logic
  - Add to campaign continue flow
- **TASK-005c** 🟢 Fix timestamp/narrative mismatch (0.5 hrs)
  - Sync timestamps with story events
  - Ensure correct chronological display

### Milestone 5: Four-Mode System Implementation (4 hrs)
- **TASK-007a** 🟡 Mode architecture design (0.5 hrs)
  - Define mode switching mechanism
  - Create mode state management
- **TASK-007b** 🟡 DM/System Admin mode (1 hr)
  - Full game state editing
  - Narrative overrides
  - Bounded to game mechanics
- **TASK-007c** 🟡 Author mode (1 hr)
  - God-like powers within universe
  - Book-writing assistance features
- **TASK-007d** 🟡 Story mode (0.75 hrs)
  - Same D&D mechanics but hidden
  - Players can query mechanics
  - Not 100% success rate
- **TASK-007e** 🟡 Game mode (0.75 hrs)
  - Full ruleset visibility
  - Real dice rolls shown
  - Complete mechanics transparency

### Milestone 6: Campaign & Combat Improvements (3 hrs)
- **TASK-006a** 🟢 Editable campaign names (0.5 hrs)
  - Add inline editing UI
  - Save to database
- **TASK-006b** 🟢 Background story display (0.5 hrs)
  - Pause auto-scroll on creation
  - Add "Continue" button
  - Let players read at own pace
- **TASK-006c** 🟡 Enhanced Ser Arion scenario (2 hrs)
  - Add 2-3 minor combat encounters
  - Build up to Ashwood Keep assault
  - Demo all GenAI RPG features
  - Balance combat and narrative

### Milestone 7: UI/UX Major Improvements (5 hrs)
- **TASK-011a** 🟢 Theme/skin system architecture (1 hr)
  - Design CSS variable system
  - Create theme switching logic
- **TASK-008b** 🟢 Figma integration prep (1.5 hrs)
  - Review Figma designs
  - Plan component mapping
- **TASK-011c** 🟢 UI responsiveness (1.5 hrs)
  - Optimize render performance
  - Reduce re-renders
  - Improve interaction speed
- **TASK-011d** 🟢 Gemini-like snappiness (1 hr)
  - Instant feedback on all actions
  - Optimistic UI updates
  - Smooth transitions

### Milestone 8: Metrics & Optimization (3 hrs)
- **TASK-009a** ✅ **COMPLETED** Token-based logging (1 hr) - PR #264
  - Convert all character counts to tokens
  - Add token usage dashboard
- **TASK-009b** 🟢 Alexiel book compression (1 hr)
  - Implement `roadmap/alexiel_book_token_reduction_scratchpad.md`
  - Reduce token usage by 50%+
- **TASK-009c** 🟢 Parallel dual-pass optimization (1 hr)
  - Implement `mvp_site/roadmap/scratchpad_parallel_dual_pass_optimization.md`
  - Speed up response generation

### Milestone 9: Launch Preparation (4 hrs)
- **TASK-010a** 🟡 Copyright cleanup (1 hr)
  - Remove D&D references
  - Replace with "5e compatible"
- **TASK-010b** 🟡 Security validation (1 hr)
  - Input sanitization audit
  - API key protection review
- **TASK-010c** 🟡 Documentation update (1 hr)
  - User guides
  - API documentation
- **TASK-010d** 🟡 Myers-Briggs hiding (1 hr)
  - Hide personality types in UI
  - Keep for internal use only
  - Special command to reveal

### Milestone 10: Navigation & Polish (2 hrs)
- **TASK-014a** ✅ **COMPLETED** Homepage navigation (0.5 hrs) - PR #266
  - Make "WorldArchitect.AI" clickable
  - Link to landing page
- **TASK-011b** 🟢 Pagination implementation (1 hr)
  - Story content pagination
  - Load more on scroll
  - Smooth loading UX
- **TASK-012a** 🟢 Combat PR #102 review (0.5 hrs)
  - Analyze existing combat work
  - Plan integration approach
  - Schedule null HP fix

## Derek Feedback Implementation

### Priority Items from Derek's Testing
- Ensure god mode and questions don't progress narrative
- Metrics for me and other users
- Campaign default starts improvements
- Combat encounter balancing
- UI/UX pain points identified during testing

*Note: Specific Derek feedback items to be integrated as they are provided*

## Development Schedule

### Week 1 Schedule
#### Friday (8 hrs - Holiday)
- Milestone 1: Critical Bugs (4 hrs)
- Milestone 2: LLM I/O Format (3 hrs)
- Milestone 3: Start continuity testing (1 hr)

#### Saturday (8 hrs)
- **[TASK-072] Alexiel Content Review** - Review `roadmap/alexiel_content_review_saturday.md` for missing content integration (1.5 hrs)
- **[TASK-092] System Instructions Optimization** 🟡 (1.5 hrs) - PR #293
  - Consider adding world_assiah.md only once during campaign creation vs every system instruction
  - Re-evaluate all system instructions for token optimization
  - Review if all prompts need to be system instructions
  - Test impact on narrative coherence with reduced system prompts
  - Document findings in `roadmap/scratchpad_8k_optimization.md`
- **[TASK-012a] Combat System PR #102 Review** 🟡 (1 hr)
  - Review existing combat system overhaul PR
  - Plan integration approach for null HP fix
  - Document combat system architecture
- **[TASK-006c] Add Guaranteed Combat to Ser Arion** 🟡 (2 hrs)
  - Add 2-3 smaller combat encounters before Ashwood Keep
  - Build narrative tension
  - Test combat mechanics thoroughly
- **[TASK-012c] Derek Campaign Combat Issues** 🟡 (1 hr)
  - Replay Derek's campaign focusing on combat
  - Document all combat-related bugs
  - Test combat flow and balance
- Milestone 3: Complete continuity testing (1 hr)

#### Sunday (8 hrs)
- **[TASK-110] Playwright MPC Evaluate** ✅ **COMPLETED** (PR #314)
  - ✅ Comprehensive testing and MCP tool evaluation documentation completed
  - ✅ Playwright configuration and sample tests implemented
  - ✅ Integration assessment with current testing framework documented
- **[TASK-111] Zen MCP Evaluate** 🟢 (45 min)
  - Evaluate Zen MCP (Model Context Protocol) tools
  - Test integration capabilities with Claude
  - Assess potential benefits for development workflow
  - Document findings and recommendations
- **[TASK-112] Context7 MCP Server Evaluate** 🟢 (45 min)
  - Evaluate Context7 MCP Server capabilities
  - Test context management features
  - Assess integration with existing development workflow
  - Compare with other MCP solutions
- **[TASK-113] Sequential Thinking MCP Server Evaluate** 🟢 (45 min)
  - Evaluate Sequential Thinking MCP Server
  - Test step-by-step reasoning capabilities
  - Assess benefits for complex problem solving
  - Document integration possibilities
- Milestone 4: UI Polish small tasks (2 hrs)
  - Keep timestamp sync task ([TASK-005c])
  - Other small UI fixes
- Milestone 6: Campaign improvements (1.5 hrs)
- Milestone 7: Start UI major improvements (1.5 hrs)

### Week 2 Plan
- Monday-Thursday (12 hrs): Milestones 7-10

#### Next Saturday (8 hrs)
- **Milestone 5: Four-Mode System Implementation** 🟡 (6 hrs)
  - [TASK-007a] Mode architecture design (0.5 hrs)
  - [TASK-007b] DM/System Admin mode (1.5 hrs)
  - [TASK-007c] Author mode (1.5 hrs)
  - [TASK-007d] Story mode (1.25 hrs)
  - [TASK-007e] Game mode (1.25 hrs)
- Integration testing and Derek feedback (2 hrs)
