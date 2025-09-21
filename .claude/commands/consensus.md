# /consensus Command - Multi-Agent Agreement Code Review

**Purpose**: Fast consensus-building review for solo MVP projects using 2025 multi-agent protocols. Simple 3-round maximum with early termination when agents agree. Focus on architecture and practical outcomes over enterprise-grade security.

**⚡ Performance**: 2-5 minutes total with parallel agent execution and smart early termination.

**🚀 Solo MVP Context**: Optimized for pre-launch projects where rollbacks are easy via GitHub, enterprise security is overkill, and speed/architecture quality matter most.

## Usage
```
/consensus [<scope>]
/cons [<scope>]          # Alias
```
- **Default scope**: Current PR (if tracking a GitHub pull request) plus any local unmerged files.
- **Optional scope**: Specific file(s), folder(s), or PR number to narrow the review focus.

## Context Acquisition (Always Performed First)
1. **Detect active PR** using `gh pr status` or `git config branch.<name>.merge` to extract the PR number and remote.
2. **Record latest commit** with `git log -1 --stat`.
3. **Capture local changes**:
   - `git status --short` for staged/unstaged files.
   - `git diff --stat` and targeted `git diff` snippets for modified files.
4. **Verify synchronization with GitHub**:
   - Fetch PR files: `gh pr view <pr> --json files,headRefName,baseRefName`.
   - Confirm branch alignment (`git rev-parse HEAD` vs PR head SHA).
5. **Basic credential filtering**: Remove obvious API keys/passwords from context (solo MVP appropriate)
6. **Assemble review bundle** containing: PR description, latest commit message, diff summaries, and local-only edits.

## Parallel Agent Execution (2025 Optimization)
Run all 4 agents simultaneously using Task tool parallel execution with proper context and role definitions:

### Agent Context & Execution Framework

**Agent Infrastructure**: Uses existing `Task` tool with `subagent_type` parameter for parallel multi-agent coordination. This is the same infrastructure used successfully by `/reviewdeep` and `/arch` commands.

**Execution Guards**: Per-agent timeout (180 seconds), token caps (5000 tokens max), and maximum 10 findings per round to prevent runaway executions.

### Agent Role Definitions:

- **`code-review`** - Architecture, correctness, maintainability (MVP-focused)
  - **Context**: Solo MVP project, GitHub rollback safety net available
  - **Focus**: Architecture quality, real bugs, maintainability over enterprise security theater
  - **Implementation**: `Task(subagent_type="code-review", description="...", prompt="...")`

- **`codex-consultant`** - System design and scaling considerations
  - **Context**: Pre-launch MVP, architecture decisions can break without user impact
  - **Focus**: System design patterns, scalability foundations, technical architecture
  - **Implementation**: `Task(subagent_type="codex-consultant", description="...", prompt="...")`

- **`gemini-consultant`** - Best practices and optimization patterns
  - **Context**: 2025 best practices adapted for solo developer workflow
  - **Focus**: Modern patterns, performance optimization, framework alignment
  - **Implementation**: `Task(subagent_type="gemini-consultant", description="...", prompt="...")`

- **`grok-consultant`** - Contrarian analysis and practical reality checks
  - **Context**: Solo developer reality vs enterprise theoretical concerns
  - **Focus**: Practical deployment concerns, real-world failure modes, pragmatic tradeoffs
  - **Implementation**: `Task(subagent_type="grok-consultant", description="...", prompt="...")`

**Speed Optimizations**:
- **Parallel execution**: All agents run simultaneously (not sequential)
- **Early termination**: Stop on architectural blockers or critical bugs
- **Simple consensus**: Agents provide PASS/REWORK verdict with confidence (1-10)
- **Evidence required**: Findings must include file:line references
- **MVP Context**: GitHub rollbacks available, focus on architecture over security paranoia

## Fast Consensus Loop (3 Rounds Max)
Streamlined workflow optimized for speed and simplicity:

