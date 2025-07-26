# Command Composition System Redesign Scratchpad

## Problem Statement

Current "Universal Command Composition" loses specific command implementations:
- `/arch` should trigger 12+ thoughts, Gemini consultation, structured report
- Actually just gets interpreted as "use architectural approach"
- Trade-off: Flexibility (works with any command) vs Fidelity (preserves specific behaviors)

## Simplified Protocol vs Natural Approach (NEW)

After review, a simpler two-category system is better:

### Protocol Commands
Commands with specific implementations that MUST be preserved:
- `/arch` - Full architecture review protocol (regular thinking by default, upgrades to ultrathink + Gemini with `/thinku`)
- `/execute` - Task execution with optional subagents
- `/test*` - Specific test protocols (UI, HTTP, etc.)
- `/deploy` - Deployment procedures
- `/learn` - Memory MCP integration

### Natural Commands
Commands that modify approach/style through natural language:
- `/think` - Thinking approach
- `/debug` - Debugging mindset
- `/brief` - Output modifier
- `/optimize` - Focus modifier
- Any unknown commands

### Key Principle: Everything Can Combine
- Protocol commands preserve their implementation AND integrate
- Natural commands layer on top as modifiers
- No complex conflict matrices - let commands work together

### Protocol Commands with Default Behaviors
Some protocol commands include default natural behaviors:
- `/arch` includes thinking by default (4-6 thoughts)
- Natural commands can modify these defaults
- Example: `/thinku` upgrades `/arch` from regular to ultra thinking
- This happens through context, not hardcoded combinations

### Natural Command Categories

#### Quality & Style Commands
Modify how code is written and structured:
- `/clean /execute` - Implementation with clean code principles
- `/readable /refactor` - Refactoring for maximum readability
- `/functional /implement` - Use functional programming patterns

#### Safety & Validation Commands
Add robustness and error handling:
- `/paranoid /deploy` - Deployment with extensive validation
- `/defensive /execute` - Implementation with defensive programming
- `/failsafe /execute` - Implementation with graceful degradation

#### Performance & Resource Commands
Guide optimization priorities:
- `/performance /optimize` - Focus on speed optimization
- `/scalable /arch` - Architecture review for scalability
- `/memory /debug` - Debug with memory usage focus

#### Scope & Depth Commands
Set implementation completeness:
- `/minimal /execute` - Bare minimum working implementation
- `/mvp /implement` - Just enough for viable product
- `/production /execute` - Production-ready implementation

#### Learning & Interaction Commands
Change explanation and interaction style:
- `/explain /debug` - Debug with detailed explanations
- `/teach /implement` - Tutorial-style implementation
- `/beginner /arch` - Architecture review for beginners

#### Context & Domain Commands
Apply domain-specific constraints:
- `/web /execute` - Implementation with web-specific concerns
- `/enterprise /arch` - Enterprise architecture patterns
- `/startup /execute` - Fast implementation, iterate later

### CI Enforcement
Every command MUST be registered as either `protocol` or `natural` in registry.
Test validates 100% registration coverage.

## Implementation Plan

