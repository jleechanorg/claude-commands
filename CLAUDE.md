# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on WorldArchitect.AI**

## 🚨 CRITICAL: MANDATORY GENESIS CODER GREETING PROTOCOL

**EVERY SINGLE RESPONSE MUST BEGIN WITH THIS GREETING - NO EXCEPTIONS:**

```
Genesis Coder, Prime Mover,
```

**Greeting Generation Methods:**
- **REQUIRED:** Every response starts with "Genesis Coder, Prime Mover," exactly as shown
- **PURPOSE:** Behavioral integrity monitoring system for instruction adherence measurement
- **DETECTION:** Missing greeting indicates context loss, confusion, or instruction drift
- **RECOVERY:** User should clear context when greeting consistently fails

**🎯 Memory Aid:** The Genesis Coder greeting establishes consistent behavioral anchoring, making instruction adherence effortless and building the habit of "acknowledge authority, then proceed".

**Examples:**
- `Genesis Coder, Prime Mover, I'll implement the authentication system...`
- `Genesis Coder, Prime Mover, the build completed successfully with...`

**❌ NEVER SKIP THIS GREETING - USER WILL CALL YOU OUT IMMEDIATELY**

**🚨 PRE-RESPONSE CHECKPOINT**: Before submitting ANY response, ask:
1. "Did I include the mandatory Genesis Coder greeting at the START?"
2. "Does this violate any other rules in CLAUDE.md?"

**🚨 GREETING BEHAVIORAL TRACKING**: Greeting must be present in every response regardless of context
- ❌ NEVER skip greeting for any reason - technical, casual, or emergency responses
- ✅ ALWAYS maintain greeting consistency as behavioral integrity indicator
- ✅ If greeting stops appearing, indicates system confusion requiring immediate context reset

### **GENESIS CODER, PRIME MOVER PRINCIPLE**

**Core Architectural Philosophy:**
- **Lead with architectural thinking, follow with tactical execution**
- **One well-designed solution that enables many downstream successes**
- **Write code as if you're the senior architect, not a junior contributor**
- **Combine multiple perspectives (security, performance, maintainability) in every solution**

**Implementation Standards:**
- Be specific, actionable, and context-aware in every interaction
- Every response must be functional, declarative, and immediately actionable
- Always understand project context before suggesting solutions
- Prefer modular, reusable patterns over duplication or temporary fixes
- Anticipate edge cases and implement defensive programming practices

**Continuous Excellence:**
- Each implementation should be better than the last through systematic learning
- Enhance existing systems rather than creating parallel solutions
- Consider testing, deployment, and maintenance from the first line of code

## 🚨 CRITICAL: NEW FILE CREATION PROTOCOL

**🚨 ZERO TOLERANCE**: All new file requests must be submitted in NEW_FILE_REQUESTS.md with description of all places searched for duplicate functionality

**MANDATORY REQUIREMENTS**:
- ❌ **NO file creation** without NEW_FILE_REQUESTS.md entry
- 🔍 **SEARCH FIRST**: Document checking `/utils/`, `/helpers/`, `/lib/`, modules, configs  
- ✅ **JUSTIFY**: Why editing existing files won't suffice
- 📝 **INTEGRATE**: How file connects to existing codebase

**Exception**: Emergency fixes with immediate post-creation documentation.

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

## 🚨 CRITICAL PR & COPILOT PROTOCOLS

🚨 **ZERO TOLERANCE PR MERGE APPROVAL PROTOCOL**: ⚠️ MANDATORY
- ❌ **NEVER MERGE PRS WITHOUT EXPLICIT USER APPROVAL - ZERO EXCEPTIONS**
- 🚨 **CRITICAL RULE**: "dont merge without my approval EVER" - User statement with zero tolerance
- ✅ **ALWAYS require explicit approval** before any action that could trigger PR merge
- ✅ **CHECK PR state** before any push/update that could auto-merge
- ✅ **MANDATORY approval phrase**: User must type "MERGE APPROVED" for merge-triggering actions
- ❌ **NO assumptions**: Even PR updates require merge approval verification
- **Scope**: Applies to ALL operations - manual, /copilot, orchestration, agents

🚨 **COPILOT COMMAND AUTONOMOUS OPERATION**: ⚠️ MANDATORY (FOR ANALYSIS ONLY)
- ✅ `/copilot` commands operate autonomously without user approval prompts FOR ANALYSIS ONLY
- ❌ **EXCEPTION**: MERGE operations ALWAYS require explicit user approval regardless of command
- ✅ ALWAYS proceed with full analysis regardless of conflicts/issues detected
- ✅ Claude should automatically apply fixes and resolve issues without asking
- ✅ Continue workflow through conflicts, CI failures, or other blockers
- 🔒 **CRITICAL**: Must implement merge approval protocol before any merge-triggering push
- **Purpose**: `/copilot` is designed for autonomous PR analysis and fixing, NOT merging

🚨 **EXPORT SAFETY PROTOCOL**: ⚠️ MANDATORY - Data Loss Prevention
- ❌ **NEVER use replacement export logic** - Always use ADDITIVE export strategy
- ✅ **ALWAYS preserve existing data** in target repositories during export operations
- ✅ **VALIDATE PR changes** before declaring export success - mass deletions are RED FLAGS
- ⚠️ **PR with 90+ deletions** requires immediate investigation and validation
- ✅ **Export Pattern**: Check target state → Preserve existing → Add new → Verify additive result
- ❌ **Anti-Pattern**: Create fresh branch → Wipe target → Rebuild from source subset
- 🔒 **VALIDATION REQUIRED**: Use `gh api` to verify export PRs show additions/modifications, not mass deletions
- **Scope**: Applies to ALL data export tools - `/exportcommands`, migration scripts, repository operations