1. **Parallel Agent Consultation** (2-3 minutes)
   - Launch all 4 agents simultaneously using Task tool with full context
   - **Context Provided to Each Agent**:
     - Solo MVP project status (pre-launch, rollback safety available)
     - Current PR/branch context and file changes
     - Architecture focus over enterprise security concerns
     - GitHub rollback strategy as primary safety mechanism
     - 2025 best practices adapted for solo developer workflow
   - Each agent provides: PASS/REWORK + confidence (1-10) + specific issues
   - Early termination if any agent finds architectural blockers or critical bugs
   - Collect findings in structured format with file:line evidence
   - **Agent Context Awareness**: Each agent understands the working multi-agent system and MVP context

2. **Simple Consensus Calculation** (30 seconds)
   - **CONSENSUS_PASS**: All agents PASS + average confidence >7
   - **CONSENSUS_REWORK**: Any agent critical issues OR average confidence <5
   - **MIXED_SIGNALS**: Disagreement between agents - document conflicts

3. **Quick Fix Application** (If REWORK, 1-2 minutes)
   - Apply highest-confidence architectural fixes with clear file:line references
   - Skip complex remediation planning - fix obvious issues immediately
   - Run basic validation (syntax check, basic tests)
   - GitHub rollback available if issues arise

4. **Streamlined Validation**
   - Run essential tests only (not full suite per change)
   - Document changes with simple before/after summary
   - No complex test creation - focus on fixing existing issues

5. **Next Round Decision**
   - If CONSENSUS_PASS: workflow complete
   - If round < 3: continue with remaining issues
   - If round = 3: document final status and unresolved items

The loop stops immediately when a round achieves PASS status or after three rounds (whichever occurs first).

## Simple Consensus Rules (2025 MVP Optimization)
- **Speed First**: Parallel execution, early termination, 3-round limit
- **Evidence Based**: All findings require file:line references + confidence scores
- **Clear Thresholds**: PASS >7 confidence, REWORK <5 confidence, mixed signals documented
- **Architecture First**: Focus on system design, scalability, maintainability
- **Practical Focus**: Fix obvious issues, document complex disagreements for later
- **Basic Safety**: Filter obvious credentials, but don't over-engineer for solo MVP
- **GitHub Safety Net**: Easy rollbacks available for any problematic changes

## Output Format
```
# Consensus Review Report

## Summary
- Round count: <1-3>
- Final status: PASS | REWORK_LIMIT_REACHED
- Key validated areas

## Major Findings
| Round | Source Agent | File/Section | Severity | Resolution |
|-------|--------------|--------------|----------|------------|

## Implemented Fixes
- <bullet list of code/test updates per round>

## Round-by-Round Summaries
- Round <n>: <main conversation highlights>
  - code-review: <key takeaways>
  - codex-consultant: <key takeaways>
  - gemini-consultant: <key takeaways>
  - grok-consultant: <key takeaways>

## Remaining Follow-Ups
- <nitpicks or deferred improvements>
```
Include references to executed test commands and link to generated guideline docs if applicable.

## 🛡️ Solo MVP Developer Focus

Following reviewdeep.md patterns for solo developer optimization:

### **Practical Focus Areas**
- **Architecture Quality**: SOLID principles, design patterns, scalability
- **Real Bugs**: Logic errors, null pointers, race conditions, performance issues
- **Maintainability**: Code clarity, modular design, technical debt
- **Integration Issues**: API contracts, dependency management, data flow

### **Filtered Out (Not MVP Critical)**
- **Enterprise Security Theater**: Over-engineered input validation for trusted sources
- **Complex Compliance**: SOX, HIPAA, PCI-DSS (unless specifically needed)
- **Theoretical Attack Vectors**: Low-probability scenarios with minimal real-world risk
- **Over-Architected Patterns**: Complex enterprise patterns for simple MVP needs

### **Solo Developer Context Detection**
- **Trusted Sources**: GitHub API, npm registry, official documentation
- **Basic Validation**: Focus on user input, file uploads, dynamic queries
- **Rollback Strategy**: Leverage git/GitHub for quick recovery vs complex prevention

## 🔧 Agent Prompt Structure (Implementation Details)

