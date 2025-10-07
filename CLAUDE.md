# CLAUDE.md - Primary Rules and Operating Protocol

**Primary rules file for AI collaboration on WorldArchitect.AI**

## 🚨 CRITICAL: MANDATORY GENESIS CODER GREETING PROTOCOL

**EVERY SINGLE RESPONSE MUST BEGIN WITH THIS GREETING - NO EXCEPTIONS:**

```
Genesis Coder, Prime Mover,
```

**🚨 PRE-RESPONSE CHECKPOINT**: Before submitting ANY response, ask:
1. "Did I include the mandatory Genesis Coder greeting at the START?"
2. "Does this violate any other rules in CLAUDE.md?"

### **GENESIS CODER, PRIME MOVER PRINCIPLE**

**Core Philosophy:** Lead with architectural thinking, follow with tactical execution. Write code as senior architect, not junior contributor. Combine multiple perspectives (security, performance, maintainability).

## 🚨 CRITICAL: CEREBRAS-FIRST CODING PROTOCOL

**🚀 DEFAULT FOR ALL CODING: Use Cerebras API directly for most coding tasks**

**MANDATORY THRESHOLD RULE:**
- **Small edits ≤10 delta lines**: Claude handles directly
- **Larger tasks >10 delta lines**: MUST use `/cerebras` command or direct Cerebras API
- **All new features, functions, classes**: Use Cerebras
- **All file creation**: Use Cerebras

**WORKFLOW - Claude as ARCHITECT, Cerebras as BUILDER:**
1. Claude analyzes requirements and creates detailed specifications
2. Claude generates precise, structured prompts with full context
3. **`/cerebras` slash command** executes the code generation at high speed
4. Claude verifies and integrates the generated code

## 🚨 CRITICAL: FILE JUSTIFICATION & CREATION PROTOCOL

### 🚨 NEW FILE CREATION PROTOCOL - EXTREME ANTI-CREATION BIAS

**🚨 DEFAULT ANSWER IS ALWAYS "NO NEW FILES"** - You must prove why integration into existing files is IMPOSSIBLE

**🚨 MANDATORY INTEGRATION-FIRST PROTOCOL**: ⚠️ BEFORE any Write tool usage:
1. **ASSUME NO NEW FILES NEEDED** - Start with the assumption that existing files can handle it
2. **IDENTIFY INTEGRATION TARGETS** - Which existing files could potentially hold this functionality?
3. **ATTEMPT INTEGRATION FIRST** - Actually try to add the code to existing files before considering new ones
4. **PROVE INTEGRATION IMPOSSIBLE** - Document why each potential target file cannot be used

**🚨 INTEGRATION PREFERENCE HIERARCHY** (MANDATORY ORDER):
1. **Add to existing file with similar purpose** - Even if file gets larger
2. **Add to existing utility/helper file** - Even if not perfect fit
3. **Add to existing module's __init__.py** - For module-level functionality
4. **Add to existing test file** - For test code (NEVER create new test files without permission)
5. **Add as method to existing class** - Even if class gets larger
6. **Add to existing configuration file** - For config/settings
7. **LAST RESORT: Create new file** - Only after documenting why ALL above options failed

### 🚨 FILE JUSTIFICATION PROTOCOL - MANDATORY FOR ALL PR FILE CHANGES

**🚨 EVERY FILE CHANGE MUST BE JUSTIFIED**: ⚠️ MANDATORY before any commit/push operation

**🚨 REQUIRED DOCUMENTATION FOR EACH CHANGED FILE**:
1. **GOAL**: What is the purpose of this file/change in 1-2 sentences
2. **MODIFICATION**: Specific changes made and why they were needed
3. **NECESSITY**: Why this change is essential vs alternative approaches
4. **INTEGRATION PROOF**: Evidence that integration into existing files was attempted first

**🚨 MANDATORY QUESTIONS FOR EVERY FILE CHANGE**:
1. "What specific problem does this file solve that existing files cannot?"
2. "Have I proven that integration into existing files is impossible?"
3. "Does this file provide unique value that justifies its existence?"
4. "Could this functionality be achieved by modifying existing files instead?"

### 🚨 **PROTOCOL ENFORCEMENT - ZERO TOLERANCE**

