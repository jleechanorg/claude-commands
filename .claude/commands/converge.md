# /converge - Iterative Goal Achievement Command

Achieve complex goals through autonomous plan-execute-validate-learn cycles until success criteria are met.

## Usage
- `/converge <goal>` - Start converging toward a specific goal
- `/converge --max-iterations N` - Set custom iteration limit (default: 10)
- `/converge --goal-integration` - Use /goal command for structured goal definition
- `/converge` - Resume previous convergence if interrupted

## Core Pattern
```
Loop: Autonomous plan→execute→validate→learn cycles
Until: Success criteria fully met
```

## 🔄 CONTINUOUS CONVERGENCE PROTOCOL

**FULLY AUTONOMOUS SYSTEM**: /converge implements a completely autonomous, self-improving system through recursive goal achievement with persistent learning and systematic iteration. **ZERO USER INTERVENTION** required after initial goal statement.

### 🎯 GOAL & SUCCESS CRITERIA DEFINITION
**MANDATORY**: All /converge operations must use structured goal integration

**Command**: `/goal` - Define goal with structured success criteria and validation framework
- Automatic success criteria generation based on goal patterns
- Integrated validation system with evidence collection
- Guidelines consultation for goal quality and compliance
- Historical tracking and learning integration with Memory MCP
- Cross-goal pattern analysis and optimization

### 🗺️ CONVERGENCE LOOP (9-STEP CYCLE)
**LOOP UNTIL CONVERGED OR MAX ITERATIONS REACHED (Default: 10 iterations)**:

#### Step 1: Intelligent Autonomous Goal Definition and Context Setup
**Command**: Goal Processing - Intelligently define goals with smart defaults and autonomous analysis
- **ENHANCED CONTEXT OPTIMIZATION**: Use direct goal processing for minimal context consumption
- **Method**: Direct inline goal analysis with structured output
- **Output**: Structured goal-spec.json in /tmp/converge/{branch}/session-{timestamp}/
- **Context Savings**: Optimized direct processing approach
- **Integration**: Load goal specification for subsequent phases without accumulating context
- **Benefits**: Direct processing, structured analysis, persistent storage
- Generate structured success criteria based on goal analysis and pattern recognition
- Establish validation methods and completion thresholds using established frameworks
- Create goal tracking structure with evidence requirements following proven patterns

#### Step 2: Strategic Planning and Tool Analysis
**Command**: `/plan` - Create comprehensive strategy with command index optimization
- **CONTEXT OPTIMIZATION**: Use command index instead of reading full .claude/commands/ files
- **Command Index**: Load /tmp/converge/{branch}/command-cache/index.json (71K chars vs 677K chars)
- **Context Savings**: 89.5% reduction in command discovery phase
- **Smart Selection**: Filter commands by context level, execution time, and goal type
- **Lazy Loading**: Defer reading full command .md files until execution phase
- **Efficiency**: Use command summaries for planning, full docs for execution only
- Remember slash commands are EXECUTABLE instructions, not documentation
- Break goal into actionable phases using appropriate slash command orchestration
- Estimate resource requirements and timeline with tool-specific considerations
- Identify potential obstacles and mitigation strategies
- Create detailed TodoWrite tracking system with command-specific tasks

#### Step 3: Plan Review & Confidence Assessment
**Action**: Review the plan using strategic analysis with confidence scoring
- Critically analyze plan against available slash command library
- **Confidence Assessment**: Evaluate goal clarity, pattern recognition, and complexity
  - **High (≥75%)**: Clear goal + recognizable patterns → Standard execution
  - **Medium (50-74%)**: Some ambiguity → Enhanced logging, continue
  - **Low (<50%)**: Major uncertainty → Extra validation, continue
- Display confidence level with reasoning for transparency
- Optimize tool selection for maximum efficiency
- Identify command synergies and integration opportunities
- Validate approach against best practices and constraints

#### Step 4: Plan Approval
**AUTONOMOUS APPROVAL**: All plans are automatically approved and proceed without human intervention
- System confidence assessment determines execution approach
- High-confidence plans: Proceed with optimal execution strategy
- Lower-confidence plans: Use more conservative execution with additional validation
- All plans proceed autonomously - no human approval gates

#### Step 5: Execution Phase
**Command**: `/cerebras` to execute (or appropriate command based on goal type)
- Execute plan using optimal slash command selection
- Monitor progress and adapt execution as needed
- Handle errors and obstacles with intelligent retry
- Maintain detailed execution logs for learning

