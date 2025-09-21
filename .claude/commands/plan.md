# Plan Command - Execute with Approval

**Purpose**: Context-aware planning that requires user approval before implementation. **CONTEXT-AWARE PLANNING** with intelligent tool selection and universal composition.

**Usage**: `/plan` - Present context-aware execution plan with approval workflow

## 🧠 CONTEXT-AWARE PLANNING PROTOCOL

### Phase 0: Context Assessment (MANDATORY FIRST STEP)

**🔍 Context Assessment**: Every planning session MUST begin with context assessment:
```bash
# Check remaining context capacity to inform planning approach
/context
```

**Context-Informed Planning Strategy**:
- **High Context (60%+ remaining)**: Comprehensive analysis and detailed planning
- **Medium Context (30-60% remaining)**: Targeted analysis with efficient tool selection
- **Low Context (< 30% remaining)**: Lightweight planning with essential tasks only

### Phase 1: Strategic Analysis

**Memory Integration**: Automatically consults Memory MCP for relevant patterns, corrections, and user preferences.

**Guidelines Consultation**: Calls `/guidelines` for systematic mistake prevention and protocol compliance.

**Tool Selection Hierarchy** (Context-Optimized):
1. **Serena MCP** - Semantic analysis for efficient context usage
2. **Targeted Reads** - Limited file reads based on context capacity
3. **Focused Implementation** - Claude direct or /cerebras based on task size
4. **Context Preservation** - Reserve capacity for execution and validation

### Phase 2: Execution Plan Presentation

**📋 CONTEXT-ADAPTIVE PLAN FORMAT**:

**🧠 Context Status**: _____% remaining → **[High/Medium/Low]** complexity planning

**🎯 Universal Composition Strategy**:
- **Primary Command**: `/plan` (this command)
- **Composed Commands**: List of commands that will be naturally integrated
- **Tool Selection**: Context-aware hierarchy (Serena MCP → Read → /cerebras/Claude → Bash)

**⚡ Implementation Approach**:
- **Analysis Tasks**: Minimal context consumption using Serena MCP
- **Generation Tasks**: /cerebras for >10 delta lines, Claude for ≤10 lines (per CLAUDE.md)
- **Integration Tasks**: Efficient tool selection based on remaining context
- **Validation**: Context-appropriate testing depth

**🔀 Execution Method Decision** (Context-Optimized):
- **Parallel Tasks** (0 additional tokens): For simple, independent operations <30 seconds
  * Method: Background processes (&), GNU parallel, xargs, or batched tool calls
  * Best for: File searches, test runs, lint operations, data aggregation
- **Sequential Tasks**: For complex workflows requiring coordination >5 minutes
  * Method: Step-by-step with context monitoring
  * Best for: Feature implementation, architectural changes, complex integrations
- **Reference**: See [parallel-vs-subagents.md](./parallel-vs-subagents.md) for full decision criteria

**🚀 Execution Sequence** (Context-Optimized):
1. **Quick Discovery**: Use Serena MCP for targeted analysis
2. **Smart Generation**: /cerebras for large tasks, Claude for integration
3. **Efficient Validation**: Context-appropriate testing and verification
4. **Clean Integration**: Minimal overhead for final steps

**Timeline**: _____ minutes (context-optimized approach)

### Phase 3: Approval Requirement

**❌ NEVER proceed without explicit user approval**

User must respond with "APPROVED" or specific modifications before execution begins.

### Phase 4: Execute Protocol

**After approval, implements the plan directly with context awareness**:
- Monitor context usage throughout execution
- Apply context-saving strategies when needed
- Use universal composition with other commands naturally
- Preserve context for testing and validation

### Phase 5: Consensus Validation Loop (3 Rounds Max)

**🎯 Multi-Agent Quality Assurance with Test Validation**

After Phase 4 execution, automatically initiate consensus validation to ensure code quality and system stability.

#### Round Structure (Repeat up to 3 times):

**1. Parallel Agent Consensus** (2-3 minutes)
- Launch 4 specialized agents simultaneously using Task tool:
  - `code-review`: Architecture, correctness, maintainability
  - `codex-consultant`: System design and scaling considerations
  - `gemini-consultant`: Best practices and optimization patterns
  - `grok-consultant`: Contrarian analysis and practical reality checks
- Each agent provides: PASS/REWORK + confidence (1-10) + specific issues with file:line references
- Early termination on architectural blockers or critical bugs
- **Execution Guards**: 180-second timeout per agent, 5000 token cap, max 10 findings per round

**2. Immediate Code Changes** (1-2 minutes)
- Apply highest-confidence fixes from agent recommendations
- Focus on clear, actionable changes with specific file:line references
- Skip complex architectural refactoring in favor of quick wins
- Document all changes made during this round