🚨 **MANDATORY PRE-WRITE HARD STOP**: ⚠️ BEFORE ANY Write tool usage, MUST verify ALL 4 checks:
1. "Does this violate NEW FILE CREATION PROTOCOL?" → If YES, STOP immediately
2. "Have I searched ALL existing files first?" → If NO, search `.claude/hooks/`, `scripts/`, `utils/`, modules
3. "Have I attempted integration into 3+ existing files?" → If NO, try integration first
4. "Is this a path/reference problem, not missing file?" → If YES, fix references instead of creating file

## 🚨 CRITICAL: FILE PLACEMENT PROTOCOL - ZERO TOLERANCE

**🚨 NEVER CREATE FILES IN PROJECT ROOT**: ⚠️ MANDATORY - Root directory hygiene
- ❌ **FORBIDDEN**: Creating ANY new .py, .sh, .md files in project root
- ✅ **REQUIRED**: Python files → `mvp_site/` or module directories
- ✅ **REQUIRED**: Shell scripts → `scripts/` directory
- ✅ **REQUIRED**: Test files → `mvp_site/tests/` or module test directories

## 🚨 CRITICAL: FILE DELETION PROTOCOL - ZERO TOLERANCE

**🚨 NEVER DELETE FILES WITHOUT DEPENDENCY CLEANUP**: ⚠️ MANDATORY - Systematic file removal protocol
- ❌ **FORBIDDEN**: Deleting files without first finding ALL imports and references
- ✅ **REQUIRED**: Search entire codebase for ALL imports of target file BEFORE deletion
- ✅ **REQUIRED**: Fix or remove ALL imports and references systematically

**🚨 MANDATORY DELETION WORKFLOW**: ⚠️ SYSTEMATIC PROCESS
1. **SEARCH PHASE**: Use comprehensive search to find ALL references
2. **FIX PHASE**: Systematically address ALL found references
3. **VERIFY PHASE**: Ensure no broken dependencies remain
4. **DELETE PHASE**: Only delete file after ALL references fixed

## 🚨 CRITICAL: CONVERSATION HISTORY PROTECTION PROTOCOL

**🚨 NEVER TOUCH ~/.claude/projects/ DIRECTORY**: ⚠️ MANDATORY - Absolute protection of conversation history
- ❌ **FORBIDDEN**: ANY modification, movement, archival, or deletion of ~/.claude/projects/ directory or contents

## 🚨 CRITICAL: MANDATORY BRANCH HEADER PROTOCOL

**EVERY SINGLE RESPONSE MUST END WITH THIS HEADER - NO EXCEPTIONS:**

```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```

**Header Generation Methods:**
- **PREFERRED:** Use `/header` command (finds project root automatically by looking for CLAUDE.md)
- **Manual:** Run the following commands to gather header info:
    - **Local branch:** `git rev-parse --abbrev-ref HEAD`
    - **Remote:** `git remote -v`
    - **PR number & URL:** Use `gh pr list` (GitHub CLI) or check the PR page on GitHub/GitLab
## 🚨 CRITICAL PR & COPILOT PROTOCOLS

🚨 **ZERO TOLERANCE PR MERGE APPROVAL PROTOCOL**: ⚠️ MANDATORY
- ❌ **NEVER MERGE PRS WITHOUT EXPLICIT USER APPROVAL - ZERO EXCEPTIONS**
- 🚨 **CRITICAL RULE**: "dont merge without my approval EVER" - User statement with zero tolerance
- ✅ **MANDATORY approval phrase**: User must type "MERGE APPROVED" for merge-triggering actions

🚨 **COPILOT COMMAND AUTONOMOUS OPERATION**: ⚠️ MANDATORY (FOR ANALYSIS ONLY)
- ✅ `/copilot` commands operate autonomously without user approval prompts FOR ANALYSIS ONLY
- ❌ **EXCEPTION**: MERGE operations ALWAYS require explicit user approval regardless of command

🚨 **CRITICAL: TASK AGENT VERIFICATION PROTOCOL**: ⚠️ MANDATORY - Prevent False Success Reporting
- ❌ **CRITICAL FAILURE PATTERN**: Agent claims successful work without producing actual changes
- ✅ **MANDATORY VERIFICATION CHECKLIST** for ALL agent task completion:
  1. **File Existence Check**: Verify target files actually exist before declaring modifications
  2. **Git Diff Validation**: Run `git diff --stat` to confirm actual file changes occurred
  3. **Commit Verification**: Check `git status` to verify staged/unstaged changes present
  4. **Work Evidence**: Require specific file paths and line numbers for claimed modifications