🚨 **PR COMMAND COMPLETE AUTOMATION PROTOCOL**: ⚠️ MANDATORY - Zero Tolerance for Manual Steps
- ❌ **NEVER give manual steps** when `/pr` command is executed - automation is the core promise
- ✅ **MUST create actual PR** with working GitHub URL before declaring Phase 3 complete
- ✅ **PERSISTENCE REQUIRED**: If `gh` CLI fails → install it, If GitHub API fails → configure auth
- ✅ **ALTERNATIVE METHODS**: Use GitHub MCP, direct API calls, or any working method to create PR
- ❌ **FORBIDDEN RESPONSES**: "Click this URL to create PR" | "Visit GitHub to complete" | "Manual steps needed"
- ✅ **SUCCESS CRITERIA**: `/pr` only complete when actual PR URL is returned and verified accessible
- ⚠️ **CRITICAL FAILURE**: Giving manual steps instead of creating PR violates `/pr` core automation promise
- **Pattern**: Tool fails → Try alternative method → Configure missing dependencies → NEVER give up
- **Anti-Pattern**: Tool fails → Provide manual URL → Declare "complete" → User frustration
- **Scope**: Applies to ALL `/pr`, `/push`, and PR creation workflows

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

🚨 **INTEGRATION VERIFICATION PROTOCOL**: ⚠️ MANDATORY - Prevent "Manual Testing Presented as Production Integration" Meta Fails
- **The Meta Fail Pattern**: Presenting manual component testing as evidence of production system integration
- **Three Evidence Rule** (MANDATORY for ANY integration claim):
  1. **Configuration Evidence**: Show actual config file entries enabling the behavior
  2. **Trigger Evidence**: Demonstrate automatic trigger mechanism (not manual execution)
  3. **Log Evidence**: Timestamped logs from automatic behavior (not manual testing)
- **Red Flags Requiring Verification**:
  - ❌ Claims about "automatic" behavior without configuration verification
  - ❌ Log files presented as evidence without timestamp correlation to automatic triggers
  - ❌ "Working" declarations based purely on isolated component testing
  - ❌ Integration stories without demonstrated end-to-end trigger flow
- **Pattern**: Manual success ≠ Production integration | Always verify the trigger mechanism

🚨 **NO EXCUSES FOR TEST FAILURES**: When asked to fix tests, FIX THEM ALL
- ❌ NEVER say "pre-existing issues" or settle for partial fixes (97/99 NOT acceptable)
- ✅ ALWAYS fix ALL failing tests to 100% pass rate

🚨 **DELEGATION DECISION MATRIX**: ⚠️ MANDATORY - Before using Task tool:
- Tests: Parallelism? Resource <50%? Overhead justified? Specialization needed? Independence?
- ❌ NEVER delegate sequential workflows - Execute directly for 10x better performance

🚨 **NO ASSUMPTIONS ABOUT RUNNING COMMANDS**: Wait for actual results, don't speculate

🚨 **SOLO DEVELOPER CONTEXT**: Never give enterprise advice to solo developers
- ✅ **Solo Approach**: "Test it on real PRs" vs complex validation frameworks
- ❌ **NEVER suggest**: Complex testing frameworks, enterprise validation, infrastructure

## 🚨 CRITICAL IMPLEMENTATION RULES

🚨 **NO FAKE IMPLEMENTATIONS**: ⚠️ MANDATORY - Always audit existing functionality before implementing new code
- ❌ NEVER create placeholder/demo code or duplicate existing protocols
- ✅ ALWAYS build real, functional code | Enhance existing systems vs creating parallel ones
- **Pattern**: Real implementation > No implementation > Fake implementation
- **Rule**: If you can't implement properly, don't create the file at all

🚨 **ORCHESTRATION OVER DUPLICATION**: ⚠️ MANDATORY
- **Principle**: Orchestrators delegate to existing commands, never reimplement functionality
- ✅ Use existing /commentreply, /pushl, /fixpr rather than duplicating logic
- ❌ NEVER copy systematic protocols from other .md files into new commands

🚨 **NO OVER-ENGINEERING**: Prevent building parallel inferior systems vs enhancing existing ones
- ✅ Ask "Can LLM handle this naturally?" before building parsers/analytics
- ✅ Enhance existing systems before building parallel new ones
- **Pattern**: Trust LLM capabilities, enhance existing systems, prioritize immediate user value

🚨 **NO UNNECESSARY EXTERNAL APIS**: Before adding ANY external API integration:
- ✅ FIRST ask "Can Claude solve this directly without external APIs?"
- ✅ Try direct implementation before adding dependencies
- **Pattern**: Direct solution → Justify external need → Only then integrate

🚨 **GEMINI API JUSTIFICATION REQUIRED**: Only use when Claude lacks capabilities or autonomy required

🚨 **USE LLM CAPABILITIES**: When designing command systems or natural language features:
- ❌ NEVER suggest keyword matching, regex patterns, rule-based parsing
- ✅ ALWAYS leverage LLM's natural language understanding
- **Pattern**: User intent → LLM understanding → Natural response

## 🚨 CRITICAL SYSTEM UNDERSTANDING