#### Step 6: Validation Against Goals
**Command**: `/goal --validate` against the goals - Objective success measurement
- Check each success criterion systematically using structured validation
- Measure progress quantitatively with evidence collection
- Identify gaps between actual and expected outcomes
- Document validation results with concrete evidence for learning phase
- Generate completion percentage and remaining work analysis

#### Step 7: Learning & Documentation Update
**Command**: `/guidelines` to update the documentation if mistakes/learnings were made
- Capture mistakes, inefficiencies, and unexpected successes
- Update project guidelines and best practices
- Evolve meta-rules for future convergence cycles
- Create persistent memory for recursive improvement

#### Step 8: Enhanced Status Report Generation
**Command**: `/status` - Generate comprehensive convergence status report with confidence data
- **Report Location**: Save to `docs/pr-guidelines/{PR_NUMBER}/convergence-status-{timestamp}.md`
- **Progress Summary**: Current completion percentage and criteria status
- **Confidence Data**: Current confidence level, reasoning, and historical accuracy
- **Resource Summary**: Token usage, iterations completed, elapsed time
- **Iteration Analysis**: Commands used, success rates, and performance metrics
- **Learning Documentation**: Patterns discovered, failures overcome, optimizations applied
- **Convergence Trajectory**: Progress velocity, estimated completion, next iteration strategy
- **Decision Context**: Evidence for convergence/continuation decision with objective rationale

#### Step 9: Convergence Decision
**LOOP CONTROL**: Start again with Step 1 (Goal Definition) and loop N times or stop when it's done

🚨 **MANDATORY AUTONOMY CHECKPOINT**: Before making convergence decision, verify autonomy preservation:
- ❌ **FORBIDDEN**: Stopping for user approval when goal not 100% achieved
- ❌ **FORBIDDEN**: Waiting for user acknowledgment of partial progress
- ❌ **FORBIDDEN**: Implicit approval requests through progress celebration
- ✅ **REQUIRED**: Continue immediately if success criteria < 100% and iterations < max

**Convergence Decision Logic**:
- **IF CONVERGED**: All PRIMARY success criteria met → STOP with completion report
  - PR is MERGEABLE status (not conflicting)
  - All SERIOUS GitHub comments addressed (blocking issues resolved)
  - CI passes (no failed checks)
  - No critical errors or failures detected
- **IF GOOD ENOUGH**: Core objectives achieved even if minor issues remain → STOP
  - Primary goal accomplished (90%+ criteria met)
  - Diminishing returns threshold reached (last 2 iterations <5% improvement)
  - PR is in good mergeable state with only cosmetic issues remaining
- **IF STALLED**: No meaningful progress in validation for 2+ iterations → STOP with stall report
  - Same validation scores for 2+ consecutive iterations
  - Unable to improve PR mergeability status
  - Repeated execution failures on same issue
- **IF IMPROVING**: Meaningful progress on PRIMARY criteria → Continue (max 2 more iterations)
  - Measurable improvement in PR status or CI state
  - Successful resolution of blocking GitHub comments
  - BUT: Hard cap at 10 iterations regardless of progress
- **IF MAX ITERATIONS**: Absolute limit reached → STOP with partial report

🔒 **AUTONOMY PRESERVATION**: No user intervention allowed during convergence decision process

**PR CONTEXT AWARENESS**: When goal involves PR work:
- Primary success = PR is MERGEABLE on current branch
- ❌ NEVER create additional PRs as "solutions"
- ✅ ALWAYS work within existing PR constraints
- ✅ STAY ON CURRENT BRANCH throughout convergence

## 🔒 AUTONOMY BOUNDARIES & OPERATION

### Complete Autonomy Scope
/converge operates with **ZERO USER INTERVENTION** after initial goal statement:
- **Goal Analysis**: Intelligent interpretation of goal requirements without questions
- **Planning Decisions**: Autonomous strategy selection using established patterns
- **Tool Selection**: Automatic command selection based on task analysis
- **Execution Management**: Self-directed execution with error recovery
- **Validation Assessment**: Objective success measurement without user confirmation
- **Learning Integration**: Automatic pattern capture and guideline updates
- **Iteration Control**: Autonomous continuation or termination decisions

### Smart Default System
**Intelligent Assumptions**: System applies reasonable defaults when information is unclear:
- Use established project patterns and conventions
- Apply best practices from accumulated learning
- Select proven tool combinations for similar tasks
- Implement conservative approaches for ambiguous requirements
- Generate comprehensive success criteria from goal context

