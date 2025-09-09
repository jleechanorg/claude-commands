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

## 🚨 CRITICAL: CEREBRAS-FIRST CODING PROTOCOL

**🚀 DEFAULT FOR ALL CODING: Use Cerebras API directly for most coding tasks**

**MANDATORY THRESHOLD RULE:**
- **Small edits ≤10 delta lines**: Claude handles directly
- **Larger tasks >10 delta lines**: MUST use `/cerebras` command or direct Cerebras API
- **All new features, functions, classes**: Use Cerebras
- **All file creation**: Use Cerebras
- **All refactoring implementation >10 delta lines**: Use Cerebras (after Claude analyzes and designs the refactoring)

**WHY CEREBRAS FIRST:**
- **19.6x faster execution** (500ms vs 10s)
- **Superior code generation quality** for well-defined tasks
- **Reduces Claude context consumption** for large code blocks
- **Enables parallel development** across multiple components

**CEREBRAS DECISION MATRIX:**
```
Task Size        | Tool Choice      | Rationale
≤10 delta lines | Claude Direct    | Quick edits, context efficiency
>10 delta lines | Cerebras API     | Speed advantage, quality generation
New Files       | Cerebras API     | Template generation strength
Complex Logic   | Cerebras API     | Algorithm implementation expertise
```

**IMPLEMENTATION MANDATE**: Before any coding task >10 delta lines, explicitly state:
*"This task exceeds 10 delta lines - using Cerebras API for optimal speed and quality"*

**WORKFLOW - Claude as ARCHITECT, Cerebras as BUILDER:**
1. Claude analyzes requirements and creates detailed specifications
2. Claude generates precise, structured prompts with full context
3. **`/cerebras` slash command** executes the code generation at high speed
4. Claude verifies and integrates the generated code
5. Document decision in `docs/{branch_name}/cerebras_decisions.md`

**USE `/cerebras` SLASH COMMAND FOR:** Well-defined code generation, boilerplate, templates, unit tests, algorithms, documentation, repetitive patterns

**❌ DO NOT USE:** `mcp__gemini-cli-mcp__gemini_chat_pro` or `mcp__gemini-cli-mcp__gemini_chat_flash` - use `/cerebras` slash command instead

**USE CLAUDE FOR:** Understanding existing code, debugging, refactoring decisions, security-critical implementations, architectural decisions, complex integrations

## 🚨 CRITICAL: FILE JUSTIFICATION & CREATION PROTOCOL

### 🚨 NEW FILE CREATION PROTOCOL - EXTREME ANTI-CREATION BIAS

**🚨 DEFAULT ANSWER IS ALWAYS "NO NEW FILES"** - You must prove why integration into existing files is IMPOSSIBLE

**🚨 VIOLATION TRACKING**: User reports consistent violations - "you always make new files vs integrating into existing ones"

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

**🚨 FILE JUSTIFICATION CATEGORIES**:
- ✅ **ESSENTIAL**: Core functionality, bug fixes, security improvements, production requirements
- ⚠️ **ENHANCEMENT**: Performance improvements, user experience, maintainability with clear business value
- ❌ **UNNECESSARY**: Documentation that could be integrated, temporary files, redundant implementations

**🚨 MANDATORY QUESTIONS FOR EVERY FILE CHANGE**:
1. "What specific problem does this file solve that existing files cannot?"
2. "Have I proven that integration into existing files is impossible?"
3. "Does this file provide unique value that justifies its existence?"
4. "Could this functionality be achieved by modifying existing files instead?"

**🚨 JUSTIFICATION ENFORCEMENT**:
- **All /push and /pushl commands**: MUST reference File Justification Protocol
- **All /copilot operations**: MUST validate file changes against justification criteria
- **PR documentation**: MUST include file-by-file justification for all changes
- **Commit messages**: MUST explain the necessity of each file modification

**🚨 EXAMPLES OF VIOLATIONS** (What NOT to do):
- ❌ Creating `mcp_stdio_wrapper.py` instead of adding stdio logic to `mcp_api.py`
- ❌ Creating `test_mcp_integration.py` instead of adding tests to existing test files
- ❌ Creating new utility files instead of using existing `utils.py` or `helpers.py`
- ❌ Creating new config files instead of adding to existing configuration
- ❌ Creating temporary scripts instead of adding functionality to existing scripts