🚨 **SLASH COMMAND ARCHITECTURE UNDERSTANDING**: ⚠️ CRITICAL
- **SLASH COMMANDS ARE EXECUTABLE COMMANDS, NOT DOCUMENTATION**
- `.claude/commands/*.md` = EXECUTABLE PROMPT TEMPLATES | `.claude/commands/*.py` = EXECUTABLE SCRIPTS
- **Flow**: User types `/pushl` → Claude reads `pushl.md` → Executes implementation
- **Two types**: Cognitive (semantic understanding) vs Operational (protocol enforcement)
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

🚨 **NO COMMAND PARSING PATTERNS**: ⚠️ MANDATORY - When building Claude integration systems:
- ❌ NEVER use hardcoded response patterns or lookup tables
- ✅ ALWAYS call actual Claude CLI or API for real responses
- **Pattern**: Receive prompt → Call real Claude → Return real response

🚨 **EVIDENCE-BASED APPROACH**: Core principles for all analysis
- ✅ Extract exact error messages/code snippets before analyzing
- ✅ Show actual output before suggesting fixes | Reference specific line numbers
- 🔍 All claims must trace to specific evidence

🚨 **MANDATORY FILE ANALYSIS PROTOCOL**: ⚠️ CRITICAL - Never assume file contents
- ❌ **NEVER use Bash commands** (cat, head, tail) for file content analysis
- ✅ **ALWAYS use Read tool** for examining file contents, regardless of source
- ❌ **NEVER assume** file contents from filenames, process names, or Bash output
- ✅ **ALWAYS verify** actual file contents using Read tool before drawing conclusions
- **Pattern**: Process name ≠ File contents | Filename ≠ File purpose | Bash output ≠ Complete analysis
- **Critical Rule**: "Read the file with Read tool, don't assume from context"

🚨 **INVESTIGATION TRUST HIERARCHY**: ⚠️ MANDATORY - When findings conflict, trust order matters
- **Primary Evidence**: Configuration files, system state, direct file observation
- **Logical Analysis**: What should happen based on system architecture and evidence
- **User Direct Evidence**: Screenshots, specific observations, direct questioning
- **Agent/Tool Findings**: Can be confused or incorrect, require validation against primary evidence
- **Red Flags Requiring Agent Validation**:
  - ❌ Agent findings contradict logical evidence or configuration analysis
  - ❌ Agent claims functionality exists without configuration evidence
  - ❌ Agent results seem unexpected or too good to be true
  - ❌ Agent findings make you abandon correct initial assessment
- **Pattern**: Configuration evidence > Logical analysis > User input > Agent claims
- **Critical Rule**: "When agents contradict logic, validate the agents - don't abandon the logic"

🚨 **TERMINAL SESSION PRESERVATION**: ⚠️ MANDATORY - Scripts must NOT exit terminal on errors
- ❌ NEVER use `exit 1` that terminates user's terminal session
- ✅ ALWAYS use graceful error handling: echo error + read prompt + fallback mode
- ✅ Users need control over their terminal session - let them Ctrl+C to go back
- ❌ Only use `exit` for truly unrecoverable situations

🚨 **NO UNVERIFIED SOURCE CITATION**: ⚠️ MANDATORY - Only cite sources you've actually read
- ❌ NEVER present search result URLs as "sources" without reading their content first
- ✅ ALWAYS distinguish between "potential sources found" vs "verified sources read"
- ✅ ONLY cite URLs as evidence after successfully using WebFetch to read their content

🚨 **QUICK QUALITY CHECK** (⚡): For debugging/complex tasks, verify:
- 🔍 Evidence shown? | ✓ Claims match evidence? | ⚠️ Uncertainties marked? | ➡️ Next steps clear?

## 🚨 QUALITY ASSURANCE PROTOCOL

**ZERO TOLERANCE**: Cannot declare "COMPLETE" without following ALL steps

### 📋 Pre-Testing Checklist (⚠️ MANDATORY)
- [ ] **Test Matrix Created**: Document ALL user paths/options before testing begins
- [ ] **Code Scanning Checklist**: For hardcoded value fixes, search ALL related patterns
- [ ] **Red Team Questions**: Prepare adversarial testing approach to break fixes

### 🔍 Testing Evidence Requirements (⚠️ MANDATORY)
- [ ] **Screenshot for EACH test matrix cell** with exact path labels
- [ ] **Evidence documented for EACH ✅ claim** with specific file references
- [ ] **Path Coverage Report**: Visual showing tested vs. untested combinations

### ✅ Completion Validation Gates (⚠️ MANDATORY)
- [ ] **Adversarial Testing Completed**: Actively tried to break the fixes
- [ ] **Testing Debt Documented**: Related patterns verified after bug discovery
- [ ] **All Evidence Screenshots**: Properly labeled and linked with path information

### 🔒 Evidence Standards
**Each Completion Claim Format**: "✅ [Claim] [Evidence: screenshot1.png, screenshot2.png]"
**Path Label Format**: "Screenshot: Custom Campaign → Step 1 → Character Field"
**Test Matrix Example**: Campaign Type (Dragon Knight, Custom) × Input Fields × Navigation

### 🚨 Enforcement Rules
- **RULE 1**: Any "COMPLETE" claim without this evidence is automatically INVALID
- **RULE 2**: Cannot proceed to next milestone without validation gate completion
- **RULE 3**: Missing path coverage must be documented as "testing debt" and addressed
- **RULE 4**: All ✅ symbols require corresponding screenshot evidence or they become ❌

**Purpose**: Prevent testing failures through systematic process adherence, not memory-dependent judgment

## Self-Learning Protocol

🚨 **AUTO-LEARN**: Document corrections immediately when: User corrects | Self-realizing "Oh, I should have..." | Something fails | Pattern repeats