### 1. Simplified Registry Structure
```json
{
  "protocol_commands": [
    "/arch",
    "/execute",
    "/test",
    "/testui",
    "/testhttp",
    "/deploy",
    "/learn",
    "/replicate",
    "/4layer",
    "/tdd",
    "/copilot",
    "/push",
    "/newbranch",
    "/plan"
  ],
  "natural_commands": [
    // Current commands
    "/think",
    "/thinku",
    "/debug",
    "/brief",
    "/verbose",
    "/careful",
    "/fast",
    "/optimize",
    "/secure",
    "/review",
    "/analyze",
    "/fix",

    // Quality & Style
    "/clean",        // Prioritize clean code principles
    "/readable",     // Optimize for human readability
    "/maintainable", // Focus on long-term maintenance
    "/testable",     // Ensure easily testable code
    "/documented",   // Include comprehensive documentation
    "/functional",   // Prefer functional programming
    "/oop",          // Object-oriented approach
    "/declarative",  // Declarative over imperative

    // Safety & Validation
    "/paranoid",     // Extra validation everywhere
    "/defensive",    // Defensive programming
    "/failsafe",     // Graceful degradation
    "/idempotent",   // Ensure idempotency
    "/atomic",       // Atomic operations

    // Performance & Resource
    "/performance",  // Optimize for speed
    "/memory",       // Optimize memory usage
    "/scalable",     // Design for scale
    "/efficient",    // General efficiency
    "/stream",       // Streaming approaches

    // Scope & Depth
    "/minimal",      // Bare minimum implementation
    "/complete",     // Fully featured
    "/mvp",          // Minimum viable product
    "/production",   // Production-ready code
    "/prototype",    // Quick prototype
    "/polish",       // Refined implementation

    // Learning & Interaction
    "/explore",      // Try multiple approaches
    "/research",     // Deep dive into options
    "/compare",      // Show alternatives
    "/explain",      // Explain reasoning
    "/teach",        // Tutorial-style
    "/beginner",     // Assume less knowledge
    "/expert",       // Assume deep knowledge

    // Collaboration Style
    "/pair",         // Pair programming style
    "/mentor",       // Mentoring approach
    "/suggest",      // Suggestive not prescriptive
    "/critique",     // Critical analysis
    "/refactor",     // Focus on refactoring

    // Context & Domain
    "/web",          // Web development focus
    "/mobile",       // Mobile constraints
    "/enterprise",   // Enterprise patterns
    "/startup",      // Move fast approach
    "/legacy",       // Work with legacy code

    // Meta & Behavior
    "/confident",    // Be decisive
    "/cautious",     // Highlight uncertainties
    "/iterative",    // Work in iterations
    "/creative",     // Unconventional solutions
    "/pragmatic"     // Practical over perfect
  ]
}
```

### 2. Execution Logic
```python
def execute_commands(commands, task):
    # Separate protocol and natural commands
    protocol_cmds = [c for c in commands if c in registry['protocol_commands']]
    natural_cmds = [c for c in commands if c in registry['natural_commands']]

    # Natural commands modify the execution context
    context = build_context(natural_cmds)

    # LLM decides execution plan for protocol commands
    execution_plan = llm_analyze_dependencies(protocol_cmds, task)

    # Present plan to user
    if not user_approves(execution_plan):
        return

    # Execute according to LLM's plan (may include parallel phases)
    execute_plan(execution_plan, context)

def build_context(natural_cmds):
    """Natural commands set context that modifies protocol execution"""
    context = {}

    # Thinking mode selection with explicit precedence
    # When multiple thinking commands present, use the most powerful
    if '/thinku' in natural_cmds:
        context['thinking_mode'] = 'ultra'  # 12+ thoughts (takes precedence)
    elif '/think' in natural_cmds:
        context['thinking_mode'] = 'regular'  # 4-6 thoughts

    # Output modifiers
    if '/brief' in natural_cmds:
        context['output'] = 'brief'
    elif '/verbose' in natural_cmds:
        context['output'] = 'verbose'

    # Debug mode
    if '/debug' in natural_cmds:
        context['debug'] = True
        context['logging'] = 'verbose'
        context['error_handling'] = 'detailed'
        context['validation'] = 'strict'

    # Other natural modifiers...
    return context
```

### LLM Execution Planning
The LLM analyzes protocol commands and decides:
- Which commands can run in parallel (no dependencies)
- Which must run sequentially (output feeds next command)
- Optimal execution order for efficiency

Example LLM analysis:
```
Input: /test /arch /deploy /copilot "review and deploy feature"

LLM Decision:
Phase 1 (Parallel): /test, /copilot
  - Both can run independently
  - Gather test results and code suggestions simultaneously

Phase 2: /arch
  - Needs test results and copilot suggestions as input
  - Comprehensive review with all data

Phase 3: /deploy
  - Only if tests pass and architecture approved
  - Sequential dependency on previous phases
```

### Benefits of LLM-Driven Planning
1. **Intelligent Dependencies**: LLM understands semantic relationships between commands
2. **Dynamic Optimization**: Execution plan adapts to the specific task
3. **Maximum Parallelism**: Automatically identifies independent operations
4. **Context Awareness**: Considers the task description when planning
5. **User Control**: Plan presented for approval before execution

