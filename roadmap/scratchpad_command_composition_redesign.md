# Command Composition System Redesign Scratchpad

## Problem Statement

Current "Universal Command Composition" loses specific command implementations:
- `/arch` should trigger 12+ thoughts, Gemini consultation, structured report
- Actually just gets interpreted as "use architectural approach"
- Trade-off: Flexibility (works with any command) vs Fidelity (preserves specific behaviors)

## Design Principles

1. **Respect All Commands**: Every command's specific implementation must be preserved
2. **Enable Integration**: Commands should work together, not just sequentially
3. **Handle Conflicts Gracefully**: Detect and resolve conflicts with user input
4. **Support Parallelism**: Run independent commands simultaneously when possible
5. **Maintain Transparency**: User sees and approves execution plans

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