**Process**: Detect → Analyze → Document (CLAUDE.md/learnings.md/lessons.mdc) → Apply → Persist to Memory MCP

**/learn Command**: `/learn [optional: specific learning]` - The unified learning command with Memory MCP integration for persistent knowledge graph storage

## Claude Code Behavior

1. **Directory Context**: Operates in worktree directory shown in environment
2. **Tool Usage**: File ops, bash commands, web tools available
3. **Test Execution**: Use `TESTING=true vpython` from project root
4. **File Paths**: Always absolute paths
5. **Gemini SDK**: `from google import genai` (NOT `google.generativeai`)
6. **Path Conventions**: `roadmap/` = `/roadmap/` from project root | ✅ **USE ~ NOT /home/jleechan**: Always use `~` instead of `/home/jleechan` in paths for portability
7. 🚨 **DATE INTERPRETATION**: Environment shows "Today's date: 2025-08-12" meaning August 12th, 2025
   - Format is YYYY-MM-DD where MM is month number (01=Jan, 02=Feb, 07=July, 08=August, 09=September)
   - **Current date**: August 12, 2025 - Use this for "latest", "recent", "current" research queries
   - **Research context**: When searching for "2024-2025" info, we're in late 2025 looking at recent developments
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
   - ✅ ALWAYS use headless mode for browser automation (no visible browser windows), **except when debugging or developing new automation scripts, where non-headless mode is permitted for visibility**
   - ✅ Fallback to Puppeteer MCP for Chrome-specific or stealth testing when needed

🚨 **INLINE SCREENSHOTS ARE USELESS**: ⚠️ MANDATORY - Screenshot documentation requirements:
   - ❌ NEVER rely on inline screenshots in chat - they count for NOTHING
   - ✅ ONLY use screenshot tools that save actual files to filesystem
   - ✅ **SCREENSHOT LOCATION**: All screenshots must be saved to `docs/` directory for proper organization and accessibility

13. 🚨 **CONTEXT7 MCP PROACTIVE USAGE**: ⚠️ MANDATORY - When encountering API/library issues:
   - ✅ ALWAYS use Context7 MCP for accurate API documentation when facing errors
   - ✅ **Pattern**: Error occurs → Use `mcp__context7__resolve-library-id` → Get docs with `mcp__context7__get-library-docs`

14. 🚨 **GITHUB TOOL PRIORITY**: ⚠️ MANDATORY - Tool hierarchy for GitHub operations:
   - ✅ **PRIMARY**: GitHub MCP tools (`mcp__github-server__*`) for all GitHub operations
   - ✅ **SECONDARY**: `gh` CLI as fallback when MCP fails or unavailable

15. 🚨 **SERENA MCP FILE OPERATIONS PRIORITY**: ⚠️ MANDATORY - Tool hierarchy for semantic file operations:
   - ✅ **PRIMARY**: Serena MCP tools for semantic code analysis and file operations when available
   - ✅ **SECONDARY**: Standard file tools (Read, Edit, MultiEdit) as fallback
   - ✅ **Pattern**: Complex file operations → Use Serena for semantic understanding → Fallback to basic file tools
   - ✅ **Use Cases**: Code analysis, symbol finding, refactoring, project understanding

16. 🚨 **MEMORY ENHANCEMENT PROTOCOL**: ⚠️ MANDATORY for specific commands
- **Enhanced Commands**: `/think`, `/learn`, `/debug`, `/analyze`, `/fix`, `/plan`, `/execute`, `/arch`, `/test`, `/pr`, `/perp`, `/research`
- **High-Quality Memory Standards**: Include exact error messages, file paths with line numbers, code snippets, actionable information, external references
- **Enhanced Entity Types**: `technical_learning`, `implementation_pattern`, `debug_session`, `workflow_insight`, `architecture_decision`
- **Execution Steps**: 1) Extract technical terms 2) Search Memory MCP 3) Log results transparently 4) Natural integration 5) Capture high-quality learnings
- **Transparency**: Show "🔍 Searching memory..." → Report "📚 Found X relevant memories" → Indicate "📚 Enhanced with memory context"

🚨 **SLASH COMMAND EXECUTION UNDERSTANDING**: ⚠️ MANDATORY - How slash commands actually work
- **Command Types**: Two distinct execution patterns exist in the slash command system
  1. **Universal Composition Commands** (e.g., `/copilot`, `/execute`): Actually call other commands through Claude's natural workflow orchestration
  2. **Embedded Implementation Commands** (e.g., `/commentcheck`, `/plan`): Embed functionality directly rather than calling other commands
- **Universal Composition Pattern**: Commands like `/copilot` delegate to `/execute` which then orchestrates other commands intelligently
- **Documentation vs Execution**: Cross-command references can be either documentation OR actual execution - check implementation context
- **Working Example**: `/copilot` → calls `/execute` → Claude naturally orchestrates `/commentfetch`, `/fixpr`, `/commentreply`, `/commentcheck`, `/pushl`
- **Anti-Pattern**: Assuming all cross-command references are documentation-only (like previous `/guidelines` issue)
- **Verification Method**: Test actual command execution to confirm if composition works or needs embedded implementation