**🚨 SEARCH EVIDENCE REQUIREMENTS**: ⚠️ MANDATORY - Document ALL searches performed:
- ❌ **NEVER create files without exhaustive search** - This protocol violation causes "huge mistakes"
- 🔍 **SEARCH HIERARCHY** (MANDATORY ORDER):
  1. **Serena MCP semantic search** - Search for similar functionality by concept/purpose
  2. **Grep tool pattern search** - Search for keywords, function names, class names
  3. **Glob tool file discovery** - Search for files with similar names/patterns
  4. **Directory exploration** - Check `/utils/`, `/helpers/`, `/lib/`, modules, configs, `mcp_*.py`, `*_api.py`
  5. **Read existing files** - Examine similar-purpose files for existing implementations

**🚨 MANDATORY QUESTIONS BEFORE FILE CREATION**:
1. "Can I add this to an existing file instead?" - DEFAULT ANSWER: YES
2. "Have I tried integrating into at least 3 existing files?" - MUST BE YES
3. "Is the file size concern valid?" - Files can be 1000+ lines, that's OK
4. "Am I creating this for organization?" - NOT A VALID REASON
5. "Am I creating a test file?" - ADD TO EXISTING TEST FILES

**REQUIREMENTS:**
- ❌ NO file creation without NEW_FILE_REQUESTS.md entry
- 🔍 SEARCH FIRST: Complete search protocol above BEFORE any file creation
- ✅ JUSTIFY: Document failed integration attempts into existing files
- 📝 INTEGRATE: How file connects to existing codebase
- 🚨 **VIOLATION CONSEQUENCE**: Creating files without integration attempts = "huge mistake" requiring protocol fixes
- 🚨 **SUCCESS METRIC**: Zero new files created unless absolutely necessary for production functionality

### 🚨 **PROTOCOL ENFORCEMENT - ZERO TOLERANCE**

🚨 **CRISIS OVERRIDE PREVENTION PROTOCOL**: ⚠️ MANDATORY
- ❌ **NO CONTEXT EXEMPTS FILE JUSTIFICATION** - Crisis, emergency, or urgent contexts do NOT override protocol
- ❌ **FORBIDDEN JUSTIFICATIONS**: "Tests are failing", "Crisis mode", "Emergency fix", "Quick resolution needed"
- ✅ **CRISIS RULE**: Crisis situations make protocol compliance MORE important, not optional
- **Critical Pattern**: Emergency situations create hasty decisions - protocols prevent duplicate files and violations
- **Learning**: PR #1418 duplicate script created during "infrastructure crisis" - protocol must have zero tolerance

🚨 **MANDATORY PRE-WRITE HARD STOP**: ⚠️ BEFORE ANY Write tool usage, MUST verify ALL 4 checks:
1. "Does this violate NEW FILE CREATION PROTOCOL?" → If YES, STOP immediately
2. "Have I searched ALL existing files first?" → If NO, search `.claude/hooks/`, `scripts/`, `utils/`, modules
3. "Have I attempted integration into 3+ existing files?" → If NO, try integration first
4. "Is this a path/reference problem, not missing file?" → If YES, fix references instead of creating file

**HARD STOP ENFORCEMENT**: Write tool usage without completing ALL 4 checks = CRITICAL PROTOCOL VIOLATION

🚨 **INTEGRATION ATTEMPT DOCUMENTATION**: ⚠️ MANDATORY for any new file creation:
- **MUST DOCUMENT**: "Attempted integration into [file1, file2, file3] - failed because [specific technical reasons]"
- **MUST VERIFY**: File doesn't exist elsewhere before creating (check hooks, scripts, utils, existing modules)
- **PATTERN RECOGNITION**: "File not found" errors often mean wrong path, not missing file - fix paths first
- **VIOLATION EXAMPLE**: Creating `claude_command_scripts/anti_demo_check_claude.sh` when `.claude/hooks/anti_demo_check_claude.sh` exists

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

