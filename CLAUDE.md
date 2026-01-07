# 📚 Reference Export - Adaptation Guide

**Note**: This is a reference export from a working Claude Code project. You may need to personally debug some configurations, but Claude Code can easily adjust for your specific needs.

These configurations may include:
- Project-specific paths and settings that need updating for your environment
- Setup assumptions and dependencies specific to the original project
- References to particular GitHub repositories and project structures

Feel free to use these as a starting point - Claude Code excels at helping you adapt and customize them for your specific workflow.

---

EOF < /dev/null
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

## 🚨 MANDATORY QUALITY ASSURANCE PROTOCOL

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
- **AI Assistant Guide**: → `$PROJECT_ROOT/README_FOR_AI.md` (CRITICAL system architecture for AI assistants)
- **📋 MVP Site Architecture**: → `$PROJECT_ROOT/README.md` (comprehensive codebase overview)
- **📋 Code Review & File Responsibilities**: → `$PROJECT_ROOT/CODE_REVIEW_SUMMARY.md` (detailed file-by-file analysis)
- **Browser Test Mode**: → `$PROJECT_ROOT/testing_ui/README_TEST_MODE.md` (How to bypass auth in browser tests)
- Documentation map → `.cursor/rules/documentation_map.md`
- Quick reference → `.cursor/rules/quick_reference.md`
- Progress tracking → `roadmap/templates/progress_tracking_template.md`
- Directory structure → `/directory_structure.md`

## Core Principles & Interaction

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

🚨 **Testing Standards**: → See "Testing Protocol" section for complete rules

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

### Website Testing & Deployment Expectations (🚨 CRITICAL)
🚨 **BRANCH ≠ WEBSITE**: ❌ NEVER assume branch changes are visible on websites without deployment
- ✅ Check PR description first - many changes are tooling/CI/backend only
- ✅ Feature branches need local server OR staging deployment for UI changes

### Quality Standards
**Files**: Descriptive names, <500 lines | **Tests**: Natural state, visual validation, dynamic discovery
**Validation**: Verify PASS/FAIL detection | Parse output, don't trust exit codes | Stop on contradictions

### 🚨 Testing Protocol
**Zero Tolerance**: Run ALL tests before completion | Fix ALL failures | No "pre-existing issues" excuse
**Commands**: `./run_tests.sh` | `./run_ui_tests.sh mock` | `gh pr view`
**Protocol**: STOP → FIX → VERIFY → EVIDENCE → Complete

🚨 **TEST WITH REAL CONFLICTS**: ⚠️ MANDATORY
- ✅ ALWAYS test merge conflict detection with PRs that actually have conflicts
- ✅ Use `gh pr view [PR] --json mergeable` to verify real conflict state before testing

**Test Assertions**: ⚠️ MANDATORY - Must match actual validation behavior exactly

**Exception Specificity**: ✅ Use specific exception types in tests (ValidationError, not Exception)

**Rules**: ✅ Run before task completion | ❌ NEVER skip without permission | ✅ Only use ✅ after real results

### Safety & Security
❌ Global `document.addEventListener('click')` without approval | Test workflows after modifications
Document blast radius | Backups → `tmp/` | ❌ commit if "DO NOT SUBMIT" | Analysis + execution required

### File Placement Rules (🚨 HARD RULE)
🚨 **NEVER add new files directly to $PROJECT_ROOT/** without explicit user permission
- ❌ NEVER create test files, documentation, or scripts directly in $PROJECT_ROOT/
- ✅ If unsure, add content to roadmap/scratchpad_[branch].md instead

🚨 **Test File Policy**: Add to existing files, NEVER create new test files
- ⚠️ MANDATORY: Always add tests to existing test files that match the functionality

🚨 **Code Review**: Check README.md and CODE_REVIEW_SUMMARY.md before $PROJECT_ROOT/ changes

### Browser vs HTTP Testing (🚨 HARD RULE)
**CRITICAL DISTINCTION**: Never confuse browser automation with HTTP simulation
- 🚨 **testing_ui/**: ONLY real browser automation using **Playwright MCP** (default) or Puppeteer MCP
- 🚨 **testing_http/**: ONLY HTTP requests using `requests` library
- ⚠️ **/testui and /testuif**: MUST use real browser automation (Playwright MCP preferred)
- ⚠️ **/testhttp and /testhttpf**: MUST use HTTP requests | NO browser automation
- **Red Flag**: If writing "browser tests" with `requests.get()`, STOP immediately