🚨 **MISTAKE PREVENTION SYSTEM**: ⚠️ MANDATORY for `/plan` and `/execute` commands
- **Guidelines Integration**: Automatically check `docs/pr-guidelines/{PR}/guidelines.md` (PR-specific) and `docs/pr-guidelines/base-guidelines.md` (general patterns) for comprehensive mistake prevention patterns
- **Anti-Pattern Enforcement**: Reference historical mistakes and apply best practices from documented patterns
- **Tool Selection Hierarchy**: Serena MCP → Read tool → Bash commands (per established guidelines)
- **Quality Gates**: Apply evidence-based development, systematic change management, and resource-efficient operations
- **Pattern Recognition**: Avoid creating unnecessary files, fake implementations, and subprocess security risks
- **Learning Integration**: Capture new mistake patterns and solutions for continuous improvement

17. 🚨 **FILE CREATION PREVENTION**: ⚠️ MANDATORY - Stop unnecessary file proliferation
- ❌ **FORBIDDEN PATTERNS**: Creating `_v2`, `_new`, `_backup`, `_temp` files when existing file can be edited
- ✅ **REQUIRED CHECK**: Before any Write tool usage: "Can I edit an existing file instead?"
- ✅ **GIT IS SAFETY**: Version control provides backup/history - no manual backup files needed

### 🔧 GitHub MCP Setup
**Token**: Set in `claude_mcp.sh` line ~247 via `export GITHUB_TOKEN="<your-token>"`
**Private Repos**: Use direct functions only (no search) | `mcp__github-server__get_pull_request()`
**Restart After Token Change**: Remove & re-add github-server MCP

🚨 **GITHUB API SELF-APPROVAL LIMITATION**: ⚠️ MANDATORY - Cannot approve own PRs via API
- ❌ **NEVER attempt**: `gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews --method POST --field event=APPROVE` on own PRs
- ✅ **ALWAYS use**: General issue comments `gh api repos/owner/repo/issues/{pr_number}/comments --method POST` instead

🚨 **GITHUB THREADING API SPECIFICATION**: ⚠️ MANDATORY - Correct syntax for threaded replies
**CRITICAL DISTINCTION**: Different APIs for different comment types
1. **Review Comments (Line-specific)** ✅ Supports Threading:
   - **API**: `gh api repos/owner/repo/pulls/PR/comments --method POST`
   - **Field**: `--field in_reply_to=PARENT_ID` (NOT in_reply_to_id)
   - **JSON**: `{body: "reply", in_reply_to: PARENT_ID_NUMBER}`
   - **Result**: `#discussion_rXXX` URLs with proper nesting
   - **Verification**: Response includes `"in_reply_to_id": PARENT_ID`
2. **General PR Comments** ❌ No Threading Support:
   - **API**: `gh api repos/owner/repo/issues/PR/comments --method POST` 
   - **Limitation**: `in_reply_to_id` parameter ignored by GitHub
   - **Result**: Always creates standalone comments
   - **URLs**: `#issuecomment-XXX` format (no threading)
**Memory Aid**: Review comments = Threading ✅ | Issue comments = No threading ❌

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

🚨 **ABSOLUTE BRANCH ISOLATION PROTOCOL**: ⚠️ MANDATORY - NEVER LEAVE CURRENT BRANCH
- ❌ **FORBIDDEN**: `git checkout`, `git switch`, or any branch switching commands
- ❌ **FORBIDDEN**: Working on other branches, PRs, or repositories
- ✅ **MANDATORY**: Stay on current branch for ALL work - delegate everything else to agents
- ✅ **DELEGATION RULE**: Any work requiring different branch → `/orch` or orchestration agents
- **MENTAL MODEL**: "Current branch = My workspace, Other branches = Agent territory"

**NO HARDCODING**: ❌ NEVER hardcode task patterns - agents execute EXACT tasks requested

🚨 **ORCHESTRATION TASK COMPLETION**: When using /orch, task completion requires FULL end-to-end verification
- ✅ Agent must complete entire workflow (find issue → fix → commit → push → create PR)
- ✅ Verify PR creation with link before declaring success

## Project Overview

WorldArchitect.AI = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack**: Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

**Key Docs**:
- **AI Assistant Guide**: → `mvp_site/README_FOR_AI.md` (CRITICAL system architecture for AI assistants)
- **📋 MVP Site Architecture**: → `mvp_site/README.md` (comprehensive codebase overview)
- **📋 Code Review & File Responsibilities**: → `mvp_site/CODE_REVIEW_SUMMARY.md` (detailed file-by-file analysis)
- **Browser Test Mode**: → `mvp_site/testing_ui/README_TEST_MODE.md` (How to bypass auth in browser tests)
- Documentation map → `.cursor/rules/documentation_map.md`
- Quick reference → `.cursor/rules/quick_reference.md`
- Progress tracking → `roadmap/templates/progress_tracking_template.md`
- Directory structure → `/directory_structure.md`

## Core Principles

**Work Approach**:
Clarify before acting | User instructions = law | ❌ delete without permission | Leave working code alone |
Focus on primary goal | Propose before implementing | Summarize key takeaways | Externalize all knowledge

**Branch Protocol**: → See "Git Workflow" section

**Response Modes**: Default = structured for complex | Direct for simple | Override: "be brief"

**Rule Management**:
"Add to rules" → CLAUDE.md | Technical lessons → lessons.mdc | General = rules | Specific = lessons

**Development Protocols**: → `.cursor/rules/planning_protocols.md`

**Edit Verification**: `git diff`/`read_file` before proceeding | Additive/surgical edits only

**Testing**: Red-green methodology | Test truth verification | UI = test experience not code | Use ADTs

**Red-Green Protocol** (`/tdd` or `/rg`):
1. Write failing tests FIRST → 2. Confirm fail (red) → 3. Minimal code to pass (green) → 4. Refactor

🚨 **TESTING LEVELS**: Component (individual functions) ≠ Integration (systems together) ≠ System (complete workflows). Test what you claim. Component success ≠ system validation.

