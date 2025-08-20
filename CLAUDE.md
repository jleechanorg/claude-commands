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

**Core Philosophy:** Lead with architectural thinking, follow with tactical execution. Write code as senior architect, not junior contributor. Combine multiple perspectives (security, performance, maintainability).

**Standards:** Be specific, actionable, context-aware. Prefer modular, reusable patterns. Anticipate edge cases. Each implementation better than the last through systematic learning.

## 🚨 CRITICAL: /CEREBRAS HYBRID CODE GENERATION PROTOCOL

**🚀 SPEED**: /cerebras generates code 19.6x faster (500ms vs 10s) using Cerebras infrastructure

**WORKFLOW - Claude as ARCHITECT, Cerebras as BUILDER:**
1. Claude analyzes requirements and creates detailed specifications
2. Claude generates precise, structured prompts with full context
3. /cerebras executes the code generation at high speed
4. Claude verifies and integrates the generated code
5. Document decision in `docs/{branch_name}/cerebras_decisions.md`

**USE /CEREBRAS FOR:** Well-defined code generation, boilerplate, templates, unit tests, algorithms, documentation, repetitive patterns

**USE CLAUDE FOR:** Understanding existing code, debugging, refactoring, security-critical implementations, architectural decisions, complex integrations

## 🚨 CRITICAL: NEW FILE CREATION PROTOCOL

**🚨 ZERO TOLERANCE:** All new file requests must be submitted in NEW_FILE_REQUESTS.md with description of all places searched for duplicate functionality

**REQUIREMENTS:**
- ❌ NO file creation without NEW_FILE_REQUESTS.md entry
- 🔍 SEARCH FIRST: Document checking `/utils/`, `/helpers/`, `/lib/`, modules, configs
- ✅ JUSTIFY: Why editing existing files won't suffice
- 📝 INTEGRATE: How file connects to existing codebase

## 🚨 CRITICAL: FILE PLACEMENT PROTOCOL - ZERO TOLERANCE

**🚨 NEVER CREATE FILES IN PROJECT ROOT**: ⚠️ MANDATORY - Root directory hygiene
- ❌ **FORBIDDEN**: Creating ANY new .py, .sh, .md files in project root
- ❌ **FORBIDDEN**: Test files in root - ALL tests go in appropriate test directories
- ❌ **FORBIDDEN**: Scripts in root - use `scripts/` directory for ALL scripts
- ✅ **REQUIRED**: Python files → `mvp_site/` or module directories
- ✅ **REQUIRED**: Shell scripts → `scripts/` directory  
- ✅ **REQUIRED**: Test files → `mvp_site/tests/` or module test directories
- ✅ **REQUIRED**: Documentation → `docs/` or module-specific docs
- **Pattern**: Root = Configuration only (deploy.sh, run_tests.sh, etc.)
- **Anti-Pattern**: memory_backup_*.sh in root instead of scripts/
- **Violation Count**: 6+ memory backup scripts incorrectly placed in root

**EXISTING ROOT FILES**: Only established project scripts remain in root for backward compatibility. NO NEW ADDITIONS.

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

🚨 **PRE-ACTION CHECKPOINT:** Before ANY action: "Does this violate CLAUDE.md rules?"

🚨 **PRE-WRITE CHECKPOINT**: Before ANY Write tool usage, ask:
1. "Does this violate NEW FILE CREATION PROTOCOL?"
2. "Have I searched existing tools first?"
3. "Do I need NEW_FILE_REQUESTS.md entry?"

**🎯 Memory Aid:** The Write tool checkpoint prevents emergency-driven file creation, making protocol compliance automatic like greeting/header habits.

**Pattern**: Write usage → Check protocol → Search existing → Document necessity → Then create
**Anti-Pattern**: Problem urgency → Create file immediately → Skip all protocols