Following `/reviewdeep` and `/arch` patterns for proper agent context:

### **Enhanced Agent Prompt Template** (Bot-Level Implementation Analysis)
```markdown
[Agent Role] analysis of [target] for solo MVP project context.

**Context**:
- Solo MVP project (pre-launch, GitHub rollbacks available)
- Current PR: [PR details]
- Modified files: [file list]
- Focus: Implementation correctness AND architecture quality
- Infrastructure: This is a working multi-agent system using Task tool parallel execution

**DUAL-LAYER ANALYSIS FRAMEWORK**:
1. **Strategic Layer**: [Role-specific focus areas], architecture, patterns
2. **Tactical Layer**: Implementation logic, shell scripting, error handling
3. **Solo MVP Context**: No team coordination, practical deployment focus
4. **Rollback Safety**: GitHub provides recovery, allow measured risk-taking

**FOCUSED ANALYSIS FOR SOLO MVP** (Bugs, Correctness, Critical Security Only):

**CRITICAL BUG DETECTION**:
- **Logic Errors**: Incorrect conditionals, off-by-one errors, null pointer exceptions
- **Runtime Failures**: Unhandled exceptions, type mismatches, missing error handling
- **Data Corruption**: Race conditions, concurrent access issues, state inconsistencies
- **Silent Failures**: Operations that fail without notification, masked errors

**MAJOR SECURITY VULNERABILITIES**:
- **Injection Risks**: SQL injection, command injection, code injection in user inputs
- **Authentication Bypasses**: Login failures, session hijacking, token misuse
- **Data Exposure**: Hardcoded secrets, logging sensitive data, insecure storage
- **Input Validation**: Missing sanitization, buffer overflows, file upload dangers

**CORRECTNESS ISSUES**:
- **API Contract Violations**: Wrong HTTP codes, malformed responses, missing parameters
- **Database Problems**: Incorrect queries, transaction failures, constraint violations
- **File Operations**: Path traversal, permission errors, encoding issues
- **Configuration Errors**: Missing environment variables, incorrect defaults, broken connections

**CRITICAL DESIGN FLAWS** (Only Major Problems):
- **Single Points of Failure**: No fallbacks for critical operations
- **Broken Error Recovery**: Application crashes instead of graceful degradation
- **Security Architecture**: Fundamental auth/authorization design flaws
- **Data Loss Risks**: Operations that could permanently corrupt or lose user data

**PRODUCTION BLOCKERS**:
- **Deployment Failures**: Broken builds, missing dependencies, environment issues
- **Performance Killers**: Infinite loops, memory leaks, blocking operations
- **User Experience Breakers**: Crashes, data loss, complete feature failures
- **Security Holes**: Immediate exploit risks, credential exposure, admin bypasses

**SKIP THESE (Not Critical for Solo MVP)**:
- ❌ Code style preferences and formatting
- ❌ Complex architecture patterns and enterprise design
- ❌ Performance micro-optimizations and premature scaling
- ❌ Comprehensive documentation and process improvements
- ❌ Team workflow and collaboration patterns
- ❌ Advanced accessibility and compliance requirements

**Output Required**:
- PASS/REWORK verdict with confidence score (1-10)
- Specific issues with file:line@commit-sha references (MANDATORY) plus 3-5 line snippet anchors
- Both strategic AND tactical concerns
- Implementation bugs and logic errors
- Solo developer deployment readiness assessment

Provide [role] perspective covering BOTH architecture AND implementation correctness.
```

### **Context Variables Populated**
- `{PR_NUMBER}`: Auto-detected from current branch context
- `{FILE_LIST}`: From git diff and PR analysis
- `{TARGET_SCOPE}`: User-specified scope or default PR context
- `{MVP_STAGE}`: Pre-launch, rollback-safe development phase

## Post-Run Clean Up
1. Ensure working tree cleanliness (`git status --short`).
2. If changes were made, restate next steps (commit, push, or request manual review).
3. Update Memory MCP with consensus patterns and successful issue resolutions.
4. Note: GitHub rollbacks available if any issues discovered post-merge.