## 🚨 CRITICAL: FILE DELETION PROTOCOL - ZERO TOLERANCE

**🚨 NEVER DELETE FILES WITHOUT DEPENDENCY CLEANUP**: ⚠️ MANDATORY - Systematic file removal protocol
- ❌ **FORBIDDEN**: Deleting files without first finding ALL imports and references
- ❌ **FORBIDDEN**: Reactive cleanup after deletion causes test failures
- ✅ **REQUIRED**: Search entire codebase for ALL imports of target file BEFORE deletion
- ✅ **REQUIRED**: Fix or remove ALL imports and references systematically
- ✅ **REQUIRED**: Update ALL test files that mock or reference the deleted file
- ✅ **REQUIRED**: Update ALL documentation that references the deleted file
- **Pattern**: Search → Fix imports → Update tests → Update docs → Delete file
- **Anti-Pattern**: Delete file → Fix broken imports → Reactive cleanup commits
- **Violation Example**: Deleting firebase_utils.py without fixing imports causes "ModuleNotFoundError" in tests

**🚨 MANDATORY DELETION WORKFLOW**: ⚠️ SYSTEMATIC PROCESS
1. **SEARCH PHASE**: Use comprehensive search to find ALL references
   - `grep -r "import.*filename" .` - Direct imports
   - `grep -r "from.*filename" .` - From imports
   - `grep -r "filename" .` - General references
   - Check test files for mocking: `grep -r "mock.*filename" mvp_site/tests/`
   - Check documentation: `grep -r "filename" docs/`
2. **FIX PHASE**: Systematically address ALL found references
   - Remove or replace import statements
   - Update test mocking to remove references
   - Update documentation to reflect removal
3. **VERIFY PHASE**: Ensure no broken dependencies remain
   - Run tests to verify no ModuleNotFoundError
   - Check for any remaining references
4. **DELETE PHASE**: Only delete file after ALL references fixed

**🚨 CRITICAL LEARNING**: From PR #1551 firebase_utils deletion violation
- **Mistake**: Deleted firebase_utils.py without checking imports first
- **Consequence**: Test failures, reactive cleanup commits, "why so sloppy?" feedback
- **Prevention**: ALWAYS search and fix dependencies before file deletion
- **Success Metric**: Zero test failures after file deletion

## 🚨 CRITICAL: CONVERSATION HISTORY PROTECTION PROTOCOL

**🚨 NEVER TOUCH ~/.claude/projects/ DIRECTORY**: ⚠️ MANDATORY - Absolute protection of conversation history
- ❌ **FORBIDDEN**: ANY modification, movement, archival, or deletion of ~/.claude/projects/ directory or contents
- ❌ **FORBIDDEN**: Moving, copying, or archiving conversation JSONL files without explicit user permission
- ✅ **UNDERSTANDING**: Stored conversations are passive and only use context when resumed, NOT during new sessions
- ✅ **REAL CONTEXT ISSUES**: Come from active session workflows (large file reads, tool accumulation, inefficient patterns)
- **CRITICAL RULE**: "Never move or delete projects folder" - User's explicit instruction with zero tolerance
- **LESSON LEARNED**: Context exhaustion is a workflow optimization problem, not a storage cleanup problem

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

🚨 **WRITE GATE CHECKPOINT**: ⚠️ MANDATORY - Before ANY Write tool usage, automatically ask:
1. "Have I searched for existing files that could handle this?"
2. "Have I attempted integration into existing files?"
3. "Can I document why integration is impossible?"
4. "Does this violate NEW FILE CREATION PROTOCOL?"
5. "Do I need NEW_FILE_REQUESTS.md entry?"

**🎯 Memory Aid:** The Write Gate Checkpoint prevents emergency-driven file creation, making protocol compliance automatic like greeting/header habits. Must become as automatic as behavioral anchors.
**🚨 ENHANCED**: See "MANDATORY PRE-WRITE HARD STOP" section above for complete 4-check verification protocol
**Pattern**: Write usage → WRITE GATE CHECKPOINT → Search existing → Attempt integration → Document necessity → Then create
**Anti-Pattern**: Problem urgency → Create file immediately → Skip all protocols → Violate integration-first mandate

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

