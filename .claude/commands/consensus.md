---
description: /consensus Command - Multi-Agent Agreement Code Review
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Parallel Agent Execution (2025 Optimization)

**Action Steps:**
Run all 5 agents simultaneously using Task tool parallel execution with proper context and role definitions:

## 📋 REFERENCE DOCUMENTATION

# /consensus Command - Multi-Agent Agreement Code Review

**Purpose**: Fast consensus-building review for solo MVP projects using 2025 multi-agent protocols. Simple 3-round maximum with early termination when agents agree. Focus on architecture and practical outcomes over enterprise-grade security.

**⚡ Performance**: 2-5 minutes total with parallel agent execution and smart early termination.

**🚀 Solo Unlaunched MVP Context**: Optimized for pre-launch projects with ZERO external users. Only serious external attacker security vulnerabilities matter (SQL injection, RCE, auth bypass). Enterprise security theater is counterproductive. GitHub rollbacks provide safety net.

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
5. **Basic credential filtering**: Remove obvious API keys/passwords from context (unlaunched MVP with zero external users - basic filtering sufficient)
6. **Assemble review bundle** containing: PR description, latest commit message, diff summaries, and local-only edits.

### Simplified Consensus Rules

**Fast Multi-Agent Consensus**: Run 5 agents in parallel and calculate simple majority agreement:
- **Eligible agents**: `code-review`, `codex-consultant`, `gemini-consultant`, `cursor-consultant`, `code-centralization-consultant` (5 total)
- **Success threshold**: 3+ of 5 agents PASS with average confidence ≥6
- **Failure threshold**: 3+ agents REWORK OR average confidence <5
- **Mixed signals**: Document disagreements, proceed with majority decision

**Simple Consensus Calculation**:
1. Run all 5 agents in parallel using Task tool
2. Collect PASS/REWORK + confidence (1-10) from each agent
3. Calculate results:
   - **CONSENSUS_PASS**: 3+ agents PASS AND average confidence ≥6
   - **CONSENSUS_REWORK**: 3+ agents REWORK OR average confidence <5
   - **MIXED_SIGNALS**: Document conflicts, use majority decision

**Agent Specialization**:
- **`code-review`**: Architecture validation, correctness, maintainability
- **`codex-consultant`**: System design patterns, scalability foundations
- **`gemini-consultant`**: 2025 best practices, performance optimization
- **`cursor-consultant`**: Practical concerns, deployment readiness
- **`code-centralization-consultant`**: Duplication detection, shared utility recommendations

### Enhanced Agent Context & Execution Framework

**Agent Infrastructure**: Uses existing `Task` tool with `subagent_type` parameter for parallel multi-agent coordination. Follows proven patterns from `/reviewdeep` and `/arch` commands with optimized execution orchestration.

**Execution Guards**: Per-agent timeout (180 seconds), token caps (5000 tokens max), and maximum 10 findings per round to prevent runaway executions. Enhanced with context-aware resource allocation.

**Command Orchestration**: Delegates to `/execute` for intelligent coordination following `/reviewdeep` optimization patterns:

**Agent Execution**: Launch 5 agents in parallel using Task tool with 180-second timeout:

1. **Architecture Review**: `code-review` agent for correctness, maintainability, architecture quality
2. **System Design**: `codex-consultant` agent for scalability, technical architecture patterns
3. **Best Practices**: `gemini-consultant` agent for 2025 patterns, performance optimization
4. **Reality Check**: `cursor-consultant` agent for practical concerns, deployment readiness
5. **Code Centralization**: `code-centralization-consultant` agent for duplication detection, shared utility recommendations

**Solo MVP Context Applied to All Agents**:
- Pre-launch product with ZERO external users
- GitHub rollback safety available
- Focus on real bugs, architecture, and serious security vulnerabilities only
- Skip enterprise security theater and theoretical concerns

**Implementation Details**:
- **`code-review`**: `Task(subagent_type="code-review", description="Architecture validation", prompt="...")`
- **`codex-consultant`**: `Task(subagent_type="codex-consultant", description="System design analysis", prompt="...")`
- **`gemini-consultant`**: `Task(subagent_type="gemini-consultant", description="Best practices review", prompt="...")`
- **`cursor-consultant`**: `Task(subagent_type="cursor-consultant", description="Practical reality check", prompt="...")`
- **`code-centralization-consultant`**: `Task(subagent_type="code-centralization-consultant", description="Duplication analysis", prompt="...")`

**Speed Optimizations**:
- **Parallel execution**: All agents run simultaneously (not sequential)
- **Early termination**: Stop on architectural blockers or critical bugs
- **Simple consensus**: Agents provide PASS/REWORK verdict with confidence (1-10)
- **Evidence required**: Findings must include file:line references
- **MVP Context**: GitHub rollbacks available, focus on architecture over security paranoia

## Fast Consensus Loop (3 Rounds Max)

Streamlined workflow optimized for speed and simplicity:

1. **Parallel Agent Consultation** (2-3 minutes)
   - Launch all 5 agents simultaneously using Task tool with full context
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
   - **CONSENSUS_PASS**: 3+ agents PASS + average confidence ≥6
   - **CONSENSUS_REWORK**: 2+ agents REWORK OR average confidence <5
   - **MIXED_SIGNALS**: Document conflicts, proceed with majority decision

3. **Quick Fix Application** (If REWORK, 1-2 minutes)
   - Apply highest-confidence architectural fixes with clear file:line references
   - Skip complex remediation planning - fix obvious issues immediately
   - Document all changes made during this round

4. **Automated Test Validation** (1-3 minutes)
   - **Syntax Validation**: Quick linting/parsing checks
     ```bash
     # Auto-detect and run project-specific linters
     if command -v npm >/dev/null 2>&1 && [ -f package.json ] && npm run --silent 2>/dev/null | grep -q "lint"; then
       npm run lint
     elif command -v eslint >/dev/null 2>&1; then
       eslint .
     elif command -v flake8 >/dev/null 2>&1; then
       flake8 .
     elif command -v ruff >/dev/null 2>&1; then
       ruff check .
     else
       echo "No supported linter found - manual validation required"
     fi
     ```
   - **Unit Tests**: Focused tests for modified components
     ```bash
     # Auto-detect test framework and run relevant tests
     if command -v npm >/dev/null 2>&1 && [ -f package.json ] && npm run --silent 2>/dev/null | grep -q "test"; then
       npm test
     elif command -v vpython >/dev/null 2>&1; then
       env TESTING=true python -m pytest
     elif command -v python3 >/dev/null 2>&1; then
       env TESTING=true python3 -m pytest
     elif command -v python >/dev/null 2>&1; then
       env TESTING=true python -m pytest
     else
       echo "No recognized test runner found - manual validation required"
     fi
     ```
   - **Integration Tests**: If APIs/interfaces changed
     ```bash
     # Run integration test suite if available
     npm run test:integration \
       || ( [ -x ./run_tests.sh ] && ./run_tests.sh ) \
       || ( [ -x ./run_ui_tests.sh ] && ./run_ui_tests.sh mock )
     ```
   - **Manual Validation**: User-guided spot checks if automated tests insufficient

**Context-Aware Test Selection**:
- **High Context**: Full test suite validation
- **Medium Context**: Targeted test execution based on changed files
- **Low Context**: Essential syntax and unit tests only

**Simplified Test Detection**:
```bash

# Safe test command detection with proper validation

if command -v npm >/dev/null 2>&1 && [ -f "package.json" ] && npm run --silent 2>/dev/null | grep -q "test"; then
    timeout 300 npm test
elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    timeout 300 env TESTING=true python -m pytest 2>/dev/null || timeout 300 env TESTING=true python3 -m pytest
elif [ -f "run_tests.sh" ] && [ -x "run_tests.sh" ]; then
    timeout 300 ./run_tests.sh
else
    echo "No automated tests detected - skipping test validation"
fi
```

5. **Round Completion Decision**
   - **CONSENSUS_PASS**: 3+ agents PASS + average confidence ≥6 + tests pass
   - **CONSENSUS_REWORK**: 2+ agents REWORK OR test failures OR average confidence <5
   - **TEST_FAILURE_ABORT**: Critical test failures abort the round
   - **ROUND_LIMIT_REACHED**: Maximum 3 rounds completed

#### Consensus Calculation Rules:

- **✅ SUCCESS**: CONSENSUS_PASS achieved (workflow complete)
- **🔄 CONTINUE**: REWORK status + round < 3 + tests pass (next round)
- **❌ ABORT**: TEST_FAILURE_ABORT or critical agent blockers (stop immediately)
- **⚠️ LIMIT**: ROUND_LIMIT_REACHED (document remaining issues)

The loop stops immediately when a round achieves PASS status or after three rounds (whichever occurs first).

#### Early Termination Triggers:

- **✅ CONSENSUS_PASS**: 3+ agents PASS + average confidence ≥6 + tests pass
- **❌ CRITICAL_BUG**: Any agent reports severity 9-10 issue
- **❌ TEST_FAILURE**: Core functionality broken by Phase 4 changes
- **❌ COMPILATION_ERROR**: Code doesn't compile/parse after changes

## Simple Consensus Rules (2025 MVP Optimization)

- **Speed First**: Parallel execution, early termination, 3-round limit
- **Evidence Based**: All findings require file:line references + confidence scores
- **Clear Thresholds**: PASS ≥6 confidence, REWORK <5 confidence, mixed signals documented
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

### **Enhanced Agent Prompt Template** (Context-Aware Multi-Agent Analysis)

Following proven patterns from `/reviewdeep` and `/arch` commands with enhanced context specialization:

```markdown
[Agent Role] consensus analysis of [target] for solo MVP project context.

**ENHANCED CONTEXT FRAMEWORK**:
- **Project Type**: Solo MVP (pre-launch, GitHub rollbacks available for safety)
- **Current Scope**: [PR details, modified files, scope definition]
- **Infrastructure**: Working multi-agent consensus system using Task tool parallel execution
- **Agent Network**: Part of 4-agent consensus (code-review, codex-consultant, gemini-consultant, cursor-consultant)
- **Goal**: Fast consensus-building with 3-round maximum, early termination on agreement
- **Focus Balance**: Implementation correctness AND architecture quality (both strategic and tactical)

**ROLE-SPECIFIC CONTEXT SPECIALIZATION**:
- **code-review**: Architectural correctness & MVP maintainability expert
- **codex-consultant**: System design & scaling intelligence specialist
- **gemini-consultant**: 2025 best practices & optimization patterns authority
- **cursor-consultant**: Pragmatic reality check & deployment readiness validator

**COMPREHENSIVE ANALYSIS FRAMEWORK**:
1. **Strategic Layer**: [Role-specific expertise], architecture patterns, system design
2. **Tactical Layer**: Implementation logic, code correctness, error handling
3. **Consensus Layer**: Inter-agent agreement consideration, conflict resolution
4. **Solo MVP Reality**: No team constraints, practical deployment focus, rollback safety net
5. **Speed Optimization**: Fast analysis with early termination on critical issues

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

**OUTPUT REQUIREMENTS FOR CONSENSUS**:
- **Verdict**: PASS/REWORK with confidence score (1-10)
- **Evidence**: Specific issues with file:line@commit-sha references (MANDATORY)
- **Code Anchors**: 3-5 line snippet anchors for validation
- **Dual Analysis**: Both strategic AND tactical concerns addressed
- **Implementation Focus**: Real bugs, logic errors, deployment blockers
- **Consensus Awareness**: Consider inter-agent agreement and conflict resolution
- **Solo MVP Readiness**: Practical deployment assessment for solo developer

**AGENT-SPECIFIC CONTEXT ENHANCEMENT**:
```

### **Specialized Agent Context Templates**

Each agent receives role-specific context enhancement following successful patterns from `/reviewdeep` and `/arch`:

#### **`code-review` Agent Context**:

```markdown
ARCHITECTURAL CORRECTNESS & MVP MAINTAINABILITY analysis for solo MVP consensus.

**Your Specialization**: Architecture quality, SOLID principles, code maintainability
**Context Awareness**: You are the architectural authority in 4-agent consensus system
**Focus Priority**: Design patterns, technical debt, scalability foundations
**Consensus Role**: Architecture quality gatekeeper - block on fundamental design flaws
**Solo MVP Lens**: Practical architecture that supports rapid iteration and deployment
```

#### **`codex-consultant` Agent Context**:

```markdown
SYSTEM DESIGN & SCALING INTELLIGENCE analysis for solo MVP consensus.

**Your Specialization**: Advanced system architecture, performance, distributed patterns
**Context Awareness**: You provide scaling perspective in consensus-building process
**Focus Priority**: Performance bottlenecks, database design, system integration patterns
**Consensus Role**: Scalability validator - ensure architecture supports growth
**Solo MVP Lens**: Foundation for scaling without over-engineering initial implementation
```

#### **`gemini-consultant` Agent Context**:

```markdown
2025 BEST PRACTICES & OPTIMIZATION PATTERNS analysis for solo MVP consensus.

**Your Specialization**: Modern frameworks, security best practices, optimization patterns
**Context Awareness**: You ensure modern standards in consensus evaluation
**Focus Priority**: Latest patterns, security (practical not paranoid), performance optimization
**Consensus Role**: Best practices validator - ensure code follows 2025 standards
**Solo MVP Lens**: Modern practices adapted for solo developer speed and efficiency
```

#### **`cursor-consultant` Agent Context**:

```markdown
PRAGMATIC REALITY CHECK & DEPLOYMENT READINESS analysis for solo MVP consensus.

**Your Specialization**: Contrarian analysis, real-world deployment, practical concerns
**Context Awareness**: You are the final reality check in consensus process
**Focus Priority**: Deployment practicalities, real failure modes, solo developer workflow
**Consensus Role**: Reality validator - ensure recommendations are actually implementable
**Solo MVP Lens**: What actually works in production vs theoretical perfection
```

### **Dynamic Context Variables**

- `{PR_NUMBER}`: Auto-detected from current branch context
- `{FILE_LIST}`: From git diff and PR analysis
- `{TARGET_SCOPE}`: User-specified scope or default PR context
- `{MVP_STAGE}`: Pre-launch, rollback-safe development phase
- `{AGENT_NETWORK}`: 4-agent consensus system with role specializations
- `{CONSENSUS_ROUND}`: Current round (1-3) in consensus-building process

## Post-Run Clean Up

1. Ensure working tree cleanliness (`git status --short`).
2. If changes were made, restate next steps (commit, push, or request manual review).
3. Update Memory MCP with consensus patterns and successful issue resolutions.
4. Note: GitHub rollbacks available if any issues discovered post-merge.