**Command Structure** (Claude Code CLI defaults to Playwright MCP):
- `/testui` = Browser (Playwright MCP) + Mock APIs
- `/testuif` = Browser (Playwright MCP) + REAL APIs (costs $)
- `/testhttp` = HTTP + Mock APIs
- `/testhttpf` = HTTP + REAL APIs (costs $)
- `/tester` = End-to-end tests with REAL APIs (user decides cost)

### Real API Testing Protocol (🚨 MANDATORY)
**NEVER push back or suggest alternatives when user requests real API testing**:
- ✅ User decides if real API costs are acceptable - respect their choice
- ✅ `/tester`, `/testuif`, `/testhttpf` commands are valid user requests
- **User autonomy**: User controls their API usage and testing approach

### Browser Test Execution Protocol (🚨 MANDATORY)
🚨 **PREFERRED**: Playwright MCP in Claude Code CLI - Accessibility-tree based, AI-optimized, cross-browser
🚨 **SECONDARY**: Puppeteer MCP for Chrome-specific or stealth testing scenarios
🚨 **HEADLESS MODE**: ⚠️ ALWAYS use headless mode for browser automation - no visible browser windows
**Commands**: `./run_ui_tests.sh mock --playwright` (default) | `./run_ui_tests.sh mock --puppeteer` (secondary)
**Test Mode URL**: `http://localhost:8081?test_mode=true&test_user_id=test-user-123` - Required for auth bypass!

### Coverage Analysis Protocol (⚠️)
**MANDATORY**: When analyzing test coverage:
1. **ALWAYS use**: `./run_tests.sh --coverage` or `./coverage.sh` (HTML default)
2. **NEVER use**: Manual `coverage run` commands on individual test files
3. **Verify full test suite**: Ensure all 94+ test files are included in coverage analysis
4. **HTML location**: `/tmp/worldarchitectai/coverage/index.html`

## Git Workflow

**Core Rules**: Main = Truth | All changes via PRs | Verify before push | Set upstream tracking
**Commands**: `git push origin HEAD:branch-name` | `gh pr create` + test results | `./integrate.sh`
**Progress**: Scratchpad + JSON (`roadmap/scratchpad_[branch].md` + `tmp/milestone_*.json`)

🚨 **No Main Push**: ✅ `git push origin HEAD:feature` | ❌ `git push origin main`
- **ALL changes require PR**: Including roadmap files, documentation, everything
- **Fresh branches from main**: Always create new branch from latest main for new work
- **Pattern**: `git checkout main && git pull && git checkout -b descriptive-name`

🚨 **PR Context Management**: Verify before creating PRs - Check git status | Ask which PR if ambiguous

🚨 **Branch Protection**: ❌ NEVER switch without explicit request | ❌ NEVER use dev[timestamp] for development
✅ Create descriptive branches | Verify context before changes | Ask if ambiguous

🚨 **Conflict Resolution**: Analyze both versions | Assess critical files | Test resolution | Document decisions
**Critical Files**: CSS, main.py, configs, schemas | **Process**: `./resolve_conflicts.sh`

🚨 **GIT ANALYSIS CONTEXT CHECKPOINT**: ⚠️ MANDATORY protocol before any git comparison
- ✅ **Steps**: 1) Identify current branch 2) Determine branch type 3) Select appropriate remote comparison 4) Execute
- **Mapping**: sync-main-* → `origin/main` | Feature branches → `origin/branch-name` | main → `origin/main`