**3. Automated Test Validation** (1-3 minutes)
- **Syntax Validation**: Quick linting/parsing checks
  ```bash
  # Auto-detect and run project-specific linters
  if command -v npm >/dev/null 2>&1 && [ -f package.json ] && npm run --silent | grep -q "^  lint$"; then
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
  if command -v npm >/dev/null 2>&1 && [ -f package.json ] && npm run --silent | grep -q "^  test$"; then
    npm test
  elif command -v vpython >/dev/null 2>&1; then
    TESTING=true vpython -m pytest
  elif command -v python >/dev/null 2>&1; then
    python -m pytest
  else
    echo "No recognized test runner found - manual validation required"
  fi
  ```
- **Integration Tests**: If APIs/interfaces changed
  ```bash
  # Run integration test suite if available
  npm run test:integration || ./run_tests.sh || ./run_ui_tests.sh mock
  ```
- **Manual Validation**: User-guided spot checks if automated tests insufficient

**4. Round Completion Decision**
- **CONSENSUS_PASS**: All agents PASS + average confidence >7 + all tests pass
- **CONSENSUS_REWORK**: Any agent critical issues OR test failures OR average confidence <5
- **TEST_FAILURE_ABORT**: Any non-zero test/lint exit (critical or blocking) aborts the round immediately
- **ROUND_LIMIT_REACHED**: Maximum 3 rounds completed

#### Consensus Calculation Rules:

- **✅ SUCCESS**: CONSENSUS_PASS achieved (workflow complete)
- **🔄 CONTINUE**: REWORK status + round < 3 + tests pass (next round)
- **❌ ABORT**: TEST_FAILURE_ABORT or critical agent blockers (stop immediately)
- **⚠️ LIMIT**: ROUND_LIMIT_REACHED (document remaining issues)

#### Test Strategy per Round:

**Context-Aware Test Selection**:
- **High Context**: Full test suite validation
- **Medium Context**: Targeted test execution based on changed files
- **Low Context**: Essential syntax and unit tests only

**Auto-Detection of Test Commands**:
```bash
# Project test command detection hierarchy
if [ -f "package.json" ] && npm run --silent | grep -q "^  test$"; then
    npm test
elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
    TESTING=true vpython -m pytest
elif [ -f "run_tests.sh" ]; then
    ./run_tests.sh
elif [ -f "Makefile" ] && grep -q "test" Makefile; then
    make test
else
    echo "No automated tests detected - manual validation required"
fi
```

#### Integration with /consensus Infrastructure:

**Agent Context Template** (Applied to each agent):
```markdown
[Agent Role] analysis for /plan execution validation in solo MVP context.

**Execution Context**:
- Phase 4 implementation completed
- Changes made: [list of files modified]
- Test results: [previous round test outcomes]
- Round: [1-3] of consensus validation

**ENHANCED VALIDATION FOCUS** (Include Implementation Details):
1. **Architecture & Integration**: System design, patterns, codebase alignment
2. **Implementation Logic**: Command chains, error handling, edge cases
3. **Shell/Script Analysis**: Bash operators, command detection, failure masking
4. **Error Propagation**: Test failures, silent errors, `||` operator behavior
5. **Edge Cases**: Package.json parsing, command availability, timeout handling
6. **Runtime Behavior**: Actual execution flow vs documented intent

**FOCUSED BUG & SECURITY ANALYSIS** (Solo MVP Priority):

**CRITICAL BUG DETECTION**:
- Logic errors: Incorrect conditionals, off-by-one errors, null pointer exceptions
- Runtime failures: Unhandled exceptions, type mismatches, missing error handling
- Data corruption: Race conditions, concurrent access issues, state inconsistencies
- Silent failures: Operations that fail without notification, masked errors

**MAJOR SECURITY VULNERABILITIES**:
- Injection risks: SQL injection, command injection, code injection in user inputs
- Authentication bypasses: Login failures, session hijacking, token misuse
- Data exposure: Hardcoded secrets, logging sensitive data, insecure storage
- Input validation: Missing sanitization, buffer overflows, file upload dangers

**CORRECTNESS ISSUES**:
- API contract violations: Wrong HTTP codes, malformed responses, missing parameters
- Database problems: Incorrect queries, transaction failures, constraint violations
- File operations: Path traversal, permission errors, encoding issues
- Configuration errors: Missing environment variables, incorrect defaults, broken connections

**PRODUCTION BLOCKERS**:
- Deployment failures: Broken builds, missing dependencies, environment issues
- Performance killers: Infinite loops, memory leaks, blocking operations
- User experience breakers: Crashes, data loss, complete feature failures
- Security holes: Immediate exploit risks, credential exposure, admin bypasses

**CRITICAL DESIGN FLAWS** (Only Major Problems):
- Single points of failure: No fallbacks for critical operations
- Broken error recovery: Application crashes instead of graceful degradation
- Security architecture: Fundamental auth/authorization design flaws
- Data loss risks: Operations that could permanently corrupt or lose user data

**Output Required**:
- PASS/REWORK verdict with confidence (1-10)
- Specific issues with file:line@commit-sha references (MANDATORY) plus 3-5 line snippet anchors
- Implementation-level concerns (not just architectural)
- Shell scripting and logic errors
- Risk assessment for solo developer deployment

**Solo MVP Context**: No team coordination concerns, focus on practical implementation correctness.
```

