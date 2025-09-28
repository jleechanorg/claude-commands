# Genesis Test Matrix - Comprehensive TDD Coverage

## Matrix 1: Core Function Interactions (Command Execution × Timeout × Output)

### Test Matrix Variables:
- **Command Types**: claude, codex, cerebras
- **Timeout Scenarios**: normal (600s), large prompt (3600s), timeout exceeded, stall detected
- **Output Patterns**: success, failure, streaming hang, completion signals
- **Process States**: clean exit, timeout termination, force kill

| Command Type | Timeout Scenario | Output Pattern | Expected Behavior |
|--------------|------------------|----------------|-------------------|
| claude | normal | success | Clean completion with output |
| claude | large prompt | completion signals | Auto-terminate after CONVERGED |
| claude | timeout exceeded | partial output | Graceful termination |
| claude | stall detected | no output 5min | Force termination |
| codex | normal | success | Proxy execution success |
| codex | timeout exceeded | partial output | Clean termination |
| cerebras | normal | success | Script execution or fallback |
| cerebras | script missing | fallback to claude | Seamless fallback |

**Total Command Matrix Tests**: 32 combinations

## Matrix 2: Goal Processing Combinations (Goal Type × Refinement × Iterations)

### Test Matrix Variables:
- **Goal Types**: directory-based, direct refinement, interactive, auto-approved
- **Goal States**: valid, ambiguous, missing files, invalid format
- **Iteration Modes**: single, multiple, resume session
- **Exit Criteria**: met, unmet, partially met, validation failed

| Goal Type | Goal State | Iterations | Exit Status | Expected Behavior |
|-----------|------------|------------|-------------|-------------------|
| directory | valid | single | met | Complete in 1 iteration |
| directory | ambiguous | multiple | met | Detect ambiguities, complete |
| directory | missing files | single | validation failed | Error with file paths |
| refinement | valid | multiple | met | Refine → execute → complete |
| refinement | invalid format | single | validation failed | Format error handling |
| interactive | valid | multiple | met | User approval workflow |
| auto-approved | valid | single | met | Skip approval, execute |

**Total Goal Processing Tests**: 28 combinations

## Matrix 3: State Transition Testing (Session × Logging × Recovery)

### Test Matrix Variables:
- **Session States**: new, resumed, corrupted, missing
- **Logging Types**: detailed, human-readable, dual, file errors
- **Recovery Scenarios**: crash recovery, partial completion, timeout recovery
- **Concurrent Access**: single process, multiple processes, file locks

| Session State | Logging Type | Recovery Scenario | Expected Behavior |
|---------------|--------------|-------------------|-------------------|
| new | dual | none | Create session, both logs |
| resumed | detailed | crash recovery | Load session, continue |
| corrupted | human-readable | partial completion | Reset session, warn |
| missing | dual | timeout recovery | New session, recover context |
| concurrent | detailed | file locks | Handle conflicts gracefully |

**Total State Transition Tests**: 20 combinations

## Matrix 4: Error Handling & Edge Cases (Input × Environment × Failures)

### Test Matrix Variables:
- **Input Types**: empty, malformed, very large, unicode, special chars
- **Environment Issues**: missing dependencies, permission errors, disk space
- **Failure Modes**: network timeout, subprocess crash, memory limits
- **Recovery Actions**: retry, fallback, abort, user intervention

| Input Type | Environment Issue | Failure Mode | Recovery Action | Expected Result |
|------------|-------------------|--------------|-----------------|-----------------|
| empty | none | none | none | Proper error message |
| malformed | permissions | subprocess crash | retry | Graceful error handling |
| very large | disk space | memory limits | fallback | Resource management |
| unicode | missing deps | network timeout | abort | Clean failure |
| special chars | none | none | none | Proper sanitization |

**Total Error Handling Tests**: 25 combinations

## Matrix 5: Integration & Workflow Testing (Git × Progress × Consensus)

### Test Matrix Variables:
- **Git States**: clean, dirty, conflicts, no repo
- **Progress Tracking**: file updates, session state, iteration data
- **Consensus Types**: achieved, failed, partial, timeout
- **Workflow Stages**: planning, execution, validation, completion

| Git State | Progress Tracking | Consensus Type | Workflow Stage | Expected Integration |
|-----------|-------------------|----------------|----------------|---------------------|
| clean | file updates | achieved | completion | Successful workflow |
| dirty | session state | failed | validation | Handle uncommitted changes |
| conflicts | iteration data | partial | execution | Conflict resolution |
| no repo | none | timeout | planning | Non-git mode operation |

**Total Integration Tests**: 16 combinations

## Complete Matrix Coverage Summary

- **Matrix 1**: 32 command execution tests
- **Matrix 2**: 28 goal processing tests
- **Matrix 3**: 20 state transition tests
- **Matrix 4**: 25 error handling tests
- **Matrix 5**: 16 integration tests

**Total Matrix Tests**: 121 comprehensive test cases

## Critical Test Paths (High Priority)

### Path 1: Standard Execution Flow
1. Directory goal → valid state → multiple iterations → success
2. Command execution → normal timeout → completion signals → clean exit
3. Session new → dual logging → no recovery → successful workflow

### Path 2: Timeout Prevention Flow
1. Large prompt → extended timeout → streaming detection → auto-termination
2. Stall detection → 5min no output → force termination → clean recovery
3. Completion signals → CONVERGED detected → 20 lines limit → graceful exit

### Path 3: Error Recovery Flow
1. Malformed input → validation error → user feedback → retry
2. Subprocess crash → timeout detection → fallback strategy → completion
3. Session corruption → recovery attempt → reset session → continue

### Path 4: Edge Case Handling
1. Unicode input → special processing → proper encoding → success
2. Very large output → size limits → truncation → warning
3. Concurrent access → file locking → conflict resolution → sequential processing

## Test Infrastructure Requirements

### Testing Dependencies
- pytest (test framework)
- pytest-mock (mocking support)
- pytest-timeout (timeout testing)
- pytest-xdist (parallel execution)
- tempfile (temporary directories)
- unittest.mock (subprocess mocking)

### Mock Requirements
- subprocess.Popen (command execution)
- os.path operations (file system)
- time.time (timeout testing)
- select.select (streaming detection)
- sys.stdout/stderr (output capture)

### Test Data Requirements
- Sample goal directories
- Mock command outputs
- Timeout simulation data
- Error condition triggers
- Session state examples