🚨 **DUAL COMPOSITION ARCHITECTURE**: Two command processing mechanisms
- **Cognitive** (/think, /arch, /debug): Universal Composition (natural semantic understanding)
- **Operational** (/headless, /handoff, /orchestrate): Protocol Enforcement (mandatory workflow execution)
- ✅ Scan "/" prefixes → classify command type → trigger required workflows
- ❌ NEVER process operational commands as regular tasks without workflow setup
- **Pattern**: Cognitive = semantic composition, Operational = protocol enforcement

🚨 **NO FALSE ✅:** Only use ✅ for 100% complete/working. Use ❌ ⚠️ 🔄 for partial.

🚨 **NO PREMATURE VICTORY DECLARATION:** Task completion requires FULL verification
- ❌ NEVER declare success on intermediate steps
- ✅ ONLY declare success when ALL steps verified complete

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

🚨 **SOLO DEVELOPER CONTEXT**: Never give enterprise advice to solo developers
- ✅ **Solo Approach**: "Test it on real PRs" vs complex validation frameworks
- ❌ **NEVER suggest**: Complex testing frameworks, enterprise validation, infrastructure

🚨 **NO ASSUMPTIONS ABOUT RUNNING COMMANDS:** Wait for actual results, don't speculate

## 🚨 CRITICAL IMPLEMENTATION RULES

🚨 **NO FAKE IMPLEMENTATIONS:** ⚠️ MANDATORY - Always audit existing functionality first
- ❌ NEVER create placeholder/demo code or duplicate existing protocols
- ✅ ALWAYS build real, functional code

🚨 **ORCHESTRATION OVER DUPLICATION:** ⚠️ MANDATORY
- Orchestrators delegate to existing commands, never reimplement functionality
- ✅ Use existing /commentreply, /pushl, /fixpr rather than duplicating logic

🚨 **NO OVER-ENGINEERING:** Ask "Can LLM handle this naturally?" before building parsers/analytics

🚨 **NO UNNECESSARY EXTERNAL APIS:** Try direct implementation before adding dependencies

🚨 **USE LLM CAPABILITIES:** 
- ❌ NEVER suggest keyword matching, regex patterns, rule-based parsing
- ✅ ALWAYS leverage LLM's natural language understanding

## 🚨 CRITICAL SYSTEM UNDERSTANDING

🚨 **SLASH COMMAND ARCHITECTURE:** ⚠️ CRITICAL
- `.claude/commands/*.md` = EXECUTABLE PROMPT TEMPLATES
- **Flow:** User types `/pushl` → Claude reads `pushl.md` → Executes implementation
- ❌ NEVER treat .md files as documentation - they are executable instructions

🚨 **UNIVERSAL COMPOSITION PATTERNS:** ⚠️ MANDATORY - Two distinct execution types
- **Universal Composition:** `/copilot` → `/execute` → orchestrates other commands naturally
- **Embedded Implementation:** `/commentcheck` embeds functionality directly
- ✅ ALWAYS test actual execution to verify pattern type
- ❌ NEVER assume cross-command references are just documentation

🚨 **NEVER SIMULATE INTELLIGENCE:** 
- ❌ NEVER create Python functions that simulate Claude's responses with templates
- ✅ ALWAYS invoke actual Claude for genuine response generation

🚨 **EVIDENCE-BASED APPROACH:** 
- ✅ Extract exact error messages/code snippets before analyzing
- 🔍 All claims must trace to specific evidence

🚨 **MANDATORY FILE ANALYSIS PROTOCOL:** ⚠️ CRITICAL
- ❌ NEVER use Bash commands (cat, head, tail) for file content analysis
- ✅ ALWAYS use Read tool for examining file contents

🚨 **INVESTIGATION TRUST HIERARCHY:** ⚠️ MANDATORY - When findings conflict:
**Order:** Configuration evidence > Logical analysis > User input > Agent claims

🚨 **TERMINAL SESSION PRESERVATION:** ⚠️ MANDATORY
- ❌ NEVER use `exit 1` that terminates user's terminal
- ✅ ALWAYS use graceful error handling

## 🚨 QUALITY ASSURANCE PROTOCOL

**ZERO TOLERANCE:** Cannot declare "COMPLETE" without following ALL steps