🚨 **COMMAND FAILURE TRANSPARENCY** (⚠️ MANDATORY): When user commands fail unexpectedly:
- ✅ Immediately explain what failed and why | Show system messages/errors received
- ✅ Explain resolution approach | Ask preference for alternatives (merge vs rebase, etc.)
- **Pattern**: Command fails > Explain > Show options > Get preference > Execute

**Commit Format**: → `.cursor/rules/examples.md`

🚨 **GITHUB API PAGINATION PROTOCOL**: ⚠️ MANDATORY - Before ANY GitHub API analysis:
- ✅ **Check total count first**: Use `gh pr view [PR] --json changed_files` to get file count before analysis
- ✅ **Verify pagination**: GitHub API defaults to 30 items per page - always check if more pages exist
- ✅ **Use pagination parameters**: Add `?per_page=100&page=N` for complete results when file count > 30
- ❌ **NEVER assume**: API returns complete results without verifying pagination and total counts

🚨 **CHALLENGE RESPONSE PROTOCOL**: ⚠️ MANDATORY - When user provides specific evidence:
- ✅ **Immediate re-verification**: Treat user evidence as debugging signal, not personal attack
- ✅ **Methodology review**: Re-check approach when user mentions details not in your analysis
- ❌ **NEVER defend**: Wrong analysis - acknowledge error and re-verify immediately

## Environment, Tooling & Scripts

1. **Python venv**: Verify activated before running Python/tests | If missing/corrupted → `VENV_SETUP.md`
2. **Robust Scripts**: Make idempotent, work from any subdirectory
3. **Python Execution**: ✅ Run from project root | ❌ cd into subdirs
4. **vpython Tests**: ⚠️ "run all tests" → `./run_tests.sh` | ⚠️ Test fails → fix immediately or ask user
   - ✅ `TESTING=true vpython $PROJECT_ROOT/test_file.py` (from root)
5. 🚨 **Test Compliance**: → See "Testing Protocol" section
6. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted
7. **Web Scraping**: Use full-content tools (curl) not search snippets
8. **Log Files Location**:
   - ✅ **Server logs are in `/tmp/your-project.com/`** with branch isolation and service-specific files
   - ✅ **Branch-specific structure**: `/tmp/your-project.com/[branch-name]/`
   - ✅ **Service logs**: `/tmp/your-project.com/[branch]/[service-name].log`
   - ✅ **Log commands**: `tail -f /tmp/your-project.com/[branch]/[service].log` for real-time monitoring
   - ✅ **Search logs**: `grep -i "pattern" /tmp/your-project.com/[branch]/[service].log`
   - ✅ **Find current log**: `git branch --show-current` then check corresponding log file

9. 🚨 **SMART SYNC CHECK PROTOCOL**: ⚠️ MANDATORY - Prevent local changes not pushed to remote
   - **Purpose**: Automatically detect and push unpushed commits after tools create changes
   - **Script Location**: `<project-root>/scripts/sync_check.sh` (e.g. `$(git rev-parse --show-toplevel)/scripts/sync_check.sh`)
   - **Integration**: Tools that create commits MUST call sync check at completion
   - **Usage**: `$(git rev-parse --show-toplevel)/scripts/sync_check.sh` or source common utilities
   - **Tools Required**: `/fixpr`, `/commentreply`, `/integrate`, any commit-creating tools
   - **Behavior**: Detects unpushed commits → Shows commits → Auto-pushes → Confirms success
   - **Safety**: Only pushes when unpushed commits detected, handles edge cases gracefully
   - **Error Handling**: Graceful fallback for no upstream, detached HEAD, push failures
   - **Benefits**: Eliminates "forgot to push" syndrome while maintaining workflow transparency