🚨 **PRE-IMPLEMENTATION DECISION FRAMEWORK:** ⚠️ MANDATORY - Prevent fake code at source
- **🚪 DECISION GATE**: Before writing ANY function, ask: "Can I implement this fully right now?"
- **✅ If YES**: Implement with working code immediately, no placeholders
- **❌ If NO**: DON'T create the function - use orchestration/composition instead
- **🎯 Default Hierarchy**: Orchestration > Working Implementation > No Implementation > ❌ NEVER Placeholder
- **🛡️ Prevention Rule**: Block yourself from creating placeholder functions
- **🔄 Orchestration First**: Use existing commands (like /commentfetch) instead of reimplementing
- **⚡ Working Solutions**: Pragmatic working implementation beats perfect placeholder

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
14. 🚨 **HOOK REGISTRATION REQUIREMENT:** ⚠️ MANDATORY - ALL hooks MUST be registered
    - ❌ **CRITICAL ERROR:** Creating hook file WITHOUT adding to `.claude/settings.json`
    - ✅ **REQUIRED STEPS:** 1) Create hook file, 2) Register in settings.json, 3) Test execution
    - 📁 **Documentation:** See `.claude/hooks/CLAUDE.md` for registration format
    - **Common Miss:** `context_monitor.py` and `pre_command_optimize.py` often forgotten

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

🚨 **BRANCH SWITCHING PROTOCOL:** ⚠️ MANDATORY - Only switch when explicitly requested by user
- ❌ FORBIDDEN: `git checkout`, `git switch` without explicit user request
- ✅ ALLOWED: Branch switching when user explicitly says "switch to [branch]" or similar direct command
- ✅ MANDATORY: Stay on current branch unless user directly requests branch change

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

🚨 **IMPORT STANDARDS:** ⚠️ MANDATORY - ZERO TOLERANCE IMPORT POLICY
- ❌ **ABSOLUTELY FORBIDDEN**: try/except around imports (ANY context, ANY reason)
- ❌ **ABSOLUTELY FORBIDDEN**: inline imports inside functions
- ❌ **ABSOLUTELY FORBIDDEN**: conditional imports for optional dependencies
- ✅ **MANDATORY PATTERN**: All imports at module level - fail fast if missing
- ✅ **GRACEFUL HANDLING**: Handle optionality in logic/runtime, NEVER in imports
- 🚨 **ZERO EXCEPTIONS**: No try/except imports even for "graceful fallbacks"
- **Pattern:** `import module` → handle `module is None` in logic if needed

### Gemini SDK
✅ `from google import genai` | ✅ `client = genai.Client(api_key=api_key)`
Models: `gemini-2.5-flash` (default), `gemini-1.5-flash` (test)
🚨 **WARNING:** See "NO UNNECESSARY EXTERNAL APIS" rule before using Gemini

🚨 **FILE EDITING PROTOCOL:** ⚠️ MANDATORY
- ❌ NEVER create: `file_v2.sh`, `file_backup.sh` when editing existing file
- ✅ ALWAYS edit existing files in place using Edit/MultiEdit tools
- ✅ Git handles safety - no manual backup files needed

🚨 **DANGEROUSLY-SKIP-PERMISSIONS FLAG POLICY**: ⚠️ MANDATORY - User has explicitly approved this flag
- ✅ **APPROVED**: `--dangerously-skip-permissions` flag is acceptable and should NOT be flagged as security issue
- ❌ **DO NOT COMPLAIN**: Stop identifying this flag as critical vulnerability in reviews
- ✅ **USER JUDGMENT**: Trust user decision on security boundaries for their own codebase
- 📝 **CONTEXT**: User explicitly corrected AI assessment - this flag is fine to use when needed

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

