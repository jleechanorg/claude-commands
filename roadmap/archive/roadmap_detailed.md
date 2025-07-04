# WorldArchitect.AI Development Roadmap - Detailed

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

## Today's Focus - Friday, January 3, 2025 (Holiday - 8 hours)

### Morning (4 hours)
1. **TASK-001** 🔴 Fix critical bugs (1.5 hrs)
   - **TASK-001a**: Investigate malformed JSON from AI responses
   - **TASK-001b**: Fix Dragon Knight v3 plot coherence issue
2. **TASK-002** 🟡 State sync testing setup (2.5 hrs)
   - Define exact LLM I/O format with Scene#, prompts, returns
   - Create test framework for continuity

### Afternoon (4 hours)
3. **TASK-003** 🟡 Complete state sync testing (2 hrs)
   - Run integration tests for proper prompts
   - Verify master prompt inclusion
   - Document in `roadmap/scratchpad_state_sync_entity.md`
4. **TASK-004** 🟡 Start continuity testing Phase 1 (2 hrs)
   - Build automated program for 10 interactions
   - Use planning block responses

## Detailed Task Specifications

### Critical Bug Fixes
- **Null HP during combat** - DEFERRED to combat system revamp (see PR #102: https://github.com/jleechan2015/worldarchitect.ai/pull/102)
- **Malformed JSON response from AI** - Need thorough investigation of when/why AI responses fail to parse, add robust error handling
- **Dragon Knight v3 plot coherence** - AI randomly introduced unrelated crypt element, need stronger narrative constraints

### LLM I/O Format Standardization
**Explicit input/output formats must include:**
- Scene # tracking system
- Prompt structure template for LLM
- Return data format specification
- Debug data section (comes first)
- Game state updates format
- Story mode entry format
- Incorporate `character_creation_state_tracking_scratchpad.md`

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
- **Campaign list click issues** - Doesn't show spinner, clicks don't always register
- **Loading spinner with messages** - During campaign continue, add random hardcoded messages like creation
- **Timestamp/narrative mismatch** - Sync timestamps with story events
- **Let player read background story** - Currently scrolls past too quickly, add pause/continue button
- **Homepage navigation** - Make "WorldArchitect.AI" text clickable to return to homepage
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

### Parallel Work Opportunities
For different worktrees:
1. **Main worktree**: Core bug fixes and state sync
2. **Parallel worktree 1**: Token optimization and compression
3. **Parallel worktree 2**: UI improvements and themes

### Derek Feedback Items
*To be provided and integrated later*

## Development Schedule

### Week 1 (Jan 3-9, 2025)

#### Friday, Jan 3 (8 hrs - Holiday)
- TASK-001: Critical bugs (1.5 hrs)
- TASK-002: State sync setup (2.5 hrs)
- TASK-003: Complete state sync (2 hrs)
- TASK-004: Start continuity testing (2 hrs)

#### Saturday, Jan 4 (8 hrs)
- TASK-004: Complete Phase 1 continuity (2 hrs)
- TASK-007: Four-mode system (4 hrs)
- TASK-005: UI Polish small tasks (2 hrs)

#### Sunday, Jan 5 (8 hrs)
- TASK-008: Continuity Phase 2 (2 hrs)
- TASK-006: Campaign improvements (2 hrs)
- TASK-009: UI Polish medium tasks (2 hrs)
- TASK-011: Start UI major improvements (2 hrs)

#### Monday-Thursday (12 hrs total)
- TASK-010: Continuity Phase 3 - 50 interactions (2 hrs)
- TASK-011: Complete UI major improvements (3 hrs)
- TASK-300: Metrics & optimization (3 hrs)
- TASK-012: Launch preparation start (4 hrs)

### Week 2 (Jan 10-16, 2025)

#### Friday (3 hrs)
- TASK-012: Complete launch preparation (3 hrs)

#### Weekend (16 hrs)
- TASK-013: Combat system PR review & integration (4 hrs)
- TASK-014: Derek feedback implementation (4 hrs)
- TASK-015: Testing and polish (8 hrs)

## Notes

- All time estimates reduced by 50% for AI-assisted development
- Use `roadmap next` command to get next task
- Use `roadmap finish [UUID]` to mark complete
- Each PR must reference task UUIDs
- Update scratchpads with detailed progress