10. 🚨 **GITHUB CLI (gh) INSTALLATION**: ⚠️ MANDATORY for GitHub operations
   - **Primary Tool**: GitHub MCP tools (`mcp__github-server__*`) for all GitHub operations
   - **Fallback**: `gh` CLI when MCP fails or unavailable
   - **Installation Method** (Container/Restricted Environments):
     ```bash
     # Download and extract gh CLI binary to /tmp
     curl -sL https://github.com/cli/cli/releases/download/v2.40.1/gh_2.40.1_linux_amd64.tar.gz | tar -xz -C /tmp

     # Verify installation
     /tmp/gh_2.40.1_linux_amd64/bin/gh --version

     # Authenticate using existing GitHub token (ensure GITHUB_TOKEN is set)
     # The gh CLI automatically uses GITHUB_TOKEN environment variable
     # Example: export GITHUB_TOKEN="ghp_xxx"  # or rely on existing environment variable
     printf '%s\n' "$GITHUB_TOKEN" | /tmp/gh_2.40.1_linux_amd64/bin/gh auth login --with-token

     # Verify authentication status
     /tmp/gh_2.40.1_linux_amd64/bin/gh auth status

     # Set up alias for convenience
     export GH_CLI="/tmp/gh_2.40.1_linux_amd64/bin/gh"

     # Use in commands
     $GH_CLI pr create --title "Feature" --body "Description"
     $GH_CLI issue create --title "Bug" --body "Details"
     ```
   - **Why This Works**: GitHub releases not blocked by container security (unlike cloud provider binaries)
   - **Benefits**: Direct binary extraction to /tmp avoids permission issues, no package manager required
   - **Authentication**: Uses GITHUB_TOKEN environment variable via `gh auth login --with-token`
   - **Note**: Container blocks binary downloads from cloud provider domains for multi-tenant security, but trusts package registries (npm, PyPI) and GitHub releases

**Test Commands**: → `.cursor/rules/validation_commands.md`

## Data Integrity & AI Management

1. **Data Defense**: Assume incomplete/malformed | Use `dict.get()` | Validate structures
2. **Critical Logic**: Implement safeguards in code, not just prompts
3. **Single Truth**: One clear way per task | Remove conflicting rules

## Operations Guide

### Memory MCP Usage
**Create**: `mcp__memory-server__create_entities([{name, entityType, observations}])`
**Search**: `mcp__memory-server__search_nodes("query")` → Find existing before creating
**Pattern**: Search first → Create if new → Add observations to existing → Build relationships

### Task Agent Patterns
**⚠️ Token Cost**: Each agent loads ~50k+ tokens. See `.claude/commands/parallel-vs-subagents.md` for alternatives.
**When to Spawn**: Complex workflows | Different directories | Long operations (>5 min)
**When NOT to Spawn**: Simple searches | Independent file ops | Data gathering (<30s each)
**Pattern**: `Task(description="Research X", prompt="Detailed instructions...")`

### TodoWrite Protocol
**When Required**: Tasks with 3+ steps | Complex implementations | /execute commands
**Status Flow**: `pending` → `in_progress` → `completed`
**Update Pattern**: Mark current task `in_progress`, complete it, then move to next

### Common Operations
**Multi-file Edits**: Use MultiEdit with 3-4 edits max per call to avoid timeouts
**Context Management**: Check remaining % before complex operations | Split large tasks
**Tool Recovery**: After 2 failures → Try alternative tool → Fetch from main if corrupted

### Context Optimization for Large PRs (🚨 MANDATORY)
**When working on PRs with 50+ changed files**, follow these patterns to prevent context exhaustion:

**1. Use Serena MCP Semantic Navigation** (PRIMARY):
- ✅ `find_symbol` for specific functions/classes instead of reading entire files
- ✅ `get_symbols_overview` to understand file structure before diving in
- ✅ `search_for_pattern` with targeted regex instead of broad file reads
- ❌ NEVER read entire files when you only need specific sections

**2. Smart File Reading Patterns**:
- ✅ Use `limit` and `offset` parameters for large files
- ✅ Target specific line ranges based on comment references
- ✅ Use Grep with `-A`/`-B` context flags for targeted reads
- ❌ AVOID reading files multiple times in same session

**3. API Response Management**:
- ✅ Use `--json` flags with specific fields (e.g., `--json id,path,line`)
- ✅ Process comments in batches with focused queries
- ✅ Use `jq` or grep to filter API responses before processing
- ❌ AVOID fetching full comment bodies when only IDs needed

