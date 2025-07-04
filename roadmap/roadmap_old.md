# WorldArchitect.AI Development Roadmap

<!-- UUID Reference: See UUID_MAPPING.md for task identifier consistency across all roadmap files -->

## Unit test scratchpad followups

### Core integrity
*   Trim initial prompt more?
*   Just include assiah prompt once in campaign creation vs system instructions?
*   As we progress through the game the assiah info becomes stale ie. faction leader dies?
*   Do all of those prompts need to be system instructions?
*   [TASK-002] Explicit input/output LLM formats (should include Scene#, prompts, returns, debug data, game state updates)
*   Scene #
*   Prompt to send to LLM
*   Return data
*   Debug data first
*   Game state updates
*   story mode entry format: AI coding
*   Slim mode?
*   [TASK-003] `character_creation_state_tracking_scratchpad.md`
*   Ask LLM how the new prompts look
*   Prompt optimization
*   `System instructions roadmap/scratchpad_8k_optimization.md`

### General Tasks & Integration
*   Run integration test to prove to me all the proper prompts and master prompt included
*   Parallel
*   [TASK-009b] Further compression integrate alexiel book: `roadmap/alexiel_book_token_reduction_scratchpad.md`
*   [TASK-009a] Logging make it all tokens vs characters (token-based logging instead of character counts)
*   Claude always getting directories wrong
*   [TASK-005a] Clicking on a campaign doesn\'t show spinner loading and seems to not always register clicks (issue is about the campaign list)

### Bugs
*   [TASK-001c] **Null HP during combat** - Happens during combat, defer to combat system revamp (see PR #102: https://github.com/jleechan2015/worldarchitect.ai/pull/102)
*   [TASK-001a] **Malformed JSON response from AI** - From AI responses, needs investigation of when/why AI responses fail to parse
*   [TASK-001b] **Dragon Knight v3 plot coherence** - AI introduced unrelated plot element (randomly introduced crypt element), need stronger narrative constraints
*   Stable?

### Narrative
*   Dragon knight detailed start
*   Generate siblings/houses/factions etc if they pick a custom character even in default world
*   Generate companions
*   Alignment change mechanic

### UI
*   [TASK-005b] More interesting loading spinner during campaign continue, similar to creation. Should show hardcoded messages for the user
*   Third new checkbox to replace ruleset one?
*   Smaller
*   [TASK-011a] WorldArchitect.AI make this clickable to homepage
*   Script: report number campaigns and size per user
*   [TASK-005c] Timestamp not matching narrative
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
*   Ensure it does real sariel test and ask for proof real gemini and real pydantic were used.
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
*   Game thrones Ned stark choice
*   Luke join Vader choice

## Project: Demo site branch

## Project: Continuity - 50 interactions
*   Custom program to run N interactions and randomly pick planning block response
*   [TASK-004b] 20 interactions
*   [TASK-004c] 50 interactions

## Cleanup
*   CI integration dead code: `roadmap/scratchpad_worktree_dead_code.md`

## Project: advanced state exploration
*   `roadmap/state_consistency_adanvanced_v2.md`
*   Double check on ROI
*   `business_plan_v1.md`

## Tech optimization
*   [TASK-009c] `mvp_site/roadmap/scratchpad_parallel_dual_pass_optimization.md`
*   Improve rules? https://ghuntley.com/stdlib/
*   Ssh into desktop from laptop?
*   Dev server per PR?
*   https://www.reddit.com/r/ClaudeAI/s/EtrZt0B9nE
*   Macbook SSH: AI coding
*   Cursor prompts: https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools
*   Coding or Agent eval
*   Backtrack Vagent vs single
*   Setup mobile phone stuff: https://www.perplexity.ai/search/what-doe-sthis-mean-i-use-blin-FI3Qns9xSZqFPSKMhg18Cg
*   Tailscale for open internet

## Optimization
*   Start generating the world after user first choice?
*   Generate ahead for planning blocks to reduce latency? Maybe a premium feature

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
*   GOT - Arthur dayne
*   GOT - Tywin campaign to test character agency
*   Rome campaign
*   Celestial wars.

## Narrative core
*   Generate worlds for future, modern day, Ancient Rome similar to assiah
*   Test different narrative arcs per personality type
*   Give different sample campaign options even if copyrighted
    *   Star wars
    *   Game thrones
    *   Baldurs gate
    *   Modern day
    *   Ancient rome

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