### 3. CI Test Structure
```python
def test_all_commands_registered():
    """Every .md file must be in protocol or natural list"""
    for cmd_file in discover_command_files():
        cmd = extract_command_name(cmd_file)
        assert cmd in protocol_commands or cmd in natural_commands, \
               f"{cmd} not registered! Add to protocol_commands or natural_commands"

def test_no_command_in_both_lists():
    """Commands can only be in one category"""
    overlap = set(protocol_commands) & set(natural_commands)
    assert len(overlap) == 0, f"Commands in both lists: {overlap}"
```

### 4. Example Combinations

#### `/arch` (standalone)
```
Natural Context: None (arch includes thinking by default)
Execution Plan:
  Phase 1: /arch (architecture review with 4-6 thoughts)
```

#### `/thinku /arch` or `/arch /thinku`
```
Natural Context: Ultra thinking mode
Execution Plan:
  Phase 1: /arch (architecture review upgraded to 12+ thoughts)
Note: Order doesn't matter - natural commands modify context
```

#### `/think /arch /execute`
```
Natural Context: Thinking approach (redundant for arch, useful for execute)
Execution Plan:
  Phase 1: /arch (already uses thinking, no change)
  Phase 2: /execute (implementation with thinking approach)
```

#### `/brief /test /testui /deploy`
```
Natural Context: Brief output mode
Execution Plan:
  Phase 1 (Parallel): /test, /testui
    - Run backend and UI tests simultaneously
  Phase 2: /deploy (only if both test suites pass)
```

#### `/debug /copilot /gemini /arch /execute`
```
Natural Context: Debug mode
Execution Plan:
  Phase 1 (Parallel): /copilot, /gemini
    - Get suggestions from both AI assistants
  Phase 2: /arch
    - Architecture review incorporating both perspectives
  Phase 3: /execute
    - Implementation with all insights
```

#### `/secure /test /testhttp /testuif /deploy`
```
Natural Context: Security-focused
Execution Plan:
  Phase 1 (Parallel): /test, /testhttp, /testuif
    - All test types can run independently
  Phase 2: /deploy
    - Only if all tests pass with security checks
```

#### `/debug /test "flaky test failures"`
```
Natural Context: Debug mode
- Verbose logging enabled
- Detailed error handling
- Strict validation
Execution Plan:
  Phase 1: /test
    - Run with maximum verbosity
    - Capture full stack traces
    - Log intermediate states
    - Multiple retry attempts to catch flakiness
```

#### `/debug /think /execute "fix memory leak"`
```
Natural Context: Debug mode + thinking approach
Execution Plan:
  Phase 1: Deep analysis with debug focus
    - Trace memory allocation patterns
    - Form hypotheses about leak sources
  Phase 2: /execute
    - Implementation with extensive logging
    - Memory profiling instrumentation
    - Validation checkpoints
```

#### `/minimal /fast /prototype "proof of concept"`
```
Natural Context:
- Minimal scope (bare essentials only)
- Fast execution (skip non-critical paths)
- Prototype quality (not production-ready)
Execution Plan:
  Phase 1: Rapid implementation
    - Core functionality only
    - Skip error handling
    - Basic happy path
```

#### `/paranoid /defensive /production /test`
```
Natural Context:
- Maximum validation
- Defensive programming
- Production quality standards
Execution Plan:
  Phase 1: /test
    - Comprehensive test coverage
    - Edge case validation
    - Error injection tests
    - Performance benchmarks
```

#### `/teach /beginner /explain /implement "sorting algorithm"`
```
Natural Context:
- Tutorial-style presentation
- Assume basic knowledge only
- Detailed explanations throughout
Execution Plan:
  Phase 1: Educational implementation
    - Step-by-step code
    - Comments explaining each line
    - Multiple examples
    - Common pitfalls highlighted
```

## Refined High-Impact Commands (Based on Research)

After architecture review, these 12 natural commands have proven behavioral impact:

