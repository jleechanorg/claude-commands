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

🚨 **COPILOT COMMAND AUTONOMOUS OPERATION**: ⚠️ MANDATORY
- ✅ `/copilot` commands operate autonomously without user approval prompts
- ✅ ALWAYS proceed with full analysis regardless of conflicts/issues detected  
- ✅ Claude should automatically apply fixes and resolve issues without asking
- ✅ Continue workflow through conflicts, CI failures, or other blockers
- ❌ NEVER stop workflow for user confirmation during `/copilot` execution
- ❌ No "proceed anyway?" or "continue with analysis?" prompts
- **Purpose**: `/copilot` is designed for autonomous PR analysis and fixing

## Legend
🚨 = CRITICAL | ⚠️ = MANDATORY | ✅ = Always/Do | ❌ = Never/Don't | → = See reference | PR = Pull Request

## File Organization
- **CLAUDE.md** (this file): Primary operating protocol
- **.cursor/rules/rules.mdc**: Cursor-specific configuration
- **.cursor/rules/lessons.mdc**: Technical lessons and incident analysis
- **.cursor/rules/examples.md**: Detailed examples and patterns
- **.cursor/rules/validation_commands.md**: Common command reference

## Meta-Rules

🚨 **PRE-ACTION CHECKPOINT**: Before ANY action, ask:
   1. "Does this violate any rules in CLAUDE.md?"
   2. "Should I check my constraints first?"

🚨 **DUAL COMPOSITION ARCHITECTURE**: Command processing uses two different mechanisms
   - **Cognitive Commands** (/think, /arch, /debug): Use Universal Composition (natural semantic understanding)
   - **Operational Commands** (/headless, /handoff, /orchestrate): Use Protocol Enforcement (mandatory workflow execution)
   - ✅ **Command Recognition**: Scan for "/" prefixes and classify command type BEFORE processing
   - ✅ **Protocol Enforcement**: Operational commands trigger required workflows automatically
   - ✅ **Composition Integration**: Both systems work together (/think /headless = thinking + headless environment)
   - ❌ NEVER process operational commands as regular tasks without workflow setup
   - **Pattern**: Cognitive = semantic composition, Operational = protocol enforcement

🚨 **NO FALSE ✅**: Only use ✅ for 100% complete/working. Use ❌ ⚠️ 🔄 or text for partial.

🚨 **NO POSITIVITY**: Be extremely self-critical. No celebration unless 100% working.

🚨 **NO PREMATURE VICTORY DECLARATION**: Task completion requires FULL verification
- ❌ NEVER declare success based on intermediate steps (file edits, partial work)
- ❌ NEVER say "successfully completed" without verifiable evidence
- ✅ ONLY declare success when ALL steps verified complete
- ✅ For agent tasks: Requires PR created + pushed + link verified
- ✅ For direct tasks: Requires changes committed + pushed + tested
- 🔍 Evidence: Agent modified schedule_branch_work.sh but no PR = TASK INCOMPLETE
- ⚠️ File changes in isolated workspaces are NOT task completion

🚨 **NO EXCUSES FOR TEST FAILURES**: When asked to fix tests, FIX THEM ALL
   - ❌ NEVER say "pre-existing issues" or "unrelated to our changes"
   - ❌ NEVER settle for partial fixes (97/99 is NOT acceptable)
   - ❌ NEVER blame test expectations - fix the code to meet them
   - ✅ ALWAYS fix ALL failing tests to 100% pass rate
   - ✅ ALWAYS take ownership of test failures, especially in new code

🚨 **NO ASSUMPTIONS ABOUT RUNNING COMMANDS**: 
   - ❌ NEVER explain what a command "will do" when it's already running
   - ❌ NEVER make assumptions about command execution or results  
   - ✅ ALWAYS wait for actual command output and results
   - ✅ ALWAYS trust command execution and observe real behavior
   - **Pattern**: User says "X is running..." → Wait for actual results, don't speculate

🚨 **TRUST USER CAPABILITY**: Focus on execution accuracy over complexity concerns
   - ✅ Provide clear, actionable guidance for complex commands
   - ✅ Focus on areas where protocol execution may be challenging
   - ✅ Be honest about personal limitations and areas for improvement
   - ✅ Trust user's ability to handle complexity; focus on improving execution
   - ❌ Avoid generic advice about "command overload" or "cognitive load"
   - ❌ Avoid patronizing about user interface complexity or learning curves

🚨 **NO FAKE IMPLEMENTATIONS**: ⚠️ MANDATORY

**CRITICAL ANTI-PATTERN**: Always audit existing functionality before implementing new code