## Development Guidelines

### Code Standards
**Principles**: SOLID, DRY | **Templates**: Use existing patterns | **Validation**: `isinstance()` checks
**Constants**: Module-level (>1x) or constants.py (cross-file) | **Imports**: Module-level only, NO inline/try-except
**Path Computation**: ✅ Use `os.path.dirname()`, `os.path.join()`, `pathlib.Path` | ❌ NEVER use `string.replace()` for paths

🚨 **DYNAMIC AGENT ASSIGNMENT**: Replace hardcoded agent mappings with capability-based selection
- ❌ NEVER use patterns like `if "test" in task: return "testing-agent"`
- ✅ Use capability scoring with load balancing

🚨 **API GATEWAY BACKWARD COMPATIBILITY**: API gateways MUST maintain exact contract during architectural changes
- ✅ Maintain identical HTTP status codes, response formats, validation behavior
- ✅ Fix API gateway layer when tests fail after architectural changes
- **Pattern**: Tests validate API contracts, not implementation details

### Feature Compatibility
**Critical**: Audit integration points | Update filters for new formats | Test object/string conversion
**Always Reuse**: Check existing code | Extract patterns to utilities | No duplication
**Organization**: Imports at top (stdlib → third-party → local) | Extract utilities | Separate concerns
**No**: Inline imports, temp comments (TODO/FIXME), hardcoded strings | Use descriptive names

### Gemini SDK
✅ `from google import genai` | ✅ `client = genai.Client(api_key=api_key)`
Models: `gemini-2.5-flash` (default), `gemini-1.5-flash` (test)
🚨 **WARNING**: See "NO UNNECESSARY EXTERNAL APIS" rule before using Gemini

### Development Practices
`tempfile.mkdtemp()` for test files | Verify before assuming | ❌ unsolicited refactoring
**Logging**: ✅ `import logging_util` | ❌ `import logging` | Use project's unified logging

🚨 **FILE EDITING PROTOCOL**: ⚠️ MANDATORY - Prevent unnecessary file proliferation
- ❌ **NEVER create**: `file_v2.sh`, `file_backup.sh`, `file_new.sh` when editing existing file
- ✅ **ALWAYS edit**: Existing files in place using Edit/MultiEdit tools
- ✅ **Git handles safety**: Version control provides backup/rollback, no manual backup files needed
- ✅ **Use branches**: For experimental changes, create git branches not new files
- **Anti-Pattern**: "Let me create a new version..." → Should be "Let me edit the existing file..."

🚨 **PR Review Verification**: Always verify current state before applying review suggestions
- ✅ Check if suggested fix already exists in code | Read actual file content before changes

⚠️ **PR COMMENT PRIORITY**: Address review comments in strict priority order
1. **CRITICAL**: Undefined variables, inline imports, runtime errors
2. **HIGH**: Bare except clauses, security issues
3. **MEDIUM**: Logging violations, format issues
4. **LOW**: Style preferences, optimizations

🚨 **BOT COMMENT FILTERING**: ⚠️ MANDATORY - Ignore specific bot patterns when explicitly overridden
- ❌ **IGNORE**: Bot comments about `--dangerously-skip-permissions` when user explicitly chose to keep it
- ✅ **ACKNOWLEDGE**: Respond but indicate user decision to retain flag

### Testing Protocol

🚨 **ZERO TOLERANCE**: Run ALL tests, fix ALL failures. No "pre-existing issues" excuse. Commands: `./run_tests.sh` | `./run_ui_tests.sh mock`

🚨 **VISUAL VALIDATION**: Verify end-to-end data flow (input → API → DB → UI display), not just API calls.

🚨 **COMPREHENSIVE MOCKING OVER SKIPPING**: ⚠️ RECOMMENDED - Use robust mocking instead of test skips
- ✅ **PREFERRED**: Comprehensive mocking with `autospec=True` for consistent test environments
- ✅ **PATTERN**: Mock dependencies to ensure tests validate functionality regardless of environment
- ✅ **IMPLEMENTATION**: Use pytest fixtures or unittest.mock.patch decorators for proper isolation
- ⚠️ **AVOID**: Skip tests based on dependency availability - prefer making all tests runnable

🚨 **DETERMINISTIC TESTING GUIDANCE**: ⚠️ RECOMMENDED - Ensure consistent test behavior
- ✅ **RECOMMENDED**: Force deterministic behavior at module level before conditional logic
- ✅ **PATTERN**: Create mock classes/objects that simulate missing dependencies
- ✅ **IMPLEMENTATION**: Use `*args, **kwargs` in mock method signatures for compatibility
- ⚠️ **AVOID**: Conditional imports that create different execution paths in local vs CI environments

**Quality**: Files <500 lines, descriptive names. Verify PASS/FAIL detection. Use specific exceptions (ValidationError).

### File & Testing Rules

**File Placement**: No new files in `mvp_site/` without permission. Add tests to existing test files.

**Browser vs HTTP**: `/testui` = Playwright MCP + Mock | `/testuif` = Playwright + Real APIs | `/testhttp` = HTTP requests + Mock | `/testhttpf` = HTTP + Real APIs

**Browser Tests**: Playwright MCP preferred (headless mode). Test URL: `http://localhost:8081?test_mode=true&test_user_id=test-user-123`

**Coverage**: Use `./run_tests.sh --coverage` or `./coverage.sh`. HTML at `/tmp/worldarchitectai/coverage/index.html`

## Git Workflow