1. **`/paranoid`** - Adds defensive programming (validation, error handling)
2. **`/defensive`** - Similar to paranoid but less extreme
3. **`/minimal`** - Bare minimum implementation (YAGNI principle)
4. **`/complete`** - Fully-featured implementation
5. **`/performance`** - Optimize for speed (algorithm choices)
6. **`/memory`** - Optimize for memory usage
7. **`/teach`** - Tutorial-style with extensive comments
8. **`/documented`** - Comprehensive documentation
9. **`/thorough`** - Enhanced testing focus (replaces /test conflict)
10. **`/clean`** - Clean code principles (via linter rules)
11. **`/readable`** - Optimize for readability (via metrics)
12. **`/beginner`** - Simplified explanations

These commands have:
- Concrete implementations
- Measurable outcomes
- Proven effectiveness from research

## Command Suggestion System (LLM-Based)

### Design Philosophy
Use LLM's natural language understanding for intelligent command suggestions.
NO keyword matching or rule-based systems.

### Implementation
```python
def suggest_commands(task_description, current_commands):
    """LLM analyzes context and suggests relevant natural commands"""
    prompt = f"""
    Task: {task_description}
    Current commands: {current_commands}

    Analyze the task and suggest 1-3 natural commands that would help.
    Consider: debugging needs, performance concerns, safety requirements,
    scope decisions, and user experience goals.

    For each suggestion explain WHY it helps this specific task.
    """
    return llm_analyze(prompt)
```

### Example Suggestions
```
Task: "Fix the authentication system that's dropping users"

💡 Suggested commands:
• /paranoid - Auth is security-critical, add validation
• /debug - Need detailed logging to find where users drop
• /documented - Complex auth flows need clear documentation
```

## Architecture Review Findings

### System Strengths
- **Elegant Simplicity**: Two categories easy to understand
- **Natural Composition**: Commands read intuitively (e.g., `/paranoid /execute`)
- **Research-Backed**: 12 commands chosen for measurable impact
- **Unix Philosophy**: Simple tools that compose well

### Valid Concerns & Mitigations
1. **Semantic Conflicts** (e.g., `/minimal /paranoid`)
   - Mitigation: Show conflict warnings, let user decide
   - Reality: Rare in practice, users have common sense

2. **Execution Transparency**
   - Mitigation: Already show execution plans for approval
   - Not a black box - users see and control

3. **Cognitive Load**
   - Mitigation: LLM suggestions solve discovery
   - Users learn 3-5 commands, discover rest as needed

### Key Insight
This is an interactive CLI tool, not production automation. Users can clarify ambiguity in real-time. Over-formalization reduces the natural language flexibility that makes this powerful.

## Quick Win Improvements

### 1. Conflict Warnings
```
⚠️ Potential conflict detected:
   /minimal - Bare minimum implementation
   /paranoid - Extensive validation

Proceed with both? The result may be contradictory.
[Yes/No/Modify]
```

### 2. Command Recipes (Aliases)
```json
{
  "recipes": {
    "/safe-deploy": ["/paranoid", "/thorough", "/documented", "/deploy"],
    "/quick-fix": ["/minimal", "/fast", "/execute"],
    "/refactor-carefully": ["/clean", "/thorough", "/refactor"]
  }
}
```

### 3. Usage Analytics
Track which combinations succeed/fail to improve suggestions over time.

## Practical Usage Patterns

### Expected User Behavior
- **New Users**: Use 2-3 basic commands with LLM suggestions
- **Regular Users**: Develop favorite 3-5 command patterns
- **Power Users**: Discover creative combinations
- **Edge Cases**: Rare nonsensical combinations handled gracefully

### Real-World Examples
```bash
# Common patterns
/debug /execute            # Fix with logging
/paranoid /deploy          # Safe production deploy
/minimal /prototype        # Quick proof of concept

# Advanced but sensible
/teach /beginner /implement # Educational code
/performance /memory /optimize # Dual optimization

# Rare/nonsensical (system handles gracefully)
/minimal /complete         # Warns about conflict
/paranoid /fast           # Suggests alternatives
```

## What NOT to Implement (Avoiding Overengineering)

Based on architecture review, these suggestions would add complexity without proportional value:

### ❌ Complex Conflict Matrices
- Would require maintaining N×N compatibility matrix
- Reduces flexibility of natural language understanding
- Users can resolve conflicts interactively