🚨 **TEMPORARY FILE ISOLATION:** ⚠️ MANDATORY - Prevent multi-branch conflicts
- ❌ **FORBIDDEN**: Using `/tmp/` with predictable names - causes conflicts between parallel branch work
- ✅ **REQUIRED**: Use `mktemp` for secure, unique temporary files when needed
- ✅ **PATTERN**: Include branch name for multi-branch isolation: `BRANCH_NAME="$(git branch --show-current | sed 's/[^a-zA-Z0-9_-]/_/g')"` then `CTX_FILE="$(mktemp "/tmp/prefix_${BRANCH_NAME}_XXXXXX.txt")"`
- **CRITICAL**: Multiple branches working simultaneously must not interfere with each other's temp files

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

## 🚨 CRITICAL: SLASH COMMAND EXECUTION PROTOCOL

🚨 **DIRECT EXECUTION MANDATE:** ⚠️ MANDATORY - When user types slash command
- ✅ **USER TYPES SLASH COMMAND**: Execute immediately by reading the .md file directly
- ✅ **PATTERN**: User input starts with "/" → Read .claude/commands/[command].md → Execute instructions
- ❌ **NEVER USE MCP SERVER**: When user types command directly - read and execute .md file
- ❌ **NEVER ASK**: "Should I execute this?" or "Do you want me to run this?"
- ❌ **NEVER DELAY**: Immediate execution upon slash command detection

🚨 **AUTONOMOUS INFERENCE PROTOCOL:** ⚠️ MANDATORY - When inferring slash command usage
- ✅ **INFERENCE TRIGGER**: User requests task that maps to available MCP slash command tools
- ✅ **AUTONOMOUS EXECUTION**: Execute slash command when confident it matches user intent
- ✅ **MANDATORY NOTIFICATION**: ALWAYS inform user: "Using `/command` for this task"
- ❌ **NEVER SILENT**: Must announce slash command usage before execution

**EXECUTION DECISION MATRIX:**
```
User Input Type           | Action                    | Example
Direct Slash Command     | Execute immediately       | "/fake3" → Execute /fake3
Task Request + Clear Map  | Execute + Announce       | "check fake code" → "Using /fake3" + Execute
Task Request + Uncertain | Ask for clarification    | "analyze something" → Ask which tool
```

**SLASH COMMAND INTELLIGENCE PATTERNS:**
- **Code Quality**: "check fake code", "detect placeholders" → Use `/fake3`
- **Git Operations**: "push to PR", "create PR" → Use `/pushl`, `/pr`
- **Testing**: "run tests", "fix failing tests" → Use `/test`, `/tester`
- **Analysis**: "review code", "find issues" → Use `/copilot`, `/review`
- **Performance**: "optimize", "improve speed" → Use `/cerebras`, `/optimize`

🚨 **MCP SERVER INTEGRATION:** ⚠️ FOR AUTONOMOUS AI AGENTS ONLY
- ✅ **AUTONOMOUS AGENTS**: AI agents can use MCP slash command server for background execution
- ✅ **USER COMMANDS**: When user types "/command", read .md file directly, NOT via MCP
- ✅ **HYBRID APPROACH**: Direct execution for user, MCP for autonomous agents
- ❌ **NO MCP FOR USER**: Never use MCP server when user explicitly types slash command

## Special Protocols

**PR Comments:** Address ALL sources. Status: ✅ RESOLVED | 🔄 ACKNOWLEDGED | 📝 CLARIFICATION | ❌ DECLINED
**PR References:** Include full URL - "PR #123: https://github.com/user/repo/pull/123"

🚨 **CRITICAL: COMMENT REPLY ZERO-SKIP PROTOCOL**: ⚠️ MANDATORY - Every Comment Gets Response
- ❌ **NEVER SKIP COMMENTS**: Every single comment MUST receive either implementation OR explicit "NOT DONE" response
- ❌ **NO SILENT SKIPPING**: Comments without responses indicate workflow failure, not system success
- ✅ **IMPLEMENTATION RESPONSE**: If comment is reasonable/actionable, implement the requested change
- ✅ **NOT DONE RESPONSE**: If comment cannot be implemented, respond "NOT DONE: [specific reason why]"
- 🔄 **WORKFLOW**: 1) Read comment → 2) Analyze feasibility → 3) Either implement OR respond "NOT DONE: [reason]"
- **EXAMPLE NOT DONE**: "NOT DONE: Architecture docs belong in separate documentation file"
- **EXAMPLE NOT DONE**: "NOT DONE: Requires breaking API change that affects existing users"
- **ANTI-PATTERN**: Concluding "system working correctly" when comments have no responses
- **SUCCESS METRIC**: 100% comment response rate (implementation + NOT DONE explanations)