**4. PR Analysis Workflow**:
```bash
# Step 1: Get high-level PR structure
gh pr view [PR] --json changedFiles --jq '.changedFiles | length'

# Step 2: Use Serena for targeted symbol analysis
mcp__serena__find_symbol --name_path "functionName" --relative_path "specific/file.py"

# Step 3: Process comments in focused batches
gh api repos/{owner}/{repo}/pulls/{pr}/comments --paginate --jq '.[].id'
```

**Anti-Pattern Example** (AVOID):
```bash
# ❌ Reading 50+ files completely
for file in $(gh pr view --json files); do
  Read --file_path "$file"  # Context killer!
done
```

**Best Practice Example**:
```bash
# ✅ Targeted semantic navigation
mcp__serena__search_for_pattern --pattern "console\\.error" --restrict_search_to_code_files true
mcp__serena__find_symbol --name_path "ClassName/methodName" --include_body true
```

## Knowledge Management

### Scratchpad Protocol (⚠️)
`roadmap/scratchpad_[branch].md`: Goal | Plan | State | Next | Context | Branch info

### File Organization
- **CLAUDE.md**: Primary protocol
- **lessons.mdc**: Technical learnings from corrections
- **project.md**: Repository-specific knowledge base
- **rules.mdc**: Cursor configuration

### Process Improvement
- **5 Whys**: Root cause → lessons.mdc
- **Sync Cursor**: Copy CLAUDE.md to Cursor settings after changes
- **Proactive Docs**: Update rules/lessons after debugging without prompting

## Critical Lessons (Compressed)

### Core Patterns
**Trust But Verify**: Test before assuming | Docs ≠ code | Trace data flow | Critical instructions first

### 🚨 Anti-Patterns
**Silent Breaking Changes**: Update all str() usage when changing objects | Test backward compatibility
**Unnecessary File Creation**: ❌ NEVER create new files when editing existing ones suffices
**Branch Confusion**: Verify context before changes | Check PR destination
**Orchestration Hardcoding**: ❌ NEVER pattern-match tasks to agent types | ✅ Execute exact requested tasks

### Debugging Protocol (🚨 MANDATORY)
**Process**: Extract evidence → Analyze → Verify → Fix | Trace: Backend → API → Frontend
**Evidence**: Primary (code/errors) > Secondary (docs) > General (patterns) > Speculation
**Details**: → `.cursor/rules/debugging_guide.md`

🚨 **NO PLATFORM BLAME WITHOUT FRESH INSTANCES**: ⚠️ MANDATORY - Before blaming external platforms
- ❌ NEVER blame "platform instability" without systematic testing with fresh instances
- ✅ ALWAYS test fresh instance creation with proper configuration before platform blame
- ✅ REQUIRED: Fresh instance + proper onstart scripts + normal timing expectations
- **Pattern**: Fresh instance test → Platform-specific requirements → Normal behavior expected

### Critical Rules
**Data Corruption**: Systemic issue - search all patterns | **Temp Fixes**: Flag + fix NOW
**Task Complete**: Solve + Update docs + Memory + Audit | **No blind execution**
**Details**: → `.cursor/rules/lessons.mdc`

## Slash Commands

**Full Documentation**: → `.claude/commands/` | Use `/list` for available commands

### Command Classification (Dual Architecture)
**🧠 Cognitive Commands** (Semantic Composition): `/think`, `/arch`, `/debug`, `/learn`, `/analyze`, `/fix`, `/perp`, `/research`
**⚙️ Operational Commands** (Protocol Enforcement): `/headless`, `/handoff`, `/orchestrate` - Modify execution environment
**🔧 Tool Commands** (Direct Execution): `/execute`, `/test`, `/pr` - Direct task execution

### Critical Enforcement
🚨 **SLASH COMMAND PROTOCOL RECOGNITION**: ⚠️ MANDATORY - Before processing ANY slash command:
- ✅ **Recognition Phase**: Scan "/" → Identify command type → Look up workflow in `.claude/commands/[command].md`
- ✅ **Execution Phase**: Follow COMPLETE documented workflow → No partial execution allowed
- ❌ NEVER treat slash commands as content suggestions - they are execution mandates

