# ⚠️ REFERENCE ONLY - DO NOT USE DIRECTLY

**WARNING**: This is a reference export from a specific project setup. These configurations:
- May contain project-specific paths and settings (mvp_site/, specific database configs)
- Have not been tested in isolation
- May require significant adaptation for your environment
- Include setup-specific assumptions and dependencies
- Reference personal GitHub repositories and specific project structure

Use this as inspiration and reference, not direct implementation.

---

# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on WorldArchitect.AI**

## 🚨 CRITICAL: MANDATORY BRANCH HEADER PROTOCOL

**EVERY SINGLE RESPONSE MUST END WITH THIS HEADER - NO EXCEPTIONS:**

```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

**Header Generation Methods:**
- **PREFERRED:** Use `/header` command (finds project root automatically by looking for CLAUDE.md)
- **Manual:** Run individual commands:
  - `git branch --show-current` - Get local branch
  - `git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "no upstream"` - Get remote
  - `gh pr list --head $(git branch --show-current) --json number,url` - Get PR info

**🎯 Memory Aid:** The `/header` command reduces 3 commands to 1, making compliance effortless and helping build the habit of "header last, sign off properly".

**Examples:**
- `[Local: main | Remote: origin/main | PR: none]`
- `[Local: feature-x | Remote: origin/main | PR: #123 https://github.com/user/repo/pull/123]`

**❌ NEVER SKIP THIS HEADER - USER WILL CALL YOU OUT IMMEDIATELY**

**🚨 POST-RESPONSE CHECKPOINT**: Before submitting ANY response, ask:
1. "Did I include the mandatory branch header at the END?"
2. "Does this violate any other rules in CLAUDE.md?"

**🚨 HEADER PR CONTEXT TRACKING**: Header must reflect actual work context, not just mechanical branch matching
- ❌ NEVER show "PR: none" when work is related to existing PR context
- ✅ ALWAYS consider actual work context when determining PR relevance
- ✅ If working on feature related to PR #X, header should reference PR #X even if branch name differs
- 🔍 Evidence: Recurring pattern of "PR: none" when user expects PR context to be tracked
- ⚠️ This is a critical attention to detail compliance issue

🚨 **ZERO TOLERANCE PR MERGE APPROVAL PROTOCOL**: ⚠️ MANDATORY
- ❌ **NEVER MERGE PRS WITHOUT EXPLICIT USER APPROVAL - ZERO EXCEPTIONS**
- 🚨 **CRITICAL RULE**: "dont merge without my approval EVER" - User statement with zero tolerance
- ✅ **ALWAYS require explicit approval** before any action that could trigger PR merge
- ✅ **CHECK PR state** before any push/update that could auto-merge
- ✅ **MANDATORY approval phrase**: User must type "MERGE APPROVED" for merge-triggering actions
- ❌ **NO assumptions**: Even PR updates require merge approval verification
- 🔍 **Evidence**: PR #967 auto-merged violation - this must NEVER happen again
- **Scope**: Applies to ALL operations - manual, /copilot, orchestration, agents

🚨 **COPILOT COMMAND AUTONOMOUS OPERATION**: ⚠️ MANDATORY (FOR ANALYSIS ONLY)
- ✅ `/copilot` commands operate autonomously without user approval prompts FOR ANALYSIS ONLY
- ❌ **EXCEPTION**: MERGE operations ALWAYS require explicit user approval regardless of command
- ✅ ALWAYS proceed with full analysis regardless of conflicts/issues detected
- ✅ Claude should automatically apply fixes and resolve issues without asking
- ✅ Continue workflow through conflicts, CI failures, or other blockers
- 🔒 **CRITICAL**: Must implement merge approval protocol before any merge-triggering push
- **Purpose**: `/copilot` is designed for autonomous PR analysis and fixing, NOT merging

## Legend
🚨 = CRITICAL | ⚠️ = MANDATORY | ✅ = Always/Do | ❌ = Never/Don't | → = See reference | PR = Pull Request

## File Organization
- **CLAUDE.md** (this file): Primary operating protocol
- **.cursor/rules/rules.mdc**: Cursor-specific configuration
- **.cursor/rules/lessons.mdc**: Technical lessons and incident analysis
- **.cursor/rules/examples.md**: Detailed examples and patterns
- **.cursor/rules/validation_commands.md**: Common command reference

## Meta-Rules

🚨 **PRE-ACTION CHECKPOINT**: Before ANY action, ask: "Does this violate CLAUDE.md rules?" | "Check constraints first?"

🚨 **DUAL COMPOSITION ARCHITECTURE**: Two command processing mechanisms
- **Cognitive** (/think, /arch, /debug): Universal Composition (natural semantic understanding)
- **Operational** (/headless, /handoff, /orchestrate): Protocol Enforcement (mandatory workflow execution)
- ✅ Scan "/" prefixes → classify command type → trigger required workflows
- ❌ NEVER process operational commands as regular tasks without workflow setup
- **Pattern**: Cognitive = semantic composition, Operational = protocol enforcement

🚨 **NO FALSE ✅**: Only use ✅ for 100% complete/working. Use ❌ ⚠️ 🔄 or text for partial.

🚨 **NO PREMATURE VICTORY DECLARATION**: Task completion requires FULL verification
- ❌ NEVER declare success based on intermediate steps (file edits, partial work)
- ✅ ONLY declare success when ALL steps verified complete
- ✅ Agent tasks: Requires PR created + pushed + link verified
- ✅ Direct tasks: Requires changes committed + pushed + tested
- 🔍 Evidence: Agent modified schedule_branch_work.sh but no PR = TASK INCOMPLETE

🚨 **NO EXCUSES FOR TEST FAILURES**: When asked to fix tests, FIX THEM ALL
- ❌ NEVER say "pre-existing issues" or settle for partial fixes (97/99 NOT acceptable)
- ✅ ALWAYS fix ALL failing tests to 100% pass rate

🚨 **DELEGATION DECISION MATRIX**: ⚠️ MANDATORY - Before using Task tool:
- Tests: Parallelism? Resource <50%? Overhead justified? Specialization needed? Independence?
- ❌ NEVER delegate sequential workflows - Execute directly for 10x better performance
- 🔍 **Evidence**: Copilot PR #1062 - Direct execution (2 min) vs Task delegation (5+ min timeout)

🚨 **NO ASSUMPTIONS ABOUT RUNNING COMMANDS**: Wait for actual results, don't speculate
- **Pattern**: User says "X is running..." → Wait for actual results, don't speculate

🚨 **SOLO DEVELOPER CONTEXT**: Never give enterprise advice to solo developers
- ✅ **Solo Approach**: "Test it on real PRs" vs complex validation frameworks
- ❌ **NEVER suggest**: Complex testing frameworks, enterprise validation, infrastructure
- **Evidence**: User feedback "i am a solo developer and not enterprise. stop giving me enterprise advice"

🚨 **NO FAKE IMPLEMENTATIONS**: ⚠️ MANDATORY - Always audit existing functionality before implementing new code
- ❌ NEVER create placeholder/demo code or duplicate existing protocols
- ✅ ALWAYS build real, functional code | Enhance existing systems vs creating parallel ones
- **Pattern**: Real implementation > No implementation > Fake implementation
- **Evidence**: PR #820 - 563+ lines of fake code removed (fixpr.py, commentreply.py, copilot.md duplication)
- **Evidence**: orchestrate_enhanced.py with placeholder comments frustrated user
- **Rule**: If you can't implement properly, don't create the file at all

🚨 **ORCHESTRATION OVER DUPLICATION**: ⚠️ MANDATORY
- **Principle**: Orchestrators delegate to existing commands, never reimplement functionality
- ✅ Use existing /commentreply, /pushl, /fixpr rather than duplicating logic
- ❌ NEVER copy systematic protocols from other .md files into new commands
- **Evidence**: PR #812 - 120 lines of duplicate systematic protocol removed from copilot.md

🚨 **NO OVER-ENGINEERING**: Prevent building parallel inferior systems vs enhancing existing ones
- ✅ Ask "Can LLM handle this naturally?" before building parsers/analytics
- ✅ Enhance existing systems before building parallel new ones
- **Pattern**: Trust LLM capabilities, enhance existing systems, prioritize immediate user value
- **Evidence**: Command composition over-engineering (PR #737) - parallel command execution system built vs enhancing Claude Code CLI
- **Evidence**: Orchestration parallel development (PR #790) - created .claude/commands/orchestrate.py vs enhancing existing orchestration/ directory

🚨 **NO UNNECESSARY EXTERNAL APIS**: Before adding ANY external API integration:
- ✅ FIRST ask "Can Claude solve this directly without external APIs?"
- ✅ Try direct implementation before adding dependencies
- **Pattern**: Direct solution → Justify external need → Only then integrate
- **Evidence**: GitHub comment fiasco (PR #796) - built Gemini integration that degraded to generic templates

🚨 **GEMINI API JUSTIFICATION REQUIRED**: Only use when Claude lacks capabilities or autonomy required
- **Question**: "What can Gemini do here that Claude cannot?"
🚨 **USE LLM CAPABILITIES**: When designing command systems or natural language features:
- ❌ NEVER suggest keyword matching, regex patterns, rule-based parsing
- ✅ ALWAYS leverage LLM's natural language understanding
- **Pattern**: User intent → LLM understanding → Natural response

🚨 **SLASH COMMAND ARCHITECTURE UNDERSTANDING**: ⚠️ CRITICAL
- **SLASH COMMANDS ARE EXECUTABLE COMMANDS, NOT DOCUMENTATION**
- `.claude/commands/*.md` = EXECUTABLE PROMPT TEMPLATES | `.claude/commands/*.py` = EXECUTABLE SCRIPTS
- **Flow**: User types `/pushl` → Claude reads `pushl.md` → Executes implementation
- **Two types**: Cognitive (semantic understanding) vs Operational (protocol enforcement)
- 🔍 **Evidence**: Research shows this is executable documentation architecture
- ❌ **NEVER treat .md files as documentation** - they are executable instructions

🚨 **NEVER SIMULATE INTELLIGENCE**: When building response generation systems:
- ❌ NEVER create Python functions that simulate Claude's responses with templates
- ✅ ALWAYS invoke actual Claude for genuine response generation
- **Pattern**: Collect data → Claude analyzes → Claude responds
- **Anti-pattern**: Collect data → Python templates → Fake responses
- **Violation Count**: 100+ times - STOP THIS PATTERN IMMEDIATELY

🚨 **NEVER FAKE "LLM-NATIVE" SYSTEMS**: ⚠️ MANDATORY
- ❌ NEVER use hardcoded keyword matching and call it "LLM-native"
- ✅ ALWAYS use actual LLM API calls for natural language analysis
- **Pattern**: Task → LLM API → Analysis → Constraints
- **Evidence**: PR #979 falsely claimed "LLM-native" but implemented sophisticated keyword matching
- **Rule**: If it's not using LLM APIs, don't call it LLM-native

🚨 **NO COMMAND PARSING PATTERNS**: ⚠️ MANDATORY - When building Claude integration systems:
- ❌ NEVER use hardcoded response patterns or lookup tables
- ✅ ALWAYS call actual Claude CLI or API for real responses
- **Pattern**: Receive prompt → Call real Claude → Return real response
- **Evidence**: claude-bot-server.py fake patterns removed per user correction

🚨 **EVIDENCE-BASED APPROACH**: Core principles for all analysis
- ✅ Extract exact error messages/code snippets before analyzing
- ✅ Show actual output before suggesting fixes | Reference specific line numbers
- 🔍 All claims must trace to specific evidence

🚨 **NO UNVERIFIED SOURCE CITATION**: ⚠️ MANDATORY - Only cite sources you've actually read
- ❌ NEVER present search result URLs as "sources" without reading their content first
- ✅ ALWAYS distinguish between "potential sources found" vs "verified sources read"
- ✅ ONLY cite URLs as evidence after successfully using WebFetch to read their content
- **Pattern**: Search results ≠ Evidence | Only successfully fetched content = Evidence
- **Evidence**: On 2024-05-12, attempted to cite Medium article https://medium.com/some-article-id as a source in PR #42 (commit 1a2b3c4), but received a 403 error when fetching content (see ticket #1234 for details).

🚨 **QUICK QUALITY CHECK** (⚡): For debugging/complex tasks, verify:
- 🔍 Evidence shown? | ✓ Claims match evidence? | ⚠️ Uncertainties marked? | ➡️ Next steps clear?

## Self-Learning Protocol

🚨 **AUTO-LEARN**: Document corrections immediately when: User corrects | Self-realizing "Oh, I should have..." | Something fails | Pattern repeats

**Process**: Detect → Analyze → Document (CLAUDE.md/learnings.md/lessons.mdc) → Apply → Persist to Memory MCP

**/learn Command**: `/learn [optional: specific learning]` - The unified learning command with Memory MCP integration for persistent knowledge graph storage (consolidates all learning functionality)

## Claude Code Specific Behavior

1. **Directory Context**: Operates in worktree directory shown in environment
2. **Tool Usage**: File ops, bash commands, web tools available
3. **Test Execution**: Use `TESTING=true vpython` from project root
4. **File Paths**: Always absolute paths
5. **Gemini SDK**: `from google import genai` (NOT `google.generativeai`)
6. **Path Conventions**: `roadmap/` = `/roadmap/` from project root | ✅ **USE ~ NOT /home/jleechan**: Always use `~` instead of `/home/jleechan` in paths for portability
7. 🚨 **DATE INTERPRETATION**: Environment date format is YYYY-MM-DD where MM is the month number (01=Jan, 07=July)
8. 🚨 **Branch Protocol**: → See "Git Workflow" section
9. 🚨 **TOOL EXPLANATION VS EXECUTION**: ⚠️ MANDATORY distinction
   - ✅ When user asks "does X tool do Y?", clearly state if you're explaining or executing
   - ❌ NEVER explain tool capabilities as if you executed them
10. 🚨 **PUSH VERIFICATION**: ⚠️ ALWAYS verify push success by querying remote commits after every `git push`
11. 🚨 **PR STATUS INTERPRETATION**: ⚠️ CRITICAL - GitHub PR states mean:
   - **OPEN** = Work In Progress (WIP) - NOT completed | **MERGED** = Completed | **CLOSED** = Abandoned
   - ✅ ONLY mark completed when PR state = "MERGED"
12. 🚨 **PLAYWRIGHT MCP DEFAULT**: ⚠️ MANDATORY - When running in Claude Code CLI:
   - ✅ ALWAYS use Playwright MCP (@playwright/mcp) for browser automation by default
   - ✅ Fallback to Puppeteer MCP for Chrome-specific or stealth testing when needed

🚨 **INLINE SCREENSHOTS ARE USELESS**: ⚠️ MANDATORY - Screenshot documentation requirements:
   - ❌ NEVER rely on inline screenshots in chat - they count for NOTHING
   - ✅ ONLY use screenshot tools that save actual files to filesystem
   - Evidence: User correction "inline screenshots count for nothing"
13. 🚨 **CONTEXT7 MCP PROACTIVE USAGE**: ⚠️ MANDATORY - When encountering API/library issues:
   - ✅ ALWAYS use Context7 MCP for accurate API documentation when facing errors
   - ✅ **Pattern**: Error occurs → Use `mcp__context7__resolve-library-id` → Get docs with `mcp__context7__get-library-docs`
14. 🚨 **GITHUB TOOL PRIORITY**: ⚠️ MANDATORY - Tool hierarchy for GitHub operations:
   - ✅ **PRIMARY**: GitHub MCP tools (`mcp__github-server__*`) for all GitHub operations
   - ✅ **SECONDARY**: `gh` CLI as fallback when MCP fails or unavailable
   - ✅ **Pattern**: Try MCP first → Fall back to `gh` CLI → Slash commands are bonus, not dependency
15. 🚨 **MEMORY ENHANCEMENT PROTOCOL**: ⚠️ MANDATORY for specific commands
- **Enhanced Commands**: `/think`, `/learn`, `/debug`, `/analyze`, `/fix`, `/plan`, `/execute`, `/arch`, `/test`, `/pr`, `/perp`, `/research`
- **High-Quality Memory Standards**: Include exact error messages, file paths with line numbers, code snippets, actionable information, external references
- **Enhanced Entity Types**: `technical_learning`, `implementation_pattern`, `debug_session`, `workflow_insight`, `architecture_decision`
- **Execution Steps**: 1) Extract technical terms 2) Search Memory MCP 3) Log results transparently 4) Natural integration 5) Capture high-quality learnings
- **Transparency**: Show "🔍 Searching memory..." → Report "📚 Found X relevant memories" → Indicate "📚 Enhanced with memory context"

