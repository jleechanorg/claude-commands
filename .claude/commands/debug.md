---
description: Debug Command
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Debug Checklist

**Action Steps:**
When `/debug` is active, ensure:
1. [ ] Exact error messages are captured
2. [ ] Stack traces include file:line references
3. [ ] **DOM inspector output** captured for UI issues
4. [ ] **CSS computed properties** extracted for visual elements
5. [ ] **Network request logs** captured for asset loading
6. [ ] **Console errors/warnings** documented
7. [ ] Reproduction steps are documented
8. [ ] Hypotheses are explicitly stated
9. [ ] Evidence supports conclusions
10. [ ] **Screenshot + technical verification** completed before any ✅ claims
11. [ ] Fix is validated with tests
12. [ ] **Anti-bias check**: "What should NOT be working?" tested
13. [ ] Learning captured (automatic `/learn` trigger when debugging succeeds)

## 📋 REFERENCE DOCUMENTATION

# Debug Command

**Usage**: `/debug [task/problem]`

**Purpose**: Apply systematic debugging approach to identify and resolve issues through methodical analysis, evidence gathering, and hypothesis testing.

## Debug Approach (Natural Command)

As a natural command, `/debug` modifies how protocol commands execute by adding:
- **Evidence-based analysis**: Extract exact errors, stack traces, and logs
- **Systematic tracing**: Follow data flow through the system
- **Hypothesis testing**: Form and validate theories about root causes
- **Verbose logging**: Enhanced output for all operations
- **State inspection**: Check variables, configs, and system state

## Debug Context Effects

When combined with protocol commands:

### `/debug /execute`

- Adds detailed logging to implementation
- Inserts debug statements and checkpoints
- Creates verbose error handling
- Implements state validation

### `/debug /test`

- Runs tests with maximum verbosity
- Shows detailed failure analysis
- Includes intermediate assertions
- Captures full stack traces

### `/debug /arch`

- Focuses on identifying architectural flaws
- Traces component interactions
- Analyzes failure points in design
- Reviews error propagation paths

## Debug Methodology

1. **Reproduce**: Establish consistent reproduction steps
2. **Isolate**: Narrow down the problem scope
3. **Technical Verification**: Auto-extract DOM state, CSS properties, network requests, console logs
4. **Hypothesize**: Form theories about root cause
5. **Test**: Validate hypotheses with evidence
6. **Evidence Collection**: Screenshot + technical data + verification report before any success claims
7. **Fix**: Apply targeted solution
8. **Verify**: Confirm fix resolves issue with complete technical verification
9. **Learn**: Auto-capture debugging insights and patterns (triggered on successful resolution)

## Examples

### Basic Debugging

```
/debug "API returns 500 error"
```
Applies systematic debugging to identify the error source.

### Debug with Implementation

```
/debug /execute "fix authentication bug"
```
Implements fix with extensive logging and validation.

### Debug with Testing

```
/debug /test "flaky test failures"
```
Runs tests with verbose output to catch intermittent issues.

### Combined Approach

```
/debug /think /execute "memory leak in production"
```
Deep analysis + systematic debugging + instrumented implementation.

### Debug with Automatic Learning

```
/debug "intermittent database connection failures"
```
When the debugging session successfully identifies and resolves the root cause, `/learn` automatically captures the debugging methodology, solution, and reusable patterns for future similar issues.

## Debug Output Characteristics

- **Stack traces**: Full traces with line numbers
- **Variable states**: Key variable values at each step
- **Execution flow**: Clear path through the code
- **Hypothesis tracking**: Document what was tried
- **Evidence citations**: Reference specific errors/logs

## Integration with Other Commands

- **With `/think`**: Enhances analytical depth
- **With `/verbose`**: Redundant since `/debug` already includes verbose logging. Using both doesn't change output but signals strong emphasis on detailed analysis
- **With `/careful`**: Adds extra validation steps
- **With `/test`**: Creates diagnostic test cases

## Automatic Learning Integration

When debugging successfully resolves an issue, `/debug` automatically triggers `/learn` to capture:

**Learning Categories**:
- **🚨 Critical Debugging Patterns**: Root causes that prevent major failures
- **⚠️ Mandatory Debug Steps**: Required validation steps discovered during debugging
- **✅ Successful Debug Techniques**: Effective hypothesis testing and isolation methods
- **❌ Debug Anti-Patterns**: Investigation approaches that led to dead ends

**Success Detection**:
- ✅ Original problem no longer reproduces after fix
- ✅ Fix validated through testing
- ✅ Root cause clearly identified with evidence
- ✅ Solution applied and verified

**Learning Content Captured**:
- **Debug Session Context**: Original problem description and symptoms
- **Investigation Process**: Hypotheses tested and evidence gathered
- **Root Cause Analysis**: Identified cause with supporting evidence
- **Solution Applied**: Specific fix implemented with file:line references
- **Verification Results**: Test outcomes and confirmation methods
- **Reusable Patterns**: How debugging approach applies to similar issues

**Memory MCP Integration**:
Debugging learnings are automatically stored in the knowledge graph as `debug_session` entities with relations to:
- Technical solutions (`fixes` relationship)
- Code locations (`implemented_in` relationship)
- Problem patterns (`prevents` relationship)
- Debugging techniques (`optimizes` relationship)

This ensures debugging knowledge accumulates and improves future debugging efficiency through pattern recognition and technique refinement.