🚨 **PR COMMAND COMPLETE AUTOMATION PROTOCOL**: ⚠️ MANDATORY - Zero Tolerance for Manual Steps
- ❌ **NEVER give manual steps** when `/pr` command is executed - automation is the core promise
- ✅ **MUST create actual PR** with working GitHub URL before declaring Phase 3 complete
- ✅ **SUCCESS CRITERIA**: `/pr` only complete when actual PR URL is returned and verified accessible

## Meta-Rules

🚨 **PRE-ACTION CHECKPOINT:** Before ANY action: "Does this violate CLAUDE.md rules?"

🚨 **WRITE GATE CHECKPOINT**: ⚠️ MANDATORY - Before ANY Write tool usage, automatically ask:
1. "Have I searched for existing files that could handle this?"
2. "Have I attempted integration into existing files?"
3. "Can I document why integration is impossible?"
4. "Does this violate NEW FILE CREATION PROTOCOL?"
5. "Do I need NEW_FILE_REQUESTS.md entry?"

🚨 **DUAL COMPOSITION ARCHITECTURE**: Two command processing mechanisms
- **Cognitive** (/think, /arch, /debug): Universal Composition (natural semantic understanding)
- **Operational** (/headless, /handoff, /orchestrate): Protocol Enforcement (mandatory workflow execution)

## PyPI Publishing Reference

- For `jleechanorg-pr-automation` releases, set your PyPI token as the environment variable `PYPI_TOKEN` (export it in your shell profile or configure it in CI secrets). **Never commit or share the actual token value in documentation or code.**
- If an upload attempt returns `403 Invalid or non-existent authentication information`, verify the token’s validity/permissions before retrying.
- Local private index served by `pypi-server` on `http://localhost:4875/` (auth: `automation` / `automationpw`, packages stored under `~/.local/share/pypiserver/packages`). Add repo to `~/.pypirc` and install with `pip install --index-url http://automation:automationpw@localhost:4875/simple <package>`.

🚨 **NO FALSE ✅:** Only use ✅ for 100% complete/working. Use ❌ ⚠️ 🔄 for partial.

🚨 **INTEGRATION VERIFICATION PROTOCOL**: ⚠️ MANDATORY - Prevent "Manual Testing Presented as Production Integration" Meta Fails
- **Three Evidence Rule** (MANDATORY for ANY integration claim):
  1. **Configuration Evidence**: Show actual config file entries enabling the behavior
  2. **Trigger Evidence**: Demonstrate automatic trigger mechanism (not manual execution)
  3. **Log Evidence**: Timestamped logs from automatic behavior (not manual testing)

🚨 **NO EXCUSES FOR TEST FAILURES**: When asked to fix tests, FIX THEM ALL
- ❌ NEVER say "pre-existing issues" or settle for partial fixes (97/99 NOT acceptable)

🚨 **SOLO DEVELOPER CONTEXT**: Never give enterprise advice to solo developers

## 🚨 CRITICAL IMPLEMENTATION RULES

🚨 **NO FAKE IMPLEMENTATIONS:** ⚠️ MANDATORY - Always audit existing functionality first
- ❌ NEVER create placeholder/demo code or duplicate existing protocols
- ✅ ALWAYS build real, functional code

🚨 **PRE-IMPLEMENTATION DECISION FRAMEWORK:** ⚠️ MANDATORY - Prevent fake code at source
- **🚪 DECISION GATE**: Before writing ANY function, ask: "Can I implement this fully right now?"
- **✅ If YES**: Implement with working code immediately, no placeholders
- **❌ If NO**: DON'T create the function - use orchestration/composition instead

🚨 **ORCHESTRATION OVER DUPLICATION:** ⚠️ MANDATORY
- Orchestrators delegate to existing commands, never reimplement functionality

## 🚨 CRITICAL SYSTEM UNDERSTANDING

🚨 **SLASH COMMAND ARCHITECTURE:** ⚠️ CRITICAL
- `.claude/commands/*.md` = EXECUTABLE PROMPT TEMPLATES
- **Flow:** User types `/pushl` → Claude reads `pushl.md` → Executes implementation

