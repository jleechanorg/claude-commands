# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on WorldArchitect.AI**

## 🚨 CRITICAL: MANDATORY BRANCH HEADER PROTOCOL

**EVERY SINGLE RESPONSE MUST END WITH THIS HEADER - NO EXCEPTIONS:**

```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

**Header Generation Methods:**
- **PREFERRED:** Use `/header` command (finds project root automatically)
- **Manual:** `git branch --show-current` | `git rev-parse --abbrev-ref @{upstream}` | `gh pr list --head $(git branch --show-current) --json number,url`

**Examples:**
- `[Local: main | Remote: origin/main | PR: none]`
- `[Local: feature-x | Remote: origin/main | PR: #123 https://github.com/user/repo/pull/123]`

**❌ NEVER SKIP THIS HEADER - USER WILL CALL YOU OUT IMMEDIATELY**

🚨 **HEADER PR CONTEXT TRACKING**: Header must reflect actual work context
- ❌ NEVER show "PR: none" when work is related to existing PR context
- ✅ ALWAYS consider actual work context when determining PR relevance
- 🔍 Evidence: Recurring pattern of "PR: none" when user expects PR context to be tracked

🚨 **ZERO TOLERANCE PR MERGE APPROVAL PROTOCOL**: ⚠️ MANDATORY
- ❌ **NEVER MERGE PRS WITHOUT EXPLICIT USER APPROVAL - ZERO EXCEPTIONS**
- ✅ **MANDATORY approval phrase**: User must type "MERGE APPROVED" for merge-triggering actions
- 🔍 **Evidence**: PR #967 auto-merged violation - this must NEVER happen again

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
- **Pattern**: Cognitive = semantic composition, Operational = protocol enforcement

🚨 **NO FALSE ✅**: Only use ✅ for 100% complete/working. Use ❌ ⚠️ 🔄 or text for partial.

🚨 **NO POSITIVITY**: Be extremely self-critical. No celebration unless 100% working.

🚨 **NO PREMATURE VICTORY DECLARATION**: Task completion requires FULL verification
- ❌ NEVER declare success based on intermediate steps (file edits, partial work)
- ✅ For agent tasks: Requires PR created + pushed + link verified
- ✅ For direct tasks: Requires changes committed + pushed + tested
- 🔍 Evidence: Agent modified schedule_branch_work.sh but no PR = TASK INCOMPLETE

🚨 **NO EXCUSES FOR TEST FAILURES**: When asked to fix tests, FIX THEM ALL
- ❌ NEVER say "pre-existing issues" or "unrelated to our changes"
- ❌ NEVER settle for partial fixes (97/99 is NOT acceptable)
- ✅ ALWAYS fix ALL failing tests to 100% pass rate

🚨 **NO ASSUMPTIONS ABOUT RUNNING COMMANDS**:
- ❌ NEVER explain what a command "will do" when it's already running
- ✅ ALWAYS wait for actual command output and results
- **Pattern**: User says "X is running..." → Wait for actual results, don't speculate

🚨 **NO FAKE IMPLEMENTATIONS**: ⚠️ MANDATORY
- ❌ NEVER create files with "# Note: In the real implementation" comments
- ❌ NEVER write placeholder code that doesn't actually work
- ❌ NEVER duplicate systematic protocols that already exist in other .md files
- ✅ ALWAYS audit existing commands before writing new implementations
- ✅ ALWAYS build real, functional code that works immediately
- **Pattern**: Real implementation > No implementation > Fake implementation
- **Evidence**: PR #820 - 563+ lines of fake code removed

🚨 **ORCHESTRATION OVER DUPLICATION**: ⚠️ MANDATORY
- **Principle**: Orchestrators delegate to existing commands, never reimplement
- ✅ Use existing /commentreply, /pushl, /fixpr rather than duplicating their logic
- ❌ NEVER copy systematic protocols from other .md files into new commands

🚨 **NO OVER-ENGINEERING**: Prevent building parallel inferior systems
- ✅ ALWAYS ask "Can the LLM handle this naturally?" before building parsers
- ✅ ALWAYS try enhancing existing systems before building parallel new ones
- ❌ NEVER build complex parsing when LLM can understand intent naturally
- **Evidence**: Command composition over-engineering (PR #737)

🚨 **NO UNNECESSARY EXTERNAL APIS**: Before adding ANY external API integration:
- ✅ FIRST ask "Can Claude solve this directly without external APIs?"
- ✅ ALWAYS try direct implementation before adding dependencies
- ❌ NEVER default to Gemini API just because it exists in codebase
- **Question to ask**: "What can Gemini do here that Claude cannot?"

🚨 **NEVER SIMULATE INTELLIGENCE**: When building response generation systems:
- ❌ NEVER create Python functions that simulate Claude's responses with templates
- ❌ NEVER use pattern matching to generate "intelligent" responses
- ✅ ALWAYS invoke actual Claude for genuine response generation
- **Pattern**: Collect data → Claude analyzes → Claude responds

🚨 **EVIDENCE-BASED APPROACH**: Core principles for all analysis
- ✅ Extract exact error messages/code snippets before analyzing
- ✅ Show actual output before suggesting fixes
- ✅ Reference specific line numbers when debugging
- 🔍 All claims must trace to specific evidence

## Self-Learning Protocol

🚨 **AUTO-LEARN**: Document corrections immediately when: User corrects | Self-realizing | Something fails | Pattern repeats

**Process**: Detect → Analyze → Document (CLAUDE.md/learnings.md/lessons.mdc) → Apply → Persist to Memory MCP

**/learn Command**: `/learn [optional: specific learning]` - Unified learning with Memory MCP integration

## Claude Code Specific Behavior

1. **Directory Context**: Operates in worktree directory shown in environment
2. **Test Execution**: Use `TESTING=true vpython` from project root
3. **File Paths**: Always absolute paths | ✅ Use `~` NOT `/home/jleechan`
4. **Gemini SDK**: `from google import genai` (NOT `google.generativeai`)
5. 🚨 **Branch Protocol**: → See "Git Workflow" section
6. 🚨 **TOOL EXPLANATION VS EXECUTION**: ⚠️ MANDATORY distinction
   - ✅ When user asks "does X tool do Y?", clearly state if explaining or executing
   - ❌ NEVER explain tool capabilities as if you executed them
7. 🚨 **PLAYWRIGHT MCP DEFAULT**: ⚠️ MANDATORY - When running in Claude Code CLI:
   - ✅ ALWAYS use Playwright MCP for browser automation by default
   - ✅ Fallback to Puppeteer MCP for Chrome-specific or stealth testing
8. 🚨 **CONTEXT7 MCP PROACTIVE USAGE**: ⚠️ MANDATORY - When encountering API/library issues:
   - ✅ **Pattern**: Error occurs → Use `mcp__context7__resolve-library-id` → Get docs
   - ❌ NEVER guess API usage or rely on outdated assumptions
9. 🚨 **GITHUB TOOL PRIORITY**: ⚠️ MANDATORY - Tool hierarchy for GitHub operations:
   - ✅ **PRIMARY**: GitHub MCP tools (`mcp__github-server__*`)
   - ✅ **SECONDARY**: `gh` CLI as fallback when MCP fails
   - ✅ **TERTIARY**: Slash commands - user wants them to work but don't wait for completion
10. 🚨 **MEMORY ENHANCEMENT PROTOCOL**: ⚠️ MANDATORY for specific commands
    - **Enhanced Commands**: `/think`, `/learn`, `/debug`, `/analyze`, `/fix`, `/plan`, `/execute`, `/arch`, `/test`, `/pr`
    - **Execution Steps**: Extract terms → Search Memory MCP → Log results → Integrate naturally
    - **Transparency**: Show "🔍 Searching memory..." and report results

### 🔧 GitHub MCP Setup
**Token**: Set in `claude_mcp.sh` line ~247 via `export GITHUB_TOKEN="your_token_here"`
**Private Repos**: Use direct functions only | `mcp__github-server__get_pull_request()`

## Orchestration System

**Full Documentation**: → `.claude/commands/orchestrate.md`

### 🚨 Agent Operation
**System**: Uses tmux sessions with dynamic task agents managed by Python monitor
**Startup**: `./claude_start.sh` auto-starts orchestration
**Monitoring**: `/orch What's the status?` or `tmux attach -t [agent-name]`
**CRITICAL**: ❌ NEVER execute orchestration tasks yourself | ✅ ALWAYS delegate to agents

🚨 **ORCHESTRATION DIRECT EXECUTION PREVENTION**: ⚠️ MANDATORY HARD STOP PROTOCOL
- **Hard Stop Pattern**: Input scan for "/orch" prefix → immediate Task tool delegation
- **Mental Model**: "/orch" = "create agent to do this", NEVER "I should do this directly"
- **Zero Exception Rule**: "/orch" ALWAYS triggers Task tool regardless of context
- 🔍 **Evidence**: Session violation (PR #979) when urgency bypassed delegation protocol

🚨 **ORCHESTRATION TASK COMPLETION**: Full end-to-end verification required
- ✅ Agent must complete entire workflow (find → fix → commit → push → create PR)
- ✅ Verify PR creation with link before declaring success
- ❌ NEVER declare success based on agent creation alone

## Project Overview

WorldArchitect.AI = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack**: Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

**Docs**: → `.cursor/rules/project_overview.md` (full details)
- **AI Assistant Guide**: → `mvp_site/README_FOR_AI.md` (CRITICAL system architecture)
- **Code Review**: → `mvp_site/CODE_REVIEW_SUMMARY.md` (file-by-file analysis)
- **Browser Test Mode**: → `mvp_site/testing_ui/README_TEST_MODE.md`

## Core Principles & Interaction

**Work Approach**:
Clarify before acting | User instructions = law | ❌ delete without permission | Leave working code alone |
Focus on primary goal | Propose before implementing | Summarize key takeaways | Externalize all knowledge

**Collaboration Guidelines**:
- **Challenge and question**: Don't immediately agree or proceed with suboptimal requests
- **Push back constructively**: If approach has issues, suggest better alternatives with reasoning
- **Think critically**: Consider edge cases, performance, maintainability, best practices
- **Seek clarification**: Ask follow-up questions when requirements are ambiguous
- **Propose improvements**: Suggest better patterns, robust solutions, cleaner implementations
- **Be a thoughtful collaborator**: Act as good teammate who helps improve overall quality

**Response Modes**: Default = structured for complex | Direct for simple | Override: "be brief"

**Testing**: Red-green methodology | Test truth verification | Use ADTs

**Red-Green Protocol** (`/tdd` or `/rg`):
1. Write failing tests FIRST → 2. Confirm fail (red) → 3. Minimal code to pass (green) → 4. Refactor

## Development Guidelines

### Code Standards
**Principles**: SOLID, DRY | **Templates**: Use existing code patterns | **Validation**: `isinstance()` checks
**Constants**: Module-level (>1x) or constants.py (cross-file) | **Imports**: Module-level only, NO inline/try-except
**Path Computation**: ✅ Use `os.path.dirname()`, `os.path.join()`, `pathlib.Path` | ❌ NEVER use `string.replace()` for paths

🚨 **DYNAMIC AGENT ASSIGNMENT**: Replace ALL hardcoded agent mappings with capability-based selection
- ❌ NEVER use patterns like `if "test" in task: return "testing-agent"`
- ✅ ALWAYS use capability scoring with load balancing
- 🔍 Evidence: PR #873 removed 150+ lines of hardcoded mappings

### Feature Compatibility
**Critical**: Audit integration points | Update filters for new formats | Test object/string conversion
**Always Reuse**: Check existing code | Extract patterns to utilities | No duplication
**No**: Inline imports, temp comments (TODO/FIXME), hardcoded strings | Use descriptive names

### Gemini SDK
✅ `from google import genai` | ✅ `client = genai.Client(api_key=api_key)`
Models: `gemini-2.5-flash` (default), `gemini-1.5-flash` (test)
🚨 **WARNING**: See "NO UNNECESSARY EXTERNAL APIS" rule before using Gemini

### Development Practices
`tempfile.mkdtemp()` for test files | Verify before assuming | ❌ unsolicited refactoring
**Logging**: ✅ `import logging_util` | ❌ `import logging` | Use project's unified logging

🚨 **PR Review Verification**: Always verify current state before applying review suggestions
- ✅ Check if suggested fix already exists in code
- ✅ Read the actual file content before making changes
- ❌ NEVER blindly apply review comments without verification

⚠️ **PR COMMENT PRIORITY**: Address review comments in strict priority order
1. **CRITICAL**: Undefined variables, inline imports, runtime errors
2. **HIGH**: Bare except clauses, security issues
3. **MEDIUM**: Logging violations, format issues
4. **LOW**: Style preferences, optimizations

### Website Testing & Deployment Expectations (🚨 CRITICAL)
🚨 **BRANCH ≠ WEBSITE**: ❌ NEVER assume branch changes are visible on websites without deployment
- ✅ Check PR description first - many changes are tooling/CI/backend only
- ✅ Feature branches need local server OR staging deployment for UI changes
- ✅ Production websites typically serve main branch only

### Quality Standards
**Files**: Descriptive names, <500 lines | **Tests**: Natural state, visual validation, dynamic discovery
**Validation**: Verify PASS/FAIL detection | Parse output, don't trust exit codes

### 🚨 Testing Protocol
**Zero Tolerance**: Run ALL tests before completion | Fix ALL failures | No "pre-existing issues" excuse
**Commands**: `./run_tests.sh` | `./run_ui_tests.sh mock` | `gh pr view`
**Protocol**: STOP → FIX → VERIFY → EVIDENCE → Complete

🚨 **TEST WITH REAL CONFLICTS**: ⚠️ MANDATORY
- ✅ ALWAYS test merge conflict detection with PRs that actually have conflicts
- ✅ Use `gh pr view [PR] --json mergeable` to verify real conflict state before testing
- 🔍 Evidence: PR #780 with real conflicts revealed false negative bug

**Test Assertions**: ⚠️ MANDATORY - Must match actual validation behavior exactly
**Exception Specificity**: ✅ Use specific exception types in tests (ValidationError, not Exception)

### Safety & Security
❌ Global `document.addEventListener('click')` without approval | Test workflows after modifications |
Document blast radius | Backups → `tmp/` | ❌ commit if "DO NOT SUBMIT"

### File Placement Rules (🚨 HARD RULE)
🚨 **NEVER add new files directly to mvp_site/** without explicit user permission
- ✅ If unsure, add content to roadmap/scratchpad_[branch].md instead
- **Exception**: Only when user explicitly requests file creation in mvp_site/

🚨 **Test File Policy**: Add to existing files, NEVER create new test files
- ⚠️ MANDATORY: Always add tests to existing test files that match the functionality
- ❌ NEVER create `test_new_feature.py` - add to `test_existing_module.py` instead

### Browser vs HTTP Testing (🚨 HARD RULE)
**CRITICAL DISTINCTION**: Never confuse browser automation with HTTP simulation
- 🚨 **testing_ui/**: ONLY real browser automation using **Playwright MCP** (default) or Puppeteer MCP
- 🚨 **testing_http/**: ONLY HTTP requests using `requests` library
- ⚠️ **/testui and /testuif**: MUST use real browser automation (Playwright MCP preferred)
- ⚠️ **/testhttp and /testhttpf**: MUST use HTTP requests | NO browser automation

### Browser Test Execution Protocol (🚨 MANDATORY)
🚨 **PREFERRED**: Playwright MCP in Claude Code CLI - Accessibility-tree based, AI-optimized
🚨 **SECONDARY**: Puppeteer MCP for Chrome-specific or stealth testing scenarios

**Commands**: `./run_ui_tests.sh mock --playwright` (default) | `./run_ui_tests.sh mock --puppeteer`
**Test Mode URL**: `http://localhost:8081?test_mode=true&test_user_id=test-user-123`

### Coverage Analysis Protocol (⚠️)
**MANDATORY**: When analyzing test coverage:
1. **ALWAYS use**: `./run_tests.sh --coverage` or `./coverage.sh`
2. **NEVER use**: Manual `coverage run` commands on individual test files
3. **Report source**: Always mention "Coverage from full test suite via run_tests.sh"

## Git Workflow

🚨 **No Main Push**: ✅ `git push origin HEAD:feature` | ❌ `git push origin main`
- **ALL changes require PR**: Including roadmap files, documentation, everything
- **Fresh branches from main**: Always create new branch from latest main for new work

🚨 **PR Context Management**: Verify before creating PRs - Check git status | Ask which PR if ambiguous

🚨 **Branch Protection**: ❌ NEVER switch without explicit request | ❌ NEVER use dev[timestamp] for development

🚨 **GIT ANALYSIS CONTEXT CHECKPOINT**: ⚠️ MANDATORY protocol before any git comparison
- ✅ **Step 1**: Identify current branch (`git branch --show-current`)
- ✅ **Step 2**: Determine branch type (sync-main-*, feature branch, main)
- ✅ **Step 3**: Select appropriate remote comparison
- ✅ **Step 4**: Execute comparison commands with correct remote

**Commands**:
- New branch: `git checkout main && git pull && git checkout -b descriptive-name`
- Push with tracking: `git push -u origin branch-name`
- Integration: `./integrate.sh`
- Progress: `roadmap/scratchpad_[branch].md`

## Environment, Tooling & Scripts

1. **Python venv**: Verify activated before running Python/tests
2. **Python Execution**: ✅ Run from project root | ❌ cd into subdirs
3. **vpython Tests**: `TESTING=true vpython mvp_site/test_file.py` (from root)
4. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted
5. **Log Files Location**: `/tmp/worldarchitectai_logs/[branch-name].log`

**Test Commands**: → `.cursor/rules/validation_commands.md`

## Operations Guide

### Memory MCP Usage
**Search Knowledge**: `mcp__memory-server__search_nodes("query")` → Find existing before creating
**Create Knowledge**: `mcp__memory-server__create_entities([{name, entityType, observations}])`
**Pattern**: Search first → Create if new → Add observations to existing → Build relationships

### Task Agent Patterns
**When to Spawn**: 3+ parallel subtasks | Independent research needed | Complex analysis
**Basic Pattern**: `Task(description="Research X", prompt="Detailed instructions...")`

### TodoWrite Protocol
**When Required**: Tasks with 3+ steps | Complex implementations | /execute commands
**Status Flow**: `pending` → `in_progress` (before starting) → `completed` (after done)
**Update Pattern**: Mark current task `in_progress`, complete it, then move to next

### Common Operations
**Multi-file Edits**: Use MultiEdit with 3-4 edits max per call to avoid timeouts
**Context Management**: Check remaining % before complex operations | Split large tasks
**Response Length**: Use bullet points | Essential info only | Split across messages if needed
**Backup Before Major Changes**: Copy critical files to `.backup` or `/tmp` first

## Knowledge Management

### Scratchpad Protocol
`roadmap/scratchpad_[branch].md`: Goal | Plan | State | Next | Context | Branch info

### File Organization
- **CLAUDE.md**: Primary protocol
- **lessons.mdc**: Technical learnings from corrections
- **project.md**: Repository-specific knowledge base

### Process Improvement
- **5 Whys**: Root cause → lessons.mdc
- **Sync Cursor**: Copy CLAUDE.md to Cursor settings after changes
- **Proactive Docs**: Update rules/lessons after debugging without prompting

## Critical Lessons (Compressed)

### Core Patterns
**Trust But Verify**: Test before assuming | Docs ≠ code | Trace data flow

### 🚨 Anti-Patterns
**Silent Breaking Changes**: Update all str() usage when changing objects
**Branch Confusion**: Verify context before changes | Check PR destination
**Orchestration Hardcoding**: ❌ NEVER pattern-match tasks to agent types

### Debugging Protocol (🚨 MANDATORY)
**Process**: Extract evidence → Analyze → Verify → Fix | Trace: Backend → API → Frontend
**Evidence**: Primary (code/errors) > Secondary (docs) > General (patterns) > Speculation

## Slash Commands

**Full Documentation**: → `.claude/commands/` | Use `/list` for available commands

### Command Classification (Dual Architecture)

**🧠 Cognitive Commands** (Semantic Composition):
- `/think`, `/arch`, `/debug`, `/learn`, `/analyze`, `/fix`, `/perp`, `/research`
- **Behavior**: Automatic semantic understanding and tool integration

**⚙️ Operational Commands** (Protocol Enforcement):
- `/headless`, `/handoff`, `/orchestrate` - Modify execution environment
- **Behavior**: Mandatory workflow execution before task processing

**🔧 Tool Commands** (Direct Execution):
- `/execute`, `/test`, `/pr` - Direct task execution
- **Behavior**: Immediate execution with optional parameters

### Critical Enforcement
🚨 **SLASH COMMAND PROTOCOL RECOGNITION**: ⚠️ MANDATORY - Before processing ANY slash command:
- ✅ **Recognition Phase**: Scan input for "/" → Identify command type → Look up required workflow
- ✅ **Execution Phase**: Follow COMPLETE documented workflow → No partial execution allowed
- ❌ NEVER treat slash commands as content suggestions - they are execution mandates

🚨 **EXECUTE CIRCUIT BREAKER**: `/e` or `/execute` → TodoWrite checklist MANDATORY
- Context % | Complexity | Subagents? | Plan presented | Approval received

🚨 **OPERATIONAL COMMAND ENFORCEMENT**: `/headless`, `/handoff`, `/orchestrate`, `/orch`
- ✅ ALWAYS trigger protocol workflow before task execution
- ❌ NEVER execute /orch or /orchestrate tasks yourself - ONLY monitor agents

**Key Commands**: `/execute` (no approval) | `/plan` (requires approval) | `/replicate` (PR analysis) | `/fake` (code quality audit)

## Special Protocols

### GitHub PR Comment Response Protocol (⚠️)
**MANDATORY**: Systematically address ALL PR comments from all sources
**Comment Sources**: Inline (`gh api`) | General (`gh pr view`) | Reviews | Copilot
**Response Status**: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED

🚨 **DATA LOSS WARNINGS**: Treat all data loss warnings from CodeRabbit/Copilot as CRITICAL
- ❌ NEVER dismiss data integrity concerns as "intentional design"
- ✅ ALWAYS implement proper validation before conflict resolution

### Import Protocol (🚨 CRITICAL)
**Zero Tolerance**: Module-level only | No inline/try-except/conditionals | Use `as` for conflicts

### PR References (⚠️)
**MANDATORY**: Include full GitHub URL - Format: "PR #123: https://github.com/jleechan2015/worldarchitect.ai/pull/123"

### PR Description Protocol (⚠️ MANDATORY)
**PR descriptions must reflect complete delta vs origin/main, not just recent work**:
- ✅ Use `git diff --stat origin/main...HEAD` to get comprehensive change summary
- ✅ Analyze actual file changes, additions, deletions vs main branch
- ❌ NEVER describe only latest commits or recent work

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

## API Timeout Prevention (🚨)

**MANDATORY**: Prevent API timeouts:
- **Edits**: MultiEdit with 3-4 max | Target sections, not whole files
- **Thinking**: 5-6 thoughts max | Concise | No unnecessary branching
- **Responses**: Bullet points | Minimal output | Essential info only
- **Tools**: Batch calls | Smart search (Grep/Glob) | Avoid re-reads
- **Complex tasks**: Split across messages | Monitor server load
