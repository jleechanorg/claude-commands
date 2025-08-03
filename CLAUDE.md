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

**Primary rules file for AI collaboration on Your Project**
*Research: AI pair programming increases task completion speed by 55.8% ([Microsoft Research](https://www.microsoft.com/en-us/research/publication/the-impact-of-ai-on-developer-productivity-evidence-from-github-copilot/))*

## 🎯 Solo Developer Essentials

**Critical rules for efficient solo development - these 10 rules handle 80% of scenarios:**

1. **🚨 MANDATORY**: End every response with: `[Local: <branch> | Remote: <upstream> | PR: <number> <url>]`
2. **❌ NO FALSE ✅**: Only use ✅ for 100% complete/working - solo developers can't afford wrong information
3. **🔥 TEST BEFORE COMPLETION**: Run ALL tests, fix ALL failures - no team to catch mistakes
4. **🔍 EVIDENCE-BASED**: Extract exact errors/output before suggesting fixes - show, don't assume
5. **📚 AUTO-LEARN**: Document corrections immediately - turn problems into permanent knowledge
6. **⚡ NO PREMATURE VICTORY**: Task complete = committed + pushed + tested + verified
7. **🚫 NO FAKE CODE**: Build real, functional implementations - no placeholders or demos
8. **📂 FILE PLACEMENT**: Never add files to $PROJECT_ROOT/ without permission - use roadmap/scratchpad_[branch].md
9. **⚠️ MERGE APPROVAL**: User must type "MERGE APPROVED" before any merge-triggering actions
10. **🏃 QUICK REFERENCE**: Use `./run_tests.sh`, `./integrate.sh`, `TESTING=true python` from project root

## 🚨 CRITICAL: MANDATORY BRANCH HEADER PROTOCOL

*Essential for AI context tracking and accurate responses*

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

## Core Principles & Meta-Rules

*Prevents hallucinations - systematic AI collaboration reduces errors and improves code quality ([ACM Human-AI Collaboration Study](https://dl.acm.org/doi/10.1145/3643690.3648236))*

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

🚨 **DELEGATION DECISION MATRIX**: ⚠️ MANDATORY - Before using Task tool for any workflow:
- **Parallelism Test**: ✅ Can subtasks run simultaneously without dependencies?
- **Resource Test**: ✅ System memory < 50% AND < 3 Claude instances running?
- **Overhead Test**: ✅ Agent startup time < estimated task execution time?
- **Specialization Test**: ✅ Task requires expertise current instance lacks?
- **Independence Test**: ✅ Can task complete without frequent coordination?
- ❌ **NEVER delegate sequential workflows** - Execute directly for 10x better performance
- ❌ **NEVER delegate simple command orchestration** - Basic workflows should run in current instance
- 🔍 **Evidence**: Copilot PR #1062 - Direct execution (2 min) vs Task delegation (5+ min timeout)

🚨 **NO ASSUMPTIONS ABOUT RUNNING COMMANDS**:
- ❌ NEVER explain what a command "will do" when it's already running
- ✅ ALWAYS wait for actual command output and results
- **Pattern**: User says "X is running..." → Wait for actual results, don't speculate

🚨 **SOLO DEVELOPER CONTEXT**: Never give enterprise advice to solo developers
   - ✅ **Solo Approach**: "Test it on real PRs" vs complex validation frameworks
   - ✅ **Practical Testing**: Direct usage validation vs enterprise testing infrastructure
   - ✅ **Simple Solutions**: Focus on "does it work?" rather than distributed systems thinking
   - ❌ **NEVER suggest**: Complex testing frameworks, enterprise validation, or infrastructure
   - ❌ **NEVER apply**: Enterprise patterns to solo development workflows
   - **User Context**: Solo developer needs practical, simple approaches that work immediately
   - **Evidence**: User feedback "i am a solo developer and not enterprise. stop giving me enterprise advice"

🚨 **NO FAKE IMPLEMENTATIONS**: ⚠️ MANDATORY
- ❌ NEVER create files with "# Note: In the real implementation" comments
- ❌ NEVER write placeholder code that doesn't actually work
- ❌ NEVER duplicate systematic protocols that already exist in other .md files
- ✅ ALWAYS audit existing commands before writing new implementations
- ✅ ALWAYS build real, functional code that works immediately
- **Pattern**: Real implementation > No implementation > Fake implementation
- **Evidence**: PR #820 - 563+ lines of fake code removed

⚠️ **COMMAND COMPOSITION ARCHITECTURE DOCUMENTATION**: When sophisticated functionality is documented without shell scripts:
- ✅ **CLARIFY IMPLEMENTATION APPROACH**: Add explicit note about command composition architecture
- ✅ **EXPLAIN NATURAL LANGUAGE EXECUTION**: Document that Claude executes markdown-defined workflows
- ✅ **PREVENT FAKE IMPLEMENTATION CONCERNS**: Clear architectural rationale prevents confusion
- ❌ **NEVER leave sophisticated documentation without implementation explanation**
- 🔍 **Evidence**: Session 2025-01-29 - push.sh deletion required architectural clarification
- **Pattern**: "Implementation: This command uses Claude Code's command composition architecture..."

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

🚨 **SLASH COMMAND ARCHITECTURE UNDERSTANDING**: ⚠️ CRITICAL - DO NOT FORGET
- **SLASH COMMANDS ARE NOT DOCUMENTATION - THEY ARE EXECUTABLE COMMANDS**
- **`.claude/commands/*.md` = EXECUTABLE PROMPT TEMPLATES that Claude reads and executes**
- **`.claude/commands/*.py` = EXECUTABLE SCRIPTS that run in local environment**
- **When user types `/pushl` → Claude reads `pushl.md` → Executes the implementation**
- **Command discovery**: CLI scans directories, filename becomes command name (`pushl.md` → `/pushl`)
- **$ARGUMENTS placeholder**: Inject user arguments into command templates
- **Universal composition**: Commands combine through semantic understanding
- **Two types**: Cognitive (semantic understanding) vs Operational (protocol enforcement)
- 🔍 **Evidence**: Research shows this is executable documentation architecture
- ❌ **NEVER treat .md files as documentation** - they are executable instructions for Claude
- ✅ **ALWAYS remember**: Slash commands execute content, they don't document it

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

*Memory MCP integration ([MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)) + 2500+ lines documented learnings = continuous improvement*

🚨 **AUTO-LEARN**: Document corrections immediately when: User corrects | Self-realizing | Something fails | Pattern repeats

**Process**: Detect → Analyze → Document → Apply → Persist to Memory MCP
**/learn Command**: `/learn [optional: specific learning]`

## Advanced Patterns

*Based on 100+ production examples + context engineering research ([Context Engineering Guide](https://www.philschmid.de/context-engineering))*

🚨 **CONTEXT ENGINEERING**: Keep concise - CLAUDE.md prepended to every prompt (impacts cost/performance) ([Anthropic Long Context Research](https://www.anthropic.com/news/prompting-long-context))
🚨 **DYNAMIC ADAPTATION**: Use Claude to evolve CLAUDE.md as project develops
🚨 **MEMORY INTEGRATION**: Turn problems into permanent improvements via Memory MCP ([Model Context Protocol](https://modelcontextprotocol.io/introduction))

## Claude Code Specific Behavior

1. **Directory Context**: Operates in worktree directory shown in environment ([Claude Code Overview](https://docs.anthropic.com/en/docs/claude-code/overview))
2. **Test Execution**: Use `TESTING=true python` from project root
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
11. 🚨 **COMPREHENSIVE REVIEW COMMENT EXTRACTION**: ⚠️ MANDATORY - When executing `/review` command:
    - ✅ **Extract ALL Comments**: Use multiple GitHub API endpoints to capture complete conversation
      - `gh pr view --comments` (general comments)
      - `gh api repos/owner/repo/pulls/PR#/comments` (inline review comments)
      - `gh api repos/owner/repo/pulls/PR#/reviews` (review summaries)
      - Include verification comments, follow-up clarifications, pattern recognition analysis
    - ✅ **Count Verification**: Report total comment count including verification responses
    - ❌ **NEVER claim complete analysis** without extracting verification and follow-up comments
    - 🔍 **Evidence**: Session 2025-01-29 - missed 5+ critical verification comments from CodeRabbit
    - **Pattern**: Incomplete extraction leads to missed implementation gaps and poor review quality
12. 🚨 **IMPLEMENTATION VERIFICATION REQUIREMENT**: ⚠️ MANDATORY - Before claiming any implementation:
    - ✅ **ALWAYS verify file state** using direct file reads after making changes
    - ✅ **NEVER claim implementation** without confirming actual file modifications
    - ✅ **Use commit evidence** to back all resolution claims with specific technical details
    - ❌ **NEVER rely on intent** - verify actual implementation vs claimed changes
    - 🔍 **Evidence**: Session 2025-01-29 - CodeRabbit verification caught false implementation claims
    - **Pattern**: "Claimed to add X but file verification shows Y" indicates verification failure
    - **Anti-Pattern**: Making resolution claims without verifying actual file state changes

### 🔧 GitHub MCP Setup
**Token**: Set in `claude_mcp.sh` line ~247 via `export GITHUB_TOKEN="your_token_here"` ([GitHub MCP Integration](https://github.com/modelcontextprotocol/servers))
**Private Repos**: Use direct functions only | `mcp__github-server__get_pull_request()`

## Orchestration System

*Multi-agent task delegation ([Azure AI Agent Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)) - See `.claude/commands/orchestrate.md` for full docs*

**Basic Usage**: `/orch [task]` → Creates agents in tmux sessions → Monitor with `/orch status`
**Critical Rule**: ❌ NEVER execute /orch tasks yourself - ALWAYS delegate to agents
**Cost**: $0.003-$0.050/task | Requires Redis coordination
**Completion**: Task complete = PR created + pushed + verified link

## Project Overview

Your Project = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack**: Python 3.11/Flask ([Flask Documentation](https://flask.palletsprojects.com/))/Gunicorn | Gemini API ([Google AI Documentation](https://ai.google.dev/gemini-api/docs)) | Firebase Firestore ([Firebase Docs](https://firebase.google.com/docs/firestore)) | Vanilla JS/Bootstrap | Docker/Cloud Run ([Google Cloud Run](https://cloud.google.com/run/docs))

**Docs**: → `.cursor/rules/project_overview.md` (full details)
- **AI Assistant Guide**: → `$PROJECT_ROOT/README_FOR_AI.md` (CRITICAL system architecture)
- **Code Review**: → `$PROJECT_ROOT/CODE_REVIEW_SUMMARY.md` (file-by-file analysis)
- **Browser Test Mode**: → `$PROJECT_ROOT/testing_ui/README_TEST_MODE.md`

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

⚠️ **VERIFICATION TOOL ACKNOWLEDGMENT**: When verification tools (CodeRabbit, Cursor, etc.) identify implementation gaps:
- ✅ **ACKNOWLEDGE ACCURACY**: "You were absolutely right" rather than defensive responses
- ✅ **EXPRESS GRATITUDE**: "Thank you for catching this" - verification improves quality
- ✅ **IMPLEMENT ACTUAL FIXES**: Address identified gaps with verifiable implementations
- ✅ **DOCUMENT IMPROVED PROCESS**: Learn from verification to prevent repeated patterns
- 🔍 **Evidence**: Session 2025-01-29 - positive user response to acknowledgment approach
- **User Preference**: Expects acknowledgment of verification accuracy and actual fixes

**Response Modes**: Default = structured for complex | Direct for simple | Override: "be brief"

**Testing**: Red-green methodology ([Microsoft TDD Research](https://www.microsoft.com/en-us/research/wp-content/uploads/2009/10/Realizing-Quality-Improvement-Through-Test-Driven-Development-Results-and-Experiences-of-Four-Industrial-Teams-nagappan_tdd.pdf)) | Test truth verification | Use ADTs

**Red-Green Protocol** (`/tdd` or `/rg`) ([TDD Systematic Review](https://www.sciencedirect.com/science/article/pii/S0950584916300222)):
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
✅ `from google import genai` | ✅ `client = genai.Client(api_key=api_key)` ([Gemini API Documentation](https://ai.google.dev/gemini-api/docs/quickstart))
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

*94+ test files, AI-enhanced code review improves quality ([AI Code Review Research](https://eleks.com/research/ai-code-review/))*

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
🚨 **NEVER add new files directly to $PROJECT_ROOT/** without explicit user permission
- ✅ If unsure, add content to roadmap/scratchpad_[branch].md instead
- **Exception**: Only when user explicitly requests file creation in $PROJECT_ROOT/

🚨 **Test File Policy**: Add to existing files, NEVER create new test files
- ⚠️ MANDATORY: Always add tests to existing test files that match the functionality
- ❌ NEVER create `test_new_feature.py` - add to `test_existing_module.py` instead

### Browser vs HTTP Testing (🚨 HARD RULE)
**CRITICAL DISTINCTION**: Never confuse browser automation with HTTP simulation ([Web Testing Survey](https://www.researchgate.net/publication/348000478_Survey_of_Testing_Methods_for_Web_Applications))
- 🚨 **testing_ui/**: ONLY real browser automation using **Playwright MCP** (default) or Puppeteer MCP
- 🚨 **testing_http/**: ONLY HTTP requests using `requests` library
- ⚠️ **/testui and /testuif**: MUST use real browser automation (Playwright MCP preferred)
- ⚠️ **/testhttp and /testhttpf**: MUST use HTTP requests | NO browser automation

### Browser Test Execution Protocol (🚨 MANDATORY)
🚨 **PREFERRED**: Playwright MCP in Claude Code CLI - Accessibility-tree based, AI-optimized ([Playwright vs Puppeteer Comparison](https://www.browserstack.com/guide/playwright-vs-puppeteer))
🚨 **SECONDARY**: Puppeteer MCP for Chrome-specific or stealth testing scenarios

**Commands**: `./run_ui_tests.sh mock --playwright` (default) | `./run_ui_tests.sh mock --puppeteer`
**Test Mode URL**: `http://localhost:8081?test_mode=true&test_user_id=test-user-123`

### Coverage Analysis Protocol (⚠️)
**MANDATORY**: When analyzing test coverage:
1. **ALWAYS use**: `./run_tests.sh --coverage` or `./coverage.sh`
2. **NEVER use**: Manual `coverage run` commands on individual test files
3. **Report source**: Always mention "Coverage from full test suite via run_tests.sh"

## Git Workflow

🚨 **No Main Push**: ✅ `git push origin HEAD:feature` | ❌ `git push origin main` ([Git Branching Best Practices](https://www.researchgate.net/publication/388531640_Git_Branching_and_Release_Strategies))
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

🚨 **GITHUB API PAGINATION PROTOCOL**: ⚠️ MANDATORY - Before ANY GitHub API analysis:
- ✅ **Check total count first**: Use `gh pr view [PR] --json changed_files` to get file count before analysis
- ✅ **Verify pagination**: GitHub API defaults to 30 items per page - always check if more pages exist
- ✅ **Use pagination parameters**: Add `?per_page=100&page=N` for complete results when file count > 30
- ✅ **Sanity check**: If API returns small number but PR shows major changes, investigate pagination
- ✅ **Multiple verification**: Use both API and web interface to cross-check important analysis
- ❌ **NEVER assume**: API returns complete results without verifying pagination and total counts

🚨 **CHALLENGE RESPONSE PROTOCOL**: ⚠️ MANDATORY - When user provides specific evidence:
- ✅ **Immediate re-verification**: Treat user evidence as debugging signal, not personal attack
- ✅ **Methodology review**: Re-check approach when user mentions details not in your analysis
- ✅ **Humble language**: Use "appears to be" until verified through multiple independent sources
- ❌ **NEVER defend**: Wrong analysis - acknowledge error and re-verify immediately

## Environment, Tooling & Scripts

1. **Python venv**: Verify activated before running Python/tests
2. **Python Execution**: ✅ Run from project root | ❌ cd into subdirs
3. **vpython Tests**: `TESTING=true python $PROJECT_ROOT/test_file.py` (from root)
4. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted
5. **Log Files Location**: `/tmp/worldarchitectai_logs/[branch-name].log`

**Test Commands**: → `.cursor/rules/validation_commands.md`

## Operations Guide

### Memory MCP Usage
**Search Knowledge**: `mcp__memory-server__search_nodes("query")` → Find existing before creating ([Knowledge Management Systems](https://www.researchgate.net/publication/347521808_Knowledge_Management_Systems_Development_and_Implementation_A_systematic_Literature_Review))
**Create Knowledge**: `mcp__memory-server__create_entities([{name, entityType, observations}])`
**Pattern**: Search first → Create if new → Add observations to existing → Build relationships

### Task Agent Patterns
**⚠️ Token Cost**: Each agent loads ~50k+ tokens. See `.claude/commands/parallel-vs-subagents.md` for alternatives.
**When to Spawn**: Complex workflows | Different directories | Long operations (>5 min)
**When NOT to Spawn**: Simple searches | Independent file ops | Data gathering (<30s each)
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
**Process**: Extract evidence → Analyze → Verify → Fix | Trace: Backend → API → Frontend ([Systematic Debugging Review](https://www.sciencedirect.com/science/article/pii/S0164121222001303))
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
**MANDATORY**: Include full GitHub URL - Format: "PR #123: https://github.com/jleechan2015/your-project.com/pull/123"

### PR Description Protocol (⚠️ MANDATORY)
**PR descriptions must reflect complete delta vs origin/main, not just recent work**:
- ✅ Use `git diff --stat origin/main...HEAD` to get comprehensive change summary
- ✅ Analyze actual file changes, additions, deletions vs main branch
- ❌ NEVER describe only latest commits or recent work

## Project-Specific

**🔍 Project Evidence**:
- **Flask Implementation**: `$PROJECT_ROOT/main.py`, `$PROJECT_ROOT/main_parallel_dual_pass.py` - Actual Flask application files
- **Python Setup**: `requirements.txt`, `venv/` directory, virtual environment confirmed active
- **AI Integration**: `$PROJECT_ROOT/gemini_service.py`, `$PROJECT_ROOT/prompts/` directory - Real AI implementation

### Flask: SPA route for index.html | Hard refresh for CSS/JS | Cache-bust in prod
**Reference**: `$PROJECT_ROOT/static/index.html`, `$PROJECT_ROOT/routes/` - Actual SPA architecture

### Python: venv required | Source .bashrc after changes | May need python3-venv
**Reference**: Project uses virtual environment, `TESTING=true python` commands throughout

### AI/LLM: Detailed prompts crucial | Critical instructions first | Long prompts = fatigue
**Reference**: `$PROJECT_ROOT/prompts/master_directive.md`, extensive prompt engineering in project

### Workflow: Simple-first | Tool fail = try alternative | Main branch = recovery source
**Reference**: Git workflow patterns evidenced in 50+ PRs and branch management protocols

## Quick Reference

**🔍 Evidence of Value**: Quick reference commands used in 50+ PRs and sessions - frequently accessed patterns.
- **Code Pointers**: All commands point to actual executable scripts in project root
- **Usage Pattern**: Referenced in debugging sessions, commit messages, and PR workflows

- **Test**: `TESTING=true python $PROJECT_ROOT/test_file.py` (from root) - Real command from project testing setup
- **Integration**: `TESTING=true python3 $PROJECT_ROOT/test_integration/test_integration.py` - Actual integration test path
- **New Branch**: `./integrate.sh` - Existing shell script for branch management
- **All Tests**: `./run_tests.sh` - Production test runner script
- **Deploy**: `./deploy.sh` or `./deploy.sh stable` - Actual deployment commands

## Advanced Workflow Patterns (Solo Developer Optimized)

### Command Composition for Efficiency
- **Planning First**: Ask Claude to make a plan before coding, confirm before execution - reduces iteration cycles
- **Quality Modifiers**: Use enhancement phrases - "Prioritize essential features and refine iteratively" - better initial results
- **Progressive Refinement**: Build → Test → Refine cycle with memory integration - MVP-compatible iteration

### Evidence-Based Problem Solving
- **Evidence Hierarchy**: Code/errors > Documentation > General patterns > Speculation ([Evidence-Based Debugging](https://www.sciencedirect.com/science/article/pii/S0164121222001303)) - faster debugging
- **Verification Protocol**: Extract evidence → Analyze → Verify → Fix → Document - systematic but lightweight
- **Learning Integration**: Document corrections immediately when patterns emerge - build personal knowledge repository

## Additional Documentation

**🔍 File Evidence**: All referenced files exist and contain substantial content (2500+ lines total)

- **Technical Lessons**: → `.cursor/rules/lessons.mdc` - 2500+ lines of documented learnings from actual corrections and incidents
- **Cursor Config**: → `.cursor/rules/rules.mdc` - Cursor IDE-specific configuration patterns
- **Examples**: → `.cursor/rules/examples.md` - Practical implementation examples from project history
- **Commands**: → `.cursor/rules/validation_commands.md` - Tested command patterns for development workflows

## API Timeout Prevention (🚨)

*CLAUDE.md prepended to every prompt - size impacts cost/performance*

**MANDATORY**: Prevent API timeouts:
- **Edits**: MultiEdit with 3-4 max | Target sections, not whole files
- **Thinking**: 5-6 thoughts max | Concise | No unnecessary branching
- **Responses**: Bullet points | Minimal output | Essential info only
- **Tools**: Batch calls | Smart search (Grep/Glob) | Avoid re-reads
- **Complex tasks**: Split across messages | Monitor server load

---

## Research References & Documentation

**External Research Sources**:
- **Anthropic Best Practices**: [Claude Code Engineering Guidelines](https://www.anthropic.com/engineering/claude-code-best-practices)
- **Community Evidence**: [CLAUDE.md Analysis](https://apidog.com/blog/claude-md/), [Implementation Guide](https://empathyfirstmedia.com/claude-md-file-claude-code/)
- **Context Engineering**: [Advanced Prompt Optimization](https://www.philschmid.de/context-engineering)
- **Community Analysis**: 100+ production CLAUDE.md examples analyzed from open source projects

**Internal Documentation** (2500+ lines total):
- **Technical Lessons**: → `.cursor/rules/lessons.mdc` - Documented corrections and incidents
- **Cursor Config**: → `.cursor/rules/rules.mdc` - IDE-specific patterns
- **Examples**: → `.cursor/rules/examples.md` - Implementation examples
- **Commands**: → `.cursor/rules/validation_commands.md` - Tested workflow patterns

**Implementation Evidence**:
- **Memory MCP**: `mcp__memory-server__create_entities`, `mcp__memory-server__search_nodes`
- **Orchestration**: `.claude/commands/orchestrate.md`, `orchestration/` scripts
- **Testing**: `./run_tests.sh`, `./run_ui_tests.sh`, 94+ test files
- **Project Files**: `$PROJECT_ROOT/main.py`, `requirements.txt`, `venv/` setup verified
# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on Your Project**

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

## Project Overview

Your Project = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack**: Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

**Docs**: → `.cursor/rules/project_overview.md` (full details)
- Documentation map → `.cursor/rules/documentation_map.md`
- Quick reference → `.cursor/rules/quick_reference.md`
- Progress tracking → `roadmap/templates/progress_tracking_template.md`
- Directory structure → `/directory_structure.md`
- **AI Assistant Guide**: → `$PROJECT_ROOT/README_FOR_AI.md` (CRITICAL system architecture for AI assistants)
- **📋 MVP Site Architecture**: → `$PROJECT_ROOT/README.md` (comprehensive codebase overview)
- **📋 Code Review & File Responsibilities**: → `$PROJECT_ROOT/CODE_REVIEW_SUMMARY.md` (detailed file-by-file analysis)
- **Browser Test Mode**: → `$PROJECT_ROOT/testing_ui/README_TEST_MODE.md` (How to bypass auth in browser tests)

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
- 🔍 Evidence: PR #818 - Replaced fragile `.replace('/tests', '')` with proper directory navigation

🚨 **DYNAMIC AGENT ASSIGNMENT**: Replace hardcoded agent mappings with capability-based selection
- ❌ NEVER use patterns like `if "test" in task: return "testing-agent"`
- ✅ Use capability scoring with load balancing
- 🔍 Evidence: PR #873 removed 150+ lines of hardcoded mappings

🚨 **API GATEWAY BACKWARD COMPATIBILITY**: API gateways MUST maintain exact contract during architectural changes
- ✅ Maintain identical HTTP status codes, response formats, validation behavior
- ✅ Fix API gateway layer when tests fail after architectural changes
- 🔍 Evidence: PR #1038 - Fixed Flask layer to maintain API contract instead of changing tests
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
- **Evidence**: PR #1127 - Created unnecessary automation/simple_pr_batch_v2.sh instead of direct edit
- **Anti-Pattern**: "Let me create a new version..." → Should be "Let me edit the existing file..."

🚨 **PR Review Verification**: Always verify current state before applying review suggestions
- ✅ Check if suggested fix already exists in code | Read actual file content before changes
- 🔍 Evidence: PR #818 - Copilot suggested fixing 'string_type' that was already correct

⚠️ **PR COMMENT PRIORITY**: Address review comments in strict priority order
1. **CRITICAL**: Undefined variables, inline imports, runtime errors
2. **HIGH**: Bare except clauses, security issues
3. **MEDIUM**: Logging violations, format issues
4. **LOW**: Style preferences, optimizations
- 🔍 Evidence: PR #873 review - fixed critical inline imports first

🚨 **BOT COMMENT FILTERING**: ⚠️ MANDATORY - Ignore specific bot patterns when explicitly overridden
- ❌ **IGNORE**: Bot comments about `--dangerously-skip-permissions` when user explicitly chose to keep it
- ✅ **ACKNOWLEDGE**: Respond but indicate user decision to retain flag
- **Evidence**: Memory automation testing requires bypass permissions for development/testing scenarios

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
- 🔍 Evidence: PR #780 with real conflicts revealed false negative bug that clean PRs missed
**Test Assertions**: ⚠️ MANDATORY - Must match actual validation behavior exactly
- 🔍 Evidence: PR #818 - MBTI test checked .lower() but validation only does .strip()
**Exception Specificity**: ✅ Use specific exception types in tests (ValidationError, not Exception)
- 🔍 Evidence: PR #818 - Improved test precision with Pydantic's ValidationError
**Rules**: ✅ Run before task completion | ❌ NEVER skip without permission | ✅ Only use ✅ after real results

### Safety & Security
❌ Global `document.addEventListener('click')` without approval | Test workflows after modifications
Document blast radius | Backups → `tmp/` | ❌ commit if "DO NOT SUBMIT" | Analysis + execution required

### File Deletion Impact Protocol (🚨 CRITICAL)
**Before deleting established files**: Run comprehensive reference search to avoid cascading cleanup
- `grep -r "<filename>" .` for code references | `find . -name "*.md" -exec grep -l "<filename>" {} \;` for docs
- Check: scripts, tests, configuration, imports, error messages, user guidance
- **Budget 2-3x normal effort** for large file deletions due to cleanup cascade
- **Evidence**: PR #722 required 36-file cleanup after deleting copilot.sh (695 lines)

### Scope Management Protocol (⚠️ MANDATORY)
**Distinguish rewrite vs consolidation** to set proper effort expectations
- **Consolidation**: Reorganizing existing functionality (preserve files, move/rename)
- **Rewrite**: Replacing with new implementation (delete old, extensive cleanup needed)
- **Evidence**: PR #722 called "consolidation" but became Option 3 rewrite with extensive cleanup

### File Placement Rules (🚨 HARD RULE)
🚨 **NEVER add new files directly to $PROJECT_ROOT/** without explicit user permission
- ❌ NEVER create test files, documentation, or scripts directly in $PROJECT_ROOT/
- ✅ If unsure, add content to roadmap/scratchpad_[branch].md instead

🚨 **Test File Policy**: Add to existing files, NEVER create new test files
- ⚠️ MANDATORY: Always add tests to existing test files that match the functionality
- 🔍 Evidence: PR #818 - CodeRabbit caught test_cache_busting_red_green.py violation
🚨 **Code Review**: Check README.md and CODE_REVIEW_SUMMARY.md before $PROJECT_ROOT/ changes

### Repository Separation
**Pattern**: Specialized systems → Dedicated repos | **Benefits**: Cleaner automation, focused workflows

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
- **Evidence**: Prevents autopilot execution errors that waste user time

🚨 **COMMAND FAILURE TRANSPARENCY** (⚠️ MANDATORY): When user commands fail unexpectedly:
- ✅ Immediately explain what failed and why | Show system messages/errors received
- ✅ Explain resolution approach | Ask preference for alternatives (merge vs rebase, etc.)
- **Pattern**: Command fails > Explain > Show options > Get preference > Execute
- **Evidence**: Silent git merge resolution leads to "ignored comment" perception

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
3. **Automation Setup Scripts**: Single setup script with validation, logging, health checks for production systems
   - **Pattern**: Prerequisites check → Logging setup → Service configuration → Validation → Health check
   - 🔍 **Evidence**: setup_automation.sh successfully deployed complete cron job + monitoring system
4. **Python Execution**: ✅ Run from project root | ❌ cd into subdirs
5. **vpython Tests**: ⚠️ "run all tests" → `./run_tests.sh` | ⚠️ Test fails → fix immediately or ask user
   - ✅ `TESTING=true vpython $PROJECT_ROOT/test_file.py` (from root)
6. 🚨 **Test Compliance**: → See "Testing Protocol" section
7. **Tool Failure**: Try alternative after 2 fails | Fetch from main if corrupted
8. **Web Scraping**: Use full-content tools (curl) not search snippets
9. **Log Files Location**:
   - ✅ **Server logs are in `/tmp/your-project.com/`** with branch isolation and service-specific files
   - ✅ **Branch-specific structure**: `/tmp/your-project.com/[branch-name]/`
   - ✅ **Service logs**: `/tmp/your-project.com/[branch]/[service-name].log`
   - ✅ **Flask server**: `/tmp/your-project.com/[branch]/flask-server.log`
   - ✅ **MCP server**: `/tmp/your-project.com/[branch]/mcp-server.log`
   - ✅ **Test server**: `/tmp/your-project.com/[branch]/test-server.log`
   - ✅ **Log commands**: `tail -f /tmp/your-project.com/[branch]/[service].log` for real-time monitoring
   - ✅ **Search logs**: `grep -i "pattern" /tmp/your-project.com/[branch]/[service].log`
   - ✅ **Find current log**: `git branch --show-current` then check corresponding log file

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
**Unnecessary File Creation**: ❌ NEVER create new files when editing existing ones suffices | Evidence: automation/simple_pr_batch_v2.sh creation instead of direct edit
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
**🧠 Cognitive Commands** (Semantic Composition): `/think`, `/arch`, `/debug`, `/learn`, `/analyze`, `/fix`, `/perp`, `/research`
**⚙️ Operational Commands** (Protocol Enforcement): `/headless`, `/handoff`, `/orchestrate` - Modify execution environment
**🔧 Tool Commands** (Direct Execution): `/execute`, `/test`, `/pr` - Direct task execution

### Critical Enforcement
🚨 **SLASH COMMAND PROTOCOL RECOGNITION**: ⚠️ MANDATORY - Before processing ANY slash command:
- ✅ **Recognition Phase**: Scan "/" → Identify command type → Look up workflow in `.claude/commands/[command].md`
- ✅ **Execution Phase**: Follow COMPLETE documented workflow → No partial execution allowed
- ❌ NEVER treat slash commands as content suggestions - they are execution mandates
- **Evidence**: PR #938 - Failed `/pr` protocol by stopping after Execute instead of continuing to Push→Copilot→Review

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
- 🔍 Evidence: CodeRabbit data loss warning prevented silent corruption in backup script

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
- **Evidence**: User feedback "pr desc is wrong. We should see the delta of the PR vs main"


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