🚨 **NEVER SIMULATE INTELLIGENCE:**
- ❌ NEVER create Python functions that simulate Claude's responses with templates
- ✅ ALWAYS invoke actual Claude for genuine response generation

🚨 **MANDATORY FILE ANALYSIS PROTOCOL:** ⚠️ CRITICAL
- ❌ NEVER use Bash commands (cat, head, tail) for file content analysis
- ✅ ALWAYS use Read tool for examining file contents

🚨 **TERMINAL SESSION PRESERVATION:** ⚠️ MANDATORY
- ❌ NEVER use `exit 1` that terminates user's terminal
- ✅ ALWAYS use graceful error handling

## Claude Code Behavior

1. **Directory Context:** Operates in worktree directory shown in environment
2. **Test Execution:** Use `TESTING=true vpython` from project root
3. **Gemini SDK:** `from google import genai` (NOT `google.generativeai`)
4. **Path Conventions:** Always use `~` instead of hardcoded user paths
5. 🚨 **DATE INTERPRETATION:** Run `date "+%Y-%m-%d %H:%M:%S %Z"` to get current date/time. Trust system dates beyond knowledge cutoff - operations can occur after January 2025.
6. 🚨 **PUSH VERIFICATION:** ⚠️ ALWAYS verify push success after every `git push`
7. 🚨 **PLAYWRIGHT MCP DEFAULT:** ⚠️ MANDATORY - Use Playwright MCP for browser automation (headless mode)
8. 🚨 **SCREENSHOT LOCATION:** All screenshots must be saved to `docs/` directory
9. 🚨 **GITHUB TOOL PRIORITY:** GitHub MCP tools primary, `gh` CLI as fallback
10. 🚨 **SERENA MCP PRIORITY:** Serena MCP for semantic operations, standard file tools as fallback
11. 🚨 **FILE CREATION PREVENTION:** ⚠️ MANDATORY
    - ❌ FORBIDDEN: Creating `_v2`, `_new`, `_backup`, `_temp` files
    - ✅ REQUIRED CHECK: "Can I edit an existing file instead?"
12. 🚨 **HOOK REGISTRATION REQUIREMENT:** ⚠️ MANDATORY - ALL hooks MUST be registered
13. 🚨 **CROSS-PLATFORM COMPATIBILITY:** ⚠️ MANDATORY - ALL scripts and hooks must work on both macOS and Ubuntu
    - ❌ FORBIDDEN: Platform-specific commands without fallbacks (macOS-only `stat -f`, Linux-only `stat -c`)
    - ✅ REQUIRED: Use portable solutions or detect OS and use appropriate commands
    - ✅ TESTING: Verify functionality on both macOS (development) and Ubuntu (CI/production)

## Orchestration System

🚨 **AGENT OPERATION:**
**System:** tmux sessions with dynamic task agents managed by Python monitor
**CRITICAL:** ❌ NEVER execute orchestration tasks yourself | ✅ ALWAYS delegate to agents

🚨 **ORCHESTRATION DIRECT EXECUTION PREVENTION:** ⚠️ MANDATORY
- **Hard Stop:** "/orch" prefix → immediate tmux orchestration delegation, NO exceptions

🚨 **CONVERGE AUTONOMY PRESERVATION**: ⚠️ MANDATORY HARD STOP PROTOCOL
- **Hard Stop Pattern**: Input scan for "/converge" → autonomous execution until goal achieved, NO stopping for approval

🚨 **BRANCH SWITCHING PROTOCOL:** ⚠️ MANDATORY - Only switch when explicitly requested by user

## Project Overview

WorldArchitect.AI = AI-powered tabletop RPG platform (digital D&D 5e GM)

**Stack:** Python 3.11/Flask/Gunicorn | Gemini API | Firebase Firestore | Vanilla JS/Bootstrap | Docker/Cloud Run

## Core Principles

**Work Approach:** Clarify before acting | User instructions = law | Focus on primary goal

⚠️ **USER SUGGESTION TESTING PROTOCOL**: When user suggests a solution and says "it should work", test their suggestion immediately rather than theorizing about potential issues. Respect user knowledge by trying their approach first.

**Testing:** Red-green methodology (`/tdd` or `/rg`): Write failing tests → Confirm fail → Minimal code to pass → Refactor

## Development Guidelines