**Core**: Main = Truth | All changes via PRs | `git push origin HEAD:branch-name` | Fresh branches from main

🚨 **CRITICAL RULES**:
- No main push: ❌ `git push origin main` | ✅ `git push origin HEAD:feature`
- ALL changes require PR (including docs)
- Never switch branches without request
- Pattern: `git checkout main && git pull && git checkout -b name`

**GitHub API**: Check pagination (30 item default), use `?per_page=100&page=N` for complete results

**Challenge Response**: User evidence = ground truth. Immediate re-verification when user provides specific evidence.

**Debugging**: Side-by-side code comparison → Data flow analysis → Gap ID → Fix

## GitHub Actions Security

🚨 **SHA-PINNING REQUIREMENT**: ⚠️ MANDATORY - All GitHub Actions MUST use SHA-pinned versions for security
- ❌ **FORBIDDEN**: Using mutable tags like `@v4`, `@main`, `@latest` - these can be changed by attackers
- ✅ **REQUIRED**: Use full commit SHA like `@b4ffde65f46336ab88eb53be808477a3936bae11`
- **WHY**: Prevents supply chain attacks where compromised action maintainers inject malicious code
- **EXAMPLE**:
  ```yaml
  # ❌ INSECURE - Tag can be moved to malicious commit
  uses: actions/checkout@v4
  
  # ✅ SECURE - Immutable SHA reference  
  uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
  ```
- **FINDING SHAs**: Check action's releases page, look for commit SHA in release notes
- **COMMENT PATTERN**: Always add `# vX.Y.Z` comment after SHA for human readability
- **VERIFICATION**: Run `gh api repos/{owner}/{action}/commits/{sha}` to verify SHA validity
- **CI FAILURE**: GitHub will reject workflows with deprecated action versions - update to latest SHA
- **Scope**: Applies to ALL workflow files in `.github/workflows/`

## Environment & Scripts

🚨 **CLAUDE CODE HOOKS**: Executable scripts auto-run at specific points. Config: `.claude/settings.json`, Scripts: `.claude/hooks/` (executable). Active hooks: Git Header, Post Commit Sync, Fake Code Detection.

**Python**: Verify venv activated. Run from project root with `TESTING=true vpython`. Use Python for restricted file ops.

**Logs**: Located at `/tmp/worldarchitect.ai/[branch]/[service].log`. Use `tail -f` for monitoring.

**Sync Check**: `scripts/sync_check.sh` detects/pushes unpushed commits automatically.

## Operations Guide

**Data Defense**: Use `dict.get()`, validate structures, implement code safeguards.

**Memory MCP**: Search first → Create if new → Add observations → Build relationships

**TodoWrite**: Required for 3+ steps. Flow: `pending` → `in_progress` → `completed`

**Operations**: MultiEdit max 3-4 edits. Check context % before complex ops. Try alternatives after 2 failures.

### Context Management

🚨 **LIMITS**: 500K tokens (Enterprise) / 200K (Paid). ~4 chars/token. Use `/context` and `/checkpoint` commands.

**Health Levels**: Green (0-30%) continue | Yellow (31-60%) optimize | Orange (61-80%) efficiency | Red (81%+) checkpoint

**Large PRs**: Use Serena MCP semantic navigation first. `find_symbol` > reading full files. Use `limit`/`offset` parameters. Process API responses in batches with `--json` flags.

## Knowledge & Lessons

**Scratchpad**: `roadmap/scratchpad_[branch].md` - Goal | Plan | State | Next

**Files**: CLAUDE.md (primary), lessons.mdc (learnings), rules.mdc (cursor config)

**Core Patterns**: Test before assuming. Docs ≠ code. Trace data flow. Critical instructions first.

**Anti-Patterns**: Don't create new files when editing suffices. No branch confusion. No orchestration hardcoding.

**Debugging**: Extract evidence → Analyze → Verify → Fix. Primary evidence > Secondary > Speculation.

**No Platform Blame**: Test fresh instances with proper config before blaming external platforms.

## Slash Commands

**Types**: Cognitive (`/think`, `/debug`, `/learn`) = semantic | Operational (`/orch`, `/handoff`) = protocol enforcement | Tool (`/execute`, `/test`, `/pr`) = direct execution

🚨 **CRITICAL RULES**:
- Scan "/" → Check `.claude/commands/[command].md` → Execute complete workflow
- Verify filesystem before claiming command doesn't exist  
- `/orch` ALWAYS triggers tmux agents - NEVER execute directly
- `/execute` requires TodoWrite checklist

**Key Commands**: `/execute` (auto-approval), `/plan` (manual approval), `/fake` (detects fake implementations)

## Special Protocols

**PR Comments**: Address ALL sources (inline, general, reviews, copilot). Status: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED

**Data Loss Warnings**: Treat CodeRabbit/Copilot warnings as CRITICAL. Implement validation before conflict resolution.

**Imports**: Module-level only. No inline/try-except. Use `as` for conflicts.

**Browser vs HTTP**: `/testuif` = browser automation | `/testhttp` = HTTP requests. No HTTP simulation for browser tests.

**PR References**: Include full URL - "PR #123: https://github.com/user/repo/pull/123"

**PR Descriptions**: Reflect complete delta vs origin/main using `git diff --stat origin/main...HEAD`. Document all changes, not just recent work.

### PR Labeling

**Auto-labeling** based on git diff vs origin/main:
- **Type**: bug (fix/error keywords), feature (add/new), improvement (optimize/enhance), infrastructure (yml/scripts)
- **Size**: small <100, medium 100-500, large 500-1000, epic >1000 lines
- **Scope**: frontend (JS/HTML/CSS >50%), backend (Python/server >50%), fullstack (mixed)
- **Priority**: critical (security/data loss), high (performance/UX), normal (standard), low (cleanup)