- ❌ NEVER create files with "# Note: In the real implementation" comments
- ❌ NEVER write placeholder code that doesn't actually work  
- ❌ NEVER create demonstration files instead of working implementations
- ❌ NEVER create Python intelligence files when .md files handle the logic
- ❌ NEVER duplicate systematic protocols that already exist in other .md files
- ❌ NEVER reimplement existing command functionality (use orchestration instead)
- ✅ ALWAYS audit existing commands and .md files before writing new implementations
- ✅ ALWAYS build real, functional code that works immediately
- ✅ ALWAYS enhance existing systems rather than creating fake parallel ones
- ✅ ALWAYS check if functionality exists: Read existing commands, Grep for patterns
- **Pattern**: Real implementation > No implementation > Fake implementation
- **Evidence**: PR #820 - 563+ lines of fake code removed (fixpr.py, commentreply.py, copilot.md duplication)
- **Evidence**: orchestrate_enhanced.py with placeholder comments frustrated user
- **Rule**: If you can't implement it properly, don't create the file at all

🚨 **ORCHESTRATION OVER DUPLICATION**: ⚠️ MANDATORY  
- **Principle**: Orchestrators delegate to existing commands, never reimplement their functionality
- ✅ Pattern: New commands should be orchestrators, not implementers
- ✅ Use existing /commentreply, /pushl, /fixpr rather than duplicating their logic
- ✅ Add command summary at top of orchestrator .md files to prevent confusion
- ❌ NEVER copy systematic protocols from other .md files into new commands
- ❌ NEVER duplicate GitHub API commands that already exist in other commands
- **Evidence**: PR #812 (https://github.com/WorldArchitectAI/repo/pull/812) - 120 lines of duplicate systematic protocol removed from copilot.md
- **Architecture**: copilot = orchestrator, not implementer