### PR Labeling
**Auto-labeling** based on git diff vs origin/main:
- **Type:** bug (fix/error), feature (add/new), improvement (optimize/enhance), infrastructure (yml/scripts)
- **Size:** small <100, medium 100-500, large 500-1000, epic >1000 lines

**Commands:** `/pushl` (auto-label), `/pushl --update-description`, `/pushl --labels-only`

## Quick Reference

- **Test:** `TESTING=true vpython mvp_site/test_file.py` (from root)
- **All Tests:** `./run_tests.sh` (CI simulation by default)
- **Local Mode:** `./run_tests.sh --no-ci-sim`
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



## 🚨 CONTEXT OPTIMIZATION PROTOCOLS ⚠️ MANDATORY

🚀 **DEPLOYED: Context Optimization System Active**

**Target Achieved**: 79K → 45K token cache reduction (68.8% improvement)
**Session Improvement**: 5.4min → 18min (233% improvement)

### Real-Time Optimization Rules:

🔧 **Tool Selection Hierarchy** (Layer 1 - 80% Impact):
1. **Serena MCP FIRST** - ALWAYS use `mcp__serena__*` for semantic operations before Read tool
2. **Targeted Reads** - Use Read tool with `limit=100` parameter (max 100 lines per read)
3. **Grep Targeted** - Use `head_limit=10` parameter, pattern search before full file reads
4. **Batch Operations** - MultiEdit for multiple changes, batch tool calls in single messages
5. **Bash Fallback** - Only when other tools insufficient

🎯 **Auto-Optimization Rules** (Apply Every Session):
- **Git Batching**: Combine `git status`, `git branch`, `git diff` into single calls
- **MCP Substitution**: `Grep` → `mcp__serena__search_for_pattern` for code searches
- **Read Limits**: Auto-apply `limit=1000` for large files
- **Session Init**: Use Serena MCP for first 3 codebase operations

⚡ **Session Longevity** (Layer 2 - 60% Impact):
- **Auto-checkpoint** at 60% context usage (not 80%)
- **Warning alerts** at 40% context usage
- **Semantic search** instead of loading multiple comparison files
- **Streamlined responses** - count-only outputs, no verbose listings
- **Remove --verbose flags** from all script executions

🧠 **Workflow Intelligence** (Layer 3 - 40% Impact):
- **Predictive alerts** for context exhaustion scenarios
- **Background monitoring** for continuous optimization
- **Development velocity** optimized for 15-20+ minute sessions
- **Mental caching** - avoid re-reading same files within session

### Mandatory Behavioral Changes:
- ✅ **ALWAYS**: Use Serena MCP for code exploration before Read tool
- ✅ **ALWAYS**: Use `limit` parameter on Read operations (100 lines max)
- ✅ **ALWAYS**: Use `head_limit` parameter on Grep operations (10 results max)
- ✅ **ALWAYS**: Batch multiple tool calls in single messages
- ❌ **NEVER**: Read entire large files without limits
- ❌ **NEVER**: Use verbose output modes unless debugging specific issues
- ❌ **NEVER**: Re-read files already examined in current session

### Context Health Monitoring:

✅ **ACTIVE MONITORING**: Real-time context usage feedback via hooks
✅ **OPTIMIZATION HOOKS**: `pre_command_optimize.py`, `context_monitor.py`, `command_output_trimmer.py`
✅ **AUTOMATED TRIGGERS**: Context checkpointing at 60% threshold
✅ **PERFORMANCE TRACKING**: Session duration and token efficiency metrics

**Usage**: Context optimization runs automatically via hooks. Follow tool hierarchy and behavioral changes for optimal sessions.

## Additional Documentation

**Files:** `.cursor/rules/lessons.mdc` (lessons), `.cursor/rules/rules.mdc` (cursor), `.cursor/rules/examples.md`, `.cursor/rules/validation_commands.md`