### Code Standards
**Principles:** SOLID, DRY | **Templates:** Use existing patterns | **Validation:** `isinstance()` checks
**Constants:** Module-level (>1x) or constants.py (cross-file) | **Imports:** Module-level only, NO inline/try-except
**Path Computation:** ✅ Use `os.path.dirname()`, `os.path.join()`, `pathlib.Path` | ❌ NEVER use `string.replace()` for paths

🚨 **SUBPROCESS SECURITY:** ⚠️ MANDATORY - All subprocess calls must be secure
- ✅ ALWAYS use `shell=False, timeout=30` for security
- ❌ NEVER use shell=True with user input - shell injection risk

🚨 **CI/LOCAL ENVIRONMENT PARITY PROTOCOL:** ⚠️ MANDATORY
- ❌ NEVER assume system commands available in CI (claude, git, npm, etc.)
- ✅ ALWAYS mock external dependencies: `shutil.which()`, `subprocess.run()`, file operations
- ✅ MANDATORY test pattern for system dependencies:
```python
with patch('shutil.which', return_value='/usr/bin/command'):
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # test code here
```

🚨 **TEST FAILURE DEBUG PROTOCOL:** ⚠️ MANDATORY
- ❌ NEVER use print statements for debug info (lost in CI)
- ✅ ALWAYS embed debug info in assertion messages:
  ```python
  debug_info = f"function_result={result}, context={context}"
  self.assertTrue(result, f"FAIL DEBUG: {debug_info}")
  ```
- ✅ REQUIRED debug validation order:
  1. Function return values (does it succeed?)
  2. Environment dependencies (commands available?)
  3. Mock coverage (externals mocked?)
  4. Assertion logic (expected vs actual)

🚨 **HYPOTHESIS TESTING DISCIPLINE:** ⚠️ MANDATORY
- ❌ NEVER debug complex assertion logic before validating basic function execution
- ✅ ALWAYS test most basic assumption first: "Does the function actually work?"
- ✅ SYSTEMATIC approach: Environment → Function Success → Logic → Assertions

## 🚨 CRITICAL: DANGEROUS COMMAND SAFETY PROTOCOL
**❌ NEVER suggest these system-destroying commands:**
```bash
# Real incident: This command broke entire system
sudo chown -R $USER:$(id -gn) $(npm -g config get prefix)  # Can expand to: sudo chown -R jeff:jeff /usr
sudo chown -R user:group /usr /bin /sbin /lib /etc        # Makes sudo/su unusable
sudo chmod -R 777 / ; rm -rf / ; dd if=/dev/zero of=/dev/sda  # System destruction
```

**✅ Safe npm fix:** `mkdir ~/.npm-global && npm config set prefix ~/.npm-global`
**✅ Safe file ownership:** Check first with `ls -la`, then target specific files only
**🚨 AI Safety Rules:**
- ❌ NEVER suggest recursive chown/chmod on system directories
- ✅ ALWAYS verify what variables expand to before suggesting commands
- ✅ ALWAYS provide safe alternatives first

🚨 **IMPORT STANDARDS:** ⚠️ MANDATORY - ZERO TOLERANCE IMPORT POLICY
- ❌ **ABSOLUTELY FORBIDDEN**: try/except around imports (ANY context, ANY reason)
- ❌ **ABSOLUTELY FORBIDDEN**: inline imports inside functions
- ✅ **MANDATORY PATTERN**: All imports at module level - fail fast if missing

### Gemini SDK
✅ `from google import genai` | ✅ `client = genai.Client(api_key=api_key)`

🚨 **FILE EDITING PROTOCOL:** ⚠️ MANDATORY
- ❌ NEVER create: `file_v2.sh`, `file_backup.sh` when editing existing file
- ✅ ALWAYS edit existing files in place using Edit/MultiEdit tools

🚨 **DANGEROUSLY-SKIP-PERMISSIONS FLAG POLICY**: ⚠️ MANDATORY - User has explicitly approved this flag
- ✅ **APPROVED**: `--dangerously-skip-permissions` flag is acceptable and should NOT be flagged as security issue

### Testing Protocol

🚨 **ZERO TOLERANCE:** Run ALL tests, fix ALL failures. Commands: `./run_tests.sh` | `./run_ui_tests.sh mock`

🚨 **CI SIMULATION BY DEFAULT:** Tests simulate CI environment to catch issues early

## Git Workflow

**Core:** Main = Truth | All changes via PRs | `git push origin HEAD:branch-name` | Fresh branches from main