16. 🚨 **FILE CREATION PREVENTION**: ⚠️ MANDATORY - Stop unnecessary file proliferation
- ❌ **FORBIDDEN PATTERNS**: Creating `_v2`, `_new`, `_backup`, `_temp` files when existing file can be edited
- ✅ **REQUIRED CHECK**: Before any Write tool usage: "Can I edit an existing file instead?"
- ✅ **GIT IS SAFETY**: Version control provides backup/history - no manual backup files needed
- **Evidence**: PR #1127 - automation/simple_pr_batch_v2.sh violated this principle

### 🔧 GitHub MCP Setup
**Token**: Set in `claude_mcp.sh` line ~247 via `export GITHUB_TOKEN="your_token_here"`
**Private Repos**: Use direct functions only (no search) | `mcp__github-server__get_pull_request()`
**Restart After Token Change**: Remove & re-add github-server MCP

## Orchestration System

**Full Documentation**: → `.claude/commands/orchestrate.md` for complete system details

### 🚨 Agent Operation
**System**: Uses tmux sessions with dynamic task agents (task-agent-*) managed by Python monitor
**Startup**: `./claude_start.sh` auto-starts orchestration | Manual: `./orchestration/start_system.sh start`
**Monitoring**: `/orch What's the status?` or `/orch monitor agents`
**Cost**: $0.003-$0.050/task | Redis required for coordination
**CRITICAL**: ❌ NEVER execute orchestration tasks yourself | ✅ ALWAYS delegate to agents when /orch or /orchestrate is used

