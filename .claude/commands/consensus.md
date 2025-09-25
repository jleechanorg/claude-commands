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
Run all 5 agents simultaneously using Task tool parallel execution with proper context and role definitions:

### Consultant Supermajority Overlay

To unlock the "consultant consensus supermajority" workflow referenced in recent playbooks, layer the
standard `/consensus` flow with an explicit PASS/REWORK vote tally across the consultant agents. The
goal is to require broad agreement from the external specialist agents before declaring success.

- **Eligible voters**: `codex-consultant`, `gemini-consultant`, `cursor-consultant`, and the new
  `code-centralization-consultant`. The internal `code-review` agent still runs for architecture
  validation, but it is not counted toward the consultant supermajority. (Rationale: keep
  architectural authority with Claude core while treating external tools as an advisory bloc.)
- **Threshold**: Minimum 3-of-4 consultant votes must return `PASS` with confidence ≥7. If that
  bar is not met, two consultants with confidence ≥9 may still declare a provisional PASS provided
  every outstanding concern is explicitly marked as deferrable (via an `accepted_deferrals` list in
  the responsible consultant outputs). Each consultant that fails to meet the ≥7 confidence bar—
  whether they voted `REWORK` or issued a low-confidence `PASS`—must log the deferrals for their
  own domain (e.g., duplication, security, performance) along with mitigation plans and follow-up
  owners. Consultants counted toward approval cannot self-certify deferrals they rely on.
- **Escalation rule**: If two consecutive rounds fail to achieve the consultant supermajority, halt
  automatic approvals and surface the conflicting findings verbatim in the report. This ensures
  humans review disagreements rather than forcing another automated round.

Implementation guidance:

1. Run the four consultant agents in parallel (as already done for `/consensus`).
2. Capture each agent's PASS/REWORK verdict and numeric confidence.
3. After collecting responses, compute the supermajority state:
   ```python
    def get_deferrals(agent):
        output = getattr(agent, "output", None)
        if isinstance(output, dict):
            return output.get("accepted_deferrals")
        return None

    passes = [a for a in consultant_agents if a.verdict == "PASS" and a.confidence >= 7]
    high_confidence = [a for a in passes if a.confidence >= 9]
    below_threshold = [
        a for a in consultant_agents
        if not (a.verdict == "PASS" and a.confidence >= 7)
    ]
    deferrals_ok = bool(below_threshold) and all(get_deferrals(a) for a in below_threshold)
    if len(passes) >= 3:
        consultant_supermajority = True
    elif len(passes) == 2 and len(high_confidence) == 2 and deferrals_ok:
        consultant_supermajority = True
    else:
        consultant_supermajority = False
   ```
4. Annotate the round summary with `Consultant Supermajority: PASS|FAIL` so downstream tooling can
   react automatically.
5. Only mark the overall round as PASS when both conditions hold:
   - Core consensus rules (all agents PASS + average confidence >7)
   - Consultant supermajority evaluated to `True`

This overlay keeps `/consensus` fast while ensuring the external consultant network (Codex, Gemini,
Cursor) broadly agrees before a change moves forward. Treat the supermajority flag as a hard gate for
automation and as a status indicator to highlight conflicting consultant guidance.

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

- **`cursor-consultant`** - Contrarian analysis and practical reality checks
  - **Context**: Solo developer reality vs enterprise theoretical concerns
  - **Focus**: Practical deployment concerns, real-world failure modes, pragmatic tradeoffs
  - **Implementation**: `Task(subagent_type="cursor-consultant", description="...", prompt="...")`
- **`code-centralization-consultant`** - Shared utility and duplication eradication specialist
  - **Context**: Works best when multiple files implement similar behavior or abstractions
  - **Focus**: Detect duplicated logic, recommend shared helpers, plan migrations to common modules
  - **Implementation**: `Task(subagent_type="code-centralization-consultant", description="...", prompt="...")`

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
   - **CONSENSUS_PASS**: All agents PASS + average confidence >7
   - **CONSENSUS_REWORK**: Any agent critical issues OR average confidence <5
   - **MIXED_SIGNALS**: Disagreement between agents - document conflicts

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
       env TESTING=true vpython -m pytest
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

**Auto-Detection of Test Commands**:
```bash
# Project test command detection hierarchy
if [ -f "package.json" ] && npm run --silent 2>/dev/null | grep -q "test"; then
    npm test
elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    if command -v vpython >/dev/null 2>&1; then
        env TESTING=true vpython -m pytest
    elif command -v python3 >/dev/null 2>&1; then
        env TESTING=true python3 -m pytest
    else
        env TESTING=true python -m pytest
    fi
elif [ -f "run_tests.sh" ] && [ -x "run_tests.sh" ]; then
    ./run_tests.sh
elif [ -f "Makefile" ] && grep -q "^test:" Makefile; then
    make test
else
    echo "No automated tests detected - manual validation required"
fi
```

5. **Round Completion Decision**
   - **CONSENSUS_PASS**: All agents PASS + average confidence >7 + all tests pass
   - **CONSENSUS_REWORK**: Any agent critical issues OR test failures OR average confidence <5
   - **TEST_FAILURE_ABORT**: Any non-zero test/lint exit (critical or blocking) aborts the round immediately
   - **ROUND_LIMIT_REACHED**: Maximum 3 rounds completed

#### Consensus Calculation Rules:

- **✅ SUCCESS**: CONSENSUS_PASS achieved (workflow complete)
- **🔄 CONTINUE**: REWORK status + round < 3 + tests pass (next round)
- **❌ ABORT**: TEST_FAILURE_ABORT or critical agent blockers (stop immediately)
- **⚠️ LIMIT**: ROUND_LIMIT_REACHED (document remaining issues)

The loop stops immediately when a round achieves PASS status or after three rounds (whichever occurs first).

#### Early Termination Triggers:

- **✅ CONSENSUS_PASS**: All agents agree + high confidence + tests pass
- **❌ CRITICAL_BUG**: Any agent reports severity 9-10 issue
- **❌ TEST_FAILURE**: Core functionality broken by Phase 4 changes
- **❌ COMPILATION_ERROR**: Code doesn't compile/parse after changes

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