### No User Interaction Points
**Eliminated User Dependencies**:
- ❌ No clarifying questions during goal definition
- ❌ No approval gates for plan execution
- ❌ No manual intervention requests during errors
- ❌ No user confirmation for validation results
- ❌ No human decision points in iteration loops

### 🚀 AUTONOMOUS INTELLIGENCE ARCHITECTURE

**Self-Improving Intelligence Markers**:
- **Goal-Driven Loops**: Each cycle begins with intelligent goal analysis (Step 1)
- **Strategic Planning**: Meta-cognitive planning capabilities with tool awareness (Step 2)
- **Autonomous Decision-Making**: Smart defaults and pattern-based choices (Step 4)
- **Self-Validation**: Objective measurement against success criteria (Step 6)
- **Persistent Learning**: Memory MCP integration with evolving knowledge graph (Step 7)
- **Status Documentation**: Comprehensive progress reporting and analysis (Step 8)
- **Recursive Improvement**: Each cycle builds on accumulated learnings (Step 9)
- **Complete Autonomy**: Zero human intervention after initial goal statement

**System Architecture Patterns**:
- **OODA Loop**: Observe → Orient (Plan/Review) → Decide (Approve) → Act (Execute/Validate) → Learn (Guidelines)
- **Autopoietic Systems**: Self-maintaining and self-improving through recursive loops
- **Multi-Agent Orchestration**: Delegates to specialized slash commands (/cerebras, /copilot, /orch)
- **Emergent Intelligence**: System intelligence emerges from iterative feedback loops
- **Memory Persistence**: Memory MCP provides persistent learning and pattern evolution

### 🎯 CONVERGENCE STATES & TERMINATION

**Convergence Indicators**:
- ✅ **CONVERGED**: All success criteria objectively validated
- 🔄 **CONVERGING**: Making measurable progress toward goals
- ⚠️ **STALLED**: No progress despite multiple iterations
- 🛑 **BLOCKED**: External dependencies preventing progress
- 📚 **LEARNING**: Accumulating insights for next iteration

**Termination Conditions**:
- **Success Termination**: 100% of success criteria met
- **Learning Termination**: Guidelines updated with valuable insights
- **Resource Termination**: Maximum iterations/time reached
- **Blocking Termination**: Unresolvable external dependencies

**Completion Report Generation**:
- Total iterations completed
- Success criteria achievement percentage
- Key learnings and guideline updates
- Performance metrics (time, commands used, efficiency)
- Recommendations for future similar goals

## Key Features
- **Autonomous Operation**: Minimal user intervention required
- **Adaptive Planning**: Adjusts strategy based on results
- **Error Recovery**: Handles failures and retries intelligently
- **Progress Tracking**: Uses TodoWrite for visibility
- **Parallel Execution**: Leverages orchestration when beneficial
- **Success Validation**: Verifies all criteria before completion

## Examples

### Example 1: PR Cleanup and Refactoring
```
/converge Implement PR #1307 roadmap - close 5 PRs, create 7 focused PRs, fix 6 existing PRs
```
Result: Autonomously closes obsolete PRs, creates new focused PRs, and fixes existing ones

### Example 2: Test Suite Convergence
```
/converge Make all tests pass in the repository
```
Result: Iteratively fixes failing tests until 100% pass rate

### Example 3: Feature Implementation
```
/converge Implement complete authentication system with tests and documentation
```
Result: Builds feature incrementally with validation at each step

## Command Integration Framework

### Universal Composition Execution
**Command Selection Protocol**: Choose appropriate slash command for each task type:
- **Code/Script Generation**: **Command**: `/cerebras` - Fast high-quality code generation
- **PR Review Processing**: **Command**: `/copilot` - Complete PR comment processing
- **Test Suite Management**: **Command**: `/test` - Run and fix failing tests
- **Complex Multi-Step**: **Command**: `/orch` - Delegate to orchestration agents
- **Planning & Analysis**: **Command**: `/execute` - Break down complex goals

## Success Criteria Patterns

### For PR Management
- All target PRs in correct state (OPEN/CLOSED/MERGED)
- CI/CD checks passing
- Review requirements met
- No merge conflicts

### For Code Implementation
- All tests passing
- Code review approved
- Documentation complete
- Deployed successfully

### For Refactoring
- Functionality preserved
- Tests still passing
- Performance maintained/improved
- Code quality metrics met