#### Early Termination Triggers:

- **✅ CONSENSUS_PASS**: All agents agree + high confidence + tests pass
- **❌ CRITICAL_BUG**: Any agent reports severity 9-10 issue
- **❌ TEST_FAILURE**: Core functionality broken by Phase 4 changes
- **❌ COMPILATION_ERROR**: Code doesn't compile/parse after changes

#### Output Integration:

**Enhanced Plan Completion Report**:
```
# /plan Execution Complete

## Phase 4: Implementation Summary
- [Implementation details from Phase 4]

## Phase 5: Consensus Validation Results
- Rounds completed: [1-3]
- Final status: [PASS/REWORK_LIMIT/ABORT]
- Test validation: [PASS/FAIL with details]
- Agent consensus: [confidence scores and key findings]

## Quality Assurance Actions Taken:
- Round 1: [agent recommendations + code changes + test results]
- Round 2: [agent recommendations + code changes + test results]
- Round 3: [agent recommendations + code changes + test results]

## Remaining Items:
- [Any unresolved agent concerns or test failures]
- [Follow-up recommendations for future iterations]
```

## 🔗 UNIVERSAL COMPOSITION PRINCIPLES

**Command Integration**: `/plan` naturally composes with:
- `/think` - Strategic analysis and problem solving
- `/guidelines` - Mistake prevention and protocol compliance
- `/context` - Continuous context monitoring
- `/cerebras` - High-speed code generation for appropriate tasks
- `/consensus` - Multi-agent validation and quality assurance (Phase 5)
- Memory MCP - Pattern recognition and preference application

**Adaptive Workflow**: The planning process adapts based on:
- Available context capacity
- Task complexity and scope
- User preferences from memory
- Guidelines and protocol requirements

## 📊 TOOL SELECTION CRITERIA

**Context-Efficient Tools** (Prioritized):
- ✅ **Serena MCP**: Semantic operations with minimal context consumption
- ✅ **Targeted Reads**: Specific file sections rather than full files
- ✅ **MultiEdit**: Batch edits to minimize tool overhead
- ✅ **Smart Search**: Grep/Glob before reading files

**High-Performance Generation** (When Appropriate):
- ✅ **/cerebras**: For tasks >10 delta lines with clear specifications
- ✅ **Claude Direct**: For ≤10 delta lines and integration work
- ✅ **Universal Composition**: Natural command integration

**Context Preservation**:
- ❌ Avoid unnecessary file reads
- ❌ Minimize redundant operations
- ❌ Skip verbose output when planning
- ✅ Reserve context for execution and validation

## Example Flow

**Context-Aware `/plan` Flow**:
```
User: /plan implement user authentication
Assistant:

Phase 0 - Context Assessment:
/context → 45% remaining → Medium Context Strategy

Phase 1 - Strategic Analysis:
[Memory consultation for auth patterns]
[Guidelines check for security requirements]
[Serena MCP discovery for efficient analysis]

Phase 2 - Execution Plan:
Context Status: 45% remaining → Medium complexity planning
- Analysis: Use Serena MCP for efficient codebase understanding
- Generation: /cerebras for new auth classes, Claude for integration
- Context preservation: Strategic tool selection

Seeking approval to proceed...

User: APPROVED
Assistant: [Executes context-optimized implementation]
```

## Key Characteristics

- ✅ **Context assessment mandatory first step**
- ✅ **Universal composition with other commands**
- ✅ **Context-adaptive planning depth**
- ✅ **Intelligent tool selection hierarchy**
- ✅ **User approval required before execution**
- ✅ **Memory and guidelines integration**
- ✅ **Efficient execution with context preservation**
- ✅ **Multi-agent consensus validation with automated testing**
- ✅ **Quality assurance loop with early termination**
- ✅ **Test-driven validation per consensus round**