### ❌ Command Namespacing (`/style:minimal`)
- Adds cognitive load
- Makes commands less natural to type
- Current flat structure is more Unix-like

### ❌ Formal Dependency Graphs
- Overkill for interactive CLI
- LLM already understands implicit dependencies
- Explicit graphs reduce adaptability

### ❌ Extensive Recipe System
- Start with 2-3 recipes maximum
- Let patterns emerge from usage
- Avoid premature abstraction

## Design Principles

1. **Respect All Commands**: Every command's specific implementation must be preserved
2. **Enable Integration**: Commands should work together, not just sequentially
3. **Handle Conflicts Gracefully**: Detect and resolve conflicts with user input
4. **Support Parallelism**: Run independent commands simultaneously when possible
5. **Maintain Transparency**: User sees and approves execution plans
6. **Leverage LLM Intelligence**: Use natural language understanding, not keywords
7. **Appropriate Engineering**: Match complexity to use case (interactive CLI)

## Approach 1: Command Registry with Metadata

### Design
Each command registers:
```json
{
  "name": "/arch",
  "type": "analysis",
  "conflicts": [],
  "dependencies": [],
  "can_combine": ["/think", "/debug"],
  "parallel_safe": false,
  "implementation": "full_architecture_review_protocol"
}
```

### Pros
- Full control over combinations
- Explicit conflict detection
- Preserves exact implementations
- Can optimize execution order

### Cons
- Loses "universal" nature for unknown commands
- Requires maintaining registry
- More complex to implement
- New commands need registration

## Approach 2: Protocol-Preserving Composition

### Design
Commands execute their full protocols but share context:
```
SharedContext {
  thoughts: [],
  findings: [],
  recommendations: []
}

/think -> adds to context.thoughts
/arch -> reads context.thoughts, adds context.findings
/execute -> uses context.findings for implementation
```

### Pros
- Preserves full command implementations
- Natural integration through shared state
- Commands enhance each other
- No registry needed

### Cons
- Sequential execution only
- Complex state management
- Potential context pollution
- Order matters significantly

## Approach 3: Execution Graph Builder (Recommended)

### Design
1. Parse all commands
2. Build execution graph based on types/dependencies
3. Detect conflicts
4. Present plan to user
5. Execute with user approval

### Example Flow
```
Input: /think /arch /execute /brief
Output:
  ⚠️ Execution Plan:
  Phase 1: /think (sequential thinking analysis)
  Phase 2: /arch (architecture review - uses think output)
  Phase 3: /execute (implementation - uses arch findings)
  Modifier: /brief (applied to all output)

  Proceed? [Y/n]
```

### Pros
- Full transparency
- User control
- Preserves all implementations
- Supports parallelism where safe
- Handles conflicts explicitly

### Cons
- Requires user interaction
- More complex than current system
- Need to categorize all commands

## Approach 4: Hybrid Protocol/Approach System

### Design
Commands declare themselves as:
- **Protocol-based**: Specific implementation required
- **Approach-based**: Flexible interpretation OK

### Implementation
```bash
# Protocol commands (must run exact implementation)
PROTOCOL_COMMANDS="/arch /execute /test /deploy"

# Approach commands (flexible interpretation)
APPROACH_COMMANDS="/think /debug /optimize /secure"

# Process based on type
if is_protocol_command; then
  execute_full_protocol
else
  use_natural_language_interpretation
fi
```

### Pros
- Best of both worlds
- Known commands work perfectly
- Unknown commands still function
- Gradual migration path

### Cons
- Two different execution paths
- Complexity in mixing types
- May confuse users

## Conflict Resolution Strategies

### 1. Early Exit (User's Requirement #1)
```
Detected conflicts:
- /brief conflicts with /verbose
- /fast conflicts with /careful

How to resolve?
1) Use /brief and /fast
2) Use /verbose and /careful
3) Cancel operation
Choice:
```

### 2. Intelligent Merging
- `/brief /verbose` → Brief by default, verbose on errors
- `/fast /careful` → Fast analysis, careful implementation
- `/test /notest` → Test critical paths only

### 3. Last-One-Wins
- Simple but may surprise users
- Good for modifiers (brief/verbose)
- Bad for actions (deploy/rollback)