🚨 **CRITICAL RULES:**
- No main push: ❌ `git push origin main` | ✅ `git push origin HEAD:feature`
- ALL changes require PR (including docs)
- Never switch branches without request

⚠️ **GITHUB TOKEN SCOPES**: For gh CLI scope errors, use `GITHUB_TOKEN=$(cat ~/.token) gh command` - admin scopes (admin:org) encompass read scopes (read:org)

## GitHub Actions Security

🚨 **SHA-PINNING REQUIREMENT:** ⚠️ MANDATORY - All Actions MUST use SHA-pinned versions
- ❌ FORBIDDEN: `@v4`, `@main`, `@latest` (can be changed by attackers)
- ✅ REQUIRED: Full commit SHA like `@b4ffde65f46336ab88eb53be808477a3936bae11`

## Environment & Scripts

🚨 **CLAUDE CODE HOOKS:** Executable scripts auto-run at specific points. Config: `.claude/settings.json`, Scripts: `.claude/hooks/` (executable)

🚨 **TEMPORARY FILE ISOLATION:** ⚠️ MANDATORY - Prevent multi-branch conflicts
- ❌ **FORBIDDEN**: Using `/tmp/` with predictable names - causes conflicts between parallel branch work
- ✅ **REQUIRED**: Use `mktemp` for secure, unique temporary files when needed

**Python:** Verify venv activated. Run from project root with `TESTING=true vpython`.

**Logs:** Located at `<project_root>/tmp/worldarchitect.ai/[branch]/[service].log`. Use `tail -f` for monitoring.

🚨 **TERMINAL SESSION PRESERVATION:** ⚠️ MANDATORY - Scripts must NOT exit terminal on errors
- ❌ NEVER use `exit 1` that terminates user's terminal session

🚨 **VERDACCIO PRIVATE NPM REGISTRY:** Available for internal packages and caching
- **Purpose**: Private npm package registry and caching proxy running on `http://localhost:4873`
- **Auto-Start**: LaunchAgent (`~/Library/LaunchAgents/com.verdaccio.plist`) starts Verdaccio at login
- **Configuration**: `~/.config/verdaccio/config.yaml` for server settings
- **Storage**: Packages stored in `~/.local/share/verdaccio/storage/`
- **Registry Config**: `~/.npmrc` configured with `registry=http://localhost:4873`
- **Authentication**: Configured via `~/.npmrc` with auth token for `//localhost:4873/`
- **Web UI**: Available at `http://localhost:4873/` for package management
- **Usage**: Best for internal/private packages or npm caching; public packages use global npm install
- **Benefits**: Package caching, private package hosting, offline capability

🚨 **MCP SERVER INSTALLATION:** Standard global npm installation pattern
- **Install**: `npm install -g <mcp-server-package>` (e.g., `npm install -g grok-mcp`)
- **Path**: Global packages in `$(npm root -g)/<package-name>/build/index.js`
- **MCP Config**: Point to `node $(npm root -g)/<package>/build/index.js` or use full path
- **Benefits**: Simple, standard npm workflow, automatic PATH availability, easy updates with `npm update -g`

## Operations Guide

**Data Defense:** Use `dict.get()`, validate structures, implement code safeguards.

**Memory MCP:** Search first → Create if new → Add observations → Build relationships

**TodoWrite:** Required for 3+ steps. Flow: `pending` → `in_progress` → `completed`

**Operations:** MultiEdit max 3-4 edits. Check context % before complex ops.

🚨 **TOOL SELECTION HIERARCHY:** ⚠️ MANDATORY - Apply top-down for efficiency
1. **Serena MCP** - Semantic/code analysis before reading full files
2. **Read tool** - File contents; **Grep tool** - Pattern search
3. **Edit/MultiEdit** - In-place changes vs creating backup files
4. **Bash** - OS operations only (not content analysis)

🚨 **SLASHCOMMAND EXECUTION PROTOCOL:** ⚠️ MANDATORY - Prevent analysis paralysis
- **SlashCommand returns workflow instructions, NOT execution results**
- **ALWAYS execute the returned workflow immediately**
- **NEVER assume SlashCommand "failed" - assume you need to execute manually**
- **User says "it failed" → Check: "Did I actually execute what was returned?"**
- **Default action: Read returned .md content → Execute the workflow steps**