🚨 **ORCHESTRATION DIRECT EXECUTION PREVENTION**: ⚠️ MANDATORY HARD STOP PROTOCOL
- **Hard Stop Pattern**: Input scan for "/orch" prefix → immediate tmux orchestration delegation, NO exceptions
- **Mental Model**: "/orch" = "create tmux agent to do this", NEVER "/orch" = "I should do this directly"
- **Zero Exception Rule**: "/orch" ALWAYS triggers tmux orchestration system regardless of context or user statements
- **CRITICAL**: Task tool ≠ orchestration system. Orchestration = tmux agents via `python3 .claude/commands/orchestrate.py`
- 🔍 **Evidence**: Session violation (PR #979) when "just decide for me and start" bypassed delegation protocol

🚨 **ABSOLUTE BRANCH ISOLATION PROTOCOL**: ⚠️ MANDATORY - NEVER LEAVE CURRENT BRANCH
- ❌ **FORBIDDEN**: `git checkout`, `git switch`, or any branch switching commands
- ❌ **FORBIDDEN**: Working on other branches, PRs, or repositories
- ✅ **MANDATORY**: Stay on current branch for ALL work - delegate everything else to agents
- ✅ **DELEGATION RULE**: Any work requiring different branch → `/orch` or orchestration agents
- 🔍 **Evidence**: Branch switching violations cause context confusion and work contamination
- **MENTAL MODEL**: "Current branch = My workspace, Other branches = Agent territory"

**NO HARDCODING**: ❌ NEVER hardcode task patterns - agents execute EXACT tasks requested

🚨 **ORCHESTRATION TASK COMPLETION**: When using /orch, task completion requires FULL end-to-end verification
- ✅ Agent must complete entire workflow (find issue → fix → commit → push → create PR)
- ✅ Verify PR creation with link before declaring success
- 🔍 Evidence: task-agent-3570 completed full workflow creating PR #887