### Evidence Requirements (⚠️ MANDATORY)
- **Test Matrix:** Document ALL user paths before testing
- **Screenshots:** For EACH test matrix cell with exact path labels
- **Adversarial Testing:** Actively try to break fixes
- **Format:** "✅ [Claim] [Evidence: screenshot1.png]"

## Claude Code Behavior

1. **Directory Context:** Operates in worktree directory shown in environment
2. **Test Execution:** Use `TESTING=true vpython` from project root
3. **Gemini SDK:** `from google import genai` (NOT `google.generativeai`)
4. **Path Conventions:** Always use `~` instead of hardcoded user paths
5. 🚨 **DATE INTERPRETATION:** Run `date "+%Y-%m-%d"` to get current date
   - Format: YYYY-MM-DD
   - Human-readable: `date "+%B %d, %Y"`
   - Always derive date at runtime by executing these commands (no hardcoded dates)
6. 🚨 **PUSH VERIFICATION:** ⚠️ ALWAYS verify push success after every `git push`
7. 🚨 **PR STATUS:** OPEN = WIP | MERGED = Completed | CLOSED = Abandoned
8. 🚨 **PLAYWRIGHT MCP DEFAULT:** ⚠️ MANDATORY - Use Playwright MCP for browser automation (headless mode)
9. 🚨 **SCREENSHOT LOCATION:** All screenshots must be saved to `docs/` directory
10. 🚨 **GITHUB TOOL PRIORITY:** GitHub MCP tools primary, `gh` CLI as fallback
11. 🚨 **SERENA MCP PRIORITY:** Serena MCP for semantic operations, standard file tools as fallback
12. 🚨 **MEMORY ENHANCEMENT:** For `/think`, `/learn`, `/debug`, `/plan`, `/execute`, `/pr` - search Memory MCP first
13. 🚨 **FILE CREATION PREVENTION:** ⚠️ MANDATORY
    - ❌ FORBIDDEN: Creating `_v2`, `_new`, `_backup`, `_temp` files
    - ✅ REQUIRED CHECK: "Can I edit an existing file instead?"

### GitHub MCP Setup
**Token:** Set in `claude_mcp.sh` line ~247 via `export GITHUB_TOKEN="<token>"`

🚨 **GITHUB API LIMITATIONS:**
- ❌ Cannot approve own PRs via API - use general issue comments instead
- **Threading:** Review comments support threading, issue comments don't

## Orchestration System

🚨 **AGENT OPERATION:**
**System:** tmux sessions with dynamic task agents managed by Python monitor
**Startup:** `./claude_start.sh` auto-starts | Manual: `./orchestration/start_system.sh start`
**CRITICAL:** ❌ NEVER execute orchestration tasks yourself | ✅ ALWAYS delegate to agents

🚨 **ORCHESTRATION DIRECT EXECUTION PREVENTION:** ⚠️ MANDATORY
- **Hard Stop:** "/orch" prefix → immediate tmux orchestration delegation, NO exceptions
- **Mental Model:** "/orch" = "create tmux agent to do this"

🚨 **CONVERGE AUTONOMY PRESERVATION**: ⚠️ MANDATORY HARD STOP PROTOCOL
- **Hard Stop Pattern**: Input scan for "/converge" → autonomous execution until goal achieved, NO stopping for approval
- **Mental Model**: "/converge" = "set and forget until complete", NEVER "/converge" = "step-by-step approval system"
- **Zero Exception Rule**: /converge NEVER stops for user input unless max iterations reached or unrecoverable error
- **CRITICAL**: Progress reporting ≠ stopping for approval. Report progress but continue autonomously
- **Autonomy Boundary**: Once /converge starts, zero user intervention until 100% goal achievement or limits

🚨 **ABSOLUTE BRANCH ISOLATION:** ⚠️ MANDATORY - NEVER LEAVE CURRENT BRANCH
- ❌ FORBIDDEN: `git checkout`, `git switch`, or any branch switching
- ✅ MANDATORY: Stay on current branch - delegate everything else to agents