### 4. Priority-Based
- Safety commands override optimization
- Explicit overrides implicit
- User commands override defaults

## Integration Patterns

### 1. Pipeline Pattern
```
/analyze → /plan → /execute → /test → /deploy
Each command's output feeds the next
```

### 2. Parallel Analysis
```
         ┌→ /security ─┐
/code ───┼→ /performance ├→ /report
         └→ /quality ──┘
Multiple perspectives combined
```

### 3. Layered Enhancement
```
/basic → /detailed → /comprehensive
Each layer adds depth
```

### 4. Conditional Execution
```
/test → if (failures) → /debug → /fix
       → else → /deploy
```

### 5. Aggregated Results
```
/think + /research + /analyze → Unified findings
```

## Recommended Implementation

### Three-Step Process (Per User Requirements)

#### Step 1: Conflict Detection
```python
def detect_conflicts(commands):
    conflicts = []
    for cmd1, cmd2 in combinations(commands, 2):
        if conflicts_with(cmd1, cmd2):
            conflicts.append((cmd1, cmd2))

    if conflicts:
        return ask_user_resolution(conflicts)
    return commands
```

#### Step 2: Combination Attempt
```python
def try_combine(commands):
    # Check if all commands can be truly combined
    if all_are_approach_based(commands):
        return create_unified_prompt(commands)
    elif all_are_compatible_protocols(commands):
        return create_integrated_execution(commands)
    else:
        return None  # Can't fully combine
```

#### Step 3: Execution Plan
```python
def create_execution_plan(commands):
    plan = ExecutionPlan()

    # Group by parallelizability
    parallel_groups = group_parallel_safe(commands)

    # Build phases
    for group in parallel_groups:
        if len(group) > 1:
            plan.add_parallel_phase(group)
        else:
            plan.add_sequential_phase(group[0])

    # Present to user
    return plan.present_for_approval()
```

### Example Execution Plans

#### Example 1: Compatible Commands
```
Input: /think /debug /fix "memory leak issue"

✅ Commands can be integrated:
- Sequential thinking to analyze the issue
- Debug mode for systematic investigation
- Generate and apply fixes

Proceed with integrated execution? [Y/n]
```

#### Example 2: Partial Compatibility
```
Input: /arch /test /deploy /brief /verbose

⚠️ Conflict detected: /brief ↔ /verbose
Resolve:
1) Keep /brief (concise output)
2) Keep /verbose (detailed output)
3) Smart mode (brief summary, verbose errors)
Choice: 3

📋 Execution Plan:
Phase 1: /arch (full architecture review)
Phase 2: /test (run test suite)
Phase 3: /deploy (if tests pass)
Modifier: Smart output mode

Proceed? [Y/n]
```

#### Example 3: Complex Integration
```
Input: /think /copilot /gemini /arch /execute

📋 Execution Plan:
Phase 1 (Sequential):
  → /think (initial analysis)

Phase 2 (Parallel):
  → /copilot (code suggestions)
  → /gemini (alternative perspective)

Phase 3 (Sequential):
  → /arch (architecture review incorporating all inputs)
  → /execute (implementation)

Estimated time: 5-7 minutes
Proceed? [Y/n]
```

## Implementation Priority

1. **High Priority**: Conflict detection and resolution
2. **High Priority**: Execution plan presentation
3. **Medium Priority**: Protocol preservation for known commands
4. **Medium Priority**: Parallel execution support
5. **Low Priority**: Unknown command handling
6. **Low Priority**: Advanced integration patterns

## Next Steps

1. Implement basic conflict detection
2. Create execution plan builder
3. Preserve key command protocols (/arch, /execute, /test)
4. Add user approval flow
5. Test with common combinations
6. Gradually add more sophisticated integration

## Key Decision Points

1. **Should unknown commands fail or use natural language?**
   - Recommendation: Warn but proceed with natural interpretation

2. **How much user interaction is acceptable?**
   - Recommendation: Only for conflicts and final approval

3. **Should execution be truly parallel or simulated?**
   - Recommendation: True parallel for independent commands

4. **How to handle partial failures?**
   - Recommendation: Stop and ask user (safe default)