🚨 **NO OVER-ENGINEERING**: Prevent building parallel inferior systems vs enhancing existing ones
   - ✅ ALWAYS ask "Can the LLM handle this naturally?" before building parsers/analytics systems
   - ✅ ALWAYS try enhancing existing systems before building parallel new ones  
   - ✅ ALWAYS prioritize user workflow integration over technical sophistication
   - ❌ NEVER build parallel command execution systems - enhance Claude Code CLI instead
   - ❌ NEVER build complex parsing when LLM can understand intent naturally
   - ❌ NEVER add analytics/tracking beyond core functionality needs
   - **Pattern**: Trust LLM capabilities, enhance existing systems, prioritize immediate user value
   - **Evidence**: Command composition over-engineering (PR #737) - a parallel command execution system was built instead of enhancing the existing Claude Code CLI. This led to unnecessary complexity, duplication of functionality, and reduced maintainability.
   - **Evidence**: Orchestration parallel development (PR #790) - created .claude/commands/orchestrate.py instead of enhancing existing orchestration/ directory with Redis infrastructure. Fixed by migrating LLM features TO the mature system and deleting parallel implementation.
   - **Root Causes**: LLM capability underestimation, perfectionist engineering, integration avoidance, demo-driven development, insufficient analysis of existing infrastructure

🚨 **NO FALSE PROMISES**: Be honest about capabilities | Conservative language | Deliver or don't promise

🚨 **NO UNNECESSARY EXTERNAL APIS**: Before adding ANY external API integration:
   - ✅ FIRST ask "Can Claude solve this directly without external APIs?"
   - ✅ ALWAYS try direct implementation before adding dependencies
   - ✅ TEST the direct solution - if it works, STOP there
   - ❌ NEVER default to Gemini API just because it exists in codebase
   - ❌ NEVER add external LLM calls when Claude can generate responses directly
   - **Pattern**: Direct solution → Justify external need → Only then integrate
   - **Anti-pattern**: See AI task → Immediately reach for Gemini API
   - **Evidence**: GitHub comment fiasco (PR #796) - built Gemini integration that degraded to useless generic templates when Claude could have generated responses directly

🚨 **GEMINI API JUSTIFICATION REQUIRED**: Gemini should ONLY be used when:
   - ✅ The task requires capabilities Claude doesn't have (e.g., image generation)
   - ✅ The system needs to work autonomously without Claude present
   - ✅ Specific model features are required (e.g., specific Gemini models)
   - ✅ User explicitly requests Gemini integration
   - ❌ NEVER use Gemini just for text generation that Claude can do
   - ❌ NEVER add complexity without clear unique value
   - **Question to ask**: "What can Gemini do here that Claude cannot?"
🚨 **USE LLM CAPABILITIES**: When designing command systems or natural language features:
   - ❌ NEVER suggest keyword matching, regex patterns, or rule-based parsing
   - ❌ NEVER propose "if word in text" simplistic approaches
   - ✅ ALWAYS leverage LLM's natural language understanding
   - ✅ ALWAYS trust the LLM to understand context, nuance, and intent
   - **Pattern**: User intent → LLM understanding → Natural response
   - **Anti-pattern**: Keywords → Rules → Rigid behavior

🚨 **NEVER SIMULATE INTELLIGENCE**: When building response generation systems:
   - ❌ NEVER create Python functions that simulate Claude's responses with templates
   - ❌ NEVER use pattern matching to generate "intelligent" responses  
   - ❌ NEVER build `_create_contextual_response()` methods that fake understanding
   - ❌ NEVER generate generic replies like "I'll fix the issue" or "Thanks for the suggestion"
   - ✅ ALWAYS invoke actual Claude for genuine response generation
   - ✅ ALWAYS pass full comment context to Claude for analysis
   - ✅ ALWAYS ensure responses address specific technical points, not patterns
   - **Pattern**: Collect data → Claude analyzes → Claude responds
   - **Anti-pattern**: Collect data → Python templates → Fake responses
   - **Violation Count**: 100+ times - STOP THIS PATTERN IMMEDIATELY

🚨 **EVIDENCE-BASED APPROACH**: Core principles for all analysis
   - ✅ Extract exact error messages/code snippets before analyzing
   - ✅ Show actual output before suggesting fixes
   - ✅ Reference specific line numbers when debugging
   - 🔍 All claims must trace to specific evidence

🚨 **QUICK QUALITY CHECK** (⚡): For debugging/complex tasks, verify:
   - 🔍 Evidence shown? (errors, code, output)
   - ✓ Claims match evidence?
   - ⚠️ Uncertainties marked?
   - ➡️ Next steps clear?

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
6. **Path Conventions**: `roadmap/` = `/roadmap/` from project root
7. 🚨 **DATE INTERPRETATION**: Environment date format is YYYY-MM-DD where MM is the month number (01=Jan, 07=July)
8. 🚨 **Branch Protocol**: → See "Git Workflow" section
9. 🚨 **TOOL EXPLANATION VS EXECUTION**: ⚠️ MANDATORY distinction
   - ✅ When user asks "does X tool do Y?", clearly state if you're explaining or executing
   - ✅ If explaining capabilities, use "X tool CAN do Y" language
   - ✅ If actually executing, use the tool and show results
   - ❌ NEVER explain tool capabilities as if you executed them
   - ⚠️ Example: "The /learn command can save to memory" vs "Saving to memory now..."
10. 🚨 **Dev Branch Protection**: → See "Git Workflow" section
11. 🚨 **PUSH VERIFICATION**: ⚠️ ALWAYS verify push success by querying remote commits after every `git push` | Use `gh pr view` or `git log origin/branch` to confirm changes are on remote
12. 🚨 **PR STATUS INTERPRETATION**: ⚠️ CRITICAL - GitHub PR states mean:
   - **OPEN** = Work In Progress (WIP) - NOT completed
   - **MERGED** = Completed and integrated into main branch  
   - **CLOSED** = Abandoned or rejected - NOT completed
   - ❌ NEVER mark tasks as completed just because PR exists
   - ✅ ONLY mark completed when PR state = "MERGED"
13. 🚨 **PLAYWRIGHT MCP DEFAULT**: ⚠️ MANDATORY - When running in Claude Code CLI:
   - ✅ ALWAYS use Playwright MCP (@playwright/mcp) for browser automation by default
   - ✅ Microsoft's 2025 accessibility-tree based MCP server for AI-first automation
   - ✅ Use Playwright MCP functions for structured, deterministic browser testing
   - ✅ Fallback to Puppeteer MCP for Chrome-specific or stealth testing when needed
   - Benefits: Accessibility-tree approach, cross-browser support, AI-optimized, session sharing
14. 🚨 **CONTEXT7 MCP PROACTIVE USAGE**: ⚠️ MANDATORY - When encountering API/library issues:
   - ✅ ALWAYS use Context7 MCP for accurate API documentation when facing errors
   - ✅ **Pattern**: Error occurs → Use `mcp__context7__resolve-library-id` → Get docs with `mcp__context7__get-library-docs`
   - ✅ Search for specific error patterns, method signatures, or usage examples
   - ✅ **Example**: Firestore transaction errors → Get google-cloud-firestore docs → Find correct API usage
   - ❌ NEVER guess API usage or rely on outdated assumptions
   - Benefits: Up-to-date docs, correct syntax, real working examples, eliminates trial-and-error
15. 🚨 **GITHUB TOOL PRIORITY**: ⚠️ MANDATORY - Tool hierarchy for GitHub operations:
   - ✅ **PRIMARY**: GitHub MCP tools (`mcp__github-server__*`) for all GitHub operations
   - ✅ **SECONDARY**: `gh` CLI as fallback when MCP fails or unavailable
   - ✅ **TERTIARY**: Slash commands (e.g., `/copilot`) - user wants them to work but don't wait/assume completion
   - ❌ NEVER wait for slash commands to complete when MCP tools can provide immediate results
   - ✅ **Pattern**: Try MCP first → Fall back to `gh` CLI → Slash commands are bonus, not dependency
   - Benefits: Immediate results, reliable API access, no command completion uncertainty
16. 🚨 **MEMORY ENHANCEMENT PROTOCOL**: ⚠️ MANDATORY for specific commands
- **Enhanced Commands**: `/think`, `/learn`, `/debug`, `/analyze`, `/fix`, `/plan`, `/execute`, `/arch`, `/test`, `/pr`, `/perp`, `/research`
- **Execution Steps**:
  1. ✅ **Extract key terms** from command arguments (entities, technical terms, PR references)
  2. ✅ **Search Memory MCP**: Call `mcp__memory-server__search_nodes(query)` with extracted terms (MCP functions use double underscores as namespace separators)
  3. ✅ **Log results**: Always show "🔍 Memory searched: X relevant memories found"
  4. ✅ **Natural integration**: If memories found, incorporate context naturally into response
  5. ❌ **Memory search is mandatory** for listed commands unless performance/availability exceptions apply (see constraints below)
- **Transparency Requirements**:
  - Show "🔍 Searching memory..." when search begins
  - Report "📚 Found X relevant memories" or "💭 No relevant memories found"
  - Indicate when response is enhanced: "📚 Enhanced with memory context"
- **Performance Constraints**:
  - Batch all terms into single search (not multiple calls)
  - Skip if search would take >100ms with notice to user (100ms chosen as UX threshold for perceived instant response)
  - Continue without enhancement if MCP unavailable (with notice)
- **Integration Approach**:
  - Use natural language understanding to weave context seamlessly
  - Don't mechanically inject memory blocks
  - Judge relevance using semantic understanding, not keyword matching
  - Prioritize recent and relevant memories

### 🔧 GitHub MCP Setup
**Token**: Set in `claude_mcp.sh` line ~247 via `export GITHUB_TOKEN="your_token_here"`
**Private Repos**: Use direct functions only (no search) | `mcp__github-server__get_pull_request()`
**Restart After Token Change**: Remove & re-add github-server MCP

## Orchestration System

**Full Documentation**: → `.claude/commands/orchestrate.md` for complete system details

### 🚨 Agent Operation
**System**: Uses tmux sessions with specialized agents (frontend, backend, testing, opus-master)
**Startup**: `./claude_start.sh` auto-starts orchestration | Manual: `./orchestration/start_system.sh start`
**Monitoring**: `/orch What's the status?` or `/orch monitor agents` | Direct tmux: `tmux attach -t [agent-name]`
**Cost**: $0.003-$0.050/task | Redis required for coordination
**Working Directory**: ❌ NEVER cd into agent workspaces | ✅ Provide cd command for user to copy if needed
**CRITICAL**: ❌ NEVER execute orchestration tasks yourself | ✅ ALWAYS delegate to agents when /orch or /orchestrate is used
**ENFORCEMENT**: When user runs /orch, you MUST ONLY monitor agents - NO direct execution allowed! The entire point of /orch is agent delegation!
**NO HARDCODING**: ❌ NEVER hardcode task patterns - agents execute EXACT tasks requested | ✅ General task agents, not pattern-matched types

## Project Overview

WorldArchitect.AI = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack**: Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

**Docs**: → `.cursor/rules/project_overview.md` (full details)
- Documentation map → `.cursor/rules/documentation_map.md`
- Quick reference → `.cursor/rules/quick_reference.md`
- Progress tracking → `roadmap/templates/progress_tracking_template.md`
- Directory structure → `/directory_structure.md`
- **AI Assistant Guide**: → `mvp_site/README_FOR_AI.md` (CRITICAL system architecture for AI assistants)
- **📋 MVP Site Architecture**: → `mvp_site/README.md` (comprehensive codebase overview)
- **📋 Code Review & File Responsibilities**: → `mvp_site/CODE_REVIEW_SUMMARY.md` (detailed file-by-file analysis)
- **Browser Test Mode**: → `mvp_site/testing_ui/README_TEST_MODE.md` (How to bypass auth in browser tests)

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
**Principles**: SOLID, DRY | **Templates**: Use existing code patterns | **Validation**: `isinstance()` checks
**Constants**: Module-level (>1x) or constants.py (cross-file) | **Imports**: Module-level only, NO inline/try-except
**Path Computation**: ✅ Use `os.path.dirname()` to retrieve the parent directory of a file path | ✅ Use `os.path.join()` for constructing paths | ✅ Use `pathlib.Path` for modern path operations | ❌ NEVER use `string.replace()` for paths
- 🔍 Evidence: PR #818 - Replaced fragile `.replace('/tests', '')` with proper directory navigation

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
`tempfile.mkdtemp()` for test files | Verify before assuming | ❌ unsolicited refactoring |
**Logging**: ✅ `import logging_util` | ❌ `import logging` | Use project's unified logging
Use docstrings, proper JS loading

🚨 **PR Review Verification**: Always verify current state before applying review suggestions
- ✅ Check if suggested fix already exists in code
- ✅ Read the actual file content before making changes
- ❌ NEVER blindly apply review comments without verification
- 🔍 Evidence: PR #818 - Copilot suggested fixing 'string_type' that was already correct

### Website Testing & Deployment Expectations (🚨 CRITICAL)
🚨 **BRANCH ≠ WEBSITE**: ❌ NEVER assume branch changes are visible on websites without deployment
- ✅ Check PR description first - many changes are tooling/CI/backend only
- ✅ Feature branches need local server OR staging deployment for UI changes
- ❌ NEVER expect developer tooling changes to affect website appearance
- ✅ Production websites typically serve main branch only

🚨 **"Website looks same" Protocol**: Check PR type | Ask URL (local vs prod) | Hard refresh | Explain: branch ≠ deployment

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
- ❌ NEVER assume conflict detection works based on testing with clean PRs only
- 🔍 Evidence: PR #780 with real conflicts revealed false negative bug that clean PRs missed
- **Why Critical**: Clean PRs won't expose detection failures - need real conflicts to validate
**Validation**: Verify PASS/FAIL detection | Output must match summary | Parse output, don't trust exit codes
**Test Assertions**: ⚠️ MANDATORY - Must match actual validation behavior exactly
- 🔍 Evidence: PR #818 - MBTI test checked .lower() but validation only does .strip()
- ✅ Always verify what transformations validation actually performs
**Exception Specificity**: ✅ Use specific exception types in tests (ValidationError, not Exception)
- 🔍 Evidence: PR #818 - Improved test precision with Pydantic's ValidationError
**Methodology**: Fix one issue at a time | Run after each fix | Prefer test fixes over core logic
**Rules**: ✅ Run before task completion | ❌ NEVER skip without permission | ✅ Only use ✅ after real results

### Safety & Security
❌ Global `document.addEventListener('click')` without approval | Test workflows after modifications |
Document blast radius | Backups → `tmp/` | ❌ commit if "DO NOT SUBMIT" | Analysis + execution required

### File Deletion Impact Protocol (🚨 CRITICAL)
**Before deleting established files**: Run comprehensive reference search to avoid cascading cleanup
- `grep -r "<filename>" .` for code references (replace "<filename>" with the actual term you're searching for)
- `find . -name "*.md" -exec grep -l "<filename>" {} \;` for documentation (replace "<filename>" with the actual term you're searching for)
- Check: scripts, tests, configuration, imports, error messages, user guidance
- **Budget 2-3x normal effort** for large file deletions due to cleanup cascade
- **Evidence**: PR #722 required 36-file cleanup after deleting copilot.sh (695 lines)

### Scope Management Protocol (⚠️ MANDATORY)  
**Distinguish rewrite vs consolidation** to set proper effort expectations
- **Consolidation**: Reorganizing existing functionality (preserve files, move/rename)
- **Rewrite**: Replacing with new implementation (delete old, extensive cleanup needed)
- ❌ NEVER use "consolidation" when you mean "rewrite" - causes scope underestimation
- **Evidence**: PR #722 called "consolidation" but became Option 3 rewrite with extensive cleanup

### File Placement Rules (🚨 HARD RULE)
🚨 **NEVER add new files directly to mvp_site/** without explicit user permission
- ❌ NEVER create test files, documentation, or scripts directly in mvp_site/
- ✅ If unsure, add content to roadmap/scratchpad_[branch].md instead
- ✅ Ask user where to place new files before creating them
- **Exception**: Only when user explicitly requests file creation in mvp_site/

🚨 **Test File Policy**: Add to existing files, NEVER create new test files
- ⚠️ MANDATORY: Always add tests to existing test files that match the functionality
- ❌ NEVER create `test_new_feature.py` - add to `test_existing_module.py` instead
- 🔍 Evidence: PR #818 - CodeRabbit caught test_cache_busting_red_green.py violation
- ✅ Moved cache busting tests to test_main_routes.py to comply with policy
🚨 **Code Review**: Check README.md and CODE_REVIEW_SUMMARY.md before mvp_site/ changes

### Repository Separation
**Pattern**: Specialized systems → Dedicated repos | **Benefits**: Cleaner automation, focused workflows

### Browser vs HTTP Testing (🚨 HARD RULE)
**CRITICAL DISTINCTION**: Never confuse browser automation with HTTP simulation
- 🚨 **testing_ui/**: ONLY real browser automation using **Playwright MCP** (default) or Puppeteer MCP | ❌ NEVER use `requests` library here
- 🚨 **testing_http/**: ONLY HTTP requests using `requests` library | ❌ NEVER use browser automation here
- ⚠️ **/testui and /testuif**: MUST use real browser automation (Playwright MCP preferred) | NO HTTP simulation
- ⚠️ **/testhttp and /testhttpf**: MUST use HTTP requests | NO browser automation
- ✅ **/testi**: HTTP requests are acceptable (integration testing)
- **Red Flag**: If writing "browser tests" with `requests.get()`, STOP immediately

- **Command Structure** (Claude Code CLI defaults to Playwright MCP):
  - `/testui` = Browser (Playwright MCP) + Mock APIs
  - `/testuif` = Browser (Playwright MCP) + REAL APIs (costs $)
  - `/testhttp` = HTTP + Mock APIs  
  - `/testhttpf` = HTTP + REAL APIs (costs $)
  - `/tester` = End-to-end tests with REAL APIs (user decides cost)

### Real API Testing Protocol (🚨 MANDATORY)
**NEVER push back or suggest alternatives when user requests real API testing**:
- ✅ User decides if real API costs are acceptable - respect their choice
- ✅ `/tester`, `/testuif`, `/testhttpf` commands are valid user requests
- ✅ Real API testing provides valuable validation that mocks cannot
- ❌ NEVER suggest mock alternatives unless specifically asked
- ❌ NEVER warn about costs unless the command requires confirmation prompts
- **User autonomy**: User controls their API usage and testing approach

### Browser Test Execution Protocol (🚨 MANDATORY)

🚨 **PREFERRED**: Playwright MCP in Claude Code CLI - Accessibility-tree based, AI-optimized, cross-browser
🚨 **SECONDARY**: Puppeteer MCP for Chrome-specific or stealth testing scenarios
🚨 **FALLBACK**: Playwright IS installed in venv! Use headless=True | ❌ NEVER say "not installed"

**Commands**: `./run_ui_tests.sh mock --playwright` (default) | `./run_ui_tests.sh mock --puppeteer` (secondary) | `./run_ui_tests.sh mock` (Playwright fallback)

**Test Mode URL**: `http://localhost:8081?test_mode=true&test_user_id=test-user-123` - Required for auth bypass!

**Details**: → `.cursor/rules/test_protocols.md`

### Coverage Analysis Protocol (⚠️)
**MANDATORY**: When analyzing test coverage:
1. **ALWAYS use**: `./run_tests.sh --coverage` or `./coverage.sh` (HTML default)
2. **NEVER use**: Manual `coverage run` commands on individual test files
3. **Verify full test suite**: Ensure all 94+ test files are included in coverage analysis
4. **Report source**: Always mention "Coverage from full test suite via run_tests.sh"
5. **HTML location**: `/tmp/worldarchitectai/coverage/index.html`

## Git Workflow

| Rule | Description | Commands/Actions |
|------|-------------|------------------|
| **Main = Truth** | Use `git show main:<file>` for originals | ❌ push to main (except roadmap/sprint files) |
| **PR Workflow** | All changes via PRs | `gh pr create` + test results in description |
| **Branch Safety** | Verify before push | `git push origin HEAD:branch-name` |
| **🚨 Upstream Tracking** | Set tracking to avoid "no upstream" in headers | `git push -u origin branch-name` OR `git branch --set-upstream-to=origin/branch-name` |
| **Integration** | Fresh branch after merge | `./integrate.sh` |
| **Pre-PR Check** | Verify commits/files | → `.cursor/rules/validation_commands.md` |
| **Post-Merge** | Check unpushed files | `git status` → follow-up PR if needed |
| **Progress Track** | Scratchpad + JSON | `roadmap/scratchpad_[branch].md` + `tmp/milestone_*.json` |
| **PR Testing** | Apply PRs locally | `gh pr checkout <PR#>` |
| **Roadmap Updates** | Always create PR | All files require PR workflow |

🚨 **No Main Push**: ✅ `git push origin HEAD:feature` | ❌ `git push origin main`
   - **ALL changes require PR**: Including roadmap files, documentation, everything
   - **Fresh branches from main**: Always create new branch from latest main for new work
   - **Pattern**: `git checkout main && git pull && git checkout -b descriptive-name`

🚨 **PR Context Management**: Verify before creating PRs - Check git status | Ask which PR if ambiguous | Use existing branches

🚨 **Branch Protection**: ❌ NEVER switch without explicit request | ❌ NEVER use dev[timestamp] for development
✅ Create descriptive branches | Verify context before changes | Ask if ambiguous

🚨 **Conflict Resolution**: Analyze both versions | Assess critical files | Test resolution | Document decisions
**Critical Files**: CSS, main.py, configs, schemas | **Process**: `./resolve_conflicts.sh`

🚨 **COMMAND FAILURE TRANSPARENCY** (⚠️ MANDATORY): When user commands fail unexpectedly:
   - ✅ Immediately explain what failed and why
   - ✅ Show system messages/errors received  
   - ✅ Explain resolution approach being taken
   - ✅ Ask preference for alternatives (merge vs rebase, etc.)
   - ❌ NEVER silently fix without explanation
   - **Pattern**: Command fails > Explain > Show options > Get preference > Execute
   - **Evidence**: Silent git merge resolution leads to "ignored comment" perception

**Commit Format**: → `.cursor/rules/examples.md`

## Environment, Tooling & Scripts

1. **Python venv**: Verify activated before running Python/tests | If missing/corrupted → `VENV_SETUP.md`
2. **Robust Scripts**: Make idempotent, work from any subdirectory
3. **Automation Setup Scripts**: Single setup script with validation, logging, health checks for production systems
   - ✅ **Pattern**: Prerequisites check → Logging setup → Service configuration → Validation → Health check
   - ✅ **Features**: Error handling, rollback capability, status reporting, documentation
   - 🔍 **Evidence**: setup_automation.sh successfully deployed complete cron job + monitoring system
   - **Application**: Cron jobs, service configuration, system initialization, deployment automation
4. **Python Execution**: ✅ Run from project root | ❌ cd into subdirs
5. **vpython Tests**: 
   - ⚠️ "run all tests" → `./run_tests.sh`
   - ⚠️ Test fails → fix immediately or ask user
   - ✅ `TESTING=true vpython mvp_site/test_file.py` (from root)
5. 🚨 **Test Compliance**: → See "Testing Protocol" section
7. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted
8. **Web Scraping**: Use full-content tools (curl) not search snippets
9. **Log Files Location**:
   - ✅ **Server logs are in `/tmp/worldarchitectai_logs/`** with subfolders/files named by branch
   - ✅ **Branch-specific logs**: `/tmp/worldarchitectai_logs/[branch-name].log`
   - ✅ **Current branch log**: `/tmp/worldarchitectai_logs/$(git branch --show-current).log`
   - ✅ **Log commands**: `tail -f /tmp/worldarchitectai_logs/[branch].log` for real-time monitoring
   - ✅ **Search logs**: `grep -i "pattern" /tmp/worldarchitectai_logs/[branch].log`
   - ✅ **Binary logs**: Use `strings /tmp/worldarchitectai_logs/[branch].log | grep -i "pattern"`
   - ✅ **Find current log**: `git branch --show-current` then check corresponding log file

**Test Commands**: → `.cursor/rules/validation_commands.md`

## Data Integrity & AI Management

1. **Data Defense**: Assume incomplete/malformed | Use `dict.get()` | Validate structures
2. **Critical Logic**: Implement safeguards in code, not just prompts
3. **Single Truth**: One clear way per task | Remove conflicting rules

## Operations Guide

### Memory MCP Usage
**Create Knowledge**: `mcp__memory-server__create_entities([{name, entityType, observations}])`
**Search Knowledge**: `mcp__memory-server__search_nodes("query")` → Find existing before creating
**Persist Learning**: `/learn` auto-saves, but use Memory MCP directly for complex knowledge graphs
**Pattern**: Search first → Create if new → Add observations to existing → Build relationships

### Task Agent Patterns
**When to Spawn**: 3+ parallel subtasks | Independent research needed | Complex analysis
**Basic Pattern**: `Task(description="Research X", prompt="Detailed instructions...")`
**Integration**: Main thread continues while agents work → Agents return results → Integrate findings
**Example**: "Analyze all test files" → Spawn agent per directory → Combine reports

### TodoWrite Protocol
**When Required**: Tasks with 3+ steps | Complex implementations | /execute commands
**Status Flow**: `pending` → `in_progress` (before starting) → `completed` (after done)
**Circuit Breaker**: For /execute - TodoWrite checklist prevents premature execution
**Update Pattern**: Mark current task `in_progress`, complete it, then move to next

### Common Operations
**Multi-file Edits**: Use MultiEdit with 3-4 edits max per call to avoid timeouts
**Context Management**: Check remaining % before complex operations | Split large tasks
**Response Length**: Use bullet points | Essential info only | Split across messages if needed
**Tool Recovery**: After 2 failures → Try alternative tool → Fetch from main if corrupted
**Backup Before Major Changes**: Copy critical files to `.backup` or `/tmp` first

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
**Branch Confusion**: Verify context before changes | Check PR destination | Evidence: PR #627/628
**Orchestration Hardcoding**: ❌ NEVER pattern-match tasks to agent types | ✅ Execute exact requested tasks | Evidence: task_dispatcher.py created test agents for all tasks

### Debugging Protocol (🚨 MANDATORY)
**Process**: Extract evidence → Analyze → Verify → Fix | Trace: Backend → API → Frontend
**Evidence**: Primary (code/errors) > Secondary (docs) > General (patterns) > Speculation
**Details**: → `.cursor/rules/debugging_guide.md`

### Critical Rules
**Data Corruption**: Systemic issue - search all patterns | **Temp Fixes**: Flag + fix NOW
**Task Complete**: Solve + Update docs + Memory + Audit | **No blind execution**
**Details**: → `.cursor/rules/lessons.mdc`

## Slash Commands

**Full Documentation**: → `.claude/commands/` | Use `/list` for available commands

### Command Classification (Dual Architecture)

**🧠 Cognitive Commands** (Semantic Composition):
- `/think`, `/arch`, `/debug` - Modify thinking approach, compose naturally
- **Behavior**: Automatic semantic understanding and tool integration

**⚙️ Operational Commands** (Protocol Enforcement):  
- `/headless`, `/handoff`, `/orchestrate` - Modify execution environment
- **Behavior**: Mandatory workflow execution before task processing

**🔧 Tool Commands** (Direct Execution):
- `/execute`, `/test`, `/pr` - Direct task execution
- **Behavior**: Immediate execution with optional parameters

### Critical Enforcement
🚨 **EXECUTE CIRCUIT BREAKER**: `/e` or `/execute` → TodoWrite checklist MANDATORY
- Context % | Complexity | Subagents? | Plan presented | Approval received
- ❌ NEVER start work without approval | TodoWrite = safety protocol

🚨 **OPERATIONAL COMMAND ENFORCEMENT**: `/headless`, `/handoff`, `/orchestrate`, `/orch`
- ✅ ALWAYS trigger protocol workflow before task execution
- ✅ Create isolated environments as specified in command documentation  
- ❌ NEVER process as regular tasks without environment setup
- ❌ NEVER execute /orch or /orchestrate tasks yourself - ONLY monitor agents
- ✅ For /orch: Create agents → Monitor progress → Report results ONLY

**Key Commands**: `/execute` (no approval) | `/plan` (requires approval) | `/replicate` (PR analysis)
**Dual Composition**: Cognitive (semantic) + Operational (protocol) + Tool (direct)
**Unified Learning**: ONE `/learn` command with Memory MCP integration

## Special Protocols

### GitHub PR Comment Response Protocol (⚠️)
**MANDATORY**: Systematically address ALL PR comments from all sources

**Comment Sources**: Inline (`gh api`) | General (`gh pr view`) | Reviews | Copilot (include "suppressed")

**Response Status**: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED

**Critical Rule**: ❌ NEVER ignore any comment type, including "suppressed" Copilot feedback

🚨 **DATA LOSS WARNINGS**: Treat all data loss warnings from CodeRabbit/Copilot as CRITICAL
- ❌ NEVER dismiss data integrity concerns as "intentional design"
- ✅ ALWAYS implement proper validation before conflict resolution
- ✅ ALWAYS treat data corruption warnings as highest priority
- 🔍 Evidence: CodeRabbit data loss warning prevented silent corruption in backup script

### Import Protocol (🚨 CRITICAL)
**Zero Tolerance**: Module-level only | No inline/try-except/conditionals | Use `as` for conflicts
**Rule**: Import or fail - no "optional" patterns

### API Error Prevention (🚨)
❌ Print code/file content | ✅ Use file_path:line_number | Keep responses concise

### Browser Testing vs HTTP Testing (🚨)
**HARD RULE**: NO HTTP simulation for browser tests!
- `/testuif` = Real browser automation (Puppeteer MCP/Playwright) | `/testi` = HTTP requests OK
- Browser tests require: Page navigation, element clicks, form fills, screenshots
- Auth bypass: Use test mode URL params, NOT HTTP simulation

### PR References (⚠️)
**MANDATORY**: Include full GitHub URL - Format: "PR #123: https://github.com/jleechan2015/worldarchitect.ai/pull/123"


## Project-Specific

### Flask: SPA route for index.html | Hard refresh for CSS/JS | Cache-bust in prod
### Python: venv required | Source .bashrc after changes | May need python3-venv
### AI/LLM: Detailed prompts crucial | Critical instructions first | Long prompts = fatigue
### Workflow: Simple-first | Tool fail = try alternative | Main branch = recovery source

## Quick Reference

- **Test**: `TESTING=true vpython mvp_site/test_file.py` (from root)
- **Integration**: `TESTING=true python3 mvp_site/test_integration/test_integration.py`
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