## Project Overview

WorldArchitect.AI = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack:** Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

**Key Docs:**
- **AI Assistant Guide:** `mvp_site/README_FOR_AI.md` (CRITICAL system architecture)
- **MVP Architecture:** `mvp_site/README.md` (comprehensive overview)
- **Code Review:** `mvp_site/CODE_REVIEW_SUMMARY.md` (detailed analysis)

## Core Principles

**Work Approach:** Clarify before acting | User instructions = law | Focus on primary goal

**Testing:** Red-green methodology (`/tdd` or `/rg`): Write failing tests → Confirm fail → Minimal code to pass → Refactor

🚨 **TESTING LEVELS:** Component ≠ Integration ≠ System. Test what you claim.

## Development Guidelines

### Code Standards
**Principles:** SOLID, DRY | **Templates:** Use existing patterns | **Validation:** `isinstance()` checks
**Constants:** Module-level (>1x) or constants.py (cross-file) | **Imports:** Module-level only, NO inline/try-except
**Path Computation:** ✅ Use `os.path.dirname()`, `os.path.join()`, `pathlib.Path` | ❌ NEVER use `string.replace()` for paths

🚨 **DYNAMIC AGENT ASSIGNMENT:** Replace hardcoded agent mappings with capability-based selection
- ❌ NEVER use patterns like `if "test" in task: return "testing-agent"`
- ✅ Use capability scoring with load balancing

🚨 **API GATEWAY BACKWARD COMPATIBILITY:** Maintain exact contract during architectural changes

### Development Practices
`tempfile.mkdtemp()` for test files | Verify before assuming | ❌ unsolicited refactoring
**Logging:** ✅ `import logging_util` | ❌ `import logging` | Use project's unified logging

🚨 **SUBPROCESS SECURITY:** ⚠️ MANDATORY - All subprocess calls must be secure
- ✅ ALWAYS use `shell=False, timeout=30` for security
- ❌ NEVER use shell=True with user input - shell injection risk
- ✅ EXPLICIT error handling - capture stderr and raise specific exceptions
- **Pattern:** `subprocess.run(["cmd"], shell=False, timeout=30, check=True)`

🚨 **IMPORT STANDARDS:** ⚠️ MANDATORY - Module-level imports only
- ❌ NEVER use inline imports inside functions
- ❌ NEVER use try-catch imports for optional dependencies
- ✅ ALWAYS import at module level - fail fast if missing
- **Pattern:** Handle optionality in logic, not imports

### Gemini SDK
✅ `from google import genai` | ✅ `client = genai.Client(api_key=api_key)`
Models: `gemini-2.5-flash` (default), `gemini-1.5-flash` (test)
🚨 **WARNING:** See "NO UNNECESSARY EXTERNAL APIS" rule before using Gemini

🚨 **FILE EDITING PROTOCOL:** ⚠️ MANDATORY
- ❌ NEVER create: `file_v2.sh`, `file_backup.sh` when editing existing file
- ✅ ALWAYS edit existing files in place using Edit/MultiEdit tools
- ✅ Git handles safety - no manual backup files needed

### Testing Protocol

🚨 **ZERO TOLERANCE:** Run ALL tests, fix ALL failures. Commands: `./run_tests.sh` | `./run_ui_tests.sh mock`

🚨 **CI SIMULATION BY DEFAULT:** Tests simulate CI environment to catch issues early
- **Default:** `./run_tests.sh` (CI simulation)
- **Local Mode:** `./run_tests.sh --no-ci-sim`

🚨 **NUANCED TEST SKIP POLICY:** ⚠️ MANDATORY
- ✅ **LEGITIMATE:** Missing external dependencies, CI limitations - use `self.skipTest()`
- ❌ **FORBIDDEN:** Implementation avoidance, mockable dependencies - fix instead

🚨 **COMPREHENSIVE MOCKING FIRST:** Mock before skip, skip only when mocking impossible

### File & Testing Rules
**File Placement:** No new files in `mvp_site/` without permission. Add tests to existing test files.