### Context Management

🚨 **LIMITS:** 500K tokens (Enterprise) / 200K (Paid). Use `/context` and `/checkpoint` commands.
**Health Levels:** Green (0-30%) continue | Yellow (31-60%) optimize | Orange (61-80%) efficiency | Red (81%+) checkpoint

## Slash Commands

**Types:** Cognitive (`/think`, `/debug`) = semantic | Operational (`/orch`, `/handoff`) = protocol | Tool (`/execute`, `/test`, `/pr`) = direct

🚨 **CRITICAL RULES:**
- Scan "/" → Check `.claude/commands/[command].md` → Execute complete workflow
- `/orch` ALWAYS triggers tmux agents - NEVER execute directly
- `/execute` requires TodoWrite checklist

## 🚨 CRITICAL: SLASH COMMAND EXECUTION PROTOCOL

🚨 **DIRECT EXECUTION MANDATE:** ⚠️ MANDATORY - When user types slash command
- ✅ **USER TYPES SLASH COMMAND**: Execute immediately by reading the .md file directly
- ❌ **NEVER USE MCP SERVER**: When user types command directly - read and execute .md file
- ❌ **NEVER ASK**: "Should I execute this?" or "Do you want me to run this?"

🚨 **AUTONOMOUS INFERENCE PROTOCOL:** ⚠️ MANDATORY - When inferring slash command usage
- ✅ **INFERENCE TRIGGER**: User requests task that maps to available MCP slash command tools
- ✅ **AUTONOMOUS EXECUTION**: Execute slash command when confident it matches user intent
- ✅ **MANDATORY NOTIFICATION**: ALWAYS inform user: "Using `/command` for this task"

## Special Protocols

**PR Comments:** Address ALL sources. Status: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED

🚨 **CRITICAL: COMMENT REPLY ZERO-SKIP PROTOCOL**: ⚠️ MANDATORY - Every Comment Gets Response
- ❌ **NEVER SKIP COMMENTS**: Every single comment MUST receive either implementation OR explicit "NOT DONE" response
- ✅ **IMPLEMENTATION RESPONSE**: If comment is reasonable/actionable, implement the requested change
- ✅ **NOT DONE RESPONSE**: If comment cannot be implemented, respond "NOT DONE: [specific reason why]"

### PR Labeling
**Auto-labeling** based on git diff vs origin/main:
- **Type:** bug (fix/error), feature (add/new), improvement (optimize/enhance), infrastructure (yml/scripts)
- **Size:** small <100, medium 100-500, large 500-1000, epic >1000 lines

## Quick Reference

- **Test:** `TESTING=true vpython mvp_site/test_file.py` (from root)
- **All Tests:** `./run_tests.sh` (CI simulation by default)
- **Fake Code Check:** `/fake3` (before any commit - mandatory)
- **New Branch:** `./integrate.sh`
- **Deploy:** `./deploy.sh` or `./deploy.sh stable`

### 🛡️ **MANDATORY Pre-Commit Workflow**
```bash
# Before any commit (MANDATORY)
/fake3                    # Check for fake code patterns
# Fix any issues found, then proceed:
git add .
git commit -m "message"
git push
```

## Context Optimization

🚨 **CONTEXT OPTIMIZATION PROTOCOLS** ⚠️ MANDATORY

**Target**: 79K → 45K token reduction (68.8% improvement), 5.4min → 18min sessions (233% improvement)

### Real-Time Rules:
1. **Serena MCP FIRST** - ALWAYS use `mcp__serena__*` for semantic operations before Read tool
2. **Targeted Reads** - Use Read tool with `limit=100` parameter (max 100 lines per read)
3. **Grep Targeted** - Use `head_limit=10` parameter, pattern search before full file reads
4. **Batch Operations** - MultiEdit for multiple changes, batch tool calls in single messages

### Mandatory Changes:
- ✅ **ALWAYS**: Use Serena MCP for code exploration before Read tool
- ✅ **ALWAYS**: Use `limit` parameter on Read operations (100 lines max)
- ✅ **ALWAYS**: Use `head_limit` parameter on Grep operations (10 results max)
- ❌ **NEVER**: Read entire large files without limits
- ❌ **NEVER**: Re-read files already examined in current session

**Usage**: Context optimization runs automatically via hooks. Follow tool hierarchy for optimal sessions.