## Error Handling & Recovery
- **Blocked Dependencies**: Implement intelligent retry with exponential backoff
- **Failing Tests**: Debug systematically, fix issues, and retry with learning
- **Conflicts**: Resolve automatically using established patterns or escalate with context
- **Rate Limits**: Implement backoff and retry strategies without user intervention
- **Resource Exhaustion**: Graceful degradation with progress preservation
- **Incomplete Goals**: Document progress, generate continuation strategy, maintain autonomous operation

## 🚀 Context Optimization Architecture

### Lazy Loading Patterns
**Context-Efficient File Loading**: Load files only when needed for execution, not during planning

```markdown
**Planning Phase** (Steps 1-3):
- Goal Processing: Use independent agent (5K tokens max)
- Command Discovery: Use command index (71K chars vs 677K chars)
- Plan Review: Work with summaries only
- Context Usage: ~80K tokens (vs 200K+ traditional)

**Execution Phase** (Steps 5+):
- Command Details: Load full .md files only when executing specific commands
- File Operations: Read files on-demand during actual operations
- Resource Usage: Targeted loading based on execution needs
- Context Management: Release completed context between iterations
```

### Command Index System Integration
**89.5% Context Reduction in Command Discovery**:
- **Index Location**: `/tmp/converge/{branch}/command-cache/index.json`
- **Content**: 106 command summaries with purpose, context requirements, execution time
- **Usage**: Planning phase uses index, execution phase loads full command docs
- **Benefits**: Instant command discovery, smart filtering, parallel planning capability

### Agent-Based Architecture
**Independent Processing Agents**:
- **Goal Processing**: Direct inline goal analysis with structured output
- **Planning Agent**: Future enhancement for command selection and sequencing
- **Execution Agents**: Parallel task execution with minimal shared context
- **Validation Agent**: Success criteria checking with targeted file access

### Session State Management
**Filesystem-Based Coordination**:
```
/tmp/converge/{branch_name}/
├── session-{timestamp}/
│   ├── goal-spec.json          # Goal processor output
│   ├── execution-plan.json     # Planning phase results
│   ├── current-state.json      # Progress tracking
│   └── results/               # Execution outputs
└── command-cache/             # Command index system
    └── index.json
```

## Best Practices
1. **Start with clear success criteria** - Ambiguous goals lead to endless loops
2. **Use TodoWrite for tracking** - Maintains visibility of progress
3. **Leverage parallel execution** - Use orchestration for independent tasks
4. **Validate frequently** - Don't wait until the end to check progress
5. **Document decisions** - Keep audit trail of what was tried
6. **Know when to stop** - Set maximum iterations to prevent infinite loops
7. **🚀 NEW: Optimize context usage** - Use lazy loading and agent architecture for efficiency
8. **🚀 NEW: Leverage command index** - Use summaries for planning, full docs for execution

## 🔗 Universal Composition Integration

**CRITICAL**: /converge achieves goals by systematically calling other slash commands:

### Primary Command Arsenal
- **`/execute`**: Planning, analysis, validation, and coordination
- **`/cerebras`**: High-speed code/script/document generation
- **`/copilot`**: Complete PR review and comment processing
- **`/test`**: Test execution and failure resolution
- **`/orch`**: Complex multi-agent task orchestration
- **`/pushl`**: Git operations and PR creation

### Command Selection Logic
```
Goal Type → Command Selection:
- Code generation → /cerebras
- PR processing → /copilot
- Test management → /test
- Multi-step automation → /orch
- Planning/validation → /execute
```

### Invocation Pattern
```markdown
**Command**: /commandname - Clear purpose and expected outcome
- Specific parameters and context
- Expected result verification
- Integration with next phase
```

## 🔄 CONVERGENCE IN ACTION: Real Example

### Goal: Create Python Testing Suite
**Command**: `/converge Create a complete Python testing suite with test_math.py, test_utils.py, and run all tests successfully`

#### Iteration 1:
**Command**: `/execute` - Analyze goal and create plan
- Parse goal: Need 2 test files + successful test execution
- Success criteria: Files exist, contain valid tests, all tests pass
- Plan: Generate test files → Run tests → Fix any failures

**Command**: `/cerebras` - Generate test_math.py with basic math function tests
- Prompt: "Create test_math.py with pytest tests for add, subtract, multiply functions"
- Result: File created with 6 test functions
- Validation: File exists ✅

**Command**: `/cerebras` - Generate test_utils.py with utility function tests
- Prompt: "Create test_utils.py with pytest tests for string and list utilities"
- Result: File created with 4 test functions
- Validation: File exists ✅

**Command**: `/test` - Run pytest and check results
- Result: 8/10 tests pass, 2 failures in test_math.py
- Analysis: Missing math.py implementation file
- Status: Converging 🔄 (files exist but tests fail)