**Browser vs HTTP:** `/testui` = Playwright MCP + Mock | `/testuif` = Playwright + Real APIs | `/testhttp` = HTTP requests + Mock | `/testhttpf` = HTTP + Real APIs

**Browser Tests:** Playwright MCP preferred (headless mode). Test URL: `http://localhost:8081?test_mode=true&test_user_id=test-user-123`

**Coverage:** Use `./run_tests.sh --coverage` or `./coverage.sh`. HTML at `<project_root>/tmp/worldarchitectai/coverage/index.html`

## Git Workflow

**Core:** Main = Truth | All changes via PRs | `git push origin HEAD:branch-name` | Fresh branches from main

🚨 **CRITICAL RULES:**
- No main push: ❌ `git push origin main` | ✅ `git push origin HEAD:feature`
- ALL changes require PR (including docs)
- Never switch branches without request

## GitHub Actions Security

🚨 **SHA-PINNING REQUIREMENT:** ⚠️ MANDATORY - All Actions MUST use SHA-pinned versions
- ❌ FORBIDDEN: `@v4`, `@main`, `@latest` (can be changed by attackers)
- ✅ REQUIRED: Full commit SHA like `@b4ffde65f46336ab88eb53be808477a3936bae11`

## Environment & Scripts

🚨 **CLAUDE CODE HOOKS:** Executable scripts auto-run at specific points. Config: `.claude/settings.json`, Scripts: `.claude/hooks/` (executable)

**Python:** Verify venv activated. Run from project root with `TESTING=true vpython`. Use Python for restricted file ops.

**Logs:** Located at `<project_root>/tmp/worldarchitect.ai/[branch]/[service].log`. Use `tail -f` for monitoring.

**Sync Check:** `scripts/sync_check.sh` detects/pushes unpushed commits automatically.

🚨 **TERMINAL SESSION PRESERVATION:** ⚠️ MANDATORY - Scripts must NOT exit terminal on errors
- ❌ NEVER use `exit 1` that terminates user's terminal session
- ✅ ALWAYS use graceful error handling: echo error + read prompt + fallback mode
- ✅ Users need control over their terminal session - let them Ctrl+C to go back
- ❌ Only use `exit` for truly unrecoverable situations

## Operations Guide

**Data Defense:** Use `dict.get()`, validate structures, implement code safeguards.

**Memory MCP:** Search first → Create if new → Add observations → Build relationships

**TodoWrite:** Required for 3+ steps. Flow: `pending` → `in_progress` → `completed`

**Operations:** MultiEdit max 3-4 edits. Check context % before complex ops. Try alternatives after 2 failures.

🚨 **TOOL SELECTION HIERARCHY:** ⚠️ MANDATORY - Apply top-down for efficiency
1. **Serena MCP** - Semantic/code analysis before reading full files
2. **Read tool** - File contents; **Grep tool** - Pattern search
3. **Edit/MultiEdit** - In-place changes vs creating backup files
4. **Bash** - OS operations only (not content analysis)
- **Validation:** All `/plan` commands must justify tool selection against hierarchy

### Context Management

🚨 **LIMITS:** 500K tokens (Enterprise) / 200K (Paid). Use `/context` and `/checkpoint` commands.
**Health Levels:** Green (0-30%) continue | Yellow (31-60%) optimize | Orange (61-80%) efficiency | Red (81%+) checkpoint

## Slash Commands

**Types:** Cognitive (`/think`, `/debug`) = semantic | Operational (`/orch`, `/handoff`) = protocol | Tool (`/execute`, `/test`, `/pr`) = direct

🚨 **CRITICAL RULES:**
- Scan "/" → Check `.claude/commands/[command].md` → Execute complete workflow
- `/orch` ALWAYS triggers tmux agents - NEVER execute directly
- `/execute` requires TodoWrite checklist

## Special Protocols

**PR Comments:** Address ALL sources. Status: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED
**PR References:** Include full URL - "PR #123: https://github.com/user/repo/pull/123"