🚨 **EXECUTE CIRCUIT BREAKER**: `/e` or `/execute` → TodoWrite checklist MANDATORY
- Context % | Complexity | Subagents? | Plan presented | Auto-approval applied

🚨 **OPERATIONAL COMMAND ENFORCEMENT**: `/headless`, `/handoff`, `/orchestrate`, `/orch`
- ✅ ALWAYS trigger tmux orchestration protocol before task execution
- ❌ NEVER execute /orch or /orchestrate tasks yourself - ONLY monitor tmux agents
- ❌ NEVER use Task tool for orchestration - use tmux system only

**Key Commands**: `/execute` (auto-approval built-in) | `/plan` (requires manual approval) | `/fake` (code quality audit)

#### `/fake`
**Purpose**: Comprehensive fake code detection | **Composition**: `/arch /thinku /devilsadvocate /diligent`
**Detection**: Identifies fake implementations, demo code, placeholder comments, duplicate protocols

## Special Protocols

### GitHub PR Comment Response Protocol (⚠️)
**MANDATORY**: Systematically address ALL PR comments from all sources
**Comment Sources**: Inline (`gh api`) | General (`gh pr view`) | Reviews | Copilot (include "suppressed")
**Response Status**: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED

🚨 **DATA LOSS WARNINGS**: Treat all data loss warnings from CodeRabbit/Copilot as CRITICAL
- ❌ NEVER dismiss data integrity concerns as "intentional design"
- ✅ ALWAYS implement proper validation before conflict resolution

### Import Protocol (🚨 CRITICAL)
**Zero Tolerance**: Module-level only | No inline/try-except/conditionals | Use `as` for conflicts

### API Error Prevention (🚨)
❌ Print code/file content | ✅ Use file_path:line_number | Keep responses concise

### Browser Testing vs HTTP Testing (🚨)
**HARD RULE**: NO HTTP simulation for browser tests!
- `/testuif` = Real browser automation (Puppeteer MCP/Playwright) | `/testi` = HTTP requests OK
- Auth bypass: Use test mode URL params, NOT HTTP simulation

### PR References (⚠️)
**MANDATORY**: Include full GitHub URL - Format: "PR #123: https://github.com/jleechan2015/your-project.com/pull/123"

### PR Description Protocol (⚠️ MANDATORY)
**PR descriptions must reflect complete delta vs origin/main, not just recent work**:
- ✅ Use `git diff --stat origin/main...HEAD` to get comprehensive change summary
- ✅ Analyze actual file changes, additions, deletions vs main branch
- ✅ Document all new features, systems, and architectural changes
- ❌ NEVER describe only latest commits or recent work

## Project-Specific

### Flask: SPA route for index.html | Hard refresh for CSS/JS | Cache-bust in prod
### Python: venv required | Source .bashrc after changes | May need python3-venv
### AI/LLM: Detailed prompts crucial | Critical instructions first | Long prompts = fatigue
### Workflow: Simple-first | Tool fail = try alternative | Main branch = recovery source

## Quick Reference

- **Test**: `TESTING=true vpython $PROJECT_ROOT/test_file.py` (from root)
- **Integration**: `TESTING=true python3 $PROJECT_ROOT/test_integration/test_integration.py`
- **New Branch**: `./integrate.sh`
- **All Tests**: `./run_tests.sh`
- **Deploy**: `./deploy.sh` or `./deploy.sh stable`

## Additional Documentation

- **Technical Lessons**: → `.cursor/rules/lessons.mdc`
- **Cursor Config**: → `.cursor/rules/rules.mdc`
- **Examples**: → `.cursor/rules/examples.md`
- **Commands**: → `.cursor/rules/validation_commands.md`

### Archive Process
Quarterly/2500 lines/new year → `lessons_archive_YYYY.mdc` | Keep critical patterns | Reference archives

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