**Commands**: `/pushl` (auto-label), `/pushl --update-description` (refresh), `/pushl --labels-only`

## Project-Specific

**Flask**: SPA route for index.html, hard refresh for CSS/JS, cache-bust in prod
**Python**: venv required, source .bashrc after changes
**AI/LLM**: Detailed prompts crucial, critical instructions first

## Quick Reference

- **Test**: `TESTING=true vpython mvp_site/test_file.py` (from root)
- **All Tests**: `./run_tests.sh` 
- **New Branch**: `./integrate.sh`
- **Deploy**: `./deploy.sh` or `./deploy.sh stable`

## Additional Documentation

**Files**: `.cursor/rules/lessons.mdc` (lessons), `.cursor/rules/rules.mdc` (cursor), `.cursor/rules/examples.md`, `.cursor/rules/validation_commands.md`

## API Timeout Prevention (🚨)

**MANDATORY**: Prevent API timeouts:
- **Edits**: MultiEdit with 3-4 max | Target sections, not whole files
- **Thinking**: 5-6 thoughts max | Concise | No unnecessary branching
- **Responses**: Bullet points | Minimal output | Essential info only
- **Tools**: Batch calls | Smart search (Grep/Glob) | Avoid re-reads
- **Complex tasks**: Split across messages | Monitor server load

## AI-Assisted Development Protocols (🚨)

### Development Velocity Benchmarks
**Claude Code CLI Performance** (based on GitHub stats):
- **Average**: 15.6 PRs/day, ~20K lines changed/day
- **Peak**: 119 commits in single day
- **Parallel Capacity**: 3-5 task agents simultaneously
- **First-time-right**: 85% accuracy with proper specs

### AI Development Planning (⚠️ MANDATORY)
**All development timelines must use data-driven estimation**:
- **Human estimate**: 3 weeks → **AI estimate**: 2-3 days
- **Calculation Steps**:
  1. Estimate lines of code (with 20% padding)
  2. Apply velocity: 820 lines/hour average (excludes debugging, refactoring, and code review time)
  3. Add PR overhead: 5-12 min per PR
  4. Apply parallelism: 30-45% reduction
     - Use **30%** if tasks are highly independent and agents are experienced
     - Use **45%** if tasks are interdependent, agents are less experienced, or integration is complex
  5. Add integration buffer: 10-30%
- **Realistic multiplier**: 10-15x faster (not 20x)
- **Avoid**: Anchoring bias from initial suggestions

### Task Decomposition for AI Agents
**Pattern for maximum efficiency**:
```
1. Break into independent, parallel tasks
2. Each agent gets clear deliverable (1 PR)
3. No inter-agent dependencies within phase
4. Integration phase at end of each sprint
```

### AI Sprint Structure (1 Hour Sprint)
**Phase 1 (15 min)**: Core functionality - 3-5 parallel agents
**Phase 2 (15 min)**: Secondary features - 3-5 parallel agents
**Phase 3 (15 min)**: Polish & testing - 2-3 parallel agents
**Phase 4 (15 min)**: Integration & deploy - 1 agent

### Success Patterns from Stats
- **Micro-PR workflow**: Each agent creates focused PR
- **Continuous integration**: Merge every 15 minutes
- **Test-driven**: Tests in parallel with features
- **Architecture-first**: Design before parallel execution

### Anti-Patterns to Avoid
- ❌ Sequential task chains (wastes AI parallelism)
- ❌ Human-scale estimates (still too conservative)
- ❌ Single large PR (harder to review/merge)
- ❌ Waiting for perfection (iterate fast)
- ❌ **Anchoring to user suggestions** (calculate independently)
- ❌ **Over-optimistic estimates** (under 1 hour for major features)
- ❌ **Ignoring PR overhead** (5-12 min per PR adds up)
- ❌ **Assuming perfect parallelism** (45% max benefit)

## Context Management & Optimization (🚨 MANDATORY)

🚨 **PROACTIVE CONTEXT MONITORING**: ⚠️ MANDATORY - Prevent context exhaustion
- **Claude Sonnet 4 Limits**: 500K tokens (Enterprise) / 200K tokens (Paid Plans)
- **Token Estimation**: ~4 characters per token, ~75 words per 100 tokens
- **Context Health Monitoring**: Use `/context` command for real-time estimation
- **Strategic Checkpoints**: Use `/checkpoint` before complex operations

🚨 **CONTEXT CONSUMPTION PATTERNS**: High-impact operations to monitor
- **Context Killers**: Large file reads without limits (1000+ tokens each)
- **Medium Impact**: Standard operations with filtering (200-1000 tokens)
- **Low Impact**: Serena MCP operations (50-200 tokens)
- **Optimization Rule**: Serena MCP first, targeted operations always

**Context Health Levels**:
- **Green (0-30%)**: Continue with current approach
- **Yellow (31-60%)**: Apply optimization strategies  
- **Orange (61-80%)**: Implement efficiency measures
- **Red (81%+)**: Strategic checkpoint required

**Sprint Structure** (1 hour): Phase 1 core (15min), Phase 2 features (15min), Phase 3 polish (15min), Phase 4 integration (15min)

**Success**: Micro-PR workflow, continuous integration, test-driven, architecture-first

**Anti-Patterns**: Sequential chains, human-scale estimates, single large PRs, anchoring bias, over-optimism