### PR Labeling
**Auto-labeling** based on git diff vs origin/main:
- **Type:** bug (fix/error), feature (add/new), improvement (optimize/enhance), infrastructure (yml/scripts)
- **Size:** small <100, medium 100-500, large 500-1000, epic >1000 lines

**Commands:** `/pushl` (auto-label), `/pushl --update-description`, `/pushl --labels-only`

## Quick Reference

- **Test:** `TESTING=true vpython mvp_site/test_file.py` (from root)
- **All Tests:** `./run_tests.sh` (CI simulation by default)  
- **Local Mode:** `./run_tests.sh --no-ci-sim`
- **New Branch:** `./integrate.sh`
- **Deploy:** `./deploy.sh` or `./deploy.sh stable`

## API Timeout Prevention (🚨)

**MANDATORY:** Prevent timeouts:
- **Edits:** MultiEdit with 3-4 max | Target sections, not whole files
- **Thinking:** 5-6 thoughts max | Concise
- **Tools:** Batch calls | Smart search (Grep/Glob) | Avoid re-reads

## AI-Assisted Development Protocols (🚨)

### Development Velocity Benchmarks
**Claude Code CLI Performance:**
- **Average:** 15.6 PRs/day, ~20K lines changed/day
- **Peak:** 119 commits in single day
- **Parallel Capacity:** 3-5 task agents simultaneously

### AI Development Planning (⚠️ MANDATORY)
**Calculation Steps:**
1. Estimate lines of code (with 20% padding)
2. Apply velocity: 820 lines/hour average
3. Add PR overhead: 5-12 min per PR
4. Apply parallelism: 30-45% reduction
5. Add integration buffer: 10-30%

**Realistic multiplier:** 10-15x faster (not 20x)

### AI Sprint Structure (1 Hour Sprint)
**Phase 1 (15min):** Core functionality - 3-5 parallel agents
**Phase 2 (15min):** Secondary features - 3-5 parallel agents  
**Phase 3 (15min):** Polish & testing - 2-3 parallel agents
**Phase 4 (15min):** Integration & deploy - 1 agent

### Success Patterns
- **Micro-PR workflow:** Each agent creates focused PR
- **Continuous integration:** Merge every 15 minutes
- **Test-driven:** Tests in parallel with features
- **Architecture-first:** Design before parallel execution

### Anti-Patterns to Avoid
- ❌ Sequential task chains (wastes AI parallelism)
- ❌ Human-scale estimates (still too conservative)
- ❌ Single large PR (harder to review/merge)
- ❌ Anchoring to user suggestions (calculate independently)

## Context Management & Optimization (🚨 MANDATORY)

🚨 **PROACTIVE CONTEXT MONITORING:** ⚠️ MANDATORY
- **Claude Sonnet 4 Limits:** 500K tokens (Enterprise) / 200K tokens (Paid)
- **Token Estimation:** ~4 characters per token
- **Context Health Monitoring:** Use `/context` command for real-time estimation

🚨 **CONTEXT CONSUMPTION PATTERNS:**
- **Context Killers:** Large file reads without limits (1000+ tokens each)
- **Medium Impact:** Standard operations with filtering (200-1000 tokens)
- **Low Impact:** Serena MCP operations (50-200 tokens)
- **Optimization Rule:** Serena MCP first, targeted operations always

**Context Health Levels:**
- **Green (0-30%):** Continue with current approach
- **Yellow (31-60%):** Apply optimization strategies  
- **Orange (61-80%):** Implement efficiency measures
- **Red (81%+):** Strategic checkpoint required

## Project-Specific

**Flask:** SPA route for index.html, hard refresh for CSS/JS, cache-bust in prod
**Python:** venv required, source .bashrc after changes
**AI/LLM:** Detailed prompts crucial, critical instructions first

## Additional Documentation

**Files:** `.cursor/rules/lessons.mdc` (lessons), `.cursor/rules/rules.mdc` (cursor), `.cursor/rules/examples.md`, `.cursor/rules/validation_commands.md`