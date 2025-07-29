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
3. **Hypothesize**: Form theories about root cause
4. **Test**: Validate hypotheses with evidence
5. **Fix**: Apply targeted solution
6. **Verify**: Confirm fix resolves issue

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

## Debug Checklist

When `/debug` is active, ensure:
- [ ] Exact error messages are captured
- [ ] Stack traces include file:line references
- [ ] Reproduction steps are documented
- [ ] Hypotheses are explicitly stated
- [ ] Evidence supports conclusions
- [ ] Fix is validated with tests