#### Iteration 2:
**Command**: `/cerebras` - Generate missing math.py implementation
- Prompt: "Create math.py with add, subtract, multiply functions to make tests pass"
- Result: Implementation file created
- Validation: File exists ✅

**Command**: `/test` - Re-run pytest
- Result: 10/10 tests pass ✅
- Validation: All success criteria met
- Status: **CONVERGED** ✅

#### Convergence Report:
- **Total iterations**: 2/10 (within default limit)
- **Commands used**: /execute (2x), /cerebras (3x), /test (2x)
- **Time**: 3 minutes
- **Success criteria**: All met ✅
- **Files created**: test_math.py, test_utils.py, math.py
- **Test results**: 10/10 passing

## Convergence Indicators
- ✅ **Converged**: All success criteria met
- 🔄 **Converging**: Making measurable progress
- ⚠️ **Stalled**: No progress in last iteration
- ❌ **Diverging**: Moving away from goal
- 🛑 **Blocked**: Cannot proceed without intervention

## Configuration & Iteration Limits

### Default Configuration
- **Max Iterations**: 10 (prevents infinite loops)
- **Convergence Threshold**: 100% success criteria met
- **Timeout**: 2 hours maximum execution time
- **Learning Mode**: Enabled (captures patterns for /guidelines)

### Iteration Limit Implementation
```bash
# Command-line configuration
/converge "goal statement" --max-iterations 15

# Per-goal configuration via /goal integration
/goal "complex implementation task" --max-iterations 20
/converge --goal-integration

# Emergency termination conditions
- Manual interruption (Ctrl+C)
- Resource exhaustion (context/API limits)
- Blocking external dependencies
- Maximum time exceeded
```

### Convergence States & Termination
- **SUCCESS**: All criteria met before max iterations
- **PARTIAL**: Some progress made, iteration limit reached
- **BLOCKED**: External dependencies prevent progress
- **TIMEOUT**: Maximum execution time exceeded
- **INTERRUPTED**: Manual termination requested

## Performance & Efficiency

### Context Optimization Results
- **Goal Processing**: 90% context reduction (5K vs 50K+ tokens)
- **Command Discovery**: 89.5% context reduction (71K vs 677K characters)
- **Planning Phase**: 75% overall context reduction through lazy loading
- **Execution Phase**: Targeted file loading reduces unnecessary context accumulation
- **Total System**: 60-80% context reduction enabling longer convergence sessions

### Execution Benefits
- **Parallel Processing**: Independent agents can execute simultaneously
- **Failure Isolation**: Agent failures don't crash entire convergence workflow
- **Resume Capability**: Session state enables restart from any step
- **Debug Clarity**: Each agent's input/output clearly defined and traceable
- **Scalability**: Add more agents without increasing main context

## Limitations
- Cannot bypass GitHub permissions
- Cannot override CI/CD requirements
- **Complete Autonomy**: No user input required at any stage after goal statement
- Rate limits may slow progress
- Some goals may be technically infeasible
- **Default 10-iteration limit** prevents infinite loops but may require adjustment for complex goals
- **Context optimization** requires proper session directory setup and command index generation

## Memory and Context
- Saves progress state for resumption
- Documents learnings for future runs
- Maintains context across iterations
- Can resume after interruption

## Example Convergence Report
```markdown
# Convergence Complete: PR #1307 Implementation

## Goal
Implement PR #1307 roadmap with 18 PR operations

## Iterations: 3
1. Closed obsolete PRs (5/5 ✅)
2. Created focused PRs (7/7 ✅)
3. Fixed existing PRs (6/6 ✅)

## Success Criteria Met
- ✅ All obsolete PRs closed
- ✅ 7 new focused PRs created
- ✅ All KEEP PRs passing CI
- ✅ No merge conflicts

## Time: 45 minutes
## Status: CONVERGED ✅
```

---

## 🎯 CORRECTED ARCHITECTURE SUMMARY

**Universal Composition**: /converge systematically calls other slash commands using explicit "**Command**: /commandname" pattern

**Iterative Convergence**: Continues plan→execute→validate→learn cycles until ALL success criteria met

**Measurable Success**: Verifies completion objectively, not through assumption

**Command Integration**: Uses appropriate specialist commands (/cerebras, /copilot, /test, /orch) based on goal type

**Remember**: /converge achieves goals by orchestrating other slash commands intelligently, not by trying to do everything itself. It's a meta-command that coordinates specialized tools until convergence is achieved.
